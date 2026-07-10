#!/usr/bin/env python3
"""Audit iter91 empirical validation suite design artifacts."""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter91_empirical_validation_suite_design_for_completion_verification")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
PREREQ = PROOF / "iter90_prerequisite_validation.json"
DESIGN = PROOF / "suite_design.json"
CASES = PROOF / "case_catalog.json"
STRATEGIES = PROOF / "strategy_comparison_plan.json"
ENDPOINTS = PROOF / "endpoint_spec.json"
GROUND_TRUTH = PROOF / "ground_truth_policy.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary.json"
REDACTION = PROOF / "redaction_scan.json"
RECEIPT = PROOF / "valid" / "receipt_empirical_validation_suite_design_for_completion_verification.json"
NEXT_GATE = Path(
    "experiments/iter92_empirical_validation_fixture_materialization_for_completion_verification/HYPOTHESIS.md"
)

ITER90_PROOF = Path("experiments/iter90_stability_replication_adjudication_after_same_slice_run/proof")
ITER90_SUMMARY = ITER90_PROOF / "run_summary.json"
ITER90_DECISION = ITER90_PROOF / "next_step_decision.json"
ITER90_EMPIRICAL = ITER90_PROOF / "empirical_validation_direction.json"
ITER90_RECEIPT = ITER90_PROOF / "valid" / "receipt_stability_replication_adjudication_after_same_slice_run.json"

CASE_FAMILIES = [
    "proxy_completion",
    "reward_hacking_behavior",
    "partial_implementation",
    "misleading_passing_tests",
    "incorrect_stopping_boundary",
    "adversarial_receipts",
    "semantically_incomplete_solution",
]
VERIFICATION_STRATEGIES = [
    "agent_self_report",
    "execution_tests_only",
    "llm_judge",
    "external_verifier",
    "complete_telos_protocol",
]
QUANTITATIVE_ENDPOINTS = [
    "false_completion_acceptance_rate",
    "false_rejection_rate",
    "legitimate_completion_preservation_rate",
    "cost_usd",
    "wall_clock_time_seconds",
    "reviewer_reproducibility_rate",
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
    re.compile(r"model_superiority_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"state_of_the_art_result_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"empirical_superiority_claimed[\"`:= ]+true", re.IGNORECASE),
    re.compile(r"benchmark/model/SOTA claim:\s*`true`", re.IGNORECASE),
    re.compile(r"\bSOTA achieved\b", re.IGNORECASE),
    re.compile(r"\bstate-of-the-art achieved\b", re.IGNORECASE),
    re.compile(r"\bmodel superiority achieved\b", re.IGNORECASE),
    re.compile(r"\bempirical superiority achieved\b", re.IGNORECASE),
    re.compile(r"\bleaderboard win\b", re.IGNORECASE),
    re.compile(r"\bSWE-bench win\b", re.IGNORECASE),
]


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be an object")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decimal_value(value: object) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.00000001"))


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
        DESIGN,
        CASES,
        STRATEGIES,
        ENDPOINTS,
        GROUND_TRUTH,
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


def audit_schemas(packets: dict[str, dict], failures: list[str]) -> None:
    expected = {
        "summary": "telos.empirical_validation_suite_design.summary.v1",
        "prereq": "telos.empirical_validation_suite_design.iter90_prerequisite_validation.v1",
        "design": "telos.empirical_validation_suite_design.suite_design.v1",
        "cases": "telos.empirical_validation_suite_design.case_catalog.v1",
        "strategies": "telos.empirical_validation_suite_design.strategy_comparison_plan.v1",
        "endpoints": "telos.empirical_validation_suite_design.endpoint_spec.v1",
        "truth": "telos.empirical_validation_suite_design.ground_truth_policy.v1",
        "boundary": "telos.empirical_validation_suite_design.claim_boundary.v1",
        "redaction": "telos.empirical_validation_suite_design.redaction_scan.v1",
    }
    for name, schema in expected.items():
        packet = packets[name]
        if packet.get("schema_version") != schema:
            failures.append(f"unexpected {name} schema")
        if packet.get("experiment_id") != EXPERIMENT.name:
            failures.append(f"{name} experiment id mismatch")


def audit_status_and_zero_spend(packets: dict[str, dict], failures: list[str]) -> None:
    summary = packets["summary"]
    redaction = packets["redaction"]
    if summary.get("status") != "pass" or summary.get("clean_pass") is not True:
        failures.append("iter91 summary must be a clean pass")
    if summary.get("blocked_result") is not False or summary.get("quality_failure") is not False:
        failures.append("summary blocked/quality flags must be false")
    if summary.get("blockers") != [] or summary.get("failures") != []:
        failures.append("pass summary must not contain blockers/failures")
    for packet_name in ["summary", "prereq", "design", "cases", "strategies", "endpoints", "truth"]:
        packet = packets[packet_name]
        calls = packet.get("provider_api_calls", packet.get("provider_calls_in_this_gate", 0))
        spend = packet.get(
            "provider_cost_usd",
            packet.get("provider_spend_in_this_gate_usd", "0.00000000"),
        )
        rows = packet.get("row_execution_in_this_gate", 0)
        if calls != 0:
            failures.append(f"{packet_name} provider calls must be zero")
        if decimal_value(spend) != Decimal("0.00000000"):
            failures.append(f"{packet_name} provider spend must be zero")
        if rows != 0:
            failures.append(f"{packet_name} row execution must be zero")
    if summary.get("strategy_execution_in_this_gate") != 0:
        failures.append("strategy execution must be zero")
    for key in ["gpu_used", "cloud_runner_started", "sentinel_named_resources_modified"]:
        if summary.get(key) is not False:
            failures.append(f"summary {key} must be false")
    if redaction.get("passed") is not True or redaction.get("findings") != []:
        failures.append("redaction scan must pass with no findings")
    if summary.get("redaction_scan_passed") is not True or summary.get("redaction_findings") != []:
        failures.append("summary redaction scan must pass")


def audit_iter90_prerequisite(packets: dict[str, dict], failures: list[str]) -> None:
    prereq = packets["prereq"]
    summary = packets["summary"]
    if prereq.get("clean_prerequisites") is not True:
        failures.append("iter90 prerequisites must be clean")
    if prereq.get("iter90_status") != "pass" or prereq.get("iter90_clean_pass") is not True:
        failures.append("iter90 must remain a clean pass")
    if prereq.get("iter90_receipt_validation_returncode") != 0:
        failures.append("iter90 receipt validation must pass")
    if prereq.get("iter90_audit_returncode") != 0:
        failures.append("iter90 audit must pass")
    if prereq.get("iter90_next_step_decision") != "design_empirical_validation_suite":
        failures.append("iter90 must select empirical suite design")
    if summary.get("iter90_clean_pass") is not True:
        failures.append("summary must preserve iter90 clean pass")
    by_path = {item.get("path"): item for item in prereq.get("source_artifacts", [])}
    expected_hashes = {
        str(ITER90_SUMMARY): sha256(ITER90_SUMMARY),
        str(ITER90_DECISION): sha256(ITER90_DECISION),
        str(ITER90_EMPIRICAL): sha256(ITER90_EMPIRICAL),
        str(ITER90_RECEIPT): sha256(ITER90_RECEIPT),
    }
    for path, expected_hash in expected_hashes.items():
        if by_path.get(path, {}).get("sha256") != expected_hash:
            failures.append(f"iter90 source hash mismatch: {path}")


def audit_design_cases_strategies_endpoints(packets: dict[str, dict], failures: list[str]) -> None:
    summary = packets["summary"]
    design = packets["design"]
    cases = packets["cases"]
    strategies = packets["strategies"]
    endpoints = packets["endpoints"]
    truth = packets["truth"]
    if design.get("suite_id") != "telos_completion_verification_empirical_suite_v0":
        failures.append("suite id changed")
    if design.get("case_family_count") != len(CASE_FAMILIES):
        failures.append("design case family count changed")
    if design.get("case_count") != 14 or cases.get("case_count") != 14:
        failures.append("suite must contain 14 planned cases")
    if design.get("false_completion_case_count") != 7 or cases.get("false_completion_case_count") != 7:
        failures.append("suite must contain seven false-completion traps")
    if (
        design.get("legitimate_completion_control_count") != 7
        or cases.get("legitimate_completion_control_count") != 7
    ):
        failures.append("suite must contain seven legitimate controls")
    if cases.get("case_families") != CASE_FAMILIES:
        failures.append("case family order changed")
    rows = cases.get("cases", [])
    by_family: dict[str, list[dict]] = {}
    for row in rows:
        by_family.setdefault(str(row.get("case_family_id")), []).append(row)
        if row.get("identical_artifacts_for_all_strategies") is not True:
            failures.append(f"{row.get('case_id')} must use identical artifacts")
        if row.get("ground_truth_source") != "fixture rubric and independent oracle; never a Telos output":
            failures.append(f"{row.get('case_id')} ground-truth source changed")
    for family in CASE_FAMILIES:
        family_rows = by_family.get(family, [])
        if len(family_rows) != 2:
            failures.append(f"{family} must have exactly two paired cases")
            continue
        labels = sorted(row.get("ground_truth_completed") for row in family_rows)
        kinds = sorted(row.get("case_kind") for row in family_rows)
        if labels != [False, True]:
            failures.append(f"{family} must have one false and one true case")
        if kinds != ["false_completion_trap", "legitimate_completion_control"]:
            failures.append(f"{family} case kinds changed")
    if strategies.get("strategy_ids") != VERIFICATION_STRATEGIES:
        failures.append("strategy id list changed")
    if strategies.get("strategy_count") != len(VERIFICATION_STRATEGIES):
        failures.append("strategy count changed")
    for strategy in strategies.get("strategies", []):
        if strategy.get("strategy_id") not in VERIFICATION_STRATEGIES:
            failures.append(f"unknown strategy {strategy.get('strategy_id')}")
        if not strategy.get("decision_source"):
            failures.append(f"{strategy.get('strategy_id')} missing decision source")
        if not isinstance(strategy.get("allowed_inputs"), list) or not strategy.get("allowed_inputs"):
            failures.append(f"{strategy.get('strategy_id')} missing allowed inputs")
    if strategies.get("llm_judge_execution_deferred") is not True:
        failures.append("LLM judge execution must be deferred")
    if strategies.get("strategy_execution_in_this_gate") != 0:
        failures.append("strategy comparison packet must record zero execution")
    if endpoints.get("endpoint_ids") != QUANTITATIVE_ENDPOINTS:
        failures.append("endpoint id list changed")
    if endpoints.get("primary_endpoint") != "false_completion_acceptance_rate":
        failures.append("primary endpoint changed")
    if endpoints.get("guardrail_endpoint") != "legitimate_completion_preservation_rate":
        failures.append("guardrail endpoint changed")
    if truth.get("ground_truth_independent_of_telos") is not True:
        failures.append("ground truth must be independent of Telos")
    if truth.get("ground_truth_visible_to_strategies") is not False:
        failures.append("ground truth must be hidden from strategies")
    if summary.get("case_family_count") != len(CASE_FAMILIES):
        failures.append("summary case family count changed")
    if summary.get("verification_strategies") != VERIFICATION_STRATEGIES:
        failures.append("summary strategy list changed")
    if summary.get("quantitative_endpoints") != QUANTITATIVE_ENDPOINTS:
        failures.append("summary endpoint list changed")
    if design.get("next_gate") != str(NEXT_GATE) or summary.get("next_gate") != str(NEXT_GATE):
        failures.append("next gate changed")
    if design.get("next_gate_pre_registered") is not True or summary.get("next_gate_pre_registered") is not True:
        failures.append("next gate must be pre-registered")
    if not NEXT_GATE.exists():
        failures.append("next gate hypothesis missing")


def audit_claim_boundary(packets: dict[str, dict], failures: list[str]) -> None:
    summary = packets["summary"]
    boundary = packets["boundary"]
    false_keys = [
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "swebench_execution_or_score_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "empirical_superiority_claimed",
        "production_or_live_domain_changed",
    ]
    for key in false_keys:
        if summary.get(key) is not False:
            failures.append(f"summary {key} must be false")
        if boundary.get(key) is not False:
            failures.append(f"claim boundary {key} must be false")
    if boundary.get("strategy_execution_completed") is not False:
        failures.append("strategy execution must not be claimed complete")
    if boundary.get("provider_execution_completed") is not False:
        failures.append("provider execution must not be claimed complete")
    if boundary.get("future_paid_execution_authorized_by_iter91") is not False:
        failures.append("iter91 must not authorize future paid execution")


def audit_receipt_text_hashes_and_secrets(summary: dict, failures: list[str]) -> None:
    try:
        receipt = load_receipt(RECEIPT)
    except ProofValidationError as exc:
        failures.append(f"gate receipt invalid: {exc}")
        return
    if receipt.status != summary.get("status"):
        failures.append("gate receipt status mismatch")

    result = RESULT.read_text(encoding="utf-8")
    review = (PROOF / "review.md").read_text(encoding="utf-8")
    command_output = (PROOF / "command_output.txt").read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`.",
        "case families: `7`",
        "total planned cases: `14`",
        "false-completion trap cases: `7`",
        "legitimate-completion controls: `7`",
        "comparison strategies: `5`",
        "quantitative endpoints: `6`",
        "ground truth independent of Telos: `true`",
        "identical artifacts for all strategies: `true`",
        "benchmark/model/SOTA claim: `false`",
        "empirical-superiority claim: `false`",
        "It is not a benchmark result",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "does not claim Telos outperforms any baseline",
        "paired false-completion traps and legitimate-completion controls",
        "No benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority,",
        "empirical-superiority, or state-of-the-art result is claimed.",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "empirical validation suite design: pass",
        "provider_api_calls=0",
        "provider_cost_usd=0.00000000",
        "strategy_execution_in_this_gate=0",
        "row_execution_in_this_gate=0",
        "case_family_count=7",
        "case_count=14",
        "false_completion_case_count=7",
        "legitimate_completion_control_count=7",
        "verification_strategy_count=5",
        "quantitative_endpoint_count=6",
        "ground_truth_independent_of_telos=true",
    ]:
        if required not in command_output:
            failures.append(f"command_output.txt missing required text: {required}")
    for pattern in FORBIDDEN_CLAIM_PATTERNS:
        for path, text in [
            (RESULT, result),
            (PROOF / "review.md", review),
            (PROOF / "command_output.txt", command_output),
        ]:
            if pattern.search(text):
                failures.append(f"unsupported claim-like text in {path}: {pattern.pattern}")

    for rel_path, expected_hash in summary.get("artifact_hashes", {}).items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"summary hash path missing: {rel_path}")
        elif sha256(path) != expected_hash:
            failures.append(f"summary hash mismatch: {rel_path}")
    for path in text_files(EXPERIMENT):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"secret pattern {pattern.pattern} found in {path}")
                break


def main() -> int:
    failures: list[str] = []
    audit_required_files(failures)
    if not failures:
        packets = {
            "summary": load_json(SUMMARY),
            "prereq": load_json(PREREQ),
            "design": load_json(DESIGN),
            "cases": load_json(CASES),
            "strategies": load_json(STRATEGIES),
            "endpoints": load_json(ENDPOINTS),
            "truth": load_json(GROUND_TRUTH),
            "boundary": load_json(CLAIM_BOUNDARY),
            "redaction": load_json(REDACTION),
        }
        audit_schemas(packets, failures)
        audit_status_and_zero_spend(packets, failures)
        audit_iter90_prerequisite(packets, failures)
        audit_design_cases_strategies_endpoints(packets, failures)
        audit_claim_boundary(packets, failures)
        audit_receipt_text_hashes_and_secrets(packets["summary"], failures)
    if failures:
        print("iter91 empirical validation suite design audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter91 empirical validation suite design audit: pass")
    print("case_count=14")
    print("verification_strategy_count=5")
    print("provider_calls_in_iter91=0")
    print("provider_spend_in_iter91_usd=0.00000000")
    print(f"next_gate={NEXT_GATE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
