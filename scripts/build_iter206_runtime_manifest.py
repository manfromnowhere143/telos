#!/usr/bin/env python3
"""Build or verify the additive iter206 admission-history recovery runtime."""

from __future__ import annotations

import argparse
import ast
import copy
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import build_iter203_runtime_manifest as iter203  # noqa: E402
from scripts import collect_iter203_execution as iter203_collection  # noqa: E402
from scripts import collect_iter206_execution as iter206_collection  # noqa: E402


EXPERIMENT_ID = "iter206_iter205_admission_history_recovery"
EXP = ROOT / "experiments" / EXPERIMENT_ID
MANIFEST = EXP / "proof/raw/runtime_manifest.json"
ITER205_EXP = ROOT / "experiments/iter205_iter204_workflow_context_recovery"
ITER205_MANIFEST = ITER205_EXP / "proof/raw/runtime_manifest.json"
ITER205_NULL = ITER205_EXP / "proof/pre_dispatch_admission_null.json"
ITER205_METADATA = ITER205_EXP / "proof/raw/public_admission_metadata/manifest.json"
SCHEMA = "telos.iter206.execution_runtime_recovery.v1"
ITER203_RUNTIME_SHA256 = "8beb0e845dbc9e3a4ce56832f28a62d4fd58ceac20adbc6bc06d6aef41be47e1"
ITER204_RUNTIME_SHA256 = "bf2062825e604d9439b0d29375d7e5219a1064ae4a33701efb74a62f81a59a45"
ITER205_RUNTIME_SHA256 = "1d427fd8e778282127ee8d782c6eb6bb8d6d44e781edceb50ad078474968b04a"
ITER205_NULL_SHA256 = "c67d3ede42555dc75f2a1b00c24a4fdb5671b4aa0eead1a5f37a7cfa1701fcad"
ITER205_METADATA_SHA256 = "6d2216038c7e1f19337795be806bf77eb39150a9be119828bc2967ed160c72ba"
ITER205_RESULT_SHA256 = "d1e36e991d26871a15bc2eb306009139cd59c8c987d50ea749d7c275052a8d0a"
ITER205_TERMINAL_LEARNING_SHA256 = (
    "b05eda703827162cb532b493f3ddd72319dd1c0eabc844acd4d0e9a0864ae32b"
)
ITER206_HYPOTHESIS_SHA256 = (
    "3e1185f5a79bf0cbd85ee046065ff9caf17fe7c1ccaa2c519be053510b1c4f26"
)
ITER206_AGGREGATE_RECEIPT_NAME = iter206_collection.AGGREGATE_RECEIPT_NAME
ITER206_AGGREGATE_RECEIPT_SCHEMA = iter206_collection.AGGREGATE_SCHEMA
ITER206_SHARD_RECEIPT_NAME_PATTERN = "_telos_iter206_shard_{shard_index}_of_8.receipt.json"
ITER206_SHARD_RECEIPT_SCHEMA = iter206_collection.SHARD_SCHEMA
ITER206_VERIFIED_SNAPSHOT_API = (
    "scripts.collect_iter206_execution.check_execution_bundle_with_logs"
)
SOURCE_BINDING_PATHS = {
    "image_lock_sha256": (
        "experiments/iter202_natural_rate_scaled/proof/raw/image_lock.json"
    ),
    "projected_scenarios_summary_sha256": (
        "experiments/iter203_iter202_safety_recovery/proof/raw/"
        "scenarios/scenarios_summary.json"
    ),
    "projected_solve_summary_sha256": (
        "experiments/iter203_iter202_safety_recovery/proof/raw/"
        "solutions/solve_summary.json"
    ),
    "safe_scenario_index_sha256": (
        "experiments/iter203_iter202_safety_recovery/proof/raw/"
        "safety_recovery_bridge/safe_scenario_index.json"
    ),
    "scenario_disposition_sha256": (
        "experiments/iter203_iter202_safety_recovery/proof/raw/"
        "safety_recovery_bridge/scenario_disposition.json"
    ),
    "solution_projection_index_sha256": (
        "experiments/iter203_iter202_safety_recovery/proof/raw/"
        "safety_recovery_bridge/solution_projection_index.json"
    ),
    "spec_index_sha256": (
        "experiments/iter203_iter202_safety_recovery/proof/raw/specs/index.json"
    ),
    "upstream_inventory_sha256": (
        "experiments/iter203_iter202_safety_recovery/proof/raw/"
        "safety_recovery_bridge/upstream_inventory.json"
    ),
    "upstream_runtime_manifest_sha256": (
        "experiments/iter202_natural_rate_scaled/proof/raw/runtime_manifest.json"
    ),
    "upstream_solve_summary_sha256": (
        "experiments/iter202_natural_rate_scaled/proof/raw/solutions/solve_summary.json"
    ),
}

NEW_RUNTIME_FILES = {
    ".github/workflows/ci.yml": "primary_ci_authorization_workflow",
    ".github/workflows/iter206-execute.yml": "attempt1_only_execution_workflow",
    "experiments/iter205_iter204_workflow_context_recovery/RESULT.md": (
        "exact_iter205_pre_dispatch_admission_null_result"
    ),
    "experiments/iter205_iter204_workflow_context_recovery/proof/learning_record.pre_dispatch_admission_null.json": (
        "completed_iter205_pre_dispatch_admission_null_learning_record"
    ),
    "experiments/iter205_iter204_workflow_context_recovery/proof/pre_dispatch_admission_null.json": (
        "exact_iter205_pre_dispatch_admission_null"
    ),
    "experiments/iter205_iter204_workflow_context_recovery/proof/raw/public_admission_metadata/all_runs.json": (
        "exact_iter205_public_admission_metadata"
    ),
    "experiments/iter205_iter204_workflow_context_recovery/proof/raw/public_admission_metadata/dispatch_runs.json": (
        "exact_iter205_public_admission_metadata"
    ),
    "experiments/iter205_iter204_workflow_context_recovery/proof/raw/public_admission_metadata/iter204_history.json": (
        "exact_iter205_public_admission_metadata"
    ),
    "experiments/iter205_iter204_workflow_context_recovery/proof/raw/public_admission_metadata/manifest.json": (
        "exact_iter205_public_admission_metadata_manifest"
    ),
    "experiments/iter205_iter204_workflow_context_recovery/proof/raw/public_admission_metadata/primary_ci_projection.json": (
        "exact_iter205_public_admission_metadata"
    ),
    "experiments/iter205_iter204_workflow_context_recovery/proof/raw/public_admission_metadata/publication_pr.json": (
        "exact_iter205_public_admission_metadata"
    ),
    "experiments/iter205_iter204_workflow_context_recovery/proof/raw/public_admission_metadata/workflow.json": (
        "exact_iter205_public_admission_metadata"
    ),
    "experiments/iter206_iter205_admission_history_recovery/HYPOTHESIS.md": (
        "post_null_pre_scientific_protocol"
    ),
    "experiments/iter206_iter205_admission_history_recovery/proof/learning_record.json": (
        "pre_execution_learning_and_next_action_ledger"
    ),
    "experiments/iter206_iter205_admission_history_recovery/proof/pre_execution_publication_safety.json": (
        "current_pre_execution_publication_safety_receipt"
    ),
    "mission/loop.json": "active_learning_gate_binding",
    "scripts/adjudicate_iter206_admission_history_recovery.py": (
        "iter206_bound_adjudicator"
    ),
    "scripts/build_iter206_runtime_manifest.py": "iter206_runtime_manifest_builder",
    "scripts/capture_iter206_runtime_host.py": "observed_host_provenance_capture",
    "scripts/ci_iter206_execute.sh": "iter206_certification_and_safe_witness_runner",
    "scripts/ci_iter206_smoke.sh": "no_science_log_driver_smoke",
    "scripts/collect_iter206_execution.py": "iter206_attempt1_chain_of_custody",
    "scripts/prepare_iter206_output_directory.py": "nofollow_empty_output_directory_guard",
    "scripts/publish_iter206_runtime_diagnostic.py": "bounded_visible_diagnostic_publisher",
    "scripts/run_iter206_admission_history_recovery_blind_judge.py": (
        "iter206_bound_strict_blind_judge"
    ),
    "scripts/validate_iter205_pre_dispatch_null.py": "exact_iter205_admission_null_guard",
    "scripts/validate_iter204_pre_dispatch_null.py": "upstream_iter204_admission_null_guard",
    "scripts/validate_iter200_corrected_result.py": (
        "current_publication_claim_pattern_dependency"
    ),
    "scripts/validate_iter205_publication_safety.py": (
        "frozen_iter205_publication_scan_dependency"
    ),
    "scripts/validate_iter206_publication_safety.py": "current_publication_safety_guard",
    "scripts/validate_iter206_runtime_recovery.py": "runtime_recovery_contract_guard",
    "scripts/validate_learning_ledger.py": "completed_learning_next_action_guard",
    "scripts/validate_mission_loop.py": "mission_source_of_truth_guard",
    "scripts/validate_supply_chain.py": "primary_ci_workflow_supply_chain_guard",
    "telos/__init__.py": "learning_guard_package_import_closure",
    "telos/agent_behavior_slice.py": "learning_guard_package_import_closure",
    "telos/ledger.py": "learning_record_discovery_and_selection",
    "telos/proof.py": "publication_claim_dependency_import_closure",
    "telos/public_slice.py": "learning_guard_package_import_closure",
    "telos/scorecard.py": "learning_guard_package_import_closure",
    "telos/survey.py": "learning_guard_package_import_closure",
    "tests/test_iter206_admission_history_recovery.py": "runtime_recovery_regression_suite",
    "tests/test_iter205_pre_dispatch_null.py": (
        "iter205_admission_null_regression_suite"
    ),
    "tests/test_iter204_infrastructure_recovery.py": (
        "frozen_iter204_snapshot_supersession_regression"
    ),
    "tests/test_iter204_pre_dispatch_null.py": "iter204_admission_null_regression_suite",
    "tests/test_ledger.py": "learning_ledger_regression_suite",
    "tests/test_mission_loop_guard.py": "mission_source_of_truth_regression_suite",
    "tests/test_supply_chain_guard.py": "workflow_permission_regression_suite",
}


class RuntimeRecoveryError(ValueError):
    """The iter206 runtime or one of its immutable inputs differs."""


LEARNING_GUARD_IMPORT_ROOTS = (
    "scripts/validate_iter205_pre_dispatch_null.py",
    "scripts/validate_learning_ledger.py",
)


def _local_module_paths(module: str) -> set[str]:
    parts = module.split(".")
    if not parts or parts[0] not in {"scripts", "telos"}:
        return set()
    paths: set[str] = set()
    for length in range(1, len(parts)):
        package = Path(*parts[:length]) / "__init__.py"
        if (ROOT / package).is_file():
            paths.add(package.as_posix())
    relative = Path(*parts)
    candidates = (relative.with_suffix(".py"), relative / "__init__.py")
    for candidate in candidates:
        if (ROOT / candidate).is_file():
            paths.add(candidate.as_posix())
            break
    return paths


def _import_from_base(source: str, node: ast.ImportFrom) -> str | None:
    if node.level == 0:
        return node.module
    source_parts = list(Path(source).with_suffix("").parts)
    package_parts = source_parts[:-1]
    ascend = node.level - 1
    if ascend > len(package_parts):
        return None
    base = package_parts[: len(package_parts) - ascend]
    if node.module:
        base.extend(node.module.split("."))
    return ".".join(base)


def local_python_import_gaps(
    files: list[dict[str, Any]],
    roots: tuple[str, ...] = LEARNING_GUARD_IMPORT_ROOTS,
) -> list[tuple[str, str]]:
    """Return uncovered imports in the newly executed learning-guard closure."""

    included = {
        record.get("path")
        for record in files
        if isinstance(record, dict) and isinstance(record.get("path"), str)
    }
    gaps: set[tuple[str, str]] = set()
    pending = list(roots)
    visited: set[str] = set()
    while pending:
        source = pending.pop()
        if source in visited:
            continue
        visited.add(source)
        if source not in included:
            gaps.add(("<runtime-root>", source))
            continue
        try:
            tree = ast.parse(iter203._read_regular(ROOT / source), filename=source)
        except (SyntaxError, UnicodeError) as exc:
            raise RuntimeRecoveryError(
                f"cannot parse runtime Python dependency source: {source}"
            ) from exc
        dependencies: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.update(_local_module_paths(alias.name))
            elif isinstance(node, ast.ImportFrom):
                base = _import_from_base(source, node)
                if base is None:
                    continue
                dependencies.update(_local_module_paths(base))
                for alias in node.names:
                    dependencies.update(_local_module_paths(f"{base}.{alias.name}"))
        for dependency in dependencies:
            if dependency not in included:
                gaps.add((source, dependency))
            elif dependency not in visited:
                pending.append(dependency)
    return sorted(gaps)


def _load_iter205_manifest() -> dict[str, Any]:
    document, raw = iter203_collection._load(ITER205_MANIFEST, canonical=True)
    if iter203.sha256(raw) != ITER205_RUNTIME_SHA256:
        raise RuntimeRecoveryError("frozen iter205 runtime manifest SHA-256 differs")
    if (
        document.get("schema_version") != "telos.iter205.execution_runtime_recovery.v1"
        or document.get("experiment_id") != "iter205_iter204_workflow_context_recovery"
        or document.get("upstream_iter204_runtime_manifest_sha256")
        != ITER204_RUNTIME_SHA256
        or document.get("upstream_iter203_runtime_manifest_sha256")
        != ITER203_RUNTIME_SHA256
    ):
        raise RuntimeRecoveryError("frozen iter205 runtime manifest identity differs")
    return document


def validate_frozen_iter205_manifest() -> dict[str, Any]:
    """Validate the sealed iter205 snapshot without reconstructing it post-successor."""
    return _load_iter205_manifest()


def _validate_record(record: dict[str, Any]) -> dict[str, Any]:
    if set(record) != {"bytes", "path", "role", "sha256"}:
        raise RuntimeRecoveryError("frozen scientific-input record keys differ")
    path = ROOT / record["path"]
    payload = iter203._read_regular(path)
    if len(payload) != record["bytes"] or iter203.sha256(payload) != record["sha256"]:
        raise RuntimeRecoveryError(f"frozen scientific input changed: {record['path']}")
    return copy.deepcopy(record)


def build_manifest() -> dict[str, Any]:
    from scripts import validate_iter205_pre_dispatch_null as null_guard

    iter203_errors = iter203.validate_committed_manifest()
    if iter203_errors:
        raise RuntimeRecoveryError(
            "active iter203 scientific runtime no longer reproduces: "
            + "; ".join(iter203_errors)
        )
    try:
        null_guard.validate()
    except (OSError, null_guard.PreDispatchNullError) as exc:
        raise RuntimeRecoveryError(
            "iter205 pre-dispatch admission null no longer verifies"
        ) from exc
    frozen_terminal = {
        ITER205_NULL: ITER205_NULL_SHA256,
        ITER205_METADATA: ITER205_METADATA_SHA256,
        ITER205_EXP / "RESULT.md": ITER205_RESULT_SHA256,
        ITER205_EXP / "proof/learning_record.pre_dispatch_admission_null.json": (
            ITER205_TERMINAL_LEARNING_SHA256
        ),
    }
    for path, expected_hash in frozen_terminal.items():
        if iter203.sha256(iter203._read_regular(path)) != expected_hash:
            raise RuntimeRecoveryError(
                f"frozen iter205 terminal evidence changed: {iter203._relative(path)}"
            )
    upstream = _load_iter205_manifest()
    if not ITER206_HYPOTHESIS_SHA256:
        raise RuntimeRecoveryError("iter206 hypothesis hash has not been frozen")
    if (
        iter203.sha256(iter203._read_regular(EXP / "HYPOTHESIS.md"))
        != ITER206_HYPOTHESIS_SHA256
    ):
        raise RuntimeRecoveryError("iter206 hypothesis changed after its frozen pre-result boundary")
    input_bridge = copy.deepcopy(upstream.get("input_bridge"))
    source_bindings = copy.deepcopy(upstream.get("source_bindings"))
    if not isinstance(input_bridge, dict) or not isinstance(source_bindings, dict):
        raise RuntimeRecoveryError("iter205 runtime lacks its exact bridge/source bindings")
    bridge_files = input_bridge.get("files")
    if (
        not isinstance(bridge_files, list)
        or input_bridge.get("file_count") != len(bridge_files)
        or len(bridge_files) != 135
    ):
        raise RuntimeRecoveryError("iter205 runtime input bridge is malformed")
    if iter203._closure(bridge_files) != input_bridge.get("sha256"):
        raise RuntimeRecoveryError("iter205 runtime input-bridge closure differs")
    if source_bindings.get("input_bridge_sha256") != input_bridge.get("sha256"):
        raise RuntimeRecoveryError("iter205 source/input-bridge binding differs")
    if set(source_bindings) != set(SOURCE_BINDING_PATHS) | {"input_bridge_sha256"}:
        raise RuntimeRecoveryError("iter205 source-binding keys differ")
    for key, relative in SOURCE_BINDING_PATHS.items():
        if iter203.sha256(iter203._read_regular(ROOT / relative)) != source_bindings[key]:
            raise RuntimeRecoveryError(f"frozen current source differs: {key}")
    files = [_validate_record(record) for record in bridge_files]
    files.append(iter203._record(ITER205_MANIFEST, "immutable_iter205_runtime_anchor"))
    for path_text, role in NEW_RUNTIME_FILES.items():
        files.append(iter203._record(ROOT / path_text, role))
    by_path: dict[str, dict[str, Any]] = {}
    for record in files:
        previous = by_path.get(record["path"])
        if previous is not None and previous != record:
            raise RuntimeRecoveryError(f"conflicting runtime record: {record['path']}")
        by_path[record["path"]] = record
    files = sorted(by_path.values(), key=lambda record: record["path"])
    import_gaps = local_python_import_gaps(files)
    if import_gaps:
        rendered = ", ".join(
            f"{source}->{dependency}" for source, dependency in import_gaps
        )
        raise RuntimeRecoveryError(
            f"runtime learning-guard Python import closure is incomplete: {rendered}"
        )
    protocol = copy.deepcopy(upstream.get("protocol"))
    if not isinstance(protocol, dict):
        raise RuntimeRecoveryError("iter205 runtime protocol is malformed")
    protocol.update(
        {
            "diagnostic_observability": {
                "diagnostic_receipt_schema": "telos.iter206.runtime_diagnostic.v1",
                "launch_scope": (
                    "all row-create preflights and every failed container create/run launch"
                ),
                "provider_credentials": "unset",
                "scientific_launch_bytes": 2_162_688,
                "scoring_eligibility": "never",
                "smoke_bytes": 65_536,
                "truncation": "infrastructure_failure",
                "visible_failure_copy_required": True,
            },
            "dispatch_authorization": {
                "branch": "master",
                "canonical_run": "first_global_iter206_dispatch_only",
                "release_ci_pair": (
                    "exact_attempt_1_push_and_pull_request_ci_runs_at_merge_parent_2"
                ),
                "repository": "manfromnowhere143/telos",
                "retry": "forbidden_advance_to_iter207_after_any_failure",
                "run_attempt": 1,
                "workflow": ".github/workflows/iter206-execute.yml",
            },
            "execution_chain_of_custody": {
                "aggregate_receipt_name": ITER206_AGGREGATE_RECEIPT_NAME,
                "aggregate_receipt_schema": ITER206_AGGREGATE_RECEIPT_SCHEMA,
                "collector_eligible_artifacts": (
                    "successful_shards_from_one_github_run_and_attempt_only"
                ),
                "exact_log_set": "gold_and_variant_pair_for_each_of_50_spec_rows",
                "shard_receipt_name_pattern": ITER206_SHARD_RECEIPT_NAME_PATTERN,
                "shard_receipt_schema": ITER206_SHARD_RECEIPT_SCHEMA,
                "verified_snapshot_api": ITER206_VERIFIED_SNAPSHOT_API,
            },
            "admission_history_recovery": {
                "allowed_delta": [
                    "mechanical_iter205_to_separately_versioned_iter206_identities",
                    (
                        "add_exact_iter205_pre_dispatch_admission_null_"
                        "evidence_and_guard"
                    ),
                    (
                        "replace_only_the_iter205_exact_two_history_predicate_"
                        "with_the_iter206_exact_six_publication_aware_predicate"
                    ),
                    (
                        "bind_exact_iter205_active_workflow_object_and_empty_"
                        "all_event_and_dispatch_histories"
                    ),
                ],
                "iter204_admission_snapshot": {
                    "baseline_push_parse_failure_run_ids": [
                        29465584664,
                        29465924803,
                        29468669956,
                        29468768706,
                    ],
                    "canonical_sha256": (
                        "SHA-256_of_UTF-8_JSON_sort_keys_true_"
                        "separators_comma_colon_allow_nan_false"
                    ),
                    "dispatch_run_count": 0,
                    "expected_push_parse_failure_count": 6,
                    "future_primary_run": (
                        "structurally_discovered_run_number_6_bound_to_approved_merge"
                    ),
                    "future_release_run": (
                        "structurally_discovered_run_number_5_bound_to_merge_parent_2"
                    ),
                    "run_numbers": [1, 2, 3, 4, 5, 6],
                    "temporal_scope": (
                        "authorization_time_snapshot_not_a_permanent_live_history_claim"
                    ),
                    "workflow_id": 314113289,
                },
                "iter205_all_event_run_count": 0,
                "iter205_dispatch_request_count": 0,
                "iter205_dispatch_run_count": 0,
                "iter205_null_receipt_sha256": ITER205_NULL_SHA256,
                "iter205_public_admission_metadata_manifest_sha256": (
                    ITER205_METADATA_SHA256
                ),
                "iter205_scientific_outcomes": 0,
                "iter205_result_sha256": ITER205_RESULT_SHA256,
                "iter205_terminal_learning_record_sha256": (
                    ITER205_TERMINAL_LEARNING_SHA256
                ),
                "iter205_workflow_id": 314141096,
                "iter206_in_run_history": "exactly_current_run_number_1_attempt_1",
                "iter206_pre_dispatch_all_event_run_count": 0,
                "iter206_pre_dispatch_dispatch_run_count": 0,
                "publication_envelope": {
                    "branch": "agent/iter206-iter205-admission-recovery",
                    "branch_push_count": 1,
                    "merge_count": 1,
                    "merge_first_parent": (
                        "4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f"
                    ),
                    "merge_method": "two_parent_no_squash_no_rebase",
                    "merge_second_parent": "exact_final_release_branch_tip",
                    "pull_request_ci": (
                        "exactly_one_completed_success_attempt_1_at_final_branch_tip_"
                        "with_two_required_jobs"
                    ),
                    "release_push_ci": (
                        "exactly_one_completed_success_attempt_1_at_final_branch_tip_"
                        "with_two_required_jobs"
                    ),
                    "subsequent_remote_mutation": "forbidden",
                },
                "scientific_semantic_change": False,
            },
            "local_logging": {
                "driver": "local",
                "options": ["max-size=3m", "max-file=1", "compress=false"],
            },
            "no_science_smoke": {
                "command": [
                    "bash",
                    "--noprofile",
                    "--norc",
                    "-c",
                    'printf "%s\\n" TELOS_ITER206_LOG_DRIVER_SMOKE_OK',
                ],
                "expected_output": "TELOS_ITER206_LOG_DRIVER_SMOKE_OK\n",
                "expected_stderr": "",
                "image": "frozen_global_ordinal_0_reference_and_id",
                "mounts": [],
                "receipt_schema": "telos.iter206.no_science_smoke_receipt.v1",
                "required_before_all_shards": True,
                "separate_streams_required": True,
            },
            "observed_host_provenance": {
                "immutability_claim": False,
                "receipt_schema": "telos.iter206.observed_runtime_host.v1",
                "required_fields": [
                    "docker_client",
                    "docker_server",
                    "runner_image",
                ],
            },
            "row_create_preflight": {
                "command": ["bash", "--noprofile", "--norc", "-c", "exit 0"],
                "container_started": False,
                "mounts": "current_row_certification_inputs_read_only",
                "required_before_each_certification": True,
            },
        }
    )
    return {
        "closure": {
            "algorithm": "SHA-256(path NUL role NUL file_sha256 NUL byte_count LF), path-sorted",
            "sha256": iter203._closure(files),
        },
        "experiment_id": EXPERIMENT_ID,
        "file_count": len(files),
        "files": files,
        "input_bridge": input_bridge,
        "protocol": protocol,
        "schema_version": SCHEMA,
        "source_bindings": source_bindings,
        "upstream_iter205_runtime_manifest_sha256": ITER205_RUNTIME_SHA256,
        "upstream_iter204_runtime_manifest_sha256": ITER204_RUNTIME_SHA256,
        "upstream_iter203_runtime_manifest_sha256": ITER203_RUNTIME_SHA256,
        "upstream_runtime_manifest_sha256": upstream.get(
            "upstream_runtime_manifest_sha256"
        ),
        "upstream_source_commit": upstream.get("upstream_source_commit"),
    }


def rendered_manifest_bytes(document: dict[str, Any]) -> bytes:
    return iter203.canonical_json_bytes(document)


def validate_committed_manifest() -> list[str]:
    try:
        expected = build_manifest()
        actual, raw = iter203_collection._load(MANIFEST, canonical=True)
    except (OSError, RuntimeRecoveryError, iter203.RuntimeManifestError, iter203_collection.ExecutionCollectionError) as exc:
        return [str(exc)]
    errors: list[str] = []
    if actual != expected:
        errors.append("committed iter206 runtime manifest differs from deterministic closure")
    if raw != rendered_manifest_bytes(actual):
        errors.append("committed iter206 runtime manifest is not canonical JSON")
    return errors


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
                    print(f"iter206 runtime error: {error}", file=sys.stderr)
                return 1
            print(
                "iter206 runtime manifest reproduces: "
                f"sha256={iter203.sha256(iter203._read_regular(MANIFEST))}"
            )
            return 0
        payload = rendered_manifest_bytes(build_manifest())
        if args.write:
            iter203.atomic_write(MANIFEST, payload)
            print(f"wrote {iter203._relative(MANIFEST)}; sha256={iter203.sha256(payload)}")
        else:
            sys.stdout.buffer.write(payload)
        return 0
    except (
        OSError,
        RuntimeRecoveryError,
        iter203.RuntimeManifestError,
        iter203_collection.ExecutionCollectionError,
    ) as exc:
        print(f"iter206 runtime error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
