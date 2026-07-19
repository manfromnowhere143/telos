#!/usr/bin/env python3
"""Retire the 29 committed historical GitHub workflows, fail closed.

Without ``--execute`` this command is read-only: it verifies that the workflow
registry equals its HEAD blob, performs the complete pre-retirement GET audit,
and prints the frozen mutation order.  ``--execute`` is the explicit
acknowledgement for the one permitted mutation class: PUT ``/disable`` against
the 29 numeric IDs committed in the registry.  There is no code path for a
dispatch, rerun, enable, workflow deletion, or run deletion.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_workflow_server_state import (  # noqa: E402
    API_ROOT,
    API_VERSION,
    USER_AGENT,
    GitHubReadOnlyClient,
    audit_observation,
    fetch_iter204_run_projection,
    fetch_workflow_inventory,
)
from validate_workflow_registry import (  # noqa: E402
    HEX40,
    ITER204_ID,
    REGISTRY_RELATIVE,
    REPOSITORY,
    collect_failures,
    load_canonical_json,
)


DEFAULT_OUTPUT_ROOT = (
    ROOT / "experiments/iter238_claim_seal_workflow_controls/proof"
)
PRE_RELATIVE = Path("raw/workflow_retirement/pre_disable.json")
POST_RELATIVE = Path("raw/workflow_retirement/post_disable.json")
RECEIPT_RELATIVE = Path("workflow_retirement_receipt.json")
SNAPSHOT_SCHEMA = "telos.github_workflow_retirement_snapshot.v1"
RECEIPT_SCHEMA = "telos.workflow_retirement_receipt.v1"


class RetirementError(RuntimeError):
    """The retirement envelope or one of its fail-closed checks failed."""


class AmbiguousDisableError(RetirementError):
    """A disable request did not return an unambiguous HTTP 204."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def canonical_bytes(document: Any) -> bytes:
    return (
        json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def run_git(root: Path, arguments: list[str]) -> bytes:
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise RetirementError(f"git {' '.join(arguments)} failed: {message}")
    return result.stdout


def load_committed_registry(
    root: Path = ROOT,
) -> tuple[dict[str, Any], bytes, str]:
    """Require current registry bytes and mode to equal the exact HEAD blob."""

    registry_path = root / REGISTRY_RELATIVE
    registry, raw = load_canonical_json(registry_path)
    head_raw = run_git(root, ["show", f"HEAD:{REGISTRY_RELATIVE.as_posix()}"])
    if raw != head_raw:
        raise RetirementError("workflow registry bytes differ from the HEAD blob")
    tree = run_git(
        root,
        ["ls-tree", "HEAD", "--", REGISTRY_RELATIVE.as_posix()],
    ).decode("utf-8")
    fields = tree.strip().split()
    if len(fields) < 4 or fields[0] != "100644" or fields[1] != "blob":
        raise RetirementError("workflow registry HEAD entry is not a regular 100644 blob")
    head = run_git(root, ["rev-parse", "HEAD"]).decode("ascii").strip()
    if HEX40.fullmatch(head) is None:
        raise RetirementError("HEAD is not an exact 40-hex commit")
    return registry, raw, head


def historical_entries(registry: dict[str, Any]) -> list[dict[str, Any]]:
    rows = registry.get("entries")
    if not isinstance(rows, list):
        raise RetirementError("workflow registry entries are malformed")
    historical = [
        row
        for row in rows
        if isinstance(row, dict) and row.get("classification") == "historical_retired"
    ]
    if len(historical) != 29:
        raise RetirementError("registry does not contain exactly 29 historical workflows")
    ids = [row.get("workflow_id") for row in historical]
    if (
        any(
            not isinstance(workflow_id, int) or isinstance(workflow_id, bool)
            for workflow_id in ids
        )
        or len(ids) != len(set(ids))
        or ITER204_ID not in ids
    ):
        raise RetirementError("historical workflow IDs are malformed")
    iter204 = [row for row in historical if row["workflow_id"] == ITER204_ID]
    remainder = sorted(
        (row for row in historical if row["workflow_id"] != ITER204_ID),
        key=lambda row: row["path"],
    )
    return [iter204[0], *remainder]


class GitHubWorkflowMutationClient(GitHubReadOnlyClient):
    """GET plus one allowlisted mutation: disable a committed workflow ID."""

    def __init__(
        self,
        *,
        repository: str,
        allowed_ids: set[int],
        token: str | None = None,
    ) -> None:
        super().__init__(repository=repository, token=token)
        self.allowed_ids = frozenset(allowed_ids)
        self.disable_puts = 0

    def disable(self, workflow_id: int) -> None:
        if workflow_id not in self.allowed_ids:
            raise RetirementError(
                f"refusing disable for uncommitted workflow ID {workflow_id}"
            )
        url = (
            f"{API_ROOT}/repos/{self.repository}/actions/workflows/"
            f"{workflow_id}/disable"
        )
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": API_VERSION,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(
            url,
            data=b"",
            headers=headers,
            method="PUT",
        )
        self.disable_puts += 1
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status != 204:
                    raise AmbiguousDisableError(
                        f"disable ID {workflow_id} returned HTTP {response.status}"
                    )
        except (urllib.error.URLError, TimeoutError) as exc:
            raise AmbiguousDisableError(
                f"disable ID {workflow_id} response is ambiguous: {exc}"
            ) from exc


def fetch_workflow_object(
    client: GitHubReadOnlyClient, workflow_id: int
) -> dict[str, Any]:
    payload = client.get(f"actions/workflows/{workflow_id}")
    if not isinstance(payload, dict):
        raise RetirementError(f"workflow object {workflow_id} is malformed")
    return payload


def fetch_run_projection(
    client: GitHubReadOnlyClient, workflow_id: int
) -> dict[str, Any]:
    payload = client.get(
        f"actions/workflows/{workflow_id}/runs",
        {"page": 1, "per_page": 1},
    )
    if not isinstance(payload, dict):
        raise RetirementError(f"workflow run projection {workflow_id} is malformed")
    total = payload.get("total_count")
    rows = payload.get("workflow_runs")
    if (
        not isinstance(total, int)
        or isinstance(total, bool)
        or total < 0
        or not isinstance(rows, list)
        or len(rows) > 1
    ):
        raise RetirementError(f"workflow run projection {workflow_id} is malformed")
    latest_id = None
    if rows:
        row = rows[0]
        if not isinstance(row, dict) or (
            not isinstance(row.get("id"), int) or isinstance(row.get("id"), bool)
        ):
            raise RetirementError(f"workflow latest run {workflow_id} is malformed")
        latest_id = row["id"]
    return {
        "latest_run_id": latest_id,
        "total_run_count": total,
        "workflow_id": workflow_id,
    }


def capture_observation(
    *,
    client: GitHubReadOnlyClient,
    registry: dict[str, Any],
    registry_raw: bytes,
    source_commit: str,
    historical: list[dict[str, Any]],
    phase: str,
) -> dict[str, Any]:
    inventory = fetch_workflow_inventory(client)
    projections = [
        fetch_run_projection(client, entry["workflow_id"]) for entry in historical
    ]
    iter204_runs = fetch_iter204_run_projection(client)
    return {
        "captured_at": utc_now(),
        "get_request_count": client.get_count,
        "historical_run_projections": projections,
        "iter204_runs": iter204_runs,
        "phase": phase,
        "registry_sha256": sha256(registry_raw),
        "repository": registry["repository"],
        "schema_version": SNAPSHOT_SCHEMA,
        "source_commit": source_commit,
        "state_scope": "mutable server state observed at captured_at",
        "workflow_inventory": inventory,
    }


def _projection_by_id(snapshot: dict[str, Any]) -> dict[int, dict[str, Any]]:
    rows = snapshot.get("historical_run_projections")
    if not isinstance(rows, list):
        raise RetirementError("historical run projections are absent")
    by_id = {
        row.get("workflow_id"): row
        for row in rows
        if isinstance(row, dict)
        and isinstance(row.get("workflow_id"), int)
        and not isinstance(row.get("workflow_id"), bool)
    }
    if len(by_id) != len(rows):
        raise RetirementError("historical run projection IDs are not unique")
    return by_id


def _inventory_by_id(snapshot: dict[str, Any]) -> dict[int, dict[str, Any]]:
    inventory = snapshot.get("workflow_inventory")
    rows = inventory.get("workflows") if isinstance(inventory, dict) else None
    if not isinstance(rows, list):
        raise RetirementError("workflow inventory is absent")
    by_id = {
        row.get("id"): row
        for row in rows
        if isinstance(row, dict)
        and isinstance(row.get("id"), int)
        and not isinstance(row.get("id"), bool)
    }
    if len(by_id) != len(rows):
        raise RetirementError("workflow inventory IDs are not unique")
    return by_id


def build_receipt(
    *,
    root: Path,
    output_root: Path,
    registry: dict[str, Any],
    registry_raw: bytes,
    source_commit: str,
    historical: list[dict[str, Any]],
    pre: dict[str, Any],
    post: dict[str, Any],
    pre_bytes: bytes,
    post_bytes: bytes,
    disable_puts: int,
) -> dict[str, Any]:
    pre_projection = _projection_by_id(pre)
    post_projection = _projection_by_id(post)
    pre_inventory = _inventory_by_id(pre)
    post_inventory = _inventory_by_id(post)
    pre_iter204 = pre["iter204_runs"]
    post_iter204 = post["iter204_runs"]

    entries: list[dict[str, Any]] = []
    for entry in historical:
        workflow_id = entry["workflow_id"]
        before = pre_projection[workflow_id]
        after = post_projection[workflow_id]
        before_object = pre_inventory[workflow_id]
        after_object = post_inventory[workflow_id]
        if (
            before["total_run_count"] != after["total_run_count"]
            or before["latest_run_id"] != after["latest_run_id"]
        ):
            raise RetirementError(
                f"workflow {workflow_id} gained a run during retirement"
            )
        if (
            before_object.get("path") != entry["path"]
            or before_object.get("state") != "active"
            or after_object.get("path") != entry["path"]
            or after_object.get("state") != "disabled_manually"
        ):
            raise RetirementError(
                f"workflow {workflow_id} pre/post identity or state differs"
            )
        row = {
            "path": entry["path"],
            "post_latest_run_id": after["latest_run_id"],
            "post_state": after_object["state"],
            "post_total_run_count": after["total_run_count"],
            "pre_latest_run_id": before["latest_run_id"],
            "pre_state": before_object["state"],
            "pre_total_run_count": before["total_run_count"],
            "workflow_id": workflow_id,
        }
        if workflow_id == ITER204_ID:
            row.update(
                {
                    "post_dispatch_run_count": post_iter204["workflow_dispatch"][
                        "total_count"
                    ],
                    "post_push_run_count": post_iter204["push"]["total_count"],
                    "pre_dispatch_run_count": pre_iter204["workflow_dispatch"][
                        "total_count"
                    ],
                    "pre_push_run_count": pre_iter204["push"]["total_count"],
                }
            )
            if (
                row["pre_dispatch_run_count"] != 0
                or row["post_dispatch_run_count"] != 0
                or row["pre_push_run_count"] != row["post_push_run_count"]
            ):
                raise RetirementError("iter204 run history changed during retirement")
        entries.append(row)

    def evidence_path(relative: Path) -> str:
        path = output_root / relative
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            return (Path(output_root.name) / relative).as_posix()

    return {
        "entries": entries,
        "observed_at": post["captured_at"],
        "operation_counts": {
            "delete_run": 0,
            "delete_workflow": 0,
            "disable_puts": disable_puts,
            "dispatch": 0,
            "enable": 0,
            "rerun": 0,
        },
        "raw_observations": [
            {
                "bytes": len(pre_bytes),
                "path": evidence_path(PRE_RELATIVE),
                "sha256": sha256(pre_bytes),
            },
            {
                "bytes": len(post_bytes),
                "path": evidence_path(POST_RELATIVE),
                "sha256": sha256(post_bytes),
            },
        ],
        "registry_sha256": sha256(registry_raw),
        "repository": registry["repository"],
        "schema_version": RECEIPT_SCHEMA,
        "source_commit": source_commit,
        "state_scope": "server state observed at observed_at; not a timeless state proof",
    }


def ensure_output_absent(output_root: Path) -> None:
    for relative in (PRE_RELATIVE, POST_RELATIVE, RECEIPT_RELATIVE):
        if (output_root / relative).exists():
            raise RetirementError(
                f"refusing to overwrite retirement evidence: {output_root / relative}"
            )


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary.exists():
            temporary.unlink()


def write_success_evidence(
    *,
    output_root: Path,
    pre_bytes: bytes,
    post_bytes: bytes,
    receipt_bytes: bytes,
) -> None:
    """Require the durable pre-state, then publish post-state and receipt."""

    pre_path = output_root / PRE_RELATIVE
    if not pre_path.is_file() or pre_path.is_symlink() or pre_path.read_bytes() != pre_bytes:
        raise RetirementError("durable pre-disable snapshot differs before finalization")
    for relative in (POST_RELATIVE, RECEIPT_RELATIVE):
        if (output_root / relative).exists():
            raise RetirementError(
                f"refusing to overwrite retirement evidence: {output_root / relative}"
            )
    atomic_write(output_root / POST_RELATIVE, post_bytes)
    atomic_write(output_root / RECEIPT_RELATIVE, receipt_bytes)


def execute_retirement(
    *,
    client: GitHubWorkflowMutationClient,
    root: Path = ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    execute: bool,
) -> dict[str, Any] | None:
    registry, registry_raw, source_commit = load_committed_registry(root)
    if registry.get("repository") != REPOSITORY:
        raise RetirementError("registry repository differs")
    offline_failures = collect_failures(root=root, pre_retirement=True)
    if offline_failures:
        raise RetirementError(
            "offline pre-retirement registry failed: " + "; ".join(offline_failures)
        )
    historical = historical_entries(registry)
    committed_ids = {entry["workflow_id"] for entry in historical}
    if committed_ids != set(client.allowed_ids):
        raise RetirementError("mutation client allowlist differs from committed 29 IDs")
    ensure_output_absent(output_root)

    pre = capture_observation(
        client=client,
        registry=registry,
        registry_raw=registry_raw,
        source_commit=source_commit,
        historical=historical,
        phase="pre_disable",
    )
    pre_failures = audit_observation(
        registry=registry,
        inventory=pre["workflow_inventory"],
        iter204_runs=pre["iter204_runs"],
        pre_retirement=True,
    )
    if pre_failures:
        raise RetirementError("pre-retirement audit failed: " + "; ".join(pre_failures))
    if not execute:
        return None
    pre_bytes = canonical_bytes(pre)
    atomic_write(output_root / PRE_RELATIVE, pre_bytes)

    for entry in historical:
        workflow_id = entry["workflow_id"]
        try:
            client.disable(workflow_id)
        except AmbiguousDisableError as exc:
            observed = fetch_workflow_object(client, workflow_id)
            if (
                observed.get("id") != workflow_id
                or observed.get("path") != entry["path"]
                or observed.get("state") != "disabled_manually"
            ):
                raise RetirementError(
                    f"{exc}; resolving GET did not prove disabled_manually"
                ) from exc
        verified = fetch_workflow_object(client, workflow_id)
        if (
            verified.get("id") != workflow_id
            or verified.get("path") != entry["path"]
            or verified.get("state") != "disabled_manually"
        ):
            raise RetirementError(
                f"post-disable GET differs for committed workflow ID {workflow_id}"
            )

    if client.disable_puts != 29:
        raise RetirementError(
            f"expected exactly 29 disable PUTs, observed {client.disable_puts}"
        )
    post = capture_observation(
        client=client,
        registry=registry,
        registry_raw=registry_raw,
        source_commit=source_commit,
        historical=historical,
        phase="post_disable",
    )
    post_bytes = canonical_bytes(post)
    receipt = build_receipt(
        root=root,
        output_root=output_root,
        registry=registry,
        registry_raw=registry_raw,
        source_commit=source_commit,
        historical=historical,
        pre=pre,
        post=post,
        pre_bytes=pre_bytes,
        post_bytes=post_bytes,
        disable_puts=client.disable_puts,
    )
    final_failures = audit_observation(
        registry=registry,
        inventory=post["workflow_inventory"],
        iter204_runs=post["iter204_runs"],
        pre_retirement=False,
        receipt=receipt,
    )
    if final_failures:
        raise RetirementError("post-retirement audit failed: " + "; ".join(final_failures))
    receipt_bytes = canonical_bytes(receipt)
    write_success_evidence(
        output_root=output_root,
        pre_bytes=pre_bytes,
        post_bytes=post_bytes,
        receipt_bytes=receipt_bytes,
    )
    return receipt


def validate_cli_output_root(*, execute: bool, output_root: Path) -> None:
    if execute and output_root != DEFAULT_OUTPUT_ROOT:
        raise RetirementError(
            "--execute requires the exact registered successor proof output root: "
            f"{DEFAULT_OUTPUT_ROOT}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="acknowledge and execute exactly 29 committed workflow-disable PUTs",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="evidence root; override is intended for isolated tests",
    )
    args = parser.parse_args()
    try:
        validate_cli_output_root(execute=args.execute, output_root=args.output_root)
        registry, _, _ = load_committed_registry(ROOT)
        historical = historical_entries(registry)
        allowed_ids = {entry["workflow_id"] for entry in historical}
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if args.execute and not token:
            raise RetirementError(
                "--execute requires GITHUB_TOKEN or GH_TOKEN for the disable API"
            )
        client = GitHubWorkflowMutationClient(
            repository=registry["repository"],
            allowed_ids=allowed_ids,
            token=token,
        )
        receipt = execute_retirement(
            client=client,
            root=ROOT,
            output_root=args.output_root,
            execute=args.execute,
        )
    except (OSError, ValueError, RetirementError) as exc:
        print(f"historical workflow retirement failed: {exc}")
        return 1
    if not args.execute:
        ordered = [entry["workflow_id"] for entry in historical]
        print(
            "historical workflow retirement dry run: pre-retirement GET audit passed; "
            f"no files or server state changed; committed disable order={ordered}"
        )
        return 0
    assert receipt is not None
    print(
        "historical workflow retirement complete: 29 committed disable PUTs, "
        "29 post-disable GET verifications, zero dispatch/rerun/enable/delete "
        "operations; canonical receipt written last"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
