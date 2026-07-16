#!/usr/bin/env python3
"""Validate the public mission loop contract."""

from __future__ import annotations

import json
import re
import shlex
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

CORE_VALIDATION_COMMANDS = (
    "python3 -m compileall telos scripts tests",
    "ruff check .",
    "pytest -q",
    "python3 scripts/validate_json.py",
    "python3 scripts/validate_docs.py",
    "python3 scripts/validate_current_paper.py",
    "python3 scripts/validate_mission_loop.py",
    "python3 scripts/validate_supply_chain.py",
    "python3 scripts/validate_detector_methodology_correction.py",
    "python3 scripts/validate_iter200_corrected_result.py",
    "python3 scripts/build_iter200_solve_targets.py --check",
    "python3 scripts/build_iter202_solve_targets.py --check",
    "python3 scripts/audit_iter202_sample_overlap.py --check",
    "python3 scripts/build_iter202_image_lock.py --check",
    "python3 scripts/build_iter203_safety_recovery.py --check",
    "python3 scripts/build_iter203_runtime_manifest.py --check",
    "python3 scripts/validate_iter203_publication_safety.py --check",
    "python3 scripts/validate_iter203_infrastructure_null.py",
    "python3 scripts/validate_iter204_pre_dispatch_null.py",
    "python3 scripts/validate_iter205_pre_dispatch_null.py",
    "python3 scripts/audit_iter207_claim_integrity.py --check",
    "python3 scripts/validate_iter206_pre_publication_null.py",
    "python3 scripts/build_iter207_runtime_manifest.py --check",
    "python3 scripts/validate_iter207_publication_safety.py --check",
    "python3 scripts/validate_iter207_runtime_recovery.py",
    "python3 scripts/validate_iter208_post_seal_forensic_correction.py",
    "python3 scripts/build_iter209_receipt.py --check",
    "python3 scripts/validate_iter209_publication_ci_recovery.py",
    "python3 scripts/build_iter210_receipt.py --check",
    "python3 scripts/validate_iter210_pr_synthetic_merge_recovery.py",
    "python3 scripts/build_iter211_tcp1_packet.py --check",
    "python3 scripts/build_iter211_receipt.py --check",
    "python3 scripts/validate_iter211_tcp1_materialization_preflight.py",
    "python3 scripts/validate_target_survey.py",
    "python3 scripts/validate_public_slice.py",
    "python3 scripts/validate_agent_behavior_slice.py",
    "python3 scripts/validate_deterministic_edit_slice.py",
    "python3 scripts/validate_provider_model_pilot_slice.py",
    "python3 scripts/validate_learning_ledger.py",
    "python3 scripts/validate_handoff.py",
)

SHELL_CONTROL_TOKENS = {
    "&",
    "&&",
    "(",
    ")",
    ";",
    ";&",
    ";;&",
    ";;",
    "<",
    "<<",
    ">",
    ">>",
    "|",
    "||",
}


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


def validate_gate_bindings(
    contract: dict[str, Any], continuity: str, handoff: str, *, root: Path = ROOT
) -> list[str]:
    """Bind the additive active gate separately from frozen runtime authority."""

    failures: list[str] = []
    active_gate = contract.get("active_gate")
    frozen_upstream_gate = contract.get("frozen_upstream_gate")
    continuity_gate = extract_gate(continuity)
    if frozen_upstream_gate != continuity_gate:
        failures.append("contract frozen upstream gate does not match CONTINUITY.md")
    if active_gate != extract_gate(handoff):
        failures.append("contract active gate does not match HANDOFF.md")
    if not isinstance(active_gate, str) or not (root / active_gate).exists():
        failures.append("contract active gate path does not exist")
    if not isinstance(frozen_upstream_gate, str) or not (root / frozen_upstream_gate).exists():
        failures.append("contract frozen upstream gate path does not exist")
    if active_gate == frozen_upstream_gate:
        failures.append("active gate must be distinct from the frozen upstream gate")
    handoff_frozen = re.findall(
        r"Frozen upstream gate recorded by runtime-bound `CONTINUITY\.md`: `([^`]+)`",
        handoff,
    )
    if handoff_frozen != [frozen_upstream_gate]:
        failures.append("HANDOFF.md does not bind the contract frozen upstream gate exactly once")
    return failures


def validate_iter207_recovery_state(contract: dict[str, Any]) -> list[str]:
    """Validate sealed predecessor nulls and the fail-closed iter207 recovery."""

    failures: list[str] = []
    expected_provider = {
        "solver_calls": 53,
        "scenario_calls": 39,
        "model_patches": 50,
        "scenario_programs": 38,
        "original_absent_scenarios": 1,
        "scenario_executions": 0,
        "official_certification_executions": 0,
    }
    state = contract.get("current_gate_state", {})
    if state.get("iter202_retained_provider_stage") != expected_provider:
        failures.append("iter202 retained provider-stage counts are not exact")
    expected_safety = {
        "status": "scenario_safety_protocol_execution_null",
        "safe_programs": 29,
        "rejected_programs": 9,
        "findings": 21,
        "rate_quantities": "no N, k, or u",
    }
    if state.get("iter202_safety_gate") != expected_safety:
        failures.append("iter202 safety-null disposition is not exact")
    infrastructure_null = state.get("iter203_recovery", {})
    if infrastructure_null.get("status") != "execution_infrastructure_null":
        failures.append("iter203 infrastructure-null status is not exact")
    if "50/50 first Docker run invocations returned exit 125" not in infrastructure_null.get(
        "launch_outcome", ""
    ):
        failures.append("iter203 launch-failure count is not exact")
    if infrastructure_null.get("scientific_execution") != (
        "0 patches applied, 0 official certifications, 0 scenario executions"
    ):
        failures.append("iter203 zero-execution boundary is not exact")
    if "not retained" not in infrastructure_null.get("stderr_limitation", ""):
        failures.append("iter203 missing-stderr evidence limitation is absent")
    if "reconstructed" not in infrastructure_null.get("root_cause_status", ""):
        failures.append("iter203 reconstructed root-cause status is absent")

    recovery = state.get("iter204_recovery", {})
    if recovery.get("status") != "pre_dispatch_infrastructure_null":
        failures.append("iter204 pre-dispatch-null status is not exact")
    if "same 50 valid patches" not in recovery.get("frozen_scientific_scope", ""):
        failures.append("iter204 does not preserve the all-patch scientific scope")
    if "compress=false" not in recovery.get("runtime_change", ""):
        failures.append("iter204 does not bind the narrow log-driver repair")
    if "29465584664 and 29465924803" not in recovery.get("public_push_records", ""):
        failures.append("iter204 exact push parse-failure records are absent")
    if "frozen closure snapshot" not in recovery.get("public_push_records", ""):
        failures.append("iter204 push records are not labeled as a closure snapshot")
    if "zero jobs and artifacts" not in recovery.get("public_push_records", ""):
        failures.append("iter204 zero-job/artifact push boundary is absent")
    if "at least one locally observed" not in recovery.get("dispatch_rejection", ""):
        failures.append("iter204 bounded local request observation is absent")
    if "exact request count not publicly auditable" not in recovery.get(
        "dispatch_rejection", ""
    ):
        failures.append("iter204 rejected-request count limitation is absent")
    if recovery.get("dispatch_history") != (
        "exactly zero workflow_dispatch runs at closure"
    ):
        failures.append("iter204 exact-zero workflow_dispatch boundary differs")
    if "no N, k, or u" not in recovery.get("scientific_execution", ""):
        failures.append("iter204 no-rate boundary is absent")
    if "cannot be retried or mutated" not in recovery.get("failure_rule", ""):
        failures.append("iter204 no-retry source-correction rule is absent")

    successor = state.get("iter205_recovery", {})
    if successor.get("status") != "pre_dispatch_admission_history_null":
        failures.append("iter205 admission-history-null status is not exact")
    if "same 50 valid patches" not in successor.get("frozen_scientific_scope", ""):
        failures.append("iter205 does not preserve the all-patch scientific scope")
    if "job-level to step-level env" not in successor.get("allowed_delta", ""):
        failures.append("iter205 narrow workflow-context correction is absent")
    if "workflow 314141096 active" not in successor.get("server_workflow", ""):
        failures.append("iter205 exact active workflow object is absent")
    if "histories both empty" not in successor.get("server_workflow", ""):
        failures.append("iter205 empty complete histories are absent")
    if "observed four" not in successor.get("admission_mismatch", ""):
        failures.append("iter205 exact-four upstream mismatch is absent")
    if successor.get("request_boundary") != (
        "dispatch request command not reached; 0 dispatch requests; "
        "no dispatch API response or rejection; 0 iter205 workflow runs"
    ):
        failures.append("iter205 pre-request boundary is not exact")
    if "no N, k, or u" not in successor.get("scientific_execution", ""):
        failures.append("iter205 no-rate boundary is absent")
    if "requires separately versioned iter206" not in successor.get("failure_rule", ""):
        failures.append("iter205 failure rule does not advance to iter206")

    stopped = state.get("iter206_recovery", {})
    if stopped.get("status") != (
        "pre_publication_claim_integrity_null_superseded_unpublished"
    ):
        failures.append("iter206 pre-publication null status is not exact")
    for fragment in (
        "0 branch pushes",
        "0 pull requests",
        "0 merges",
        "0 workflow runs",
        "0 dispatch requests",
    ):
        if fragment not in stopped.get("publication", ""):
            failures.append(f"iter206 zero-publication boundary missing: {fragment}")
    if "no N, k, or u" not in stopped.get("scientific_execution", ""):
        failures.append("iter206 no-rate boundary is absent")
    if stopped.get("source_commit") != "e7c2ec28daa746dbcfb5812d3771ab981ff984c0":
        failures.append("iter206 frozen source identity differs")
    if stopped.get("seal_commit") != "a2a05ef2ed05a0c457076f2bd5f1475507190685":
        failures.append("iter206 frozen seal identity differs")

    expected_correction = {
        "ledger": (
            "experiments/iter207_claim_integrity_and_admission_recovery/"
            "proof/claim_integrity_correction.json"
        ),
        "iter192_status": (
            "conservative_novelty_fail_literal_v1_trigger_indeterminate_"
            "construct_recount_retained"
        ),
        "iter195_status": (
            "strict_protocol_fail_ten_exploratory_reference_differentials_retained"
        ),
        "iter196_status": "partial_protocol_blocked",
        "iter179_cost_status": "score_guard_13_128090_diagnostics_excluded_not_invoice",
        "iter198_status": "accuracy_fail_writing_artifacts_retained",
        "iter199_status": "registration_timing_not_independently_established",
        "corpus_label": (
            "22_gold_assisted_targeted_reference_differential_rows_"
            "not_independent_semantic_ground_truth"
        ),
    }
    if state.get("construction_integrity_correction") != expected_correction:
        failures.append("iter207 construction-integrity correction is not exact")

    active = state.get("iter207_recovery", {})
    if active.get("status") != (
        "active_pre_publication_pre_dispatch_pre_scientific_output_"
        "claim_integrity_and_admission_recovery"
    ):
        failures.append("iter207 active recovery status is not exact")
    if "same 50 patches" not in active.get("frozen_scientific_scope", ""):
        failures.append("iter207 does not preserve the all-patch scientific scope")
    allowed = active.get("allowed_delta", "")
    for fragment in (
        "claim corrections",
        "iter206 terminal null",
        "mechanical iter206-to-iter207 identities",
        "bind exact empty iter206 histories",
    ):
        if fragment not in allowed:
            failures.append(f"iter207 allowed delta missing: {fragment}")
    publication = active.get("publication_envelope", "")
    for fragment in (
        "push agent/iter207-claim-integrity-admission-recovery exactly once",
        "one successful attempt-1 ci.yml push run",
        "one successful attempt-1 pull_request run",
        "merge once",
        "first parent 4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f",
        "no follow-up push",
    ):
        if fragment not in publication:
            failures.append(f"iter207 publication envelope missing: {fragment}")
    selection = active.get("selection_rule", "")
    for fragment in (
        "exact iter204 run numbers 1..6",
        "frozen rows 1..4",
        "structurally bound iter207 publication rows 5..6",
        "empty iter204 dispatch, iter205, and iter206 histories",
        "empty iter207 histories before at most one request",
    ):
        if fragment not in selection:
            failures.append(f"iter207 selection rule missing: {fragment}")
    if "closes iter207 without retry" not in active.get("failure_rule", ""):
        failures.append("iter207 no-retry failure rule is absent")

    claim = contract.get("claim_boundary", "")
    for fragment in (
        "iter192 is conservatively adjudicated FAIL",
        "literal v1-specific falsifier trigger is indeterminate",
        "Iter195 is strict protocol FAIL",
        "22 official-harness-resolved, gold-assisted targeted reference-differential rows",
        "not independent semantic ground truth",
        "iter196 is partial/protocol-blocked",
        "iter199 is post-provider/pre-execution",
        "$13.128090 estimated spend guard for 240 score-producing calls",
        "rounded $13.59 through-repair total includes excluded diagnostics",
        "not a provider invoice",
        "four disclosed shared-line diagnostic rows",
        "N=24, k=1, u=6",
        "Iter202 is a provider-complete pre-execution safety null",
        "iter203 is an execution-infrastructure null",
        "iter204 is a pre-dispatch parse null",
        "iter205 is a pre-dispatch admission-history null",
        "iter206 is a locally sealed pre-publication claim-integrity null",
        "Iter207 is the active separately versioned correction and admission recovery",
        "exact fixed 50-row scientific/runtime plan",
        "exact-six iter204 snapshot",
        "empty complete iter205 and iter206 histories",
        "Telos operates from its standalone repository",
    ):
        if fragment not in claim:
            failures.append(f"claim boundary missing current recovery fact: {fragment}")

    required_sources = {
        "experiments/iter202_natural_rate_scaled/RESULT.md",
        "experiments/iter202_natural_rate_scaled/proof/learning_record.json",
        "experiments/iter203_iter202_safety_recovery/HYPOTHESIS.md",
        "experiments/iter203_iter202_safety_recovery/UPSTREAM_PROTOCOL_NULL.md",
        "experiments/iter203_iter202_safety_recovery/RESULT.md",
        "experiments/iter203_iter202_safety_recovery/proof/learning_record.json",
        "experiments/iter203_iter202_safety_recovery/proof/infrastructure_null.json",
        "experiments/iter204_iter203_infrastructure_recovery/HYPOTHESIS.md",
        "experiments/iter204_iter203_infrastructure_recovery/RESULT.md",
        "experiments/iter204_iter203_infrastructure_recovery/proof/learning_record.json",
        "experiments/iter204_iter203_infrastructure_recovery/proof/learning_record.pre_dispatch_null.json",
        "experiments/iter204_iter203_infrastructure_recovery/proof/pre_dispatch_infrastructure_null.json",
        "experiments/iter204_iter203_infrastructure_recovery/proof/raw/public_dispatch_metadata/manifest.json",
        "experiments/iter204_iter203_infrastructure_recovery/proof/raw/runtime_manifest.json",
        "experiments/iter204_iter203_infrastructure_recovery/proof/pre_execution_publication_safety.json",
        "experiments/iter205_iter204_workflow_context_recovery/HYPOTHESIS.md",
        "experiments/iter205_iter204_workflow_context_recovery/RESULT.md",
        "experiments/iter205_iter204_workflow_context_recovery/proof/learning_record.json",
        "experiments/iter205_iter204_workflow_context_recovery/proof/learning_record.pre_dispatch_admission_null.json",
        "experiments/iter205_iter204_workflow_context_recovery/proof/pre_dispatch_admission_null.json",
        "experiments/iter205_iter204_workflow_context_recovery/proof/raw/public_admission_metadata/manifest.json",
        "experiments/iter205_iter204_workflow_context_recovery/proof/raw/runtime_manifest.json",
        "experiments/iter205_iter204_workflow_context_recovery/proof/pre_execution_publication_safety.json",
        "experiments/iter206_iter205_admission_history_recovery/HYPOTHESIS.md",
        "experiments/iter206_iter205_admission_history_recovery/proof/learning_record.json",
        "experiments/iter206_iter205_admission_history_recovery/proof/raw/runtime_manifest.json",
        "experiments/iter206_iter205_admission_history_recovery/proof/pre_execution_publication_safety.json",
        "experiments/iter206_iter205_admission_history_recovery/RESULT.md",
        "experiments/iter206_iter205_admission_history_recovery/proof/pre_publication_claim_integrity_null.json",
        "experiments/iter206_iter205_admission_history_recovery/proof/learning_record.pre_publication_claim_integrity_null.json",
        "experiments/iter207_claim_integrity_and_admission_recovery/HYPOTHESIS.md",
        "experiments/iter207_claim_integrity_and_admission_recovery/proof/claim_integrity_correction.json",
        "experiments/iter207_claim_integrity_and_admission_recovery/proof/corrections/iter192_novelty_scope_correction.json",
        "experiments/iter207_claim_integrity_and_admission_recovery/proof/strict/iter195_protocol_failure.json",
        "experiments/iter207_claim_integrity_and_admission_recovery/proof/learning_record.json",
        ".github/workflows/iter203-execute.yml",
        ".github/workflows/iter204-execute.yml",
        ".github/workflows/iter205-execute.yml",
        ".github/workflows/iter206-execute.yml",
        ".github/workflows/iter207-execute.yml",
        "scripts/build_iter203_safety_recovery.py",
        "scripts/build_iter203_runtime_manifest.py",
        "scripts/validate_iter203_publication_safety.py",
        "scripts/collect_iter203_execution.py",
        "scripts/validate_iter203_infrastructure_null.py",
        "scripts/build_iter204_runtime_manifest.py",
        "scripts/capture_iter204_runtime_host.py",
        "scripts/prepare_iter204_output_directory.py",
        "scripts/publish_iter204_runtime_diagnostic.py",
        "scripts/ci_iter204_smoke.sh",
        "scripts/ci_iter204_execute.sh",
        "scripts/collect_iter204_execution.py",
        "scripts/adjudicate_iter204_infrastructure_recovery.py",
        "scripts/run_iter204_infrastructure_recovery_blind_judge.py",
        "scripts/validate_iter204_publication_safety.py",
        "scripts/validate_iter204_runtime_recovery.py",
        "scripts/validate_iter204_pre_dispatch_null.py",
        "scripts/adjudicate_iter205_workflow_context_recovery.py",
        "scripts/build_iter205_runtime_manifest.py",
        "scripts/capture_iter205_runtime_host.py",
        "scripts/ci_iter205_smoke.sh",
        "scripts/ci_iter205_execute.sh",
        "scripts/collect_iter205_execution.py",
        "scripts/prepare_iter205_output_directory.py",
        "scripts/publish_iter205_runtime_diagnostic.py",
        "scripts/run_iter205_workflow_context_recovery_blind_judge.py",
        "scripts/validate_iter205_publication_safety.py",
        "scripts/validate_iter205_runtime_recovery.py",
        "scripts/validate_iter205_pre_dispatch_null.py",
        "scripts/adjudicate_iter206_admission_history_recovery.py",
        "scripts/build_iter206_runtime_manifest.py",
        "scripts/capture_iter206_runtime_host.py",
        "scripts/ci_iter206_smoke.sh",
        "scripts/ci_iter206_execute.sh",
        "scripts/collect_iter206_execution.py",
        "scripts/prepare_iter206_output_directory.py",
        "scripts/publish_iter206_runtime_diagnostic.py",
        "scripts/run_iter206_admission_history_recovery_blind_judge.py",
        "scripts/validate_iter206_publication_safety.py",
        "scripts/validate_iter206_runtime_recovery.py",
        "scripts/validate_iter206_pre_publication_null.py",
        "scripts/audit_iter207_claim_integrity.py",
        "scripts/build_iter207_runtime_manifest.py",
        "scripts/capture_iter207_runtime_host.py",
        "scripts/ci_iter207_smoke.sh",
        "scripts/ci_iter207_execute.sh",
        "scripts/collect_iter207_execution.py",
        "scripts/prepare_iter207_output_directory.py",
        "scripts/publish_iter207_runtime_diagnostic.py",
        "scripts/adjudicate_iter207_claim_integrity_and_admission_recovery.py",
        "scripts/run_iter207_claim_integrity_and_admission_recovery_blind_judge.py",
        "scripts/validate_iter207_publication_safety.py",
        "scripts/validate_iter207_runtime_recovery.py",
        "tests/test_iter204_pre_dispatch_null.py",
        "tests/test_iter205_workflow_context_recovery.py",
        "tests/test_iter205_pre_dispatch_null.py",
        "tests/test_iter206_admission_history_recovery.py",
        "tests/test_iter206_pre_publication_null.py",
        "tests/test_audit_iter207_claim_integrity.py",
        "tests/test_iter207_claim_integrity_and_admission_recovery.py",
        "experiments/iter203_iter202_safety_recovery/proof/raw/runtime_manifest.json",
        "experiments/iter203_iter202_safety_recovery/proof/pre_execution_publication_safety.json",
    }
    sources = contract.get("source_of_truth", [])
    if not isinstance(sources, list) or not required_sources.issubset(set(sources)):
        failures.append("iter203--iter207 source-of-truth set is incomplete")
    else:
        missing_required_sources = sorted(
            source for source in required_sources if not (ROOT / source).is_file()
        )
        if missing_required_sources:
            failures.append(
                "iter203--iter207 source-of-truth files are absent: "
                + ", ".join(missing_required_sources)
            )
    return failures


def validate_iter208_correction_state(
    contract: dict[str, Any], *, root: Path = ROOT
) -> list[str]:
    """Validate the sealed iter208 correction and its failed publication attempt."""

    failures: list[str] = []
    expected_gate = "experiments/iter208_post_seal_forensic_correction/HYPOTHESIS.md"
    if not (root / expected_gate).is_file():
        failures.append("iter208 sealed publication gate is absent")

    state = contract.get("current_gate_state", {}).get("iter208_correction", {})
    if state.get("status") != "sealed_publication_correction_remote_ci_failed":
        failures.append("iter208 correction status differs")
    if state.get("predecessor_seal") != "f4ee0d5bcb3b4abee7ebf1683be5b9edda263c28":
        failures.append("iter208 predecessor seal differs")
    if state.get("source_commit") != "184883088336cbae834e812a8d1dce0b7b031821":
        failures.append("iter208 source commit differs")
    if state.get("seal_commit") != "a2c2863cf993cb6dd39d2fada8d58e4796929120":
        failures.append("iter208 seal commit differs")
    actions = state.get("actions_before_source_seal")
    if not isinstance(actions, dict) or not actions or any(value != 0 for value in actions.values()):
        failures.append("iter208 pre-seal action ledger is not exact zero")
    if "no scientific numerator or denominator" not in state.get("claim_boundary", ""):
        failures.append("iter208 scientific claim boundary is absent")
    if "artifact-bound receipt v2" not in state.get("correction_scope", ""):
        failures.append("iter208 correction scope omits receipt v2")
    attempt = state.get("remote_publication_attempt", {})
    if not (
        isinstance(attempt, dict)
        and attempt.get("draft_pull_request") == 8
        and attempt.get("push_ci_run") == 29491806574
        and attempt.get("pull_request_ci_run") == 29491841840
        and attempt.get("head_sha") == "a2c2863cf993cb6dd39d2fada8d58e4796929120"
        and attempt.get("merged") is False
        and attempt.get("failed_branch_mutated_after_observation") is False
    ):
        failures.append("iter208 remote publication failure record differs")

    claim = contract.get("publication_claim_boundary", "")
    for fragment in (
        "Iter207 is the immutable local correction and admission baseline",
        "Iter208 is the sealed post-seal forensic correction",
        "failed two non-scientific CI validators and was not merged",
        "Iter210 merged through PR #10",
        "Iter211 is the active zero-execution TCP-1 materialization preflight",
        "Iter208 through iter211 are not population estimates",
    ):
        if fragment not in claim:
            failures.append(f"claim boundary missing publication-recovery fact: {fragment}")

    required_sources = {
        "AGENTS.md",
        "CITATION.cff",
        "docs/FORENSIC-AUDIT-2026-07-16.md",
        "docs/TELOS-ROADMAP-2026.md",
        expected_gate,
        "experiments/iter208_post_seal_forensic_correction/RESULT.md",
        "experiments/iter208_post_seal_forensic_correction/proof/forensic_findings.json",
        "experiments/iter208_post_seal_forensic_correction/proof/frontier_sources.json",
        "experiments/iter208_post_seal_forensic_correction/proof/hardware_preflight.json",
        "experiments/iter208_post_seal_forensic_correction/proof/receipt_v2.json",
        "scripts/validate_iter208_post_seal_forensic_correction.py",
        "scripts/validate_handoff.py",
        "tests/test_iter208_post_seal_forensic_correction.py",
        "tests/test_make_handoff.py",
    }
    sources = contract.get("source_of_truth", [])
    if not isinstance(sources, list) or not required_sources.issubset(set(sources)):
        failures.append("iter208 source-of-truth set is incomplete")
    else:
        missing = sorted(source for source in required_sources if not (root / source).is_file())
        if missing:
            failures.append("iter208 source-of-truth files are absent: " + ", ".join(missing))
    return failures


def validate_iter209_recovery_state(
    contract: dict[str, Any], *, root: Path = ROOT
) -> list[str]:
    """Validate sealed iter209 and its PR-only publication failure."""

    failures: list[str] = []
    expected_gate = "experiments/iter209_publication_ci_recovery/HYPOTHESIS.md"
    if not (root / expected_gate).is_file():
        failures.append("iter209 sealed publication gate is absent")
    state = contract.get("current_gate_state", {}).get("iter209_recovery", {})
    if state.get("status") != "sealed_publication_ci_recovery_pr_ci_failed":
        failures.append("iter209 recovery status differs")
    if state.get("predecessor_seal") != "a2c2863cf993cb6dd39d2fada8d58e4796929120":
        failures.append("iter209 predecessor seal differs")
    if state.get("source_commit") != "1659670c6c13758cc9b1840e87633a627444ca39":
        failures.append("iter209 source commit differs")
    if state.get("seal_commit") != "91f9258730bf5520d86c9235d7ed2f03724ea103":
        failures.append("iter209 seal commit differs")
    actions = state.get("actions_before_source_seal")
    if not isinstance(actions, dict) or not actions or any(value != 0 for value in actions.values()):
        failures.append("iter209 pre-seal action ledger is not exact zero")
    if "no scientific numerator, denominator, score, or result" not in state.get(
        "claim_boundary", ""
    ):
        failures.append("iter209 scientific claim boundary is absent")
    for fragment in (
        "historical Git-blob hash validation",
        "pull-request test-environment isolation",
        "iter208 descendant-safe receipt validation",
        "no scientific change",
    ):
        if fragment not in state.get("correction_scope", ""):
            failures.append(f"iter209 correction scope is incomplete: {fragment}")
    attempt = state.get("remote_publication_attempt", {})
    if not (
        isinstance(attempt, dict)
        and attempt.get("draft_pull_request") == 9
        and attempt.get("push_ci_run") == 29493772108
        and attempt.get("push_ci_conclusion") == "success"
        and attempt.get("pull_request_ci_run") == 29494386126
        and attempt.get("pull_request_ci_conclusion") == "failure"
        and attempt.get("head_sha") == "91f9258730bf5520d86c9235d7ed2f03724ea103"
        and attempt.get("merged") is False
        and attempt.get("failed_branch_mutated_after_observation") is False
    ):
        failures.append("iter209 remote publication record differs")
    required_sources = {
        expected_gate,
        "experiments/iter209_publication_ci_recovery/RESULT.md",
        "experiments/iter209_publication_ci_recovery/proof/ci_failure_diagnosis.json",
        "experiments/iter209_publication_ci_recovery/proof/receipt_v2.json",
        "scripts/audit_receipt_schema_prompt_alignment.py",
        "scripts/build_iter209_receipt.py",
        "scripts/validate_current_paper.py",
        "scripts/validate_iter208_post_seal_forensic_correction.py",
        "scripts/validate_iter209_publication_ci_recovery.py",
        "tests/test_iter209_publication_ci_recovery.py",
    }
    sources = contract.get("source_of_truth", [])
    if not isinstance(sources, list) or not required_sources.issubset(set(sources)):
        failures.append("iter209 source-of-truth set is incomplete")
    else:
        missing = sorted(source for source in required_sources if not (root / source).is_file())
        if missing:
            failures.append("iter209 source-of-truth files are absent: " + ", ".join(missing))
    return failures


def validate_iter210_recovery_state(
    contract: dict[str, Any], *, root: Path = ROOT
) -> list[str]:
    """Validate the sealed and merged PR-topology recovery above iter209."""

    failures: list[str] = []
    expected_gate = "experiments/iter210_pr_synthetic_merge_recovery/HYPOTHESIS.md"
    if not (root / expected_gate).is_file():
        failures.append("iter210 sealed publication gate is absent")
    state = contract.get("current_gate_state", {}).get("iter210_recovery", {})
    if state.get("status") != "merged_publication_recovery_green":
        failures.append("iter210 recovery status differs")
    if state.get("predecessor_seal") != "91f9258730bf5520d86c9235d7ed2f03724ea103":
        failures.append("iter210 predecessor seal differs")
    expected_publication = {
        "source_commit": "323130bd96b20c062005f097294d8fab235bea93",
        "seal_commit": "c109312d5ee525599abfbac178c3fb245117ab49",
        "pull_request": 10,
        "merge_commit": "fb348eb1f67c0605679cd56a1cfa210cf192db03",
        "push_ci_run": 29496323167,
        "pull_request_ci_run": 29496355871,
        "merged_master_ci_run": 29496560409,
    }
    for field, expected in expected_publication.items():
        if state.get(field) != expected:
            failures.append(f"iter210 merged publication {field} differs")
    actions = state.get("actions_before_source_seal")
    if not isinstance(actions, dict) or not actions or any(value != 0 for value in actions.values()):
        failures.append("iter210 pre-seal action ledger is not exact zero")
    if "no scientific numerator, denominator, score, or result" not in state.get(
        "claim_boundary", ""
    ):
        failures.append("iter210 scientific claim boundary is absent")
    for fragment in (
        "exact iter209 sealed-target selection",
        "Git-blob-bound descendant receipt checks",
        "handoff-derived source/seal parent topology",
        "no scientific change",
    ):
        if fragment not in state.get("correction_scope", ""):
            failures.append(f"iter210 correction scope is incomplete: {fragment}")
    claim = contract.get("publication_claim_boundary", "")
    for fragment in (
        "Iter209 fixed those defects and passed push CI",
        "pull-request CI exposed one synthetic-merge branch-tip assumption",
        "Iter210 merged through PR #10",
        "Iter211 is the active zero-execution TCP-1 materialization preflight",
        "scientific execution remains blocked",
    ):
        if fragment not in claim:
            failures.append(f"claim boundary missing iter210 fact: {fragment}")
    required_sources = {
        expected_gate,
        "experiments/iter210_pr_synthetic_merge_recovery/RESULT.md",
        "experiments/iter210_pr_synthetic_merge_recovery/proof/pr_synthetic_merge_failure.json",
        "experiments/iter210_pr_synthetic_merge_recovery/proof/receipt_v2.json",
        "scripts/build_iter209_receipt.py",
        "scripts/build_iter210_receipt.py",
        "scripts/validate_iter209_publication_ci_recovery.py",
        "scripts/validate_iter210_pr_synthetic_merge_recovery.py",
        "tests/test_iter209_publication_ci_recovery.py",
        "tests/test_iter210_pr_synthetic_merge_recovery.py",
    }
    sources = contract.get("source_of_truth", [])
    if not isinstance(sources, list) or not required_sources.issubset(set(sources)):
        failures.append("iter210 source-of-truth set is incomplete")
    else:
        missing = sorted(source for source in required_sources if not (root / source).is_file())
        if missing:
            failures.append("iter210 source-of-truth files are absent: " + ", ".join(missing))
    return failures


def validate_iter211_materialization_state(
    contract: dict[str, Any], *, root: Path = ROOT
) -> list[str]:
    """Validate the active zero-execution TCP-1 materialization boundary."""

    failures: list[str] = []
    expected_gate = "experiments/iter211_tcp1_materialization_preflight/HYPOTHESIS.md"
    if contract.get("active_publication_gate") != expected_gate:
        failures.append("iter211 active publication gate differs")
    if not (root / expected_gate).is_file():
        failures.append("iter211 active materialization gate is absent")
    state = contract.get("current_gate_state", {}).get("iter211_tcp1_materialization", {})
    expected = {
        "status": "materialization_preflight_pass_execution_blocked",
        "predecessor_merge": "fb348eb1f67c0605679cd56a1cfa210cf192db03",
        "planned_task_count": 12,
        "seeds_per_task": 5,
        "planned_natural_trajectories": 60,
        "admitted_task_count": 0,
        "filled_reviewer_roles": 0,
        "passed_gate_count": 2,
        "blocked_gate_count": 9,
        "accelerator_hour_ceiling": 64,
        "accelerator_hours_used": 0,
        "provider_calls": 0,
        "scientific_trajectories": 0,
        "execution_authorized": False,
        "next_gate": (
            "experiments/iter212_tcp1_independent_cohort_and_custody_freeze/HYPOTHESIS.md"
        ),
    }
    for field, value in expected.items():
        if state.get(field) != value:
            failures.append(f"iter211 materialization {field} differs")
    for fragment in (
        "deterministic TCP-1 protocol",
        "custody schemas",
        "separate controls",
        "isolation threat model",
        "no scientific execution",
    ):
        if fragment not in state.get("correction_scope", ""):
            failures.append(f"iter211 materialization scope omits: {fragment}")
    claim = state.get("claim_boundary", "")
    for fragment in ("no scientific numerator", "ranking", "state-of-the-art result"):
        if fragment not in claim:
            failures.append(f"iter211 claim boundary omits: {fragment}")

    admission_path = root / "experiments/iter211_tcp1_materialization_preflight/proof/admission_report.json"
    try:
        admission = read_json(admission_path)
    except (OSError, json.JSONDecodeError):
        failures.append("iter211 admission report is unreadable")
    else:
        if not (
            admission.get("materialization_preflight_status") == "pass"
            and admission.get("scientific_execution_admission") == "blocked"
            and admission.get("passed_gate_count") == 2
            and admission.get("blocked_gate_count") == 9
            and admission.get("execution_authorized") is False
        ):
            failures.append("iter211 admission report overstates readiness")

    required_sources = {
        expected_gate,
        "experiments/iter211_tcp1_materialization_preflight/RESULT.md",
        "experiments/iter211_tcp1_materialization_preflight/proof/admission_report.json",
        "experiments/iter211_tcp1_materialization_preflight/proof/analysis_plan.json",
        "experiments/iter211_tcp1_materialization_preflight/proof/protocol.json",
        "experiments/iter211_tcp1_materialization_preflight/proof/receipt_v2.json",
        "experiments/iter211_tcp1_materialization_preflight/proof/review.md",
        "experiments/iter212_tcp1_independent_cohort_and_custody_freeze/HYPOTHESIS.md",
        "scripts/build_iter211_handoff.py",
        "scripts/build_iter211_receipt.py",
        "scripts/build_iter211_tcp1_packet.py",
        "scripts/validate_iter211_tcp1_materialization_preflight.py",
        "telos/tcp1.py",
        "tests/test_iter211_tcp1_materialization_preflight.py",
        "tests/test_tcp1.py",
    }
    sources = contract.get("source_of_truth", [])
    if not isinstance(sources, list) or not required_sources.issubset(set(sources)):
        failures.append("iter211 source-of-truth set is incomplete")
    else:
        missing = sorted(source for source in required_sources if not (root / source).is_file())
        if missing:
            failures.append("iter211 source-of-truth files are absent: " + ", ".join(missing))
    return failures


def validate_iter204_recovery_state(contract: dict[str, Any]) -> list[str]:
    """Compatibility alias for the current recovery validator."""

    return validate_iter207_recovery_state(contract)


def validate_iter205_recovery_state(contract: dict[str, Any]) -> list[str]:
    """Compatibility alias for callers predating the iter206 gate."""

    return validate_iter207_recovery_state(contract)


def validate_iter206_recovery_state(contract: dict[str, Any]) -> list[str]:
    """Compatibility alias for callers predating the iter207 gate."""

    return validate_iter207_recovery_state(contract)


def _decode_inline_yaml_scalar(value: str) -> str | None:
    """Decode the small YAML scalar subset accepted for workflow ``run`` values."""

    value = value.strip()
    if not value:
        return None
    if value.startswith('"'):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return None
        return decoded if isinstance(decoded, str) else None
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            return None
        return value[1:-1].replace("''", "'")
    return value


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _block_end(lines: list[str], start: int, indent: int, *, list_item: bool) -> int:
    """Return the exclusive end of one YAML mapping or list-item mapping."""

    for index in range(start + 1, len(lines)):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        candidate_indent = _indent(line)
        if candidate_indent < indent:
            return index
        if list_item and candidate_indent == indent and line.lstrip().startswith("- "):
            return index
        if not list_item and candidate_indent == indent:
            return index
    return len(lines)


def _mapping_has_key(
    lines: list[str],
    start: int,
    end: int,
    *,
    indent: int,
    key: str,
    list_item: bool = False,
) -> bool:
    """Return whether a key occurs directly in one YAML mapping."""

    escaped = re.escape(key)
    key_pattern = re.compile(rf"(?:{escaped}|'{escaped}'|\"{escaped}\")\s*:")
    for index in range(start, end):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if _indent(line) != indent:
            continue
        stripped = line.lstrip()
        if list_item and index == start:
            stripped = re.sub(r"^-\s+", "", stripped, count=1)
        if key_pattern.match(stripped):
            return True
    return False


def _mapping_has_run_default_override(
    lines: list[str], start: int, end: int, *, mapping_indent: int
) -> bool:
    """Reject shell or working-directory remapping below a direct ``defaults`` key."""

    for index in range(start, end):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if _indent(line) != mapping_indent:
            continue
        defaults_match = re.match(
            r"(?:defaults|'defaults'|\"defaults\")\s*:\s*(.*?)\s*$",
            line.lstrip(),
        )
        if defaults_match is None:
            continue
        inline_value = defaults_match.group(1)
        if inline_value and not inline_value.startswith("#"):
            return True
        defaults_end = _block_end(lines, index, mapping_indent, list_item=False)
        for nested in lines[index + 1 : defaults_end]:
            if not nested.strip() or nested.lstrip().startswith("#"):
                continue
            if re.match(
                r"(?:shell|working-directory|'shell'|'working-directory'|"
                r"\"shell\"|\"working-directory\")\s*:",
                nested.lstrip(),
            ):
                return True
            if re.match(r"(?:<<\s*:|[^:#]+:\s*\*)", nested.lstrip()):
                return True
    return False


def _workflow_has_run_default_override(lines: list[str]) -> bool:
    """Return whether workflow-wide defaults can change command interpretation."""

    return _mapping_has_run_default_override(
        lines,
        0,
        len(lines),
        mapping_indent=0,
    )


def _run_step_is_unconditional(lines: list[str], run_index: int, run_indent: int) -> bool:
    """Accept a run key only on a direct, fail-closed execution path."""

    step_start: int | None = None
    step_indent: int | None = None
    for index in range(run_index, -1, -1):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        candidate_indent = _indent(line)
        if line.lstrip().startswith("- ") and candidate_indent <= run_indent:
            step_start = index
            step_indent = candidate_indent
            break
    if step_start is None or step_indent is None:
        return False

    steps_start: int | None = None
    steps_indent: int | None = None
    for index in range(step_start - 1, -1, -1):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        candidate_indent = _indent(line)
        if candidate_indent < step_indent and re.fullmatch(r"steps\s*:\s*", line.lstrip()):
            steps_start = index
            steps_indent = candidate_indent
            break
        if candidate_indent < step_indent - 2:
            break
    if steps_start is None or steps_indent is None:
        return False

    step_end = _block_end(lines, step_start, step_indent, list_item=True)
    if any(
        _mapping_has_key(
            lines,
            step_start,
            step_end,
            indent=step_indent if key_on_list_item else step_indent + 2,
            key=key,
            list_item=key_on_list_item,
        )
        for key in ("if", "continue-on-error", "shell", "working-directory", "<<")
        for key_on_list_item in (True, False)
    ):
        return False

    job_start: int | None = None
    job_indent: int | None = None
    for index in range(steps_start - 1, -1, -1):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        candidate_indent = _indent(line)
        if candidate_indent < steps_indent and re.fullmatch(
            r"[^:#][^:]*\s*:\s*", line.lstrip()
        ):
            job_start = index
            job_indent = candidate_indent
            break
    if job_start is None or job_indent is None:
        return False

    job_end = _block_end(lines, job_start, job_indent, list_item=False)
    if any(
        _mapping_has_key(
            lines,
            job_start,
            job_end,
            indent=job_indent + 2,
            key=key,
        )
        for key in ("if", "continue-on-error", "needs", "<<")
    ):
        return False
    return not _mapping_has_run_default_override(
        lines,
        job_start,
        job_end,
        mapping_indent=job_indent + 2,
    )


def ci_run_scripts(source: str) -> list[str]:
    """Extract active GitHub Actions ``run`` scalars without treating comments as steps."""

    lines = source.splitlines()
    workflow_defaults_safe = not _workflow_has_run_default_override(lines)
    scripts: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)
        match = re.fullmatch(r"(?:-\s+)?run\s*:\s*(.*?)\s*", stripped)
        if not match:
            index += 1
            continue

        value = match.group(1)
        unconditional = workflow_defaults_safe and _run_step_is_unconditional(
            lines, index, indent
        )
        block_match = re.fullmatch(r"([|>])(?:[+-]?\d*|\d*[+-]?)(?:\s+#.*)?", value)
        if not block_match:
            decoded = _decode_inline_yaml_scalar(value)
            if unconditional and decoded is not None:
                scripts.append(decoded)
            index += 1
            continue

        block_lines: list[str] = []
        index += 1
        while index < len(lines):
            candidate = lines[index]
            candidate_stripped = candidate.lstrip(" ")
            candidate_indent = len(candidate) - len(candidate_stripped)
            if candidate.strip() and candidate_indent <= indent:
                break
            block_lines.append(candidate)
            index += 1
        nonblank_indents = [
            len(item) - len(item.lstrip(" ")) for item in block_lines if item.strip()
        ]
        if not nonblank_indents:
            continue
        block_indent = min(nonblank_indents)
        deindented = [
            item[block_indent:] if item.strip() else "" for item in block_lines
        ]
        separator = "\n" if block_match.group(1) == "|" else " "
        if unconditional:
            scripts.append(separator.join(deindented))
    return scripts


def standalone_shell_command(script: str) -> tuple[str, ...] | None:
    """Return tokens only when a run scalar is one unconditional simple command."""

    logical_lines: list[str] = []
    pending = ""
    for raw_line in script.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith("\\") and not line.endswith("\\\\"):
            pending += line[:-1].rstrip() + " "
            continue
        logical_lines.append(pending + line)
        pending = ""
    if pending or len(logical_lines) != 1:
        return None

    lexer = shlex.shlex(
        logical_lines[0],
        posix=True,
        punctuation_chars="();<>|&",
    )
    lexer.whitespace_split = True
    lexer.commenters = "#"
    try:
        tokens = tuple(lexer)
    except ValueError:
        return None
    if not tokens or any(token in SHELL_CONTROL_TOKENS for token in tokens):
        return None
    return tokens


def executable_ci_commands(source: str) -> set[tuple[str, ...]]:
    """Return stand-alone commands that GitHub Actions will actually execute."""

    commands: set[tuple[str, ...]] = set()
    for script in ci_run_scripts(source):
        command = standalone_shell_command(script)
        if command is not None:
            commands.add(command)
    return commands


def validate_current_validation(
    contract: dict[str, Any],
    ci: str,
    *,
    required_commands: tuple[str, ...] = CORE_VALIDATION_COMMANDS,
) -> list[str]:
    """Validate exact contract membership and executable CI coverage."""

    failures: list[str] = []
    raw_commands = contract.get("current_validation")
    if not isinstance(raw_commands, list) or not raw_commands:
        return ["current_validation must be a nonempty command list"]
    if any(not isinstance(command, str) for command in raw_commands):
        return ["current_validation entries must all be strings"]

    commands = list(raw_commands)
    if len(commands) != len(set(commands)):
        failures.append("current_validation contains duplicate commands")

    parsed_commands: dict[str, tuple[str, ...]] = {}
    for command in commands:
        parsed = standalone_shell_command(command)
        if parsed is None or shlex.join(parsed) != command:
            failures.append(f"current_validation command is not canonical: {command!r}")
            continue
        parsed_commands[command] = parsed

    for required in required_commands:
        if required not in commands:
            failures.append(f"core mission validation command missing from contract: {required}")

    ci_commands = executable_ci_commands(ci)
    for command, parsed in parsed_commands.items():
        if parsed not in ci_commands:
            failures.append(f"mission validation command is not an executable CI step: {command}")
    return failures


def required_command(specification: str) -> str:
    """Expand historical script specifications into exact contract commands."""

    if specification.startswith(("python3 ", "pytest ", "ruff ")):
        return specification
    return f"python3 scripts/{specification}"


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
    semantics = contract.get("claim_boundary_semantics", {})
    if semantics.get("current_field") != "publication_claim_boundary" or semantics.get(
        "historical_field"
    ) != "historical_claim_ledger":
        failures.append("current and historical claim authorities are not explicit")
    if not str(contract.get("historical_claim_ledger_notice", "")).startswith(
        "NONCURRENT PROVENANCE ONLY"
    ):
        failures.append("historical claim ledger lacks a fail-closed noncurrent notice")
    correction = contract.get("active_gate_correction", {})
    if correction.get("supersedes_stale_historical_claims") is not True:
        failures.append("active-gate correction does not supersede stale historical claims")
    publication_claim = contract.get("publication_claim_boundary", "")
    if "TELOS, Sentinel, Inbar, and Odeya" not in publication_claim or (
        "separate from Aweb" not in publication_claim
    ):
        failures.append("publication claim boundary must state the project boundary")

    active_gate = contract.get("active_gate")
    failures.extend(validate_gate_bindings(contract, continuity, handoff))
    failures.extend(validate_iter207_recovery_state(contract))
    failures.extend(validate_iter208_correction_state(contract))
    failures.extend(validate_iter209_recovery_state(contract))
    failures.extend(validate_iter210_recovery_state(contract))
    failures.extend(validate_iter211_materialization_state(contract))

    phases = [phase.get("phase") for phase in contract.get("loop", [])]
    if phases != REQUIRED_PHASES:
        failures.append(f"mission loop phases mismatch: {phases}")

    failures.extend(validate_current_validation(contract, ci))
    current_validation = contract.get("current_validation", [])
    exact_validation_commands = (
        set(current_validation)
        if isinstance(current_validation, list)
        and all(isinstance(command, str) for command in current_validation)
        else set()
    )

    for specification in [
        "python3 -m compileall telos scripts tests",
        "validate_mission_loop.py",
        "validate_supply_chain.py",
        "validate_detector_methodology_correction.py",
        "validate_iter200_corrected_result.py",
        "build_iter200_solve_targets.py --check",
        "build_iter202_solve_targets.py --check",
        "audit_iter202_sample_overlap.py --check",
        "build_iter202_image_lock.py --check",
        "build_iter203_safety_recovery.py --check",
        "build_iter203_runtime_manifest.py --check",
        "validate_iter203_publication_safety.py --check",
        "validate_iter203_infrastructure_null.py",
        "validate_iter204_pre_dispatch_null.py",
        "validate_iter205_pre_dispatch_null.py",
        "audit_iter207_claim_integrity.py --check",
        "validate_iter206_pre_publication_null.py",
        "build_iter207_runtime_manifest.py --check",
        "validate_iter207_publication_safety.py --check",
        "validate_iter207_runtime_recovery.py",
        "validate_iter208_post_seal_forensic_correction.py",
        "build_iter209_receipt.py --check",
        "validate_iter209_publication_ci_recovery.py",
        "build_iter210_receipt.py --check",
        "validate_iter210_pr_synthetic_merge_recovery.py",
        "build_iter211_tcp1_packet.py --check",
        "build_iter211_receipt.py --check",
        "validate_iter211_tcp1_materialization_preflight.py",
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
        "validate_receipts.py experiments/iter83_benchmark_facing_protocol_effect_execution_pilot/proof",
        "audit_benchmark_facing_protocol_effect_execution_pilot.py",
        "validate_receipts.py experiments/iter84_benchmark_facing_null_signal_adjudication/proof",
        "audit_benchmark_facing_null_signal_adjudication.py",
        "validate_receipts.py experiments/iter85_discriminating_task_metric_redesign/proof",
        "audit_discriminating_task_metric_redesign.py",
        "validate_receipts.py experiments/iter86_discriminating_metric_backtest_on_committed_artifacts/proof",
        "audit_discriminating_metric_backtest_on_committed_artifacts.py",
        "validate_receipts.py experiments/iter87_benchmark_facing_discriminating_metric_execution_pilot/proof",
        "audit_benchmark_facing_discriminating_metric_execution_pilot.py",
        "validate_receipts.py experiments/iter88_external_benchmark_readiness_adjudication_after_discriminating_pilot/proof",
        "audit_external_benchmark_readiness_adjudication_after_discriminating_pilot.py",
        "validate_receipts.py experiments/iter89_same_slice_discriminating_metric_stability_replication/proof",
        "audit_same_slice_discriminating_metric_stability_replication.py",
        "validate_receipts.py experiments/iter90_stability_replication_adjudication_after_same_slice_run/proof",
        "audit_stability_replication_adjudication_after_same_slice_run.py",
        "validate_receipts.py experiments/iter91_empirical_validation_suite_design_for_completion_verification/proof",
        "audit_empirical_validation_suite_design_for_completion_verification.py",
        "validate_receipts.py experiments/iter92_empirical_validation_fixture_materialization_for_completion_verification/proof",
        "audit_empirical_validation_fixture_materialization_for_completion_verification.py",
        "validate_receipts.py experiments/iter93_deterministic_strategy_execution_on_materialized_fixtures/proof",
        "audit_deterministic_strategy_execution_on_materialized_fixtures.py",
        "validate_receipts.py experiments/iter94_provider_llm_judge_execution_on_materialized_fixtures/proof",
        "audit_provider_llm_judge_execution_on_materialized_fixtures.py",
        "validate_receipts.py experiments/iter95_provider_llm_judge_prompt_budget_recovery_after_block/proof",
        "audit_provider_llm_judge_prompt_budget_recovery_after_block.py",
        "validate_receipts.py experiments/iter96_provider_llm_judge_bounded_retry_after_prompt_budget_recovery/proof",
        "audit_provider_llm_judge_bounded_retry_after_prompt_budget_recovery.py",
        "validate_receipts.py experiments/iter97_five_strategy_completion_verification_adjudication_after_llm_judge/proof",
        "audit_five_strategy_completion_verification_adjudication_after_llm_judge.py",
        "validate_receipts.py experiments/iter98_external_verifier_telos_differential_suite_design_after_adjudication/proof",
        "audit_external_verifier_telos_differential_suite_design_after_adjudication.py",
        "validate_receipts.py experiments/iter99_external_verifier_telos_differential_fixture_materialization_after_design/proof",
        "audit_external_verifier_telos_differential_fixture_materialization_after_design.py",
        "validate_receipts.py experiments/iter100_deterministic_strategy_execution_on_differential_fixtures_after_materialization/proof",
        "audit_deterministic_strategy_execution_on_differential_fixtures_after_materialization.py",
        "validate_receipts.py experiments/iter101_provider_llm_judge_execution_on_differential_fixtures_after_deterministic/proof",
        "audit_provider_llm_judge_execution_on_differential_fixtures_after_deterministic.py",
        "validate_receipts.py experiments/iter102_provider_llm_judge_differential_retry_recovery_after_block/proof",
        "audit_provider_llm_judge_differential_retry_recovery_after_block.py",
        "validate_receipts.py experiments/iter103_differential_provider_llm_judge_full_retry_after_block_recovery/proof",
        "audit_differential_provider_llm_judge_full_retry_after_block_recovery.py",
        "validate_receipts.py experiments/iter104_five_strategy_differential_adjudication_after_recovered_llm_judge/proof",
        "audit_five_strategy_differential_adjudication_after_recovered_llm_judge.py",
        "validate_receipts.py experiments/iter105_external_benchmark_pilot_design_after_differential_adjudication/proof",
        "audit_external_benchmark_pilot_design_after_differential_adjudication.py",
        "validate_receipts.py experiments/iter106_external_benchmark_pilot_materialization_after_design/proof",
        "audit_external_benchmark_pilot_materialization_after_design.py",
        "validate_receipts.py experiments/iter107_external_benchmark_pilot_execution_after_materialization/proof",
        "audit_external_benchmark_pilot_execution_after_materialization.py",
        "validate_handoff.py",
    ]:
        command = required_command(specification)
        if command not in exact_validation_commands:
            failures.append(f"mission validation command missing from contract: {command}")

    for required in [
        "../mission/loop.json",
        "Repository boundary: Telos is a standalone repository",
        "Claim not allowed now: an uncommitted private runtime is part of the standing evidence chain.",
        "Refinement is allowed only after evidence identifies a concrete gap.",
    ]:
        if required not in doc:
            failures.append(f"mission loop doc missing required text: {required}")

    if failures:
        print("MISSION LOOP GUARD FAILED:")
        for failure in failures:
            print(" -", failure)
        return 1

    publication_gate = contract.get("active_publication_gate")
    print(
        "mission loop guard: "
        f"sealed runtime gate={active_gate} active publication gate={publication_gate} "
        f"phases={len(REQUIRED_PHASES)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
