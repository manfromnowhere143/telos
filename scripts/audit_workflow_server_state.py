#!/usr/bin/env python3
"""Read-only audit of registered GitHub Actions workflow lifecycle state.

This command performs GET requests only.  It does not disable, enable,
dispatch, rerun, cancel, or delete anything.  Its result is an observation at
the time of the request, never timeless proof of server state.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any
import urllib.error
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_workflow_registry import (  # noqa: E402
    ITER204_ID,
    REGISTRY_RELATIVE,
    REPOSITORY,
    collect_failures,
    live_observation_document_failures,
    load_canonical_json,
)


API_ROOT = "https://api.github.com"
API_VERSION = "2022-11-28"
USER_AGENT = "telos-workflow-state-read-only-audit"
OBSERVATION_RELATIVE = Path(
    "experiments/iter238_claim_seal_workflow_controls/proof/raw/"
    "post_retirement_live_audit.json"
)
HEX40 = re.compile(r"^[0-9a-f]{40}$")
UTC_SECOND = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
ITER204_LATEST_FIELDS = (
    "conclusion",
    "created_at",
    "event",
    "head_branch",
    "head_sha",
    "id",
    "run_number",
    "status",
)


class LiveAuditError(RuntimeError):
    """A read-only GitHub observation could not be completed."""


class GitHubReadOnlyClient:
    def __init__(self, *, repository: str, token: str | None = None) -> None:
        if repository != REPOSITORY:
            raise LiveAuditError(f"unexpected repository: {repository}")
        self.repository = repository
        self.token = token
        self.get_count = 0

    def get(self, path: str, parameters: dict[str, object] | None = None) -> Any:
        """Perform one literal GET request against the fixed GitHub API origin."""

        query = ""
        if parameters:
            query = "?" + urllib.parse.urlencode(parameters)
        url = f"{API_ROOT}/repos/{self.repository}/{path}{query}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": API_VERSION,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(url, headers=headers, method="GET")
        self.get_count += 1
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status != 200:
                    raise LiveAuditError(
                        f"GitHub GET returned HTTP {response.status}: {path}"
                    )
                return json.load(response)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise LiveAuditError(f"GitHub GET failed for {path}: {exc}") from exc


def fetch_workflow_inventory(client: GitHubReadOnlyClient) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    declared_total: int | None = None
    for page in range(1, 11):
        payload = client.get(
            "actions/workflows",
            {"page": page, "per_page": 100},
        )
        if not isinstance(payload, dict):
            raise LiveAuditError("workflow inventory response is not an object")
        total = payload.get("total_count")
        page_rows = payload.get("workflows")
        if (
            not isinstance(total, int)
            or isinstance(total, bool)
            or total < 0
            or not isinstance(page_rows, list)
            or not all(isinstance(row, dict) for row in page_rows)
        ):
            raise LiveAuditError("workflow inventory response is malformed")
        if declared_total is None:
            declared_total = total
        elif declared_total != total:
            raise LiveAuditError("workflow inventory count changed during pagination")
        rows.extend(page_rows)
        if len(page_rows) < 100:
            break
    else:
        raise LiveAuditError("workflow inventory exceeds the bounded pagination window")
    if declared_total is None or len(rows) != declared_total:
        raise LiveAuditError("workflow inventory pagination is incomplete")
    return {"total_count": declared_total, "workflows": rows}


def fetch_iter204_run_projection(client: GitHubReadOnlyClient) -> dict[str, Any]:
    projections: dict[str, Any] = {}
    for event in ("push", "workflow_dispatch"):
        payload = client.get(
            f"actions/workflows/{ITER204_ID}/runs",
            {"event": event, "page": 1, "per_page": 1},
        )
        if not isinstance(payload, dict):
            raise LiveAuditError(f"iter204 {event} run response is not an object")
        total = payload.get("total_count")
        rows = payload.get("workflow_runs")
        if (
            not isinstance(total, int)
            or isinstance(total, bool)
            or total < 0
            or not isinstance(rows, list)
            or len(rows) > 1
        ):
            raise LiveAuditError(f"iter204 {event} run response is malformed")
        latest = None
        if rows:
            row = rows[0]
            if not isinstance(row, dict):
                raise LiveAuditError(f"iter204 {event} latest run is malformed")
            latest = {
                "conclusion": row.get("conclusion"),
                "created_at": row.get("created_at"),
                "event": row.get("event"),
                "head_branch": row.get("head_branch"),
                "head_sha": row.get("head_sha"),
                "id": row.get("id"),
                "run_number": row.get("run_number"),
                "status": row.get("status"),
            }
        projections[event] = {"latest": latest, "total_count": total}
    return projections


def _receipt_iter204(receipt: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(receipt, dict):
        return None
    rows = receipt.get("entries")
    if not isinstance(rows, list):
        return None
    matches = [
        row
        for row in rows
        if isinstance(row, dict) and row.get("workflow_id") == ITER204_ID
    ]
    return matches[0] if len(matches) == 1 else None


def audit_observation(
    *,
    registry: dict[str, Any],
    inventory: dict[str, Any],
    iter204_runs: dict[str, Any],
    pre_retirement: bool,
    receipt: dict[str, Any] | None = None,
) -> list[str]:
    failures: list[str] = []
    entries = registry.get("entries")
    if not isinstance(entries, list):
        return ["live workflow audit: registry entries are malformed"]
    expected = {
        row.get("workflow_id"): row
        for row in entries
        if isinstance(row, dict)
        and isinstance(row.get("workflow_id"), int)
        and not isinstance(row.get("workflow_id"), bool)
    }
    rows = inventory.get("workflows")
    total = inventory.get("total_count")
    if (
        not isinstance(rows, list)
        or not all(isinstance(row, dict) for row in rows)
        or total != len(rows)
    ):
        return ["live workflow audit: workflow inventory is malformed"]
    observed = {
        row.get("id"): row
        for row in rows
        if isinstance(row.get("id"), int) and not isinstance(row.get("id"), bool)
    }
    if len(observed) != len(rows):
        failures.append("live workflow audit: server workflow IDs are not unique")
    if set(observed) != set(expected):
        unknown = sorted(set(observed) - set(expected))
        absent = sorted(set(expected) - set(observed))
        failures.append(
            f"live workflow audit: server inventory differs; unknown={unknown}, absent={absent}"
        )
    for workflow_id, entry in expected.items():
        row = observed.get(workflow_id)
        if row is None:
            continue
        expected_state = entry.get("desired_server_state")
        if pre_retirement and entry.get("classification") == "historical_retired":
            expected_state = "active"
        if (
            row.get("path") != entry.get("path")
            or row.get("state") != expected_state
        ):
            failures.append(
                f"live workflow audit: identity/state differs for {entry.get('path')}: "
                f"path={row.get('path')!r}, state={row.get('state')!r}, "
                f"expected_state={expected_state!r}"
            )

    push = iter204_runs.get("push")
    dispatch = iter204_runs.get("workflow_dispatch")
    if not isinstance(push, dict) or not isinstance(dispatch, dict):
        failures.append("live workflow audit: iter204 run projection is malformed")
        return failures
    if dispatch.get("total_count") != 0 or dispatch.get("latest") is not None:
        failures.append("live workflow audit: iter204 dispatch history is not exact zero")
    if not isinstance(push.get("total_count"), int) or isinstance(
        push.get("total_count"), bool
    ):
        failures.append("live workflow audit: iter204 push count is malformed")
    if not pre_retirement:
        receipt_row = _receipt_iter204(receipt)
        latest = push.get("latest")
        latest_id = latest.get("id") if isinstance(latest, dict) else None
        if receipt_row is None:
            failures.append("live workflow audit: final iter204 receipt row is absent")
        elif (
            push.get("total_count") != receipt_row.get("post_push_run_count")
            or latest_id != receipt_row.get("post_latest_run_id")
            or receipt_row.get("post_dispatch_run_count") != 0
        ):
            failures.append(
                "live workflow audit: iter204 gained a post-retirement run or receipt differs"
            )
    return failures


def load_snapshot(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        document, _ = load_canonical_json(path)
    except (OSError, UnicodeError, ValueError) as exc:
        raise LiveAuditError(f"cannot parse snapshot {path}: {exc}") from exc
    if document.get("schema_version") == "telos.workflow_live_observation.v1":
        failures = validate_live_observation_document(document)
        if failures:
            raise LiveAuditError("; ".join(failures))
    inventory = document.get("workflow_inventory")
    iter204 = document.get("iter204_runs")
    if not isinstance(inventory, dict) or not isinstance(iter204, dict):
        raise LiveAuditError("snapshot inventory or iter204 projection is absent")
    return inventory, iter204


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_utc_second(value: object) -> bool:
    if not isinstance(value, str) or UTC_SECOND.fullmatch(value) is None:
        return False
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return False
    return True


def project_workflow_inventory(inventory: dict[str, Any]) -> dict[str, Any]:
    """Retain only the identity/state fields needed by the lifecycle audit."""

    if not isinstance(inventory, dict):
        raise LiveAuditError("cannot project malformed workflow inventory")
    total = inventory.get("total_count")
    rows = inventory.get("workflows")
    if (
        not _nonnegative_int(total)
        or not isinstance(rows, list)
        or len(rows) != total
        or not all(isinstance(row, dict) for row in rows)
    ):
        raise LiveAuditError("cannot project malformed workflow inventory")
    projected: list[dict[str, Any]] = []
    for row in rows:
        workflow_id = row.get("id")
        path = row.get("path")
        state = row.get("state")
        if (
            not _positive_int(workflow_id)
            or not isinstance(path, str)
            or not isinstance(state, str)
        ):
            raise LiveAuditError(
                "cannot project workflow inventory with malformed identity/state"
            )
        projected.append({"id": workflow_id, "path": path, "state": state})
    projected.sort(key=lambda row: row["id"])
    if len({row["id"] for row in projected}) != len(projected):
        raise LiveAuditError("cannot project duplicate workflow IDs")
    return {"total_count": total, "workflows": projected}


def project_iter204_runs(iter204_runs: dict[str, Any]) -> dict[str, Any]:
    """Retain a fixed, credential-safe iter204 run projection."""

    if not isinstance(iter204_runs, dict) or set(iter204_runs) != {
        "push",
        "workflow_dispatch",
    }:
        raise LiveAuditError("cannot project malformed iter204 event inventory")
    projected: dict[str, Any] = {}
    for event in ("push", "workflow_dispatch"):
        value = iter204_runs.get(event)
        if not isinstance(value, dict):
            raise LiveAuditError(f"cannot project malformed iter204 {event} data")
        total = value.get("total_count")
        latest = value.get("latest")
        if not _nonnegative_int(total):
            raise LiveAuditError(
                f"cannot project malformed iter204 {event} count"
            )
        if latest is None:
            if total != 0:
                raise LiveAuditError(
                    f"cannot project missing iter204 {event} latest row"
                )
            projected_latest = None
        elif isinstance(latest, dict):
            if (
                total == 0
                or not _positive_int(latest.get("id"))
                or not _positive_int(latest.get("run_number"))
                or latest.get("event") != event
                or not isinstance(latest.get("head_branch"), str)
                or not isinstance(latest.get("head_sha"), str)
                or HEX40.fullmatch(latest["head_sha"]) is None
                or not _is_utc_second(latest.get("created_at"))
                or not isinstance(latest.get("status"), str)
                or (
                    latest.get("conclusion") is not None
                    and not isinstance(latest.get("conclusion"), str)
                )
            ):
                raise LiveAuditError(
                    f"cannot project malformed iter204 {event} latest row"
                )
            projected_latest = {
                field: latest.get(field) for field in ITER204_LATEST_FIELDS
            }
        else:
            raise LiveAuditError(
                f"cannot project malformed iter204 {event} latest row"
            )
        projected[event] = {
            "latest": projected_latest,
            "total_count": total,
        }
    if projected["workflow_dispatch"] != {
        "latest": None,
        "total_count": 0,
    }:
        raise LiveAuditError(
            "cannot project nonzero iter204 workflow_dispatch history"
        )
    return projected


def build_observation(
    *,
    registry: dict[str, Any],
    registry_raw: bytes,
    inventory: dict[str, Any],
    iter204_runs: dict[str, Any],
    observed_at: str,
    head_commit: str,
    get_count: int,
) -> dict[str, Any]:
    """Build a credential-free, observation-time-scoped live-audit record."""

    if (
        registry.get("repository") != REPOSITORY
        or not _is_utc_second(observed_at)
        or not isinstance(head_commit, str)
        or HEX40.fullmatch(head_commit) is None
        or not _positive_int(get_count)
    ):
        raise LiveAuditError("live observation binding metadata is malformed")
    return {
        "schema_version": "telos.workflow_live_observation.v1",
        "repository": registry["repository"],
        "observed_at": observed_at,
        "head_commit": head_commit,
        "registry_sha256": hashlib.sha256(registry_raw).hexdigest(),
        "request_counts": {
            "get": get_count,
            "disable": 0,
            "dispatch": 0,
            "enable": 0,
            "rerun": 0,
            "delete_workflow": 0,
            "delete_run": 0,
        },
        "workflow_inventory": project_workflow_inventory(inventory),
        "iter204_runs": project_iter204_runs(iter204_runs),
        "state_scope": (
            "mutable GitHub server state observed at observed_at; "
            "not timeless proof"
        ),
    }


def validate_live_observation_document(document: dict[str, Any]) -> list[str]:
    """Validate retained live-observation metadata without contacting GitHub."""

    return live_observation_document_failures(
        document,
        label="live observation",
    )


def canonical_observation_bytes(document: dict[str, Any]) -> bytes:
    return (
        json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")


def current_head(root: Path = ROOT) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    value = result.stdout.strip()
    if result.returncode != 0 or HEX40.fullmatch(value) is None:
        raise LiveAuditError("cannot bind live observation to current Git HEAD")
    return value


def current_head_for_registry(
    registry_raw: bytes,
    root: Path = ROOT,
) -> str:
    """Bind a live observation to a HEAD-committed regular registry blob."""

    head = current_head(root)
    relative = REGISTRY_RELATIVE.as_posix()
    tree = subprocess.run(
        ["git", "ls-tree", "-z", head, "--", relative],
        cwd=root,
        capture_output=True,
        check=False,
        timeout=30,
    )
    entries = [entry for entry in tree.stdout.split(b"\0") if entry]
    if (
        tree.returncode != 0
        or len(entries) != 1
        or b"\t" not in entries[0]
    ):
        raise LiveAuditError("cannot bind live observation to registry Git entry")
    metadata, path = entries[0].split(b"\t", 1)
    fields = metadata.split()
    if (
        path != relative.encode()
        or len(fields) != 3
        or fields[0] != b"100644"
        or fields[1] != b"blob"
    ):
        raise LiveAuditError(
            "live observation registry Git entry is not a regular 100644 blob"
        )
    blob = subprocess.run(
        ["git", "show", f"{head}:{relative}"],
        cwd=root,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if blob.returncode != 0 or blob.stdout != registry_raw:
        raise LiveAuditError(
            "live observation registry bytes differ from the HEAD blob"
        )
    return head


def observation_path_is_tracked(root: Path = ROOT) -> bool:
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "--error-unmatch",
            "--",
            OBSERVATION_RELATIVE.as_posix(),
        ],
        cwd=root,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise LiveAuditError(
        "cannot determine whether the live observation path is tracked"
    )


def write_observation(document: dict[str, Any], root: Path = ROOT) -> Path:
    """Write once before sealing; never replace any prior observation."""

    validation_failures = validate_live_observation_document(document)
    if validation_failures:
        raise LiveAuditError(
            "refusing malformed live observation: "
            + "; ".join(validation_failures)
        )
    if observation_path_is_tracked(root):
        raise LiveAuditError(
            "refusing to rewrite the tracked post-retirement live observation"
        )
    destination = root / OBSERVATION_RELATIVE
    if destination.exists() or destination.is_symlink():
        raise LiveAuditError(
            "refusing to overwrite an existing post-retirement live observation"
        )
    cursor = root
    for component in OBSERVATION_RELATIVE.parent.parts:
        cursor /= component
        if cursor.is_symlink():
            raise LiveAuditError(
                "live observation parent path contains a symlink"
            )
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_observation_bytes(document)
    with tempfile.NamedTemporaryFile(
        dir=destination.parent,
        prefix=f".{destination.name}.",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        os.fchmod(handle.fileno(), 0o644)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.link(temporary, destination)
        directory = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pre-retirement",
        action="store_true",
        help="observe the frozen pre-disable active inventory",
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        help="audit a retained JSON observation without making network requests",
    )
    parser.add_argument(
        "--write-observation",
        action="store_true",
        help=(
            "after a successful post-retirement live GET audit, write the fixed "
            "credential-free observation artifact exactly once"
        ),
    )
    args = parser.parse_args()
    if args.write_observation and (args.snapshot or args.pre_retirement):
        parser.error(
            "--write-observation requires a live post-retirement observation"
        )

    registry, registry_raw = load_canonical_json(ROOT / REGISTRY_RELATIVE)
    offline_failures = collect_failures(
        pre_retirement=args.pre_retirement,
    )
    if offline_failures:
        print("live workflow audit failed: offline lifecycle registry is not green")
        for failure in offline_failures:
            print(f" - {failure}")
        return 1
    receipt: dict[str, Any] | None = None
    if not args.pre_retirement:
        receipt_relative = registry.get("retirement_receipt")
        if not isinstance(receipt_relative, str):
            print("live workflow audit failed: registry retirement receipt path is absent")
            return 1
        try:
            receipt, _ = load_canonical_json(ROOT / receipt_relative)
        except (OSError, ValueError) as exc:
            print(f"live workflow audit failed: cannot load final receipt: {exc}")
            return 1

    get_count = 0
    try:
        if args.snapshot:
            inventory, iter204_runs = load_snapshot(args.snapshot)
        else:
            token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
            client = GitHubReadOnlyClient(repository=registry["repository"], token=token)
            inventory = fetch_workflow_inventory(client)
            iter204_runs = fetch_iter204_run_projection(client)
            get_count = client.get_count
    except LiveAuditError as exc:
        print(f"live workflow audit failed: {exc}")
        return 1

    failures = audit_observation(
        registry=registry,
        inventory=inventory,
        iter204_runs=iter204_runs,
        pre_retirement=args.pre_retirement,
        receipt=receipt,
    )
    if failures:
        print("live workflow audit failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1
    if args.write_observation:
        try:
            observation = build_observation(
                registry=registry,
                registry_raw=registry_raw,
                inventory=inventory,
                iter204_runs=iter204_runs,
                observed_at=datetime.now(timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z"),
                head_commit=current_head_for_registry(registry_raw),
                get_count=get_count,
            )
            destination = write_observation(observation)
        except (OSError, LiveAuditError) as exc:
            print(f"live workflow audit failed: {exc}")
            return 1
        print(
            "live workflow audit observation written: "
            f"{destination.relative_to(ROOT)} "
            f"sha256={hashlib.sha256(destination.read_bytes()).hexdigest()}"
        )
    mode = "pre-retirement" if args.pre_retirement else "post-retirement"
    if args.snapshot:
        print(
            f"workflow snapshot audit: {inventory['total_count']} exact workflow "
            f"objects and zero iter204 dispatches pass ({mode}, GET requests=0); "
            "this audits retained bytes and is not a current server observation"
        )
    else:
        print(
            f"live workflow audit: {inventory['total_count']} exact workflow objects "
            f"and zero iter204 dispatches observed ({mode}, "
            f"GET requests={get_count}); this is mutable server state observed now, "
            "not timeless proof"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
