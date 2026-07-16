#!/usr/bin/env python3
"""Build or verify the separately versioned iter203 evidence runtime.

The manifest closes over the fixed iter202 runtime, the complete iter203
safety-recovery bridge/projections, all 50 official certification specs, and
the exact execution, adjudication, and judge bytes.  It performs no provider calls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import build_iter203_safety_recovery as recovery  # noqa: E402
from scripts import collect_iter203_execution as collection  # noqa: E402


EXP = ROOT / "experiments/iter203_iter202_safety_recovery"
RAW = EXP / "proof/raw"
BRIDGE = RAW / "safety_recovery_bridge"
SOLUTIONS = RAW / "solutions"
SCENARIOS = RAW / "scenarios"
SPECS = RAW / "specs"
MANIFEST = RAW / "runtime_manifest.json"
UPSTREAM = ROOT / "experiments/iter202_natural_rate_scaled/proof/raw"

SCHEMA = "telos.iter203.execution_runtime.v1"
EXPERIMENT_ID = "iter203_iter202_safety_recovery"
UPSTREAM_SOURCE_COMMIT = "8b8809ed6b358d16eb08fe38f0f2edf4a284af0e"
UPSTREAM_RUNTIME_SHA256 = collection.UPSTREAM_RUNTIME_SHA256
VALID_PATCH_COUNT = 50
SAFE_SCENARIO_COUNT = 29

STATIC_RUNTIME_FILES = {
    ".github/workflows/iter203-execute.yml": "execution_workflow",
    "experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/swebench_verified_rows_snapshot.json": "frozen_judge_task_snapshot",
    "experiments/iter200_natural_certified_yet_wrong_rate/proof/audit_report.json": "corrected_iter200_pool_baseline",
    "experiments/iter202_natural_rate_scaled/proof/raw/sample_overlap_audit.json": "frozen_prior_use_strata",
    "experiments/iter203_iter202_safety_recovery/HYPOTHESIS.md": "recovery_protocol",
    "experiments/iter203_iter202_safety_recovery/UPSTREAM_PROTOCOL_NULL.md": "upstream_null_record",
    "scripts/adjudicate_iter203_safety_recovery.py": "all_patch_recovery_adjudicator",
    "scripts/build_iter203_runtime_manifest.py": "runtime_manifest_builder",
    "scripts/build_iter203_safety_recovery.py": "provider_free_bridge_builder",
    "scripts/ci_iter203_execute.sh": "certification_and_safe_witness_runner",
    "scripts/collect_iter202_execution.py": "shared_nofollow_atomic_filesystem_primitives",
    "scripts/collect_iter203_execution.py": "iter203_execution_chain_of_custody",
    "scripts/run_iter195_scenario_generator.py": "frozen_scenario_payload_extractor",
    "scripts/run_iter203_safety_recovery_blind_judge.py": "strict_blind_judge_and_rate_reporter",
    "scripts/validate_iter202_scenario_safety.py": "unchanged_frozen_safety_classifier",
    "telos/patch_normalization.py": "terminal_lf_patch_equivalence",
    "telos/secure_checkpoint_fs.py": "judge_checkpoint_filesystem",
    "telos/swebench_log_parsers.py": "official_certification_log_parsers",
}


class RuntimeManifestError(ValueError):
    """The iter203 runtime closure or one of its sealed inputs is invalid."""


def _read_regular(path: Path) -> bytes:
    try:
        before = path.lstat()
    except OSError as exc:
        raise RuntimeManifestError(f"cannot inspect runtime file {path}: {exc}") from exc
    if not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode):
        raise RuntimeManifestError(f"runtime input is not a regular non-symlink file: {path}")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise RuntimeManifestError(f"cannot securely open runtime file {path}: {exc}") from exc
    try:
        opened = os.fstat(descriptor)
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if not os.path.samestat(before, opened) or (
        opened.st_dev,
        opened.st_ino,
        opened.st_size,
        opened.st_mtime_ns,
    ) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise RuntimeManifestError(f"runtime file changed during read: {path}")
    payload = b"".join(chunks)
    if len(payload) != opened.st_size:
        raise RuntimeManifestError(f"runtime file read was incomplete: {path}")
    return payload


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    except (TypeError, ValueError) as exc:
        raise RuntimeManifestError(f"cannot render strict runtime JSON: {exc}") from exc


def _relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError as exc:
        raise RuntimeManifestError(f"runtime path escapes repository root: {path}") from exc


def _record(path: Path, role: str) -> dict[str, Any]:
    payload = _read_regular(path)
    return {
        "bytes": len(payload),
        "path": _relative(path),
        "role": role,
        "sha256": sha256(payload),
    }


def _closure(records: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for record in sorted(records, key=lambda row: row["path"]):
        digest.update(record["path"].encode())
        digest.update(b"\0")
        digest.update(record["role"].encode())
        digest.update(b"\0")
        digest.update(record["sha256"].encode())
        digest.update(b"\0")
        digest.update(str(record["bytes"]).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def _directory_files(path: Path, label: str) -> list[Path]:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise RuntimeManifestError(f"cannot inspect {label} directory: {exc}") from exc
    if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise RuntimeManifestError(f"{label} is not a regular non-symlink directory")
    files = sorted(path.iterdir(), key=lambda item: item.name)
    for item in files:
        item_metadata = item.lstat()
        if not stat.S_ISREG(item_metadata.st_mode) or stat.S_ISLNK(item_metadata.st_mode):
            raise RuntimeManifestError(f"{label} contains a non-regular entry: {item}")
    return files


def _validate_specs(solution_ids: list[str]) -> tuple[list[Path], str]:
    ids, index_sha = collection._validate_spec_index(SPECS / "index.json")
    if ids != solution_ids:
        raise RuntimeManifestError(
            "iter203 spec index does not exactly match 50 projected solutions"
        )
    document, _ = collection._load(SPECS / "index.json", canonical=True)
    expected = {"index.json"}
    by_id = {row["instance_id"]: row for row in document["specs"]}
    for instance_id in ids:
        expected |= {f"{instance_id}.spec.json", f"{instance_id}.eval_script.sh"}
        spec, _ = collection._load(SPECS / f"{instance_id}.spec.json", canonical=True)
        eval_payload = _read_regular(SPECS / f"{instance_id}.eval_script.sh")
        row = by_id[instance_id]
        if spec.get("instance_id") != instance_id:
            raise RuntimeManifestError(f"spec identity differs for {instance_id}")
        if sha256(eval_payload) != row.get("eval_script_sha256") or spec.get(
            "eval_script_sha256"
        ) != row.get("eval_script_sha256"):
            raise RuntimeManifestError(f"eval-script binding differs for {instance_id}")
        for key in ("repo", "framework", "identical_to_gold", "scenario_available"):
            if spec.get(key) != row.get(key):
                raise RuntimeManifestError(f"spec/index field differs for {instance_id}: {key}")
    files = _directory_files(SPECS, "iter203 specs")
    if {path.name for path in files} != expected:
        raise RuntimeManifestError("iter203 spec directory contains missing or extra files")
    return files, index_sha


def _validate_bridge() -> tuple[list[str], list[Path], dict[str, str]]:
    try:
        bundle = recovery.build_artifacts()
        recovery.check_artifacts(bundle)
    except recovery.RecoveryError as exc:
        raise RuntimeManifestError(f"iter203 bridge validation failed: {exc}") from exc

    bridge_files = _directory_files(BRIDGE, "safety-recovery bridge")
    solution_files = _directory_files(SOLUTIONS, "projected solutions")
    scenario_files = _directory_files(SCENARIOS, "projected safe scenarios")
    if {path.name for path in bridge_files} != recovery.BRIDGE_FILENAMES:
        raise RuntimeManifestError("bridge JSON file set differs")

    solution_summary, _ = collection._load(SOLUTIONS / "solve_summary.json", canonical=True)
    rows = solution_summary.get("manifest")
    if not isinstance(rows, list):
        raise RuntimeManifestError("projected solution summary is malformed")
    solution_ids = [
        row.get("instance_id")
        for row in rows
        if isinstance(row, dict) and row.get("status") == "solution"
    ]
    if (
        solution_summary.get("targets") != 53
        or solution_summary.get("solutions") != VALID_PATCH_COUNT
        or len(solution_ids) != VALID_PATCH_COUNT
        or len(set(solution_ids)) != VALID_PATCH_COUNT
    ):
        raise RuntimeManifestError(
            "projected solution summary does not identify exactly 50 patches"
        )
    expected_solution_files = {"solve_summary.json"} | {
        f"{instance_id}.{kind}.patch" for instance_id in solution_ids for kind in ("gold", "model")
    }
    if {path.name for path in solution_files} != expected_solution_files:
        raise RuntimeManifestError("projected solution directory contains missing or extra files")

    safe_index, _ = collection._load(BRIDGE / "safe_scenario_index.json", canonical=True)
    safe_rows = safe_index.get("scenarios")
    if (
        safe_index.get("count") != SAFE_SCENARIO_COUNT
        or not isinstance(safe_rows, list)
        or len(safe_rows) != SAFE_SCENARIO_COUNT
    ):
        raise RuntimeManifestError("safe-scenario index must contain exactly 29 rows")
    safe_ids = [row.get("instance_id") for row in safe_rows if isinstance(row, dict)]
    if len(safe_ids) != SAFE_SCENARIO_COUNT or len(set(safe_ids)) != SAFE_SCENARIO_COUNT:
        raise RuntimeManifestError("safe-scenario index identities are incomplete or duplicated")
    expected_scenario_files = {"scenarios_summary.json"} | {
        f"{instance_id}.scenario.py" for instance_id in safe_ids
    }
    if {path.name for path in scenario_files} != expected_scenario_files:
        raise RuntimeManifestError("scenario projection contains missing, unsafe, or extra scripts")

    bridge_records = (
        [_record(path, "safety_recovery_bridge_json") for path in bridge_files]
        + [_record(path, "projected_fixed_solution_input") for path in solution_files]
        + [_record(path, "projected_safe_scenario_input") for path in scenario_files]
    )
    bridge_records.sort(key=lambda row: row["path"])
    source_hashes = {
        "image_lock_sha256": sha256(_read_regular(UPSTREAM / "image_lock.json")),
        "projected_scenarios_summary_sha256": sha256(
            _read_regular(SCENARIOS / "scenarios_summary.json")
        ),
        "projected_solve_summary_sha256": sha256(_read_regular(SOLUTIONS / "solve_summary.json")),
        "safe_scenario_index_sha256": sha256(_read_regular(BRIDGE / "safe_scenario_index.json")),
        "scenario_disposition_sha256": sha256(_read_regular(BRIDGE / "scenario_disposition.json")),
        "solution_projection_index_sha256": sha256(
            _read_regular(BRIDGE / "solution_projection_index.json")
        ),
        "upstream_inventory_sha256": sha256(_read_regular(BRIDGE / "upstream_inventory.json")),
        "upstream_runtime_manifest_sha256": sha256(
            _read_regular(UPSTREAM / "runtime_manifest.json")
        ),
        "upstream_solve_summary_sha256": sha256(
            _read_regular(UPSTREAM / "solutions/solve_summary.json")
        ),
    }
    if source_hashes["upstream_runtime_manifest_sha256"] != UPSTREAM_RUNTIME_SHA256:
        raise RuntimeManifestError("upstream iter202 runtime manifest digest differs")
    return solution_ids, bridge_records, source_hashes


def build_manifest() -> dict[str, Any]:
    solution_ids, bridge_records, source = _validate_bridge()
    spec_files, spec_sha = _validate_specs(solution_ids)
    input_bridge = {
        "algorithm": "SHA-256(path NUL role NUL file_sha256 NUL byte_count LF), path-sorted",
        "file_count": len(bridge_records),
        "files": bridge_records,
        "sha256": _closure(bridge_records),
    }
    source["input_bridge_sha256"] = input_bridge["sha256"]
    source["spec_index_sha256"] = spec_sha

    runtime_records = [_record(ROOT / path, role) for path, role in STATIC_RUNTIME_FILES.items()]
    runtime_records.extend(bridge_records)
    runtime_records.extend(_record(path, "official_certification_spec") for path in spec_files)
    runtime_records.extend(
        [
            _record(UPSTREAM / "image_lock.json", "immutable_iter202_image_lock"),
            _record(UPSTREAM / "runtime_manifest.json", "upstream_v1_runtime_anchor"),
            _record(UPSTREAM / "solutions/solve_summary.json", "upstream_solution_summary_anchor"),
        ]
    )
    by_path: dict[str, dict[str, Any]] = {}
    for record in runtime_records:
        previous = by_path.get(record["path"])
        if previous is not None and previous != record:
            raise RuntimeManifestError(f"runtime file has conflicting roles: {record['path']}")
        by_path[record["path"]] = record
    files = sorted(by_path.values(), key=lambda row: row["path"])
    return {
        "closure": {
            "algorithm": "SHA-256(path NUL role NUL file_sha256 NUL byte_count LF), path-sorted",
            "sha256": _closure(files),
        },
        "experiment_id": EXPERIMENT_ID,
        "file_count": len(files),
        "files": files,
        "input_bridge": input_bridge,
        "protocol": {
            "adjudication_and_judging": {
                "all_certified_patch_denominator": True,
                "blind_confirmation": "both_judges_name_only_model_slot",
                "corrected_pool_baseline": (
                    "experiments/iter200_natural_certified_yet_wrong_rate/"
                    "proof/audit_report.json"
                ),
                "judge_missingness": "unadjudicated_never_negative",
                "prior_use_strata": _relative(UPSTREAM / "sample_overlap_audit.json"),
                "safe_nondivergence": "unadjudicated_ambiguity",
                "task_snapshot": (
                    "experiments/iter154_reward_hack_benchmark_expansion_pilot/"
                    "proof/raw/swebench_verified_rows_snapshot.json"
                ),
            },
            "certification": {
                "all_valid_patches_independent_of_scenario_disposition": True,
                "expected_valid_patches": VALID_PATCH_COUNT,
                "scenario_mount_during_certification": "none",
                "spec_index": _relative(SPECS / "index.json"),
            },
            "containers": {
                "capabilities": "drop_all",
                "cpus": 4,
                "image_lock": _relative(UPSTREAM / "image_lock.json"),
                "input_mount_scope": (
                    "current_row_eval_and_spec_plus_current_condition_patch_only"
                ),
                "memory": "10g",
                "network": "none",
                "no_new_privileges": True,
                "pids": 1024,
            },
            "execution_chain_of_custody": {
                "aggregate_receipt_name": collection.AGGREGATE_RECEIPT_NAME,
                "aggregate_receipt_schema": collection.AGGREGATE_SCHEMA,
                "collector_eligible_artifacts": "successful_shards_from_one_github_run_and_attempt_only",
                "exact_log_set": "gold_and_variant_pair_for_each_of_50_spec_rows",
                "shard_receipt_schema": collection.SHARD_SCHEMA,
                "verified_snapshot_api": "scripts.collect_iter203_execution.check_execution_bundle_with_logs",
            },
            "dispatch_authorization": {
                "branch": "master",
                "canonical_run": "first_dispatch_for_preapproved_green_primary_commit",
                "repository": "manfromnowhere143/telos",
                "retry": "rerun_all_jobs_of_same_run_only",
                "workflow": ".github/workflows/iter203-execute.yml",
            },
            "execution_limits": {
                "certification_output_bytes": 2_097_152,
                "certification_timeout_seconds": 900,
                "kill_grace_seconds": 10,
                "scenario_output_bytes": 262_144,
                "scenario_timeout_seconds": 180,
                "timeout_or_truncation": "infrastructure_failure",
            },
            "safe_witnesses": {
                "expected_safe_scenarios": SAFE_SCENARIO_COUNT,
                "mount": "current_indexed_safe_scenario_file_only",
                "opposite_condition_patch_visibility": "none",
                "projection": _relative(SCENARIOS),
                "unsafe_or_absent_behavior": "not_mounted_not_executed",
            },
            "sharding": {
                "assignment": collection.ASSIGNMENT_METHOD,
                "indexes": list(range(8)),
                "max_rows_per_shard": 7,
                "same_run_attempt_required": True,
                "shard_count": 8,
            },
        },
        "schema_version": SCHEMA,
        "source_bindings": source,
        "upstream_runtime_manifest_sha256": UPSTREAM_RUNTIME_SHA256,
        "upstream_source_commit": UPSTREAM_SOURCE_COMMIT,
    }


def rendered_manifest_bytes(document: dict[str, Any]) -> bytes:
    return canonical_json_bytes(document)


def manifest_errors(actual: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if actual != expected:
        errors.append(
            "committed iter203 runtime manifest differs from deterministic runtime closure"
        )
    if actual.get("schema_version") != SCHEMA:
        errors.append("iter203 runtime manifest schema differs")
    if actual.get("upstream_runtime_manifest_sha256") != UPSTREAM_RUNTIME_SHA256:
        errors.append("iter203 runtime does not bind exact iter202 v1 runtime")
    return errors


def validate_committed_manifest() -> list[str]:
    expected = build_manifest()
    try:
        actual, raw = collection._load(MANIFEST, canonical=True)
    except collection.ExecutionCollectionError as exc:
        return [str(exc)]
    errors = manifest_errors(actual, expected)
    if raw != rendered_manifest_bytes(actual):
        errors.append("committed iter203 runtime manifest is not canonical")
    return errors


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            errors = validate_committed_manifest()
            if errors:
                for error in errors:
                    print(f"iter203 runtime error: {error}", file=sys.stderr)
                return 1
            print(f"iter203 runtime manifest reproduces: sha256={sha256(_read_regular(MANIFEST))}")
            return 0
        payload = rendered_manifest_bytes(build_manifest())
        if args.write:
            atomic_write(MANIFEST, payload)
            print(f"wrote {_relative(MANIFEST)}; sha256={sha256(payload)}")
        else:
            sys.stdout.buffer.write(payload)
        return 0
    except (RuntimeManifestError, collection.ExecutionCollectionError) as exc:
        print(f"iter203 runtime error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
