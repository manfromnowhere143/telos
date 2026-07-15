#!/usr/bin/env python3
"""Create, collect, and verify iter202 execution chain-of-custody receipts.

The certification workflow runs eight disjoint shards.  A shard is eligible for
scientific use only after this module has recorded an immutable receipt for the
exact log bytes produced by that shard.  Collection then requires all eight
receipts from one GitHub run attempt, copies without overwrite through a
fsync'd staging directory, and records one aggregate receipt.  ``check`` is the
same offline verifier used by adjudication before any derived write or judge
credential access.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import subprocess
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/iter202_natural_rate_scaled"
DEFAULT_SPEC_INDEX = EXP / "proof/raw/specs/index.json"
DEFAULT_RUNTIME_MANIFEST = EXP / "proof/raw/runtime_manifest.json"
DEFAULT_EXECUTION_DIR = EXP / "proof/raw/execution"
AGGREGATE_RECEIPT_NAME = "_telos_iter202_execution_complete.receipt.json"

EXPERIMENT_ID = "iter202_natural_rate_scaled"
SHARD_COUNT = 8
TARGET_COUNT = 53
SCENARIO_CALL_CEILING = 50
SHARD_SCHEMA = "telos.iter202.execution_shard_receipt.v1"
AGGREGATE_SCHEMA = "telos.iter202.execution_aggregate_receipt.v1"
SPEC_INDEX_SCHEMA = "telos.iter200.spec_index.v2"
RUNTIME_MANIFEST_SCHEMA = "telos.iter202.runtime_freeze.v1"
TARGET_SCHEMA = "telos.iter202.solve_targets.v1"
SOLVE_SUMMARY_SCHEMA = "telos.iter200.solve_summary.v1"
SCENARIOS_SUMMARY_SCHEMA = "telos.iter200.scenarios_summary.v1"
ASSIGNMENT_METHOD = "zero_based_ordered_certification_spec_ordinal_modulo_8"

INSTANCE_ID_RE = re.compile(r"[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
GITHUB_SHA_RE = re.compile(r"[0-9a-f]{40}")
POSITIVE_INTEGER_RE = re.compile(r"[1-9][0-9]*")
GITHUB_REPOSITORY_RE = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
ARTIFACT_RE = re.compile(
    r"iter202-execution-run-([1-9][0-9]*)-attempt-([1-9][0-9]*)-"
    r"shard-([0-7])-of-8"
)

SHARD_TOP_KEYS = {
    "assignment",
    "experiment_id",
    "github",
    "logs",
    "schema_version",
    "source",
}
AGGREGATE_TOP_KEYS = {
    "assignment",
    "experiment_id",
    "github",
    "logs",
    "schema_version",
    "shards",
    "source",
}
ASSIGNMENT_KEYS = {
    "method",
    "ordered_instance_ids",
    "shard_count",
    "shard_index",
}
AGGREGATE_ASSIGNMENT_KEYS = {
    "method",
    "ordered_instance_ids",
    "shard_count",
}
GITHUB_KEYS = {"repository", "run_attempt", "run_id", "sha", "workflow_ref"}
SOURCE_KEYS = {
    "runtime_manifest_sha256",
    "scenarios_summary_sha256",
    "solve_summary_sha256",
    "solve_targets_sha256",
    "spec_index_sha256",
}
FILE_KEYS = {"bytes", "name", "sha256"}
AGGREGATE_LOG_KEYS = {"bytes", "name", "sha256", "shard_index"}
SHARD_RECORD_KEYS = {
    "artifact_name",
    "ordered_instance_ids",
    "receipt_bytes",
    "receipt_name",
    "receipt_sha256",
    "shard_index",
}


class ExecutionCollectionError(ValueError):
    """Execution evidence cannot be proved complete and single-provenance."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ExecutionCollectionError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_nonfinite_constant(value: str) -> Any:
    raise ExecutionCollectionError(f"non-finite JSON constant is forbidden: {value}")


def canonical_json_bytes(value: dict[str, Any]) -> bytes:
    """Return the sole accepted rendering for an execution receipt."""

    try:
        return (
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ExecutionCollectionError(f"receipt is not strict JSON: {exc}") from exc


def _read_regular_file(path: Path) -> bytes:
    """Read one regular file through a descriptor-anchored no-follow path."""

    path = _absolute_no_resolve(path)
    parent_descriptor = _open_directory_fd(path.parent, f"parent of evidence {path}")
    try:
        return _read_regular_file_at(parent_descriptor, path.name, path)
    finally:
        os.close(parent_descriptor)


def _load_json_strict_with_payload(
    path: Path, *, canonical: bool = False
) -> tuple[dict[str, Any], bytes]:
    payload = _read_regular_file(path)
    try:
        value = json.loads(
            payload,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonfinite_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExecutionCollectionError(f"cannot parse strict JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ExecutionCollectionError(f"JSON evidence must be an object: {path}")
    if canonical and payload != canonical_json_bytes(value):
        raise ExecutionCollectionError(f"JSON evidence is not canonical: {path}")
    return value, payload


def load_json_strict(path: Path, *, canonical: bool = False) -> dict[str, Any]:
    value, _ = _load_json_strict_with_payload(path, canonical=canonical)
    return value


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise ExecutionCollectionError(
            f"{label} keys differ: expected {sorted(expected)}, got {sorted(value)}"
        )


def _is_plain_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _absolute_no_resolve(path: Path) -> Path:
    """Return an absolute lexical path, normalizing only the trusted OS /tmp alias."""

    absolute = Path(os.path.abspath(os.fspath(path)))
    trusted_tmp = Path("/tmp")
    try:
        relative = absolute.relative_to(trusted_tmp)
    except ValueError:
        return absolute
    try:
        trusted_tmp_metadata = trusted_tmp.lstat()
    except OSError as exc:
        raise ExecutionCollectionError(f"cannot stat trusted /tmp alias: {exc}") from exc
    if not stat.S_ISLNK(trusted_tmp_metadata.st_mode):
        return absolute
    try:
        trusted_target = trusted_tmp.resolve(strict=True)
        target_metadata = trusted_target.lstat()
    except OSError as exc:
        raise ExecutionCollectionError(f"cannot resolve trusted /tmp alias: {exc}") from exc
    if not stat.S_ISDIR(target_metadata.st_mode) or stat.S_ISLNK(target_metadata.st_mode):
        raise ExecutionCollectionError("trusted /tmp alias does not resolve to a regular directory")
    return trusted_target / relative


def _reject_symlink_components(path: Path, label: str) -> None:
    """Reject every existing symlink component below the trusted filesystem root."""

    path = _absolute_no_resolve(path)
    parts = path.parts
    if not path.is_absolute() or not parts:
        raise ExecutionCollectionError(f"{label} is not an absolute path: {path}")
    current = Path(parts[0])
    for ordinal, component in enumerate(parts[1:], start=1):
        current /= component
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            return
        except OSError as exc:
            raise ExecutionCollectionError(
                f"cannot inspect {label} component {current}: {exc}"
            ) from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise ExecutionCollectionError(
                f"{label} contains a symlink path component: {current}"
            )
        if ordinal < len(parts) - 1 and not stat.S_ISDIR(metadata.st_mode):
            raise ExecutionCollectionError(
                f"{label} contains a non-directory parent component: {current}"
            )


def _open_directory_fd(path: Path, label: str) -> int:
    """Open an absolute directory one no-follow component at a time."""

    path = _absolute_no_resolve(path)
    parts = path.parts
    if not path.is_absolute() or not parts:
        raise ExecutionCollectionError(f"{label} is not an absolute path: {path}")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        descriptor = os.open(parts[0], flags)
    except OSError as exc:
        raise ExecutionCollectionError(f"cannot anchor {label} at {parts[0]}: {exc}") from exc
    current = Path(parts[0])
    try:
        for component in parts[1:]:
            current /= component
            try:
                child = os.open(component, flags, dir_fd=descriptor)
            except OSError as exc:
                raise ExecutionCollectionError(
                    f"cannot open {label} without following symlinks at {current}: {exc}"
                ) from exc
            os.close(descriptor)
            descriptor = child
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _read_regular_file_at(parent_descriptor: int, name: str, display: Path) -> bytes:
    """Read a named child while its already-verified parent descriptor is pinned."""

    try:
        before = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
    except OSError as exc:
        raise ExecutionCollectionError(f"cannot stat required file {display}: {exc}") from exc
    if not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode):
        raise ExecutionCollectionError(
            f"required file is not a regular non-symlink: {display}"
        )
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(name, flags, dir_fd=parent_descriptor)
    except OSError as exc:
        raise ExecutionCollectionError(f"cannot open required file {display}: {exc}") from exc
    try:
        opened = os.fstat(descriptor)
        identity = (
            opened.st_dev,
            opened.st_ino,
            opened.st_size,
            opened.st_mtime_ns,
        )
        if not stat.S_ISREG(opened.st_mode) or identity != (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        ):
            raise ExecutionCollectionError(f"evidence changed before it was opened: {display}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if identity != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise ExecutionCollectionError(f"evidence changed while being read: {display}")
    try:
        named_after = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
    except OSError as exc:
        raise ExecutionCollectionError(
            f"evidence name changed while being read {display}: {exc}"
        ) from exc
    if identity != (
        named_after.st_dev,
        named_after.st_ino,
        named_after.st_size,
        named_after.st_mtime_ns,
    ):
        raise ExecutionCollectionError(f"evidence name changed while being read: {display}")
    payload = b"".join(chunks)
    if len(payload) != opened.st_size:
        raise ExecutionCollectionError(f"short read for evidence file: {display}")
    return payload


def _lstat_no_follow(path: Path, label: str, *, missing_ok: bool = False) -> os.stat_result | None:
    path = _absolute_no_resolve(path)
    parent_descriptor = _open_directory_fd(path.parent, f"parent of {label}")
    try:
        try:
            return os.stat(path.name, dir_fd=parent_descriptor, follow_symlinks=False)
        except FileNotFoundError as exc:
            if missing_ok:
                return None
            raise ExecutionCollectionError(f"cannot stat {label} {path}: {exc}") from exc
        except OSError as exc:
            raise ExecutionCollectionError(f"cannot stat {label} {path}: {exc}") from exc
    finally:
        os.close(parent_descriptor)


def _mkdir_parents_no_follow(path: Path, label: str) -> None:
    """Create missing directory components without ever following a symlink."""

    path = _absolute_no_resolve(path)
    parts = path.parts
    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        descriptor = os.open(parts[0], flags)
    except OSError as exc:
        raise ExecutionCollectionError(f"cannot anchor {label}: {exc}") from exc
    current = Path(parts[0])
    try:
        for component in parts[1:]:
            current /= component
            try:
                child = os.open(component, flags, dir_fd=descriptor)
            except FileNotFoundError:
                try:
                    os.mkdir(component, mode=0o777, dir_fd=descriptor)
                except FileExistsError:
                    pass
                except OSError as exc:
                    raise ExecutionCollectionError(
                        f"cannot create {label} component {current}: {exc}"
                    ) from exc
                try:
                    child = os.open(component, flags, dir_fd=descriptor)
                except OSError as exc:
                    raise ExecutionCollectionError(
                        f"cannot pin newly created {label} component {current}: {exc}"
                    ) from exc
            except OSError as exc:
                raise ExecutionCollectionError(
                    f"cannot traverse {label} without following symlinks at {current}: {exc}"
                ) from exc
            os.close(descriptor)
            descriptor = child
    finally:
        os.close(descriptor)


def _require_regular_directory(path: Path, label: str) -> list[Path]:
    path = _absolute_no_resolve(path)
    descriptor = _open_directory_fd(path, label)
    try:
        names = os.listdir(descriptor)
    except OSError as exc:
        raise ExecutionCollectionError(f"cannot enumerate {label} {path}: {exc}") from exc
    finally:
        os.close(descriptor)
    return [path / name for name in names]


def _require_regular_file_entries(entries: Iterable[Path], label: str) -> None:
    for entry in entries:
        metadata = _lstat_no_follow(entry, f"{label} entry")
        if metadata is None or not stat.S_ISREG(metadata.st_mode):
            raise ExecutionCollectionError(f"{label} contains non-regular evidence: {entry}")


def _validated_spec_index(path: Path) -> tuple[list[str], list[dict[str, Any]], str]:
    document, payload = _load_json_strict_with_payload(path, canonical=True)
    if document.get("schema_version") != SPEC_INDEX_SCHEMA:
        raise ExecutionCollectionError("certification spec index has an unknown schema")
    rows = document.get("specs")
    if not isinstance(rows, list):
        raise ExecutionCollectionError("certification spec index rows are malformed")
    ids: list[str] = []
    for ordinal, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ExecutionCollectionError(f"spec row {ordinal} is not an object")
        instance_id = row.get("instance_id")
        if not isinstance(instance_id, str) or INSTANCE_ID_RE.fullmatch(instance_id) is None:
            raise ExecutionCollectionError(f"spec row {ordinal} has an unsafe instance id")
        if not isinstance(row.get("identical_to_gold"), bool):
            raise ExecutionCollectionError(
                f"spec row {ordinal} has invalid gold-equivalence metadata"
            )
        if not isinstance(row.get("scenario_available"), bool):
            raise ExecutionCollectionError(
                f"spec row {ordinal} has invalid scenario-availability metadata"
            )
        ids.append(instance_id)
    if len(ids) != len(set(ids)):
        raise ExecutionCollectionError("certification spec index contains duplicate ids")
    if not _is_plain_int(document.get("count")) or document.get("count") != len(ids):
        raise ExecutionCollectionError("certification spec index count is inconsistent")
    return ids, rows, _sha256(payload)


def _validate_stage_summary_relationships(
    *,
    target_ids: list[str],
    ordered_ids: list[str],
    spec_rows: list[dict[str, Any]],
    solve: dict[str, Any],
    scenarios: dict[str, Any],
) -> None:
    """Prove that the certification index is the complete valid-solution cohort."""

    solve_manifest = solve.get("manifest")
    solution_count = solve.get("solutions")
    target_count = solve.get("targets")
    if (
        not isinstance(solve_manifest, list)
        or not _is_plain_int(solution_count)
        or not _is_plain_int(target_count)
        or target_count != len(solve_manifest)
    ):
        raise ExecutionCollectionError("solve summary counts or manifest are malformed")
    solve_ids: list[str] = []
    solution_rows: list[dict[str, Any]] = []
    for ordinal, row in enumerate(solve_manifest):
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("instance_id"), str)
            or INSTANCE_ID_RE.fullmatch(row["instance_id"]) is None
            or not isinstance(row.get("status"), str)
        ):
            raise ExecutionCollectionError(f"solve summary row {ordinal} is malformed")
        solve_ids.append(row["instance_id"])
        if row["status"] == "solution":
            if not isinstance(row.get("identical_to_gold"), bool):
                raise ExecutionCollectionError(
                    f"solve solution row {ordinal} has invalid gold-equivalence metadata"
                )
            solution_rows.append(row)
    if len(solve_ids) != len(set(solve_ids)):
        raise ExecutionCollectionError("solve summary contains duplicate instance ids")
    if target_count != TARGET_COUNT or solve_ids != target_ids:
        raise ExecutionCollectionError(
            "solve summary does not exactly cover the frozen 53-target order"
        )
    if solution_count != len(solution_rows):
        raise ExecutionCollectionError("solve summary solution count is inconsistent")
    solution_ids = [row["instance_id"] for row in solution_rows]
    if solution_ids != ordered_ids:
        raise ExecutionCollectionError(
            "certification spec index does not exactly cover ordered valid solutions"
        )
    for ordinal, (spec, solution) in enumerate(zip(spec_rows, solution_rows, strict=True)):
        if spec["identical_to_gold"] != solution["identical_to_gold"]:
            raise ExecutionCollectionError(
                f"spec/solve gold-equivalence metadata differs at row {ordinal}"
            )

    scenario_manifest = scenarios.get("manifest")
    scenario_count = scenarios.get("scenarios")
    differing_count = scenarios.get("differing_solutions")
    differing_ids = [
        row["instance_id"] for row in solution_rows if not row["identical_to_gold"]
    ]
    if (
        not isinstance(scenario_manifest, list)
        or not _is_plain_int(scenario_count)
        or not _is_plain_int(differing_count)
        or differing_count != len(differing_ids)
    ):
        raise ExecutionCollectionError("scenario summary counts or manifest are malformed")
    scenario_ids_seen: list[str] = []
    available_ids: list[str] = []
    allowed_statuses = {"no_scenario", "no_src", "provider_error", "scenario"}
    for ordinal, row in enumerate(scenario_manifest):
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("instance_id"), str)
            or INSTANCE_ID_RE.fullmatch(row["instance_id"]) is None
            or row.get("status") not in allowed_statuses
        ):
            raise ExecutionCollectionError(f"scenario summary row {ordinal} is malformed")
        instance_id = row["instance_id"]
        if instance_id not in differing_ids:
            raise ExecutionCollectionError(
                f"scenario summary row {ordinal} is not a differing valid solution"
            )
        scenario_ids_seen.append(instance_id)
        if row["status"] == "scenario":
            available_ids.append(instance_id)
    if len(scenario_ids_seen) != len(set(scenario_ids_seen)):
        raise ExecutionCollectionError("scenario summary contains duplicate instance ids")
    if len(scenario_ids_seen) < min(len(differing_ids), SCENARIO_CALL_CEILING):
        raise ExecutionCollectionError(
            "scenario summary does not cover every differing solution required before the call cap"
        )
    expected_manifest_order = [
        instance_id for instance_id in differing_ids if instance_id in set(scenario_ids_seen)
    ]
    if scenario_ids_seen != expected_manifest_order:
        raise ExecutionCollectionError("scenario summary order differs from valid-solution order")
    if scenario_count != len(available_ids):
        raise ExecutionCollectionError("scenario summary scenario count is inconsistent")
    indexed_available_ids = [
        row["instance_id"] for row in spec_rows if row["scenario_available"]
    ]
    if indexed_available_ids != available_ids:
        raise ExecutionCollectionError(
            "spec scenario availability does not exactly match scenario summary"
        )
    if any(
        row["identical_to_gold"] and row["scenario_available"] for row in spec_rows
    ):
        raise ExecutionCollectionError(
            "normalized gold-equivalent spec rows cannot require a scenario"
        )


def _validated_source_binding(spec_index: Path, runtime_manifest: Path) -> tuple[list[str], dict[str, str]]:
    ids, spec_rows, spec_sha256 = _validated_spec_index(spec_index)
    runtime, runtime_payload = _load_json_strict_with_payload(
        runtime_manifest, canonical=True
    )
    if (
        runtime.get("schema_version") != RUNTIME_MANIFEST_SCHEMA
        or runtime.get("experiment_id") != EXPERIMENT_ID
    ):
        raise ExecutionCollectionError("runtime manifest identity is invalid")
    raw_root = spec_index.parent.parent
    solve_targets_path = raw_root / "solve_targets.json"
    solve_summary = raw_root / "solutions/solve_summary.json"
    scenarios_summary = raw_root / "scenarios/scenarios_summary.json"
    solve_targets, solve_targets_payload = _load_json_strict_with_payload(
        solve_targets_path, canonical=True
    )
    solve, solve_payload = _load_json_strict_with_payload(solve_summary, canonical=True)
    scenarios, scenarios_payload = _load_json_strict_with_payload(
        scenarios_summary, canonical=True
    )
    target_rows = solve_targets.get("targets")
    if (
        solve_targets.get("schema_version") != TARGET_SCHEMA
        or not _is_plain_int(solve_targets.get("count"))
        or solve_targets["count"] != TARGET_COUNT
        or not isinstance(target_rows, list)
        or len(target_rows) != TARGET_COUNT
    ):
        raise ExecutionCollectionError("frozen solve-target manifest is malformed")
    target_ids: list[str] = []
    for ordinal, row in enumerate(target_rows):
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("instance_id"), str)
            or INSTANCE_ID_RE.fullmatch(row["instance_id"]) is None
        ):
            raise ExecutionCollectionError(
                f"frozen solve-target row {ordinal} has an unsafe instance id"
            )
        target_ids.append(row["instance_id"])
    if len(target_ids) != len(set(target_ids)):
        raise ExecutionCollectionError("frozen solve-target manifest contains duplicate ids")
    if solve.get("schema_version") != SOLVE_SUMMARY_SCHEMA:
        raise ExecutionCollectionError("solve summary has an unknown schema")
    if scenarios.get("schema_version") != SCENARIOS_SUMMARY_SCHEMA:
        raise ExecutionCollectionError("scenario summary has an unknown schema")
    _validate_stage_summary_relationships(
        target_ids=target_ids,
        ordered_ids=ids,
        spec_rows=spec_rows,
        solve=solve,
        scenarios=scenarios,
    )
    return ids, {
        "runtime_manifest_sha256": _sha256(runtime_payload),
        "scenarios_summary_sha256": _sha256(scenarios_payload),
        "solve_summary_sha256": _sha256(solve_payload),
        "solve_targets_sha256": _sha256(solve_targets_payload),
        "spec_index_sha256": spec_sha256,
    }


def _github_from_environment(*, required: bool) -> dict[str, str] | None:
    names = (
        "GITHUB_RUN_ID",
        "GITHUB_RUN_ATTEMPT",
        "GITHUB_SHA",
        "GITHUB_REPOSITORY",
        "GITHUB_WORKFLOW_REF",
    )
    values = [os.environ.get(name) for name in names]
    if not any(values):
        if required:
            raise ExecutionCollectionError(
                "complete GitHub run/repository/workflow provenance is required"
            )
        return None
    if not all(values):
        raise ExecutionCollectionError("GitHub run provenance is only partially defined")
    run_id, run_attempt, sha, repository, workflow_ref = values
    assert all(value is not None for value in values)
    github = {
        "repository": repository,
        "run_attempt": run_attempt,
        "run_id": run_id,
        "sha": sha,
        "workflow_ref": workflow_ref,
    }
    _validate_github(github, "GitHub environment")
    return github


def _validate_github(value: Any, label: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ExecutionCollectionError(f"{label} is not an object")
    _require_exact_keys(value, GITHUB_KEYS, label)
    if not all(isinstance(value[key], str) for key in GITHUB_KEYS):
        raise ExecutionCollectionError(f"{label} fields must be strings")
    if POSITIVE_INTEGER_RE.fullmatch(value["run_id"]) is None:
        raise ExecutionCollectionError(f"{label} run id is invalid")
    if POSITIVE_INTEGER_RE.fullmatch(value["run_attempt"]) is None:
        raise ExecutionCollectionError(f"{label} run attempt is invalid")
    if GITHUB_SHA_RE.fullmatch(value["sha"]) is None:
        raise ExecutionCollectionError(f"{label} commit SHA is invalid")
    if GITHUB_REPOSITORY_RE.fullmatch(value["repository"]) is None:
        raise ExecutionCollectionError(f"{label} repository is invalid")
    workflow_prefix = f"{value['repository']}/.github/workflows/iter202-execute.yml@"
    if (
        not value["workflow_ref"].startswith(workflow_prefix)
        or len(value["workflow_ref"]) > 512
        or any(character.isspace() or ord(character) < 32 for character in value["workflow_ref"])
    ):
        raise ExecutionCollectionError(f"{label} workflow ref is invalid")
    return value


def _require_current_checkout_sha(github: dict[str, str]) -> None:
    """Bind workflow receipts to the checkout; offline verification stays Git-independent."""

    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ExecutionCollectionError(f"cannot bind receipt to checked-out commit: {exc}") from exc
    head = completed.stdout.strip()
    if head != github["sha"]:
        raise ExecutionCollectionError(
            f"checked-out commit {head!r} differs from GITHUB_SHA {github['sha']!r}"
        )


def shard_receipt_name(index: int) -> str:
    return f"_telos_iter202_shard_{index}_of_8.receipt.json"


def artifact_name(github: dict[str, str], index: int) -> str:
    return (
        f"iter202-execution-run-{github['run_id']}-attempt-{github['run_attempt']}-"
        f"shard-{index}-of-8"
    )


def _expected_log_names(ids: Iterable[str]) -> list[str]:
    return [f"{instance_id}.{kind}.log" for instance_id in ids for kind in ("gold", "variant")]


def _file_record(path: Path) -> dict[str, Any]:
    payload = _read_regular_file(path)
    return {"bytes": len(payload), "name": path.name, "sha256": _sha256(payload)}


def _expected_shard_document(
    *,
    execution_dir: Path,
    ordered_ids: list[str],
    source: dict[str, str],
    github: dict[str, str],
    index: int,
) -> dict[str, Any]:
    assigned = [instance_id for ordinal, instance_id in enumerate(ordered_ids) if ordinal % SHARD_COUNT == index]
    logs = [_file_record(execution_dir / name) for name in _expected_log_names(assigned)]
    return {
        "assignment": {
            "method": ASSIGNMENT_METHOD,
            "ordered_instance_ids": assigned,
            "shard_count": SHARD_COUNT,
            "shard_index": index,
        },
        "experiment_id": EXPERIMENT_ID,
        "github": github,
        "logs": logs,
        "schema_version": SHARD_SCHEMA,
        "source": source,
    }


def _fsync_directory(path: Path) -> None:
    path = _absolute_no_resolve(path)
    descriptor = _open_directory_fd(path, f"directory fsync path {path}")
    try:
        os.fsync(descriptor)
    except OSError as exc:
        raise ExecutionCollectionError(f"cannot fsync directory {path}: {exc}") from exc
    finally:
        os.close(descriptor)


def _materialize_once(path: Path, payload: bytes) -> None:
    """Atomically create an immutable file, or prove an existing file identical."""

    path = _absolute_no_resolve(path)
    _mkdir_parents_no_follow(path.parent, f"parent of materialization path {path}")
    parent_descriptor = _open_directory_fd(path.parent, f"parent of materialization path {path}")
    existing = None
    try:
        try:
            existing = os.stat(path.name, dir_fd=parent_descriptor, follow_symlinks=False)
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise ExecutionCollectionError(f"cannot stat materialization path {path}: {exc}") from exc
        if existing is not None:
            if not stat.S_ISREG(existing.st_mode) or _read_regular_file_at(
                parent_descriptor, path.name, path
            ) != payload:
                raise ExecutionCollectionError(
                    f"refusing to overwrite divergent evidence: {path}"
                )
            return
    finally:
        if existing is not None:
            os.close(parent_descriptor)
    temporary_name = f".{path.name}.{os.getpid()}.{secrets.token_hex(8)}.tmp"
    temporary = path.parent / temporary_name
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    temporary_created = False
    try:
        descriptor = os.open(temporary_name, flags, 0o600, dir_fd=parent_descriptor)
        temporary_created = True
        try:
            view = memoryview(payload)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise ExecutionCollectionError(
                        f"short write for temporary evidence: {temporary}"
                    )
                view = view[written:]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        try:
            os.link(
                temporary_name,
                path.name,
                src_dir_fd=parent_descriptor,
                dst_dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except FileExistsError:
            if _read_regular_file_at(parent_descriptor, path.name, path) != payload:
                raise ExecutionCollectionError(f"concurrent divergent evidence appeared: {path}")
        os.fsync(parent_descriptor)
    finally:
        if temporary_created:
            try:
                os.unlink(temporary_name, dir_fd=parent_descriptor)
            except FileNotFoundError:
                pass
        os.close(parent_descriptor)


def create_shard_receipt(
    *,
    execution_dir: Path,
    spec_index: Path,
    runtime_manifest: Path,
    shard_index: int,
    shard_count: int,
) -> Path:
    """Create the canonical receipt for one successful workflow shard."""

    if shard_count != SHARD_COUNT or shard_index not in range(SHARD_COUNT):
        raise ExecutionCollectionError("iter202 shard receipt requires index 0..7 and count 8")
    github = _github_from_environment(required=True)
    assert github is not None
    _require_current_checkout_sha(github)
    ordered_ids, source = _validated_source_binding(spec_index, runtime_manifest)
    assigned = [instance_id for ordinal, instance_id in enumerate(ordered_ids) if ordinal % SHARD_COUNT == shard_index]
    receipt_path = execution_dir / shard_receipt_name(shard_index)
    expected_entries = set(_expected_log_names(assigned))
    entries = _require_regular_directory(execution_dir, "shard execution directory")
    actual_names = {entry.name for entry in entries}
    allowed_names = expected_entries | ({receipt_path.name} if receipt_path.name in actual_names else set())
    if actual_names != allowed_names:
        raise ExecutionCollectionError(
            f"shard {shard_index} file set differs: expected {sorted(allowed_names)}, got {sorted(actual_names)}"
        )
    _require_regular_file_entries(entries, f"shard {shard_index}")
    document = _expected_shard_document(
        execution_dir=execution_dir,
        ordered_ids=ordered_ids,
        source=source,
        github=github,
        index=shard_index,
    )
    _materialize_once(receipt_path, canonical_json_bytes(document))
    return receipt_path


def _validate_file_record(record: Any, *, aggregate: bool, label: str) -> None:
    if not isinstance(record, dict):
        raise ExecutionCollectionError(f"{label} is not an object")
    _require_exact_keys(record, AGGREGATE_LOG_KEYS if aggregate else FILE_KEYS, label)
    if not isinstance(record["name"], str) or "/" in record["name"] or "\\" in record["name"]:
        raise ExecutionCollectionError(f"{label} has an unsafe file name")
    if not _is_plain_int(record["bytes"]) or record["bytes"] < 0:
        raise ExecutionCollectionError(f"{label} has an invalid byte count")
    if not isinstance(record["sha256"], str) or SHA256_RE.fullmatch(record["sha256"]) is None:
        raise ExecutionCollectionError(f"{label} has an invalid SHA-256")
    if aggregate and (
        not _is_plain_int(record["shard_index"])
        or record["shard_index"] not in range(SHARD_COUNT)
    ):
        raise ExecutionCollectionError(f"{label} has an invalid shard index")


def _validate_shard_receipt(
    *,
    receipt_path: Path,
    log_root: Path,
    ordered_ids: list[str],
    source: dict[str, str],
    expected_github: dict[str, str],
    expected_index: int,
) -> dict[str, Any]:
    document = load_json_strict(receipt_path, canonical=True)
    _require_exact_keys(document, SHARD_TOP_KEYS, "shard receipt")
    if document["schema_version"] != SHARD_SCHEMA or document["experiment_id"] != EXPERIMENT_ID:
        raise ExecutionCollectionError(f"shard {expected_index} receipt identity is invalid")
    if document["source"] != source:
        raise ExecutionCollectionError(f"shard {expected_index} source hashes differ")
    if document["github"] != expected_github:
        raise ExecutionCollectionError(f"shard {expected_index} GitHub provenance differs")
    assignment = document["assignment"]
    if not isinstance(assignment, dict):
        raise ExecutionCollectionError(f"shard {expected_index} assignment is not an object")
    _require_exact_keys(assignment, ASSIGNMENT_KEYS, "shard assignment")
    if (
        not _is_plain_int(assignment.get("shard_count"))
        or not _is_plain_int(assignment.get("shard_index"))
        or not isinstance(assignment.get("ordered_instance_ids"), list)
    ):
        raise ExecutionCollectionError(f"shard {expected_index} assignment types are invalid")
    assigned = [instance_id for ordinal, instance_id in enumerate(ordered_ids) if ordinal % SHARD_COUNT == expected_index]
    expected_assignment = {
        "method": ASSIGNMENT_METHOD,
        "ordered_instance_ids": assigned,
        "shard_count": SHARD_COUNT,
        "shard_index": expected_index,
    }
    if assignment != expected_assignment:
        raise ExecutionCollectionError(f"shard {expected_index} assignment differs")
    logs = document["logs"]
    if not isinstance(logs, list):
        raise ExecutionCollectionError(f"shard {expected_index} logs are not a list")
    for ordinal, record in enumerate(logs):
        _validate_file_record(record, aggregate=False, label=f"shard {expected_index} log {ordinal}")
    expected_names = _expected_log_names(assigned)
    if [record["name"] for record in logs] != expected_names:
        raise ExecutionCollectionError(f"shard {expected_index} log order or names differ")
    expected_document = _expected_shard_document(
        execution_dir=log_root,
        ordered_ids=ordered_ids,
        source=source,
        github=expected_github,
        index=expected_index,
    )
    if document != expected_document:
        raise ExecutionCollectionError(f"shard {expected_index} log hashes or byte counts differ")
    return document


def _infer_artifact_identity(entries: list[Path]) -> tuple[dict[str, str], dict[int, Path]]:
    by_index: dict[int, Path] = {}
    run_ids: set[str] = set()
    attempts: set[str] = set()
    for entry in entries:
        metadata = _lstat_no_follow(entry, "artifact root entry")
        if metadata is None or not stat.S_ISDIR(metadata.st_mode):
            raise ExecutionCollectionError(f"artifact root contains a non-directory entry: {entry}")
        match = ARTIFACT_RE.fullmatch(entry.name)
        if match is None:
            raise ExecutionCollectionError(f"unexpected collector artifact directory: {entry.name}")
        run_id, attempt, index_text = match.groups()
        index = int(index_text)
        if index in by_index:
            raise ExecutionCollectionError(f"duplicate shard artifact index: {index}")
        by_index[index] = entry
        run_ids.add(run_id)
        attempts.add(attempt)
    if set(by_index) != set(range(SHARD_COUNT)):
        raise ExecutionCollectionError(
            f"collector requires exact shard indexes 0..7, got {sorted(by_index)}"
        )
    if len(run_ids) != 1 or len(attempts) != 1:
        raise ExecutionCollectionError("artifact directories mix GitHub runs or attempts")
    run_id = next(iter(run_ids))
    attempt = next(iter(attempts))
    environment = _github_from_environment(required=False)
    if environment is not None and (
        environment["run_id"] != run_id or environment["run_attempt"] != attempt
    ):
        raise ExecutionCollectionError("artifact directories are not from the current GitHub run attempt")
    github = {
        "repository": environment["repository"] if environment is not None else "",
        "run_attempt": attempt,
        "run_id": run_id,
        "sha": environment["sha"] if environment is not None else "",
        "workflow_ref": environment["workflow_ref"] if environment is not None else "",
    }
    return github, by_index


def _write_staged_file(path: Path, payload: bytes) -> None:
    path = _absolute_no_resolve(path)
    parent_descriptor = _open_directory_fd(path.parent, f"parent of staged-write path {path}")
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        descriptor = os.open(path.name, flags, 0o600, dir_fd=parent_descriptor)
    except OSError as exc:
        os.close(parent_descriptor)
        raise ExecutionCollectionError(f"cannot create staged file {path}: {exc}") from exc
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise ExecutionCollectionError(f"short write while collecting {path}")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
        os.close(parent_descriptor)


def _create_staging_directory_at(
    parent_descriptor: int, name: str, display: Path
) -> None:
    try:
        os.mkdir(name, mode=0o700, dir_fd=parent_descriptor)
        os.fsync(parent_descriptor)
    except OSError as exc:
        raise ExecutionCollectionError(f"cannot create staging directory {display}: {exc}") from exc


def _directory_names_at(parent_descriptor: int, name: str, display: Path) -> list[str]:
    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        descriptor = os.open(name, flags, dir_fd=parent_descriptor)
    except OSError as exc:
        raise ExecutionCollectionError(
            f"cannot open directory without following symlinks {display}: {exc}"
        ) from exc
    try:
        return os.listdir(descriptor)
    except OSError as exc:
        raise ExecutionCollectionError(f"cannot enumerate directory {display}: {exc}") from exc
    finally:
        os.close(descriptor)


def _remove_staging_directory_at(
    parent_descriptor: int, name: str, display: Path
) -> None:
    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        descriptor = os.open(name, flags, dir_fd=parent_descriptor)
    except FileNotFoundError:
        return
    except OSError as exc:
        raise ExecutionCollectionError(
            f"cannot open staging directory without following symlinks {display}: {exc}"
        ) from exc
    opened = os.fstat(descriptor)
    try:
        names = os.listdir(descriptor)
        for child_name in names:
            metadata = os.stat(
                child_name, dir_fd=descriptor, follow_symlinks=False
            )
            if not stat.S_ISREG(metadata.st_mode):
                raise ExecutionCollectionError(
                    f"refusing to remove non-regular staging entry: {display / child_name}"
                )
            os.unlink(child_name, dir_fd=descriptor)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    try:
        named_after = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
    except OSError as exc:
        raise ExecutionCollectionError(
            f"staging directory name changed before removal {display}: {exc}"
        ) from exc
    if (opened.st_dev, opened.st_ino) != (named_after.st_dev, named_after.st_ino):
        raise ExecutionCollectionError(
            f"staging directory name changed before removal: {display}"
        )
    try:
        os.rmdir(name, dir_fd=parent_descriptor)
        os.fsync(parent_descriptor)
    except OSError as exc:
        raise ExecutionCollectionError(f"cannot remove staging directory {display}: {exc}") from exc


def _aggregate_document(
    *,
    execution_dir: Path,
    ordered_ids: list[str],
    source: dict[str, str],
    github: dict[str, str],
    receipts: list[dict[str, Any]],
) -> dict[str, Any]:
    shards: list[dict[str, Any]] = []
    log_shard_by_name: dict[str, int] = {}
    for index, receipt in enumerate(receipts):
        receipt_path = execution_dir / shard_receipt_name(index)
        receipt_payload = _read_regular_file(receipt_path)
        assigned = receipt["assignment"]["ordered_instance_ids"]
        shards.append(
            {
                "artifact_name": artifact_name(github, index),
                "ordered_instance_ids": assigned,
                "receipt_bytes": len(receipt_payload),
                "receipt_name": receipt_path.name,
                "receipt_sha256": _sha256(receipt_payload),
                "shard_index": index,
            }
        )
        for record in receipt["logs"]:
            if record["name"] in log_shard_by_name:
                raise ExecutionCollectionError(f"duplicate log across shard receipts: {record['name']}")
            log_shard_by_name[record["name"]] = index
    expected_names = _expected_log_names(ordered_ids)
    if set(log_shard_by_name) != set(expected_names):
        raise ExecutionCollectionError("shard receipt union does not exactly cover the spec index")
    logs: list[dict[str, Any]] = []
    for name in expected_names:
        record = _file_record(execution_dir / name)
        record["shard_index"] = log_shard_by_name[name]
        logs.append(record)
    return {
        "assignment": {
            "method": ASSIGNMENT_METHOD,
            "ordered_instance_ids": ordered_ids,
            "shard_count": SHARD_COUNT,
        },
        "experiment_id": EXPERIMENT_ID,
        "github": github,
        "logs": logs,
        "schema_version": AGGREGATE_SCHEMA,
        "shards": shards,
        "source": source,
    }


def collect_shards(
    *,
    artifacts_dir: Path,
    output_dir: Path,
    aggregate_receipt: Path,
    spec_index: Path = DEFAULT_SPEC_INDEX,
    runtime_manifest: Path = DEFAULT_RUNTIME_MANIFEST,
) -> dict[str, Any]:
    """Collect exactly eight same-attempt shard artifacts through atomic staging."""

    aggregate_receipt = _absolute_no_resolve(aggregate_receipt)
    output_dir = _absolute_no_resolve(output_dir)
    artifacts_dir = _absolute_no_resolve(artifacts_dir)
    spec_index = _absolute_no_resolve(spec_index)
    runtime_manifest = _absolute_no_resolve(runtime_manifest)
    _reject_symlink_components(output_dir, "collector output path")
    _reject_symlink_components(aggregate_receipt, "aggregate receipt path")
    if aggregate_receipt != output_dir / AGGREGATE_RECEIPT_NAME:
        raise ExecutionCollectionError("aggregate receipt must use the frozen name inside output-dir")
    ordered_ids, source = _validated_source_binding(spec_index, runtime_manifest)
    artifact_entries = _require_regular_directory(artifacts_dir, "artifact download root")
    github_hint, by_index = _infer_artifact_identity(artifact_entries)
    environment = _github_from_environment(required=False)
    if environment is not None:
        _require_current_checkout_sha(environment)
    receipts: list[dict[str, Any]] = []
    github: dict[str, str] | None = None
    source_files: dict[str, Path] = {}
    for index in range(SHARD_COUNT):
        directory = by_index[index]
        receipt_path = directory / shard_receipt_name(index)
        provisional = load_json_strict(receipt_path, canonical=True)
        candidate_github = _validate_github(
            provisional.get("github"), f"shard {index} GitHub provenance"
        )
        if github is None:
            github = candidate_github
        elif candidate_github != github:
            raise ExecutionCollectionError("shard receipts mix GitHub provenance")
        if candidate_github["run_id"] != github_hint["run_id"] or candidate_github["run_attempt"] != github_hint["run_attempt"]:
            raise ExecutionCollectionError(f"shard {index} receipt/artifact run identity differs")
        if environment is not None and candidate_github != environment:
            raise ExecutionCollectionError(f"shard {index} is not from the current GitHub run attempt")
        receipt = _validate_shard_receipt(
            receipt_path=receipt_path,
            log_root=directory,
            ordered_ids=ordered_ids,
            source=source,
            expected_github=candidate_github,
            expected_index=index,
        )
        expected_entries = set(_expected_log_names(receipt["assignment"]["ordered_instance_ids"])) | {
            receipt_path.name
        }
        entries = _require_regular_directory(directory, f"shard {index} artifact")
        if {entry.name for entry in entries} != expected_entries:
            raise ExecutionCollectionError(f"shard {index} artifact contains missing or extra files")
        _require_regular_file_entries(entries, f"shard {index} artifact")
        for name in expected_entries:
            if name in source_files:
                raise ExecutionCollectionError(f"collector file collision: {name}")
            source_files[name] = directory / name
        receipts.append(receipt)
    assert github is not None

    output_parent = output_dir.parent
    _mkdir_parents_no_follow(output_parent, "collector output parent")
    parent_descriptor = _open_directory_fd(output_parent, "collector output parent")
    staging_name = f".{output_dir.name}.{os.getpid()}.{secrets.token_hex(8)}.collecting"
    staging = output_parent / staging_name
    staging_exists = False
    try:
        _create_staging_directory_at(parent_descriptor, staging_name, staging)
        staging_exists = True
        for name in sorted(source_files):
            _write_staged_file(staging / name, _read_regular_file(source_files[name]))
        aggregate = _aggregate_document(
            execution_dir=staging,
            ordered_ids=ordered_ids,
            source=source,
            github=github,
            receipts=receipts,
        )
        _write_staged_file(staging / AGGREGATE_RECEIPT_NAME, canonical_json_bytes(aggregate))
        _fsync_directory(staging)
        checked = check_execution_bundle(
            execution_dir=staging,
            aggregate_receipt=staging / AGGREGATE_RECEIPT_NAME,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
        )
        try:
            output_metadata = os.stat(
                output_dir.name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            output_metadata = None
        except OSError as exc:
            raise ExecutionCollectionError(
                f"cannot inspect collector output {output_dir}: {exc}"
            ) from exc
        if output_metadata is not None:
            if not stat.S_ISDIR(output_metadata.st_mode):
                raise ExecutionCollectionError(
                    f"collector output is not a non-symlink directory: {output_dir}"
                )
            output_names = _directory_names_at(
                parent_descriptor, output_dir.name, output_dir
            )
            if output_names:
                raise ExecutionCollectionError(f"refusing to overwrite non-empty collector output: {output_dir}")
            os.rmdir(output_dir.name, dir_fd=parent_descriptor)
        os.replace(
            staging_name,
            output_dir.name,
            src_dir_fd=parent_descriptor,
            dst_dir_fd=parent_descriptor,
        )
        staging_exists = False
        os.fsync(parent_descriptor)
    finally:
        if staging_exists:
            _remove_staging_directory_at(parent_descriptor, staging_name, staging)
        os.close(parent_descriptor)
    return checked


def check_execution_bundle(
    *,
    execution_dir: Path,
    aggregate_receipt: Path,
    spec_index: Path = DEFAULT_SPEC_INDEX,
    runtime_manifest: Path = DEFAULT_RUNTIME_MANIFEST,
) -> dict[str, Any]:
    """Prove an aggregate bundle exact against current sources and retained bytes."""

    execution_dir = _absolute_no_resolve(execution_dir)
    aggregate_receipt = _absolute_no_resolve(aggregate_receipt)
    spec_index = _absolute_no_resolve(spec_index)
    runtime_manifest = _absolute_no_resolve(runtime_manifest)
    if aggregate_receipt != execution_dir / AGGREGATE_RECEIPT_NAME:
        raise ExecutionCollectionError("aggregate receipt path is not the frozen path")
    entries = _require_regular_directory(execution_dir, "aggregate execution directory")
    ordered_ids, source = _validated_source_binding(spec_index, runtime_manifest)
    aggregate = load_json_strict(aggregate_receipt, canonical=True)
    _require_exact_keys(aggregate, AGGREGATE_TOP_KEYS, "aggregate receipt")
    if aggregate["schema_version"] != AGGREGATE_SCHEMA or aggregate["experiment_id"] != EXPERIMENT_ID:
        raise ExecutionCollectionError("aggregate receipt identity is invalid")
    if aggregate["source"] != source:
        raise ExecutionCollectionError("aggregate source hashes differ from current evidence")
    github = _validate_github(aggregate["github"], "aggregate GitHub provenance")
    environment = _github_from_environment(required=False)
    if environment is not None and github != environment:
        raise ExecutionCollectionError("aggregate is not from the current GitHub run attempt")
    assignment = aggregate["assignment"]
    if not isinstance(assignment, dict):
        raise ExecutionCollectionError("aggregate assignment is not an object")
    _require_exact_keys(assignment, AGGREGATE_ASSIGNMENT_KEYS, "aggregate assignment")
    if (
        not _is_plain_int(assignment.get("shard_count"))
        or not isinstance(assignment.get("ordered_instance_ids"), list)
    ):
        raise ExecutionCollectionError("aggregate assignment types are invalid")
    if assignment != {
        "method": ASSIGNMENT_METHOD,
        "ordered_instance_ids": ordered_ids,
        "shard_count": SHARD_COUNT,
    }:
        raise ExecutionCollectionError("aggregate assignment differs from current spec order")

    shard_records = aggregate["shards"]
    if not isinstance(shard_records, list) or len(shard_records) != SHARD_COUNT:
        raise ExecutionCollectionError("aggregate receipt must contain exactly eight shard records")
    receipts: list[dict[str, Any]] = []
    for index, record in enumerate(shard_records):
        if not isinstance(record, dict):
            raise ExecutionCollectionError(f"aggregate shard record {index} is not an object")
        _require_exact_keys(record, SHARD_RECORD_KEYS, f"aggregate shard record {index}")
        if (
            not _is_plain_int(record.get("shard_index"))
            or not _is_plain_int(record.get("receipt_bytes"))
            or record["receipt_bytes"] < 0
            or not isinstance(record.get("artifact_name"), str)
            or not isinstance(record.get("receipt_name"), str)
            or not isinstance(record.get("receipt_sha256"), str)
            or SHA256_RE.fullmatch(record["receipt_sha256"]) is None
            or not isinstance(record.get("ordered_instance_ids"), list)
        ):
            raise ExecutionCollectionError(
                f"aggregate shard record {index} types are invalid"
            )
        receipt_name = shard_receipt_name(index)
        if (
            record["shard_index"] != index
            or record["artifact_name"] != artifact_name(github, index)
            or record["receipt_name"] != receipt_name
        ):
            raise ExecutionCollectionError(f"aggregate shard record {index} identity differs")
        receipt_path = execution_dir / receipt_name
        receipt_payload = _read_regular_file(receipt_path)
        if (
            record["receipt_bytes"] != len(receipt_payload)
            or record["receipt_sha256"] != _sha256(receipt_payload)
        ):
            raise ExecutionCollectionError(f"aggregate shard receipt binding differs for {index}")
        receipt = _validate_shard_receipt(
            receipt_path=receipt_path,
            log_root=execution_dir,
            ordered_ids=ordered_ids,
            source=source,
            expected_github=github,
            expected_index=index,
        )
        if record["ordered_instance_ids"] != receipt["assignment"]["ordered_instance_ids"]:
            raise ExecutionCollectionError(f"aggregate shard membership differs for {index}")
        receipts.append(receipt)

    logs = aggregate["logs"]
    if not isinstance(logs, list):
        raise ExecutionCollectionError("aggregate logs are not a list")
    for ordinal, record in enumerate(logs):
        _validate_file_record(record, aggregate=True, label=f"aggregate log {ordinal}")
    expected_entries = set(_expected_log_names(ordered_ids)) | {
        shard_receipt_name(index) for index in range(SHARD_COUNT)
    } | {AGGREGATE_RECEIPT_NAME}
    if {entry.name for entry in entries} != expected_entries:
        raise ExecutionCollectionError("aggregate execution directory has missing or extra files")
    _require_regular_file_entries(entries, "aggregate execution directory")
    expected_aggregate = _aggregate_document(
        execution_dir=execution_dir,
        ordered_ids=ordered_ids,
        source=source,
        github=github,
        receipts=receipts,
    )
    if aggregate != expected_aggregate:
        raise ExecutionCollectionError("aggregate log, shard, or receipt binding differs")
    return aggregate


def check_execution_bundle_with_logs(
    *,
    execution_dir: Path,
    aggregate_receipt: Path,
    spec_index: Path = DEFAULT_SPEC_INDEX,
    runtime_manifest: Path = DEFAULT_RUNTIME_MANIFEST,
) -> tuple[dict[str, Any], dict[str, bytes]]:
    """Verify a bundle and return the exact receipt-bound log-byte snapshot.

    Adjudication must consume these bytes rather than reopening mutable paths
    after verification. A replacement between the aggregate check and this
    snapshot is detected against the aggregate's retained byte count and hash.
    """

    execution_dir = _absolute_no_resolve(execution_dir)
    aggregate = check_execution_bundle(
        execution_dir=execution_dir,
        aggregate_receipt=aggregate_receipt,
        spec_index=spec_index,
        runtime_manifest=runtime_manifest,
    )
    log_bytes: dict[str, bytes] = {}
    for ordinal, record in enumerate(aggregate["logs"]):
        name = record["name"]
        payload = _read_regular_file(execution_dir / name)
        if len(payload) != record["bytes"] or _sha256(payload) != record["sha256"]:
            raise ExecutionCollectionError(
                f"aggregate log {ordinal} changed before the verified snapshot"
            )
        if name in log_bytes:
            raise ExecutionCollectionError(f"aggregate snapshot duplicates log name: {name}")
        log_bytes[name] = payload
    return aggregate, log_bytes


def ingest_execution_bundle(
    *,
    bundle_dir: Path,
    execution_dir: Path,
    spec_index: Path = DEFAULT_SPEC_INDEX,
    runtime_manifest: Path = DEFAULT_RUNTIME_MANIFEST,
    expected_run_id: str,
    expected_run_attempt: str,
    expected_github_sha: str,
) -> dict[str, Any]:
    """Validate a downloaded complete artifact and install it without overwrite."""

    bundle_dir = _absolute_no_resolve(bundle_dir)
    execution_dir = _absolute_no_resolve(execution_dir)
    spec_index = _absolute_no_resolve(spec_index)
    runtime_manifest = _absolute_no_resolve(runtime_manifest)
    _reject_symlink_components(bundle_dir, "downloaded bundle path")
    _reject_symlink_components(execution_dir, "execution destination path")
    document = check_execution_bundle(
        execution_dir=bundle_dir,
        aggregate_receipt=bundle_dir / AGGREGATE_RECEIPT_NAME,
        spec_index=spec_index,
        runtime_manifest=runtime_manifest,
    )
    if POSITIVE_INTEGER_RE.fullmatch(expected_run_id) is None:
        raise ExecutionCollectionError("expected GitHub run id is invalid")
    if POSITIVE_INTEGER_RE.fullmatch(expected_run_attempt) is None:
        raise ExecutionCollectionError("expected GitHub run attempt is invalid")
    if GITHUB_SHA_RE.fullmatch(expected_github_sha) is None:
        raise ExecutionCollectionError("expected GitHub commit SHA is invalid")
    actual_github = document["github"]
    if (
        actual_github["run_id"] != expected_run_id
        or actual_github["run_attempt"] != expected_run_attempt
        or actual_github["sha"] != expected_github_sha
    ):
        raise ExecutionCollectionError(
            "downloaded execution bundle differs from the operator-recorded run identity"
        )
    _mkdir_parents_no_follow(execution_dir.parent, "execution destination parent")
    destination_parent_descriptor = _open_directory_fd(
        execution_dir.parent, "execution destination parent"
    )
    try:
        destination_metadata = os.stat(
            execution_dir.name,
            dir_fd=destination_parent_descriptor,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        destination_metadata = None
    except OSError as exc:
        os.close(destination_parent_descriptor)
        raise ExecutionCollectionError(
            f"cannot inspect execution destination {execution_dir}: {exc}"
        ) from exc
    if destination_metadata is not None:
        try:
            try:
                existing = check_execution_bundle(
                    execution_dir=execution_dir,
                    aggregate_receipt=execution_dir / AGGREGATE_RECEIPT_NAME,
                    spec_index=spec_index,
                    runtime_manifest=runtime_manifest,
                )
            except ExecutionCollectionError as exc:
                raise ExecutionCollectionError(
                    f"refusing to overwrite existing execution evidence: {exc}"
                ) from exc
            if existing != document:
                raise ExecutionCollectionError(
                    "refusing to overwrite a different valid execution bundle"
                )
        finally:
            os.close(destination_parent_descriptor)
        return existing

    staging_name = f".{execution_dir.name}.{os.getpid()}.{secrets.token_hex(8)}.ingesting"
    staging = execution_dir.parent / staging_name
    staging_exists = False
    try:
        _create_staging_directory_at(
            destination_parent_descriptor, staging_name, staging
        )
        staging_exists = True
        entries = _require_regular_directory(bundle_dir, "downloaded execution bundle")
        for entry in sorted(entries, key=lambda path: path.name):
            _write_staged_file(staging / entry.name, _read_regular_file(entry))
        _fsync_directory(staging)
        checked = check_execution_bundle(
            execution_dir=staging,
            aggregate_receipt=staging / AGGREGATE_RECEIPT_NAME,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
        )
        os.replace(
            staging_name,
            execution_dir.name,
            src_dir_fd=destination_parent_descriptor,
            dst_dir_fd=destination_parent_descriptor,
        )
        staging_exists = False
        os.fsync(destination_parent_descriptor)
    finally:
        if staging_exists:
            _remove_staging_directory_at(
                destination_parent_descriptor, staging_name, staging
            )
        os.close(destination_parent_descriptor)
    return checked


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    shard = subparsers.add_parser("shard-receipt")
    shard.add_argument("--execution-dir", type=Path, required=True)
    shard.add_argument("--spec-index", type=Path, required=True)
    shard.add_argument("--runtime-manifest", type=Path, required=True)
    shard.add_argument("--shard-index", type=int, required=True)
    shard.add_argument("--shard-count", type=int, required=True)

    collect = subparsers.add_parser("collect")
    collect.add_argument("--artifacts-dir", type=Path, required=True)
    collect.add_argument("--output-dir", type=Path, required=True)
    collect.add_argument("--aggregate-receipt", type=Path, required=True)
    collect.add_argument("--spec-index", type=Path, default=DEFAULT_SPEC_INDEX)
    collect.add_argument("--runtime-manifest", type=Path, default=DEFAULT_RUNTIME_MANIFEST)

    check = subparsers.add_parser("check")
    check.add_argument("--execution-dir", type=Path, required=True)
    check.add_argument("--aggregate-receipt", type=Path, required=True)
    check.add_argument("--spec-index", type=Path, required=True)
    check.add_argument("--runtime-manifest", type=Path, required=True)

    ingest = subparsers.add_parser("ingest")
    ingest.add_argument("--bundle-dir", type=Path, required=True)
    ingest.add_argument("--execution-dir", type=Path, required=True)
    ingest.add_argument("--spec-index", type=Path, required=True)
    ingest.add_argument("--runtime-manifest", type=Path, required=True)
    ingest.add_argument("--expected-run-id", required=True)
    ingest.add_argument("--expected-run-attempt", required=True)
    ingest.add_argument("--expected-github-sha", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "shard-receipt":
            path = create_shard_receipt(
                execution_dir=args.execution_dir,
                spec_index=args.spec_index,
                runtime_manifest=args.runtime_manifest,
                shard_index=args.shard_index,
                shard_count=args.shard_count,
            )
            print(f"iter202 shard receipt complete: {path}")
        elif args.command == "collect":
            document = collect_shards(
                artifacts_dir=args.artifacts_dir,
                output_dir=args.output_dir,
                aggregate_receipt=args.aggregate_receipt,
                spec_index=args.spec_index,
                runtime_manifest=args.runtime_manifest,
            )
            print(
                "iter202 execution collection complete: "
                f"{len(document['shards'])} shards, {len(document['logs'])} logs"
            )
        elif args.command == "check":
            document = check_execution_bundle(
                execution_dir=args.execution_dir,
                aggregate_receipt=args.aggregate_receipt,
                spec_index=args.spec_index,
                runtime_manifest=args.runtime_manifest,
            )
            print(
                "iter202 execution bundle verifies: "
                f"{len(document['shards'])} shards, {len(document['logs'])} logs"
            )
        else:
            document = ingest_execution_bundle(
                bundle_dir=args.bundle_dir,
                execution_dir=args.execution_dir,
                spec_index=args.spec_index,
                runtime_manifest=args.runtime_manifest,
                expected_run_id=args.expected_run_id,
                expected_run_attempt=args.expected_run_attempt,
                expected_github_sha=args.expected_github_sha,
            )
            print(
                "iter202 execution bundle ingested: "
                f"{len(document['shards'])} shards, {len(document['logs'])} logs"
            )
    except ExecutionCollectionError as exc:
        print(f"iter202 execution collection failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
