#!/usr/bin/env python3
"""Adjudicate the failed iter241 capture without importing its frozen validator."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
from pathlib import Path
import stat
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter241_iter240_repository_closure"
RAW_ROOT = EXPERIMENT / "proof/raw/iter240_repository_closure"
ORIGINAL_RECEIPT = EXPERIMENT / "proof/iter240_repository_closure.json"
CORRECTION_RECEIPT = EXPERIMENT / "proof/iter240_repository_closure_correction.json"
ATTEMPT_MARKER = RAW_ROOT / "capture_attempt.json"
PREARM_RECORD = EXPERIMENT / "proof/prearm_stop_record.json"
SAFE_FIXTURE = EXPERIMENT / "fixtures/repository_closure_correction_safe.json"
KNOWN_BAD_FIXTURE = EXPERIMENT / "fixtures/repository_closure_correction_known_bad.json"

REPOSITORY = "manfromnowhere143/telos"
AUTHORIZATION_HEAD = "6a9a4f66ec331011c9dfbe14b3a22259a5b585d5"
SEALED_HEAD = "f954696c935ad0b733dcd613b553e1799a7b3810"
PREDECESSOR = "b597b763f2eb52b2f4f2d36e7daaa31654be076b"
MERGE = "39e2484cba450fe5346349921572720b0e456fb7"
MERGE_TREE = "1a6384324dd3e2a15121d981938a0bcee397c904"

ORIGINAL_RECEIPT_SHA256 = "b37b19a288445311ae4a7ba04313b87646c79240adf156e345ddc75cbefab874"
ATTEMPT_MARKER_SHA256 = "99e3c9e3952c75e7a11e081dcb1d6c1fdd80ca7d6fa15f945500081315518987"
PREARM_RECORD_SHA256 = "240161b3c845882ee58171223e911b2e2808d6a03a99262439ba5edd2171b8e0"

FROZEN_INSTRUMENT_SHA256 = {
    "experiments/iter241_iter240_repository_closure/HYPOTHESIS.md": (
        "4c2e8096e1be16a1fb25c6772b99d2ee5a849b6e552969f43e73ae1b87cc0699"
    ),
    "experiments/iter241_iter240_repository_closure/fixtures/repository_closure_known_bad.json": (
        "4b019f2f124191de816fb98f5d97be530be5a6396b0c9f075e781657341d7453"
    ),
    "experiments/iter241_iter240_repository_closure/fixtures/repository_closure_safe.json": (
        "b6cfa94634221faec002ccf487ecb4e29b580389cb312aaf878d3307c76d81e6"
    ),
    "scripts/capture_iter240_repository_closure.py": (
        "a09336866ebdf43c1f214da5b215e4a59c386c3b2745e2a9aaf742964ab293fd"
    ),
    "scripts/validate_iter240_repository_closure.py": (
        "9f54fdacca4ce334d97c60593c585873f07ec968fcffded7d82c19e649cd36ec"
    ),
    "scripts/validate_seal_registry.py": (
        "c8b393f1adbb1960cead14a9da198baae02d62c7ec65413b58fd0dec8cc5ed4d"
    ),
    "tests/test_iter240_repository_closure.py": (
        "1b2804edaa05eb049ca6eeca776f6477766b6f86c61e6ad37946c319ea1341a7"
    ),
}

EXPECTED_ENDPOINT_NAMES = [
    "pull_request_88",
    "pull_request_88_timeline",
    "pull_request_88_reviews",
    "sealed_push_run",
    "sealed_pr_run",
    "sealed_tip_check_runs",
    "gitguardian_check_run",
    "merge_commit",
    "merged_master_run",
    "merged_master_check_runs",
    "master_branch",
    "ruleset",
    "effective_rules",
]

EXPECTED_REQUEST_COUNTS = {
    "DELETE": 0,
    "GET": 13,
    "PATCH": 0,
    "POST": 0,
    "PUT": 0,
}

MERGE_FIELD_CONTRACT = (
    "merge_commit_sha must be a present object member whose value is either explicit null "
    "or the exact registered merge SHA"
)

RAW_HEADER_BYTE_CONTRACT = (
    "the exact response header-section bytes must be retained without a parsed or "
    "reserialized substitute"
)

EXPECTED_FIXTURE_CASE_IDS = {
    "repository_closure_correction_known_bad.json": [
        "omitted_member",
        "conflicting_sha_member",
    ],
    "repository_closure_correction_safe.json": [
        "explicit_null_member",
        "exact_sha_member",
    ],
}

EXPECTED_HEADER_FIXTURE_CASE_IDS = {
    "repository_closure_correction_known_bad.json": [
        "canonicalized_returned_pairs_only",
    ],
    "repository_closure_correction_safe.json": [
        "raw_header_section_bytes_retained",
    ],
}

EXPECTED_STATUS_VECTOR = {
    "all_checks_green": "contradicted",
    "attempt": "failed",
    "capture_completeness": "failed",
    "frozen_validator_acceptance": "invalid",
    "independent_ground_truth": "blocked",
    "independent_review": "blocked",
    "non_required_security_check": "failed",
    "repository_closure": "failed",
    "required_ci": "supported",
    "raw_header_byte_fidelity": "failed",
    "retry_authority": "none",
    "scientific_authority": "none",
}


class AdjudicationError(ValueError):
    """The retained correction source is malformed or differs."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AdjudicationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise AdjudicationError(f"non-finite JSON number: {value}")


def strict_json_bytes(raw: bytes, *, label: str) -> Any:
    try:
        return json.loads(
            raw,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise AdjudicationError(f"{label} is not strict JSON: {exc}") from exc


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _regular_file(path: Path, *, label: str) -> bytes:
    try:
        metadata = path.lstat()
        raw = path.read_bytes()
    except OSError as exc:
        raise AdjudicationError(f"{label} is unavailable: {path}") from exc
    if (
        not stat.S_ISREG(metadata.st_mode)
        or path.is_symlink()
        or stat.S_IMODE(metadata.st_mode) != 0o644
    ):
        raise AdjudicationError(f"{label} is not a regular nonsymlink mode-0644 file")
    return raw


def read_json(path: Path, *, label: str) -> Any:
    return strict_json_bytes(_regular_file(path, label=label), label=label)


def merge_member_adjudication(document: object) -> dict[str, object]:
    """Classify key membership separately from the member's value."""

    if not isinstance(document, dict):
        return {"accepted": False, "classification": "malformed"}
    if "merge_commit_sha" not in document:
        return {"accepted": False, "classification": "omitted"}
    value = document["merge_commit_sha"]
    if value is None:
        return {"accepted": True, "classification": "explicit_null"}
    if value == MERGE:
        return {"accepted": True, "classification": "exact_sha"}
    return {"accepted": False, "classification": "conflicting_sha"}


def raw_header_byte_adjudication(document: object) -> dict[str, object]:
    """Distinguish exact header-section bytes from parsed and reserialized pairs."""

    if not isinstance(document, dict):
        return {
            "accepted": False,
            "classification": "malformed",
            "status": {
                "capture_completeness": "failed",
                "raw_header_byte_fidelity": "failed",
            },
        }
    if (
        document.get("raw_header_section_bytes_retained") is True
        and document.get("serialization") == "identity_bytes"
        and document.get("source_api") == "raw_header_section_bytes"
    ):
        return {
            "accepted": True,
            "classification": "raw_header_section_bytes_retained",
            "status": {"raw_header_byte_fidelity": "supported"},
        }
    if (
        document.get("raw_header_section_bytes_retained") is False
        and document.get("serialization") == "canonical_json_header_pairs"
        and document.get("source_api") == "http.client.HTTPResponse.getheaders"
    ):
        return {
            "accepted": False,
            "classification": "canonicalized_returned_pairs_only",
            "status": {
                "capture_completeness": "failed",
                "raw_header_byte_fidelity": "failed",
            },
        }
    return {
        "accepted": False,
        "classification": "unproven_raw_header_bytes",
        "status": {
            "capture_completeness": "failed",
            "raw_header_byte_fidelity": "failed",
        },
    }


def fixture_failures(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    paths = (
        (
            root / SAFE_FIXTURE.relative_to(ROOT),
            "telos.iter241.repository_closure_correction.safe.v1",
        ),
        (
            root / KNOWN_BAD_FIXTURE.relative_to(ROOT),
            "telos.iter241.repository_closure_correction.known_bad.v1",
        ),
    )
    for path, schema in paths:
        fixture = read_json(path, label=f"correction fixture {path.name}")
        if not isinstance(fixture, dict) or fixture.get("schema_version") != schema:
            failures.append(f"{path.name}: schema differs")
            continue
        if fixture.get("contract") != MERGE_FIELD_CONTRACT:
            failures.append(f"{path.name}: intent contract differs")
        if fixture.get("raw_header_byte_contract") != RAW_HEADER_BYTE_CONTRACT:
            failures.append(f"{path.name}: raw-header-byte intent contract differs")
        cases = fixture.get("cases")
        if not isinstance(cases, list) or not cases:
            failures.append(f"{path.name}: cases are absent")
            continue
        observed_ids = [case.get("case_id") for case in cases if isinstance(case, dict)]
        if observed_ids != EXPECTED_FIXTURE_CASE_IDS[path.name]:
            failures.append(f"{path.name}: exact case census differs")
        for case in cases:
            if not isinstance(case, dict):
                failures.append(f"{path.name}: malformed case")
                continue
            observed = merge_member_adjudication(case.get("document"))
            if observed.get("classification") != case.get("expected_classification"):
                failures.append(f"{case.get('case_id')}: classification differs")
            if observed.get("accepted") is not case.get("expected_contract_acceptance"):
                failures.append(f"{case.get('case_id')}: acceptance differs")
        header_cases = fixture.get("header_fidelity_cases")
        if not isinstance(header_cases, list) or not header_cases:
            failures.append(f"{path.name}: header-fidelity cases are absent")
            continue
        observed_header_ids = [
            case.get("case_id") for case in header_cases if isinstance(case, dict)
        ]
        if observed_header_ids != EXPECTED_HEADER_FIXTURE_CASE_IDS[path.name]:
            failures.append(f"{path.name}: exact header-fidelity case census differs")
        for case in header_cases:
            if not isinstance(case, dict):
                failures.append(f"{path.name}: malformed header-fidelity case")
                continue
            observed = raw_header_byte_adjudication(case.get("document"))
            if observed.get("classification") != case.get("expected_classification"):
                failures.append(f"{case.get('case_id')}: header classification differs")
            if observed.get("accepted") is not case.get("expected_contract_acceptance"):
                failures.append(f"{case.get('case_id')}: header acceptance differs")
            if observed.get("status") != case.get("expected_status"):
                failures.append(f"{case.get('case_id')}: header status differs")
    return failures


def _expected_protected_records(root: Path, receipt: dict[str, Any]) -> list[dict[str, Any]]:
    expected: dict[str, str] = dict(FROZEN_INSTRUMENT_SHA256)
    expected[ATTEMPT_MARKER.relative_to(ROOT).as_posix()] = ATTEMPT_MARKER_SHA256
    expected[ORIGINAL_RECEIPT.relative_to(ROOT).as_posix()] = ORIGINAL_RECEIPT_SHA256
    expected[PREARM_RECORD.relative_to(ROOT).as_posix()] = PREARM_RECORD_SHA256
    capture = receipt.get("capture")
    if not isinstance(capture, dict):
        raise AdjudicationError("original receipt capture is malformed")
    inventory = capture.get("response_inventory")
    if not isinstance(inventory, list):
        raise AdjudicationError("original receipt inventory is malformed")
    for row in inventory:
        if not isinstance(row, dict):
            raise AdjudicationError("original receipt inventory row is malformed")
        body_path = row.get("raw_body_path")
        body_hash = row.get("raw_body_sha256")
        header_path = row.get("raw_headers_path")
        header_hash = row.get("raw_headers_sha256")
        if not all(
            isinstance(value, str) for value in (body_path, body_hash, header_path, header_hash)
        ):
            raise AdjudicationError("original receipt inventory identity is malformed")
        expected[body_path] = body_hash
        expected[header_path] = header_hash
    records: list[dict[str, Any]] = []
    for relative, expected_hash in sorted(expected.items()):
        raw = _regular_file(root / relative, label=f"protected artifact {relative}")
        records.append({"byte_count": len(raw), "path": relative, "sha256": expected_hash})
    return records


def _header_pairs(document: object, *, label: str) -> list[dict[str, str]]:
    if not isinstance(document, dict) or document.get("schema_version") != (
        "telos.iter241.github_response_headers.v1"
    ):
        raise AdjudicationError(f"{label} header document schema differs")
    rows = document.get("headers")
    if not isinstance(rows, list):
        raise AdjudicationError(f"{label} header pairs are malformed")
    result: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"name", "value"}:
            raise AdjudicationError(f"{label} header pair is malformed")
        name = row.get("name")
        value = row.get("value")
        if (
            not isinstance(name, str)
            or not isinstance(value, str)
            or any(character in name + value for character in "\r\n")
        ):
            raise AdjudicationError(f"{label} header pair is unsafe")
        result.append({"name": name, "value": value})
    return result


def _one_header(rows: list[dict[str, str]], name: str) -> str | None:
    values = [row["value"] for row in rows if row["name"].lower() == name.lower()]
    if len(values) > 1:
        raise AdjudicationError(f"response header {name} is ambiguous")
    return values[0] if values else None


def _run_matches(document: object, expected: dict[str, object]) -> bool:
    if not isinstance(document, dict):
        return False
    return all(document.get(key) == value for key, value in expected.items())


def _check_rows(document: object) -> dict[int, dict[str, Any]]:
    if not isinstance(document, dict):
        raise AdjudicationError("check-run response is malformed")
    rows = document.get("check_runs")
    if not isinstance(rows, list) or document.get("total_count") != len(rows):
        raise AdjudicationError("check-run response count differs")
    result: dict[int, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), int):
            raise AdjudicationError("check-run row is malformed")
        if row["id"] in result:
            raise AdjudicationError("check-run ID is duplicated")
        result[row["id"]] = row
    return result


def _required_check_matches(
    row: object,
    *,
    check_id: int,
    check_name: str,
    head_sha: str,
) -> bool:
    if not isinstance(row, dict):
        return False
    app = row.get("app")
    return (
        row.get("id") == check_id
        and row.get("name") == check_name
        and row.get("status") == "completed"
        and row.get("conclusion") == "success"
        and row.get("head_sha") == head_sha
        and isinstance(app, dict)
        and app.get("id") == 15368
    )


def source_failures(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    original_receipt_path = root / ORIGINAL_RECEIPT.relative_to(ROOT)
    original_receipt_raw = _regular_file(original_receipt_path, label="original receipt")
    if sha256(original_receipt_raw) != ORIGINAL_RECEIPT_SHA256:
        return ["original receipt SHA-256 differs"]
    receipt = strict_json_bytes(original_receipt_raw, label="original receipt")
    if not isinstance(receipt, dict):
        return ["original receipt is not an object"]

    marker_path = root / ATTEMPT_MARKER.relative_to(ROOT)
    marker_raw = _regular_file(marker_path, label="attempt marker")
    if sha256(marker_raw) != ATTEMPT_MARKER_SHA256:
        failures.append("attempt marker SHA-256 differs")
    marker = strict_json_bytes(marker_raw, label="attempt marker")
    if not isinstance(marker, dict):
        failures.append("attempt marker is not an object")
    else:
        marker_instruments = marker.get("instruments")
        observed_instruments = (
            {
                row.get("path"): row.get("sha256")
                for row in marker_instruments
                if isinstance(row, dict)
            }
            if isinstance(marker_instruments, list)
            else {}
        )
        if observed_instruments != FROZEN_INSTRUMENT_SHA256:
            failures.append("attempt-marker instrument inventory differs")
        if marker.get("state") != "armed_before_first_request":
            failures.append("attempt-marker state differs")
        if marker.get("authorization_head") != AUTHORIZATION_HEAD:
            failures.append("attempt-marker authorization head differs")
        if marker.get("planned_request_counts") != EXPECTED_REQUEST_COUNTS:
            failures.append("attempt-marker request counts differ")

    prearm_raw = _regular_file(
        root / PREARM_RECORD.relative_to(ROOT),
        label="pre-arm stop record",
    )
    if sha256(prearm_raw) != PREARM_RECORD_SHA256:
        failures.append("pre-arm stop record SHA-256 differs")

    try:
        protected = _expected_protected_records(root, receipt)
    except AdjudicationError as exc:
        failures.append(str(exc))
        protected = []
    for record in protected:
        relative = record["path"]
        actual = sha256(_regular_file(root / relative, label=f"protected artifact {relative}"))
        if actual != record["sha256"]:
            failures.append(f"protected artifact SHA-256 differs: {relative}")

    capture = receipt.get("capture")
    inventory = capture.get("response_inventory") if isinstance(capture, dict) else None
    if not isinstance(inventory, list) or len(inventory) != 13:
        failures.append("response inventory does not contain exactly thirteen rows")
        return failures
    if [row.get("name") for row in inventory if isinstance(row, dict)] != EXPECTED_ENDPOINT_NAMES:
        failures.append("response inventory order or names differ")
    if receipt.get("request_counts") != EXPECTED_REQUEST_COUNTS:
        failures.append("original receipt request counts differ")

    expected_raw_names = {"capture_attempt.json"}
    documents: dict[str, Any] = {}
    request_ids: list[str] = []
    response_dates: list[str] = []
    body_total = 0
    header_total = 0
    for row in inventory:
        if not isinstance(row, dict):
            failures.append("response inventory row is malformed")
            continue
        name = row.get("name")
        body_relative = row.get("raw_body_path")
        header_relative = row.get("raw_headers_path")
        if not all(isinstance(value, str) for value in (name, body_relative, header_relative)):
            failures.append("response inventory path identity is malformed")
            continue
        expected_raw_names.update({Path(body_relative).name, Path(header_relative).name})
        body_raw = _regular_file(root / body_relative, label=f"raw body {name}")
        header_raw = _regular_file(root / header_relative, label=f"header document {name}")
        body_total += len(body_raw)
        header_total += len(header_raw)
        if len(body_raw) != row.get("raw_body_byte_count") or sha256(body_raw) != row.get(
            "raw_body_sha256"
        ):
            failures.append(f"raw body binding differs: {name}")
        if len(header_raw) != row.get("raw_headers_byte_count") or sha256(header_raw) != row.get(
            "raw_headers_sha256"
        ):
            failures.append(f"header document binding differs: {name}")
        try:
            documents[name] = strict_json_bytes(body_raw, label=f"raw body {name}")
            header_document = strict_json_bytes(header_raw, label=f"header document {name}")
            if canonical_json(header_document) != header_raw:
                failures.append(f"header document is not canonical JSON: {name}")
            pairs = _header_pairs(header_document, label=name)
            request_id = _one_header(pairs, "X-GitHub-Request-Id")
            selected_version = _one_header(pairs, "x-github-api-version-selected")
            etag = _one_header(pairs, "ETag")
            date = _one_header(pairs, "Date")
            link = _one_header(pairs, "Link")
            if request_id != row.get("github_request_id"):
                failures.append(f"GitHub request ID differs: {name}")
            if selected_version != row.get("api_version_selected"):
                failures.append(f"selected API version differs: {name}")
            if etag != row.get("etag"):
                failures.append(f"ETag differs: {name}")
            if link != row.get("link"):
                failures.append(f"Link header differs: {name}")
            request_ids.append(str(request_id))
            response_dates.append(str(row.get("response_date")))
            if date is None:
                failures.append(f"Date header is absent: {name}")
            else:
                try:
                    header_date = parsedate_to_datetime(date).astimezone(timezone.utc)
                    header_date_iso = header_date.isoformat().replace("+00:00", "Z")
                except (TypeError, ValueError):
                    failures.append(f"Date header is malformed: {name}")
                else:
                    if header_date_iso != row.get("response_date"):
                        failures.append(f"Date header differs from inventory: {name}")
        except AdjudicationError as exc:
            failures.append(str(exc))
        if row.get("method") != "GET" or row.get("http_status") != 200:
            failures.append(f"request method or status differs: {name}")

    raw_root = root / RAW_ROOT.relative_to(ROOT)
    actual_raw_names = {path.name for path in raw_root.iterdir() if path.is_file()}
    if actual_raw_names != expected_raw_names:
        failures.append("retained raw artifact filename set differs")
    if body_total != 134661 or header_total != 34439:
        failures.append("retained body or header-document byte total differs")
    if len(set(request_ids)) != 13:
        failures.append("GitHub request IDs are not thirteen distinct values")
    try:
        parsed_dates = [
            datetime.fromisoformat(value.replace("Z", "+00:00")) for value in response_dates
        ]
        if parsed_dates != sorted(parsed_dates):
            failures.append("response dates are not nondecreasing")
    except ValueError:
        failures.append("response date is malformed")

    pull = documents.get("pull_request_88")
    merge_adjudication = merge_member_adjudication(pull)
    if merge_adjudication != {"accepted": False, "classification": "omitted"}:
        failures.append("retained pull-request merge_commit_sha is not the registered omission")
    if not isinstance(pull, dict):
        failures.append("pull-request document is malformed")
    else:
        head = pull.get("head")
        base = pull.get("base")
        if (
            pull.get("number") != 88
            or pull.get("state") != "closed"
            or pull.get("merged") is not True
            or pull.get("merged_at") != "2026-07-19T23:30:24Z"
            or not isinstance(head, dict)
            or head.get("sha") != SEALED_HEAD
            or not isinstance(base, dict)
            or base.get("sha") != PREDECESSOR
        ):
            failures.append("pull-request positive observations differ")

    reviews = documents.get("pull_request_88_reviews")
    if reviews != []:
        failures.append("review response is not the empty array")
    timeline = documents.get("pull_request_88_timeline")
    merge_events = (
        [row for row in timeline if isinstance(row, dict) and row.get("event") == "merged"]
        if isinstance(timeline, list)
        else []
    )
    if len(merge_events) != 1 or merge_events[0].get("commit_id") != MERGE:
        failures.append("timeline merge observation differs")
    merge = documents.get("merge_commit")
    if not isinstance(merge, dict):
        failures.append("merge-commit document is malformed")
    else:
        parents = merge.get("parents")
        tree = merge.get("tree")
        parent_shas = (
            [row.get("sha") for row in parents if isinstance(row, dict)]
            if isinstance(parents, list)
            else []
        )
        if (
            merge.get("sha") != MERGE
            or parent_shas != [PREDECESSOR, SEALED_HEAD]
            or not isinstance(tree, dict)
            or tree.get("sha") != MERGE_TREE
        ):
            failures.append("merge topology differs")

    run_expectations = {
        "sealed_push_run": {
            "id": 29707762374,
            "run_attempt": 1,
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "head_sha": SEALED_HEAD,
            "check_suite_id": 80442019864,
            "workflow_id": 309260095,
        },
        "sealed_pr_run": {
            "id": 29707871077,
            "run_attempt": 1,
            "status": "completed",
            "conclusion": "success",
            "event": "pull_request",
            "head_sha": SEALED_HEAD,
            "check_suite_id": 80442290702,
            "workflow_id": 309260095,
        },
        "merged_master_run": {
            "id": 29708028160,
            "run_attempt": 1,
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "head_sha": MERGE,
            "check_suite_id": 80442674659,
            "workflow_id": 309260095,
        },
    }
    for name, expected in run_expectations.items():
        if not _run_matches(documents.get(name), expected):
            failures.append(f"required Actions run differs: {name}")
    try:
        sealed_checks = _check_rows(documents.get("sealed_tip_check_runs"))
        merged_checks = _check_rows(documents.get("merged_master_check_runs"))
        sealed_required = {
            88247471509: "verify push py3.11",
            88247471499: "verify push py3.12",
            88247740624: "verify pull_request py3.11",
            88247740616: "verify pull_request py3.12",
        }
        merged_required = {
            88248101958: "verify push py3.11",
            88248101954: "verify push py3.12",
        }
        sealed_required_ids = list(sealed_required)
        merged_required_ids = list(merged_required)
        if set(sealed_checks) != set(sealed_required_ids + [88247740246]):
            failures.append("sealed-head check set differs")
        if set(merged_checks) != set(merged_required_ids):
            failures.append("merged-master check set differs")
        for check_id in sealed_required_ids:
            if not _required_check_matches(
                sealed_checks.get(check_id),
                check_id=check_id,
                check_name=sealed_required[check_id],
                head_sha=SEALED_HEAD,
            ):
                failures.append(f"sealed-head required check differs: {check_id}")
        for check_id in merged_required_ids:
            if not _required_check_matches(
                merged_checks.get(check_id),
                check_id=check_id,
                check_name=merged_required[check_id],
                head_sha=MERGE,
            ):
                failures.append(f"merged-master required check differs: {check_id}")
        guardian = documents.get("gitguardian_check_run")
        guardian_row = sealed_checks.get(88247740246)
        app = guardian.get("app") if isinstance(guardian, dict) else None
        output = guardian.get("output") if isinstance(guardian, dict) else None
        if (
            guardian != guardian_row
            or not isinstance(guardian, dict)
            or guardian.get("status") != "completed"
            or guardian.get("conclusion") != "failure"
            or guardian.get("head_sha") != SEALED_HEAD
            or not isinstance(app, dict)
            or app.get("id") != 46505
            or app.get("slug") != "gitguardian"
            or not isinstance(output, dict)
            or output.get("title") != "9 secrets uncovered!"
            or output.get("annotations_count") != 0
        ):
            failures.append("retained GitGuardian failure observation differs")
    except AdjudicationError as exc:
        failures.append(str(exc))

    branch = documents.get("master_branch")
    branch_commit = branch.get("commit") if isinstance(branch, dict) else None
    if (
        not isinstance(branch, dict)
        or branch.get("name") != "master"
        or branch.get("protected") is not True
        or not isinstance(branch_commit, dict)
        or branch_commit.get("sha") != AUTHORIZATION_HEAD
    ):
        failures.append("protected-branch observation differs")
    ruleset = documents.get("ruleset")
    if (
        not isinstance(ruleset, dict)
        or ruleset.get("id") != 19177100
        or ruleset.get("name") != "telos-default-branch-technical-floor-v1"
        or ruleset.get("enforcement") != "active"
        or ruleset.get("bypass_actors") != []
        or ruleset.get("current_user_can_bypass") != "never"
    ):
        failures.append("ruleset observation differs")

    projection = receipt.get("projection")
    conclusion = projection.get("conclusion") if isinstance(projection, dict) else None
    if not isinstance(conclusion, dict) or conclusion.get("repository_closure") != "supported":
        failures.append("original frozen acceptance record differs")
    frozen_validator_raw = _regular_file(
        root / "scripts/validate_iter240_repository_closure.py",
        label="frozen validator",
    )
    capture_instrument_raw = _regular_file(
        root / "scripts/capture_iter240_repository_closure.py",
        label="capture instrument",
    )
    if b'"rest_merge_commit_sha": pull.get("merge_commit_sha")' not in frozen_validator_raw:
        failures.append("frozen validator omission defect signature differs")
    if b"projection = deepcopy(safe)" not in frozen_validator_raw:
        failures.append("frozen validator safe-projection signature differs")
    if b"projection = validator.document_projection(documents)" not in capture_instrument_raw:
        failures.append("capture/validator common-mode signature differs")
    if b"header_document = _header_document(response.getheaders())" not in capture_instrument_raw:
        failures.append("capture parsed-header source signature differs")
    if b"header_raw = canonical_json(header_document)" not in capture_instrument_raw:
        failures.append("capture canonical-header serialization signature differs")
    retained_header_adjudication = raw_header_byte_adjudication(
        {
            "raw_header_section_bytes_retained": False,
            "serialization": "canonical_json_header_pairs",
            "source_api": "http.client.HTTPResponse.getheaders",
        }
    )
    if retained_header_adjudication != {
        "accepted": False,
        "classification": "canonicalized_returned_pairs_only",
        "status": {
            "capture_completeness": "failed",
            "raw_header_byte_fidelity": "failed",
        },
    }:
        failures.append("retained header-byte fidelity adjudication differs")
    return failures


def expected_correction_receipt(root: Path = ROOT) -> dict[str, Any]:
    original_receipt = read_json(
        root / ORIGINAL_RECEIPT.relative_to(ROOT),
        label="original receipt",
    )
    if not isinstance(original_receipt, dict):
        raise AdjudicationError("original receipt is not an object")
    correction_instrument_paths = [
        "experiments/iter241_iter240_repository_closure/fixtures/"
        "repository_closure_correction_known_bad.json",
        "experiments/iter241_iter240_repository_closure/fixtures/"
        "repository_closure_correction_safe.json",
        "pyproject.toml",
        "scripts/adjudicate_iter241_repository_closure_correction.py",
        "tests/test_iter241_repository_closure_correction.py",
    ]
    correction_instruments = []
    for relative in correction_instrument_paths:
        raw = _regular_file(root / relative, label=f"correction instrument {relative}")
        correction_instruments.append(
            {"byte_count": len(raw), "path": relative, "sha256": sha256(raw)}
        )
    return {
        "adjudication": EXPECTED_STATUS_VECTOR,
        "correction_instruments": correction_instruments,
        "correction_scope": "architecture_and_retained_evidence_only",
        "defect": {
            "capture_validator_common_mode": {
                "capture_calls_frozen_document_projection": True,
                "independent_projection_wording": "retracted",
                "validator_seeds_projection_from_safe_fixture": True,
            },
            "frozen_validator": {
                "acceptance_as_closure_authority": "invalid",
                "defect": "dict.get conflates an omitted merge_commit_sha member with an explicit null member",
                "path": "scripts/validate_iter240_repository_closure.py",
                "sha256": FROZEN_INSTRUMENT_SHA256[
                    "scripts/validate_iter240_repository_closure.py"
                ],
            },
            "retained_pull_request": {
                "contract_acceptance": False,
                "merge_commit_sha_classification": "omitted",
                "merge_commit_sha_member_present": False,
                "original_projection_value": None,
            },
            "retained_response_headers": {
                "capture_completeness": "failed",
                "contract_acceptance": False,
                "exact_header_section_bytes_reconstructible": False,
                "raw_header_byte_fidelity": "failed",
                "raw_header_section_bytes_retained": False,
                "retained_representation": "canonicalized_returned_header_pair_documents",
                "source_api": "http.client.HTTPResponse.getheaders",
            },
        },
        "limitations": [
            "This additive receipt corrects retained architecture and evidence interpretation; it performs no GitHub, provider, scientific, publication, or other external action.",
            "The conversational defect report that triggered reinspection is not retained as independent review or attestation.",
            "Byte digests establish retained identity only; they do not establish authorship, external chronology, semantic truth, security approval, or scientific correctness.",
            "Positive component observations do not satisfy the registered repository-closure conjunction after a required response member was omitted and the required raw header-section bytes were not retained.",
            "The armed one-shot attempt has no retry authority under iter241.",
        ],
        "original_attempt": {
            "armed_at": "2026-07-21T10:20:50Z",
            "attempt_marker_path": ATTEMPT_MARKER.relative_to(ROOT).as_posix(),
            "attempt_marker_sha256": ATTEMPT_MARKER_SHA256,
            "original_receipt_path": ORIGINAL_RECEIPT.relative_to(ROOT).as_posix(),
            "original_receipt_sha256": ORIGINAL_RECEIPT_SHA256,
            "request_counts": EXPECTED_REQUEST_COUNTS,
            "retry_authority": "none",
        },
        "protected_artifacts": _expected_protected_records(root, original_receipt),
        "retained_observations": {
            "all_checks_green": "contradicted",
            "canonicalized_header_pair_document_bytes": 34439,
            "canonicalized_header_pair_document_count": 13,
            "gitguardian": {
                "annotations_count": 0,
                "conclusion": "failure",
                "output_title": "9 secrets uncovered!",
                "status": "completed",
            },
            "header_representation": "canonicalized_returned_header_pair_documents_not_raw_wire_bytes",
            "raw_header_section_bytes_reconstructible": False,
            "raw_header_section_bytes_retained": False,
            "independent_review": "blocked",
            "merge_topology": "supported",
            "raw_json_body_bytes": 134661,
            "raw_json_body_count": 13,
            "request_ids_unique": True,
            "required_ci": "supported",
            "response_dates_nondecreasing": True,
            "review_count": 0,
            "ruleset_observation": "supported",
        },
        "repository": REPOSITORY,
        "schema_version": "telos.iter241.repository_closure_correction.v1",
        "source_review_role": "conversational_defect_report_not_independent_attestation",
    }


def validate(root: Path = ROOT, *, check_receipt: bool = True) -> list[str]:
    failures = source_failures(root) + fixture_failures(root)
    if failures or not check_receipt:
        return failures
    receipt_path = root / CORRECTION_RECEIPT.relative_to(ROOT)
    try:
        raw = _regular_file(receipt_path, label="correction receipt")
        observed = strict_json_bytes(raw, label="correction receipt")
        if raw != canonical_json(observed):
            failures.append("correction receipt is not canonical JSON")
        expected = expected_correction_receipt(root)
        if observed != expected:
            failures.append("correction receipt does not regenerate")
    except AdjudicationError as exc:
        failures.append(str(exc))
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--print-receipt", action="store_true")
    args = parser.parse_args()
    failures = validate(check_receipt=not args.print_receipt)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    if args.print_receipt:
        print(canonical_json(expected_correction_receipt()).decode(), end="")
        return 0
    print(
        "iter241 correction validates: attempt and capture completeness failed; "
        "repository closure failed; raw header byte fidelity failed; required CI supported; "
        "GitGuardian failed; retry authority none"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
