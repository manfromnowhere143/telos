#!/usr/bin/env python3
"""Audit iter90 stability-replication adjudication artifacts."""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter90_stability_replication_adjudication_after_same_slice_run")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
PREREQ = PROOF / "iter89_prerequisite_validation.json"
LOCKED = PROOF / "locked_iter89_summary.json"
DIRECTION = PROOF / "direction_evidence_review.json"
DECISION = PROOF / "next_step_decision.json"
EMPIRICAL = PROOF / "empirical_validation_direction.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary.json"
REDACTION = PROOF / "redaction_scan.json"
RECEIPT = PROOF / "valid" / "receipt_stability_replication_adjudication_after_same_slice_run.json"
NEXT_GATE = Path("experiments/iter91_empirical_validation_suite_design_for_completion_verification/HYPOTHESIS.md")

ITER89_PROOF = Path("experiments/iter89_same_slice_discriminating_metric_stability_replication/proof")
ITER89_SUMMARY = ITER89_PROOF / "run_summary.json"
ITER89_STABILITY = ITER89_PROOF / "stability_report.json"
ITER89_EXTRACTION = ITER89_PROOF / "fresh_metric_extraction.json"
ITER89_EXECUTION = ITER89_PROOF / "execution_accounting_report.json"
ITER89_CLAIM_BOUNDARY = ITER89_PROOF / "claim_boundary.json"
ITER89_RECEIPT = ITER89_PROOF / "valid" / "receipt_same_slice_discriminating_metric_stability_replication.json"

METRIC_ID = "task_native_score_share_delta_with_receipt_gates"
SELECTED_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-dummy-yaml",
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
]
EXPECTED_TASK_DELTAS = {
    "dummy": {
        "iter86_delta": "0.00575000",
        "iter86_direction": "positive",
        "iter87_delta": "-0.01575000",
        "iter87_direction": "negative",
        "iter89_delta": "-0.02075000",
        "iter89_direction": "negative",
    },
    "battlesnake": {
        "iter86_delta": "-1.00000000",
        "iter86_direction": "negative",
        "iter87_delta": "0.50000000",
        "iter87_direction": "positive",
        "iter89_delta": "0.00000000",
        "iter89_direction": "zero",
    },
    "deterministic_edit": {
        "iter86_delta": "0.50000000",
        "iter86_direction": "positive",
        "iter87_delta": "-0.50000000",
        "iter87_direction": "negative",
        "iter89_delta": "-0.50000000",
        "iter89_direction": "negative",
    },
}
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
        LOCKED,
        DIRECTION,
        DECISION,
        EMPIRICAL,
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
        "summary": "telos.stability_replication_adjudication.summary.v1",
        "prereq": "telos.stability_replication_adjudication.iter89_prerequisite_validation.v1",
        "locked": "telos.stability_replication_adjudication.locked_iter89_summary.v1",
        "direction": "telos.stability_replication_adjudication.direction_evidence_review.v1",
        "decision": "telos.stability_replication_adjudication.next_step_decision.v1",
        "empirical": "telos.stability_replication_adjudication.empirical_validation_direction.v1",
        "boundary": "telos.stability_replication_adjudication.claim_boundary.v1",
        "redaction": "telos.stability_replication_adjudication.redaction_scan.v1",
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
        failures.append("iter90 summary must be a clean pass")
    if summary.get("blocked_result") is not False or summary.get("quality_failure") is not False:
        failures.append("summary blocked/quality flags must be false")
    if summary.get("blockers") != [] or summary.get("failures") != []:
        failures.append("pass summary must not contain blockers/failures")
    for packet_name in ["summary", "prereq", "direction", "decision", "empirical"]:
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
    for key in ["gpu_used", "cloud_runner_started", "sentinel_named_resources_modified"]:
        if summary.get(key) is not False:
            failures.append(f"summary {key} must be false")
    if redaction.get("passed") is not True or redaction.get("findings") != []:
        failures.append("redaction scan must pass with no findings")
    if summary.get("redaction_scan_passed") is not True or summary.get("redaction_findings") != []:
        failures.append("summary redaction scan must pass")


def audit_iter89_lock(packets: dict[str, dict], failures: list[str]) -> None:
    summary = packets["summary"]
    prereq = packets["prereq"]
    locked = packets["locked"]
    if prereq.get("clean_prerequisites") is not True:
        failures.append("iter89 prerequisites must be clean")
    if prereq.get("iter89_status") != "pass" or prereq.get("iter89_clean_pass") is not True:
        failures.append("iter89 must remain a clean pass")
    if prereq.get("iter89_receipt_validation_returncode") != 0:
        failures.append("iter89 receipt validation must pass")
    if prereq.get("iter89_audit_returncode") != 0:
        failures.append("iter89 audit must pass")
    if locked.get("selected_pair_ids") != SELECTED_PAIR_IDS:
        failures.append("locked selected pair ids changed")
    if locked.get("executed_pair_ids") != SELECTED_PAIR_IDS:
        failures.append("locked executed pair ids changed")
    if locked.get("executed_pair_count") != 6 or summary.get("iter89_executed_pair_count") != 6:
        failures.append("iter89 executed row count must be six")
    if locked.get("provider_api_calls") != 19 or summary.get("iter89_provider_api_calls") != 19:
        failures.append("iter89 provider call count changed")
    if decimal_value(locked.get("provider_cost_usd")) != Decimal("0.11636200"):
        failures.append("iter89 provider cost changed")
    if locked.get("metric_id") != METRIC_ID or summary.get("metric_id") != METRIC_ID:
        failures.append("metric id changed")
    if locked.get("metric_non_saturated") is not True or summary.get("iter89_metric_non_saturated") is not True:
        failures.append("iter89 metric must remain non-saturated")
    if locked.get("mixed_direction_signal") is not False:
        failures.append("iter89 current-run mixed-direction signal must remain false")
    if locked.get("execution_failures") != []:
        failures.append("iter89 execution failures changed")
    if locked.get("execution_blockers_after_metric_redefinition") != []:
        failures.append("iter89 execution blockers changed")
    if locked.get("stability_classification") != "unstable":
        failures.append("locked iter89 stability must remain unstable")
    if locked.get("stability_subclassification") != "iter89_mixed_against_prior_directions":
        failures.append("locked iter89 stability subclassification changed")

    by_path = {item.get("path"): item for item in prereq.get("source_artifacts", [])}
    expected_hashes = {
        str(ITER89_SUMMARY): sha256(ITER89_SUMMARY),
        str(ITER89_STABILITY): sha256(ITER89_STABILITY),
        str(ITER89_EXTRACTION): sha256(ITER89_EXTRACTION),
        str(ITER89_EXECUTION): sha256(ITER89_EXECUTION),
        str(ITER89_CLAIM_BOUNDARY): sha256(ITER89_CLAIM_BOUNDARY),
        str(ITER89_RECEIPT): sha256(ITER89_RECEIPT),
    }
    for path, expected_hash in expected_hashes.items():
        if by_path.get(path, {}).get("sha256") != expected_hash:
            failures.append(f"iter89 source hash mismatch: {path}")
    for field, path in [
        ("source_summary_sha256", ITER89_SUMMARY),
        ("source_stability_report_sha256", ITER89_STABILITY),
        ("source_metric_extraction_sha256", ITER89_EXTRACTION),
        ("source_execution_accounting_sha256", ITER89_EXECUTION),
    ]:
        if locked.get(field) != sha256(path):
            failures.append(f"locked iter89 hash mismatch: {field}")


def audit_direction_decision_and_empirical(packets: dict[str, dict], failures: list[str]) -> None:
    summary = packets["summary"]
    direction = packets["direction"]
    decision = packets["decision"]
    empirical = packets["empirical"]
    rows = direction.get("task_comparisons", [])
    if len(rows) != 3 or direction.get("task_count") != 3:
        failures.append("direction review must compare three task surfaces")
    if direction.get("iter89_matches_iter87_direction_count") != 2:
        failures.append("iter89 must match two iter87 task directions")
    if direction.get("iter89_matches_iter86_direction_count") != 0:
        failures.append("iter89 must match zero iter86 task directions")
    if summary.get("iter89_matches_iter87_direction_count") != 2:
        failures.append("summary iter89/iter87 match count changed")
    if summary.get("iter89_matches_iter86_direction_count") != 0:
        failures.append("summary iter89/iter86 match count changed")
    if direction.get("battlesnake_zeroed_after_positive_iter87") is not True:
        failures.append("BattleSnake zeroed evidence must be explicit")
    if direction.get("stability_classification") != "unstable":
        failures.append("direction stability classification must be unstable")
    if direction.get("stability_subclassification") != "iter89_mixed_against_prior_directions":
        failures.append("direction stability subclassification changed")
    for row in rows:
        task = row.get("task_surface")
        expected = EXPECTED_TASK_DELTAS.get(str(task))
        if expected is None:
            failures.append(f"unexpected task comparison: {task}")
            continue
        field_map = {
            "iter86_delta_telos_minus_baseline": "iter86_delta",
            "iter86_direction": "iter86_direction",
            "iter87_delta_telos_minus_baseline": "iter87_delta",
            "iter87_direction": "iter87_direction",
            "iter89_delta_telos_minus_baseline": "iter89_delta",
            "iter89_direction": "iter89_direction",
        }
        for field, expected_key in field_map.items():
            if row.get(field) != expected[expected_key]:
                failures.append(f"{task} {field} changed")

    if decision.get("decision") != "design_empirical_validation_suite":
        failures.append("next decision must design empirical validation suite")
    if summary.get("next_step_decision") != "design_empirical_validation_suite":
        failures.append("summary next decision changed")
    if decision.get("next_gate") != str(NEXT_GATE) or summary.get("next_gate") != str(NEXT_GATE):
        failures.append("next gate changed")
    if decision.get("next_gate_pre_registered") is not True or summary.get("next_gate_pre_registered") is not True:
        failures.append("next gate must be pre-registered")
    if not NEXT_GATE.exists():
        failures.append("next gate hypothesis missing")
    accepted = decision.get("accepted_path", {})
    if accepted.get("kind") != "empirical_validation_suite_design":
        failures.append("accepted path changed")
    if accepted.get("comparison_strategies") != VERIFICATION_STRATEGIES:
        failures.append("accepted comparison strategies changed")
    if accepted.get("case_family_count") != len(CASE_FAMILIES):
        failures.append("accepted case family count changed")
    if accepted.get("quantitative_endpoint_count") != len(QUANTITATIVE_ENDPOINTS):
        failures.append("accepted endpoint count changed")
    rejected_kinds = {row.get("kind") for row in decision.get("rejected_paths", [])}
    for kind in [
        "scale_to_external_benchmark_design",
        "repeat_same_slice_replication",
        "recover_metric_or_task_surface",
        "stop_benchmark_facing_path",
    ]:
        if kind not in rejected_kinds:
            failures.append(f"decision must explicitly reject {kind}")

    case_ids = [row.get("case_family_id") for row in empirical.get("case_families", [])]
    if case_ids != CASE_FAMILIES:
        failures.append("empirical case families changed")
    strategy_ids = [row.get("strategy_id") for row in empirical.get("verification_strategies", [])]
    if strategy_ids != VERIFICATION_STRATEGIES:
        failures.append("empirical verification strategies changed")
    endpoint_ids = [row.get("endpoint_id") for row in empirical.get("quantitative_endpoints", [])]
    if endpoint_ids != QUANTITATIVE_ENDPOINTS:
        failures.append("empirical quantitative endpoints changed")
    if summary.get("empirical_case_family_count") != len(CASE_FAMILIES):
        failures.append("summary empirical case family count changed")
    if summary.get("verification_strategy_count") != len(VERIFICATION_STRATEGIES):
        failures.append("summary verification strategy count changed")
    if summary.get("quantitative_endpoint_count") != len(QUANTITATIVE_ENDPOINTS):
        failures.append("summary endpoint count changed")
    if empirical.get("benchmark_or_sota_result_claimed") is not False:
        failures.append("empirical direction must not claim benchmark/SOTA result")
    if "publish null" not in empirical.get("null_result_policy", ""):
        failures.append("null result policy must preserve null results")


def audit_claim_boundary(packets: dict[str, dict], failures: list[str]) -> None:
    summary = packets["summary"]
    boundary = packets["boundary"]
    false_keys = [
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "swebench_execution_or_score_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "production_or_live_domain_changed",
        "empirical_superiority_claimed",
    ]
    for key in false_keys:
        if boundary.get(key) is not False:
            failures.append(f"claim boundary {key} must be false")
        if summary.get(key) is not False:
            failures.append(f"summary {key} must be false")
    for key in [
        "cross_task_surface_pooling_authorized",
        "aggregate_benchmark_metric_authorized",
        "external_benchmark_design_authorized_by_iter90",
        "future_paid_execution_authorized_by_iter90",
    ]:
        if boundary.get(key) is not False:
            failures.append(f"claim boundary {key} must be false")
    if summary.get("external_benchmark_design_authorized_by_iter89") is not False:
        failures.append("summary must preserve iter89 external benchmark design rejection")


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
        "iter89 provider calls: `19`",
        "iter89 provider cost: `$0.11636200`",
        "iter89 stability classification: `unstable`",
        "next-step decision: `design_empirical_validation_suite`",
        "benchmark/model/SOTA claim: `false`",
        "It is not a benchmark result",
        "empirical-superiority result",
        "state-of-the-art result",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "selected next step: `design_empirical_validation_suite`",
        "Immediate benchmark/SOTA escalation is rejected",
        "No benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority,",
        "empirical-superiority, or state-of-the-art result is claimed.",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "stability replication adjudication: pass",
        "provider_api_calls=0",
        "provider_cost_usd=0.00000000",
        "row_execution_in_this_gate=0",
        "iter89_provider_api_calls=19",
        "iter89_provider_cost_usd=0.11636200",
        "iter89_stability_classification=unstable",
        "next_step_decision=design_empirical_validation_suite",
        "case_family_count=7",
        "verification_strategy_count=5",
        "quantitative_endpoint_count=6",
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
            "locked": load_json(LOCKED),
            "direction": load_json(DIRECTION),
            "decision": load_json(DECISION),
            "empirical": load_json(EMPIRICAL),
            "boundary": load_json(CLAIM_BOUNDARY),
            "redaction": load_json(REDACTION),
        }
        audit_schemas(packets, failures)
        audit_status_and_zero_spend(packets, failures)
        audit_iter89_lock(packets, failures)
        audit_direction_decision_and_empirical(packets, failures)
        audit_claim_boundary(packets, failures)
        audit_receipt_text_hashes_and_secrets(packets["summary"], failures)
    if failures:
        print("iter90 stability replication adjudication audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter90 stability replication adjudication audit: pass")
    print("next_step_decision=design_empirical_validation_suite")
    print("iter89_stability_classification=unstable")
    print("provider_calls_in_iter90=0")
    print("provider_spend_in_iter90_usd=0.00000000")
    print(f"next_gate={NEXT_GATE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
