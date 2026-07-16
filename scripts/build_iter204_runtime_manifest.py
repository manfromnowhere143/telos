#!/usr/bin/env python3
"""Build or verify the additive iter204 infrastructure-recovery runtime."""

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
from scripts import collect_iter204_execution as iter204_collection  # noqa: E402
from scripts import validate_iter203_infrastructure_null as null_guard  # noqa: E402


EXPERIMENT_ID = "iter204_iter203_infrastructure_recovery"
EXP = ROOT / "experiments" / EXPERIMENT_ID
MANIFEST = EXP / "proof/raw/runtime_manifest.json"
ITER203_EXP = ROOT / "experiments/iter203_iter202_safety_recovery"
ITER203_MANIFEST = ITER203_EXP / "proof/raw/runtime_manifest.json"
ITER203_NULL = ITER203_EXP / "proof/infrastructure_null.json"
ITER203_LOGS = ITER203_EXP / "proof/raw/public_workflow_logs"
ITER203_METADATA = ITER203_EXP / "proof/raw/public_workflow_metadata"
SCHEMA = "telos.iter204.execution_runtime_recovery.v1"
ITER203_RUNTIME_SHA256 = "8beb0e845dbc9e3a4ce56832f28a62d4fd58ceac20adbc6bc06d6aef41be47e1"
ITER204_HYPOTHESIS_SHA256 = "7f6b9e0ba0ba0077115e64e38239a6eeafb2b18797fdd160a3eb9c0297396dfd"
ITER204_AGGREGATE_RECEIPT_NAME = iter204_collection.AGGREGATE_RECEIPT_NAME
ITER204_AGGREGATE_RECEIPT_SCHEMA = iter204_collection.AGGREGATE_SCHEMA
ITER204_SHARD_RECEIPT_NAME_PATTERN = "_telos_iter204_shard_{shard_index}_of_8.receipt.json"
ITER204_SHARD_RECEIPT_SCHEMA = iter204_collection.SHARD_SCHEMA
ITER204_VERIFIED_SNAPSHOT_API = (
    "scripts.collect_iter204_execution.check_execution_bundle_with_logs"
)

NEW_RUNTIME_FILES = {
    ".github/workflows/ci.yml": "primary_ci_authorization_workflow",
    ".github/workflows/iter204-execute.yml": "attempt1_only_execution_workflow",
    "experiments/iter203_iter202_safety_recovery/proof/infrastructure_null.json": (
        "exact_iter203_infrastructure_null"
    ),
    "experiments/iter204_iter203_infrastructure_recovery/HYPOTHESIS.md": (
        "post_null_pre_scientific_protocol"
    ),
    "experiments/iter204_iter203_infrastructure_recovery/proof/learning_record.json": (
        "pre_execution_learning_and_next_action_ledger"
    ),
    "experiments/iter204_iter203_infrastructure_recovery/proof/pre_execution_publication_safety.json": (
        "current_pre_execution_publication_safety_receipt"
    ),
    "scripts/adjudicate_iter204_infrastructure_recovery.py": (
        "iter204_bound_adjudicator"
    ),
    "scripts/build_iter204_runtime_manifest.py": "iter204_runtime_manifest_builder",
    "scripts/capture_iter204_runtime_host.py": "observed_host_provenance_capture",
    "scripts/ci_iter204_execute.sh": "iter204_certification_and_safe_witness_runner",
    "scripts/ci_iter204_smoke.sh": "no_science_log_driver_smoke",
    "scripts/collect_iter204_execution.py": "iter204_attempt1_chain_of_custody",
    "scripts/prepare_iter204_output_directory.py": "nofollow_empty_output_directory_guard",
    "scripts/publish_iter204_runtime_diagnostic.py": "bounded_visible_diagnostic_publisher",
    "scripts/run_iter204_infrastructure_recovery_blind_judge.py": (
        "iter204_bound_strict_blind_judge"
    ),
    "scripts/validate_iter203_infrastructure_null.py": "exact_iter203_null_guard",
    "scripts/validate_iter203_publication_safety.py": (
        "post_null_frozen_iter203_publication_receipt_validator"
    ),
    "scripts/validate_iter200_corrected_result.py": (
        "current_publication_claim_pattern_dependency"
    ),
    "scripts/validate_iter204_publication_safety.py": "current_publication_safety_guard",
    "scripts/validate_iter204_runtime_recovery.py": "runtime_recovery_contract_guard",
    "scripts/validate_supply_chain.py": "primary_ci_workflow_supply_chain_guard",
    "telos/proof.py": "publication_claim_dependency_import_closure",
    "tests/test_iter204_infrastructure_recovery.py": "runtime_recovery_regression_suite",
    "tests/test_supply_chain_guard.py": "workflow_permission_regression_suite",
}


class RuntimeRecoveryError(ValueError):
    """The iter204 runtime or one of its immutable inputs differs."""


def _load_iter203_manifest() -> dict[str, Any]:
    errors = iter203.validate_committed_manifest()
    if errors:
        raise RuntimeRecoveryError("iter203 runtime no longer reproduces: " + "; ".join(errors))
    document, raw = iter203_collection._load(ITER203_MANIFEST, canonical=True)
    if iter203.sha256(raw) != ITER203_RUNTIME_SHA256:
        raise RuntimeRecoveryError("iter203 runtime manifest SHA-256 differs")
    return document


def _validate_record(record: dict[str, Any]) -> dict[str, Any]:
    if set(record) != {"bytes", "path", "role", "sha256"}:
        raise RuntimeRecoveryError("iter203 runtime file record keys differ")
    path = ROOT / record["path"]
    payload = iter203._read_regular(path)
    if len(payload) != record["bytes"] or iter203.sha256(payload) != record["sha256"]:
        raise RuntimeRecoveryError(f"iter203 runtime input changed: {record['path']}")
    return copy.deepcopy(record)


def build_manifest() -> dict[str, Any]:
    null_guard.validate()
    upstream = _load_iter203_manifest()
    if iter203.sha256(iter203._read_regular(EXP / "HYPOTHESIS.md")) != ITER204_HYPOTHESIS_SHA256:
        raise RuntimeRecoveryError("iter204 hypothesis changed after its frozen pre-result boundary")
    files = [_validate_record(record) for record in upstream.get("files", [])]
    files.append(iter203._record(ITER203_MANIFEST, "immutable_iter203_runtime_anchor"))
    for path in sorted(ITER203_LOGS.iterdir(), key=lambda item: item.name):
        files.append(iter203._record(path, "exact_iter203_public_workflow_log_evidence"))
    for path in sorted(ITER203_METADATA.iterdir(), key=lambda item: item.name):
        files.append(iter203._record(path, "exact_iter203_public_workflow_metadata_evidence"))
    for path_text, role in NEW_RUNTIME_FILES.items():
        files.append(iter203._record(ROOT / path_text, role))
    by_path: dict[str, dict[str, Any]] = {}
    for record in files:
        previous = by_path.get(record["path"])
        if previous is not None and previous != record:
            raise RuntimeRecoveryError(f"conflicting runtime record: {record['path']}")
        by_path[record["path"]] = record
    files = sorted(by_path.values(), key=lambda record: record["path"])
    input_bridge = copy.deepcopy(upstream.get("input_bridge"))
    source_bindings = copy.deepcopy(upstream.get("source_bindings"))
    if not isinstance(input_bridge, dict) or not isinstance(source_bindings, dict):
        raise RuntimeRecoveryError("iter203 runtime lacks its exact bridge/source bindings")
    protocol = copy.deepcopy(upstream.get("protocol"))
    if not isinstance(protocol, dict):
        raise RuntimeRecoveryError("iter203 runtime protocol is malformed")
    protocol.update(
        {
            "diagnostic_observability": {
                "diagnostic_receipt_schema": "telos.iter204.runtime_diagnostic.v1",
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
                "canonical_run": "first_global_iter204_dispatch_only",
                "repository": "manfromnowhere143/telos",
                "retry": "forbidden_advance_to_iter205_after_any_failure",
                "run_attempt": 1,
                "workflow": ".github/workflows/iter204-execute.yml",
            },
            "execution_chain_of_custody": {
                "aggregate_receipt_name": ITER204_AGGREGATE_RECEIPT_NAME,
                "aggregate_receipt_schema": ITER204_AGGREGATE_RECEIPT_SCHEMA,
                "collector_eligible_artifacts": (
                    "successful_shards_from_one_github_run_and_attempt_only"
                ),
                "exact_log_set": "gold_and_variant_pair_for_each_of_50_spec_rows",
                "shard_receipt_name_pattern": ITER204_SHARD_RECEIPT_NAME_PATTERN,
                "shard_receipt_schema": ITER204_SHARD_RECEIPT_SCHEMA,
                "verified_snapshot_api": ITER204_VERIFIED_SNAPSHOT_API,
            },
            "infrastructure_recovery": {
                "iter203_head_sha": null_guard.HEAD_SHA,
                "iter203_null_receipt_sha256": iter203.sha256(
                    iter203._read_regular(ITER203_NULL)
                ),
                "iter203_public_logs_manifest_sha256": iter203.sha256(
                    iter203._read_regular(ITER203_LOGS / "manifest.json")
                ),
                "iter203_public_metadata_manifest_sha256": iter203.sha256(
                    iter203._read_regular(ITER203_METADATA / "manifest.json")
                ),
                "iter203_run_attempt": null_guard.RUN_ATTEMPT,
                "iter203_run_id": null_guard.RUN_ID,
                "moby_peeled_commit": "6430e49a55babd9b8f4d08e70ecb2b68900770fe",
                "moby_source_path": "daemon/logger/local/config.go",
                "scientific_outcomes_in_iter203": 0,
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
                    'printf "%s\\n" TELOS_ITER204_LOG_DRIVER_SMOKE_OK',
                ],
                "expected_output": "TELOS_ITER204_LOG_DRIVER_SMOKE_OK\n",
                "expected_stderr": "",
                "image": "frozen_global_ordinal_0_reference_and_id",
                "mounts": [],
                "receipt_schema": "telos.iter204.no_science_smoke_receipt.v1",
                "required_before_all_shards": True,
                "separate_streams_required": True,
            },
            "observed_host_provenance": {
                "immutability_claim": False,
                "receipt_schema": "telos.iter204.observed_runtime_host.v1",
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
        "upstream_iter203_runtime_manifest_sha256": ITER203_RUNTIME_SHA256,
        "upstream_runtime_manifest_sha256": iter203.UPSTREAM_RUNTIME_SHA256,
        "upstream_source_commit": iter203.UPSTREAM_SOURCE_COMMIT,
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
        errors.append("committed iter204 runtime manifest differs from deterministic closure")
    if raw != rendered_manifest_bytes(actual):
        errors.append("committed iter204 runtime manifest is not canonical JSON")
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
                    print(f"iter204 runtime error: {error}", file=sys.stderr)
                return 1
            print(
                "iter204 runtime manifest reproduces: "
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
    except (OSError, RuntimeRecoveryError, iter203.RuntimeManifestError) as exc:
        print(f"iter204 runtime error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
