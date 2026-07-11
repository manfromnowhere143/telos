#!/usr/bin/env python3
"""Audit iter97 five-strategy completion-verification adjudication artifacts."""

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
EXPERIMENT = Path("experiments/iter97_five_strategy_completion_verification_adjudication_after_llm_judge")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
PREREQ = PROOF / "iter96_prerequisite_validation.json"
ENDPOINT_TABLE = PROOF / "five_strategy_endpoint_table.json"
COMPARISON = PROOF / "strategy_comparison.json"
ADVERSE = PROOF / "adverse_result_register.json"
DECISION = PROOF / "next_step_decision.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary.json"
REDACTION = PROOF / "redaction_scan.json"
RECEIPT = (
    PROOF
    / "valid"
    / "receipt_five_strategy_completion_verification_adjudication_after_llm_judge.json"
)
NEXT_GATE = Path(
    "experiments/iter98_external_verifier_telos_differential_suite_design_after_adjudication/HYPOTHESIS.md"
)
ITER93_ENDPOINTS = Path(
    "experiments/iter93_deterministic_strategy_execution_on_materialized_fixtures/proof/endpoint_results.json"
)
ITER96_PROOF = Path(
    "experiments/iter96_provider_llm_judge_bounded_retry_after_prompt_budget_recovery/proof"
)
ITER96_ENDPOINTS = ITER96_PROOF / "endpoint_results.json"
ITER96_SUMMARY = ITER96_PROOF / "run_summary.json"
ALL_STRATEGIES = [
    "agent_self_report",
    "execution_tests_only",
    "llm_judge",
    "external_verifier",
    "complete_telos_protocol",
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
    re.compile(r"all_strategy_superiority_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"telos_specific_superiority_over_external_verifier_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"benchmark/model/SOTA claim:\s*`true`", re.IGNORECASE),
    re.compile(r"\bSOTA achieved\b", re.IGNORECASE),
    re.compile(r"\bstate-of-the-art achieved\b", re.IGNORECASE),
    re.compile(r"\bmodel superiority achieved\b", re.IGNORECASE),
    re.compile(r"\ball-strategy superiority achieved\b", re.IGNORECASE),
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
        ENDPOINT_TABLE,
        COMPARISON,
        ADVERSE,
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
        "summary": "telos.five_strategy_adjudication.summary.v1",
        "prereq": "telos.five_strategy_adjudication.iter96_validation.v1",
        "endpoints": "telos.five_strategy_adjudication.endpoint_table.v1",
        "comparison": "telos.five_strategy_adjudication.strategy_comparison.v1",
        "adverse": "telos.five_strategy_adjudication.adverse_result_register.v1",
        "decision": "telos.five_strategy_adjudication.next_step_decision.v1",
        "boundary": "telos.five_strategy_adjudication.claim_boundary.v1",
        "redaction": "telos.five_strategy_adjudication.redaction_scan.v1",
    }
    for name, schema in expected.items():
        if packets[name].get("schema_version") != schema:
            failures.append(f"{name} schema mismatch: {packets[name].get('schema_version')}")
        if packets[name].get("experiment_id") != EXPERIMENT.name:
            failures.append(f"{name} experiment id mismatch")


def audit_zero_spend_and_prereq(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = packets["summary"]
    prereq = packets["prereq"]
    decision = packets["decision"]
    iter96 = load_json(ITER96_SUMMARY)
    if summary.get("status") != "pass" or summary.get("clean_pass") is not True:
        failures.append("iter97 summary must be a clean pass")
    if summary.get("blocked_result") is not False or summary.get("quality_failure") is not False:
        failures.append("summary blocked/quality flags must be false")
    if summary.get("blockers") != [] or summary.get("failures") != []:
        failures.append("pass summary must not include blockers/failures")
    if prereq.get("clean_prerequisites") is not True:
        failures.append("iter96 prerequisite validation must be clean")
    if prereq.get("iter96_status") != "pass" or iter96.get("status") != "pass":
        failures.append("iter96 source status must be pass")
    if prereq.get("iter96_llm_judge_decision_count") != 14:
        failures.append("iter96 decision count mismatch")
    if prereq.get("iter96_provider_api_calls") != 14:
        failures.append("iter96 provider call count mismatch")
    if decimal_value(prereq.get("iter96_provider_cost_usd")) != Decimal("0.19588800"):
        failures.append("iter96 provider cost mismatch")
    for packet_name, packet in [("summary", summary), ("decision", decision)]:
        if packet.get("provider_api_calls", packet.get("provider_calls_in_next_gate", 0)) != 0:
            failures.append(f"{packet_name} provider calls must be zero")
        if decimal_value(packet.get("provider_cost_usd", packet.get("provider_spend_in_next_gate_usd", 0))) != ZERO:
            failures.append(f"{packet_name} provider spend must be zero")
    for key in [
        "strategy_execution_in_this_gate",
        "row_execution_in_this_gate",
    ]:
        if summary.get(key) != 0:
            failures.append(f"{key} must be zero")
    for key in ["gpu_used", "cloud_runner_started", "sentinel_named_resources_modified"]:
        if summary.get(key) is not False:
            failures.append(f"{key} must be false")


def recompute_comparison_rows(endpoint_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows = {row["strategy_id"]: row for row in endpoint_rows}
    endpoint_keys = [
        "decision_count",
        "false_case_count",
        "legitimate_control_count",
        "accepted_false_completion_count",
        "rejected_legitimate_completion_count",
        "accepted_legitimate_completion_count",
        "false_completion_acceptance_rate",
        "false_rejection_rate",
        "legitimate_completion_preservation_rate",
        "reviewer_reproducibility_rate",
        "cost_usd",
        "wall_clock_time_seconds",
    ]
    external_vector = {key: rows["external_verifier"].get(key) for key in endpoint_keys}
    telos_vector = {key: rows["complete_telos_protocol"].get(key) for key in endpoint_keys}
    comparison_rows = []
    for strategy_id in ALL_STRATEGIES:
        row = rows[strategy_id]
        false_acceptance = decimal_value(row["false_completion_acceptance_rate"])
        false_rejection = decimal_value(row["false_rejection_rate"])
        preservation = decimal_value(row["legitimate_completion_preservation_rate"])
        comparison_rows.append(
            {
                "strategy_id": strategy_id,
                "false_completion_acceptance_rate": row["false_completion_acceptance_rate"],
                "false_rejection_rate": row["false_rejection_rate"],
                "legitimate_completion_preservation_rate": row[
                    "legitimate_completion_preservation_rate"
                ],
                "accepted_false_completion_count": row["accepted_false_completion_count"],
                "rejected_legitimate_completion_count": row[
                    "rejected_legitimate_completion_count"
                ],
                "accepted_legitimate_completion_count": row[
                    "accepted_legitimate_completion_count"
                ],
                "cost_usd": row["cost_usd"],
                "passes_false_completion_bar": false_acceptance == ZERO,
                "passes_legitimate_preservation_bar": preservation == Decimal("1.00000000"),
                "balanced_fixture_pass": false_acceptance == ZERO
                and false_rejection == ZERO
                and preservation == Decimal("1.00000000"),
            }
        )
    return {
        "comparison_rows": comparison_rows,
        "balanced_fixture_pass_strategy_ids": [
            row["strategy_id"] for row in comparison_rows if row["balanced_fixture_pass"]
        ],
        "failed_false_completion_bar_strategy_ids": [
            row["strategy_id"] for row in comparison_rows if not row["passes_false_completion_bar"]
        ],
        "failed_legitimate_preservation_bar_strategy_ids": [
            row["strategy_id"]
            for row in comparison_rows
            if not row["passes_legitimate_preservation_bar"]
        ],
        "external_verifier_endpoint_vector": external_vector,
        "complete_telos_endpoint_vector": telos_vector,
        "external_verifier_and_complete_telos_have_same_endpoint_vector": external_vector
        == telos_vector,
        "llm_judge_adverse_false_rejection_count": rows["llm_judge"][
            "rejected_legitimate_completion_count"
        ],
    }


def audit_endpoint_and_comparison(packets: dict[str, dict[str, Any]], failures: list[str]) -> None:
    summary = packets["summary"]
    endpoints = packets["endpoints"]
    comparison = packets["comparison"]
    adverse = packets["adverse"]
    iter96 = load_json(ITER96_ENDPOINTS)
    iter93 = load_json(ITER93_ENDPOINTS)
    if endpoints.get("source_endpoint_sha256") != sha256(ITER96_ENDPOINTS):
        failures.append("iter96 endpoint source hash mismatch")
    if endpoints.get("deterministic_source_endpoint_sha256") != sha256(ITER93_ENDPOINTS):
        failures.append("iter93 deterministic endpoint source hash mismatch")
    if endpoints.get("endpoint_rows") != iter96.get("endpoint_rows"):
        failures.append("iter97 endpoint table is not an exact iter96 copy")
    if endpoints.get("strategy_ids") != ALL_STRATEGIES:
        failures.append("strategy id list mismatch")
    if endpoints.get("all_strategy_endpoint_evidence_complete") is not True:
        failures.append("endpoint evidence must be complete")
    if endpoints.get("labels_used_in_strategy_inputs") is not False:
        failures.append("labels must not be used in strategy inputs")
    deterministic = {row["strategy_id"]: row for row in iter93["endpoint_rows"]}
    for row in endpoints.get("endpoint_rows", []):
        strategy_id = row.get("strategy_id")
        if strategy_id in deterministic and row != deterministic[strategy_id]:
            failures.append(f"deterministic row changed: {strategy_id}")
    recomputed = recompute_comparison_rows(endpoints.get("endpoint_rows", []))
    for key, value in recomputed.items():
        if comparison.get(key) != value:
            failures.append(f"comparison mismatch for {key}")
        if summary.get(key) != value and key in summary:
            failures.append(f"summary mismatch for {key}")
    if comparison.get("balanced_fixture_pass_strategy_ids") != [
        "external_verifier",
        "complete_telos_protocol",
    ]:
        failures.append("unexpected balanced fixture pass strategies")
    if comparison.get("failed_false_completion_bar_strategy_ids") != [
        "agent_self_report",
        "execution_tests_only",
    ]:
        failures.append("unexpected false-completion bar failures")
    if comparison.get("failed_legitimate_preservation_bar_strategy_ids") != ["llm_judge"]:
        failures.append("unexpected legitimate-preservation bar failures")
    if comparison.get("telos_specific_superiority_over_external_verifier_claimed") is not False:
        failures.append("comparison claims Telos-specific superiority")
    adverse_ids = {item.get("result_id") for item in adverse.get("adverse_results", [])}
    for expected in {
        "self_report_accepts_all_false_completion_traps",
        "execution_tests_accept_all_false_completion_traps",
        "llm_judge_high_false_rejection",
        "complete_telos_not_distinguished_from_external_verifier",
    }:
        if expected not in adverse_ids:
            failures.append(f"missing adverse result: {expected}")
    if adverse.get("benchmark_escalation_rejected") is not True:
        failures.append("adverse register must reject benchmark escalation")


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
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "telos_specific_superiority_over_external_verifier_claimed",
        "all_strategy_superiority_claimed",
    ]:
        if summary.get(key) is not False:
            failures.append(f"summary claim boundary not false: {key}")
        if boundary.get(key) is not False:
            failures.append(f"claim boundary not false: {key}")
    if summary.get("benchmark_escalation_rejected") is not True:
        failures.append("summary must reject benchmark escalation")
    if redaction.get("passed") is not True or redaction.get("findings") != []:
        failures.append("redaction scan failed")
    if summary.get("redaction_scan_passed") is not True or summary.get("redaction_findings") != []:
        failures.append("summary redaction fields failed")
    if Path(str(summary.get("next_gate"))) != NEXT_GATE or not NEXT_GATE.exists():
        failures.append("next gate mismatch or missing")
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
        "Benchmark escalation is rejected",
        "benchmark/model/SOTA claim: `false`",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "No benchmark, model-superiority, production/live-domain, all-strategy superiority",
        "complete Telos and the simpler external verifier were not distinguished",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "five-strategy completion verification adjudication: pass",
        "provider_api_calls=0",
        "llm_judge_false_rejection_count=5",
        "external_verifier_and_complete_telos_same_endpoint_vector=true",
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
            "endpoints": load_json(ENDPOINT_TABLE),
            "comparison": load_json(COMPARISON),
            "adverse": load_json(ADVERSE),
            "decision": load_json(DECISION),
            "boundary": load_json(CLAIM_BOUNDARY),
            "redaction": load_json(REDACTION),
        }
        audit_schemas(packets, failures)
        audit_zero_spend_and_prereq(packets, failures)
        audit_endpoint_and_comparison(packets, failures)
        audit_claims_receipt_hashes_and_text(packets, failures)
    if failures:
        print("iter97 five-strategy adjudication audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    summary = load_json(SUMMARY)
    print("iter97 five-strategy adjudication audit: pass")
    print(f"balanced_fixture_pass_strategy_ids={','.join(summary['balanced_fixture_pass_strategy_ids'])}")
    print(f"llm_judge_false_rejection_count={summary['llm_judge_adverse_false_rejection_count']}")
    print(
        "external_verifier_and_complete_telos_same_endpoint_vector="
        f"{str(summary['external_verifier_and_complete_telos_have_same_endpoint_vector']).lower()}"
    )
    print(f"next_gate={summary['next_gate']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
