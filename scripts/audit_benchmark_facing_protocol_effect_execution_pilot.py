#!/usr/bin/env python3
"""Audit iter83 benchmark-facing protocol-effect execution pilot artifacts."""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter83_benchmark_facing_protocol_effect_execution_pilot")
PROOF = EXPERIMENT / "proof"
RAW = PROOF / "raw"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
REPORT = PROOF / "protocol_effect_report.json"
PREFLIGHT = PROOF / "preflight.json"
PREREQ = PROOF / "prerequisite_validation.json"
ROW_PLAN = PROOF / "selected_row_plan.json"
RECOVERED = PROOF / "recovered_agent_overlay_manifest.json"
OVERLAY = PROOF / "overlay_materialization_manifest.json"
REDACTION = PROOF / "redaction_scan.json"
RECEIPT = PROOF / "valid" / "receipt_benchmark_facing_protocol_effect_execution_pilot.json"
ITER82_SUMMARY = Path("experiments/iter82_benchmark_facing_protocol_effect_slice_design/proof/run_summary.json")
ITER82_FUTURE_PLAN = Path(
    "experiments/iter82_benchmark_facing_protocol_effect_slice_design/proof/future_paid_run_plan.json"
)
SELECTED_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-dummy-yaml",
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
]
TASK_BY_PAIR = {
    SELECTED_PAIR_IDS[0]: "dummy",
    SELECTED_PAIR_IDS[1]: "battlesnake",
    SELECTED_PAIR_IDS[2]: "deterministic_edit",
    SELECTED_PAIR_IDS[3]: "dummy",
    SELECTED_PAIR_IDS[4]: "battlesnake",
    SELECTED_PAIR_IDS[5]: "deterministic_edit",
}
TELOS_PAIR_IDS = {
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
}
PER_ROW_CALL_LIMIT = 16
TOTAL_CALL_CEILING = 96
PER_ROW_SPEND_LIMIT = Decimal("2.0")
TOTAL_SPEND_CEILING = Decimal("10.0")
WALL_CLOCK_CEILING_SECONDS = 90 * 60
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
        REPORT,
        PREFLIGHT,
        PREREQ,
        ROW_PLAN,
        RECOVERED,
        OVERLAY,
        REDACTION,
        PROOF / "runtime_access_path_binding.json",
        PROOF / "runtime_access_path_model_config.yaml",
        PROOF / "command_output.txt",
        PROOF / "review.md",
        PROOF / "learning_record.json",
        RECEIPT,
    ]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")


def audit_common_packets(
    summary: dict,
    report: dict,
    preflight: dict,
    prereq: dict,
    row_plan: dict,
    recovered: dict,
    overlay: dict,
    redaction: dict,
    failures: list[str],
) -> None:
    expected_schemas = {
        "summary": (summary, "telos.benchmark_facing_protocol_effect_execution.summary.v1"),
        "report": (report, "telos.benchmark_facing_protocol_effect_execution.report.v1"),
        "preflight": (preflight, "telos.benchmark_facing_protocol_effect_execution.preflight.v1"),
        "prereq": (prereq, "telos.benchmark_facing_protocol_effect_execution.prerequisite_validation.v1"),
        "row_plan": (row_plan, "telos.benchmark_facing_protocol_effect_execution.selected_row_plan.v1"),
        "recovered": (recovered, "telos.benchmark_facing_protocol_effect_execution.recovered_agent_overlays.v1"),
        "overlay": (overlay, "telos.benchmark_facing_protocol_effect_execution.overlay_materialization.v1"),
        "redaction": (redaction, "telos.benchmark_facing_protocol_effect_execution.redaction_scan.v1"),
    }
    for name, (packet, schema) in expected_schemas.items():
        if packet.get("schema_version") != schema:
            failures.append(f"unexpected {name} schema")
        if packet.get("experiment_id") not in {None, EXPERIMENT.name}:
            failures.append(f"{name} experiment id mismatch")

    status = summary.get("status")
    if status not in {"pass", "blocked", "fail"}:
        failures.append(f"unexpected summary status: {status}")
    if report.get("status") != status:
        failures.append("summary/report status mismatch")
    if summary.get("clean_pass") is not (status == "pass"):
        failures.append("summary clean_pass inconsistent")
    if summary.get("blocked_result") is not (status == "blocked"):
        failures.append("summary blocked_result inconsistent")
    if summary.get("quality_failure") is not (status == "fail"):
        failures.append("summary quality_failure inconsistent")
    if report.get("clean_pass") is not (status == "pass"):
        failures.append("report clean_pass inconsistent")
    if report.get("blocked_result") is not (status == "blocked"):
        failures.append("report blocked_result inconsistent")
    if report.get("quality_failure") is not (status == "fail"):
        failures.append("report quality_failure inconsistent")
    if status == "pass" and (summary.get("blockers") or summary.get("failures")):
        failures.append("pass result must not contain blockers or failures")
    if status == "blocked" and not summary.get("blockers"):
        failures.append("blocked result must name a blocker")
    if status == "fail" and not summary.get("failures"):
        failures.append("fail result must name a quality failure")

    for packet_name, packet in [
        ("summary", summary),
        ("report", report),
        ("preflight", preflight),
        ("row_plan", row_plan),
        ("recovered", recovered),
    ]:
        if packet.get("selected_pair_ids") != SELECTED_PAIR_IDS:
            failures.append(f"{packet_name} selected pair ids changed")
    if row_plan.get("expected_selected_pair_ids") != SELECTED_PAIR_IDS:
        failures.append("row plan expected selected pair ids changed")
    if row_plan.get("row_count") != len(SELECTED_PAIR_IDS):
        failures.append("row plan row count changed")

    for packet_name, packet in [("summary", summary), ("report", report), ("preflight", preflight)]:
        if packet.get("provider_call_ceiling") != TOTAL_CALL_CEILING:
            failures.append(f"{packet_name} provider call ceiling changed")
        if decimal_value(packet.get("provider_spend_ceiling_usd")) != TOTAL_SPEND_CEILING:
            failures.append(f"{packet_name} provider spend ceiling changed")
        if packet.get("per_row_call_limit") != PER_ROW_CALL_LIMIT:
            failures.append(f"{packet_name} per-row call ceiling changed")
        if decimal_value(packet.get("per_row_spend_limit_usd")) != PER_ROW_SPEND_LIMIT:
            failures.append(f"{packet_name} per-row spend ceiling changed")
    if summary.get("provider_api_calls", 10**9) > TOTAL_CALL_CEILING:
        failures.append("summary provider call ceiling exceeded")
    if decimal_value(summary.get("provider_cost_usd")) > TOTAL_SPEND_CEILING:
        failures.append("summary provider spend ceiling exceeded")
    if summary.get("wall_clock_seconds", 10**9) > WALL_CLOCK_CEILING_SECONDS:
        failures.append("wall-clock ceiling exceeded")

    for key in [
        "gpu_used",
        "cloud_runner_started",
        "sentinel_named_resources_modified",
        "production_or_live_domain_changed",
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "swebench_execution_or_score_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "cross_task_surface_pooling_authorized",
        "aggregate_benchmark_or_model_claim_authorized",
    ]:
        for packet_name, packet in [("summary", summary), ("report", report)]:
            if key in packet and packet.get(key) is not False:
                failures.append(f"{packet_name} {key} must be false")
        if key in preflight and preflight.get(key) is not False:
            failures.append(f"preflight {key} must be false")

    if prereq.get("iter82_status") != "pass" or prereq.get("iter82_clean_pass") is not True:
        failures.append("iter82 prerequisite must be clean pass")
    if prereq.get("iter82_receipt_validation_returncode") != 0:
        failures.append("iter82 receipt validation must pass")
    if prereq.get("iter82_audit_returncode") != 0:
        failures.append("iter82 audit must pass")
    if prereq.get("source_iter82_summary_sha256") != sha256(ITER82_SUMMARY):
        failures.append("iter82 summary hash mismatch")
    if prereq.get("source_iter82_future_plan_sha256") != sha256(ITER82_FUTURE_PLAN):
        failures.append("iter82 future plan hash mismatch")
    if preflight.get("iter82_receipt_validation_returncode") != 0:
        failures.append("preflight iter82 receipt validation must pass")
    if preflight.get("iter82_audit_returncode") != 0:
        failures.append("preflight iter82 audit must pass")
    if preflight.get("codeclash_commit_matches_expected") is not True:
        failures.append("CodeClash commit mismatch")
    if preflight.get("docker_ready") is not True and status == "pass":
        failures.append("pass requires Docker readiness")
    if preflight.get("adc_access_token_available") is not True and status == "pass":
        failures.append("pass requires ADC readiness")

    generated = recovered.get("generated", [])
    if len(generated) != len(SELECTED_PAIR_IDS):
        failures.append("recovered overlay manifest must contain six rows")
    generated_by_pair = {item.get("pair_id"): item for item in generated if isinstance(item, dict)}
    for pair_id in SELECTED_PAIR_IDS:
        item = generated_by_pair.get(pair_id)
        if not item:
            failures.append(f"missing recovered overlay for {pair_id}")
            continue
        if item.get("recovered_step_limit") != PER_ROW_CALL_LIMIT:
            failures.append(f"{pair_id} recovered step limit changed")
        destination = Path(str(item.get("destination", "")))
        if not destination.exists():
            failures.append(f"{pair_id} recovered overlay destination missing")
        elif sha256(destination) != item.get("destination_sha256"):
            failures.append(f"{pair_id} recovered overlay hash mismatch")

    if status == "pass":
        if overlay.get("all_materialized") is not True:
            failures.append("pass requires runtime overlay materialization")
        if overlay.get("copied_hashes_match") is not True:
            failures.append("pass requires copied overlay hashes to match")
        if overlay.get("runtime_model_config_has_secret_values_only_in_tmp") is not True:
            failures.append("pass requires runtime secret boundary")
        if overlay.get("all_selected_agent_overlays_materialized") is not True:
            failures.append("pass requires all selected agent overlays materialized")

    if redaction.get("redaction_scan_passed") is not True:
        failures.append("redaction scan packet must pass")
    if redaction.get("redaction_findings") != []:
        failures.append("redaction scan packet must have no findings")
    if summary.get("redaction_scan_passed") is not True or summary.get("redaction_findings") != []:
        failures.append("summary redaction scan must pass")
    if report.get("redaction_scan_passed") is not True or report.get("redaction_findings") != []:
        failures.append("report redaction scan must pass")


def audit_rows(summary: dict, report: dict, failures: list[str]) -> None:
    row_results = report.get("row_results", [])
    executed_pair_ids = report.get("executed_pair_ids", [])
    if summary.get("executed_pair_ids") != executed_pair_ids:
        failures.append("summary/report executed pair ids mismatch")
    if summary.get("executed_pair_count") != report.get("executed_pair_count"):
        failures.append("summary/report executed count mismatch")
    if len(row_results) != report.get("executed_pair_count"):
        failures.append("row result count mismatch")
    if executed_pair_ids not in [[], SELECTED_PAIR_IDS] and report.get("status") != "fail":
        failures.append("non-fail result must execute zero rows or exactly the six selected rows")
    if set(executed_pair_ids) - set(SELECTED_PAIR_IDS):
        failures.append("unselected row executed")
    rows = {row.get("pair_id"): row for row in row_results if isinstance(row, dict)}
    if executed_pair_ids and list(rows) != executed_pair_ids:
        failures.append("row result order does not match executed ids")

    for pair_id in executed_pair_ids:
        row = rows.get(pair_id, {})
        raw_dir = RAW / pair_id
        if row.get("task_surface") != TASK_BY_PAIR.get(pair_id):
            failures.append(f"{pair_id} task surface mismatch")
        if row.get("provider_api_calls", 10**9) > PER_ROW_CALL_LIMIT:
            failures.append(f"{pair_id} exceeded per-row call ceiling")
        if decimal_value(row.get("provider_cost_usd")) > PER_ROW_SPEND_LIMIT:
            failures.append(f"{pair_id} exceeded per-row spend ceiling")
        if row.get("raw_evidence_present") is not True:
            failures.append(f"{pair_id} raw evidence missing")
        for required in [
            "command_execution.json",
            "command_stdout.txt",
            "command_stderr.txt",
            "raw_manifest.json",
            "metadata.json",
        ]:
            if not (raw_dir / required).exists():
                failures.append(f"{pair_id} missing raw artifact {required}")
        if pair_id in TELOS_PAIR_IDS:
            if row.get("receipt_required") is not True:
                failures.append(f"{pair_id} must require receipt")
            if row.get("verified_completion_evidence") is True and row.get("receipt_valid") is not True:
                failures.append(f"{pair_id} verified completion accepted without valid receipt")
        else:
            if row.get("receipt_required") is not False:
                failures.append(f"{pair_id} baseline must not require receipt")

    metric = summary.get("primary_metric", {})
    if metric != report.get("primary_metric"):
        failures.append("summary/report primary metric mismatch")
    expected_metric_keys = {
        "metric_id",
        "aggregate_benchmark_metric_authorized",
        "dummy_baseline_verified_completion_evidence",
        "dummy_telos_verified_completion_evidence",
        "dummy_delta_telos_minus_baseline",
        "battlesnake_baseline_verified_completion_evidence",
        "battlesnake_telos_verified_completion_evidence",
        "battlesnake_delta_telos_minus_baseline",
        "deterministic_edit_baseline_verified_completion_evidence",
        "deterministic_edit_telos_verified_completion_evidence",
        "deterministic_edit_delta_telos_minus_baseline",
        "interpretable_protocol_effect_signal",
    }
    if set(metric) != expected_metric_keys:
        failures.append("primary metric key set changed")
    if metric.get("aggregate_benchmark_metric_authorized") is not False:
        failures.append("primary metric must not authorize aggregate benchmark")
    deltas = [
        int(metric.get("dummy_delta_telos_minus_baseline", 0)),
        int(metric.get("battlesnake_delta_telos_minus_baseline", 0)),
        int(metric.get("deterministic_edit_delta_telos_minus_baseline", 0)),
    ]
    if bool(metric.get("interpretable_protocol_effect_signal")) != any(delta != 0 for delta in deltas):
        failures.append("interpretable signal flag inconsistent with deltas")
    if summary.get("null_result") is True:
        if "no_interpretable_telos_minus_baseline_signal" not in summary.get("blockers", []):
            failures.append("null result must name no-signal blocker")
        if metric.get("interpretable_protocol_effect_signal") is not False:
            failures.append("null result must not have interpretable signal")
    if summary.get("status") == "pass":
        if summary.get("executed_pair_ids") != SELECTED_PAIR_IDS:
            failures.append("pass requires exactly six selected rows")
        if metric.get("interpretable_protocol_effect_signal") is not True:
            failures.append("pass requires an interpretable stratified signal")


def audit_receipt_text_and_hashes(summary: dict, failures: list[str]) -> None:
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
        "Benchmark-Facing Protocol-Effect Execution Pilot",
        "selected row count: `6`",
        "per-row provider call ceiling: `16`",
        "provider call ceiling: `96`",
        "provider spend ceiling: `$10.00`",
        "benchmark/model/SOTA claim: `false`",
        "It is not a benchmark",
        "state-of-the-art result",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "frozen six-row benchmark-facing pilot",
        "no aggregate benchmark",
        "state-of-the-art claim is authorized",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "benchmark-facing protocol-effect execution pilot:",
        "selected_pair_count=6",
        "per_row_call_limit=16",
        "provider_call_ceiling=96",
        "provider_spend_ceiling_usd=10.00",
        "interpretable_protocol_effect_signal=",
    ]:
        if required not in command_output:
            failures.append(f"command_output.txt missing required text: {required}")
    for forbidden in [
        "This is a benchmark result",
        "This is a state-of-the-art result",
        "This is a model-superiority result",
        "This is a leaderboard result",
        "Telos is SOTA",
        "Telos outperforms baseline overall",
    ]:
        if forbidden in result or forbidden in review:
            failures.append(f"claim boundary regression: {forbidden}")

    for rel_path, expected_hash in summary.get("artifact_hashes", {}).items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"summary hash path missing: {rel_path}")
        elif sha256(path) != expected_hash:
            failures.append(f"summary hash mismatch: {rel_path}")


def audit_secrets(failures: list[str]) -> None:
    for path in text_files(EXPERIMENT):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"secret-like or identifier residue in {path}")
                break


def main() -> int:
    failures: list[str] = []
    audit_required_files(failures)
    if not failures:
        summary = load_json(SUMMARY)
        report = load_json(REPORT)
        preflight = load_json(PREFLIGHT)
        prereq = load_json(PREREQ)
        row_plan = load_json(ROW_PLAN)
        recovered = load_json(RECOVERED)
        overlay = load_json(OVERLAY)
        redaction = load_json(REDACTION)
        audit_common_packets(
            summary,
            report,
            preflight,
            prereq,
            row_plan,
            recovered,
            overlay,
            redaction,
            failures,
        )
        audit_rows(summary, report, failures)
        audit_receipt_text_and_hashes(summary, failures)
        audit_secrets(failures)
    if failures:
        print("iter83 benchmark-facing protocol-effect execution pilot audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter83 benchmark-facing protocol-effect execution pilot audit: clean artifact packet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
