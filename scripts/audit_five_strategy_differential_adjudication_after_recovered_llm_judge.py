#!/usr/bin/env python3
"""Audit iter104 five-strategy differential adjudication artifacts."""

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
EXPERIMENT = Path("experiments/iter104_five_strategy_differential_adjudication_after_recovered_llm_judge")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
PREREQ = PROOF / "iter103_prerequisite_validation.json"
ENDPOINT_TABLE = PROOF / "five_strategy_differential_endpoint_table.json"
COMPARISON = PROOF / "strategy_comparison.json"
ADVERSE = PROOF / "adverse_result_register.json"
DECISION = PROOF / "next_step_decision.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary.json"
REDACTION = PROOF / "redaction_scan.json"
RECEIPT = (
    PROOF
    / "valid"
    / "receipt_five_strategy_differential_adjudication_after_recovered_llm_judge.json"
)
NEXT_GATE = Path("experiments/iter105_external_benchmark_pilot_design_after_differential_adjudication/HYPOTHESIS.md")
ITER100_ENDPOINTS = Path(
    "experiments/iter100_deterministic_strategy_execution_on_differential_fixtures_after_materialization/"
    "proof/endpoint_results.json"
)
ITER103_PROOF = Path(
    "experiments/iter103_differential_provider_llm_judge_full_retry_after_block_recovery/proof"
)
ITER103_ENDPOINTS = ITER103_PROOF / "endpoint_results.json"
ITER103_SUMMARY = ITER103_PROOF / "run_summary.json"
ALL_STRATEGIES = [
    "agent_self_report",
    "execution_tests_only",
    "llm_judge",
    "external_verifier",
    "complete_telos_protocol",
]
ZERO = Decimal("0.00000000")
ONE = Decimal("1.00000000")
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


def decimal_string(value: Decimal) -> str:
    return format(value.quantize(ZERO), "f")


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
        "summary": "telos.differential_five_strategy_adjudication.summary.v1",
        "prereq": "telos.differential_five_strategy_adjudication.iter103_validation.v1",
        "endpoints": "telos.differential_five_strategy_adjudication.endpoint_table.v1",
        "comparison": "telos.differential_five_strategy_adjudication.strategy_comparison.v1",
        "adverse": "telos.differential_five_strategy_adjudication.adverse_result_register.v1",
        "decision": "telos.differential_five_strategy_adjudication.next_step_decision.v1",
        "boundary": "telos.differential_five_strategy_adjudication.claim_boundary.v1",
        "redaction": "telos.differential_five_strategy_adjudication.redaction_scan.v1",
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
    iter103 = load_json(ITER103_SUMMARY)
    if summary.get("status") != "pass" or summary.get("clean_pass") is not True:
        failures.append("iter104 summary must be a clean pass")
    if summary.get("blocked_result") is not False or summary.get("quality_failure") is not False:
        failures.append("summary blocked/quality flags must be false")
    if summary.get("blockers") != [] or summary.get("failures") != []:
        failures.append("pass summary must not include blockers/failures")
    if prereq.get("clean_prerequisites") is not True:
        failures.append("iter103 prerequisite validation must be clean")
    if prereq.get("iter103_status") != "pass" or iter103.get("status") != "pass":
        failures.append("iter103 source status must be pass")
    if prereq.get("iter103_llm_judge_decision_count") != 16:
        failures.append("iter103 decision count mismatch")
    if prereq.get("iter103_provider_api_calls") != 16:
        failures.append("iter103 provider call count mismatch")
    if decimal_value(prereq.get("iter103_provider_cost_usd")) != Decimal("0.23633000"):
        failures.append("iter103 provider cost mismatch")
    for packet_name, packet in [("summary", summary), ("decision", decision)]:
        if packet.get("provider_api_calls", packet.get("provider_calls_in_next_gate", 0)) != 0:
            failures.append(f"{packet_name} provider calls must be zero")
        if decimal_value(packet.get("provider_cost_usd", packet.get("provider_spend_in_next_gate_usd", 0))) != ZERO:
            failures.append(f"{packet_name} provider spend must be zero")
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
    if decision.get("immediate_benchmark_claim_rejected") is not True:
        failures.append("next-step decision must reject immediate benchmark claim")
    if decision.get("external_benchmark_pilot_design_selected") is not True:
        failures.append("next-step decision must select external benchmark-pilot design")


def recompute_comparison_rows(endpoint_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows = {row["strategy_id"]: row for row in endpoint_rows}
    endpoint_keys = [
        "decision_count",
        "false_completion_trap_count",
        "legitimate_control_count",
        "accepted_false_completion_count",
        "rejected_legitimate_completion_count",
        "accepted_legitimate_completion_count",
        "false_completion_acceptance_rate",
        "false_rejection_rate",
        "legitimate_completion_preservation_rate",
        "reviewer_reproducibility_rate",
        "cost_usd",
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
                "false_completion_trap_count": row["false_completion_trap_count"],
                "legitimate_control_count": row["legitimate_control_count"],
                "cost_usd": row["cost_usd"],
                "passes_false_completion_bar": false_acceptance == ZERO,
                "passes_legitimate_preservation_bar": preservation == ONE,
                "balanced_fixture_pass": false_acceptance == ZERO
                and false_rejection == ZERO
                and preservation == ONE,
            }
        )
    external_false_accepts = int(rows["external_verifier"]["accepted_false_completion_count"])
    telos_false_accepts = int(rows["complete_telos_protocol"]["accepted_false_completion_count"])
    trap_count = int(rows["complete_telos_protocol"]["false_completion_trap_count"])
    telos_specific_detection_count = external_false_accepts - telos_false_accepts
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
        "complete_telos_specific_detection_count": telos_specific_detection_count,
        "complete_telos_specific_detection_rate_delta": decimal_string(
            Decimal(telos_specific_detection_count) / Decimal(trap_count)
        ),
        "complete_telos_only_balanced_pass_observed": True,
        "llm_judge_adverse_false_rejection_count": rows["llm_judge"][
            "rejected_legitimate_completion_count"
        ],
        "agent_self_report_false_acceptance_rate": rows["agent_self_report"][
            "false_completion_acceptance_rate"
        ],
        "execution_tests_only_false_acceptance_rate": rows["execution_tests_only"][
            "false_completion_acceptance_rate"
        ],
        "external_verifier_false_acceptance_rate": rows["external_verifier"][
            "false_completion_acceptance_rate"
        ],
    }


def audit_endpoint_and_comparison(
    packets: dict[str, dict[str, Any]], failures: list[str]
) -> None:
    summary = packets["summary"]
    endpoints = packets["endpoints"]
    comparison = packets["comparison"]
    adverse = packets["adverse"]
    iter103 = load_json(ITER103_ENDPOINTS)
    iter100 = load_json(ITER100_ENDPOINTS)
    if endpoints.get("source_endpoint_sha256") != sha256(ITER103_ENDPOINTS):
        failures.append("iter103 endpoint source hash mismatch")
    if endpoints.get("deterministic_source_endpoint_sha256") != sha256(ITER100_ENDPOINTS):
        failures.append("iter100 deterministic endpoint source hash mismatch")
    if endpoints.get("endpoint_rows") != iter103.get("endpoint_rows"):
        failures.append("iter104 endpoint table is not an exact iter103 copy")
    if endpoints.get("strategy_ids") != ALL_STRATEGIES:
        failures.append("strategy id list mismatch")
    if endpoints.get("all_strategy_endpoint_evidence_complete") is not True:
        failures.append("endpoint evidence must be complete")
    if endpoints.get("labels_used_in_strategy_inputs") is not False:
        failures.append("labels must not be used in strategy inputs")
    if endpoints.get("labels_used_in_llm_judge_prompt") is not False:
        failures.append("labels must not be used in LLM judge prompt")
    deterministic = {row["strategy_id"]: row for row in iter100["endpoint_rows"]}
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
    if comparison.get("balanced_fixture_pass_strategy_ids") != ["complete_telos_protocol"]:
        failures.append("unexpected balanced fixture pass strategies")
    if comparison.get("failed_false_completion_bar_strategy_ids") != [
        "agent_self_report",
        "execution_tests_only",
        "external_verifier",
    ]:
        failures.append("unexpected false-completion bar failures")
    if comparison.get("failed_legitimate_preservation_bar_strategy_ids") != ["llm_judge"]:
        failures.append("unexpected legitimate-preservation bar failures")
    if comparison.get("complete_telos_specific_detection_count") != 4:
        failures.append("complete Telos differential detection count mismatch")
    if comparison.get("complete_telos_specific_detection_rate_delta") != "0.50000000":
        failures.append("complete Telos differential rate delta mismatch")
    if comparison.get("fixture_level_telos_specific_advantage_over_external_verifier_claimed") is not True:
        failures.append("fixture-level Telos advantage claim missing")
    if comparison.get("all_strategy_superiority_claimed") is not False:
        failures.append("comparison claims broad all-strategy superiority")
    adverse_ids = {item.get("result_id") for item in adverse.get("adverse_results", [])}
    for expected in {
        "self_report_accepts_all_false_completion_traps",
        "execution_tests_accept_all_false_completion_traps",
        "llm_judge_high_false_rejection",
        "external_verifier_accepts_half_differential_traps",
        "synthetic_fixture_scope_limit",
    }:
        if expected not in adverse_ids:
            failures.append(f"missing adverse result: {expected}")
    if adverse.get("immediate_benchmark_claim_rejected") is not True:
        failures.append("adverse register must reject immediate benchmark claim")
    if adverse.get("external_benchmark_pilot_design_selected") is not True:
        failures.append("adverse register must select external benchmark-pilot design")


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
    if boundary.get("fixture_level_telos_specific_advantage_over_external_verifier_claimed") is not True:
        failures.append("fixture-level Telos advantage boundary claim missing")
    for key in [
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
    if summary.get("immediate_benchmark_claim_rejected") is not True:
        failures.append("summary must reject immediate benchmark claim")
    if summary.get("external_benchmark_pilot_design_selected") is not True:
        failures.append("summary must select external benchmark-pilot design")
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
        "Complete Telos was the only balanced pass",
        "benchmark/model/SOTA claim: `false`",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "complete Telos was the only balanced pass",
        "No benchmark, model-superiority, production/live-domain, broad all-strategy superiority",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "five-strategy differential adjudication: pass",
        "provider_api_calls=0",
        "complete_telos_specific_detection_count=4",
        "llm_judge_false_rejection_count=6",
        "external_verifier_and_complete_telos_same_endpoint_vector=false",
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
        print("iter104 five-strategy differential adjudication audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    summary = load_json(SUMMARY)
    print("iter104 five-strategy differential adjudication audit: pass")
    print(f"balanced_fixture_pass_strategy_ids={','.join(summary['balanced_fixture_pass_strategy_ids'])}")
    print(
        "complete_telos_specific_detection_count="
        f"{summary['complete_telos_specific_detection_count']}"
    )
    print(
        "complete_telos_specific_detection_rate_delta="
        f"{summary['complete_telos_specific_detection_rate_delta']}"
    )
    print(f"llm_judge_false_rejection_count={summary['llm_judge_adverse_false_rejection_count']}")
    print(f"next_gate={summary['next_gate']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
