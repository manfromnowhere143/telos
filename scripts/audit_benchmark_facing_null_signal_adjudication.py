#!/usr/bin/env python3
"""Audit iter84 benchmark-facing null-signal adjudication artifacts."""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter84_benchmark_facing_null_signal_adjudication")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
PREREQ = PROOF / "prerequisite_validation.json"
ROW_ACCOUNTING = PROOF / "row_accounting.json"
DELTA_TABLE = PROOF / "delta_table.json"
CLASSIFICATION = PROOF / "null_signal_classification.json"
DECISION = PROOF / "next_step_decision.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary.json"
REDACTION = PROOF / "redaction_scan.json"
RECEIPT = PROOF / "valid" / "receipt_benchmark_facing_null_signal_adjudication.json"
NEXT_GATE = Path("experiments/iter85_discriminating_task_metric_redesign/HYPOTHESIS.md")
ITER83_SUMMARY = Path(
    "experiments/iter83_benchmark_facing_protocol_effect_execution_pilot/proof/run_summary.json"
)
ITER83_REPORT = Path(
    "experiments/iter83_benchmark_facing_protocol_effect_execution_pilot/proof/protocol_effect_report.json"
)
ITER83_RECEIPT = Path(
    "experiments/iter83_benchmark_facing_protocol_effect_execution_pilot/proof/valid/"
    "receipt_benchmark_facing_protocol_effect_execution_pilot.json"
)
SELECTED_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-dummy-yaml",
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
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
        PREREQ,
        ROW_ACCOUNTING,
        DELTA_TABLE,
        CLASSIFICATION,
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


def audit_packets(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    prereq = load_json(PREREQ)
    rows = load_json(ROW_ACCOUNTING)
    delta = load_json(DELTA_TABLE)
    classification = load_json(CLASSIFICATION)
    decision = load_json(DECISION)
    boundary = load_json(CLAIM_BOUNDARY)
    redaction = load_json(REDACTION)
    expected_schemas = {
        "summary": (summary, "telos.benchmark_facing_null_signal.summary.v1"),
        "prereq": (prereq, "telos.benchmark_facing_null_signal.prerequisite_validation.v1"),
        "rows": (rows, "telos.benchmark_facing_null_signal.row_accounting.v1"),
        "delta": (delta, "telos.benchmark_facing_null_signal.delta_table.v1"),
        "classification": (
            classification,
            "telos.benchmark_facing_null_signal.classification.v1",
        ),
        "decision": (decision, "telos.benchmark_facing_null_signal.next_step_decision.v1"),
        "boundary": (boundary, "telos.benchmark_facing_null_signal.claim_boundary.v1"),
        "redaction": (redaction, "telos.benchmark_facing_null_signal.redaction_scan.v1"),
    }
    for name, (packet, schema) in expected_schemas.items():
        if packet.get("schema_version") != schema:
            failures.append(f"unexpected {name} schema")
        if packet.get("experiment_id") != EXPERIMENT.name:
            failures.append(f"{name} experiment id mismatch")

    if summary.get("status") != "pass":
        failures.append("iter84 must pass as zero-spend adjudication")
    if summary.get("clean_pass") is not True:
        failures.append("summary clean_pass must be true")
    if summary.get("blocked_result") is not False or summary.get("quality_failure") is not False:
        failures.append("summary blocked/quality flags must be false")
    if summary.get("blockers") != [] or summary.get("failures") != []:
        failures.append("pass summary must not contain blockers/failures")

    if prereq.get("clean_prerequisites") is not True:
        failures.append("iter83 prerequisites must be clean")
    if prereq.get("iter83_status") != "blocked":
        failures.append("iter83 status must remain blocked")
    if prereq.get("iter83_null_result") is not True:
        failures.append("iter83 null result must remain true")
    if prereq.get("iter83_blockers") != ["no_interpretable_telos_minus_baseline_signal"]:
        failures.append("iter83 no-signal blocker changed")
    if prereq.get("iter83_failures") != []:
        failures.append("iter83 failures must be empty")
    if prereq.get("iter83_executed_pair_count") != 6:
        failures.append("iter83 executed row count changed")
    if prereq.get("iter83_provider_api_calls") != 21:
        failures.append("iter83 provider call count changed")
    if decimal_value(prereq.get("iter83_provider_cost_usd")) != Decimal("0.11319400"):
        failures.append("iter83 provider cost changed")
    if prereq.get("iter83_receipt_validation_returncode") != 0:
        failures.append("iter83 receipt validation must pass")
    if prereq.get("iter83_audit_returncode") != 0:
        failures.append("iter83 audit must pass")
    by_path = {item.get("path"): item for item in prereq.get("source_artifacts", [])}
    for path in [ITER83_SUMMARY, ITER83_REPORT, ITER83_RECEIPT]:
        if by_path.get(str(path), {}).get("sha256") != sha256(path):
            failures.append(f"iter83 source hash mismatch: {path}")

    if rows.get("selected_pair_ids") != SELECTED_PAIR_IDS:
        failures.append("selected pair ids changed")
    if rows.get("executed_pair_ids") != SELECTED_PAIR_IDS:
        failures.append("executed pair ids changed")
    if rows.get("executed_pair_count") != 6:
        failures.append("row accounting executed count changed")
    if rows.get("all_rows_verified_completion") is not True:
        failures.append("iter83 all-row completion evidence must be true")
    if rows.get("all_required_receipts_valid") is not True:
        failures.append("iter83 required receipts must be valid")
    if rows.get("all_raw_evidence_present") is not True:
        failures.append("iter83 raw evidence must be present")
    if rows.get("provider_calls_in_this_gate") != 0:
        failures.append("iter84 provider calls must be zero in row accounting")
    if decimal_value(rows.get("provider_spend_in_this_gate_usd")) != Decimal("0"):
        failures.append("iter84 provider spend must be zero in row accounting")
    if rows.get("row_execution_in_this_gate") != 0:
        failures.append("iter84 must not execute rows")

    deltas = delta.get("deltas", [])
    if len(deltas) != 3:
        failures.append("delta table must contain three task surfaces")
    if delta.get("all_task_surface_deltas_zero") is not True:
        failures.append("delta table must preserve all-zero result")
    if delta.get("interpretable_protocol_effect_signal") is not False:
        failures.append("delta table must not claim interpretable signal")
    if delta.get("aggregate_benchmark_metric_authorized") is not False:
        failures.append("delta table must not authorize aggregate benchmark metric")
    for row in deltas:
        if row.get("baseline_verified_completion_evidence") is not True:
            failures.append(f"{row.get('task_surface')} baseline verification changed")
        if row.get("telos_verified_completion_evidence") is not True:
            failures.append(f"{row.get('task_surface')} Telos verification changed")
        if row.get("delta_telos_minus_baseline") != 0:
            failures.append(f"{row.get('task_surface')} delta must be zero")

    if classification.get("classification") != "verified_completion_metric_saturated":
        failures.append("null classification changed")
    if classification.get("null_signal_preserved") is not True:
        failures.append("null signal must be preserved")
    if classification.get("no_signal_blocker_preserved") != (
        "no_interpretable_telos_minus_baseline_signal"
    ):
        failures.append("no-signal blocker preservation changed")
    if decision.get("decision") != "redesign_task_metric":
        failures.append("next-step decision changed")
    if decision.get("next_gate") != str(NEXT_GATE):
        failures.append("next gate changed")
    if decision.get("next_gate_pre_registered") is not True:
        failures.append("next gate must be pre-registered")

    for key in [
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "swebench_execution_or_score_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "production_or_live_domain_changed",
        "cross_task_surface_pooling_authorized",
        "aggregate_benchmark_metric_authorized",
    ]:
        if boundary.get(key) is not False:
            failures.append(f"claim boundary {key} must be false")
        if key in summary and summary.get(key) is not False:
            failures.append(f"summary {key} must be false")
    for key in ["gpu_used", "cloud_runner_started", "sentinel_named_resources_modified"]:
        if summary.get(key) is not False:
            failures.append(f"summary {key} must be false")
    if summary.get("provider_api_calls") != 0:
        failures.append("iter84 provider calls must be zero")
    if decimal_value(summary.get("provider_cost_usd")) != Decimal("0"):
        failures.append("iter84 provider cost must be zero")
    if summary.get("row_execution_in_this_gate") != 0:
        failures.append("iter84 row execution must be zero")
    if summary.get("next_gate") != str(NEXT_GATE):
        failures.append("summary next gate changed")
    if summary.get("redaction_scan_passed") is not True or summary.get("redaction_findings") != []:
        failures.append("summary redaction scan must pass")
    if redaction.get("passed") is not True or redaction.get("findings") != []:
        failures.append("redaction scan packet must pass")

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
        "Status: `PASS`.",
        "provider calls in this gate: `0`",
        "provider spend in this gate: `$0.00000000`",
        "row execution in this gate: `0`",
        "classification: `verified_completion_metric_saturated`",
        "next-step decision: `redesign_task_metric`",
        "benchmark/model/SOTA claim: `false`",
        "not a benchmark result",
        "state-of-the-art result",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "real null evidence",
        "zero-spend task/metric redesign",
        "No benchmark, leaderboard, SWE-bench",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "benchmark-facing null-signal adjudication: pass",
        "provider_calls_in_this_gate=0",
        "provider_spend_in_this_gate_usd=0.00000000",
        "row_execution_in_this_gate=0",
        "classification=verified_completion_metric_saturated",
        "next_step_decision=redesign_task_metric",
    ]:
        if required not in command_output:
            failures.append(f"command_output.txt missing required text: {required}")
    for forbidden in [
        "This is a benchmark result",
        "This is a state-of-the-art result",
        "This is a model-superiority result",
        "This is a leaderboard result",
        "Telos is SOTA",
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
        print("iter84 benchmark-facing null-signal adjudication audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter84 benchmark-facing null-signal adjudication audit: clean pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
