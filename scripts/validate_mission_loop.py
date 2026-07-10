#!/usr/bin/env python3
"""Validate the public mission loop contract."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path.cwd()
CONTRACT = ROOT / "mission" / "loop.json"
DOC = ROOT / "docs" / "MISSION_LOOP.md"
CONTINUITY = ROOT / "CONTINUITY.md"
HANDOFF = ROOT / "HANDOFF.md"
CI = ROOT / ".github" / "workflows" / "ci.yml"

REQUIRED_PHASES = [
    "pre_register",
    "execute",
    "collect_evidence",
    "audit",
    "publish_result",
    "learn_or_stop",
    "handoff",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_gate(src: str) -> str | None:
    match = re.search(r"Current gate:\n\n- `([^`]+)`", src)
    if match:
        return match.group(1)
    match = re.search(r"Active gate: `([^`]+)`", src)
    if match:
        return match.group(1)
    return None


def main() -> int:
    failures: list[str] = []

    for path in [CONTRACT, DOC, CONTINUITY, HANDOFF, CI]:
        if not path.exists():
            failures.append(f"missing required mission-loop file: {path.relative_to(ROOT)}")

    if failures:
        for failure in failures:
            print(f"mission loop guard: {failure}")
        return 1

    contract = read_json(CONTRACT)
    doc = DOC.read_text(encoding="utf-8")
    continuity = CONTINUITY.read_text(encoding="utf-8")
    handoff = HANDOFF.read_text(encoding="utf-8")
    ci = CI.read_text(encoding="utf-8")

    if contract.get("mission_id") != "telos":
        failures.append("mission_id must be telos")
    if contract.get("standard") != "maestro-compatible-evidence-loop-v1":
        failures.append("unexpected mission loop standard")
    if "No callable Aweb/Maestro Telos capability is claimed" not in contract.get(
        "claim_boundary", ""
    ):
        failures.append("claim boundary must forbid unverified Aweb/Maestro runtime claims")

    active_gate = contract.get("active_gate")
    if active_gate != extract_gate(continuity):
        failures.append("contract active gate does not match CONTINUITY.md")
    if active_gate != extract_gate(handoff):
        failures.append("contract active gate does not match HANDOFF.md")
    if not isinstance(active_gate, str) or not (ROOT / active_gate).exists():
        failures.append("contract active gate path does not exist")

    phases = [phase.get("phase") for phase in contract.get("loop", [])]
    if phases != REQUIRED_PHASES:
        failures.append(f"mission loop phases mismatch: {phases}")

    discovery = contract.get("aweb_discovery", {})
    queries = discovery.get("queries", [])
    if len(queries) < 4:
        failures.append("Aweb discovery must record the checked catalog queries")
    if any(query.get("capability_count") != 0 for query in queries):
        failures.append("nonzero Aweb discovery count requires updating the activation claim")
    if "Register or expose a concrete Aweb/Maestro capability slug" not in discovery.get(
        "activation_gate", ""
    ):
        failures.append("Aweb activation gate is missing")

    for required in [
        "validate_mission_loop.py",
        "validate_deterministic_edit_slice.py",
        "validate_receipts.py experiments/iter03_codeclash_smoke/proof",
        "audit_codeclash_smoke.py",
        "validate_receipts.py experiments/iter05_agent_behavior_smoke/proof",
        "audit_agent_behavior_smoke.py",
        "validate_receipts.py experiments/iter23_tail_semantics_falsification/proof",
        "audit_tail_semantics_falsification.py",
        "validate_receipts.py experiments/iter24_tail_safety_control/proof",
        "audit_tail_safety_control.py",
        "validate_receipts.py experiments/iter25_tail_safety_mutation_guard/proof",
        "audit_tail_safety_mutation_guard.py",
        "validate_receipts.py experiments/iter26_own_tail_redundancy_mutation_guard/proof",
        "audit_own_tail_redundancy_mutation_guard.py",
        "validate_receipts.py experiments/iter27_semantic_claim_boundary_matrix/proof",
        "audit_semantic_claim_boundary_matrix.py",
        "validate_receipts.py experiments/iter28_public_claim_surface_guard/proof",
        "audit_public_claim_surface_guard.py",
        "validate_receipts.py experiments/iter29_public_claim_surface_negative_guard/proof",
        "audit_public_claim_surface_negative_guard.py",
        "validate_receipts.py experiments/iter30_boundary_matrix_schema_guard/proof",
        "audit_boundary_matrix_schema_guard.py",
        "validate_receipts.py experiments/iter31_claim_boundary_release_manifest/proof",
        "audit_claim_boundary_release_manifest.py",
        "validate_receipts.py experiments/iter32_claim_boundary_release_manifest_negative_guard/proof",
        "audit_claim_boundary_release_manifest_negative_guard.py",
        "validate_receipts.py experiments/iter33_release_manifest_public_sync_guard/proof",
        "audit_release_manifest_public_sync_guard.py",
        "validate_receipts.py experiments/iter34_release_manifest_public_sync_negative_guard/proof",
        "audit_release_manifest_public_sync_negative_guard.py",
        "validate_receipts.py experiments/iter35_release_manifest_self_coverage_guard/proof",
        "audit_release_manifest_self_coverage_guard.py",
        "validate_receipts.py experiments/iter36_release_manifest_self_coverage_negative_guard/proof",
        "audit_release_manifest_self_coverage_negative_guard.py",
        "validate_receipts.py experiments/iter37_release_manifest_self_coverage_public_sync_guard/proof",
        "audit_release_manifest_self_coverage_public_sync_guard.py",
        "validate_receipts.py experiments/iter38_release_manifest_self_coverage_public_sync_negative_guard/proof",
        "audit_release_manifest_self_coverage_public_sync_negative_guard.py",
        "validate_receipts.py experiments/iter39_public_task_protocol_effect_slice/proof",
        "audit_public_task_protocol_effect_slice.py",
        "validate_receipts.py experiments/iter40_public_task_protocol_effect_execution/proof",
        "audit_public_task_protocol_effect_execution.py",
        "validate_receipts.py experiments/iter41_public_task_protocol_effect_runner_recovery/proof",
        "audit_public_task_protocol_effect_runner_recovery.py",
        "validate_receipts.py experiments/iter42_public_task_protocol_effect_execution_retry/proof",
        "audit_public_task_protocol_effect_execution_retry.py",
        "validate_receipts.py experiments/iter43_provider_execution_harness_recovery/proof",
        "audit_provider_execution_harness_recovery.py",
        "validate_receipts.py experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/proof",
        "audit_public_task_protocol_effect_execution_after_harness_recovery.py",
        "validate_receipts.py experiments/iter45_public_task_condition_executor_assembly/proof",
        "audit_public_task_condition_executor_assembly.py",
        "validate_receipts.py experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor/proof",
        "audit_public_task_protocol_effect_execution_with_assembled_executor.py",
        "validate_receipts.py experiments/iter47_provider_task_condition_command_binding_recovery/proof",
        "audit_provider_task_condition_command_binding_recovery.py",
        "validate_receipts.py experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/proof",
        "audit_provider_compatible_protocol_effect_slice_refreeze.py",
        "validate_receipts.py experiments/iter49_provider_compatible_protocol_effect_execution_retry/proof",
        "audit_provider_compatible_protocol_effect_execution_retry.py",
        "validate_receipts.py experiments/iter50_provider_compatible_execution_wrapper_recovery/proof",
        "audit_provider_compatible_execution_wrapper_recovery.py",
        "validate_receipts.py experiments/iter51_provider_compatible_protocol_effect_execution_with_wrapper/proof",
        "audit_provider_compatible_protocol_effect_execution_with_wrapper.py",
        "validate_receipts.py experiments/iter52_provider_condition_runtime_separation_recovery/proof",
        "audit_provider_condition_runtime_separation_recovery.py",
        "validate_receipts.py experiments/iter53_provider_compatible_protocol_effect_execution_after_condition_recovery/proof",
        "audit_provider_compatible_protocol_effect_execution_after_condition_recovery.py",
        "validate_receipts.py experiments/iter54_provider_pair_executor_recovery/proof",
        "audit_provider_pair_executor_recovery.py",
        "validate_receipts.py experiments/iter55_provider_compatible_paid_execution_after_executor_recovery/proof",
        "audit_provider_compatible_paid_execution_after_executor_recovery.py",
        "validate_receipts.py experiments/iter56_provider_auth_recovery_for_paid_protocol_effect/proof",
        "audit_provider_auth_recovery_for_paid_protocol_effect.py",
        "validate_receipts.py experiments/iter57_provider_compatible_paid_execution_after_auth_recovery/proof",
        "audit_provider_compatible_paid_execution_after_auth_recovery.py",
        "validate_receipts.py experiments/iter58_codeclash_vertex_dependency_recovery/proof",
        "audit_codeclash_vertex_dependency_recovery.py",
        "validate_receipts.py experiments/iter59_provider_compatible_paid_execution_after_dependency_recovery/proof",
        "audit_provider_compatible_paid_execution_after_dependency_recovery.py",
        "validate_receipts.py experiments/iter60_provider_model_binding_recovery/proof",
        "audit_provider_model_binding_recovery.py",
        "validate_receipts.py experiments/iter61_vertex_quota_project_binding_recovery/proof",
        "audit_vertex_quota_project_binding_recovery.py",
        "validate_receipts.py experiments/iter62_vertex_bearer_token_path_recovery/proof",
        "audit_vertex_bearer_token_path_recovery.py",
        "validate_receipts.py experiments/iter63_vertex_access_path_parity_recheck/proof",
        "audit_vertex_access_path_parity_recheck.py",
        "validate_receipts.py experiments/iter64_provider_compatible_paid_execution_after_access_path_recovery/proof",
        "audit_provider_compatible_paid_execution_after_access_path_recovery.py",
        "validate_receipts.py experiments/iter65_receipt_schema_prompt_alignment/proof",
        "audit_receipt_schema_prompt_alignment.py",
        "validate_receipts.py experiments/iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment/proof",
        "audit_provider_compatible_paid_execution_after_receipt_prompt_alignment.py",
        "validate_receipts.py experiments/iter67_provider_compatible_expanded_slice_refreeze/proof",
        "audit_provider_compatible_expanded_slice_refreeze.py",
        "validate_receipts.py experiments/iter68_provider_compatible_task_surface_adapter_recovery/proof",
        "audit_provider_compatible_task_surface_adapter_recovery.py",
        "validate_receipts.py experiments/iter69_codeclash_task_surface_source_snapshot_recovery/proof",
        "audit_codeclash_task_surface_source_snapshot_recovery.py",
        "validate_receipts.py experiments/iter70_provider_compatible_expanded_adapter_completion/proof",
        "audit_provider_compatible_expanded_adapter_completion.py",
        "validate_receipts.py experiments/iter71_provider_compatible_expanded_slice_after_adapter_completion/proof",
        "audit_provider_compatible_expanded_slice_after_adapter_completion.py",
        "validate_receipts.py experiments/iter72_provider_compatible_expanded_paid_execution_after_slice_refreeze/proof",
        "audit_provider_compatible_expanded_paid_execution_after_slice_refreeze.py",
        "validate_receipts.py experiments/iter73_expanded_receipt_prompt_recovery_after_paid_block/proof",
        "audit_expanded_receipt_prompt_recovery_after_paid_block.py",
        "validate_receipts.py experiments/iter74_provider_compatible_expanded_paid_retry_after_receipt_prompt_recovery/proof",
        "audit_provider_compatible_expanded_paid_retry_after_receipt_prompt_recovery.py",
        "validate_receipts.py experiments/iter75_provider_compatible_runtime_adc_recovery_after_paid_retry_block/proof",
        "audit_provider_compatible_runtime_adc_recovery_after_paid_retry_block.py",
        "validate_receipts.py experiments/iter76_runtime_adc_recheck_after_operator_refresh/proof",
        "audit_runtime_adc_recheck_after_operator_refresh.py",
        "validate_receipts.py experiments/iter77_runtime_adc_recheck_after_application_default_login/proof",
        "audit_runtime_adc_recheck_after_application_default_login.py",
        "validate_receipts.py experiments/iter78_provider_compatible_expanded_paid_retry_after_adc_recovery/proof",
        "audit_provider_compatible_expanded_paid_retry_after_adc_recovery.py",
        "validate_receipts.py experiments/iter79_dummy_row_call_ceiling_recovery_after_paid_retry_block/proof",
        "audit_dummy_row_call_ceiling_recovery_after_paid_retry_block.py",
        "validate_receipts.py experiments/iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery/proof",
        "audit_dummy_call_ceiling_bounded_paid_retry_after_recovery.py",
        "validate_receipts.py experiments/iter81_expanded_stratified_adapter_validation_consolidation/proof",
        "audit_expanded_stratified_adapter_validation_consolidation.py",
        "validate_receipts.py experiments/iter82_benchmark_facing_protocol_effect_slice_design/proof",
        "audit_benchmark_facing_protocol_effect_slice_design.py",
        "validate_handoff.py",
    ]:
        if required not in "\n".join(contract.get("current_validation", [])):
            failures.append(f"mission validation command missing from contract: {required}")
        if required not in ci:
            failures.append(f"mission validation command missing from CI: {required}")

    for required in [
        "../mission/loop.json",
        "Claim not allowed now: Telos is already executing through a private Aweb/Maestro runtime.",
        "Refinement is allowed only after evidence identifies a concrete gap.",
    ]:
        if required not in doc:
            failures.append(f"mission loop doc missing required text: {required}")

    if failures:
        print("MISSION LOOP GUARD FAILED:")
        for failure in failures:
            print(" -", failure)
        return 1

    print(f"mission loop guard: active gate={active_gate} phases={len(REQUIRED_PHASES)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
