#!/usr/bin/env python3
"""Validate the offline workflow lifecycle registry.

The default mode is the completed iter238 contract: the current gate, seal
links, retirement receipt, and desired disabled states must all be evidenced.
``--pre-retirement`` is a deliberately narrower staging mode.  It validates
the frozen IDs, file bytes, trigger inventory, and default-deny
classifications before the separately authorized GitHub disable operation.
It does not claim that the desired server states have already been observed.
"""

from __future__ import annotations

import argparse
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_RELATIVE = Path("mission/workflow_registry.json")
CURRENT_RELATIVE = Path("mission/current.json")
ITER238_GATE = "experiments/iter238_claim_seal_workflow_controls/HYPOTHESIS.md"
REPOSITORY = "manfromnowhere143/telos"
SCHEMA = "telos.workflow_registry.v1"
RECEIPT_SCHEMA = "telos.workflow_retirement_receipt.v1"
SNAPSHOT_SCHEMA = "telos.github_workflow_retirement_snapshot.v1"
HISTORICAL_SEAL = "iter237-merged-historical-baseline"
ITER204_PATH = ".github/workflows/iter204-execute.yml"
ITER204_ID = 314113289
ITER204_SHA256 = "84f7f8b228624ff7244991e317e7f8146a6aacd93f803c1df983b6cceae4deb4"
PLATFORM_PATH = "dynamic/dependabot/update-graph"
PLATFORM_ID = 309260104
RETIREMENT_PROOF_ROOT = Path(
    "experiments/iter238_claim_seal_workflow_controls/proof"
)
PRE_OBSERVATION_RELATIVE = (
    RETIREMENT_PROOF_ROOT / "raw/workflow_retirement/pre_disable.json"
)
POST_OBSERVATION_RELATIVE = (
    RETIREMENT_PROOF_ROOT / "raw/workflow_retirement/post_disable.json"
)
LIVE_OBSERVATION_RELATIVE = (
    RETIREMENT_PROOF_ROOT / "raw/post_retirement_live_audit.json"
)
ITER238_RESULT_RELATIVE = Path(
    "experiments/iter238_claim_seal_workflow_controls/RESULT.md"
)
SEAL_REGISTRY_RELATIVE = Path("mission/seal_registry.json")
LIVE_OBSERVATION_SCHEMA = "telos.workflow_live_observation.v1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
UTC_SECOND = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
RUNNER_EXPRESSION = re.compile(r"\$\{\{[^}]*\brunner\.", re.IGNORECASE)
EXPECTED_CLASSES = {
    "active_control",
    "authorized_one_shot",
    "historical_retired",
    "platform_service",
}
ENTRY_KEYS = {
    "classification",
    "declared_triggers",
    "desired_server_state",
    "execution_authority",
    "known_invalidity",
    "path",
    "retirement_receipt",
    "seal_reference",
    "sha256",
    "source_kind",
    "workflow_id",
}
REGISTRY_KEYS = {
    "active_gate",
    "default_policy",
    "entries",
    "repository",
    "retirement_receipt",
    "schema_version",
    "seal_registry",
    "updated",
}
SNAPSHOT_KEYS = {
    "captured_at",
    "get_request_count",
    "historical_run_projections",
    "iter204_runs",
    "phase",
    "registry_sha256",
    "repository",
    "schema_version",
    "source_commit",
    "state_scope",
    "workflow_inventory",
}
RUN_PROJECTION_KEYS = {
    "latest_run_id",
    "total_run_count",
    "workflow_id",
}
ITER204_LATEST_KEYS = {
    "conclusion",
    "created_at",
    "event",
    "head_branch",
    "head_sha",
    "id",
    "run_number",
    "status",
}
LIVE_OBSERVATION_KEYS = {
    "head_commit",
    "iter204_runs",
    "observed_at",
    "registry_sha256",
    "repository",
    "request_counts",
    "schema_version",
    "state_scope",
    "workflow_inventory",
}
LIVE_ZERO_REQUESTS = {
    "delete_run",
    "delete_workflow",
    "disable",
    "dispatch",
    "enable",
    "rerun",
}


class RegistryError(ValueError):
    """A strict JSON or GitHub-workflow document is ambiguous."""


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_canonical_json_bytes(
    raw: bytes, *, label: str
) -> dict[str, Any]:
    """Load canonical JSON bytes while refusing duplicate or non-finite values."""

    duplicates: list[str] = []

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                duplicates.append(key)
            value[key] = item
        return value

    try:
        document = json.loads(
            raw,
            object_pairs_hook=unique,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
        )
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise RegistryError(f"cannot parse strict JSON {label}: {exc}") from exc
    if duplicates:
        raise RegistryError(
            f"duplicate JSON keys in {label}: {sorted(set(duplicates))}"
        )
    if not isinstance(document, dict):
        raise RegistryError(f"JSON root is not an object: {label}")
    rendered = (json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    if raw != rendered:
        raise RegistryError(f"JSON is not canonical: {label}")
    return document


def load_canonical_json(path: Path) -> tuple[dict[str, Any], bytes]:
    """Load a canonical JSON object while refusing duplicate keys."""

    raw = path.read_bytes()
    document = load_canonical_json_bytes(raw, label=str(path))
    return document, raw


def load_unique_json_object(path: Path) -> dict[str, Any]:
    """Load another guard's JSON without imposing this registry's key order."""

    raw = path.read_bytes()
    duplicates: list[str] = []

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                duplicates.append(key)
            value[key] = item
        return value

    try:
        document = json.loads(
            raw,
            object_pairs_hook=unique,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
        )
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise RegistryError(f"cannot parse strict JSON {path}: {exc}") from exc
    if duplicates:
        raise RegistryError(f"duplicate JSON keys in {path}: {sorted(set(duplicates))}")
    if not isinstance(document, dict):
        raise RegistryError(f"JSON root is not an object: {path}")
    return document


def _is_int(value: object, *, minimum: int = 0) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value >= minimum
    )


def _parse_utc_second(value: object) -> datetime | None:
    if not isinstance(value, str) or UTC_SECOND.fullmatch(value) is None:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None


def _is_iso_date(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%Y-%m-%d") == value
    except ValueError:
        return False


def regular_0644_failures(
    *,
    root: Path,
    relative: Path,
    label: str,
) -> list[str]:
    """Require a nonsymlink regular worktree file and canonical Git index mode."""

    path = root / relative
    try:
        metadata = path.lstat()
    except OSError as exc:
        return [f"{label}: cannot inspect current path: {exc}"]
    failures: list[str] = []
    if (
        not stat.S_ISREG(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o644
    ):
        failures.append(
            f"{label}: current path is not a nonsymlink regular 0644 file"
        )

    repository_probe = _git(root, "rev-parse", "--is-inside-work-tree")
    if (
        repository_probe.returncode != 0
        or repository_probe.stdout.strip() != b"true"
    ):
        return failures

    result = _git(
        root,
        "ls-files",
        "-s",
        "-z",
        "--",
        relative.as_posix(),
    )
    if result.returncode != 0:
        failures.append(f"{label}: cannot inspect Git index mode")
        return failures
    entries = [entry for entry in result.stdout.split(b"\0") if entry]
    if len(entries) != 1 or b"\t" not in entries[0]:
        failures.append(f"{label}: Git index entry is absent or ambiguous")
        return failures
    metadata_raw, observed_path = entries[0].split(b"\t", 1)
    fields = metadata_raw.split()
    if (
        observed_path != relative.as_posix().encode()
        or len(fields) != 3
        or fields[0] != b"100644"
    ):
        failures.append(f"{label}: Git index entry is not mode 100644")
    return failures


def _git(
    root: Path,
    *arguments: str,
) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            ["git", *arguments],
            cwd=root,
            capture_output=True,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RegistryError(
            f"git command failed: {' '.join(arguments)}"
        ) from exc


def _git_checked(root: Path, *arguments: str) -> bytes:
    result = _git(root, *arguments)
    if result.returncode != 0:
        diagnostic = (result.stderr or result.stdout).decode(
            "utf-8", errors="replace"
        ).strip()
        raise RegistryError(
            f"git command failed: {' '.join(arguments)}"
            + (f": {diagnostic}" if diagnostic else "")
        )
    return result.stdout


def load_source_registry(
    root: Path, source_commit: str
) -> tuple[dict[str, Any], bytes]:
    """Load the exact regular registry blob that authorized retirement."""

    if HEX40.fullmatch(source_commit) is None:
        raise RegistryError("workflow retirement source_commit is not 40-hex")
    ancestry = _git(root, "merge-base", "--is-ancestor", source_commit, "HEAD")
    if ancestry.returncode != 0:
        raise RegistryError(
            "workflow retirement source_commit is not an ancestor of HEAD"
        )

    relative = REGISTRY_RELATIVE.as_posix()
    tree = _git_checked(
        root,
        "ls-tree",
        "-z",
        source_commit,
        "--",
        relative,
    )
    entries = [entry for entry in tree.split(b"\0") if entry]
    if len(entries) != 1 or b"\t" not in entries[0]:
        raise RegistryError(
            "workflow retirement source registry Git entry is absent or ambiguous"
        )
    metadata, path = entries[0].split(b"\t", 1)
    fields = metadata.split()
    if (
        path != relative.encode()
        or len(fields) != 3
        or fields[0] != b"100644"
        or fields[1] != b"blob"
    ):
        raise RegistryError(
            "workflow retirement source registry is not a regular 100644 Git blob"
        )

    raw = _git_checked(root, "show", f"{source_commit}:{relative}")
    return (
        load_canonical_json_bytes(
            raw,
            label=f"{source_commit[:12]}:{relative}",
        ),
        raw,
    )


def introducing_blob_failures(
    *,
    root: Path,
    relative: Path,
    current_raw: bytes,
    label: str,
    expected_parent: str | None = None,
) -> list[str]:
    """Require current evidence bytes to equal their unique introducing blob."""

    history = _git(
        root,
        "log",
        "--follow",
        "--diff-filter=A",
        "--format=%H",
        "--",
        relative.as_posix(),
    )
    if history.returncode != 0:
        return [f"{label}: cannot discover the introducing commit"]
    commits = [
        line.decode("ascii", errors="replace")
        for line in history.stdout.splitlines()
        if line
    ]
    if len(commits) != 1 or HEX40.fullmatch(commits[0]) is None:
        return [f"{label}: introducing commit is absent or ambiguous"]
    introducing_commit = commits[0]

    tree = _git_checked(
        root,
        "ls-tree",
        "-z",
        introducing_commit,
        "--",
        relative.as_posix(),
    )
    entries = [entry for entry in tree.split(b"\0") if entry]
    if len(entries) != 1 or b"\t" not in entries[0]:
        return [f"{label}: introducing Git entry is absent or ambiguous"]
    metadata, path = entries[0].split(b"\t", 1)
    fields = metadata.split()
    if (
        path != relative.as_posix().encode()
        or len(fields) != 3
        or fields[0] != b"100644"
        or fields[1] != b"blob"
    ):
        return [f"{label}: introducing Git entry is not a regular 100644 blob"]
    source_raw = _git_checked(
        root,
        "show",
        f"{introducing_commit}:{relative.as_posix()}",
    )
    if current_raw != source_raw:
        return [f"{label}: current bytes differ from the introducing Git blob"]
    if expected_parent is None:
        return []

    parent_line = _git_checked(
        root,
        "rev-list",
        "--parents",
        "-n",
        "1",
        introducing_commit,
    ).decode("ascii", errors="strict").split()
    if (
        len(parent_line) != 2
        or parent_line[0] != introducing_commit
        or parent_line[1] != expected_parent
    ):
        return [
            f"{label}: introducing commit is not the single-parent direct "
            "child of the recorded observation head"
        ]
    return []


def registry_evolution_failures(
    source: dict[str, Any],
    current: dict[str, Any],
) -> list[str]:
    """Freeze authority while allowing the current pointer and CI digest to evolve."""

    failures: list[str] = []
    mutable_pointer_fields = {"active_gate", "updated"}
    source_top = {
        key: value
        for key, value in source.items()
        if key != "entries" and key not in mutable_pointer_fields
    }
    current_top = {
        key: value
        for key, value in current.items()
        if key != "entries" and key not in mutable_pointer_fields
    }
    if source_top != current_top:
        failures.append(
            "workflow registry: post-retirement top-level evolution exceeds "
            "the current-pointer and active ci.yml digest allowances"
        )
    if source.get("active_gate") != ITER238_GATE:
        failures.append(
            "workflow registry: retirement source active gate is not iter238"
        )

    source_rows = source.get("entries")
    current_rows = current.get("entries")
    if not isinstance(source_rows, list) or not all(
        isinstance(row, dict) for row in source_rows
    ):
        return failures + [
            "workflow registry: retirement source entries are malformed"
        ]
    if not isinstance(current_rows, list) or not all(
        isinstance(row, dict) for row in current_rows
    ):
        return failures + ["workflow registry: current entries are malformed"]

    source_paths = [row.get("path") for row in source_rows]
    current_paths = [row.get("path") for row in current_rows]
    if not all(isinstance(path, str) for path in source_paths + current_paths):
        return failures + [
            "workflow registry: post-retirement entry paths are malformed"
        ]
    if (
        len(source_paths) != len(set(source_paths))
        or source_paths != current_paths
    ):
        return failures + [
            "workflow registry: post-retirement entry inventory or order changed"
        ]

    source_historical = [
        row
        for row in source_rows
        if row.get("classification") == "historical_retired"
    ]
    source_platform = [
        row
        for row in source_rows
        if row.get("classification") == "platform_service"
    ]
    source_active = [
        row
        for row in source_rows
        if row.get("classification") == "active_control"
    ]
    if (
        len(source_rows) != 31
        or len(source_historical) != 29
        or len(source_platform) != 1
        or len(source_active) != 1
        or any(
            row.get("classification")
            not in {"active_control", "historical_retired", "platform_service"}
            for row in source_rows
        )
        or source_active[0].get("path") != ".github/workflows/ci.yml"
    ):
        failures.append(
            "workflow registry: retirement source classification inventory differs"
        )

    current_by_path = {
        row["path"]: row
        for row in current_rows
        if isinstance(row.get("path"), str)
    }
    for source_row in source_historical + source_platform:
        path = source_row.get("path")
        current_row = current_by_path.get(path)
        if current_row != source_row:
            failures.append(
                "workflow registry: retirement-authorized immutable entry changed: "
                f"{path}"
            )

    if len(source_active) == 1:
        source_ci = source_active[0]
        current_ci = current_by_path.get(".github/workflows/ci.yml")
        if not isinstance(current_ci, dict):
            failures.append(
                "workflow registry: active ci.yml entry is absent after retirement"
            )
        else:
            normalized_source = copy.deepcopy(source_ci)
            normalized_source["sha256"] = current_ci.get("sha256")
            if normalized_source != current_ci:
                failures.append(
                    "workflow registry: active ci.yml evolution exceeds "
                    "the SHA-256 digest-only allowance"
                )
    return failures


def registry_provenance_failures(
    *,
    root: Path,
    current_registry: dict[str, Any],
    source_commit: str,
    expected_registry_sha256: str,
) -> list[str]:
    """Bind retirement evidence to source Git bytes and controlled evolution."""

    try:
        source_registry, source_raw = load_source_registry(root, source_commit)
    except RegistryError as exc:
        return [f"workflow retirement receipt: {exc}"]
    failures: list[str] = []
    observed_digest = sha256(source_raw)
    if expected_registry_sha256 != observed_digest:
        failures.append(
            "workflow retirement receipt: registry digest does not match "
            "the source_commit Git blob"
        )
    failures.extend(
        registry_evolution_failures(source_registry, current_registry)
    )
    return failures


def live_observation_document_failures(
    document: dict[str, Any],
    *,
    label: str = "retained live workflow observation",
) -> list[str]:
    """Validate the credential-free live-observation projection itself."""

    failures: list[str] = []
    if set(document) != LIVE_OBSERVATION_KEYS:
        failures.append(f"{label}: top-level fields differ")
    if document.get("schema_version") != LIVE_OBSERVATION_SCHEMA:
        failures.append(f"{label}: schema_version differs")
    if document.get("repository") != REPOSITORY:
        failures.append(f"{label}: repository differs")
    if _parse_utc_second(document.get("observed_at")) is None:
        failures.append(f"{label}: observed_at is not an exact UTC timestamp")
    head_commit = document.get("head_commit")
    if not isinstance(head_commit, str) or HEX40.fullmatch(head_commit) is None:
        failures.append(f"{label}: head_commit is not 40-hex")
    registry_digest = document.get("registry_sha256")
    if (
        not isinstance(registry_digest, str)
        or HEX64.fullmatch(registry_digest) is None
    ):
        failures.append(f"{label}: registry_sha256 is not 64-hex")
    if document.get("state_scope") != (
        "mutable GitHub server state observed at observed_at; not timeless proof"
    ):
        failures.append(f"{label}: mutable state scope differs")

    counts = document.get("request_counts")
    if (
        not isinstance(counts, dict)
        or set(counts) != {*LIVE_ZERO_REQUESTS, "get"}
        or not _is_int(counts.get("get"), minimum=1)
        or any(
            not _is_int(counts.get(name)) or counts.get(name) != 0
            for name in LIVE_ZERO_REQUESTS
        )
    ):
        failures.append(f"{label}: request counts differ")

    inventory = document.get("workflow_inventory")
    if not isinstance(inventory, dict) or set(inventory) != {
        "total_count",
        "workflows",
    }:
        failures.append(f"{label}: workflow inventory fields differ")
    else:
        rows = inventory.get("workflows")
        total = inventory.get("total_count")
        if (
            not _is_int(total)
            or not isinstance(rows, list)
            or len(rows) != total
            or not all(isinstance(row, dict) for row in rows)
        ):
            failures.append(f"{label}: workflow inventory is malformed")
        else:
            for row in rows:
                if (
                    set(row) != {"id", "path", "state"}
                    or not _is_int(row.get("id"), minimum=1)
                    or not isinstance(row.get("path"), str)
                    or not isinstance(row.get("state"), str)
                ):
                    failures.append(
                        f"{label}: workflow inventory row is malformed"
                    )
            ids = [
                row.get("id")
                for row in rows
                if _is_int(row.get("id"), minimum=1)
            ]
            if len(ids) != len(set(ids)):
                failures.append(f"{label}: workflow IDs are not unique")
            if len(ids) == len(rows) and ids != sorted(ids):
                failures.append(
                    f"{label}: workflow inventory projection is not sorted"
                )

    iter204 = document.get("iter204_runs")
    if not isinstance(iter204, dict) or set(iter204) != {
        "push",
        "workflow_dispatch",
    }:
        failures.append(f"{label}: iter204 run projection fields differ")
    else:
        for event in ("push", "workflow_dispatch"):
            projection = iter204.get(event)
            if not isinstance(projection, dict) or set(projection) != {
                "latest",
                "total_count",
            }:
                failures.append(
                    f"{label}: iter204 {event} projection is malformed"
                )
                continue
            total = projection.get("total_count")
            latest = projection.get("latest")
            if not _is_int(total):
                failures.append(
                    f"{label}: iter204 {event} count is malformed"
                )
            if latest is None:
                if total != 0:
                    failures.append(
                        f"{label}: iter204 {event} latest row is absent"
                    )
                continue
            if not isinstance(latest, dict) or set(latest) != ITER204_LATEST_KEYS:
                failures.append(
                    f"{label}: iter204 {event} latest row fields differ"
                )
                continue
            if (
                total == 0
                or not _is_int(latest.get("id"), minimum=1)
                or not _is_int(latest.get("run_number"), minimum=1)
                or latest.get("event") != event
                or not isinstance(latest.get("head_branch"), str)
                or not isinstance(latest.get("head_sha"), str)
                or HEX40.fullmatch(latest["head_sha"]) is None
                or _parse_utc_second(latest.get("created_at")) is None
                or not isinstance(latest.get("status"), str)
                or (
                    latest.get("conclusion") is not None
                    and not isinstance(latest.get("conclusion"), str)
                )
            ):
                failures.append(
                    f"{label}: iter204 {event} latest row is malformed"
                )
        if iter204.get("workflow_dispatch") != {
            "latest": None,
            "total_count": 0,
        }:
            failures.append(
                f"{label}: iter204 workflow_dispatch history is not exact zero"
            )
    return failures


def _iter238_completion_evidence_present(root: Path) -> bool:
    """Return whether RESULT or a committed/staged completion seal is present."""

    try:
        (root / ITER238_RESULT_RELATIVE).lstat()
    except FileNotFoundError:
        pass
    except OSError:
        return True
    else:
        return True

    result_index = _git(
        root,
        "ls-files",
        "--error-unmatch",
        "--",
        ITER238_RESULT_RELATIVE.as_posix(),
    )
    if result_index.returncode == 0:
        return True

    try:
        seal = load_unique_json_object(root / SEAL_REGISTRY_RELATIVE)
    except (OSError, RegistryError):
        return False
    records = seal.get("records")
    if not isinstance(records, list):
        return False
    iter238_path = ITER238_RESULT_RELATIVE.parent.as_posix()
    for record in records:
        if (
            not isinstance(record, dict)
            or record.get("record_type") != "successor_path_snapshot"
        ):
            continue
        protected_sets = record.get("protected_sets")
        if not isinstance(protected_sets, list):
            continue
        for protected in protected_sets:
            selector = (
                protected.get("selector")
                if isinstance(protected, dict)
                else None
            )
            if (
                isinstance(selector, dict)
                and selector.get("kind") == "tree"
                and selector.get("path") == iter238_path
            ):
                return True
    return False


def retained_live_observation_failures(
    *,
    root: Path,
    registry: dict[str, Any],
) -> list[str]:
    """Re-verify a retained live observation against Git and current authority."""

    label = "retained live workflow observation"
    path = root / LIVE_OBSERVATION_RELATIVE
    repository_probe = _git(root, "rev-parse", "--is-inside-work-tree")
    in_git_repository = (
        repository_probe.returncode == 0
        and repository_probe.stdout.strip() == b"true"
    )
    tracked_probe = _git(
        root,
        "ls-files",
        "--error-unmatch",
        "--",
        LIVE_OBSERVATION_RELATIVE.as_posix(),
    )
    if tracked_probe.returncode not in {0, 1}:
        if in_git_repository:
            return [f"{label}: cannot inspect Git tracking state"]
        tracked = False
    else:
        tracked = tracked_probe.returncode == 0
    required = _iter238_completion_evidence_present(root) or tracked
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        if required:
            return [
                f"{label}: required completed-evidence artifact is absent: "
                f"{LIVE_OBSERVATION_RELATIVE.as_posix()}"
            ]
        return []
    except OSError as exc:
        return [f"{label}: cannot inspect fixed artifact path: {exc}"]

    failures: list[str] = []
    if required and in_git_repository and not tracked:
        failures.append(
            f"{label}: completed evidence requires a staged or tracked artifact"
        )
    if (
        not stat.S_ISREG(metadata.st_mode)
        or path.is_symlink()
        or stat.S_IMODE(metadata.st_mode) != 0o644
    ):
        failures.append(
            f"{label}: fixed artifact is not a nonsymlink regular 0644 file"
        )
        return failures

    index = _git(
        root,
        "ls-files",
        "--stage",
        "-z",
        "--",
        LIVE_OBSERVATION_RELATIVE.as_posix(),
    )
    if index.returncode != 0:
        failures.append(f"{label}: cannot inspect Git index mode")
    else:
        entries = [entry for entry in index.stdout.split(b"\0") if entry]
        if entries:
            try:
                index_metadata, observed_path = entries[0].split(b"\t", 1)
                mode, _, stage = index_metadata.decode("ascii").split()
            except (UnicodeDecodeError, ValueError):
                mode = ""
                stage = ""
                observed_path = b""
            if (
                len(entries) != 1
                or observed_path
                != LIVE_OBSERVATION_RELATIVE.as_posix().encode()
                or mode != "100644"
                or stage != "0"
            ):
                failures.append(
                    f"{label}: Git index entry is not one stage-0 mode-100644 blob"
                )

    try:
        observation, observation_raw = load_canonical_json(path)
    except (OSError, RegistryError) as exc:
        return failures + [f"{label}: {exc}"]
    failures.extend(live_observation_document_failures(observation, label=label))

    head = observation.get("head_commit")
    registry_digest = observation.get("registry_sha256")
    if in_git_repository:
        head_tree = _git(
            root,
            "ls-tree",
            "-z",
            "HEAD",
            "--",
            LIVE_OBSERVATION_RELATIVE.as_posix(),
        )
        if head_tree.returncode != 0:
            failures.append(
                f"{label}: cannot inspect committed artifact provenance"
            )
        elif head_tree.stdout:
            try:
                failures.extend(
                    introducing_blob_failures(
                        root=root,
                        relative=LIVE_OBSERVATION_RELATIVE,
                        current_raw=observation_raw,
                        label=label,
                        expected_parent=(
                            head
                            if isinstance(head, str)
                            and HEX40.fullmatch(head) is not None
                            else None
                        ),
                    )
                )
            except (RegistryError, UnicodeError) as exc:
                failures.append(
                    f"{label}: cannot verify introducing Git blob: {exc}"
                )

    head_registry: dict[str, Any] | None = None
    if isinstance(head, str) and HEX40.fullmatch(head) is not None:
        ancestry = _git(root, "merge-base", "--is-ancestor", head, "HEAD")
        if ancestry.returncode != 0:
            failures.append(
                f"{label}: recorded head_commit is not an ancestor of HEAD"
            )
        relative = REGISTRY_RELATIVE.as_posix()
        tree = _git(root, "ls-tree", "-z", head, "--", relative)
        tree_entries = [
            entry for entry in tree.stdout.split(b"\0") if entry
        ]
        valid_tree_entry = False
        if (
            tree.returncode == 0
            and len(tree_entries) == 1
            and b"\t" in tree_entries[0]
        ):
            tree_metadata, observed_path = tree_entries[0].split(b"\t", 1)
            fields = tree_metadata.split()
            valid_tree_entry = (
                observed_path == relative.encode()
                and len(fields) == 3
                and fields[0] == b"100644"
                and fields[1] == b"blob"
            )
        if not valid_tree_entry:
            failures.append(
                f"{label}: recorded head lacks a regular 100644 "
                f"{relative} blob"
            )
        else:
            blob = _git(root, "show", f"{head}:{relative}")
            if blob.returncode != 0:
                failures.append(
                    f"{label}: cannot read recorded workflow-registry blob"
                )
            else:
                if (
                    isinstance(registry_digest, str)
                    and HEX64.fullmatch(registry_digest) is not None
                    and sha256(blob.stdout) != registry_digest
                ):
                    failures.append(
                        f"{label}: registry_sha256 differs from the recorded "
                        "head blob"
                    )
                try:
                    head_registry = load_canonical_json_bytes(
                        blob.stdout,
                        label=f"{head[:12]}:{relative}",
                    )
                except RegistryError as exc:
                    failures.append(
                        f"{label}: recorded workflow-registry blob is invalid: "
                        f"{exc}"
                    )
    if head_registry is not None:
        if head_registry.get("repository") != registry.get("repository"):
            failures.append(
                f"{label}: recorded registry repository differs from current authority"
            )
        failures.extend(
            f"{label}: recorded-head {failure}"
            for failure in registry_evolution_failures(
                head_registry,
                registry,
            )
        )

    observed_inventory = observation.get("workflow_inventory")
    observed_rows = (
        observed_inventory.get("workflows")
        if isinstance(observed_inventory, dict)
        else None
    )

    def compare_inventory(
        authority: dict[str, Any],
        *,
        authority_label: str,
    ) -> None:
        registered_rows = authority.get("entries")
        if not isinstance(registered_rows, list) or not isinstance(
            observed_rows,
            list,
        ):
            failures.append(
                f"{label}: cannot compare workflow inventory with "
                f"{authority_label} lifecycle registry"
            )
            return
        expected = {
            row.get("workflow_id"): row
            for row in registered_rows
            if isinstance(row, dict)
            and _is_int(row.get("workflow_id"), minimum=1)
        }
        observed = {
            row.get("id"): row
            for row in observed_rows
            if isinstance(row, dict) and _is_int(row.get("id"), minimum=1)
        }
        if len(expected) != len(registered_rows) or set(observed) != set(expected):
            failures.append(
                f"{label}: workflow inventory IDs differ from "
                f"{authority_label} lifecycle registry"
            )
        for workflow_id in sorted(set(observed) & set(expected)):
            row = observed[workflow_id]
            entry = expected[workflow_id]
            if (
                row.get("path") != entry.get("path")
                or row.get("state") != entry.get("desired_server_state")
            ):
                failures.append(
                    f"{label}: identity/state differs from {authority_label} "
                    "lifecycle registry for "
                    f"{entry.get('path')}"
                )

    if head_registry is not None:
        compare_inventory(head_registry, authority_label="recorded-head")
    compare_inventory(registry, authority_label="current")

    receipt_relative = registry.get("retirement_receipt")
    if _safe_relative_path(receipt_relative):
        try:
            receipt, _ = load_canonical_json(root / str(receipt_relative))
        except (OSError, RegistryError) as exc:
            failures.append(f"{label}: cannot load retirement receipt: {exc}")
        else:
            live_time = _parse_utc_second(observation.get("observed_at"))
            retirement_time = _parse_utc_second(receipt.get("observed_at"))
            if (
                live_time is None
                or retirement_time is None
                or live_time <= retirement_time
            ):
                failures.append(
                    f"{label}: observation does not postdate the retirement receipt"
                )
            retirement_source = receipt.get("source_commit")
            if (
                not isinstance(retirement_source, str)
                or HEX40.fullmatch(retirement_source) is None
            ):
                failures.append(
                    f"{label}: retirement receipt source_commit is not 40-hex"
                )
            elif (
                isinstance(head, str)
                and HEX40.fullmatch(head) is not None
                and _git(
                    root,
                    "merge-base",
                    "--is-ancestor",
                    retirement_source,
                    head,
                ).returncode
                != 0
            ):
                failures.append(
                    f"{label}: recorded head predates the retirement authority"
                )
            receipt_rows = receipt.get("entries")
            iter204_rows = (
                [
                    row
                    for row in receipt_rows
                    if isinstance(row, dict)
                    and row.get("workflow_id") == ITER204_ID
                ]
                if isinstance(receipt_rows, list)
                else []
            )
            iter204 = observation.get("iter204_runs")
            push = iter204.get("push") if isinstance(iter204, dict) else None
            dispatch = (
                iter204.get("workflow_dispatch")
                if isinstance(iter204, dict)
                else None
            )
            if (
                len(iter204_rows) != 1
                or not isinstance(push, dict)
                or not isinstance(dispatch, dict)
            ):
                failures.append(
                    f"{label}: iter204 receipt comparison is unavailable"
                )
            else:
                receipt_row = iter204_rows[0]
                latest = push.get("latest")
                latest_id = (
                    latest.get("id") if isinstance(latest, dict) else None
                )
                if (
                    push.get("total_count")
                    != receipt_row.get("post_push_run_count")
                    or latest_id != receipt_row.get("post_latest_run_id")
                    or dispatch != {"latest": None, "total_count": 0}
                    or receipt_row.get("post_dispatch_run_count") != 0
                ):
                    failures.append(
                        f"{label}: iter204 gained a post-retirement run "
                        "or receipt differs"
                    )
    else:
        failures.append(f"{label}: retirement receipt path is invalid")
    return failures


def raw_observation_binding_failures(
    observation: dict[str, Any],
    *,
    expected_source_commit: object,
    expected_registry_sha256: object,
    label: str,
) -> list[str]:
    """Require retained pre/post observations to name the authorization bytes."""

    failures: list[str] = []
    if observation.get("source_commit") != expected_source_commit:
        failures.append(
            f"workflow retirement receipt: raw observation source_commit differs: {label}"
        )
    if observation.get("registry_sha256") != expected_registry_sha256:
        failures.append(
            f"workflow retirement receipt: raw observation registry digest differs: {label}"
        )
    return failures


class GitHubWorkflowLoader(yaml.SafeLoader):
    """YAML 1.2-like loader for GitHub Actions, where ``on`` is a string."""


GitHubWorkflowLoader.yaml_implicit_resolvers = copy.deepcopy(
    yaml.SafeLoader.yaml_implicit_resolvers
)
for resolver_key, resolvers in GitHubWorkflowLoader.yaml_implicit_resolvers.items():
    GitHubWorkflowLoader.yaml_implicit_resolvers[resolver_key] = [
        (tag, expression)
        for tag, expression in resolvers
        if tag != "tag:yaml.org,2002:bool"
    ]
GitHubWorkflowLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)


def _construct_unique_mapping(
    loader: GitHubWorkflowLoader,
    node: yaml.nodes.MappingNode,
    deep: bool = False,
) -> dict[object, object]:
    loader.flatten_mapping(node)
    mapping: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable mapping key",
                key_node.start_mark,
            ) from exc
        if duplicate:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


GitHubWorkflowLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def parse_workflow(path: Path) -> dict[str, Any]:
    try:
        document = yaml.load(path.read_text(encoding="utf-8"), Loader=GitHubWorkflowLoader)
    except (UnicodeError, yaml.YAMLError) as exc:
        raise RegistryError(f"invalid workflow YAML {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise RegistryError(f"workflow root is not a mapping: {path}")
    return document


def declared_triggers(document: dict[str, Any]) -> list[str]:
    trigger = document.get("on")
    if isinstance(trigger, str):
        values = [trigger]
    elif isinstance(trigger, list) and all(isinstance(item, str) for item in trigger):
        values = trigger
    elif isinstance(trigger, dict) and all(isinstance(item, str) for item in trigger):
        values = list(trigger)
    else:
        raise RegistryError("workflow 'on' is not a supported literal trigger declaration")
    if len(values) != len(set(values)):
        raise RegistryError("workflow trigger declaration contains duplicates")
    return sorted(values)


def executable_job_env_runner_failures(
    document: dict[str, Any], *, label: str
) -> list[str]:
    """Reject runner context where GitHub does not make it available."""

    failures: list[str] = []
    jobs = document.get("jobs")
    if not isinstance(jobs, dict):
        return [f"{label}: jobs is not a mapping"]
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        environment = job.get("env")
        if not isinstance(environment, dict):
            continue
        for name, value in environment.items():
            if isinstance(value, str) and RUNNER_EXPRESSION.search(value):
                failures.append(
                    f"{label}: executable job {job_name!r} job-level env {name!r} "
                    "uses unavailable runner.* context"
                )
    return failures


def _safe_relative_path(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and "\\" not in value


def _find_seal_record(value: Any, identifier: str) -> dict[str, Any] | None:
    if isinstance(value, dict):
        if any(value.get(key) == identifier for key in ("id", "record_id", "seal_id")):
            return value
        for child in value.values():
            found = _find_seal_record(child, identifier)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_seal_record(child, identifier)
            if found is not None:
                return found
    return None


def _path_lists(value: Any) -> list[list[str]]:
    lists: list[list[str]] = []
    if isinstance(value, dict):
        if value.get("kind") == "path_list" and isinstance(value.get("paths"), list):
            paths = value["paths"]
            if all(isinstance(item, str) for item in paths):
                lists.append(paths)
        for key, child in value.items():
            if key == "path_list" and isinstance(child, list) and all(
                isinstance(item, str) for item in child
            ):
                lists.append(child)
            lists.extend(_path_lists(child))
    elif isinstance(value, list):
        for child in value:
            lists.extend(_path_lists(child))
    return lists


def validate_seal_links(
    root: Path, registry: dict[str, Any], historical_paths: set[str]
) -> list[str]:
    failures: list[str] = []
    seal_relative = registry.get("seal_registry")
    if not _safe_relative_path(seal_relative):
        return ["workflow registry: seal_registry is not a safe relative path"]
    seal_path = root / str(seal_relative)
    if not seal_path.is_file() or seal_path.is_symlink():
        return [f"workflow registry: seal registry is absent: {seal_relative}"]
    try:
        seals = load_unique_json_object(seal_path)
    except (OSError, RegistryError) as exc:
        return [f"workflow registry: cannot validate seal registry: {exc}"]
    record = _find_seal_record(seals, HISTORICAL_SEAL)
    if record is None:
        return [f"workflow registry: seal reference is absent: {HISTORICAL_SEAL}"]
    path_lists = _path_lists(record)
    if not any(historical_paths <= set(paths) for paths in path_lists):
        failures.append(
            "workflow registry: historical seal path_list does not cover all 29 workflows"
        )
    return failures


def _historical_order(
    historical: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    iter204 = [
        row for row in historical if row.get("workflow_id") == ITER204_ID
    ]
    remainder = sorted(
        (
            row
            for row in historical
            if row.get("workflow_id") != ITER204_ID
        ),
        key=lambda row: str(row.get("path")),
    )
    return [*iter204, *remainder]


def _iter204_projection_failures(
    value: object,
    *,
    label: str,
) -> list[str]:
    failures: list[str] = []
    if not isinstance(value, dict) or set(value) != {
        "push",
        "workflow_dispatch",
    }:
        return [f"{label}: iter204 projection fields differ"]
    for event in ("push", "workflow_dispatch"):
        projection = value.get(event)
        if not isinstance(projection, dict) or set(projection) != {
            "latest",
            "total_count",
        }:
            failures.append(f"{label}: iter204 {event} projection is malformed")
            continue
        total = projection.get("total_count")
        latest = projection.get("latest")
        if not _is_int(total):
            failures.append(
                f"{label}: iter204 {event} total_count is not a nonnegative integer"
            )
            continue
        if total == 0:
            if latest is not None:
                failures.append(
                    f"{label}: iter204 {event} latest must be null at zero count"
                )
            continue
        if not isinstance(latest, dict) or set(latest) != ITER204_LATEST_KEYS:
            failures.append(f"{label}: iter204 {event} latest row is malformed")
            continue
        if (
            not _is_int(latest.get("id"), minimum=1)
            or not _is_int(latest.get("run_number"), minimum=1)
            or latest.get("event") != event
            or not isinstance(latest.get("head_branch"), str)
            or not isinstance(latest.get("head_sha"), str)
            or HEX40.fullmatch(latest["head_sha"]) is None
            or _parse_utc_second(latest.get("created_at")) is None
            or not isinstance(latest.get("status"), str)
            or (
                latest.get("conclusion") is not None
                and not isinstance(latest.get("conclusion"), str)
            )
        ):
            failures.append(
                f"{label}: iter204 {event} latest-row scalar types differ"
            )
    dispatch = value.get("workflow_dispatch")
    if isinstance(dispatch, dict) and (
        dispatch.get("total_count") != 0
        or dispatch.get("latest") is not None
    ):
        failures.append(f"{label}: iter204 dispatch history is not exact zero")
    return failures


def validate_retirement_snapshot(
    snapshot: dict[str, Any],
    *,
    registry: dict[str, Any],
    historical: list[dict[str, Any]],
    expected_phase: str,
    expected_source_commit: object,
    expected_registry_sha256: object,
    label: str,
) -> tuple[
    list[str],
    dict[int, dict[str, Any]],
    dict[int, dict[str, Any]],
]:
    """Validate one raw retirement snapshot and return its exact projections."""

    failures: list[str] = []
    if set(snapshot) != SNAPSHOT_KEYS:
        failures.append(f"{label}: raw snapshot top-level fields differ")
    if snapshot.get("schema_version") != SNAPSHOT_SCHEMA:
        failures.append(f"{label}: raw snapshot schema_version differs")
    if snapshot.get("repository") != REPOSITORY:
        failures.append(f"{label}: raw snapshot repository differs")
    if snapshot.get("phase") != expected_phase:
        failures.append(f"{label}: raw snapshot phase differs")
    if snapshot.get("state_scope") != (
        "mutable server state observed at captured_at"
    ):
        failures.append(f"{label}: raw snapshot mutable state scope differs")
    if _parse_utc_second(snapshot.get("captured_at")) is None:
        failures.append(f"{label}: captured_at is not an exact UTC timestamp")
    if not _is_int(snapshot.get("get_request_count"), minimum=1):
        failures.append(
            f"{label}: get_request_count is not a positive integer"
        )
    failures.extend(
        raw_observation_binding_failures(
            snapshot,
            expected_source_commit=expected_source_commit,
            expected_registry_sha256=expected_registry_sha256,
            label=label,
        )
    )

    expected_entries = {
        row.get("workflow_id"): row
        for row in registry.get("entries", [])
        if isinstance(row, dict)
        and _is_int(row.get("workflow_id"), minimum=1)
    }
    inventory = snapshot.get("workflow_inventory")
    inventory_by_id: dict[int, dict[str, Any]] = {}
    if not isinstance(inventory, dict) or set(inventory) != {
        "total_count",
        "workflows",
    }:
        failures.append(f"{label}: workflow inventory fields differ")
    else:
        rows = inventory.get("workflows")
        total = inventory.get("total_count")
        if (
            not _is_int(total)
            or not isinstance(rows, list)
            or not all(isinstance(row, dict) for row in rows)
            or total != len(rows)
        ):
            failures.append(f"{label}: workflow inventory is malformed")
        else:
            inventory_by_id = {
                row.get("id"): row
                for row in rows
                if _is_int(row.get("id"), minimum=1)
            }
            if len(inventory_by_id) != len(rows):
                failures.append(f"{label}: workflow inventory IDs are not unique")
            if set(inventory_by_id) != set(expected_entries):
                failures.append(
                    f"{label}: workflow inventory IDs differ from the registry"
                )
            for workflow_id, entry in expected_entries.items():
                row = inventory_by_id.get(workflow_id)
                if row is None:
                    continue
                expected_state = entry.get("desired_server_state")
                if (
                    expected_phase == "pre_disable"
                    and entry.get("classification") == "historical_retired"
                ):
                    expected_state = "active"
                if (
                    row.get("path") != entry.get("path")
                    or row.get("state") != expected_state
                ):
                    failures.append(
                        f"{label}: workflow identity/state differs for "
                        f"{entry.get('path')}"
                    )

    expected_historical = _historical_order(historical)
    expected_historical_ids = [
        row.get("workflow_id") for row in expected_historical
    ]
    projections = snapshot.get("historical_run_projections")
    projection_by_id: dict[int, dict[str, Any]] = {}
    if (
        not isinstance(projections, list)
        or not all(isinstance(row, dict) for row in projections)
    ):
        failures.append(f"{label}: historical run projections are malformed")
    else:
        observed_order = [row.get("workflow_id") for row in projections]
        if observed_order != expected_historical_ids:
            failures.append(
                f"{label}: historical run projection order/IDs differ"
            )
        projection_by_id = {
            row.get("workflow_id"): row
            for row in projections
            if _is_int(row.get("workflow_id"), minimum=1)
        }
        if len(projection_by_id) != len(projections):
            failures.append(
                f"{label}: historical run projection IDs are not unique"
            )
        for row in projections:
            if set(row) != RUN_PROJECTION_KEYS:
                failures.append(
                    f"{label}: historical run projection fields differ"
                )
                continue
            total = row.get("total_run_count")
            latest = row.get("latest_run_id")
            if not _is_int(total):
                failures.append(
                    f"{label}: historical total_run_count is not "
                    "a nonnegative integer"
                )
            elif total == 0 and latest is not None:
                failures.append(
                    f"{label}: historical latest_run_id must be null at zero count"
                )
            elif total > 0 and not _is_int(latest, minimum=1):
                failures.append(
                    f"{label}: historical latest_run_id is not a positive integer"
                )

    failures.extend(
        _iter204_projection_failures(
            snapshot.get("iter204_runs"),
            label=label,
        )
    )
    iter204_events = snapshot.get("iter204_runs")
    iter204_projection = projection_by_id.get(ITER204_ID)
    if isinstance(iter204_events, dict) and isinstance(iter204_projection, dict):
        push = iter204_events.get("push")
        dispatch = iter204_events.get("workflow_dispatch")
        if isinstance(push, dict) and isinstance(dispatch, dict):
            latest = push.get("latest")
            latest_id = latest.get("id") if isinstance(latest, dict) else None
            push_count = push.get("total_count")
            dispatch_count = dispatch.get("total_count")
            if (
                not _is_int(push_count)
                or dispatch_count != 0
                or iter204_projection.get("total_run_count") != push_count
                or iter204_projection.get("latest_run_id") != latest_id
            ):
                failures.append(
                    f"{label}: iter204 event and historical projections conflict"
                )
    return failures, inventory_by_id, projection_by_id


def exact_receipt_derivation_failures(
    *,
    receipt: dict[str, Any],
    historical: list[dict[str, Any]],
    pre: dict[str, Any],
    post: dict[str, Any],
    pre_inventory: dict[int, dict[str, Any]],
    post_inventory: dict[int, dict[str, Any]],
    pre_projections: dict[int, dict[str, Any]],
    post_projections: dict[int, dict[str, Any]],
) -> list[str]:
    """Rebuild every receipt row from the retained pre/post observations."""

    failures: list[str] = []
    if receipt.get("observed_at") != post.get("captured_at"):
        failures.append(
            "workflow retirement receipt: observed_at differs from "
            "the post snapshot"
        )
    pre_time = _parse_utc_second(pre.get("captured_at"))
    post_time = _parse_utc_second(post.get("captured_at"))
    if pre_time is not None and post_time is not None and pre_time > post_time:
        failures.append(
            "workflow retirement receipt: snapshot timestamps are reversed"
        )
    pre_gets = pre.get("get_request_count")
    post_gets = post.get("get_request_count")
    minimum_snapshot_gets = 1 + len(historical) + 2
    minimum_post_delta = len(historical) + minimum_snapshot_gets
    if (
        _is_int(pre_gets, minimum=1)
        and pre_gets < minimum_snapshot_gets
    ):
        failures.append(
            "workflow retirement receipt: pre snapshot GET count is incomplete"
        )
    if (
        _is_int(pre_gets, minimum=1)
        and _is_int(post_gets, minimum=1)
        and post_gets - pre_gets < minimum_post_delta
    ):
        failures.append(
            "workflow retirement receipt: post snapshot GET count is incomplete"
        )

    rows = receipt.get("entries")
    if not isinstance(rows, list):
        return failures
    expected_rows: list[dict[str, Any]] = []
    for entry in _historical_order(historical):
        workflow_id = entry.get("workflow_id")
        before_projection = pre_projections.get(workflow_id)
        after_projection = post_projections.get(workflow_id)
        before_object = pre_inventory.get(workflow_id)
        after_object = post_inventory.get(workflow_id)
        if not all(
            isinstance(value, dict)
            for value in (
                before_projection,
                after_projection,
                before_object,
                after_object,
            )
        ):
            continue
        row = {
            "path": entry.get("path"),
            "post_latest_run_id": after_projection.get("latest_run_id"),
            "post_state": after_object.get("state"),
            "post_total_run_count": after_projection.get("total_run_count"),
            "pre_latest_run_id": before_projection.get("latest_run_id"),
            "pre_state": before_object.get("state"),
            "pre_total_run_count": before_projection.get("total_run_count"),
            "workflow_id": workflow_id,
        }
        if workflow_id == ITER204_ID:
            pre_iter204 = pre.get("iter204_runs")
            post_iter204 = post.get("iter204_runs")
            if isinstance(pre_iter204, dict) and isinstance(post_iter204, dict):
                def event_count(
                    document: dict[str, Any],
                    event: str,
                ) -> object:
                    projection = document.get(event)
                    return (
                        projection.get("total_count")
                        if isinstance(projection, dict)
                        else None
                    )

                row.update(
                    {
                        "post_dispatch_run_count": event_count(
                            post_iter204,
                            "workflow_dispatch",
                        ),
                        "post_push_run_count": event_count(
                            post_iter204,
                            "push",
                        ),
                        "pre_dispatch_run_count": event_count(
                            pre_iter204,
                            "workflow_dispatch",
                        ),
                        "pre_push_run_count": event_count(
                            pre_iter204,
                            "push",
                        ),
                    }
                )
        expected_rows.append(row)
    if rows != expected_rows:
        failures.append(
            "workflow retirement receipt: entries do not exactly regenerate "
            "from the retained pre/post snapshots"
        )
    if pre.get("iter204_runs") != post.get("iter204_runs"):
        failures.append(
            "workflow retirement receipt: iter204 projection changed during retirement"
        )
    for entry in _historical_order(historical):
        workflow_id = entry.get("workflow_id")
        if pre_projections.get(workflow_id) != post_projections.get(workflow_id):
            failures.append(
                "workflow retirement receipt: historical run projection changed "
                f"during retirement: {entry.get('path')}"
            )
    return failures


def validate_retirement_receipt(
    root: Path,
    registry: dict[str, Any],
    historical: list[dict[str, Any]],
) -> list[str]:
    failures: list[str] = []
    receipt_relative = registry.get("retirement_receipt")
    if not _safe_relative_path(receipt_relative):
        return ["workflow registry: retirement_receipt is not a safe relative path"]
    receipt_path = root / str(receipt_relative)
    if not receipt_path.is_file() or receipt_path.is_symlink():
        return [f"workflow registry: final retirement receipt is absent: {receipt_relative}"]
    try:
        receipt, receipt_raw = load_canonical_json(receipt_path)
    except (OSError, RegistryError) as exc:
        return [f"workflow registry: cannot validate retirement receipt: {exc}"]
    try:
        failures.extend(
            introducing_blob_failures(
                root=root,
                relative=Path(str(receipt_relative)),
                current_raw=receipt_raw,
                label="workflow retirement receipt",
            )
        )
    except RegistryError as exc:
        failures.append(f"workflow retirement receipt: {exc}")
    required_top = {
        "entries",
        "observed_at",
        "operation_counts",
        "raw_observations",
        "registry_sha256",
        "repository",
        "schema_version",
        "source_commit",
        "state_scope",
    }
    if set(receipt) != required_top:
        failures.append("workflow retirement receipt: top-level fields differ")
    if receipt.get("schema_version") != RECEIPT_SCHEMA:
        failures.append("workflow retirement receipt: schema_version differs")
    if receipt.get("repository") != REPOSITORY:
        failures.append("workflow retirement receipt: repository differs")
    registry_digest = receipt.get("registry_sha256")
    if not isinstance(registry_digest, str) or HEX64.fullmatch(registry_digest) is None:
        failures.append(
            "workflow retirement receipt: registry digest is not 64-hex"
        )
    if _parse_utc_second(receipt.get("observed_at")) is None:
        failures.append(
            "workflow retirement receipt: observed_at is not an exact UTC timestamp"
        )
    source_commit = receipt.get("source_commit")
    if (
        not isinstance(source_commit, str)
        or HEX40.fullmatch(source_commit) is None
    ):
        failures.append("workflow retirement receipt: source_commit is not 40-hex")
    elif (
        isinstance(registry_digest, str)
        and HEX64.fullmatch(registry_digest) is not None
    ):
        failures.extend(
            registry_provenance_failures(
                root=root,
                current_registry=registry,
                source_commit=source_commit,
                expected_registry_sha256=registry_digest,
            )
        )
    if (
        receipt.get("state_scope")
        != "server state observed at observed_at; not a timeless state proof"
    ):
        failures.append("workflow retirement receipt: mutable state scope differs")
    expected_operations = {
        "delete_run": 0,
        "delete_workflow": 0,
        "disable_puts": 29,
        "dispatch": 0,
        "enable": 0,
        "rerun": 0,
    }
    operations = receipt.get("operation_counts")
    if (
        not isinstance(operations, dict)
        or set(operations) != set(expected_operations)
        or any(not _is_int(value) for value in operations.values())
        or operations != expected_operations
    ):
        failures.append("workflow retirement receipt: operation counts differ")

    rows = receipt.get("entries")
    by_id: dict[int, dict[str, Any]] = {}
    if not isinstance(rows, list) or len(rows) != 29:
        failures.append("workflow retirement receipt: expected exactly 29 entries")
    else:
        expected_order = [
            row.get("workflow_id") for row in _historical_order(historical)
        ]
        observed_order = [
            row.get("workflow_id") for row in rows if isinstance(row, dict)
        ]
        if observed_order != expected_order:
            failures.append(
                "workflow retirement receipt: iter204-first disable order differs"
            )
        by_id = {
            row.get("workflow_id"): row
            for row in rows
            if isinstance(row, dict)
            and isinstance(row.get("workflow_id"), int)
            and not isinstance(row.get("workflow_id"), bool)
        }
        if len(by_id) != 29:
            failures.append("workflow retirement receipt: workflow IDs are not unique")
    expected_by_id = {entry["workflow_id"]: entry for entry in historical}
    if set(by_id) != set(expected_by_id):
        failures.append("workflow retirement receipt: historical workflow IDs differ")
    for workflow_id, expected in expected_by_id.items():
        row = by_id.get(workflow_id)
        if row is None:
            continue
        if (
            row.get("path") != expected["path"]
            or row.get("pre_state") != "active"
            or row.get("post_state") != "disabled_manually"
            or not isinstance(row.get("pre_total_run_count"), int)
            or isinstance(row.get("pre_total_run_count"), bool)
            or row.get("pre_total_run_count") < 0
            or row.get("post_total_run_count") != row.get("pre_total_run_count")
            or row.get("post_latest_run_id") != row.get("pre_latest_run_id")
            or (
                row.get("pre_total_run_count") == 0
                and row.get("pre_latest_run_id") is not None
            )
            or (
                row.get("pre_total_run_count") > 0
                and not _is_int(row.get("pre_latest_run_id"), minimum=1)
            )
        ):
            failures.append(
                f"workflow retirement receipt: state/run binding differs for {expected['path']}"
            )
    iter204 = by_id.get(ITER204_ID)
    if iter204 is not None and (
        not _is_int(iter204.get("pre_push_run_count"))
        or not _is_int(iter204.get("post_push_run_count"))
        or not _is_int(iter204.get("pre_dispatch_run_count"))
        or not _is_int(iter204.get("post_dispatch_run_count"))
        or iter204.get("pre_push_run_count")
        != iter204.get("post_push_run_count")
        or iter204.get("pre_dispatch_run_count") != 0
        or iter204.get("post_dispatch_run_count") != 0
    ):
        failures.append("workflow retirement receipt: iter204 run boundary differs")

    observations = receipt.get("raw_observations")
    expected_observation_paths = [
        PRE_OBSERVATION_RELATIVE.as_posix(),
        POST_OBSERVATION_RELATIVE.as_posix(),
    ]
    loaded_observations: dict[str, dict[str, Any]] = {}
    if (
        not isinstance(observations, list)
        or len(observations) != 2
        or [
            row.get("path") if isinstance(row, dict) else None
            for row in observations
        ]
        != expected_observation_paths
    ):
        failures.append(
            "workflow retirement receipt: expected exact ordered pre/post "
            "raw observations"
        )
    else:
        for row in observations:
            if not isinstance(row, dict) or set(row) != {"bytes", "path", "sha256"}:
                failures.append("workflow retirement receipt: raw observation row is malformed")
                continue
            relative = row.get("path")
            digest = row.get("sha256")
            byte_count = row.get("bytes")
            if (
                not _safe_relative_path(relative)
                or not isinstance(digest, str)
                or HEX64.fullmatch(digest) is None
                or not isinstance(byte_count, int)
                or isinstance(byte_count, bool)
                or byte_count < 0
            ):
                failures.append("workflow retirement receipt: raw observation metadata differs")
                continue
            path = root / relative
            if path.is_symlink() or not path.is_file():
                failures.append(
                    f"workflow retirement receipt: raw observation is absent: {relative}"
                )
                continue
            payload = path.read_bytes()
            if len(payload) != byte_count or sha256(payload) != digest:
                failures.append(
                    f"workflow retirement receipt: raw observation digest differs: {relative}"
                )
                continue
            try:
                observation = load_canonical_json_bytes(
                    payload,
                    label=str(relative),
                )
            except RegistryError as exc:
                failures.append(
                    "workflow retirement receipt: raw observation is not "
                    f"canonical JSON: {exc}"
                )
                continue
            loaded_observations[str(relative)] = observation
    pre = loaded_observations.get(PRE_OBSERVATION_RELATIVE.as_posix())
    post = loaded_observations.get(POST_OBSERVATION_RELATIVE.as_posix())
    if isinstance(pre, dict) and isinstance(post, dict):
        pre_failures, pre_inventory, pre_projections = (
            validate_retirement_snapshot(
                pre,
                registry=registry,
                historical=historical,
                expected_phase="pre_disable",
                expected_source_commit=source_commit,
                expected_registry_sha256=registry_digest,
                label=PRE_OBSERVATION_RELATIVE.as_posix(),
            )
        )
        post_failures, post_inventory, post_projections = (
            validate_retirement_snapshot(
                post,
                registry=registry,
                historical=historical,
                expected_phase="post_disable",
                expected_source_commit=source_commit,
                expected_registry_sha256=registry_digest,
                label=POST_OBSERVATION_RELATIVE.as_posix(),
            )
        )
        failures.extend(pre_failures)
        failures.extend(post_failures)
        failures.extend(
            exact_receipt_derivation_failures(
                receipt=receipt,
                historical=historical,
                pre=pre,
                post=post,
                pre_inventory=pre_inventory,
                post_inventory=post_inventory,
                pre_projections=pre_projections,
                post_projections=post_projections,
            )
        )
    return failures


def collect_failures(
    *,
    root: Path = ROOT,
    pre_retirement: bool = False,
) -> list[str]:
    failures: list[str] = []
    registry_path = root / REGISTRY_RELATIVE
    try:
        registry, _ = load_canonical_json(registry_path)
    except (OSError, RegistryError) as exc:
        return [f"workflow registry: {exc}"]
    failures.extend(
        regular_0644_failures(
            root=root,
            relative=REGISTRY_RELATIVE,
            label="workflow registry",
        )
    )
    if set(registry) != REGISTRY_KEYS:
        failures.append("workflow registry: top-level fields differ")
    if registry.get("schema_version") != SCHEMA:
        failures.append("workflow registry: schema_version differs")
    if registry.get("repository") != REPOSITORY:
        failures.append("workflow registry: repository differs")
    if registry.get("default_policy") != "deny":
        failures.append("workflow registry: default policy must be deny")
    active_gate = registry.get("active_gate")
    if (
        not _safe_relative_path(active_gate)
        or not str(active_gate).startswith("experiments/")
        or not str(active_gate).endswith("/HYPOTHESIS.md")
    ):
        failures.append(
            "workflow registry: active gate is not a safe experiment hypothesis"
        )
    else:
        active_gate_path = root / str(active_gate)
        if active_gate_path.is_symlink() or not active_gate_path.is_file():
            failures.append("workflow registry: active gate file is absent")
    if not _is_iso_date(registry.get("updated")):
        failures.append("workflow registry: updated is not an exact ISO date")

    current: dict[str, Any] | None = None
    current_path = root / CURRENT_RELATIVE
    try:
        current = load_unique_json_object(current_path)
    except (OSError, RegistryError) as exc:
        failures.append(f"workflow registry: cannot validate current state: {exc}")
    else:
        if current.get("active_gate") != active_gate:
            failures.append(
                "workflow registry: active gate differs from mission/current.json"
            )
        if current.get("updated") != registry.get("updated"):
            failures.append(
                "workflow registry: updated differs from mission/current.json"
            )

    rows = registry.get("entries")
    if not isinstance(rows, list):
        return failures + ["workflow registry: entries is not a list"]
    paths: list[str] = []
    workflow_ids: list[int] = []
    valid_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        label = f"workflow registry entry {index}"
        if not isinstance(row, dict):
            failures.append(f"{label}: entry is not an object")
            continue
        valid_rows.append(row)
        if set(row) != ENTRY_KEYS:
            failures.append(f"{label}: fields differ")
        path = row.get("path")
        if not _safe_relative_path(path):
            failures.append(f"{label}: path is not a safe relative POSIX path")
        else:
            paths.append(path)
        workflow_id = row.get("workflow_id")
        if (
            not isinstance(workflow_id, int)
            or isinstance(workflow_id, bool)
            or workflow_id <= 0
        ):
            failures.append(f"{label}: workflow_id is not a positive integer")
        else:
            workflow_ids.append(workflow_id)
        if row.get("classification") not in EXPECTED_CLASSES:
            failures.append(f"{label}: classification is unknown")
    if len(paths) != len(set(paths)):
        failures.append("workflow registry: paths are not unique")
    if paths != sorted(paths):
        failures.append("workflow registry: entries are not sorted by path")
    if len(workflow_ids) != len(set(workflow_ids)):
        failures.append("workflow registry: workflow IDs are not unique")

    repository_rows = [
        row for row in valid_rows if row.get("source_kind") == "repository_file"
    ]
    platform_rows = [
        row for row in valid_rows if row.get("source_kind") == "platform_generated"
    ]
    if len(repository_rows) != 30:
        failures.append("workflow registry: expected exactly 30 repository workflows")
    if len(platform_rows) != 1:
        failures.append("workflow registry: expected exactly one platform workflow")
    actual_workflows = {
        str(path.relative_to(root))
        for pattern in ("*.yml", "*.yaml")
        for path in (root / ".github/workflows").glob(pattern)
    }
    registered_workflows = {
        str(row.get("path"))
        for row in repository_rows
        if isinstance(row.get("path"), str)
    }
    if actual_workflows != registered_workflows:
        missing = sorted(actual_workflows - registered_workflows)
        extra = sorted(registered_workflows - actual_workflows)
        failures.append(
            f"workflow registry: file inventory differs; unregistered={missing}, absent={extra}"
        )

    classes = {
        name: [row for row in valid_rows if row.get("classification") == name]
        for name in EXPECTED_CLASSES
    }
    if len(classes["active_control"]) != 1:
        failures.append("workflow registry: expected exactly one active control")
    if classes["authorized_one_shot"]:
        failures.append("workflow registry: expected zero authorized one-shot workflows")
    if len(classes["historical_retired"]) != 29:
        failures.append("workflow registry: expected exactly 29 historical workflows")
    if len(classes["platform_service"]) != 1:
        failures.append("workflow registry: expected exactly one platform service")

    historical_paths: set[str] = set()
    for row in repository_rows:
        path_value = row.get("path")
        if not isinstance(path_value, str):
            continue
        path = root / path_value
        mode_failures = regular_0644_failures(
            root=root,
            relative=Path(path_value),
            label=f"workflow registry: {path_value}",
        )
        if mode_failures:
            failures.extend(mode_failures)
            continue
        payload = path.read_bytes()
        digest = row.get("sha256")
        if not isinstance(digest, str) or HEX64.fullmatch(digest) is None:
            failures.append(f"workflow registry: invalid SHA-256 for {path_value}")
        elif sha256(payload) != digest:
            failures.append(f"workflow registry: workflow digest differs: {path_value}")
        try:
            document = parse_workflow(path)
            triggers = declared_triggers(document)
        except RegistryError as exc:
            failures.append(f"workflow registry: {exc}")
            continue
        if row.get("declared_triggers") != triggers:
            failures.append(f"workflow registry: trigger set differs: {path_value}")
        classification = row.get("classification")
        if classification == "active_control":
            if (
                path_value != ".github/workflows/ci.yml"
                or row.get("desired_server_state") != "active"
                or row.get("execution_authority")
                != "continuous_repository_verification"
                or triggers != ["pull_request", "push"]
                or row.get("retirement_receipt") is not None
                or row.get("seal_reference") is not None
                or row.get("known_invalidity") is not None
            ):
                failures.append("workflow registry: active ci control contract differs")
            failures.extend(
                executable_job_env_runner_failures(document, label=path_value)
            )
        elif classification == "authorized_one_shot":
            failures.extend(
                executable_job_env_runner_failures(document, label=path_value)
            )
        elif classification == "historical_retired":
            historical_paths.add(path_value)
            if (
                row.get("desired_server_state") != "disabled_manually"
                or row.get("execution_authority") != "none"
                or triggers != ["workflow_dispatch"]
                or row.get("retirement_receipt") != registry.get("retirement_receipt")
                or row.get("seal_reference") != HISTORICAL_SEAL
            ):
                failures.append(
                    f"workflow registry: historical retirement contract differs: {path_value}"
                )
            expected_invalidity = (
                {
                    "class": "github_expression_context",
                    "column": 36,
                    "expression": "runner.temp",
                    "line": 318,
                    "result": (
                        "experiments/iter204_iter203_infrastructure_recovery/RESULT.md"
                    ),
                }
                if path_value == ITER204_PATH
                else None
            )
            if row.get("known_invalidity") != expected_invalidity:
                failures.append(
                    f"workflow registry: known invalidity differs: {path_value}"
                )
            if path_value == ITER204_PATH:
                lines = payload.decode("utf-8").splitlines()
                if (
                    row.get("workflow_id") != ITER204_ID
                    or digest != ITER204_SHA256
                    or len(lines) < 318
                    or lines[317]
                    != (
                        "      TELOS_ITER204_SMOKE_RECEIPT: "
                        "${{ runner.temp }}/iter204-smoke/smoke.receipt.json"
                    )
                ):
                    failures.append("workflow registry: sealed iter204 defect anchor differs")

    platform = platform_rows[0] if len(platform_rows) == 1 else {}
    if platform and (
        platform.get("path") != PLATFORM_PATH
        or platform.get("workflow_id") != PLATFORM_ID
        or platform.get("classification") != "platform_service"
        or platform.get("declared_triggers") != ["dynamic"]
        or platform.get("desired_server_state") != "active"
        or platform.get("execution_authority") != "github_platform_service"
        or platform.get("sha256") is not None
        or platform.get("seal_reference") is not None
        or platform.get("retirement_receipt") is not None
        or platform.get("known_invalidity") is not None
    ):
        failures.append("workflow registry: Dependency Graph service contract differs")

    if not pre_retirement:
        failures.extend(validate_seal_links(root, registry, historical_paths))
        failures.extend(
            validate_retirement_receipt(
                root,
                registry,
                classes["historical_retired"],
            )
        )
    failures.extend(
        retained_live_observation_failures(
            root=root,
            registry=registry,
        )
    )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pre-retirement",
        action="store_true",
        help="validate frozen local identities without claiming server retirement",
    )
    args = parser.parse_args()
    failures = collect_failures(pre_retirement=args.pre_retirement)
    if failures:
        print("workflow lifecycle registry failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1
    mode = "pre-retirement identities" if args.pre_retirement else "final retirement"
    print(
        f"workflow lifecycle registry: 30 repository workflows, 29 historical, "
        f"1 active control, and 1 platform service pass ({mode})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
