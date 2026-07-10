#!/usr/bin/env python3
"""Audit iter81 stratified adapter-validation consolidation artifacts."""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter81_expanded_stratified_adapter_validation_consolidation")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
SOURCE_VALIDATION = PROOF / "source_packet_validation.json"
ROW_ACCOUNTING = PROOF / "stratified_row_accounting.json"
PROVIDER_TOTALS = PROOF / "provider_totals.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary.json"
NEXT_RECOMMENDATION = PROOF / "next_gate_recommendation.json"
REDACTION = PROOF / "redaction_scan.json"
RECEIPT = PROOF / "valid" / "receipt_expanded_stratified_adapter_validation_consolidation.json"
NEXT_GATE = "experiments/iter82_benchmark_facing_protocol_effect_slice_design/HYPOTHESIS.md"
TEXT_SUFFIXES = {".json", ".jsonl", ".log", ".txt", ".md", ".yaml", ".yml", ".py"}
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"Bearer\s+(?!\$\{TELOS_VERTEX_BEARER_TOKEN\}|\[REDACTED_BEARER_TOKEN\])\S+"),
    re.compile(r"-----BEGIN PRIVATE KEY-----"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com"),
    re.compile(r"telos-vertex-runner"),
    re.compile(r"sunlit-unison-[A-Za-z0-9-]+"),
    re.compile(r"errorId=Ci"),
    re.compile(r'"error_info_id"\s*:\s*"Ci'),
]
BATTLESNAKE_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
]
DETERMINISTIC_EDIT_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
]
DUMMY_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-dummy-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
]
CONSOLIDATED_PAIR_IDS = BATTLESNAKE_PAIR_IDS + DETERMINISTIC_EDIT_PAIR_IDS + DUMMY_PAIR_IDS
SOURCE_SUMMARIES = {
    "iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment": Path(
        "experiments/iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment/proof/run_summary.json"
    ),
    "iter78_provider_compatible_expanded_paid_retry_after_adc_recovery": Path(
        "experiments/iter78_provider_compatible_expanded_paid_retry_after_adc_recovery/proof/run_summary.json"
    ),
    "iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery": Path(
        "experiments/iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery/proof/run_summary.json"
    ),
}
SOURCE_REPORTS = {
    "iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment": Path(
        "experiments/iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment/proof/protocol_effect_report.json"
    ),
    "iter78_provider_compatible_expanded_paid_retry_after_adc_recovery": Path(
        "experiments/iter78_provider_compatible_expanded_paid_retry_after_adc_recovery/proof/protocol_effect_report.json"
    ),
    "iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery": Path(
        "experiments/iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery/proof/protocol_effect_report.json"
    ),
}
SOURCE_RECEIPTS = {
    "iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment": Path(
        "experiments/iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment/proof/valid/receipt_provider_compatible_paid_execution_after_receipt_prompt_alignment.json"
    ),
    "iter78_provider_compatible_expanded_paid_retry_after_adc_recovery": Path(
        "experiments/iter78_provider_compatible_expanded_paid_retry_after_adc_recovery/proof/valid/receipt_provider_compatible_expanded_paid_retry_after_adc_recovery.json"
    ),
    "iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery": Path(
        "experiments/iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery/proof/valid/receipt_dummy_call_ceiling_bounded_paid_retry_after_recovery.json"
    ),
}


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be an object")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decimal_value(value: object) -> Decimal:
    return Decimal(str(value or 0))


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
        SOURCE_VALIDATION,
        ROW_ACCOUNTING,
        PROVIDER_TOTALS,
        CLAIM_BOUNDARY,
        NEXT_RECOMMENDATION,
        REDACTION,
        PROOF / "command_output.txt",
        PROOF / "review.md",
        PROOF / "learning_record.json",
        RECEIPT,
        Path(NEXT_GATE),
    ]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")


def audit_source_validation(source_validation: dict, failures: list[str]) -> None:
    if source_validation.get("schema_version") != (
        "telos.expanded_stratified_adapter_validation.source_validation.v1"
    ):
        failures.append("unexpected source validation schema")
    if source_validation.get("experiment_id") != EXPERIMENT.name:
        failures.append("source validation experiment id mismatch")
    if source_validation.get("all_source_packets_valid") is not True:
        failures.append("source packets must validate cleanly for consolidation")
    source_packets = source_validation.get("source_packets", [])
    if len(source_packets) != 3:
        failures.append("expected three source packets")
    expected_status = {
        "iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment": "pass",
        "iter78_provider_compatible_expanded_paid_retry_after_adc_recovery": "blocked",
        "iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery": "pass",
    }
    by_iteration = {
        item.get("source_iteration"): item
        for item in source_packets
        if isinstance(item, dict)
    }
    if set(by_iteration) != set(expected_status):
        failures.append("source packet iteration set changed")
    for iteration_id, expected in expected_status.items():
        item = by_iteration.get(iteration_id, {})
        if item.get("expected_status") != expected or item.get("observed_status") != expected:
            failures.append(f"{iteration_id} status mismatch")
        if item.get("clean_for_consolidation") is not True:
            failures.append(f"{iteration_id} not clean for consolidation")
        if item.get("receipt_validation_returncode") != 0:
            failures.append(f"{iteration_id} receipt validation failed")
        if item.get("audit_returncode") != 0:
            failures.append(f"{iteration_id} audit failed")
        if item.get("quality_failure") is not False:
            failures.append(f"{iteration_id} quality failure must be false")
        if item.get("source_summary_sha256") != sha256(SOURCE_SUMMARIES[iteration_id]):
            failures.append(f"{iteration_id} summary hash mismatch")
        if item.get("source_report_sha256") != sha256(SOURCE_REPORTS[iteration_id]):
            failures.append(f"{iteration_id} report hash mismatch")
        if item.get("source_receipt_sha256") != sha256(SOURCE_RECEIPTS[iteration_id]):
            failures.append(f"{iteration_id} receipt hash mismatch")
    for command in source_validation.get("command_results", []):
        if command.get("returncode") != 0 or command.get("timed_out") is not False:
            failures.append(f"source validation command failed: {command.get('command')}")


def audit_row_accounting(row_accounting: dict, failures: list[str]) -> None:
    if row_accounting.get("schema_version") != (
        "telos.expanded_stratified_adapter_validation.row_accounting.v1"
    ):
        failures.append("unexpected row accounting schema")
    if row_accounting.get("experiment_id") != EXPERIMENT.name:
        failures.append("row accounting experiment id mismatch")
    if row_accounting.get("adapter_rows_executed_in_this_gate") != 0:
        failures.append("iter81 must execute zero rows")
    if row_accounting.get("provider_calls_in_this_gate") != 0:
        failures.append("iter81 must make zero provider calls")
    if decimal_value(row_accounting.get("provider_cost_usd_in_this_gate")) != Decimal("0.00000000"):
        failures.append("iter81 must spend zero provider dollars")
    if row_accounting.get("consolidated_pair_ids") != CONSOLIDATED_PAIR_IDS:
        failures.append("consolidated pair ids changed")
    if row_accounting.get("consolidated_success_pair_count") != 6:
        failures.append("expected six consolidated successful rows")
    if row_accounting.get("source_row_executions_accounted") != 8:
        failures.append("expected eight source row executions accounted")
    if row_accounting.get("diagnostic_blocked_pair_ids") != DUMMY_PAIR_IDS:
        failures.append("diagnostic blocked Dummy pair ids changed")
    if row_accounting.get("diagnostic_blocked_pair_count") != 2:
        failures.append("expected two diagnostic blocked Dummy rows")
    if row_accounting.get("all_task_surfaces_stratified") is not True:
        failures.append("task surfaces must remain stratified")
    if row_accounting.get("cross_task_surface_pooling_authorized") is not False:
        failures.append("cross-task-surface pooling must not be authorized")
    if row_accounting.get("aggregate_benchmark_or_model_claim_authorized") is not False:
        failures.append("aggregate benchmark/model claim must not be authorized")
    if row_accounting.get("row_accounting_reconciled") is not True:
        failures.append("row accounting must reconcile")

    consolidated_rows = row_accounting.get("consolidated_rows", [])
    diagnostic_rows = row_accounting.get("diagnostic_rows", [])
    if len(consolidated_rows) != 6 or len(diagnostic_rows) != 2:
        failures.append("consolidated/diagnostic row counts changed")
    row_ids = [item.get("pair_id") for item in consolidated_rows if isinstance(item, dict)]
    if row_ids != CONSOLIDATED_PAIR_IDS:
        failures.append("consolidated row order or ids changed")
    diagnostic_ids = [item.get("pair_id") for item in diagnostic_rows if isinstance(item, dict)]
    if diagnostic_ids != DUMMY_PAIR_IDS:
        failures.append("diagnostic row order or ids changed")
    for item in consolidated_rows:
        if item.get("executed_in_iter81") is not False:
            failures.append(f"{item.get('pair_id')} must not execute in iter81")
        if item.get("consolidated_success_evidence") is not True:
            failures.append(f"{item.get('pair_id')} must be consolidated success evidence")
        if item.get("command_returncode") != 0:
            failures.append(f"{item.get('pair_id')} return code must be zero")
        if item.get("command_timed_out") is not False:
            failures.append(f"{item.get('pair_id')} must not time out")
        if item.get("verified_completion_evidence") is not True:
            failures.append(f"{item.get('pair_id')} must verify completion")
        if item.get("raw_evidence_present") is not True:
            failures.append(f"{item.get('pair_id')} raw evidence must be present")
        if item.get("receipt_required") is True and item.get("receipt_valid") is not True:
            failures.append(f"{item.get('pair_id')} required receipt must be valid")
    for item in diagnostic_rows:
        if item.get("consolidated_success_evidence") is not False:
            failures.append(f"{item.get('pair_id')} diagnostic row must not be success evidence")
        if item.get("command_returncode") != 1:
            failures.append(f"{item.get('pair_id')} diagnostic row must preserve iter78 block")
        if item.get("verified_completion_evidence") is not False:
            failures.append(f"{item.get('pair_id')} diagnostic row must remain unverified")

    strata = row_accounting.get("consolidated_success_strata", [])
    if len(strata) != 3:
        failures.append("expected three consolidated success strata")
    expected_strata = {
        "retained_battlesnake_prior_paid_evidence": {
            "pair_ids": BATTLESNAKE_PAIR_IDS,
            "calls": 8,
            "cost": Decimal("0.05937800"),
        },
        "deterministic_edit_adapter_validation": {
            "pair_ids": DETERMINISTIC_EDIT_PAIR_IDS,
            "calls": 4,
            "cost": Decimal("0.01756600"),
        },
        "dummy_minimal_adapter_validation": {
            "pair_ids": DUMMY_PAIR_IDS,
            "calls": 6,
            "cost": Decimal("0.02840000"),
        },
    }
    by_name = {item.get("name"): item for item in strata if isinstance(item, dict)}
    if set(by_name) != set(expected_strata):
        failures.append("consolidated stratum names changed")
    for name, expected in expected_strata.items():
        item = by_name.get(name, {})
        if item.get("pair_ids") != expected["pair_ids"]:
            failures.append(f"{name} pair ids changed")
        if item.get("provider_api_calls") != expected["calls"]:
            failures.append(f"{name} provider calls changed")
        if decimal_value(item.get("provider_cost_usd")) != expected["cost"]:
            failures.append(f"{name} provider cost changed")
        if item.get("baseline_verified_completion_evidence") is not True:
            failures.append(f"{name} baseline must be verified")
        if item.get("telos_verified_completion_evidence") is not True:
            failures.append(f"{name} Telos must be verified")
        if item.get("telos_minus_baseline_verified_completion_delta") != 0:
            failures.append(f"{name} delta must be zero")
        if item.get("cross_task_surface_pooling_authorized") is not False:
            failures.append(f"{name} must not authorize pooling")


def audit_provider_totals(provider_totals: dict, failures: list[str]) -> None:
    if provider_totals.get("schema_version") != (
        "telos.expanded_stratified_adapter_validation.provider_totals.v1"
    ):
        failures.append("unexpected provider totals schema")
    if provider_totals.get("experiment_id") != EXPERIMENT.name:
        failures.append("provider totals experiment id mismatch")
    expected = {
        "source_packet_count": 3,
        "source_packet_total_provider_api_calls": 23,
        "source_packet_total_provider_cost_usd": Decimal("0.12765400"),
        "consolidated_success_evidence_provider_api_calls": 18,
        "consolidated_success_evidence_provider_cost_usd": Decimal("0.10534400"),
        "diagnostic_blocked_dummy_provider_api_calls": 5,
        "diagnostic_blocked_dummy_provider_cost_usd": Decimal("0.02231000"),
        "provider_api_calls_in_this_gate": 0,
        "provider_cost_usd_in_this_gate": Decimal("0.00000000"),
        "provider_spend_in_this_gate_usd": Decimal("0.00000000"),
    }
    for key, value in expected.items():
        observed = provider_totals.get(key)
        if isinstance(value, Decimal):
            if decimal_value(observed) != value:
                failures.append(f"{key} changed")
        elif observed != value:
            failures.append(f"{key} changed")
    if provider_totals.get("exact_source_packet_totals_preserved") is not True:
        failures.append("source packet totals must be preserved")


def audit_claims(summary: dict, claim_boundary: dict, next_gate: dict, failures: list[str]) -> None:
    for packet_name, packet in [
        ("summary", summary),
        ("claim_boundary", claim_boundary),
    ]:
        for key in [
            "benchmark_result_claimed",
            "leaderboard_or_swebench_result_claimed",
            "model_superiority_claimed",
            "state_of_the_art_result_claimed",
            "production_or_live_domain_changed",
            "cross_task_surface_pooling_authorized",
            "aggregate_benchmark_or_model_claim_authorized",
        ]:
            if packet.get(key) is not False:
                failures.append(f"{packet_name} must keep {key}=false")
    if claim_boundary.get("schema_version") != (
        "telos.expanded_stratified_adapter_validation.claim_boundary.v1"
    ):
        failures.append("unexpected claim boundary schema")
    if claim_boundary.get("aggregate_primary_metric_authorized") is not False:
        failures.append("aggregate primary metric must not be authorized")
    if next_gate.get("schema_version") != "telos.expanded_stratified_adapter_validation.next_gate.v1":
        failures.append("unexpected next gate schema")
    if next_gate.get("recommended_next_gate") != NEXT_GATE:
        failures.append("recommended next gate changed")
    if next_gate.get("adapter_rows_to_execute") != 0:
        failures.append("next gate must execute zero rows")
    if next_gate.get("provider_model_invocations") != 0:
        failures.append("next gate must allow zero provider invocations")
    if decimal_value(next_gate.get("provider_spend_ceiling_usd")) != Decimal("0.00000000"):
        failures.append("next gate must have zero spend ceiling")
    if next_gate.get("benchmark_model_or_sota_claim") != "forbidden":
        failures.append("next gate must forbid benchmark/model/SOTA claim")


def audit_summary(summary: dict, failures: list[str]) -> None:
    if summary.get("schema_version") != "telos.expanded_stratified_adapter_validation.summary.v1":
        failures.append("unexpected summary schema")
    if summary.get("experiment_id") != EXPERIMENT.name:
        failures.append("summary experiment id mismatch")
    if summary.get("status") != "pass":
        failures.append("iter81 must pass")
    if summary.get("clean_pass") is not True:
        failures.append("summary clean_pass must be true")
    if summary.get("blocked_result") is not False or summary.get("quality_failure") is not False:
        failures.append("summary blocked/quality flags must be false")
    if summary.get("blockers") != [] or summary.get("failures") != []:
        failures.append("pass summary must not contain blockers/failures")
    if summary.get("source_packet_count") != 3:
        failures.append("summary source packet count changed")
    if summary.get("source_packets_valid") is not True:
        failures.append("summary source packets must be valid")
    if summary.get("consolidated_success_pair_count") != 6:
        failures.append("summary consolidated pair count changed")
    if summary.get("diagnostic_blocked_pair_count") != 2:
        failures.append("summary diagnostic pair count changed")
    if summary.get("adapter_rows_executed_in_this_gate") != 0:
        failures.append("summary must record zero iter81 row execution")
    if summary.get("provider_api_calls") != 0:
        failures.append("summary must record zero iter81 provider calls")
    if decimal_value(summary.get("provider_cost_usd")) != Decimal("0"):
        failures.append("summary must record zero iter81 provider cost")
    if summary.get("provider_call_ceiling") != 0:
        failures.append("summary provider call ceiling must be zero")
    if summary.get("gpu_used") is not False:
        failures.append("GPU use must be false")
    if summary.get("cloud_runner_started") is not False:
        failures.append("cloud runner startup must be false")
    if summary.get("sentinel_named_resources_modified") is not False:
        failures.append("Sentinel mutation must be false")
    if summary.get("redaction_scan_passed") is not True:
        failures.append("summary redaction scan must pass")
    if summary.get("redaction_findings") != []:
        failures.append("summary redaction findings must be empty")
    if summary.get("next_gate") != NEXT_GATE:
        failures.append("summary next gate changed")
    metric = summary.get("primary_metric", {})
    for key in [
        "battlesnake_baseline_verified_completion_evidence",
        "battlesnake_telos_verified_completion_evidence",
        "deterministic_edit_baseline_verified_completion_evidence",
        "deterministic_edit_telos_verified_completion_evidence",
        "dummy_baseline_verified_completion_evidence",
        "dummy_telos_verified_completion_evidence",
    ]:
        if metric.get(key) is not True:
            failures.append(f"summary metric {key} must be true")
    for key in [
        "battlesnake_delta_telos_minus_baseline",
        "deterministic_edit_delta_telos_minus_baseline",
        "dummy_delta_telos_minus_baseline",
    ]:
        if metric.get(key) != 0:
            failures.append(f"summary metric {key} must be zero")
    if metric.get("aggregate_primary_metric_authorized") is not False:
        failures.append("summary must not authorize aggregate primary metric")


def audit_redaction(redaction: dict, failures: list[str]) -> None:
    if redaction.get("schema_version") != (
        "telos.expanded_stratified_adapter_validation.redaction_scan.v1"
    ):
        failures.append("unexpected redaction schema")
    if redaction.get("experiment_id") != EXPERIMENT.name:
        failures.append("redaction experiment id mismatch")
    if redaction.get("passed") is not True:
        failures.append("redaction scan packet must pass")
    if redaction.get("findings") != []:
        failures.append("redaction scan packet must have no findings")
    for path in text_files(EXPERIMENT):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"redaction finding in {path}")
                break


def audit_review_text(failures: list[str]) -> None:
    result_text = RESULT.read_text(encoding="utf-8")
    review_text = (PROOF / "review.md").read_text(encoding="utf-8")
    command_output = (PROOF / "command_output.txt").read_text(encoding="utf-8")
    required = [
        "not a benchmark result",
        "model-superiority result",
        "state-of-the-art result",
        "cross-surface pooling",
        "provider calls and $0.00000000",
    ]
    combined = f"{result_text}\n{review_text}"
    for needle in required:
        if needle not in combined:
            failures.append(f"missing claim-boundary text: {needle}")
    for forbidden in [
        "adapter rows executed: 1",
        "provider model invocations: 1",
        "benchmark result claimed: true",
        "state_of_the_art_result_claimed: true",
    ]:
        if forbidden in command_output:
            failures.append(f"forbidden command-output marker: {forbidden}")


def audit_receipt(failures: list[str]) -> None:
    try:
        receipt = load_receipt(RECEIPT)
    except (OSError, json.JSONDecodeError, ProofValidationError) as exc:
        failures.append(f"invalid receipt: {exc}")
        return
    if receipt.status != "pass":
        failures.append("receipt status must be pass")
    if receipt.receipt_id != "iter81-expanded-stratified-adapter-validation-consolidation-pass":
        failures.append("receipt id changed")


def main() -> int:
    failures: list[str] = []
    audit_required_files(failures)
    if failures:
        for failure in failures:
            print(f"iter81 audit failed: {failure}", file=sys.stderr)
        return 1

    summary = load_json(SUMMARY)
    source_validation = load_json(SOURCE_VALIDATION)
    row_accounting = load_json(ROW_ACCOUNTING)
    provider_totals = load_json(PROVIDER_TOTALS)
    claim_boundary = load_json(CLAIM_BOUNDARY)
    next_gate = load_json(NEXT_RECOMMENDATION)
    redaction = load_json(REDACTION)

    audit_summary(summary, failures)
    audit_source_validation(source_validation, failures)
    audit_row_accounting(row_accounting, failures)
    audit_provider_totals(provider_totals, failures)
    audit_claims(summary, claim_boundary, next_gate, failures)
    audit_redaction(redaction, failures)
    audit_review_text(failures)
    audit_receipt(failures)

    if failures:
        for failure in failures:
            print(f"iter81 audit failed: {failure}", file=sys.stderr)
        return 1
    print("iter81 expanded stratified adapter-validation consolidation audit: pass")
    print("source_packets=3")
    print("consolidated_success_pair_count=6")
    print("diagnostic_blocked_pair_count=2")
    print("provider_calls_in_this_gate=0")
    print("provider_spend_in_this_gate_usd=0.00000000")
    print(f"next_gate={NEXT_GATE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
