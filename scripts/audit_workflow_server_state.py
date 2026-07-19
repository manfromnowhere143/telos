#!/usr/bin/env python3
"""Read-only audit of registered GitHub Actions workflow lifecycle state.

This command performs GET requests only.  It does not disable, enable,
dispatch, rerun, cancel, or delete anything.  Its result is an observation at
the time of the request, never timeless proof of server state.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
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
    load_canonical_json,
)


API_ROOT = "https://api.github.com"
API_VERSION = "2022-11-28"
USER_AGENT = "telos-workflow-state-read-only-audit"


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
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise LiveAuditError(f"cannot parse snapshot {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise LiveAuditError("snapshot root is not an object")
    inventory = document.get("workflow_inventory")
    iter204 = document.get("iter204_runs")
    if not isinstance(inventory, dict) or not isinstance(iter204, dict):
        raise LiveAuditError("snapshot inventory or iter204 projection is absent")
    return inventory, iter204


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
    args = parser.parse_args()

    registry, _ = load_canonical_json(ROOT / REGISTRY_RELATIVE)
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
    mode = "pre-retirement" if args.pre_retirement else "post-retirement"
    print(
        f"live workflow audit: {inventory['total_count']} exact workflow objects and "
        f"zero iter204 dispatches observed ({mode}, GET requests={get_count}); "
        "this is mutable server state observed now, not timeless proof"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
