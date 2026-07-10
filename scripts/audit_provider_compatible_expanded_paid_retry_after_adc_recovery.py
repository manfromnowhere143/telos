#!/usr/bin/env python3
"""Audit iter78 provider-compatible expanded paid-retry artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path(
    "experiments/iter78_provider_compatible_expanded_paid_retry_after_adc_recovery"
)
PROOF = EXPERIMENT / "proof"
RAW = PROOF / "raw"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
REPORT = PROOF / "protocol_effect_report.json"
PREFLIGHT = PROOF / "preflight.json"
PREREQ = PROOF / "prerequisite_validation.json"
OVERLAY = PROOF / "overlay_materialization_manifest.json"
RECOVERED_BINDING = PROOF / "recovered_prompt_overlay_binding.json"
RECEIPT = (
    PROOF
    / "valid"
    / "receipt_provider_compatible_expanded_paid_retry_after_adc_recovery.json"
)
EXPECTED_SELECTED_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-dummy-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
    "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
]
EXPECTED_RETAINED_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
]
RECEIPT_REQUIRED_PAIR_IDS = {
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
}
EXPECTED_RECOVERED_SOURCES = {
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml": (
        "experiments/iter73_expanded_receipt_prompt_recovery_after_paid_block/proof/"
        "recovered_overlay/configs/mini/telos_vertex_gemini_dummy_receipt_enforced_agent.yaml"
    ),
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml": (
        "experiments/iter73_expanded_receipt_prompt_recovery_after_paid_block/proof/"
        "recovered_overlay/configs/mini/telos_vertex_gemini_edit_receipt_enforced_agent.yaml"
    ),
}
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
        OVERLAY,
        RECOVERED_BINDING,
        PROOF / "runtime_access_path_binding.json",
        PROOF / "runtime_access_path_model_config.yaml",
        PROOF / "command_output.txt",
        PROOF / "review.md",
        PROOF / "learning_record.json",
        RECEIPT,
    ]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")


def expected_primary_metric(rows: dict[str, dict]) -> dict:
    metric = {
        "dummy_baseline_verified_completion_evidence": rows.get(
            "baseline-agent-completion-evidence__configs-test-dummy-yaml", {}
        ).get("verified_completion_evidence", False),
        "dummy_telos_verified_completion_evidence": rows.get(
            "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml", {}
        ).get("verified_completion_evidence", False),
        "deterministic_edit_baseline_verified_completion_evidence": rows.get(
            "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml", {}
        ).get("verified_completion_evidence", False),
        "deterministic_edit_telos_verified_completion_evidence": rows.get(
            "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
            {},
        ).get("verified_completion_evidence", False),
    }
    metric["dummy_delta_telos_minus_baseline"] = int(
        bool(metric["dummy_telos_verified_completion_evidence"])
    ) - int(bool(metric["dummy_baseline_verified_completion_evidence"]))
    metric["deterministic_edit_delta_telos_minus_baseline"] = int(
        bool(metric["deterministic_edit_telos_verified_completion_evidence"])
    ) - int(bool(metric["deterministic_edit_baseline_verified_completion_evidence"]))
    return metric


def audit_prerequisites_and_overlays(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    prereq = load_json(PREREQ)
    overlay = load_json(OVERLAY)
    binding = load_json(RECOVERED_BINDING)
    executed_pair_count = int(summary.get("executed_pair_count", 0))

    if prereq.get("schema_version") != "telos.provider_compatible_expanded_paid_retry.prerequisite_validation.v1":
        failures.append("unexpected prerequisite schema")
    if prereq.get("iter72_status") != "blocked" or prereq.get("iter72_blocked_result") is not True:
        failures.append("iter72 prerequisite must be a clean blocked packet")
    if prereq.get("iter72_receipt_validation_returncode") != 0:
        failures.append("iter72 receipt validation must pass")
    if prereq.get("iter72_audit_returncode") != 0:
        failures.append("iter72 audit must pass")
    if prereq.get("iter73_status") != "pass" or prereq.get("iter73_clean_pass") is not True:
        failures.append("iter73 prerequisite must be a clean recovery pass")
    if prereq.get("iter73_receipt_validation_returncode") != 0:
        failures.append("iter73 receipt validation must pass")
    if prereq.get("iter73_audit_returncode") != 0:
        failures.append("iter73 audit must pass")
    if prereq.get("iter74_status") != "blocked" or prereq.get("iter74_blocked_result") is not True:
        failures.append("iter74 prerequisite must be a clean no-row blocked packet")
    if int(prereq.get("iter74_executed_pair_count", -1)) != 0:
        failures.append("iter74 prerequisite must have zero executed pairs")
    if int(prereq.get("iter74_provider_api_calls", -1)) != 0:
        failures.append("iter74 prerequisite must have zero provider calls")
    if float(prereq.get("iter74_provider_cost_usd", -1.0)) != 0.0:
        failures.append("iter74 prerequisite must have zero provider cost")
    if prereq.get("iter74_receipt_validation_returncode") != 0:
        failures.append("iter74 receipt validation must pass")
    if prereq.get("iter74_audit_returncode") != 0:
        failures.append("iter74 audit must pass")
    if prereq.get("iter77_status") != "pass" or prereq.get("iter77_clean_pass") is not True:
        failures.append("iter77 prerequisite must be a clean ADC readiness pass")
    if prereq.get("iter77_adc_access_token_available") is not True:
        failures.append("iter77 prerequisite must prove ADC token availability")
    if int(prereq.get("iter77_provider_model_calls", -1)) != 0:
        failures.append("iter77 prerequisite must have zero provider calls")
    if float(prereq.get("iter77_provider_spend_usd", -1.0)) != 0.0:
        failures.append("iter77 prerequisite must have zero provider spend")
    if prereq.get("iter77_receipt_validation_returncode") != 0:
        failures.append("iter77 receipt validation must pass")
    if prereq.get("iter77_audit_returncode") != 0:
        failures.append("iter77 audit must pass")
    if prereq.get("clean_prerequisites") is not True:
        failures.append("clean prerequisites flag must be true for paid retry")

    if binding.get("schema_version") != (
        "telos.provider_compatible_expanded_paid_retry.recovered_prompt_overlay_binding.v1"
    ):
        failures.append("unexpected recovered overlay binding schema")
    if (
        executed_pair_count
        and binding.get("all_required_recovered_overlays_materialized") is not True
    ):
        failures.append("recovered iter73 prompt overlays must be materialized")
    bindings = {item.get("pair_id"): item for item in binding.get("bindings", [])}
    if set(bindings) != set(EXPECTED_RECOVERED_SOURCES):
        failures.append("recovered overlay binding pair ids changed")
    for pair_id, source in EXPECTED_RECOVERED_SOURCES.items():
        item = bindings.get(pair_id, {})
        if item.get("source") != source:
            failures.append(f"{pair_id} recovered overlay source changed")
        if executed_pair_count and (
            item.get("copied_or_written") is not True or item.get("hash_match") is not True
        ):
            failures.append(f"{pair_id} recovered overlay was not copied with matching hash")
        source_path = Path(source)
        if source_path.exists() and item.get("source_sha256") != sha256(source_path):
            failures.append(f"{pair_id} recovered overlay source hash mismatch")

    if executed_pair_count and overlay.get("iter73_recovered_prompt_overlays_all_materialized") is not True:
        failures.append("overlay manifest must confirm iter73 recovered prompts")
    copy_sources = {
        item.get("source"): item
        for item in overlay.get("copies", [])
        if isinstance(item, dict)
    }
    for source in EXPECTED_RECOVERED_SOURCES.values():
        copy = copy_sources.get(source, {})
        if executed_pair_count and copy.get("materialization") != "copied_iter73_recovered_receipt_prompt_overlay":
            failures.append(f"overlay manifest missing iter73 materialization for {source}")


def audit_summary_report_preflight(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    report = load_json(REPORT)
    preflight = load_json(PREFLIGHT)

    expected_schemas = {
        "summary": (
            summary,
            "telos.provider_compatible_expanded_paid_retry_after_adc_recovery.summary.v1",
        ),
        "report": (
            report,
            "telos.provider_compatible_expanded_paid_retry_after_adc_recovery.report.v1",
        ),
        "preflight": (
            preflight,
            "telos.provider_compatible_expanded_paid_retry_after_adc_recovery.preflight.v1",
        ),
    }
    for name, (packet, expected_schema) in expected_schemas.items():
        if packet.get("schema_version") != expected_schema:
            failures.append(f"unexpected {name} schema")
        if packet.get("experiment_id") not in {None, EXPERIMENT.name}:
            failures.append(f"{name} experiment id mismatch")

    status = summary.get("status")
    if status not in {"pass", "blocked", "fail"}:
        failures.append(f"unexpected summary status {status!r}")
    if report.get("status") != status:
        failures.append("summary/report status mismatch")
    if summary.get("clean_pass") is not (status == "pass"):
        failures.append("summary clean_pass/status mismatch")
    if summary.get("blocked_result") is not (status == "blocked"):
        failures.append("summary blocked_result/status mismatch")
    if summary.get("quality_failure") is not (status == "fail"):
        failures.append("summary quality_failure/status mismatch")
    if status == "fail" and not summary.get("failures"):
        failures.append("fail status must name at least one failure")
    if status == "blocked" and not summary.get("blockers"):
        failures.append("blocked status must name at least one blocker")
    if status == "pass" and (summary.get("blockers") or summary.get("failures")):
        failures.append("pass status must have no blockers or failures")

    for packet_name, packet in [("summary", summary), ("report", report)]:
        for key in [
            "gpu_used",
            "cloud_runner_started",
            "sentinel_named_resources_modified",
            "production_or_live_domain_changed",
            "benchmark_result_claimed",
            "leaderboard_or_swebench_result_claimed",
            "model_superiority_claimed",
            "state_of_the_art_result_claimed",
            "cross_task_surface_pooling_authorized",
            "aggregate_benchmark_or_model_claim_authorized",
        ]:
            if key in packet and packet.get(key) is not False:
                failures.append(f"{packet_name} {key} must be false")
        if packet.get("selected_pair_ids") != EXPECTED_SELECTED_PAIR_IDS:
            failures.append(f"{packet_name} selected pair ids changed")
        if packet.get("retained_existing_pair_ids") != EXPECTED_RETAINED_PAIR_IDS:
            failures.append(f"{packet_name} retained pair ids changed")
        if packet.get("provider_call_ceiling") != 32:
            failures.append(f"{packet_name} provider call ceiling changed")
        if float(packet.get("provider_spend_ceiling_usd", -1.0)) != 10.0:
            failures.append(f"{packet_name} provider spend ceiling changed")
        if int(packet.get("provider_api_calls", 10**9)) > 32:
            failures.append(f"{packet_name} provider call ceiling exceeded")
        if float(packet.get("provider_cost_usd", 10**9)) > 10.0:
            failures.append(f"{packet_name} provider spend ceiling exceeded")
        if packet.get("executed_pair_count", 0) and packet.get(
            "receipt_enforced_rows_used_iter73_recovered_overlays"
        ) is not True:
            failures.append(f"{packet_name} must prove iter73 recovered overlays were used")

    if preflight.get("selected_pair_ids") != EXPECTED_SELECTED_PAIR_IDS:
        failures.append("preflight selected pair ids changed")
    if preflight.get("retained_existing_pair_ids") != EXPECTED_RETAINED_PAIR_IDS:
        failures.append("preflight retained pair ids changed")
    for key in [
        "iter72_receipt_validation_returncode",
        "iter72_audit_returncode",
        "iter73_receipt_validation_returncode",
        "iter73_audit_returncode",
        "iter74_receipt_validation_returncode",
        "iter74_audit_returncode",
        "iter77_receipt_validation_returncode",
        "iter77_audit_returncode",
    ]:
        if summary.get(key) != 0 or report.get(key) != 0 or preflight.get(key) != 0:
            failures.append(f"{key} must be zero in all machine-readable packets")
    if summary.get("iter72_status") != "blocked" or report.get("iter72_status") != "blocked":
        failures.append("iter72 status must stay blocked")
    if summary.get("iter73_status") != "pass" or report.get("iter73_status") != "pass":
        failures.append("iter73 status must stay pass")
    if summary.get("iter74_status") != "blocked" or report.get("iter74_status") != "blocked":
        failures.append("iter74 status must stay blocked")
    if int(summary.get("iter74_executed_pair_count", -1)) != 0:
        failures.append("iter74 executed pair count must stay zero")
    if summary.get("iter77_status") != "pass" or report.get("iter77_status") != "pass":
        failures.append("iter77 status must stay pass")
    if summary.get("iter77_adc_access_token_available") is not True:
        failures.append("iter77 ADC availability must stay true")

    row_results = report.get("row_results", [])
    if summary.get("executed_pair_ids") != report.get("executed_pair_ids"):
        failures.append("summary/report executed pair ids mismatch")
    if summary.get("executed_pair_count") != len(row_results):
        failures.append("summary executed pair count mismatch")
    if row_results and summary.get("executed_pair_ids") != EXPECTED_SELECTED_PAIR_IDS:
        failures.append("executed pair ids must equal the four selected rows")
    if len(row_results) not in {0, 4}:
        failures.append("iter78 must either block before execution or execute exactly four rows")

    rows = {row.get("pair_id"): row for row in row_results if isinstance(row, dict)}
    if row_results and list(rows) != EXPECTED_SELECTED_PAIR_IDS:
        failures.append("row result order changed")
    for pair_id, row in rows.items():
        if row.get("provider_api_calls", 10**9) > 8:
            failures.append(f"{pair_id} exceeded per-row call limit")
        if float(row.get("provider_cost_usd", 10**9)) > 2.5:
            failures.append(f"{pair_id} exceeded per-row spend limit")
        if row.get("raw_evidence_present") is not True:
            failures.append(f"{pair_id} must preserve raw evidence")
        raw_dir = RAW / pair_id
        for required in [
            "command_execution.json",
            "command_stdout.txt",
            "command_stderr.txt",
            "raw_manifest.json",
            "metadata.json",
        ]:
            if not (raw_dir / required).exists():
                failures.append(f"{pair_id} missing raw artifact {required}")
        if pair_id in RECEIPT_REQUIRED_PAIR_IDS:
            if row.get("receipt_required") is not True:
                failures.append(f"{pair_id} must require receipt")
            if status == "pass" and row.get("receipt_valid") is not True:
                failures.append(f"{pair_id} must have valid receipt for pass status")
        elif row.get("receipt_required") is not False:
            failures.append(f"{pair_id} should not require receipt")

    expected_metric = expected_primary_metric(rows)
    if summary.get("primary_metric") != expected_metric:
        failures.append("summary primary metric is inconsistent with row results")
    if report.get("primary_metric") != expected_metric:
        failures.append("report primary metric is inconsistent with row results")
    if summary.get("redaction_scan_passed") is not True or summary.get("redaction_findings") != []:
        failures.append("summary redaction scan must pass with no findings")
    if report.get("redaction_scan_passed") is not True or report.get("redaction_findings") != []:
        failures.append("report redaction scan must pass with no findings")

    for rel_path, expected_hash in summary.get("artifact_hashes", {}).items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"summary hash path missing: {rel_path}")
        elif sha256(path) != expected_hash:
            failures.append(f"summary hash mismatch: {rel_path}")


def audit_receipt_and_text(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
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
        "Iteration 78 Result",
        "recovered iter73 prompt overlays materialized",
        "benchmark/model/SOTA claim: `false`",
        "It is not a benchmark result",
        "state-of-the-art result",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "validating the",
        "iter73 recovered prompt overlays",
        "were not rerun",
        "Receipt validation was required",
        "No benchmark, SWE-bench, leaderboard",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "provider-compatible expanded paid retry after ADC recovery:",
        "iter72_receipt_validation_returncode=0",
        "iter72_audit_returncode=0",
        "iter73_receipt_validation_returncode=0",
        "iter73_audit_returncode=0",
        "iter74_receipt_validation_returncode=0",
        "iter74_audit_returncode=0",
        "iter77_receipt_validation_returncode=0",
        "iter77_audit_returncode=0",
        "iter77_adc_access_token_available=true",
        "provider_call_ceiling=32",
        "provider_spend_ceiling_usd=10.00",
    ]:
        if required not in command_output:
            failures.append(f"command output missing required line: {required}")
    materialization_line = "recovered_iter73_prompt_overlays_materialized="
    if materialization_line not in command_output:
        failures.append("command output missing recovered overlay materialization line")
    for forbidden in [
        "This is a benchmark result",
        "This is a state-of-the-art result",
        "This is a model-superiority result",
        "This is a leaderboard result",
        "Telos outperforms baseline",
    ]:
        if forbidden in result or forbidden in review:
            failures.append(f"claim boundary regression: {forbidden}")


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
        audit_prerequisites_and_overlays(failures)
        audit_summary_report_preflight(failures)
        audit_receipt_and_text(failures)
        audit_secrets(failures)
    if failures:
        print("iter78 provider-compatible expanded paid retry audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter78 provider-compatible expanded paid retry audit: clean artifact packet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
