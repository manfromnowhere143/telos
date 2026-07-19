#!/usr/bin/env python3
"""Execute or observe iter239's one-shot repository-governance transaction.

The default command is a credentialed, read-only preflight.  ``--execute`` is
the only mode that can create a ruleset, and the client enforces one literal
POST to the frozen endpoint with no redirect, retry, proxy, or second write.
Operational-check capture is GET-only and is kept separate from that mutation
budget.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import ssl
import subprocess
import sys
from typing import Any, Callable, Iterable, Iterator, Mapping
import urllib.parse


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import validate_iter239_repository_governance as guard  # noqa: E402


API_HOST = "api.github.com"
API_PREFIX = f"/repos/{guard.REPOSITORY}"
USER_AGENT = "telos-iter239-repository-governance"
TIMEOUT_SECONDS = 30
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
MAX_PAGES = 100
TRANSACTION_METHOD_BUDGETS = {
    "DELETE": 0,
    "GET": 96,
    "PATCH": 0,
    "POST": 1,
    "PUT": 0,
}
OPERATIONAL_METHOD_BUDGETS = {
    "DELETE": 0,
    "GET": 64,
    "PATCH": 0,
    "POST": 0,
    "PUT": 0,
}
BRANCH_NAME = "agent/iter239-repository-governance"
BRANCH_REF = f"refs/heads/{BRANCH_NAME}"
DISPATCH_STAGE_RELATIVE = (
    guard.ITERATION_ROOT / "proof" / ".post_dispatch_stage.json"
)
OPERATIONAL_STAGE_RELATIVE = (
    guard.ITERATION_ROOT / "proof" / ".operational_pending_stage.json"
)
EXPECTED_PULL_CHECKS = (
    "verify pull_request py3.11",
    "verify pull_request py3.12",
)
EXPECTED_PUSH_CHECKS = (
    "verify push py3.11",
    "verify push py3.12",
)
OPERATIONAL_STAGE_SCHEMA = "telos.iter239.operational_pending_stage.v1"


class GovernanceMutationError(RuntimeError):
    """The frozen governance transaction cannot proceed or cannot be proved."""


class AmbiguousPostError(GovernanceMutationError):
    """The POST may have reached GitHub but no accepted response was obtained."""

    def __init__(
        self,
        message: str,
        *,
        http_status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.http_status = http_status


class PreconditionDriftError(GovernanceMutationError):
    """The exact frozen before-state no longer holds."""


class PostconditionDriftError(GovernanceMutationError):
    """An unrelated compared projection changed after the POST."""


class CreatedRulesetMismatchError(GovernanceMutationError):
    """The created/effective ruleset does not reproduce the frozen policy."""


def utc_second() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def strict_json_document(raw: bytes, *, label: str) -> Any:
    """Parse untrusted server JSON without accepting duplicate/non-finite data."""

    duplicates: list[str] = []

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                duplicates.append(key)
            result[key] = value
        return result

    try:
        value = json.loads(
            raw,
            object_pairs_hook=unique_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                GovernanceMutationError(
                    f"{label}: non-finite JSON value {token!r}"
                )
            ),
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise GovernanceMutationError(
            f"{label}: strict JSON parse failed: {exc}"
        ) from exc
    if duplicates:
        raise GovernanceMutationError(
            f"{label}: duplicate JSON keys: {sorted(set(duplicates))}"
        )
    return value


@dataclass(frozen=True)
class RawResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes


@dataclass(frozen=True)
class ParsedResponse:
    status: int
    headers: Mapping[str, str]
    document: Any
    body: bytes


RequestFunction = Callable[
    [str, str, Mapping[str, str], bytes | None, int],
    RawResponse,
]


def _direct_https_request(
    method: str,
    target: str,
    headers: Mapping[str, str],
    body: bytes | None,
    timeout: int,
) -> RawResponse:
    """Make one direct TLS request; ``http.client`` never follows redirects."""

    context = ssl.create_default_context()
    connection = http.client.HTTPSConnection(
        API_HOST,
        port=443,
        timeout=timeout,
        context=context,
    )
    try:
        connection.request(method, target, body=body, headers=dict(headers))
        response = connection.getresponse()
        payload = response.read(MAX_RESPONSE_BYTES + 1)
        if len(payload) > MAX_RESPONSE_BYTES:
            raise GovernanceMutationError(
                f"GitHub {method} response exceeds {MAX_RESPONSE_BYTES} bytes"
            )
        response_headers: dict[str, str] = {}
        for key, value in response.getheaders():
            lowered = key.lower()
            if lowered in response_headers:
                if lowered != "link":
                    raise GovernanceMutationError(
                        "GitHub response contains a duplicate "
                        f"{lowered!r} header"
                    )
                response_headers[lowered] += f", {value}"
            else:
                response_headers[lowered] = value
        return RawResponse(response.status, response_headers, payload)
    finally:
        connection.close()


def _canonical_query(parameters: Mapping[str, object] | None) -> str:
    if not parameters:
        return ""
    rows: list[tuple[str, str]] = []
    for key, value in sorted(parameters.items()):
        if not isinstance(key, str) or not key:
            raise GovernanceMutationError("GitHub query key is invalid")
        if isinstance(value, bool):
            rendered = "true" if value else "false"
        elif isinstance(value, (int, str)) and not isinstance(value, bool):
            rendered = str(value)
        else:
            raise GovernanceMutationError(
                f"GitHub query value for {key!r} is not scalar"
            )
        rows.append((key, rendered))
    return urllib.parse.urlencode(rows, doseq=False, safe="")


def _validate_api_target(target: str) -> None:
    if not isinstance(target, str) or not (
        target == API_PREFIX
        or target.startswith(f"{API_PREFIX}/")
        or target.startswith(f"{API_PREFIX}?")
    ):
        raise GovernanceMutationError(
            f"GitHub target is outside the frozen repository: {target!r}"
        )
    parsed = urllib.parse.urlsplit(target)
    if parsed.scheme or parsed.netloc or parsed.fragment:
        raise GovernanceMutationError(
            f"GitHub target must be an origin-relative path: {target!r}"
        )
    decoded = urllib.parse.unquote(parsed.path)
    if (
        "\\" in decoded
        or "\x00" in decoded
        or any(part in {"", ".", ".."} for part in decoded.split("/")[1:])
    ):
        raise GovernanceMutationError(
            f"GitHub target path is not canonical: {target!r}"
        )


class GitHubClient:
    """Fixed-origin client with a literal one-POST mutation budget."""

    def __init__(
        self,
        *,
        token: str,
        request_function: RequestFunction = _direct_https_request,
        allow_post: bool,
        method_budgets: Mapping[str, int] = TRANSACTION_METHOD_BUDGETS,
    ) -> None:
        if not token or any(ord(character) < 33 for character in token):
            raise GovernanceMutationError("GitHub credential is empty or malformed")
        self._token = token
        self._request_function = request_function
        self._allow_post = allow_post
        self._post_consumed = False
        if (
            set(method_budgets) != guard.HTTP_METHODS
            or any(
                isinstance(limit, bool) or not isinstance(limit, int) or limit < 0
                for limit in method_budgets.values()
            )
        ):
            raise GovernanceMutationError("HTTP method budgets are invalid")
        self._method_budgets = dict(method_budgets)
        self.counts = {
            method: 0 for method in sorted(guard.HTTP_METHODS)
        }
        self.semantic_counts = {
            operation: 0 for operation in sorted(guard.SEMANTIC_MUTATIONS)
        }

    def _headers(self, *, has_body: bool) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._token}",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": guard.API_VERSION,
        }
        if has_body:
            headers["Content-Type"] = "application/json"
        return headers

    def request_detail(
        self,
        method: str,
        path: str,
        *,
        parameters: Mapping[str, object] | None = None,
        document: Mapping[str, Any] | None = None,
        expected_statuses: Iterable[int] = (200,),
        allow_404: bool = False,
    ) -> ParsedResponse:
        method = method.upper()
        if method not in guard.HTTP_METHODS:
            raise GovernanceMutationError(f"forbidden HTTP method: {method}")
        if method not in {"GET", "POST"}:
            raise GovernanceMutationError(f"forbidden HTTP method: {method}")
        query = _canonical_query(parameters)
        target = path + (f"?{query}" if query else "")
        _validate_api_target(target)

        body: bytes | None = None
        if method == "POST":
            if not self._allow_post:
                raise GovernanceMutationError(
                    "POST is forbidden in this read-only client"
                )
            if self._post_consumed:
                raise GovernanceMutationError("a second POST is forbidden")
            if path != urllib.parse.urlsplit(guard.CREATE_ENDPOINT).path:
                raise GovernanceMutationError(
                    "POST endpoint differs from the frozen ruleset endpoint"
                )
            if parameters:
                raise GovernanceMutationError("the ruleset POST cannot use a query")
            try:
                candidate_body = guard.canonical_json_bytes(document)
            except (TypeError, ValueError, guard.GovernanceError) as exc:
                raise GovernanceMutationError(
                    "POST body is not canonical JSON"
                ) from exc
            expected_body = guard.canonical_json_bytes(
                guard.EXPECTED_REQUEST_BODY
            )
            if candidate_body != expected_body:
                raise GovernanceMutationError(
                    "POST body differs from the frozen ruleset body"
                )
            body = candidate_body
            self._post_consumed = True
        elif document is not None:
            raise GovernanceMutationError("GET cannot carry a JSON document")

        if self.counts[method] >= self._method_budgets[method]:
            raise GovernanceMutationError(
                f"GitHub {method} request budget is exhausted"
            )
        self.counts[method] += 1
        try:
            response = self._request_function(
                method,
                target,
                self._headers(has_body=body is not None),
                body,
                TIMEOUT_SECONDS,
            )
        except Exception as exc:
            if method == "POST":
                raise AmbiguousPostError(
                    f"ruleset POST transport was ambiguous: {type(exc).__name__}"
                ) from exc
            if isinstance(exc, GovernanceMutationError):
                raise
            raise GovernanceMutationError(
                f"GitHub GET transport failed: {type(exc).__name__}"
            ) from exc

        if 300 <= response.status <= 399:
            if method == "POST":
                raise AmbiguousPostError(
                    "ruleset POST returned a forbidden redirect",
                    http_status=response.status,
                )
            raise GovernanceMutationError(
                f"GitHub GET returned forbidden redirect HTTP {response.status}"
            )
        accepted = set(expected_statuses)
        if allow_404:
            accepted.add(404)
        if response.status not in accepted:
            if method == "POST":
                raise AmbiguousPostError(
                    f"ruleset POST returned HTTP {response.status}",
                    http_status=response.status,
                )
            raise GovernanceMutationError(
                f"GitHub {method} returned HTTP {response.status}"
            )
        if method == "POST" and not response.body:
            raise AmbiguousPostError(
                "ruleset POST returned an empty accepted response",
                http_status=response.status,
            )
        if response.status == 204 or not response.body:
            parsed: Any = None
        else:
            try:
                parsed = strict_json_document(
                    response.body,
                    label=f"GitHub {method} {path}",
                )
            except GovernanceMutationError as exc:
                if method == "POST":
                    raise AmbiguousPostError(
                        "ruleset POST returned malformed strict JSON",
                        http_status=response.status,
                    ) from exc
                raise
        return ParsedResponse(
            status=response.status,
            headers=dict(response.headers),
            document=parsed,
            body=response.body,
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        parameters: Mapping[str, object] | None = None,
        document: Mapping[str, Any] | None = None,
        expected_statuses: Iterable[int] = (200,),
        allow_404: bool = False,
    ) -> tuple[int, Any, bytes]:
        response = self.request_detail(
            method,
            path,
            parameters=parameters,
            document=document,
            expected_statuses=expected_statuses,
            allow_404=allow_404,
        )
        return response.status, response.document, response.body

    def get(
        self,
        path: str,
        *,
        parameters: Mapping[str, object] | None = None,
        allow_404: bool = False,
    ) -> tuple[int, Any]:
        status, document, _raw = self.request(
            "GET",
            path,
            parameters=parameters,
            allow_404=allow_404,
        )
        return status, document

    def get_detail(
        self,
        path: str,
        *,
        parameters: Mapping[str, object] | None = None,
        allow_404: bool = False,
    ) -> ParsedResponse:
        return self.request_detail(
            "GET",
            path,
            parameters=parameters,
            allow_404=allow_404,
        )

    def post_ruleset(
        self,
        document: Mapping[str, Any],
    ) -> tuple[int, Any, bytes]:
        return self.request(
            "POST",
            urllib.parse.urlsplit(guard.CREATE_ENDPOINT).path,
            document=document,
            expected_statuses=(201,),
        )

    def receipt_counts(self) -> dict[str, int]:
        return {
            **self.counts,
            **self.semantic_counts,
        }


def github_token() -> str:
    """Obtain the active GitHub credential without exposing it in arguments."""

    result = subprocess.run(
        ["gh", "auth", "token"],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    if result.returncode != 0:
        raise GovernanceMutationError(
            "cannot obtain the active GitHub credential from gh"
        )
    try:
        token = result.stdout.decode("utf-8").strip()
    except UnicodeError as exc:
        raise GovernanceMutationError("GitHub credential is not UTF-8") from exc
    if not token or "\n" in token or "\r" in token:
        raise GovernanceMutationError("GitHub credential is empty or malformed")
    return token


def git(*arguments: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    if check and result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise GovernanceMutationError(
            f"git {' '.join(arguments)} failed: {detail}"
        )
    return result.stdout.decode("utf-8", "strict").strip()


def _assert_regular_parents(path: Path) -> None:
    try:
        relative = path.relative_to(ROOT)
    except ValueError as exc:
        raise GovernanceMutationError(
            f"evidence path escapes repository: {path}"
        ) from exc
    cursor = ROOT
    for component in relative.parent.parts:
        cursor /= component
        if cursor.is_symlink():
            raise GovernanceMutationError(
                f"evidence parent is a symlink: {cursor}"
            )


def materialize_once(path: Path, document: Mapping[str, Any]) -> bytes:
    """Exclusively create, file-fsync, and directory-fsync canonical evidence."""

    _assert_regular_parents(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise GovernanceMutationError(f"refusing to overwrite evidence: {path}")
    raw = guard.canonical_json_bytes(document)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o644)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(descriptor)
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    return raw


def load_policy() -> tuple[dict[str, Any], bytes]:
    policy, raw = guard.load_canonical_json(ROOT / guard.POLICY_RELATIVE)
    failures = guard.policy_failures(policy)
    if failures:
        raise GovernanceMutationError(
            "committed policy is invalid: " + "; ".join(failures)
        )
    return policy, raw


def _object(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GovernanceMutationError(f"{label} must be a JSON object")
    return value


def _array(value: Any, *, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise GovernanceMutationError(f"{label} must be a JSON array")
    return value


def _positive_integer(value: Any, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise GovernanceMutationError(f"{label} must be a positive integer")
    return value


def _string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise GovernanceMutationError(f"{label} must be a nonempty string")
    return value


@dataclass
class EndpointTrace:
    """Request/page accounting retained beside one canonical projection."""

    http_statuses: list[int]
    page_count: int

    @classmethod
    def single(cls, status: int) -> EndpointTrace:
        return cls(http_statuses=[status], page_count=1)

    @property
    def request_count(self) -> int:
        return len(self.http_statuses)

    def add_request(self, status: int, *, page: bool = False) -> None:
        self.http_statuses.append(status)
        if page:
            self.page_count += 1

    def record(self, projection: Any) -> dict[str, Any]:
        return pagination_record(
            projection,
            statuses=self.http_statuses,
            page_count=self.page_count,
            request_count=self.request_count,
        )


def pagination_record(
    projection: Any,
    *,
    complete: bool = True,
    http_statuses: Iterable[int] | None = None,
    statuses: Iterable[int] | None = None,
    page_count: int,
    request_count: int,
) -> dict[str, Any]:
    """Build the validator's exact page/request/digest record."""

    if complete is not True:
        raise GovernanceMutationError(
            "pagination cannot be retained as complete"
        )
    if (http_statuses is None) == (statuses is None):
        raise GovernanceMutationError(
            "exactly one pagination status sequence is required"
        )
    retained_statuses = list(
        http_statuses if http_statuses is not None else statuses or ()
    )
    if (
        isinstance(page_count, bool)
        or not isinstance(page_count, int)
        or page_count < 1
        or isinstance(request_count, bool)
        or not isinstance(request_count, int)
        or request_count < page_count
    ):
        raise GovernanceMutationError("pagination accounting is inconsistent")
    if len(retained_statuses) != request_count:
        raise GovernanceMutationError(
            "pagination status count differs from request count"
        )
    if not all(
        isinstance(status, int)
        and not isinstance(status, bool)
        and 100 <= status <= 599
        for status in retained_statuses
    ):
        raise GovernanceMutationError("pagination HTTP status is invalid")
    if isinstance(projection, list):
        item_count = len(projection)
    elif (
        isinstance(projection, dict)
        and isinstance(projection.get("entries"), list)
    ):
        item_count = len(projection["entries"])
    else:
        item_count = 1
    return {
        "complete": True,
        "http_statuses": retained_statuses,
        "item_count": item_count,
        "page_count": page_count,
        "projection_sha256": guard.canonical_sha256(projection),
        "request_count": request_count,
    }


def _link_relations(value: str | None) -> dict[str, str]:
    if value is None:
        return {}
    relations: dict[str, str] = {}
    for segment in value.split(","):
        match = re.fullmatch(
            r'\s*<([^<>]+)>\s*;\s*rel="([a-z]+)"\s*',
            segment,
        )
        if match is None:
            raise GovernanceMutationError("GitHub Link header is malformed")
        url, relation = match.groups()
        if relation in relations:
            raise GovernanceMutationError(
                f"GitHub Link header duplicates rel={relation!r}"
            )
        parsed = urllib.parse.urlsplit(url)
        if (
            parsed.scheme != "https"
            or parsed.netloc != API_HOST
            or parsed.fragment
        ):
            raise GovernanceMutationError(
                "GitHub Link header escapes the fixed TLS origin"
            )
        target = parsed.path + (f"?{parsed.query}" if parsed.query else "")
        _validate_api_target(target)
        relations[relation] = url
    return relations


def _validated_next_page(
    link_header: str | None,
    *,
    path: str,
    parameters: Mapping[str, object],
    current_page: int,
) -> int | None:
    relations = _link_relations(link_header)
    last_page: int | None = None
    last_url = relations.get("last")
    if last_url is not None:
        parsed_last = urllib.parse.urlsplit(last_url)
        if parsed_last.path != path:
            raise GovernanceMutationError("GitHub last-page path drifted")
        last_pairs = urllib.parse.parse_qsl(
            parsed_last.query,
            keep_blank_values=True,
            strict_parsing=True,
        )
        if len(last_pairs) != len({key for key, _value in last_pairs}):
            raise GovernanceMutationError(
                "GitHub last-page query contains duplicate keys"
            )
        last_parameters = dict(last_pairs)
        expected_nonpage = {
            key: (
                "true"
                if value is True
                else "false"
                if value is False
                else str(value)
            )
            for key, value in parameters.items()
            if key != "page"
        }
        last_value = last_parameters.pop("page", None)
        if last_parameters != expected_nonpage:
            raise GovernanceMutationError(
                "GitHub last-page query differs from the bounded sequence"
            )
        try:
            last_page = int(last_value) if last_value is not None else None
        except ValueError as exc:
            raise GovernanceMutationError(
                "GitHub last-page number is invalid"
            ) from exc
        if last_page is None or last_page < current_page:
            raise GovernanceMutationError(
                "GitHub last-page relation is inconsistent"
            )
    next_url = relations.get("next")
    if next_url is None:
        if last_page is not None and last_page > current_page:
            raise GovernanceMutationError(
                "GitHub Link header omits a required next relation"
            )
        return None
    parsed = urllib.parse.urlsplit(next_url)
    if parsed.path != path:
        raise GovernanceMutationError("GitHub next-page path drifted")
    pairs = urllib.parse.parse_qsl(
        parsed.query,
        keep_blank_values=True,
        strict_parsing=True,
    )
    if len(pairs) != len({key for key, _value in pairs}):
        raise GovernanceMutationError(
            "GitHub next-page query contains duplicate keys"
        )
    observed = dict(pairs)
    expected = {
        key: (
            "true"
            if value is True
            else "false"
            if value is False
            else str(value)
        )
        for key, value in parameters.items()
    }
    expected["page"] = str(current_page + 1)
    if observed != expected:
        raise GovernanceMutationError(
            "GitHub next-page query differs from the bounded sequence"
        )
    if last_page is not None and last_page < current_page + 1:
        raise GovernanceMutationError(
            "GitHub next/last page relations are inconsistent"
        )
    return current_page + 1


def get_paginated(
    client: GitHubClient,
    path: str,
    *,
    parameters: Mapping[str, object] | None = None,
    envelope: str | None = None,
    identity: Callable[[Any], object],
) -> tuple[list[Any], EndpointTrace]:
    """Read every REST page by validated Link relation, with no silent truncation."""

    fixed_parameters = dict(parameters or {})
    fixed_parameters["per_page"] = 100
    page = 1
    items: list[Any] = []
    statuses: list[int] = []
    total_count: int | None = None
    while True:
        if page > MAX_PAGES:
            raise GovernanceMutationError(
                f"GitHub pagination exceeds {MAX_PAGES} pages"
            )
        request_parameters = {**fixed_parameters, "page": page}
        response = client.get_detail(path, parameters=request_parameters)
        statuses.append(response.status)
        if envelope is None:
            page_items = _array(
                response.document,
                label=f"GitHub page {path}",
            )
        else:
            document = _object(
                response.document,
                label=f"GitHub page {path}",
            )
            count = document.get("total_count")
            if (
                isinstance(count, bool)
                or not isinstance(count, int)
                or count < 0
            ):
                raise GovernanceMutationError(
                    f"GitHub {path} total_count is invalid"
                )
            if total_count is None:
                total_count = count
            elif total_count != count:
                raise GovernanceMutationError(
                    f"GitHub {path} total_count drifted during pagination"
                )
            page_items = _array(
                document.get(envelope),
                label=f"GitHub page {path}.{envelope}",
            )
        items.extend(page_items)
        next_page = _validated_next_page(
            response.headers.get("link"),
            path=path,
            parameters=fixed_parameters,
            current_page=page,
        )
        if len(page_items) > 100:
            raise GovernanceMutationError(
                f"GitHub {path} page exceeds the requested page size"
            )
        if envelope is None and len(page_items) == 100 and next_page is None:
            raise GovernanceMutationError(
                f"GitHub {path} has an ambiguous full terminal page"
            )
        if next_page is None:
            break
        page = next_page
    if total_count is not None and len(items) != total_count:
        raise GovernanceMutationError(
            f"GitHub {path} retained item count differs from total_count"
        )
    identities: list[object] = []
    for item in items:
        item_identity = identity(item)
        try:
            hash(item_identity)
        except TypeError as exc:
            raise GovernanceMutationError(
                f"GitHub {path} item identity is not hashable"
            ) from exc
        identities.append(item_identity)
    if len(identities) != len(set(identities)):
        raise GovernanceMutationError(
            f"GitHub {path} contains duplicate objects"
        )
    return items, EndpointTrace(
        http_statuses=statuses,
        page_count=len(statuses),
    )


def get_single(
    client: GitHubClient,
    path: str,
    *,
    parameters: Mapping[str, object] | None = None,
    allow_404: bool = False,
) -> tuple[int, Any, EndpointTrace]:
    response = client.get_detail(
        path,
        parameters=parameters,
        allow_404=allow_404,
    )
    return (
        response.status,
        response.document,
        EndpointTrace.single(response.status),
    )


def method_counts(*, get_count: int, post_count: int = 0) -> dict[str, int]:
    counts = {method: 0 for method in sorted(guard.HTTP_METHODS)}
    counts["GET"] = get_count
    counts["POST"] = post_count
    return counts


def assert_transport_counts(
    client: GitHubClient,
    *,
    expected_get: int,
    expected_post: int,
    label: str,
) -> None:
    expected = method_counts(
        get_count=expected_get,
        post_count=expected_post,
    )
    if client.counts != expected:
        raise GovernanceMutationError(
            f"{label} transport counts differ from retained accounting"
        )


def _projection_count(pagination: Mapping[str, Mapping[str, Any]]) -> int:
    return sum(
        int(record["request_count"])
        for record in pagination.values()
    )


def _identity_field(field: str, *, label: str) -> Callable[[Any], object]:
    def extract(value: Any) -> object:
        row = _object(value, label=label)
        identity = row.get(field)
        if isinstance(identity, bool) or not isinstance(identity, (int, str)):
            raise GovernanceMutationError(
                f"{label}.{field} is not an identity"
            )
        return identity

    return extract


def _canonical_identity(value: Any) -> str:
    return guard.canonical_sha256(value)


def project_repository(value: Any) -> dict[str, Any]:
    row = _object(value, label="repository response")
    return {
        "default_branch": row.get("default_branch"),
        "full_name": row.get("full_name"),
        "merge_settings": {
            "allow_merge_commit": row.get("allow_merge_commit"),
            "allow_rebase_merge": row.get("allow_rebase_merge"),
            "allow_squash_merge": row.get("allow_squash_merge"),
        },
        "visibility": row.get("visibility"),
    }


def project_branch(value: Any) -> dict[str, Any]:
    row = _object(value, label="branch response")
    commit = _object(row.get("commit"), label="branch response.commit")
    return {
        "name": row.get("name"),
        "protected": row.get("protected"),
        "sha": commit.get("sha"),
    }


def project_source_ref(value: Any) -> dict[str, Any]:
    row = _object(value, label="source-ref response")
    target = _object(row.get("object"), label="source-ref response.object")
    return {
        "ref": row.get("ref"),
        "sha": target.get("sha"),
    }


def project_collaborators(values: list[Any]) -> list[dict[str, Any]]:
    projected = []
    for value in values:
        row = _object(value, label="collaborator response")
        projected.append(
            {
                "login": row.get("login"),
                "role_name": row.get("role_name"),
            }
        )
    return sorted(projected, key=lambda row: str(row["login"]))


def project_invitations(values: list[Any]) -> list[dict[str, Any]]:
    projected = []
    for value in values:
        row = _object(value, label="invitation response")
        invitee = row.get("invitee")
        projected.append(
            {
                "id": row.get("id"),
                "invitee_login": (
                    invitee.get("login")
                    if isinstance(invitee, dict)
                    else None
                ),
                "permissions": row.get("permissions"),
            }
        )
    return sorted(projected, key=lambda row: str(row["id"]))


def project_open_pull_request(value: Any) -> dict[str, Any]:
    row = _object(value, label="pull-request response")
    base = _object(row.get("base"), label="pull-request response.base")
    head = _object(row.get("head"), label="pull-request response.head")
    base_repo = _object(
        base.get("repo"),
        label="pull-request response.base.repo",
    )
    head_repo = _object(
        head.get("repo"),
        label="pull-request response.head.repo",
    )
    return {
        "base_ref": base.get("ref"),
        "base_repository": base_repo.get("full_name"),
        "head_ref": head.get("ref"),
        "head_repository": head_repo.get("full_name"),
        "head_sha": head.get("sha"),
        "number": row.get("number"),
        "state": row.get("state"),
    }


def project_operational_pull_request(value: Any) -> dict[str, Any]:
    row = _object(value, label="operational pull-request response")
    base = _object(row.get("base"), label="operational pull-request.base")
    head = _object(row.get("head"), label="operational pull-request.head")
    base_repo = _object(
        base.get("repo"),
        label="operational pull-request.base.repo",
    )
    head_repo = _object(
        head.get("repo"),
        label="operational pull-request.head.repo",
    )
    return {
        "base_ref": base.get("ref"),
        "base_repository": base_repo.get("full_name"),
        "draft": row.get("draft"),
        "head_ref": head.get("ref"),
        "head_repository": head_repo.get("full_name"),
        "head_sha": head.get("sha"),
        "mergeable": row.get("mergeable"),
        "mergeable_state": row.get("mergeable_state"),
        "review_comment_count": row.get("review_comments"),
        "state": row.get("state"),
    }


def project_ruleset(
    value: Any,
    *,
    request_policy: Mapping[str, Any] = guard.EXPECTED_REQUEST_BODY,
    require_current_user_bypass: bool = True,
    validate_policy: bool = True,
) -> dict[str, Any]:
    row = _object(value, label="ruleset response")
    server_policy = {
        key: deepcopy(row[key])
        for key in (
            "bypass_actors",
            "conditions",
            "enforcement",
            "name",
            "rules",
            "target",
        )
        if key in row
    }
    request_projection = deepcopy(dict(request_policy))
    normalization, _normalized = guard.server_policy_normalization(
        request_projection,
        server_policy,
    )
    bypass_present = "current_user_can_bypass" in row
    projection = {
        "id": row.get("id"),
        "normalization": normalization,
        "request_policy": request_projection,
        "server_metadata": {
            "created_at": row.get("created_at"),
            "current_user_can_bypass": (
                row.get("current_user_can_bypass")
                if bypass_present
                else None
            ),
            "current_user_can_bypass_present": bypass_present,
            "links": deepcopy(row.get("_links")),
            "node_id": row.get("node_id"),
            "updated_at": row.get("updated_at"),
        },
        "server_policy": server_policy,
        "source": row.get("source"),
        "source_type": row.get("source_type"),
    }
    if validate_policy:
        failures = guard._ruleset_projection_failures(
            projection,
            label="ruleset projection",
            require_current_user_bypass=require_current_user_bypass,
        )
        if failures:
            raise GovernanceMutationError(
                "ruleset projection failed: " + "; ".join(failures)
            )
    return projection


def project_ruleset_summaries(values: list[Any]) -> list[dict[str, Any]]:
    projected = []
    for value in values:
        row = _object(value, label="ruleset summary")
        projected.append(
            {
                "enforcement": row.get("enforcement"),
                "id": row.get("id"),
                "name": row.get("name"),
                "source": row.get("source"),
                "source_type": row.get("source_type"),
                "target": row.get("target"),
            }
        )
    return sorted(projected, key=lambda row: str(row["id"]))


def project_effective_rules(values: list[Any]) -> list[dict[str, Any]]:
    projected: list[dict[str, Any]] = []
    for value in values:
        row = _object(value, label="effective-rule response")
        item = {
            "ruleset_id": row.get("ruleset_id"),
            "ruleset_source": row.get("ruleset_source"),
            "ruleset_source_type": row.get("ruleset_source_type"),
            "type": row.get("type"),
        }
        if "parameters" in row:
            item["parameters"] = deepcopy(row["parameters"])
        projected.append(item)
    return projected


def capture_ruleset_inventory(
    client: GitHubClient,
    *,
    request_policy: Mapping[str, Any],
    require_details: bool,
) -> tuple[list[dict[str, Any]], EndpointTrace]:
    path = f"{API_PREFIX}/rulesets"
    raw, trace = get_paginated(
        client,
        path,
        parameters={"includes_parents": False},
        identity=_identity_field("id", label="ruleset summary"),
    )
    if not require_details:
        return project_ruleset_summaries(raw), trace
    projected = []
    for summary in raw:
        row = _object(summary, label="ruleset summary")
        ruleset_id = _positive_integer(
            row.get("id"),
            label="ruleset summary.id",
        )
        status, detail, _detail_trace = get_single(
            client,
            f"{API_PREFIX}/rulesets/{ruleset_id}",
        )
        trace.add_request(status)
        projected.append(
            project_ruleset(
                detail,
                request_policy=request_policy,
                validate_policy=False,
            )
        )
    return sorted(projected, key=lambda row: int(row["id"])), trace


def capture_named_rulesets_before(
    client: GitHubClient,
) -> tuple[list[dict[str, Any]], EndpointTrace]:
    raw, trace = get_paginated(
        client,
        f"{API_PREFIX}/rulesets",
        parameters={"includes_parents": False},
        identity=_identity_field("id", label="named ruleset summary"),
    )
    named = [
        value
        for value in raw
        if isinstance(value, dict) and value.get("name") == guard.RULESET_NAME
    ]
    return project_ruleset_summaries(named), trace


def capture_named_ruleset(
    client: GitHubClient,
    *,
    ruleset_id: int,
    request_policy: Mapping[str, Any],
) -> tuple[dict[str, Any], EndpointTrace]:
    status, value, trace = get_single(
        client,
        f"{API_PREFIX}/rulesets/{ruleset_id}",
    )
    if status != 200:
        raise GovernanceMutationError("named ruleset lookup did not return 200")
    return (
        project_ruleset(value, request_policy=request_policy),
        trace,
    )


def capture_ruleset_history(
    client: GitHubClient,
    *,
    ruleset_id: int,
    request_policy: Mapping[str, Any],
) -> tuple[dict[str, Any], EndpointTrace]:
    path = f"{API_PREFIX}/rulesets/{ruleset_id}/history"
    raw, trace = get_paginated(
        client,
        path,
        identity=_identity_field("version_id", label="ruleset history"),
    )
    entries = []
    for value in raw:
        row = _object(value, label="ruleset history entry")
        actor = _object(
            row.get("actor"),
            label="ruleset history entry.actor",
        )
        entries.append(
            {
                "actor": {
                    "id": actor.get("id"),
                    "type": actor.get("type"),
                },
                "updated_at": row.get("updated_at"),
                "version_id": row.get("version_id"),
            }
        )
    if len(entries) != 1:
        raise GovernanceMutationError(
            "new ruleset history does not contain exactly one version"
        )
    version_id = _positive_integer(
        entries[0]["version_id"],
        label="ruleset history version_id",
    )
    status, latest_raw, _latest_trace = get_single(
        client,
        f"{path}/{version_id}",
    )
    trace.add_request(status)
    latest = _object(latest_raw, label="ruleset history version")
    actor = _object(
        latest.get("actor"),
        label="ruleset history version.actor",
    )
    state = _object(
        latest.get("state"),
        label="ruleset history version.state",
    )
    server_policy = {
        key: deepcopy(state[key])
        for key in (
            "bypass_actors",
            "conditions",
            "enforcement",
            "name",
            "rules",
            "target",
        )
        if key in state
    }
    latest_projection = {
        "actor": {
            "id": actor.get("id"),
            "type": actor.get("type"),
        },
        "state": {
            "id": state.get("id"),
            "request_policy": deepcopy(dict(request_policy)),
            "server_policy": server_policy,
            "source": state.get("source"),
            "source_type": state.get("source_type"),
        },
        "updated_at": latest.get("updated_at"),
        "version_id": latest.get("version_id"),
    }
    return (
        {
            "entries": entries,
            "latest_version": latest_projection,
            "ruleset_id": ruleset_id,
        },
        trace,
    )


def project_check_rows(
    check_runs: Iterable[Any],
    *,
    workflow_runs_by_suite_id: Mapping[int, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    projected: list[dict[str, Any]] = []
    observed_names: set[str] = set()
    for value in check_runs:
        row = _object(value, label="check run")
        check_suite = _object(
            row.get("check_suite"),
            label="check run.check_suite",
        )
        suite_id_value = check_suite.get("id")
        suite_id = (
            suite_id_value
            if isinstance(suite_id_value, int)
            and not isinstance(suite_id_value, bool)
            else None
        )
        if suite_id is None or suite_id not in workflow_runs_by_suite_id:
            run: Mapping[str, Any] = {}
        else:
            run = workflow_runs_by_suite_id[suite_id]
        app = _object(row.get("app"), label="check run.app")
        name = row.get("name")
        if not isinstance(name, str) or not name:
            raise GovernanceMutationError("check run name is invalid")
        if name in observed_names:
            raise GovernanceMutationError(
                f"duplicate projected check name: {name}"
            )
        observed_names.add(name)
        projected.append(
            {
                "attempt": run.get("run_attempt", run.get("attempt")),
                "check_run_id": row.get("id"),
                "check_suite_id": suite_id_value,
                "conclusion": row.get("conclusion"),
                "event": run.get("event"),
                "head_sha": row.get("head_sha"),
                "integration_id": app.get("id"),
                "name": name,
                "status": row.get("status"),
                "workflow_id": run.get("workflow_id"),
                "workflow_path": run.get(
                    "path",
                    run.get("workflow_path"),
                ),
                "workflow_run_id": run.get(
                    "id",
                    run.get("workflow_run_id"),
                ),
            }
        )
    return sorted(projected, key=lambda row: str(row["name"]))


def capture_checks(
    client: GitHubClient,
    *,
    source_commit: str,
    include_push: bool,
) -> tuple[list[dict[str, Any]], EndpointTrace]:
    workflow_path = (
        f"{API_PREFIX}/actions/workflows/{guard.WORKFLOW_ID}/runs"
    )
    workflow_runs, workflow_trace = get_paginated(
        client,
        workflow_path,
        parameters={"head_sha": source_commit},
        envelope="workflow_runs",
        identity=_identity_field("id", label="workflow run"),
    )
    expected_events = (
        {"pull_request", "push"} if include_push else {"pull_request"}
    )
    selected_runs: list[dict[str, Any]] = []
    for value in workflow_runs:
        row = _object(value, label="workflow run")
        if row.get("event") not in expected_events:
            continue
        if row.get("head_sha") != source_commit:
            continue
        if row.get("workflow_id") != guard.WORKFLOW_ID:
            continue
        if row.get("path") != guard.WORKFLOW_RELATIVE.as_posix():
            continue
        selected_runs.append(row)
    runs_by_event: dict[str, list[dict[str, Any]]] = {
        event: [] for event in expected_events
    }
    for run in selected_runs:
        event = run.get("event")
        if isinstance(event, str) and event in runs_by_event:
            runs_by_event[event].append(run)
    for event, event_runs in sorted(runs_by_event.items()):
        if len(event_runs) != 1:
            raise GovernanceMutationError(
                f"expected exactly one same-head {event} workflow run"
            )
        run = event_runs[0]
        if (
            isinstance(run.get("run_attempt"), bool)
            or run.get("run_attempt") != 1
        ):
            raise GovernanceMutationError(
                f"same-head {event} workflow run is not attempt one"
            )
        _positive_integer(
            run.get("id"),
            label=f"{event} workflow run.id",
        )
        _positive_integer(
            run.get("check_suite_id"),
            label=f"{event} workflow run.check_suite_id",
        )
    suites: dict[int, dict[str, Any]] = {}
    for run in selected_runs:
        suite_id = _positive_integer(
            run.get("check_suite_id"),
            label="workflow run.check_suite_id",
        )
        if suite_id in suites:
            raise GovernanceMutationError(
                "multiple workflow runs share one check suite"
            )
        suites[suite_id] = run
    check_path = f"{API_PREFIX}/commits/{source_commit}/check-runs"
    check_runs, check_trace = get_paginated(
        client,
        check_path,
        parameters={"filter": "all"},
        envelope="check_runs",
        identity=_identity_field("id", label="check run"),
    )
    workflow_trace.http_statuses.extend(check_trace.http_statuses)
    workflow_trace.page_count += check_trace.page_count

    expected_names = set(EXPECTED_PULL_CHECKS)
    if include_push:
        expected_names.update(EXPECTED_PUSH_CHECKS)
    selected_checks = []
    for value in check_runs:
        row = _object(value, label="check run")
        check_suite = _object(
            row.get("check_suite"),
            label="check run.check_suite",
        )
        suite_id = check_suite.get("id")
        if row.get("name") in expected_names or suite_id in suites:
            selected_checks.append(row)
    return (
        project_check_rows(
            selected_checks,
            workflow_runs_by_suite_id=suites,
        ),
        workflow_trace,
    )


def _capture_repository(
    client: GitHubClient,
) -> tuple[dict[str, Any], EndpointTrace]:
    _status, value, trace = get_single(client, API_PREFIX)
    return project_repository(value), trace


def _capture_branch(
    client: GitHubClient,
) -> tuple[dict[str, Any], EndpointTrace]:
    _status, value, trace = get_single(
        client,
        f"{API_PREFIX}/branches/{guard.DEFAULT_BRANCH}",
    )
    return project_branch(value), trace


def _capture_classic_protection(
    client: GitHubClient,
) -> tuple[dict[str, Any], EndpointTrace]:
    status, _value, trace = get_single(
        client,
        f"{API_PREFIX}/branches/{guard.DEFAULT_BRANCH}/protection",
        allow_404=True,
    )
    return {
        "classification": "absent" if status == 404 else "present",
        "http_status": status,
    }, trace


def _capture_effective_rules(
    client: GitHubClient,
) -> tuple[list[dict[str, Any]], EndpointTrace]:
    values, trace = get_paginated(
        client,
        f"{API_PREFIX}/rules/branches/{guard.DEFAULT_BRANCH}",
        identity=_canonical_identity,
    )
    return project_effective_rules(values), trace


def _capture_collaborators(
    client: GitHubClient,
) -> tuple[list[dict[str, Any]], EndpointTrace]:
    values, trace = get_paginated(
        client,
        f"{API_PREFIX}/collaborators",
        parameters={"affiliation": "direct"},
        identity=_identity_field("id", label="collaborator"),
    )
    return project_collaborators(values), trace


def _capture_invitations(
    client: GitHubClient,
) -> tuple[list[dict[str, Any]], EndpointTrace]:
    values, trace = get_paginated(
        client,
        f"{API_PREFIX}/invitations",
        identity=_identity_field("id", label="invitation"),
    )
    return project_invitations(values), trace


def _capture_exact_object(
    client: GitHubClient,
    *,
    path: str,
    label: str,
    keys: set[str],
) -> tuple[dict[str, Any], EndpointTrace]:
    _status, value, trace = get_single(client, path)
    row = _object(value, label=label)
    projection = {key: deepcopy(row.get(key)) for key in sorted(keys)}
    return projection, trace


def _capture_source_ref(
    client: GitHubClient,
) -> tuple[dict[str, Any], EndpointTrace]:
    _status, value, trace = get_single(
        client,
        f"{API_PREFIX}/git/ref/heads/{BRANCH_NAME}",
    )
    return project_source_ref(value), trace


def _capture_open_pull_request(
    client: GitHubClient,
) -> tuple[dict[str, Any], EndpointTrace]:
    values, trace = get_paginated(
        client,
        f"{API_PREFIX}/pulls",
        parameters={
            "base": guard.DEFAULT_BRANCH,
            "head": f"manfromnowhere143:{BRANCH_NAME}",
            "state": "open",
        },
        identity=_identity_field("id", label="pull request"),
    )
    if len(values) != 1:
        raise GovernanceMutationError(
            "formal source must have exactly one open pull request"
        )
    return project_open_pull_request(values[0]), trace


def _capture_before_projections(
    client: GitHubClient,
    *,
    source_commit: str,
    request_policy: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    projections: dict[str, Any] = {}
    traces: dict[str, EndpointTrace] = {}

    projections["repository"], traces["repository"] = _capture_repository(client)
    projections["branch"], traces["branch"] = _capture_branch(client)
    (
        projections["classic_protection"],
        traces["classic_protection"],
    ) = _capture_classic_protection(client)
    (
        projections["rulesets"],
        traces["rulesets"],
    ) = capture_ruleset_inventory(
        client,
        request_policy=request_policy,
        require_details=False,
    )
    (
        projections["named_rulesets"],
        traces["named_rulesets"],
    ) = capture_named_rulesets_before(client)
    (
        projections["effective_rules"],
        traces["effective_rules"],
    ) = _capture_effective_rules(client)
    (
        projections["collaborators"],
        traces["collaborators"],
    ) = _capture_collaborators(client)
    (
        projections["invitations"],
        traces["invitations"],
    ) = _capture_invitations(client)
    projections["actions"], traces["actions"] = _capture_exact_object(
        client,
        path=f"{API_PREFIX}/actions/permissions",
        label="Actions permissions",
        keys={"allowed_actions", "enabled", "sha_pinning_required"},
    )
    (
        projections["default_workflow_permissions"],
        traces["default_workflow_permissions"],
    ) = _capture_exact_object(
        client,
        path=f"{API_PREFIX}/actions/permissions/workflow",
        label="workflow permissions",
        keys={
            "can_approve_pull_request_reviews",
            "default_workflow_permissions",
        },
    )
    (
        projections["fork_pull_request_policy"],
        traces["fork_pull_request_policy"],
    ) = _capture_exact_object(
        client,
        path=(
            f"{API_PREFIX}/actions/permissions/"
            "fork-pr-contributor-approval"
        ),
        label="fork pull-request approval policy",
        keys={"approval_policy"},
    )
    (
        projections["source_ref"],
        traces["source_ref"],
    ) = _capture_source_ref(client)
    (
        projections["open_pull_request"],
        traces["open_pull_request"],
    ) = _capture_open_pull_request(client)
    projections["checks"], traces["checks"] = capture_checks(
        client,
        source_commit=source_commit,
        include_push=True,
    )
    pagination = {
        key: traces[key].record(projections[key])
        for key in sorted(projections)
    }
    return projections, pagination


def capture_before_state(
    client: GitHubClient,
    *,
    source_commit: str,
    policy: Mapping[str, Any],
    policy_sha256: str,
) -> dict[str, Any]:
    projections, pagination = _capture_before_projections(
        client,
        source_commit=source_commit,
        request_policy=_object(
            policy.get("request_body"),
            label="policy.request_body",
        ),
    )
    get_count = _projection_count(pagination)
    return {
        "api_version": guard.API_VERSION,
        "observed_at": utc_second(),
        "pagination": pagination,
        "policy_sha256": policy_sha256,
        "projections": projections,
        "repository": guard.REPOSITORY,
        "request_counts": method_counts(get_count=get_count),
        "schema_version": guard.BEFORE_SCHEMA,
        "source_commit": source_commit,
    }


def assert_before_preconditions(
    before: dict[str, Any],
    *,
    policy_sha256: str,
) -> None:
    failures = guard.before_state_failures(
        before,
        policy_sha256=policy_sha256,
    )
    if failures:
        raise PreconditionDriftError(
            "formal precondition drift: " + "; ".join(failures)
        )


def _capture_after_projections(
    client: GitHubClient,
    *,
    before: Mapping[str, Any],
    request_policy: Mapping[str, Any],
    expected_ruleset_id: int | None,
) -> tuple[
    dict[str, Any],
    dict[str, dict[str, Any]],
    int,
    list[str],
]:
    projections: dict[str, Any] = {}
    traces: dict[str, EndpointTrace] = {}
    projections["repository"], traces["repository"] = _capture_repository(client)
    projections["branch"], traces["branch"] = _capture_branch(client)
    (
        projections["collaborators"],
        traces["collaborators"],
    ) = _capture_collaborators(client)
    (
        projections["invitations"],
        traces["invitations"],
    ) = _capture_invitations(client)
    projections["actions"], traces["actions"] = _capture_exact_object(
        client,
        path=f"{API_PREFIX}/actions/permissions",
        label="Actions permissions",
        keys={"allowed_actions", "enabled", "sha_pinning_required"},
    )
    (
        projections["default_workflow_permissions"],
        traces["default_workflow_permissions"],
    ) = _capture_exact_object(
        client,
        path=f"{API_PREFIX}/actions/permissions/workflow",
        label="workflow permissions",
        keys={
            "can_approve_pull_request_reviews",
            "default_workflow_permissions",
        },
    )
    (
        projections["fork_pull_request_policy"],
        traces["fork_pull_request_policy"],
    ) = _capture_exact_object(
        client,
        path=(
            f"{API_PREFIX}/actions/permissions/"
            "fork-pr-contributor-approval"
        ),
        label="fork pull-request approval policy",
        keys={"approval_policy"},
    )
    inventory, traces["rulesets"] = capture_ruleset_inventory(
        client,
        request_policy=request_policy,
        require_details=True,
    )
    projections["rulesets"] = inventory
    inventory_ids = [
        _positive_integer(row.get("id"), label="ruleset inventory id")
        for row in inventory
    ]
    concurrent_inventory_drift = False
    if expected_ruleset_id is None:
        if len(inventory_ids) != 1:
            raise CreatedRulesetMismatchError(
                "ambiguous POST did not reconcile to exactly one ruleset"
            )
        observed_id = inventory_ids[0]
    else:
        if expected_ruleset_id not in inventory_ids:
            raise CreatedRulesetMismatchError(
                "POST-created ruleset ID is absent from inventory"
            )
        observed_id = expected_ruleset_id
        concurrent_inventory_drift = len(inventory_ids) != 1
    named, traces["named_ruleset"] = capture_named_ruleset(
        client,
        ruleset_id=observed_id,
        request_policy=request_policy,
    )
    projections["named_ruleset"] = named
    (
        projections["effective_rules"],
        traces["effective_rules"],
    ) = _capture_effective_rules(client)
    history, traces["ruleset_history"] = capture_ruleset_history(
        client,
        ruleset_id=observed_id,
        request_policy=request_policy,
    )
    projections["ruleset_history"] = history

    before_projections = before.get("projections")
    if not isinstance(before_projections, dict):
        raise GovernanceMutationError(
            "retained before-state projections are invalid"
        )
    drift = [
        key
        for key in guard.UNCHANGED_PROJECTIONS
        if guard.canonical_json_bytes(projections.get(key))
        != guard.canonical_json_bytes(before_projections.get(key))
    ]
    if concurrent_inventory_drift:
        drift.append("rulesets")
    pagination = {
        key: traces[key].record(projections[key])
        for key in sorted(projections)
    }
    return projections, pagination, observed_id, drift


def capture_after_state(
    client: GitHubClient,
    *,
    before: Mapping[str, Any],
    source_commit: str,
    policy: Mapping[str, Any],
    policy_sha256: str,
    expected_ruleset_id: int | None,
) -> dict[str, Any]:
    projections, pagination, ruleset_id, drift = (
        _capture_after_projections(
            client,
            before=before,
            request_policy=_object(
                policy.get("request_body"),
                label="policy.request_body",
            ),
            expected_ruleset_id=expected_ruleset_id,
        )
    )
    get_count = _projection_count(pagination)
    return {
        "api_version": guard.API_VERSION,
        "before_comparison": {
            "drift": drift,
            "unchanged": deepcopy(guard.UNCHANGED_PROJECTIONS),
        },
        "created_ruleset_id": ruleset_id,
        "observed_at": utc_second(),
        "pagination": pagination,
        "policy_sha256": policy_sha256,
        "projections": projections,
        "repository": guard.REPOSITORY,
        "request_counts": method_counts(get_count=get_count),
        "schema_version": guard.AFTER_SCHEMA,
        "source_commit": source_commit,
    }


def assert_after_postconditions(
    after: dict[str, Any],
    *,
    policy_sha256: str,
    before: dict[str, Any],
    policy: dict[str, Any],
) -> None:
    failures = guard.after_state_failures(
        after,
        policy_sha256=policy_sha256,
        before=before,
        policy=policy,
    )
    if not failures:
        return
    comparison = after.get("before_comparison")
    if (
        isinstance(comparison, dict)
        and isinstance(comparison.get("drift"), list)
        and comparison["drift"]
    ):
        raise PostconditionDriftError(
            "unrelated postcondition drift: " + "; ".join(failures)
        )
    raise CreatedRulesetMismatchError(
        "created ruleset/effective state mismatch: " + "; ".join(failures)
    )


def project_post_response(
    value: Any,
    *,
    request_policy: Mapping[str, Any],
) -> dict[str, Any]:
    projection = project_ruleset(
        value,
        request_policy=request_policy,
        require_current_user_bypass=False,
    )
    failures = guard._ruleset_projection_failures(
        projection,
        label="POST ruleset response",
        require_current_user_bypass=False,
    )
    if failures:
        raise CreatedRulesetMismatchError(
            "POST response ruleset mismatch: " + "; ".join(failures)
        )
    return projection


def exhaustive_request_counts(
    *,
    get_count: int,
    post_count: int,
) -> dict[str, int]:
    counts = {
        key: 0
        for key in sorted(guard.HTTP_METHODS | guard.SEMANTIC_MUTATIONS)
    }
    counts["GET"] = get_count
    counts["POST"] = post_count
    return counts


def _proof_path(proof_root: Path, label: str) -> Path:
    return proof_root / guard.EVIDENCE_RELATIVES[label].name


def _evidence_digests(proof_root: Path) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for label in sorted(guard.EVIDENCE_RELATIVES):
        path = _proof_path(proof_root, label)
        result[label] = (
            sha256_bytes(path.read_bytes())
            if path.is_file() and not path.is_symlink()
            else None
        )
    return result


def classify_abort(reason_code: str) -> dict[str, Any]:
    classification = next(
        (
            status
            for status, reasons in guard.ABORT_OUTCOMES.items()
            if reason_code in reasons
        ),
        None,
    )
    if classification is None:
        raise GovernanceMutationError(
            f"unregistered abort reason: {reason_code}"
        )
    if reason_code == "precondition_drift":
        phase = "precondition"
    elif reason_code == "dispatch_not_attempted":
        phase = "dispatch"
    else:
        phase = "postcondition"
    required_post_count = (
        0
        if reason_code in {"dispatch_not_attempted", "precondition_drift"}
        else 1
    )
    return {
        "classification": classification,
        "phase": phase,
        "required_post_count": required_post_count,
    }


def build_abort_record(
    *,
    source_commit: str,
    policy_sha256: str,
    reason_code: str,
    request_counts: Mapping[str, int],
    dispatch_attempt: Mapping[str, Any] | None,
    proof_root: Path,
    recorded_at: str | None = None,
) -> dict[str, Any]:
    classification = classify_abort(reason_code)
    return {
        "available_evidence_sha256": _evidence_digests(proof_root),
        "classification": classification["classification"],
        "dispatch_attempt": (
            deepcopy(dict(dispatch_attempt))
            if dispatch_attempt is not None
            else None
        ),
        "phase": classification["phase"],
        "policy_sha256": policy_sha256,
        "reason_code": reason_code,
        "recorded_at": recorded_at or utc_second(),
        "repository": guard.REPOSITORY,
        "request_counts": dict(request_counts),
        "schema_version": guard.ABORT_SCHEMA,
        "source_commit": source_commit,
    }


def _materialize_abort(
    *,
    source_commit: str,
    policy_sha256: str,
    reason_code: str,
    request_counts: Mapping[str, int],
    dispatch_attempt: Mapping[str, Any] | None,
    proof_root: Path,
    write_document: Callable[[Path, Mapping[str, Any]], bytes] = materialize_once,
    recorded_at: str | None = None,
) -> dict[str, Any]:
    abort = build_abort_record(
        source_commit=source_commit,
        policy_sha256=policy_sha256,
        reason_code=reason_code,
        request_counts=request_counts,
        dispatch_attempt=dispatch_attempt,
        proof_root=proof_root,
        recorded_at=recorded_at,
    )
    expected_root = ROOT / guard.PROOF_ROOT
    if proof_root == expected_root:
        failures = guard.abort_record_failures(
            root=ROOT,
            abort=abort,
            policy_sha256=policy_sha256,
        )
        if failures:
            raise GovernanceMutationError(
                "refusing to retain invalid abort record: "
                + "; ".join(failures)
            )
    write_document(proof_root / guard.ABORT_RELATIVE.name, abort)
    return abort


def build_mutation_intent(
    *,
    source_commit: str,
    policy: Mapping[str, Any],
    policy_sha256: str,
    before_raw: bytes,
    persisted_at: str | None = None,
) -> dict[str, Any]:
    return {
        "api_version": guard.API_VERSION,
        "before_state_sha256": sha256_bytes(before_raw),
        "endpoint": guard.CREATE_ENDPOINT,
        "method": "POST",
        "persisted_at": persisted_at or utc_second(),
        "policy_sha256": policy_sha256,
        "repository": guard.REPOSITORY,
        "request_body": deepcopy(policy["request_body"]),
        "request_body_sha256": policy["request_body_sha256"],
        "schema_version": guard.INTENT_SCHEMA,
        "source_commit": source_commit,
        "write_guards": {
            "directory_fsync_completed": True,
            "exclusive_create": True,
            "file_fsync_completed": True,
        },
    }


def build_dispatch_attempt(
    *,
    source_commit: str,
    intent_raw: bytes | None = None,
    mutation_intent_sha256: str | None = None,
    consumed_at: str | None = None,
) -> dict[str, Any]:
    if (intent_raw is None) == (mutation_intent_sha256 is None):
        raise GovernanceMutationError(
            "dispatch attempt requires exactly one intent binding"
        )
    intent_digest = (
        sha256_bytes(intent_raw)
        if intent_raw is not None
        else mutation_intent_sha256
    )
    return {
        "consumed_at": consumed_at or utc_second(),
        "endpoint": guard.CREATE_ENDPOINT,
        "method": "POST",
        "mutation_intent_sha256": intent_digest,
        "schema_version": guard.DISPATCH_SCHEMA,
        "source_commit": source_commit,
        "write_guards": {
            "directory_fsync_completed": True,
            "exclusive_create": True,
            "file_fsync_completed": True,
        },
    }


def _remove_materialized_stage(path: Path) -> None:
    if not path.is_file() or path.is_symlink():
        raise GovernanceMutationError(
            f"transaction stage is absent or not regular: {path}"
        )
    path.unlink()
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _assert_fresh_transaction_paths(proof_root: Path) -> None:
    paths = [
        *(
            _proof_path(proof_root, label)
            for label in guard.EVIDENCE_RELATIVES
        ),
        proof_root / guard.ABORT_RELATIVE.name,
        proof_root / DISPATCH_STAGE_RELATIVE.name,
        proof_root / OPERATIONAL_STAGE_RELATIVE.name,
    ]
    if proof_root == ROOT / guard.PROOF_ROOT:
        paths.append(ROOT / guard.RESULT_RELATIVE)
    existing = [
        str(path)
        for path in paths
        if path.exists() or path.is_symlink()
    ]
    if existing:
        raise GovernanceMutationError(
            "partial transaction artifacts exist; use explicit recovery: "
            f"{sorted(existing)}"
        )


@contextmanager
def repository_transaction_lock(
    proof_root: Path | None = None,
) -> Iterator[None]:
    """Take a nonblocking process-lifetime lock for the formal transaction."""

    if proof_root is None:
        git_path = git(
            "rev-parse",
            "--path-format=absolute",
            "--git-path",
            "telos-iter239-governance.lock",
        )
        path = Path(git_path)
    else:
        path = proof_root.parent / ".telos-iter239-governance.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_RDWR | os.O_CREAT
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise GovernanceMutationError(
                "another iter239 governance transaction is active"
            ) from exc
        os.ftruncate(descriptor, 0)
        os.write(descriptor, f"{os.getpid()}\n".encode("ascii"))
        os.fsync(descriptor)
        yield
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def transaction_lock() -> Iterator[None]:
    """Backward-compatible alias for the production repository lock."""

    return repository_transaction_lock()


def run_read_only_preflight(
    client: GitHubClient,
    *,
    source_commit: str,
    policy: dict[str, Any],
    policy_raw: bytes,
) -> dict[str, Any]:
    before = capture_before_state(
        client,
        source_commit=source_commit,
        policy=policy,
        policy_sha256=sha256_bytes(policy_raw),
    )
    assert_before_preconditions(
        before,
        policy_sha256=sha256_bytes(policy_raw),
    )
    retained_counts = _object(
        before.get("request_counts"),
        label="before-state request counts",
    )
    assert_transport_counts(
        client,
        expected_get=_positive_integer(
            retained_counts.get("GET"),
            label="before-state GET count",
        ),
        expected_post=0,
        label="read-only preflight",
    )
    return before


def _load_proof_document(
    proof_root: Path,
    label: str,
) -> tuple[dict[str, Any], bytes]:
    path = _proof_path(proof_root, label)
    try:
        return guard.load_canonical_json(path)
    except guard.GovernanceError as exc:
        raise GovernanceMutationError(
            f"partial recovery evidence {label} is invalid: {exc}"
        ) from exc


def _recover_governance_transaction(
    client: GitHubClient,
    *,
    source_commit: str,
    policy: dict[str, Any],
    policy_raw: bytes,
    proof_root: Path,
    capture_after: Callable[..., dict[str, Any]],
    write_document: Callable[[Path, Mapping[str, Any]], bytes],
    clock: Callable[[], str],
) -> dict[str, Any]:
    """Recover only what durable bytes prove; never dispatch or accept anew."""

    before_path = _proof_path(proof_root, "before_state")
    intent_path = _proof_path(proof_root, "mutation_intent")
    forbidden = [
        _proof_path(proof_root, "after_state"),
        _proof_path(proof_root, "mutation_receipt"),
        _proof_path(proof_root, "operational_check"),
        proof_root / guard.ABORT_RELATIVE.name,
    ]
    if (
        not before_path.is_file()
        or not intent_path.is_file()
        or any(path.exists() or path.is_symlink() for path in forbidden)
    ):
        raise GovernanceMutationError(
            "partial recovery state is not the exact before+intent boundary"
        )
    before, before_raw = _load_proof_document(proof_root, "before_state")
    intent, intent_raw = _load_proof_document(proof_root, "mutation_intent")
    policy_sha256 = sha256_bytes(policy_raw)
    before_failures = guard.before_state_failures(
        before,
        policy_sha256=policy_sha256,
    )
    intent_failures = guard.mutation_intent_failures(
        intent,
        policy_sha256=policy_sha256,
        before=before,
        before_raw=before_raw,
        policy=policy,
    )
    if before_failures or intent_failures:
        raise GovernanceMutationError(
            "partial recovery evidence fails reconstruction: "
            + "; ".join([*before_failures, *intent_failures])
        )
    if before.get("source_commit") != source_commit:
        raise GovernanceMutationError(
            "restart source commit differs from retained evidence"
        )

    dispatch_path = proof_root / DISPATCH_STAGE_RELATIVE.name
    if not dispatch_path.exists():
        retained_counts = before.get("request_counts")
        get_count = (
            retained_counts.get("GET")
            if isinstance(retained_counts, dict)
            else None
        )
        if (
            isinstance(get_count, bool)
            or not isinstance(get_count, int)
            or get_count < 1
        ):
            raise GovernanceMutationError(
                "retained before-state GET count is invalid"
            )
        abort = _materialize_abort(
            source_commit=source_commit,
            policy_sha256=policy_sha256,
            reason_code="dispatch_not_attempted",
            request_counts=exhaustive_request_counts(
                get_count=get_count,
                post_count=0,
            ),
            dispatch_attempt=None,
            proof_root=proof_root,
            write_document=write_document,
            recorded_at=clock(),
        )
        return {
            "abort_record": abort,
            "before_state": before,
            "mutation_intent": intent,
        }
    try:
        dispatch, _dispatch_raw = guard.load_canonical_json(dispatch_path)
    except guard.GovernanceError as exc:
        raise GovernanceMutationError(
            f"partial recovery dispatch journal is invalid: {exc}"
        ) from exc
    dispatch_failures = guard.dispatch_attempt_failures(
        dispatch,
        label="recovery dispatch attempt",
        source_commit=source_commit,
        mutation_intent_sha256=sha256_bytes(intent_raw),
    )
    if dispatch_failures:
        raise GovernanceMutationError(
            "partial recovery dispatch journal fails reconstruction: "
            + "; ".join(dispatch_failures)
        )
    try:
        capture_after(
            client,
            before=before,
            source_commit=source_commit,
            policy=policy,
            policy_sha256=policy_sha256,
            expected_ruleset_id=None,
        )
    except GovernanceMutationError:
        pass
    raise GovernanceMutationError(
        "restart incident cannot accept the transaction: prior GET and "
        "POST attempt counts are not fully reconstructible"
    )


def _run_governance_transaction(
    client: GitHubClient,
    *,
    source_commit: str,
    policy: dict[str, Any],
    policy_raw: bytes,
    proof_root: Path,
    recover: bool,
    capture_before: Callable[..., dict[str, Any]],
    capture_after: Callable[..., dict[str, Any]],
    write_document: Callable[[Path, Mapping[str, Any]], bytes],
    project_post: Callable[[Any], dict[str, Any]],
    clock: Callable[[], str],
) -> dict[str, Any]:
    """Run the fresh, live-process one-POST transaction to a retained receipt."""

    if recover:
        return _recover_governance_transaction(
            client,
            source_commit=source_commit,
            policy=policy,
            policy_raw=policy_raw,
            proof_root=proof_root,
            capture_after=capture_after,
            write_document=write_document,
            clock=clock,
        )
    _assert_fresh_transaction_paths(proof_root)
    policy_sha256 = sha256_bytes(policy_raw)
    started_at = clock()
    before = capture_before(
        client,
        source_commit=source_commit,
        policy=policy,
        policy_sha256=policy_sha256,
    )
    before_raw = write_document(
        _proof_path(proof_root, "before_state"),
        before,
    )
    try:
        retained_before_counts = _object(
            before.get("request_counts"),
            label="before-state request counts",
        )
        try:
            assert_transport_counts(
                client,
                expected_get=_positive_integer(
                    retained_before_counts.get("GET"),
                    label="formal before-state GET count",
                ),
                expected_post=0,
                label="formal before-state",
            )
        except GovernanceMutationError as exc:
            raise PreconditionDriftError(str(exc)) from exc
        assert_before_preconditions(
            before,
            policy_sha256=policy_sha256,
        )
    except PreconditionDriftError:
        abort = _materialize_abort(
            source_commit=source_commit,
            policy_sha256=policy_sha256,
            reason_code="precondition_drift",
            request_counts=exhaustive_request_counts(
                get_count=client.counts["GET"],
                post_count=0,
            ),
            dispatch_attempt=None,
            proof_root=proof_root,
            write_document=write_document,
            recorded_at=clock(),
        )
        return {
            "abort_record": abort,
            "before_state": before,
        }

    intent = build_mutation_intent(
        source_commit=source_commit,
        policy=policy,
        policy_sha256=policy_sha256,
        before_raw=before_raw,
        persisted_at=clock(),
    )
    intent_raw = write_document(
        _proof_path(proof_root, "mutation_intent"),
        intent,
    )
    intent_failures = guard.mutation_intent_failures(
        intent,
        policy_sha256=policy_sha256,
        before=before,
        before_raw=before_raw,
        policy=policy,
    )
    if intent_failures:
        abort = _materialize_abort(
            source_commit=source_commit,
            policy_sha256=policy_sha256,
            reason_code="dispatch_not_attempted",
            request_counts=exhaustive_request_counts(
                get_count=client.counts["GET"],
                post_count=0,
            ),
            dispatch_attempt=None,
            proof_root=proof_root,
            write_document=write_document,
            recorded_at=clock(),
        )
        return {
            "abort_record": abort,
            "before_state": before,
            "mutation_intent": intent,
        }

    dispatch = build_dispatch_attempt(
        source_commit=source_commit,
        intent_raw=intent_raw,
        consumed_at=clock(),
    )
    write_document(proof_root / DISPATCH_STAGE_RELATIVE.name, dispatch)

    ambiguous: AmbiguousPostError | None = None
    post_projection: dict[str, Any] | None = None
    expected_ruleset_id: int | None = None
    try:
        _status, post_document, _post_raw = client.post_ruleset(
            deepcopy(policy["request_body"])
        )
        try:
            post_projection = project_post(post_document)
            expected_ruleset_id = _positive_integer(
                post_projection.get("id"),
                label="POST response ruleset id",
            )
        except GovernanceMutationError as exc:
            ambiguous = AmbiguousPostError(
                "HTTP 201 response did not prove the created ruleset",
                http_status=201,
            )
            ambiguous.__cause__ = exc
    except AmbiguousPostError as exc:
        ambiguous = exc

    try:
        after = capture_after(
            client,
            before=before,
            source_commit=source_commit,
            policy=policy,
            policy_sha256=policy_sha256,
            expected_ruleset_id=expected_ruleset_id,
        )
    except CreatedRulesetMismatchError:
        reason = (
            "ambiguous_unresolved"
            if ambiguous is not None
            else "mismatched_created_ruleset"
        )
        _materialize_abort(
            source_commit=source_commit,
            policy_sha256=policy_sha256,
            reason_code=reason,
            request_counts=exhaustive_request_counts(
                get_count=client.counts["GET"],
                post_count=1,
            ),
            dispatch_attempt=dispatch,
            proof_root=proof_root,
            write_document=write_document,
            recorded_at=clock(),
        )
        raise
    except GovernanceMutationError:
        reason = (
            "ambiguous_unresolved"
            if ambiguous is not None
            else "postcondition_unobserved"
        )
        _materialize_abort(
            source_commit=source_commit,
            policy_sha256=policy_sha256,
            reason_code=reason,
            request_counts=exhaustive_request_counts(
                get_count=client.counts["GET"],
                post_count=1,
            ),
            dispatch_attempt=dispatch,
            proof_root=proof_root,
            write_document=write_document,
            recorded_at=clock(),
        )
        raise

    after_raw = write_document(
        _proof_path(proof_root, "after_state"),
        after,
    )
    try:
        assert_after_postconditions(
            after,
            policy_sha256=policy_sha256,
            before=before,
            policy=policy,
        )
    except PostconditionDriftError:
        _materialize_abort(
            source_commit=source_commit,
            policy_sha256=policy_sha256,
            reason_code="postcondition_drift",
            request_counts=exhaustive_request_counts(
                get_count=client.counts["GET"],
                post_count=1,
            ),
            dispatch_attempt=dispatch,
            proof_root=proof_root,
            write_document=write_document,
            recorded_at=clock(),
        )
        raise
    except CreatedRulesetMismatchError:
        reason = (
            "ambiguous_unresolved"
            if ambiguous is not None
            else "mismatched_created_ruleset"
        )
        _materialize_abort(
            source_commit=source_commit,
            policy_sha256=policy_sha256,
            reason_code=reason,
            request_counts=exhaustive_request_counts(
                get_count=client.counts["GET"],
                post_count=1,
            ),
            dispatch_attempt=dispatch,
            proof_root=proof_root,
            write_document=write_document,
            recorded_at=clock(),
        )
        raise

    named = after["projections"]["named_ruleset"]
    if (
        post_projection is not None
        and guard.canonical_json_bytes(
            guard.ruleset_response_core(post_projection)
        )
        != guard.canonical_json_bytes(
            guard.ruleset_response_core(named)
        )
    ):
        _materialize_abort(
            source_commit=source_commit,
            policy_sha256=policy_sha256,
            reason_code="mismatched_created_ruleset",
            request_counts=exhaustive_request_counts(
                get_count=client.counts["GET"],
                post_count=1,
            ),
            dispatch_attempt=dispatch,
            proof_root=proof_root,
            write_document=write_document,
            recorded_at=clock(),
        )
        raise CreatedRulesetMismatchError(
            "POST response core differs from fresh named ruleset"
        )

    if ambiguous is None:
        outcome = "applied"
        reconciliation = "not_required"
        post_response = {
            "classification": "accepted_created",
            "http_status": 201,
            "projection": post_projection,
            "projection_sha256": guard.canonical_sha256(post_projection),
        }
    else:
        outcome = "ambiguous_applied"
        reconciliation = "exact_get_match"
        post_response = {
            "classification": (
                "ambiguous_transport"
                if ambiguous.http_status is None
                else "ambiguous_http_response"
            ),
            "http_status": ambiguous.http_status,
            "projection": None,
            "projection_sha256": None,
        }
    receipt = {
        "after_state_sha256": sha256_bytes(after_raw),
        "ambiguous_reconciliation": reconciliation,
        "before_state_sha256": sha256_bytes(before_raw),
        "dispatch_attempt": dispatch,
        "finished_at": clock(),
        "mutation_intent_sha256": sha256_bytes(intent_raw),
        "outcome": outcome,
        "policy_sha256": policy_sha256,
        "post_response": post_response,
        "repository": guard.REPOSITORY,
        "request_body_sha256": policy["request_body_sha256"],
        "request_counts": client.receipt_counts(),
        "ruleset_id": after["created_ruleset_id"],
        "schema_version": guard.RECEIPT_SCHEMA,
        "source_commit": source_commit,
        "started_at": started_at,
    }
    receipt_failures = guard.mutation_receipt_failures(
        receipt,
        policy_sha256=policy_sha256,
        before=before,
        before_raw=before_raw,
        intent=intent,
        intent_raw=intent_raw,
        after=after,
        after_raw=after_raw,
        policy=policy,
    )
    if receipt_failures:
        _materialize_abort(
            source_commit=source_commit,
            policy_sha256=policy_sha256,
            reason_code="postcondition_unobserved",
            request_counts=exhaustive_request_counts(
                get_count=client.counts["GET"],
                post_count=1,
            ),
            dispatch_attempt=dispatch,
            proof_root=proof_root,
            write_document=write_document,
            recorded_at=clock(),
        )
        raise GovernanceMutationError(
            "mutation receipt failed local reconstruction: "
            + "; ".join(receipt_failures)
        )
    write_document(
        _proof_path(proof_root, "mutation_receipt"),
        receipt,
    )
    _remove_materialized_stage(proof_root / DISPATCH_STAGE_RELATIVE.name)
    return {
        "after_state": after,
        "before_state": before,
        "mutation_intent": intent,
        "mutation_receipt": receipt,
    }


def run_governance_transaction(
    client: GitHubClient,
    *,
    source_commit: str,
    policy: dict[str, Any],
    policy_raw: bytes,
    proof_root: Path | None = None,
    recover: bool = False,
    capture_before: Callable[..., dict[str, Any]] = capture_before_state,
    capture_after: Callable[..., dict[str, Any]] = capture_after_state,
    write_document: Callable[
        [Path, Mapping[str, Any]],
        bytes,
    ] = materialize_once,
    project_ruleset: Callable[[Any], dict[str, Any]] | None = None,
    clock: Callable[[], str] = utc_second,
) -> dict[str, Any]:
    """Lock and execute the injected-or-live transaction state machine."""

    supplied_proof_root = proof_root
    retained_root = (
        proof_root if proof_root is not None else ROOT / guard.PROOF_ROOT
    )
    projector = (
        project_ruleset
        if project_ruleset is not None
        else lambda value: project_post_response(
            value,
            request_policy=policy["request_body"],
        )
    )
    lock_root = retained_root if supplied_proof_root is not None else None
    with repository_transaction_lock(lock_root):
        return _run_governance_transaction(
            client,
            source_commit=source_commit,
            policy=policy,
            policy_raw=policy_raw,
            proof_root=retained_root,
            recover=recover,
            capture_before=capture_before,
            capture_after=capture_after,
            write_document=write_document,
            project_post=projector,
            clock=clock,
        )


def _canonical_equal(left: Any, right: Any) -> bool:
    return guard.canonical_json_bytes(left) == guard.canonical_json_bytes(
        right
    )


def capture_operational_phase(
    client: GitHubClient,
    *,
    phase_name: str,
    pull_request_number: int,
    source_commit: str,
    policy: Mapping[str, Any],
    after_state: Mapping[str, Any],
) -> dict[str, Any]:
    """Capture one fresh GET-only pending or success gate observation."""

    if phase_name not in {"pending", "success"}:
        raise GovernanceMutationError("operational phase is invalid")
    projections: dict[str, Any] = {}
    traces: dict[str, EndpointTrace] = {}

    _status, pull_raw, traces["pull_request"] = get_single(
        client,
        f"{API_PREFIX}/pulls/{pull_request_number}",
    )
    projections["pull_request"] = project_operational_pull_request(pull_raw)
    review_comments, traces["review_comments"] = get_paginated(
        client,
        f"{API_PREFIX}/pulls/{pull_request_number}/comments",
        identity=_identity_field("id", label="review comment"),
    )
    projections["review_comments"] = review_comments
    projections["checks"], traces["checks"] = capture_checks(
        client,
        source_commit=source_commit,
        include_push=False,
    )
    projections["branch"], traces["branch"] = _capture_branch(client)
    inventory, traces["rulesets"] = capture_ruleset_inventory(
        client,
        request_policy=_object(
            policy.get("request_body"),
            label="policy.request_body",
        ),
        require_details=True,
    )
    projections["rulesets"] = inventory
    after_ruleset_id = after_state.get("created_ruleset_id")
    ruleset_id = _positive_integer(
        after_ruleset_id,
        label="retained after-state ruleset ID",
    )
    (
        projections["named_ruleset"],
        traces["named_ruleset"],
    ) = capture_named_ruleset(
        client,
        ruleset_id=ruleset_id,
        request_policy=_object(
            policy.get("request_body"),
            label="policy.request_body",
        ),
    )
    (
        projections["effective_rules"],
        traces["effective_rules"],
    ) = _capture_effective_rules(client)

    pagination = {
        key: traces[key].record(projections[key])
        for key in sorted(projections)
    }
    raw_pull = projections["pull_request"]
    non_check_satisfied = (
        raw_pull.get("base_ref") == guard.DEFAULT_BRANCH
        and raw_pull.get("base_repository") == guard.REPOSITORY
        and raw_pull.get("head_ref") == BRANCH_NAME
        and raw_pull.get("head_repository") == guard.REPOSITORY
        and raw_pull.get("head_sha") == source_commit
        and raw_pull.get("draft") is False
        and raw_pull.get("mergeable") is True
        and raw_pull.get("review_comment_count") == 0
        and raw_pull.get("state") == "open"
        and review_comments == []
    )
    rollup = "PENDING" if phase_name == "pending" else "SUCCESS"
    merge_permitted = (
        rollup == "SUCCESS"
        and raw_pull.get("mergeable_state") == "clean"
        and non_check_satisfied
    )
    phase = {
        "branch": projections["branch"],
        "checks": projections["checks"],
        "effective_rules": projections["effective_rules"],
        "merge_permitted": merge_permitted,
        "named_ruleset": projections["named_ruleset"],
        "non_check_requirements_satisfied": non_check_satisfied,
        "observed_at": utc_second(),
        "pagination": pagination,
        "pull_request": raw_pull,
        "request_counts": method_counts(
            get_count=_projection_count(pagination)
        ),
        "review_comments": review_comments,
        "required_check_rollup_state": rollup,
        "rulesets": projections["rulesets"],
        "source_commit": source_commit,
    }
    expected_after = after_state.get("projections")
    if not isinstance(expected_after, dict):
        raise GovernanceMutationError(
            "retained after-state projections are invalid"
        )
    failures: list[str] = []
    for key in (
        "branch",
        "effective_rules",
        "named_ruleset",
        "rulesets",
    ):
        if not _canonical_equal(phase[key], expected_after.get(key)):
            failures.append(
                f"fresh operational {key} differs from retained after-state"
            )
    failures.extend(
        guard._check_run_failures(
            phase["checks"],
            source_commit=source_commit,
            expected_status=phase_name,
            include_push=False,
            label=f"operational {phase_name}.checks",
        )
    )
    failures.extend(
        guard._pagination_failures(
            pagination,
            expected_endpoints=set(projections),
            projections=projections,
            label=f"operational {phase_name}.pagination",
        )
    )
    expected_merge_state = "blocked" if phase_name == "pending" else "clean"
    if raw_pull.get("mergeable_state") != expected_merge_state:
        failures.append(
            f"operational {phase_name} mergeable_state is not "
            f"{expected_merge_state}"
        )
    if non_check_satisfied is not True:
        failures.append(
            f"operational {phase_name} non-check requirements are not satisfied"
        )
    if merge_permitted is not (phase_name == "success"):
        failures.append(
            f"operational {phase_name} merge permission derivation differs"
        )
    if phase["request_counts"]["GET"] != _projection_count(pagination):
        failures.append(
            f"operational {phase_name} GET accounting differs"
        )
    if client.counts != phase["request_counts"]:
        failures.append(
            f"operational {phase_name} transport counts differ from "
            "retained accounting"
        )
    if failures:
        raise GovernanceMutationError(
            f"operational {phase_name} capture failed: "
            + "; ".join(failures)
        )
    return phase


def merge_operational_phases(
    *,
    pending: dict[str, Any],
    success: dict[str, Any],
    policy_sha256: str,
    pull_request: dict[str, Any],
    ruleset_source_commit: str,
) -> dict[str, Any]:
    """Join only a fresh pending→success transition on one exact PR head."""

    pending_head = pending.get("source_commit")
    success_head = success.get("source_commit")
    if pending_head != success_head:
        raise GovernanceMutationError(
            "operational phases do not follow the same head"
        )
    pending_time = pending.get("observed_at")
    success_time = success.get("observed_at")
    if (
        not isinstance(pending_time, str)
        or not isinstance(success_time, str)
        or pending_time >= success_time
    ):
        raise GovernanceMutationError(
            "operational success is not fresh or does not follow pending"
        )
    pending_checks = pending.get("checks")
    success_checks = success.get("checks")
    if not isinstance(pending_checks, list) or not isinstance(
        success_checks,
        list,
    ):
        raise GovernanceMutationError(
            "operational checks are not retained arrays"
        )
    identity_keys = (
        "attempt",
        "check_run_id",
        "check_suite_id",
        "event",
        "head_sha",
        "integration_id",
        "name",
        "workflow_id",
        "workflow_path",
        "workflow_run_id",
    )
    pending_identity = sorted(
        (
            tuple(row.get(key) for key in identity_keys)
            if isinstance(row, dict)
            else ()
        )
        for row in pending_checks
    )
    success_identity = sorted(
        (
            tuple(row.get(key) for key in identity_keys)
            if isinstance(row, dict)
            else ()
        )
        for row in success_checks
    )
    if guard.canonical_json_bytes(pending_identity) != guard.canonical_json_bytes(
        success_identity
    ):
        raise GovernanceMutationError(
            "operational phases do not follow the same check runs"
        )
    operational = {
        "api_version": guard.API_VERSION,
        "independent_review_status": "blocked",
        "pending": deepcopy(pending),
        "policy_sha256": policy_sha256,
        "pull_request": deepcopy(pull_request),
        "repository": guard.REPOSITORY,
        "ruleset_source_commit": ruleset_source_commit,
        "schema_version": guard.OPERATIONAL_SCHEMA,
        "source_commit": pending_head,
        "success": deepcopy(success),
    }
    after_state = {
        "projections": {
            key: deepcopy(pending.get(key))
            for key in (
                "branch",
                "effective_rules",
                "named_ruleset",
                "rulesets",
            )
        }
    }
    failures = guard.operational_check_failures(
        operational,
        policy_sha256=policy_sha256,
        source_commit=ruleset_source_commit,
        expected_pull_request_number=pull_request.get("number"),
        after_state=after_state,
    )
    if failures:
        raise GovernanceMutationError(
            "operational phase merge failed: " + "; ".join(failures)
        )
    return operational


def _load_completed_transaction(
    *,
    proof_root: Path,
    policy: dict[str, Any],
    policy_raw: bytes,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    abort_path = proof_root / guard.ABORT_RELATIVE.name
    dispatch_path = proof_root / DISPATCH_STAGE_RELATIVE.name
    if abort_path.exists() or abort_path.is_symlink():
        raise GovernanceMutationError(
            "completed transaction cannot coexist with an abort record"
        )
    if dispatch_path.exists() or dispatch_path.is_symlink():
        raise GovernanceMutationError(
            "completed transaction cannot retain a dispatch stage"
        )
    before, before_raw = _load_proof_document(proof_root, "before_state")
    intent, intent_raw = _load_proof_document(
        proof_root,
        "mutation_intent",
    )
    after, after_raw = _load_proof_document(proof_root, "after_state")
    receipt, _receipt_raw = _load_proof_document(
        proof_root,
        "mutation_receipt",
    )
    policy_sha256 = sha256_bytes(policy_raw)
    failures = [
        *guard.before_state_failures(
            before,
            policy_sha256=policy_sha256,
        ),
        *guard.mutation_intent_failures(
            intent,
            policy_sha256=policy_sha256,
            before=before,
            before_raw=before_raw,
            policy=policy,
        ),
        *guard.after_state_failures(
            after,
            policy_sha256=policy_sha256,
            before=before,
            policy=policy,
        ),
        *guard.mutation_receipt_failures(
            receipt,
            policy_sha256=policy_sha256,
            before=before,
            before_raw=before_raw,
            intent=intent,
            intent_raw=intent_raw,
            after=after,
            after_raw=after_raw,
            policy=policy,
        ),
    ]
    if failures:
        raise GovernanceMutationError(
            "retained transaction fails reconstruction: "
            + "; ".join(failures)
        )
    return before, intent, after, receipt


def _operational_pull_identity(before: Mapping[str, Any]) -> dict[str, Any]:
    projections = before.get("projections")
    pull = (
        projections.get("open_pull_request")
        if isinstance(projections, dict)
        else None
    )
    row = _object(pull, label="retained open pull request")
    return {
        "base_ref": row.get("base_ref"),
        "base_repository": row.get("base_repository"),
        "head_ref": row.get("head_ref"),
        "head_repository": row.get("head_repository"),
        "number": row.get("number"),
    }


def capture_operational_transition(
    client: GitHubClient,
    *,
    phase_name: str,
    source_commit: str,
    policy: dict[str, Any],
    policy_raw: bytes,
    proof_root: Path | None = None,
    write_document: Callable[
        [Path, Mapping[str, Any]],
        bytes,
    ] = materialize_once,
) -> dict[str, Any]:
    """Persist pending stage or complete success evidence, using GET only."""

    retained_root = (
        proof_root if proof_root is not None else ROOT / guard.PROOF_ROOT
    )
    before, _intent, after, _receipt = _load_completed_transaction(
        proof_root=retained_root,
        policy=policy,
        policy_raw=policy_raw,
    )
    ruleset_source = _string(
        before.get("source_commit"),
        label="ruleset source commit",
    )
    pull_identity = _operational_pull_identity(before)
    pull_number = _positive_integer(
        pull_identity.get("number"),
        label="pull-request number",
    )
    stage_path = retained_root / OPERATIONAL_STAGE_RELATIVE.name
    operational_path = _proof_path(retained_root, "operational_check")
    if operational_path.exists() or operational_path.is_symlink():
        raise GovernanceMutationError(
            "operational evidence already exists; refusing overwrite"
        )
    policy_sha256 = sha256_bytes(policy_raw)

    if phase_name == "pending":
        if stage_path.exists() or stage_path.is_symlink():
            raise GovernanceMutationError(
                "operational pending stage already exists"
            )
        pending = capture_operational_phase(
            client,
            phase_name="pending",
            pull_request_number=pull_number,
            source_commit=source_commit,
            policy=policy,
            after_state=after,
        )
        stage = {
            "pending": pending,
            "policy_sha256": policy_sha256,
            "pull_request": pull_identity,
            "repository": guard.REPOSITORY,
            "ruleset_source_commit": ruleset_source,
            "schema_version": OPERATIONAL_STAGE_SCHEMA,
            "source_commit": source_commit,
        }
        write_document(stage_path, stage)
        if client.counts["POST"] != 0:
            raise GovernanceMutationError(
                "operational pending capture consumed a POST"
            )
        return stage

    if phase_name != "success":
        raise GovernanceMutationError("operational phase is invalid")
    if not stage_path.is_file() or stage_path.is_symlink():
        raise GovernanceMutationError(
            "operational success requires a regular pending stage"
        )
    try:
        stage, _stage_raw = guard.load_canonical_json(stage_path)
    except guard.GovernanceError as exc:
        raise GovernanceMutationError(
            f"operational pending stage is invalid: {exc}"
        ) from exc
    expected_stage_keys = {
        "pending",
        "policy_sha256",
        "pull_request",
        "repository",
        "ruleset_source_commit",
        "schema_version",
        "source_commit",
    }
    if set(stage) != expected_stage_keys:
        raise GovernanceMutationError(
            "operational pending stage keys differ"
        )
    expected_stage_identity = {
        "policy_sha256": policy_sha256,
        "pull_request": pull_identity,
        "repository": guard.REPOSITORY,
        "ruleset_source_commit": ruleset_source,
        "schema_version": OPERATIONAL_STAGE_SCHEMA,
        "source_commit": source_commit,
    }
    for key, expected in expected_stage_identity.items():
        if not _canonical_equal(stage.get(key), expected):
            raise GovernanceMutationError(
                f"operational pending stage {key} differs"
            )
    success = capture_operational_phase(
        client,
        phase_name="success",
        pull_request_number=pull_number,
        source_commit=source_commit,
        policy=policy,
        after_state=after,
    )
    operational = merge_operational_phases(
        pending=_object(stage.get("pending"), label="pending stage"),
        success=success,
        policy_sha256=policy_sha256,
        pull_request=pull_identity,
        ruleset_source_commit=ruleset_source,
    )
    failures = guard.operational_check_failures(
        operational,
        policy_sha256=policy_sha256,
        source_commit=ruleset_source,
        expected_pull_request_number=pull_number,
        after_state=after,
    )
    if failures:
        raise GovernanceMutationError(
            "operational transition fails reconstruction: "
            + "; ".join(failures)
        )
    write_document(operational_path, operational)
    _remove_materialized_stage(stage_path)
    if client.counts["POST"] != 0:
        raise GovernanceMutationError(
            "operational success capture consumed a POST"
        )
    return operational


def local_source_commit(*, require_clean: bool) -> str:
    head = git("rev-parse", "HEAD")
    if re.fullmatch(r"[0-9a-f]{40}", head) is None:
        raise GovernanceMutationError("HEAD is not an exact commit")
    if head in {guard.MERGED_MASTER_ANCHOR, guard.ACTIVATION_COMMIT}:
        raise GovernanceMutationError(
            "formal source must be a post-activation implementation commit"
        )
    if (
        subprocess.run(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                guard.ACTIVATION_COMMIT,
                head,
            ],
            cwd=ROOT,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        != 0
    ):
        raise GovernanceMutationError(
            "HEAD does not descend from the exact iter239 activation"
        )
    branch = git("branch", "--show-current")
    if branch != BRANCH_NAME:
        raise GovernanceMutationError(
            f"current branch differs from {BRANCH_NAME!r}"
        )
    if require_clean:
        status = git("status", "--porcelain=v1", "--untracked-files=all")
        if status:
            raise GovernanceMutationError(
                "formal execution requires an exactly clean worktree"
            )
    for relative in guard.SOURCE_BOUND_RELATIVES:
        current = (ROOT / relative).read_bytes()
        retained = subprocess.run(
            ["git", "show", f"{head}:{relative.as_posix()}"],
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
        if retained.returncode != 0 or retained.stdout != current:
            raise GovernanceMutationError(
                "executing source differs from committed HEAD: "
                f"{relative.as_posix()}"
            )
    return head


def operational_source_commit(*, phase_name: str) -> str:
    head = local_source_commit(require_clean=False)
    proof_root = ROOT / guard.PROOF_ROOT
    before, _before_raw = _load_proof_document(
        proof_root,
        "before_state",
    )
    ruleset_source = _string(
        before.get("source_commit"),
        label="ruleset source commit",
    )
    if head == ruleset_source:
        raise GovernanceMutationError(
            "operational check requires an ordinary new commit"
        )
    ancestry = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            ruleset_source,
            head,
        ],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if ancestry.returncode != 0:
        raise GovernanceMutationError(
            "operational source does not descend from ruleset source"
        )
    allowed = {
        f"?? {_proof_path(proof_root, label).relative_to(ROOT).as_posix()}"
        for label in (
            "after_state",
            "before_state",
            "mutation_intent",
            "mutation_receipt",
        )
    }
    if phase_name == "success":
        allowed.add(
            "?? "
            + (
                proof_root / OPERATIONAL_STAGE_RELATIVE.name
            ).relative_to(ROOT).as_posix()
        )
    status = git("status", "--porcelain=v1", "--untracked-files=all")
    observed = set(status.splitlines()) if status else set()
    if observed != allowed:
        raise GovernanceMutationError(
            "operational worktree differs from the exact retained-proof "
            f"boundary: {sorted(observed ^ allowed)}"
        )
    return head


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--execute",
        action="store_true",
        help="perform the one authorized ruleset POST after every gate passes",
    )
    modes.add_argument(
        "--recover",
        action="store_true",
        help=(
            "inspect an interrupted transaction without issuing a new POST "
            "or synthesizing acceptance"
        ),
    )
    modes.add_argument(
        "--capture-operational",
        choices=("pending", "success"),
        help="capture the GET-only pending or success operational phase",
    )
    args = parser.parse_args(argv)
    try:
        policy, policy_raw = load_policy()
        token = github_token()
        if args.capture_operational:
            source_commit = operational_source_commit(
                phase_name=args.capture_operational
            )
            client = GitHubClient(
                token=token,
                allow_post=False,
                method_budgets=OPERATIONAL_METHOD_BUDGETS,
            )
            with transaction_lock():
                retained = capture_operational_transition(
                    client,
                    phase_name=args.capture_operational,
                    source_commit=source_commit,
                    policy=policy,
                    policy_raw=policy_raw,
                )
            if args.capture_operational == "pending":
                print(
                    "iter239 operational pending phase retained "
                    f"for {retained['source_commit']}; "
                    "success evidence is still required"
                )
            else:
                print(
                    "iter239 operational pending-to-success transition "
                    f"retained for {retained['source_commit']}"
                )
            return 0

        if args.recover:
            source_commit = local_source_commit(require_clean=False)
            client = GitHubClient(
                token=token,
                allow_post=False,
            )
            retained = run_governance_transaction(
                client,
                source_commit=source_commit,
                policy=policy,
                policy_raw=policy_raw,
                recover=True,
            )
            abort = retained.get("abort_record")
            if isinstance(abort, dict):
                print(
                    "iter239 interrupted transaction retained as "
                    f"{abort['classification']}/{abort['reason_code']}; "
                    "acceptance remains unavailable"
                )
                return 1
            raise GovernanceMutationError(
                "recovery returned no explicit non-acceptance record"
            )

        source_commit = local_source_commit(require_clean=True)
        if args.execute:
            client = GitHubClient(
                token=token,
                allow_post=True,
            )
            retained = run_governance_transaction(
                client,
                source_commit=source_commit,
                policy=policy,
                policy_raw=policy_raw,
            )
            abort = retained.get("abort_record")
            if isinstance(abort, dict):
                print(
                    "iter239 governance transaction did not pass: "
                    f"{abort['classification']}/{abort['reason_code']}",
                    file=sys.stderr,
                )
                return 1
            receipt = _object(
                retained.get("mutation_receipt"),
                label="retained mutation receipt",
            )
            print(
                "iter239 governance transaction retained: "
                f"{receipt['outcome']}; ruleset_id={receipt['ruleset_id']}; "
                "operational acceptance is still required"
            )
            return 0

        _assert_fresh_transaction_paths(ROOT / guard.PROOF_ROOT)
        client = GitHubClient(
            token=token,
            allow_post=False,
        )
        before = run_read_only_preflight(
            client,
            source_commit=source_commit,
            policy=policy,
            policy_raw=policy_raw,
        )
        print(
            "iter239 read-only preflight passed for "
            f"{source_commit}; GET={before['request_counts']['GET']}; "
            "zero evidence files and zero mutation requests were emitted; "
            "gate acceptance remains unestablished"
        )
        return 0
    except GovernanceMutationError as exc:
        print(f"iter239 governance driver failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
