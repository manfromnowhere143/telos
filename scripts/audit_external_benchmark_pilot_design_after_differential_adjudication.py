#!/usr/bin/env python3
"""Audit iter105 external benchmark pilot design artifacts."""

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
EXPERIMENT = Path("experiments/iter105_external_benchmark_pilot_design_after_differential_adjudication")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
PREREQ = PROOF / "iter104_prerequisite_validation.json"
TASK_SOURCE = PROOF / "pilot_task_source_selection.json"
COMPARISON = PROOF / "baseline_telos_comparison_design.json"
BUDGET = PROOF / "sample_size_budget_rationale.json"
STOPPING = PROOF / "stopping_null_result_rules.json"
ARTIFACTS = PROOF / "artifact_receipt_requirements.json"
DECISION = PROOF / "next_step_decision.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary.json"
REDACTION = PROOF / "redaction_scan.json"
RECEIPT = (
    PROOF
    / "valid"
    / "receipt_external_benchmark_pilot_design_after_differential_adjudication.json"
)
NEXT_GATE = Path("experiments/iter106_external_benchmark_pilot_materialization_after_design/HYPOTHESIS.md")
ITER104_PROOF = Path(
    "experiments/iter104_five_strategy_differential_adjudication_after_recovered_llm_judge/proof"
)
ITER104_SUMMARY = ITER104_PROOF / "run_summary.json"
ITER104_COMPARISON = ITER104_PROOF / "strategy_comparison.json"
ITER104_ADVERSE = ITER104_PROOF / "adverse_result_register.json"
ITER104_RECEIPT = (
    ITER104_PROOF
    / "valid"
    / "receipt_five_strategy_differential_adjudication_after_recovered_llm_judge.json"
)
ZERO = Decimal("0.00000000")
FUTURE_SPEND_CEILING = Decimal("10.00000000")
PLANNED_PACKET_COUNT = 20
PLANNED_FALSE_PACKET_COUNT = 10
PLANNED_LEGITIMATE_PACKET_COUNT = 10
PLANNED_PROVIDER_CALL_CEILING = 30
STRATEGY_IDS = [
    "agent_self_report",
    "execution_tests_only",
    "llm_judge",
    "external_verifier",
    "complete_telos_protocol",
]
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
    re.compile(r"external_benchmark_result_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"leaderboard_or_swebench_result_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"model_superiority_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"state_of_the_art_result_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"all_strategy_superiority_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"benchmark/model/SOTA claim:\s*`true`", re.IGNORECASE),
    re.compile(r"\bSOTA achieved\b", re.IGNORECASE),
    re.compile(r"\bstate-of-the-art achieved\b", re.IGNORECASE),
    re.compile(r"\bmodel superiority achieved\b", re.IGNORECASE),
    re.compile(r"\bbenchmark achieved\b", re.IGNORECASE),
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
        TASK_SOURCE,
        COMPARISON,
        BUDGET,
        STOPPING,
        ARTIFACTS,
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
        "summary": "telos.external_benchmark_pilot_design.summary.v1",
        "prereq": "telos.external_benchmark_pilot_design.iter104_validation.v1",
        "task_source": "telos.external_benchmark_pilot_design.task_source_selection.v1",
        "comparison": "telos.external_benchmark_pilot_design.comparison_design.v1",
        "budget": "telos.external_benchmark_pilot_design.sample_size_budget.v1",
        "stopping": "telos.external_benchmark_pilot_design.stopping_rules.v1",
        "artifacts": "telos.external_benchmark_pilot_design.artifact_requirements.v1",
        "decision": "telos.external_benchmark_pilot_design.next_step_decision.v1",
        "boundary": "telos.external_benchmark_pilot_design.claim_boundary.v1",
        "redaction": "telos.external_benchmark_pilot_design.redaction_scan.v1",
    }
    for name, schema in expected.items():
        if packets[name].get("schema_version") != schema:
            failures.append(f"{name} schema mismatch: {packets[name].get('schema_version')}")
        if packets[name].get("experiment_id") != EXPERIMENT.name:
            failures.append(f"{name} experiment id mismatch")


def audit_prereq_and_zero_spend(
    packets: dict[str, dict[str, Any]], failures: list[str]
) -> None:
    summary = packets["summary"]
    prereq = packets["prereq"]
    iter104 = load_json(ITER104_SUMMARY)
    if summary.get("status") != "pass" or summary.get("clean_pass") is not True:
        failures.append("iter105 summary must be a clean pass")
    if summary.get("blocked_result") is not False or summary.get("quality_failure") is not False:
        failures.append("summary blocked/quality flags must be false")
    if summary.get("blockers") != [] or summary.get("failures") != []:
        failures.append("pass summary must not include blockers/failures")
    if prereq.get("clean_prerequisites") is not True:
        failures.append("iter104 prerequisite validation must be clean")
    if prereq.get("iter104_status") != "pass" or iter104.get("status") != "pass":
        failures.append("iter104 source status must be pass")
    if prereq.get("iter104_balanced_fixture_pass_strategy_ids") != ["complete_telos_protocol"]:
        failures.append("iter104 balanced pass evidence mismatch")
    if prereq.get("iter104_complete_telos_specific_detection_count") != 4:
        failures.append("iter104 detection count mismatch")
    if prereq.get("iter104_complete_telos_specific_detection_rate_delta") != "0.50000000":
        failures.append("iter104 detection delta mismatch")
    if prereq.get("iter104_benchmark_result_claimed") is not False:
        failures.append("iter104 must not claim benchmark result")
    expected_hashes = {
        "iter104_summary": sha256(ITER104_SUMMARY),
        "iter104_comparison": sha256(ITER104_COMPARISON),
        "iter104_adverse": sha256(ITER104_ADVERSE),
        "iter104_receipt": sha256(ITER104_RECEIPT),
    }
    if prereq.get("source_hashes") != expected_hashes:
        failures.append("iter104 source hashes mismatch")
    zero_packets = ["summary", "task_source", "budget"]
    for packet_name in zero_packets:
        packet = packets[packet_name]
        calls = packet.get("provider_api_calls", packet.get("provider_calls_in_this_gate", 0))
        spend = packet.get(
            "provider_cost_usd",
            packet.get("provider_spend_in_this_gate_usd", "0.00000000"),
        )
        task_execution = packet.get(
            "benchmark_task_execution_in_this_gate",
            packet.get("task_execution_in_this_gate", 0),
        )
        if calls != 0:
            failures.append(f"{packet_name} provider calls must be zero")
        if decimal_value(spend) != ZERO:
            failures.append(f"{packet_name} provider spend must be zero")
        if task_execution != 0:
            failures.append(f"{packet_name} task execution must be zero")
    for key in ["strategy_execution_in_this_gate", "row_execution_in_this_gate"]:
        if summary.get(key) != 0:
            failures.append(f"{key} must be zero")
    for key in [
        "gpu_used",
        "cloud_runner_started",
        "sentinel_named_resources_modified",
        "production_or_live_domain_changed",
    ]:
        if summary.get(key) is not False:
            failures.append(f"{key} must be false")


def audit_design(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = packets["summary"]
    task_source = packets["task_source"]
    comparison = packets["comparison"]
    budget = packets["budget"]
    stopping = packets["stopping"]
    artifacts = packets["artifacts"]
    decision = packets["decision"]
    if task_source.get("selected_pilot_source_family") != "public_software_agent_tasks_with_frozen_artifacts":
        failures.append("pilot source family mismatch")
    if task_source.get("planned_packet_count") != PLANNED_PACKET_COUNT:
        failures.append("task source planned packet count mismatch")
    if task_source.get("planned_false_completion_packet_count") != PLANNED_FALSE_PACKET_COUNT:
        failures.append("task source false packet count mismatch")
    if task_source.get("planned_legitimate_control_packet_count") != PLANNED_LEGITIMATE_PACKET_COUNT:
        failures.append("task source legitimate packet count mismatch")
    for required in [
        "public task statement and repository commit are immutable",
        "artifacts can be frozen with hashes and private labels excluded from strategy inputs",
    ]:
        if required not in task_source.get("selection_criteria", []):
            failures.append(f"missing selection criterion: {required}")
    for required in [
        "requires private data, secrets, account state, payments, or live mutation",
        "cannot publish enough raw evidence for hostile review",
    ]:
        if required not in task_source.get("exclusion_criteria", []):
            failures.append(f"missing exclusion criterion: {required}")
    if comparison.get("strategy_ids") != STRATEGY_IDS:
        failures.append("strategy list mismatch")
    if comparison.get("paired_design") is not True:
        failures.append("comparison must be paired")
    if comparison.get("same_public_artifacts_for_all_strategies") is not True:
        failures.append("public artifacts must be identical for all strategies")
    if comparison.get("private_labels_excluded_from_strategy_inputs") is not True:
        failures.append("private labels must be excluded from strategy inputs")
    if comparison.get("primary_endpoint") != "false_completion_acceptance_rate":
        failures.append("primary endpoint mismatch")
    if comparison.get("guardrail_endpoint") != "legitimate_completion_preservation_rate":
        failures.append("guardrail endpoint mismatch")
    if comparison.get("candidate_strategy") != "complete_telos_protocol":
        failures.append("candidate strategy mismatch")
    if comparison.get("benchmark_result_claimed") is not False:
        failures.append("comparison must not claim benchmark result")
    if budget.get("planned_packet_count") != PLANNED_PACKET_COUNT:
        failures.append("budget planned packet count mismatch")
    if budget.get("future_paid_pilot_provider_call_ceiling") != PLANNED_PROVIDER_CALL_CEILING:
        failures.append("future provider call ceiling mismatch")
    if decimal_value(budget.get("future_paid_pilot_spend_ceiling_usd")) != FUTURE_SPEND_CEILING:
        failures.append("future spend ceiling mismatch")
    if budget.get("future_execution_requires_operator_budget_confirmation") is not True:
        failures.append("future execution must require budget confirmation")
    if "private labels leak into any strategy input" not in stopping.get(
        "must_stop_and_publish_null_or_blocker_if", []
    ):
        failures.append("stopping rules must include label leakage")
    if "complete Telos ties external verifier" not in stopping.get("null_results_to_preserve", []):
        failures.append("null results must preserve Telos/external-verifier tie")
    if artifacts.get("hash_every_public_artifact") is not True:
        failures.append("artifact requirements must hash every public artifact")
    if artifacts.get("labels_excluded_from_strategy_inputs") is not True:
        failures.append("artifact requirements must exclude labels")
    if artifacts.get("publish_failed_hypotheses") is not True:
        failures.append("artifact requirements must publish failed hypotheses")
    if decision.get("decision") != "materialize_external_benchmark_pilot_packets":
        failures.append("next-step decision mismatch")
    if decision.get("paid_execution_rejected_for_this_gate") is not True:
        failures.append("decision must reject paid execution for this gate")
    if summary.get("next_gate") != str(NEXT_GATE):
        failures.append("summary next gate mismatch")
    if summary.get("external_benchmark_pilot_design_claimed") is not True:
        failures.append("summary must claim only pilot design")


def audit_claims_receipt_hashes_and_text(
    packets: dict[str, dict[str, Any]], failures: list[str]
) -> None:
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
    if boundary.get("external_benchmark_pilot_design_claimed") is not True:
        failures.append("pilot design boundary claim missing")
    for key in [
        "external_benchmark_result_claimed",
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "all_strategy_superiority_claimed",
    ]:
        if summary.get(key) is not False:
            failures.append(f"summary claim boundary not false: {key}")
        if boundary.get(key) is not False:
            failures.append(f"claim boundary not false: {key}")
    if redaction.get("passed") is not True or redaction.get("findings") != []:
        failures.append("redaction scan failed")
    if summary.get("redaction_scan_passed") is not True or summary.get("redaction_findings") != []:
        failures.append("summary redaction fields failed")
    if not NEXT_GATE.exists():
        failures.append("next gate is missing")
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
        "external benchmark pilot protocol was designed",
        "benchmark/model/SOTA claim: `false`",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "did not execute benchmark tasks",
        "one more zero-spend materialization gate",
        "No benchmark, model-superiority, production/live-domain",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "external benchmark pilot design: pass",
        "planned_packet_count=20",
        "future_paid_pilot_spend_ceiling_usd=10.00000000",
        "provider_api_calls=0",
        "benchmark_model_sota_claimed=false",
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
            "task_source": load_json(TASK_SOURCE),
            "comparison": load_json(COMPARISON),
            "budget": load_json(BUDGET),
            "stopping": load_json(STOPPING),
            "artifacts": load_json(ARTIFACTS),
            "decision": load_json(DECISION),
            "boundary": load_json(CLAIM_BOUNDARY),
            "redaction": load_json(REDACTION),
        }
        audit_schemas(packets, failures)
        audit_prereq_and_zero_spend(packets, failures)
        audit_design(packets, failures)
        audit_claims_receipt_hashes_and_text(packets, failures)
    if failures:
        print("iter105 external benchmark pilot design audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    summary = load_json(SUMMARY)
    print("iter105 external benchmark pilot design audit: pass")
    print(f"planned_packet_count={summary['planned_packet_count']}")
    print(
        "future_paid_pilot_provider_call_ceiling="
        f"{summary['future_paid_pilot_provider_call_ceiling']}"
    )
    print(
        "future_paid_pilot_spend_ceiling_usd="
        f"{summary['future_paid_pilot_spend_ceiling_usd']}"
    )
    print(f"next_gate={summary['next_gate']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
