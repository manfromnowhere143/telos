#!/usr/bin/env python3
"""Audit iter98 external-verifier/Telos differential suite design artifacts."""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


ROOT = Path.cwd()
EXPERIMENT = Path("experiments/iter98_external_verifier_telos_differential_suite_design_after_adjudication")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
PREREQ = PROOF / "iter97_prerequisite_validation.json"
TARGET_MATRIX = PROOF / "differential_target_matrix.json"
FIXTURE_RULES = PROOF / "fixture_design_rules.json"
ENDPOINTS = PROOF / "endpoint_sample_size_rationale.json"
DECISION = PROOF / "next_step_decision.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary.json"
REDACTION = PROOF / "redaction_scan.json"
RECEIPT = (
    PROOF
    / "valid"
    / "receipt_external_verifier_telos_differential_suite_design_after_adjudication.json"
)
NEXT_GATE = Path(
    "experiments/iter99_external_verifier_telos_differential_fixture_materialization_after_design/HYPOTHESIS.md"
)
ITER97_PROOF = Path(
    "experiments/iter97_five_strategy_completion_verification_adjudication_after_llm_judge/proof"
)
ITER97_SUMMARY = ITER97_PROOF / "run_summary.json"
ITER97_COMPARISON = ITER97_PROOF / "strategy_comparison.json"
ITER97_ADVERSE = ITER97_PROOF / "adverse_result_register.json"
ITER97_RECEIPT = (
    ITER97_PROOF / "valid" / "receipt_five_strategy_completion_verification_adjudication_after_llm_judge.json"
)
TARGET_IDS = [
    "stale_receipt_current_artifacts",
    "missing_falsifier_hidden_by_passing_tests",
    "setup_done_not_task_done",
    "contradictory_artifact_packet",
    "schema_valid_semantic_incomplete_receipt",
    "live_domain_flag_without_live_evidence",
    "nondeterministic_result_no_replay",
    "adversarial_receipt_digest_collision_attempt",
]
ENDPOINT_IDS = [
    "false_completion_acceptance_rate",
    "false_rejection_rate",
    "legitimate_completion_preservation_rate",
    "external_verifier_miss_count",
    "complete_telos_specific_detection_count",
    "differential_detection_delta",
    "cost_usd",
    "reviewer_reproducibility_rate",
]
ZERO = Decimal("0.00000000")
TEXT_SUFFIXES = {".json", ".jsonl", ".log", ".txt", ".md", ".yaml", ".yml", ".py"}
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"Bearer\s+(?!\$\{[A-Z0-9_]+\}|\[REDACTED_BEARER_TOKEN\])\S+"),
    re.compile(r"-----BEGIN PRIVATE KEY-----"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com"),
    re.compile(r"telos-vertex-runner"),
    re.compile(r"sunlit-unison-[A-Za-z0-9-]+"),
    re.compile(r"errorId=Ci"),
    re.compile(r'"error_info_id"\s*:\s*"Ci'),
]
FORBIDDEN_CLAIM_PATTERNS = [
    re.compile(r"benchmark_result_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"model_superiority_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"state_of_the_art_result_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"telos_specific_superiority_over_external_verifier_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"external_verifier_telos_differential_result_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"expected_divergence_claimed_as_result[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"benchmark/model/SOTA claim:\s*`true`", re.IGNORECASE),
    re.compile(r"\bSOTA achieved\b", re.IGNORECASE),
    re.compile(r"\bstate-of-the-art achieved\b", re.IGNORECASE),
    re.compile(r"\bmodel superiority achieved\b", re.IGNORECASE),
    re.compile(r"\bTelos-specific superiority achieved\b", re.IGNORECASE),
]


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} root must be an object")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decimal_value(value: object) -> Decimal:
    return Decimal(str(value or 0)).quantize(ZERO)


def text_files(path: Path) -> list[Path]:
    return [
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file() and candidate.suffix in TEXT_SUFFIXES
    ]


def audit_required_files(failures: list[str]) -> None:
    for path in [
        RESULT,
        SUMMARY,
        PREREQ,
        TARGET_MATRIX,
        FIXTURE_RULES,
        ENDPOINTS,
        DECISION,
        CLAIM_BOUNDARY,
        REDACTION,
        PROOF / "command_output.txt",
        PROOF / "review.md",
        PROOF / "learning_record.json",
        RECEIPT,
        NEXT_GATE,
    ]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")


def audit_schemas(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    expected = {
        "summary": "telos.differential_suite_design.summary.v1",
        "prereq": "telos.differential_suite_design.iter97_validation.v1",
        "matrix": "telos.differential_suite_design.target_matrix.v1",
        "rules": "telos.differential_suite_design.fixture_design_rules.v1",
        "endpoints": "telos.differential_suite_design.endpoint_sample_size_rationale.v1",
        "decision": "telos.differential_suite_design.next_step_decision.v1",
        "boundary": "telos.differential_suite_design.claim_boundary.v1",
        "redaction": "telos.differential_suite_design.redaction_scan.v1",
    }
    for name, schema in expected.items():
        if packets[name].get("schema_version") != schema:
            failures.append(f"{name} schema mismatch: {packets[name].get('schema_version')}")
        if packets[name].get("experiment_id") != EXPERIMENT.name:
            failures.append(f"{name} experiment id mismatch")


def audit_zero_spend_and_prereq(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = packets["summary"]
    prereq = packets["prereq"]
    iter97 = load_json(ITER97_SUMMARY)
    if summary.get("status") != "pass" or summary.get("clean_pass") is not True:
        failures.append("iter98 summary must be a clean pass")
    if summary.get("blocked_result") is not False or summary.get("quality_failure") is not False:
        failures.append("summary blocked/quality flags must be false")
    if summary.get("blockers") != [] or summary.get("failures") != []:
        failures.append("pass summary must not include blockers/failures")
    if prereq.get("clean_prerequisites") is not True:
        failures.append("iter97 prerequisites must be clean")
    if prereq.get("iter97_status") != "pass" or iter97.get("status") != "pass":
        failures.append("iter97 source status must be pass")
    if prereq.get("iter97_external_verifier_and_complete_telos_same_endpoint_vector") is not True:
        failures.append("iter97 must preserve external-verifier/Telos tie")
    if prereq.get("iter97_benchmark_escalation_rejected") is not True:
        failures.append("iter97 must reject benchmark escalation")
    expected_hashes = {
        str(ITER97_SUMMARY): sha256(ITER97_SUMMARY),
        str(ITER97_COMPARISON): sha256(ITER97_COMPARISON),
        str(ITER97_ADVERSE): sha256(ITER97_ADVERSE),
        str(ITER97_RECEIPT): sha256(ITER97_RECEIPT),
    }
    for label, expected_hash in expected_hashes.items():
        key = Path(label).stem
        if expected_hash not in prereq.get("source_hashes", {}).values():
            failures.append(f"missing iter97 source hash for {key}")
    for packet_name in ["summary", "rules", "endpoints"]:
        packet = packets[packet_name]
        calls = packet.get("provider_api_calls", packet.get("provider_calls_in_this_gate", 0))
        spend = packet.get(
            "provider_cost_usd",
            packet.get("provider_spend_in_this_gate_usd", "0.00000000"),
        )
        rows = packet.get("row_execution_in_this_gate", 0)
        if calls != 0:
            failures.append(f"{packet_name} provider calls must be zero")
        if decimal_value(spend) != ZERO:
            failures.append(f"{packet_name} provider spend must be zero")
        if rows != 0:
            failures.append(f"{packet_name} row execution must be zero")
    if summary.get("strategy_execution_in_this_gate") != 0:
        failures.append("strategy execution must be zero")
    for key in ["gpu_used", "cloud_runner_started", "sentinel_named_resources_modified"]:
        if summary.get(key) is not False:
            failures.append(f"{key} must be false")


def audit_design(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = packets["summary"]
    matrix = packets["matrix"]
    rules = packets["rules"]
    endpoints = packets["endpoints"]
    decision = packets["decision"]
    rows = matrix.get("differential_target_rows", [])
    if matrix.get("suite_id") != "telos_external_verifier_differential_suite_v0":
        failures.append("suite id mismatch")
    if matrix.get("target_family_count") != 8 or len(rows) != 8:
        failures.append("target family count must be eight")
    if matrix.get("planned_fixture_count") != 16 or summary.get("planned_fixture_count") != 16:
        failures.append("planned fixture count must be sixteen")
    if matrix.get("planned_false_completion_trap_count") != 8:
        failures.append("planned false-completion trap count must be eight")
    if matrix.get("planned_legitimate_control_count") != 8:
        failures.append("planned legitimate control count must be eight")
    if [row.get("target_family_id") for row in rows] != TARGET_IDS:
        failures.append("target family order mismatch")
    for index, row in enumerate(rows, 1):
        if row.get("target_index") != index:
            failures.append(f"target index mismatch for {row.get('target_family_id')}")
        if row.get("planned_false_completion_fixture_id") != f"DIFF-{index:02d}-FALSE":
            failures.append(f"false fixture id mismatch for {row.get('target_family_id')}")
        if row.get("planned_legitimate_control_fixture_id") != f"DIFF-{index:02d}-TRUE":
            failures.append(f"true fixture id mismatch for {row.get('target_family_id')}")
        for required in [
            "external_verifier_blind_spot",
            "complete_telos_required_signal",
            "false_completion_trap_design",
            "legitimate_control_design",
        ]:
            if not row.get(required):
                failures.append(f"{row.get('target_family_id')} missing {required}")
        if row.get("expected_divergence_is_hypothesis_not_result") is not True:
            failures.append(f"{row.get('target_family_id')} must mark divergence as hypothesis")
        if row.get("private_label_visible_to_strategies") is not False:
            failures.append(f"{row.get('target_family_id')} private label visibility mismatch")
        if row.get("identical_public_artifacts_for_all_strategies") is not True:
            failures.append(f"{row.get('target_family_id')} strategy artifact identity mismatch")
    if rules.get("ground_truth_visible_to_strategies") is not False:
        failures.append("ground truth must be hidden from strategies")
    if rules.get("identical_artifacts_for_all_strategies") is not True:
        failures.append("artifacts must be identical for all strategies")
    if "complete_telos_protocol" not in rules.get("strategy_input_rules", {}):
        failures.append("complete Telos strategy input rule missing")
    if endpoints.get("endpoint_ids") != ENDPOINT_IDS:
        failures.append("endpoint list mismatch")
    if endpoints.get("primary_endpoint") != "differential_detection_delta":
        failures.append("primary endpoint mismatch")
    if endpoints.get("guardrail_endpoint") != "legitimate_completion_preservation_rate":
        failures.append("guardrail endpoint mismatch")
    if endpoints.get("benchmark_or_sota_claim_allowed_after_this_gate") is not False:
        failures.append("endpoint packet allows benchmark/SOTA claim")
    if decision.get("decision") != "materialize_external_verifier_telos_differential_fixtures":
        failures.append("next decision mismatch")
    if decision.get("next_gate") != str(NEXT_GATE) or summary.get("next_gate") != str(NEXT_GATE):
        failures.append("next gate mismatch")
    if decision.get("benchmark_escalation_rejected") is not True:
        failures.append("decision must reject benchmark escalation")
    if not NEXT_GATE.exists():
        failures.append("next gate hypothesis missing")


def audit_claims_receipt_hashes_and_text(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = packets["summary"]
    boundary = packets["boundary"]
    redaction = packets["redaction"]
    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt validation failed: {exc}")
        return
    if receipt.status != "pass" or receipt.status != summary.get("status"):
        failures.append("receipt status mismatch")
    for key in [
        "fixture_materialization_claimed",
        "strategy_execution_claimed",
        "external_verifier_telos_differential_result_claimed",
        "telos_specific_superiority_over_external_verifier_claimed",
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
    ]:
        if summary.get(key) is not False:
            failures.append(f"summary claim boundary not false: {key}")
        if boundary.get(key) is not False:
            failures.append(f"claim boundary not false: {key}")
    if summary.get("expected_divergence_claimed_as_result") is not False:
        failures.append("expected divergence must not be claimed as result")
    if redaction.get("passed") is not True or redaction.get("findings") != []:
        failures.append("redaction scan failed")
    if summary.get("redaction_scan_passed") is not True or summary.get("redaction_findings") != []:
        failures.append("summary redaction fields failed")
    for rel_path, expected_hash in summary.get("artifact_hashes", {}).items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"summary hash path missing: {rel_path}")
        elif sha256(path) != expected_hash:
            failures.append(f"summary hash mismatch: {rel_path}")
    result = RESULT.read_text(encoding="utf-8")
    review = (PROOF / "review.md").read_text(encoding="utf-8")
    command_output = (PROOF / "command_output.txt").read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`.",
        "Expected divergence is a hypothesis to test, not a",
        "benchmark/model/SOTA claim: `false`",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "Expected divergence is only a hypothesis",
        "No benchmark, model-superiority, production/live-domain, Telos-specific superiority",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "external-verifier/Telos differential suite design: pass",
        "provider_api_calls=0",
        "planned_fixture_count=16",
        "expected_divergence_claimed_as_result=false",
    ]:
        if required not in command_output:
            failures.append(f"command_output.txt missing required text: {required}")
    for path in text_files(EXPERIMENT):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"secret pattern {pattern.pattern} found in {path}")
                break
        for pattern in FORBIDDEN_CLAIM_PATTERNS:
            if pattern.search(text):
                failures.append(f"unsupported claim-like text in {path}: {pattern.pattern}")
                break


def main() -> int:
    failures: list[str] = []
    audit_required_files(failures)
    if not failures:
        packets = {
            "summary": load_json(SUMMARY),
            "prereq": load_json(PREREQ),
            "matrix": load_json(TARGET_MATRIX),
            "rules": load_json(FIXTURE_RULES),
            "endpoints": load_json(ENDPOINTS),
            "decision": load_json(DECISION),
            "boundary": load_json(CLAIM_BOUNDARY),
            "redaction": load_json(REDACTION),
        }
        audit_schemas(packets, failures)
        audit_zero_spend_and_prereq(packets, failures)
        audit_design(packets, failures)
        audit_claims_receipt_hashes_and_text(packets, failures)
    if failures:
        print("iter98 differential suite design audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    summary = load_json(SUMMARY)
    print("iter98 differential suite design audit: pass")
    print(f"target_family_count={summary['target_family_count']}")
    print(f"planned_fixture_count={summary['planned_fixture_count']}")
    print(f"next_gate={summary['next_gate']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
