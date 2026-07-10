#!/usr/bin/env python3
"""Audit iter80 Dummy-only bounded paid-retry artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery")
PROOF = EXPERIMENT / "proof"
RAW = PROOF / "raw"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
REPORT = PROOF / "protocol_effect_report.json"
PREFLIGHT = PROOF / "preflight.json"
PREREQ = PROOF / "prerequisite_validation.json"
OVERLAY = PROOF / "overlay_materialization_manifest.json"
BINDING = PROOF / "call_ceiling_overlay_binding.json"
RECOVERED = PROOF / "recovered_agent_overlay_manifest.json"
RECEIPT = PROOF / "valid" / "receipt_dummy_call_ceiling_bounded_paid_retry_after_recovery.json"
ITER79_SUMMARY = Path("experiments/iter79_dummy_row_call_ceiling_recovery_after_paid_retry_block/proof/run_summary.json")
ITER79_PLAN = Path("experiments/iter79_dummy_row_call_ceiling_recovery_after_paid_retry_block/proof/recovery_plan.json")
DUMMY_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-dummy-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
]
DETERMINISTIC_EDIT_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
]
BATTLESNAKE_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
]
PER_ROW_CALL_LIMIT = 16
TOTAL_CALL_CEILING = 32
PER_ROW_SPEND_LIMIT_USD = 2.5
TOTAL_SPEND_CEILING_USD = 5.0
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
        BINDING,
        RECOVERED,
        PROOF / "runtime_access_path_binding.json",
        PROOF / "runtime_access_path_model_config.yaml",
        PROOF / "command_output.txt",
        PROOF / "review.md",
        PROOF / "learning_record.json",
        RECEIPT,
    ]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")


def audit_packets(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    report = load_json(REPORT)
    preflight = load_json(PREFLIGHT)
    prereq = load_json(PREREQ)
    overlay = load_json(OVERLAY)
    binding = load_json(BINDING)
    recovered = load_json(RECOVERED)
    iter79_summary = load_json(ITER79_SUMMARY)
    iter79_plan = load_json(ITER79_PLAN)

    expected_schemas = {
        "summary": (summary, "telos.dummy_call_ceiling_bounded_paid_retry.summary.v1"),
        "report": (report, "telos.dummy_call_ceiling_bounded_paid_retry.report.v1"),
        "preflight": (preflight, "telos.dummy_call_ceiling_bounded_paid_retry.preflight.v1"),
        "prereq": (prereq, "telos.dummy_call_ceiling_bounded_paid_retry.prerequisite_validation.v1"),
        "binding": (binding, "telos.dummy_call_ceiling_bounded_paid_retry.call_ceiling_overlay_binding.v1"),
        "recovered": (recovered, "telos.dummy_call_ceiling_bounded_paid_retry.recovered_agent_overlays.v1"),
        "overlay": (overlay, "telos.dummy_call_ceiling_bounded_paid_retry.overlay_materialization.v1"),
    }
    for name, (packet, schema) in expected_schemas.items():
        if packet.get("schema_version") != schema:
            failures.append(f"unexpected {name} schema")
        if packet.get("experiment_id") not in {None, EXPERIMENT.name}:
            failures.append(f"{name} experiment id mismatch")

    status = summary.get("status")
    if status not in {"pass", "blocked", "fail"}:
        failures.append(f"invalid status: {status!r}")
        return
    if report.get("status") != status:
        failures.append("summary/report status mismatch")
    if summary.get("clean_pass") is not (status == "pass"):
        failures.append("clean_pass/status mismatch")
    if summary.get("blocked_result") is not (status == "blocked"):
        failures.append("blocked_result/status mismatch")
    if summary.get("quality_failure") is not (status == "fail"):
        failures.append("quality_failure/status mismatch")
    if status == "pass" and (summary.get("blockers") or summary.get("failures")):
        failures.append("pass status must not have blockers or failures")
    if status == "blocked" and not summary.get("blockers"):
        failures.append("blocked status must name blockers")
    if status == "fail" and not summary.get("failures"):
        failures.append("fail status must name failures")

    if prereq.get("clean_prerequisites") is not True:
        failures.append("iter79 prerequisites must be clean")
    if prereq.get("iter79_status") != "pass":
        failures.append("iter79 must be a pass prerequisite")
    if prereq.get("iter79_receipt_validation_returncode") != 0:
        failures.append("iter79 receipt validation must pass")
    if prereq.get("iter79_audit_returncode") != 0:
        failures.append("iter79 audit must pass")
    if prereq.get("source_iter79_summary_sha256") != sha256(ITER79_SUMMARY):
        failures.append("iter79 summary hash mismatch")
    if prereq.get("source_iter79_recovery_plan_sha256") != sha256(ITER79_PLAN):
        failures.append("iter79 recovery plan hash mismatch")
    if iter79_summary.get("next_gate") != f"experiments/{EXPERIMENT.name}/HYPOTHESIS.md":
        failures.append("iter79 next gate mismatch")
    if iter79_plan.get("selected_pair_ids") != DUMMY_PAIR_IDS:
        failures.append("iter79 selected pair ids changed")

    if recovered.get("all_recovered_step_limits_written") is not True:
        failures.append("recovered step limits must be written")
    generated = recovered.get("generated", [])
    if len(generated) != 2:
        failures.append("expected two recovered Dummy agent overlays")
    for item in generated:
        if item.get("previous_step_limit") != 8:
            failures.append("previous recovered step limit must be 8")
        if item.get("recovered_step_limit") != PER_ROW_CALL_LIMIT:
            failures.append("recovered step limit must be 16")
        destination = Path(str(item.get("destination", "")))
        if not destination.exists():
            failures.append(f"missing recovered overlay destination: {destination}")
        elif item.get("destination_sha256") != sha256(destination):
            failures.append(f"recovered overlay hash mismatch: {destination}")
        if "step_limit: 16" not in destination.read_text(encoding="utf-8"):
            failures.append(f"recovered overlay missing step_limit 16: {destination}")

    if binding.get("all_required_call_ceiling_overlays_materialized") is not True:
        failures.append("call-ceiling overlays must be materialized")
    bindings = {
        item.get("pair_id"): item
        for item in binding.get("bindings", [])
        if isinstance(item, dict)
    }
    if set(bindings) != set(DUMMY_PAIR_IDS):
        failures.append("call-ceiling binding pair set changed")
    for pair_id, item in bindings.items():
        if item.get("recovered_step_limit") != PER_ROW_CALL_LIMIT:
            failures.append(f"{pair_id} recovered step limit must be 16")
        if item.get("copied_or_written") is not True or item.get("hash_match") is not True:
            failures.append(f"{pair_id} call-ceiling overlay copy must match")

    for packet_name, packet in [("summary", summary), ("report", report), ("preflight", preflight)]:
        if packet.get("selected_pair_ids") != DUMMY_PAIR_IDS:
            failures.append(f"{packet_name} selected pair ids changed")
        if packet.get("provider_call_ceiling") != TOTAL_CALL_CEILING:
            failures.append(f"{packet_name} provider call ceiling changed")
        if float(packet.get("provider_spend_ceiling_usd", -1.0)) != TOTAL_SPEND_CEILING_USD:
            failures.append(f"{packet_name} provider spend ceiling changed")
        if packet.get("per_row_call_limit") != PER_ROW_CALL_LIMIT:
            failures.append(f"{packet_name} per-row call limit changed")
        if float(packet.get("per_row_spend_limit_usd", -1.0)) != PER_ROW_SPEND_LIMIT_USD:
            failures.append(f"{packet_name} per-row spend limit changed")
    if summary.get("deterministic_edit_pair_ids_retained_not_rerun") != DETERMINISTIC_EDIT_PAIR_IDS:
        failures.append("deterministic-edit retained pair ids changed")
    if summary.get("retained_battlesnake_pair_ids_not_rerun") != BATTLESNAKE_PAIR_IDS:
        failures.append("BattleSnake retained pair ids changed")
    if summary.get("executed_pair_count") not in {0, 2}:
        failures.append("executed pair count must be 0 preflight block or 2")
    if set(summary.get("executed_pair_ids", [])) - set(DUMMY_PAIR_IDS):
        failures.append("unselected row executed")
    if summary.get("executed_pair_count") == 2 and set(summary.get("executed_pair_ids", [])) != set(DUMMY_PAIR_IDS):
        failures.append("executed pair ids must be exactly Dummy rows")
    if int(summary.get("provider_api_calls", 0)) > TOTAL_CALL_CEILING:
        failures.append("provider call ceiling exceeded")
    if float(summary.get("provider_cost_usd", 0.0)) > TOTAL_SPEND_CEILING_USD:
        failures.append("provider spend ceiling exceeded")

    row_results = report.get("row_results", [])
    if len(row_results) != summary.get("executed_pair_count"):
        failures.append("row result count mismatch")
    for row in row_results:
        pair_id = row.get("pair_id")
        if pair_id not in DUMMY_PAIR_IDS:
            failures.append(f"unexpected row result: {pair_id}")
        if int(row.get("provider_api_calls", 0)) > PER_ROW_CALL_LIMIT:
            failures.append(f"{pair_id} per-row call ceiling exceeded")
        if float(row.get("provider_cost_usd", 0.0)) > PER_ROW_SPEND_LIMIT_USD:
            failures.append(f"{pair_id} per-row spend ceiling exceeded")
        if row.get("receipt_required") is True and row.get("receipt_valid") is not True:
            if f"{pair_id}_receipt_not_valid" not in summary.get("blockers", []):
                failures.append(f"{pair_id} invalid receipt must be a blocker")
        raw_dir = RAW / str(pair_id)
        if not raw_dir.exists():
            failures.append(f"raw directory missing for {pair_id}")
    if status == "pass":
        metric = summary.get("primary_metric", {})
        if metric.get("dummy_baseline_verified_completion_evidence") is not True:
            failures.append("pass requires Dummy baseline verified evidence")
        if metric.get("dummy_telos_verified_completion_evidence") is not True:
            failures.append("pass requires Dummy Telos verified evidence")

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
        if summary.get(key) is not False:
            failures.append(f"summary {key} must be false")
    if summary.get("redaction_scan_passed") is not True or summary.get("redaction_findings") != []:
        failures.append("summary redaction scan must pass")

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
        failures.append("receipt status mismatch")
    result = RESULT.read_text(encoding="utf-8")
    review = (PROOF / "review.md").read_text(encoding="utf-8")
    command_output = (PROOF / "command_output.txt").read_text(encoding="utf-8")
    for required in [
        "Iteration 80 Result",
        "per-row provider call ceiling: `16`",
        "provider call ceiling: `32`",
        "provider spend ceiling: `$5.00`",
        "state-of-the-art result",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "executed only the two Dummy adapter rows",
        "Deterministic-edit rows and retained BattleSnake",
        "No benchmark, SWE-bench, leaderboard",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "dummy call-ceiling bounded paid retry:",
        "selected_pair_count=2",
        "deterministic_edit_rows_rerun=false",
        "retained_battlesnake_rows_rerun=false",
        "per_row_call_limit=16",
        "provider_call_ceiling=32",
        "provider_spend_ceiling_usd=5.00",
    ]:
        if required not in command_output:
            failures.append(f"command_output.txt missing required line: {required}")
    for forbidden in [
        "This is a benchmark result",
        "This is a state-of-the-art result",
        "This is a model-superiority result",
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
        audit_packets(failures)
        audit_receipt_and_text(failures)
        audit_secrets(failures)
    if failures:
        print("iter80 Dummy call-ceiling bounded paid retry audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter80 Dummy call-ceiling bounded paid retry audit: clean artifact packet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
