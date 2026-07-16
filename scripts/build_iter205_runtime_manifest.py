#!/usr/bin/env python3
"""Build or verify the additive iter205 workflow-context recovery runtime."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import build_iter203_runtime_manifest as iter203  # noqa: E402
from scripts import collect_iter203_execution as iter203_collection  # noqa: E402
from scripts import collect_iter205_execution as iter205_collection  # noqa: E402


EXPERIMENT_ID = "iter205_iter204_workflow_context_recovery"
EXP = ROOT / "experiments" / EXPERIMENT_ID
MANIFEST = EXP / "proof/raw/runtime_manifest.json"
ITER204_EXP = ROOT / "experiments/iter204_iter203_infrastructure_recovery"
ITER204_MANIFEST = ITER204_EXP / "proof/raw/runtime_manifest.json"
ITER204_NULL = ITER204_EXP / "proof/pre_dispatch_infrastructure_null.json"
ITER204_METADATA = ITER204_EXP / "proof/raw/public_dispatch_metadata/manifest.json"
SCHEMA = "telos.iter205.execution_runtime_recovery.v1"
ITER203_RUNTIME_SHA256 = "8beb0e845dbc9e3a4ce56832f28a62d4fd58ceac20adbc6bc06d6aef41be47e1"
ITER204_RUNTIME_SHA256 = "bf2062825e604d9439b0d29375d7e5219a1064ae4a33701efb74a62f81a59a45"
ITER205_HYPOTHESIS_SHA256 = (
    "2b00f43f581176eaf4e134c7e3e3b2a9981f0767545a1f1b21397458bb215395"
)
ITER205_AGGREGATE_RECEIPT_NAME = iter205_collection.AGGREGATE_RECEIPT_NAME
ITER205_AGGREGATE_RECEIPT_SCHEMA = iter205_collection.AGGREGATE_SCHEMA
ITER205_SHARD_RECEIPT_NAME_PATTERN = "_telos_iter205_shard_{shard_index}_of_8.receipt.json"
ITER205_SHARD_RECEIPT_SCHEMA = iter205_collection.SHARD_SCHEMA
ITER205_VERIFIED_SNAPSHOT_API = (
    "scripts.collect_iter205_execution.check_execution_bundle_with_logs"
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
    ".github/workflows/iter205-execute.yml": "attempt1_only_execution_workflow",
    "experiments/iter204_iter203_infrastructure_recovery/RESULT.md": (
        "exact_iter204_pre_dispatch_null_result"
    ),
    "experiments/iter204_iter203_infrastructure_recovery/proof/learning_record.pre_dispatch_null.json": (
        "completed_iter204_pre_dispatch_null_learning_record"
    ),
    "experiments/iter204_iter203_infrastructure_recovery/proof/pre_dispatch_infrastructure_null.json": (
        "exact_iter204_pre_dispatch_infrastructure_null"
    ),
    "experiments/iter204_iter203_infrastructure_recovery/proof/raw/public_dispatch_metadata/dispatch_runs.json": (
        "exact_iter204_public_dispatch_metadata"
    ),
    "experiments/iter204_iter203_infrastructure_recovery/proof/raw/public_dispatch_metadata/manifest.json": (
        "exact_iter204_public_dispatch_metadata_manifest"
    ),
    "experiments/iter204_iter203_infrastructure_recovery/proof/raw/public_dispatch_metadata/primary_ci_projection.json": (
        "exact_iter204_public_dispatch_metadata"
    ),
    "experiments/iter204_iter203_infrastructure_recovery/proof/raw/public_dispatch_metadata/push_validation_runs.json": (
        "exact_iter204_public_dispatch_metadata"
    ),
    "experiments/iter204_iter203_infrastructure_recovery/proof/raw/public_dispatch_metadata/workflow.json": (
        "exact_iter204_public_dispatch_metadata"
    ),
    "experiments/iter205_iter204_workflow_context_recovery/HYPOTHESIS.md": (
        "post_null_pre_scientific_protocol"
    ),
    "experiments/iter205_iter204_workflow_context_recovery/proof/learning_record.json": (
        "pre_execution_learning_and_next_action_ledger"
    ),
    "experiments/iter205_iter204_workflow_context_recovery/proof/pre_execution_publication_safety.json": (
        "current_pre_execution_publication_safety_receipt"
    ),
    "mission/loop.json": "active_learning_gate_binding",
    "scripts/adjudicate_iter205_workflow_context_recovery.py": (
        "iter205_bound_adjudicator"
    ),
    "scripts/build_iter205_runtime_manifest.py": "iter205_runtime_manifest_builder",
    "scripts/capture_iter205_runtime_host.py": "observed_host_provenance_capture",
    "scripts/ci_iter205_execute.sh": "iter205_certification_and_safe_witness_runner",
    "scripts/ci_iter205_smoke.sh": "no_science_log_driver_smoke",
    "scripts/collect_iter205_execution.py": "iter205_attempt1_chain_of_custody",
    "scripts/prepare_iter205_output_directory.py": "nofollow_empty_output_directory_guard",
    "scripts/publish_iter205_runtime_diagnostic.py": "bounded_visible_diagnostic_publisher",
    "scripts/run_iter205_workflow_context_recovery_blind_judge.py": (
        "iter205_bound_strict_blind_judge"
    ),
    "scripts/validate_iter204_pre_dispatch_null.py": "exact_iter204_admission_null_guard",
    "scripts/build_iter204_runtime_manifest.py": "historical_iter204_manifest_builder",
    "scripts/validate_iter200_corrected_result.py": (
        "current_publication_claim_pattern_dependency"
    ),
    "scripts/validate_iter205_publication_safety.py": "current_publication_safety_guard",
    "scripts/validate_iter205_runtime_recovery.py": "runtime_recovery_contract_guard",
    "scripts/validate_learning_ledger.py": "completed_learning_next_action_guard",
    "scripts/validate_supply_chain.py": "primary_ci_workflow_supply_chain_guard",
    "telos/__init__.py": "learning_guard_package_import_closure",
    "telos/ledger.py": "learning_record_discovery_and_selection",
    "telos/proof.py": "publication_claim_dependency_import_closure",
    "tests/test_iter205_workflow_context_recovery.py": "runtime_recovery_regression_suite",
    "tests/test_iter204_infrastructure_recovery.py": (
        "frozen_iter204_snapshot_supersession_regression"
    ),
    "tests/test_iter204_pre_dispatch_null.py": "iter204_admission_null_regression_suite",
    "tests/test_ledger.py": "learning_ledger_regression_suite",
    "tests/test_supply_chain_guard.py": "workflow_permission_regression_suite",
}


class RuntimeRecoveryError(ValueError):
    """The iter205 runtime or one of its immutable inputs differs."""


def _load_iter204_manifest() -> dict[str, Any]:
    document, raw = iter203_collection._load(ITER204_MANIFEST, canonical=True)
    if iter203.sha256(raw) != ITER204_RUNTIME_SHA256:
        raise RuntimeRecoveryError("frozen iter204 runtime manifest SHA-256 differs")
    if (
        document.get("schema_version") != "telos.iter204.execution_runtime_recovery.v1"
        or document.get("experiment_id") != "iter204_iter203_infrastructure_recovery"
        or document.get("upstream_iter203_runtime_manifest_sha256")
        != ITER203_RUNTIME_SHA256
    ):
        raise RuntimeRecoveryError("frozen iter204 runtime manifest identity differs")
    return document


def validate_frozen_iter204_manifest() -> dict[str, Any]:
    """Validate the sealed iter204 snapshot without reconstructing it post-successor."""
    return _load_iter204_manifest()


def _validate_record(record: dict[str, Any]) -> dict[str, Any]:
    if set(record) != {"bytes", "path", "role", "sha256"}:
        raise RuntimeRecoveryError("frozen scientific-input record keys differ")
    path = ROOT / record["path"]
    payload = iter203._read_regular(path)
    if len(payload) != record["bytes"] or iter203.sha256(payload) != record["sha256"]:
        raise RuntimeRecoveryError(f"frozen scientific input changed: {record['path']}")
    return copy.deepcopy(record)


def build_manifest() -> dict[str, Any]:
    from scripts import validate_iter204_pre_dispatch_null as null_guard

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
            "iter204 pre-dispatch infrastructure null no longer verifies"
        ) from exc
    upstream = _load_iter204_manifest()
    if not ITER205_HYPOTHESIS_SHA256:
        raise RuntimeRecoveryError("iter205 hypothesis hash has not been frozen")
    if (
        iter203.sha256(iter203._read_regular(EXP / "HYPOTHESIS.md"))
        != ITER205_HYPOTHESIS_SHA256
    ):
        raise RuntimeRecoveryError("iter205 hypothesis changed after its frozen pre-result boundary")
    input_bridge = copy.deepcopy(upstream.get("input_bridge"))
    source_bindings = copy.deepcopy(upstream.get("source_bindings"))
    if not isinstance(input_bridge, dict) or not isinstance(source_bindings, dict):
        raise RuntimeRecoveryError("iter204 runtime lacks its exact bridge/source bindings")
    bridge_files = input_bridge.get("files")
    if (
        not isinstance(bridge_files, list)
        or input_bridge.get("file_count") != len(bridge_files)
        or len(bridge_files) != 135
    ):
        raise RuntimeRecoveryError("iter204 runtime input bridge is malformed")
    if iter203._closure(bridge_files) != input_bridge.get("sha256"):
        raise RuntimeRecoveryError("iter204 runtime input-bridge closure differs")
    if source_bindings.get("input_bridge_sha256") != input_bridge.get("sha256"):
        raise RuntimeRecoveryError("iter204 source/input-bridge binding differs")
    if set(source_bindings) != set(SOURCE_BINDING_PATHS) | {"input_bridge_sha256"}:
        raise RuntimeRecoveryError("iter204 source-binding keys differ")
    for key, relative in SOURCE_BINDING_PATHS.items():
        if iter203.sha256(iter203._read_regular(ROOT / relative)) != source_bindings[key]:
            raise RuntimeRecoveryError(f"frozen current source differs: {key}")
    files = [_validate_record(record) for record in bridge_files]
    files.append(iter203._record(ITER204_MANIFEST, "immutable_iter204_runtime_anchor"))
    for path_text, role in NEW_RUNTIME_FILES.items():
        files.append(iter203._record(ROOT / path_text, role))
    by_path: dict[str, dict[str, Any]] = {}
    for record in files:
        previous = by_path.get(record["path"])
        if previous is not None and previous != record:
            raise RuntimeRecoveryError(f"conflicting runtime record: {record['path']}")
        by_path[record["path"]] = record
    files = sorted(by_path.values(), key=lambda record: record["path"])
    protocol = copy.deepcopy(upstream.get("protocol"))
    if not isinstance(protocol, dict):
        raise RuntimeRecoveryError("iter204 runtime protocol is malformed")
    protocol.update(
        {
            "diagnostic_observability": {
                "diagnostic_receipt_schema": "telos.iter205.runtime_diagnostic.v1",
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
                "canonical_run": "first_global_iter205_dispatch_only",
                "repository": "manfromnowhere143/telos",
                "retry": "forbidden_advance_to_iter206_after_any_failure",
                "run_attempt": 1,
                "workflow": ".github/workflows/iter205-execute.yml",
            },
            "execution_chain_of_custody": {
                "aggregate_receipt_name": ITER205_AGGREGATE_RECEIPT_NAME,
                "aggregate_receipt_schema": ITER205_AGGREGATE_RECEIPT_SCHEMA,
                "collector_eligible_artifacts": (
                    "successful_shards_from_one_github_run_and_attempt_only"
                ),
                "exact_log_set": "gold_and_variant_pair_for_each_of_50_spec_rows",
                "shard_receipt_name_pattern": ITER205_SHARD_RECEIPT_NAME_PATTERN,
                "shard_receipt_schema": ITER205_SHARD_RECEIPT_SCHEMA,
                "verified_snapshot_api": ITER205_VERIFIED_SNAPSHOT_API,
            },
            "infrastructure_recovery": {
                "allowed_delta": [
                    "mechanical_iter204_to_separately_versioned_iter205_identities",
                    (
                        "move_smoke_receipt_runner_temp_binding_from_job_env_"
                        "to_execution_step_env"
                    ),
                    "add_exact_iter204_pre_dispatch_null_guards",
                    (
                        "strengthen_workflow_object_all_event_dispatch_current_run_"
                        "and_upstream_history_validation"
                    ),
                ],
                "iter204_dispatch_api_observation": {
                    "http_status": 422,
                    "locally_observed": True,
                    "raw_response_committed": False,
                    "request_count_exact": None,
                    "request_count_lower_bound": 1,
                },
                "iter204_global_workflow_dispatch_count": 0,
                "iter204_null_receipt_sha256": iter203.sha256(
                    iter203._read_regular(ITER204_NULL)
                ),
                "iter204_primary_ci_run_id": 29465925393,
                "iter204_primary_sha": (
                    "c1137f896b7ee3c9a26ee35bcda2c5f5c6b79446"
                ),
                "iter204_public_dispatch_metadata_manifest_sha256": iter203.sha256(
                    iter203._read_regular(ITER204_METADATA)
                ),
                "iter204_push_parse_failure_run_ids": [29465584664, 29465924803],
                "iter204_workflow_id": 314113289,
                "scientific_outcomes_in_iter204": 0,
                "workflow_dispatch_run_created_in_iter204": False,
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
                    'printf "%s\\n" TELOS_ITER205_LOG_DRIVER_SMOKE_OK',
                ],
                "expected_output": "TELOS_ITER205_LOG_DRIVER_SMOKE_OK\n",
                "expected_stderr": "",
                "image": "frozen_global_ordinal_0_reference_and_id",
                "mounts": [],
                "receipt_schema": "telos.iter205.no_science_smoke_receipt.v1",
                "required_before_all_shards": True,
                "separate_streams_required": True,
            },
            "observed_host_provenance": {
                "immutability_claim": False,
                "receipt_schema": "telos.iter205.observed_runtime_host.v1",
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
        errors.append("committed iter205 runtime manifest differs from deterministic closure")
    if raw != rendered_manifest_bytes(actual):
        errors.append("committed iter205 runtime manifest is not canonical JSON")
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
                    print(f"iter205 runtime error: {error}", file=sys.stderr)
                return 1
            print(
                "iter205 runtime manifest reproduces: "
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
        print(f"iter205 runtime error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
