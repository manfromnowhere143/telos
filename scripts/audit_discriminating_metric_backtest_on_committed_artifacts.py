#!/usr/bin/env python3
"""Audit iter86 discriminating metric backtest artifacts."""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter86_discriminating_metric_backtest_on_committed_artifacts")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
PREREQ = PROOF / "prerequisite_validation.json"
EXTRACTION = PROOF / "raw_metric_extraction.json"
BACKTEST = PROOF / "backtest_report.json"
DECISION = PROOF / "next_step_decision.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary.json"
REDACTION = PROOF / "redaction_scan.json"
RECEIPT = PROOF / "valid" / "receipt_discriminating_metric_backtest_on_committed_artifacts.json"
NEXT_GATE = Path("experiments/iter87_benchmark_facing_discriminating_metric_execution_pilot/HYPOTHESIS.md")
ITER85_PROOF = Path("experiments/iter85_discriminating_task_metric_redesign/proof")
ITER85_SUMMARY = ITER85_PROOF / "run_summary.json"
ITER85_METRIC = ITER85_PROOF / "metric_contract.json"
ITER85_FIELD_INVENTORY = ITER85_PROOF / "source_field_inventory.json"
ITER85_RECEIPT = ITER85_PROOF / "valid" / "receipt_discriminating_task_metric_redesign.json"
METRIC_ID = "task_native_score_share_delta_with_receipt_gates"
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
        EXTRACTION,
        BACKTEST,
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
    extraction = load_json(EXTRACTION)
    backtest = load_json(BACKTEST)
    decision = load_json(DECISION)
    boundary = load_json(CLAIM_BOUNDARY)
    redaction = load_json(REDACTION)
    expected_schemas = {
        "summary": (summary, "telos.discriminating_metric_backtest.summary.v1"),
        "prereq": (prereq, "telos.discriminating_metric_backtest.prerequisite_validation.v1"),
        "extraction": (extraction, "telos.discriminating_metric_backtest.raw_metric_extraction.v1"),
        "backtest": (backtest, "telos.discriminating_metric_backtest.report.v1"),
        "decision": (decision, "telos.discriminating_metric_backtest.next_step_decision.v1"),
        "boundary": (boundary, "telos.discriminating_metric_backtest.claim_boundary.v1"),
        "redaction": (redaction, "telos.discriminating_metric_backtest.redaction_scan.v1"),
    }
    for name, (packet, schema) in expected_schemas.items():
        if packet.get("schema_version") != schema:
            failures.append(f"unexpected {name} schema")
        if packet.get("experiment_id") != EXPERIMENT.name:
            failures.append(f"{name} experiment id mismatch")

    if summary.get("status") != "pass":
        failures.append("iter86 must pass as zero-spend backtest")
    if summary.get("clean_pass") is not True:
        failures.append("summary clean_pass must be true")
    if summary.get("blocked_result") is not False or summary.get("quality_failure") is not False:
        failures.append("summary blocked/quality flags must be false")
    if summary.get("blockers") != [] or summary.get("failures") != []:
        failures.append("pass summary must not contain blockers/failures")
    if summary.get("metric_id") != METRIC_ID:
        failures.append("summary metric changed")
    if summary.get("metric_computable") is not True:
        failures.append("metric must be computable")
    if summary.get("metric_collapsed_to_completion_boolean") is not False:
        failures.append("metric must not collapse to completion boolean")
    if summary.get("metric_non_saturated") is not True:
        failures.append("metric must be non-saturated")
    if summary.get("source_rows_parsed") != 6:
        failures.append("source rows parsed must be 6")
    if summary.get("task_deltas_computed") != 3:
        failures.append("task deltas computed must be 3")
    if summary.get("nonzero_task_delta_count", 0) < 1:
        failures.append("at least one task delta must be nonzero")
    if summary.get("next_step_decision") != "pre_register_bounded_paid_discriminating_metric_execution":
        failures.append("next-step decision changed")
    if summary.get("next_gate") != str(NEXT_GATE):
        failures.append("summary next gate changed")
    if summary.get("future_paid_execution_pre_registered") is not True:
        failures.append("future paid execution must be separately pre-registered")

    if prereq.get("clean_prerequisites") is not True:
        failures.append("iter85 prerequisites must be clean")
    if prereq.get("iter85_status") != "pass" or prereq.get("iter85_clean_pass") is not True:
        failures.append("iter85 status must be clean pass")
    if prereq.get("iter85_candidate_metric_id") != METRIC_ID:
        failures.append("iter85 metric id changed")
    if prereq.get("iter85_source_rows_inventoried") != 6:
        failures.append("iter85 source row inventory changed")
    if prereq.get("iter85_receipt_validation_returncode") != 0:
        failures.append("iter85 receipt validation must pass")
    if prereq.get("iter85_audit_returncode") != 0:
        failures.append("iter85 audit must pass")
    expected_hashes = {
        str(ITER85_SUMMARY): sha256(ITER85_SUMMARY),
        str(ITER85_METRIC): sha256(ITER85_METRIC),
        str(ITER85_FIELD_INVENTORY): sha256(ITER85_FIELD_INVENTORY),
        str(ITER85_RECEIPT): sha256(ITER85_RECEIPT),
    }
    by_path = {item.get("path"): item for item in prereq.get("source_artifacts", [])}
    for path, expected_hash in expected_hashes.items():
        if by_path.get(path, {}).get("sha256") != expected_hash:
            failures.append(f"iter85 source hash mismatch: {path}")

    if extraction.get("metric_id") != METRIC_ID:
        failures.append("extraction metric changed")
    if extraction.get("all_rows_parsed") is not True:
        failures.append("extraction must parse all rows")
    if extraction.get("metric_collapsed_to_completion_boolean") is not False:
        failures.append("extraction collapsed to completion boolean")
    if extraction.get("row_count") != 6:
        failures.append("extraction row count must be 6")
    if extraction.get("task_delta_count") != 3:
        failures.append("extraction task delta count must be 3")
    if len(extraction.get("rows", [])) != 6:
        failures.append("extraction rows length must be 6")
    if len(extraction.get("task_deltas", [])) != 3:
        failures.append("extraction task deltas length must be 3")
    for row in extraction.get("rows", []):
        if row.get("controlled_player") != "p1":
            failures.append(f"unexpected controlled player for {row.get('pair_id')}")
        metadata = Path(str(row.get("metadata_path")))
        if not metadata.exists():
            failures.append(f"metadata path missing: {metadata}")
        elif row.get("metadata_sha256") != sha256(metadata):
            failures.append(f"metadata hash mismatch: {metadata}")
        if decimal_value(row.get("all_player_score_total")) <= Decimal("0"):
            failures.append(f"nonpositive score total for {row.get('pair_id')}")
    task_set = {row.get("task_surface") for row in extraction.get("task_deltas", [])}
    if task_set != {"dummy", "battlesnake", "deterministic_edit"}:
        failures.append("task delta set changed")

    if backtest.get("metric_computable") is not True:
        failures.append("backtest must mark metric computable")
    if backtest.get("metric_non_saturated") is not True:
        failures.append("backtest must mark metric non-saturated")
    if "diagnostic only" not in backtest.get("interpretation", ""):
        failures.append("backtest interpretation must remain diagnostic")
    if decision.get("decision") != "pre_register_bounded_paid_discriminating_metric_execution":
        failures.append("decision packet changed")
    if decision.get("next_gate") != str(NEXT_GATE):
        failures.append("decision next gate changed")
    if decision.get("next_gate_pre_registered") is not True:
        failures.append("decision next gate must be pre-registered")
    accepted = decision.get("accepted_path", {})
    if accepted.get("future_provider_call_ceiling") != 96:
        failures.append("future provider call ceiling changed")
    if decimal_value(accepted.get("future_provider_spend_ceiling_usd")) != Decimal("10.00000000"):
        failures.append("future provider spend ceiling changed")

    for key in [
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "swebench_execution_or_score_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "production_or_live_domain_changed",
        "cross_task_surface_pooling_authorized",
        "aggregate_benchmark_metric_authorized",
        "fresh_paid_execution_claimed",
    ]:
        if boundary.get(key) is not False:
            failures.append(f"claim boundary {key} must be false")
        if key in summary and summary.get(key) is not False:
            failures.append(f"summary {key} must be false")
    for key in ["gpu_used", "cloud_runner_started", "sentinel_named_resources_modified"]:
        if summary.get(key) is not False:
            failures.append(f"summary {key} must be false")
    if summary.get("provider_api_calls") != 0:
        failures.append("iter86 provider calls must be zero")
    if decimal_value(summary.get("provider_cost_usd")) != Decimal("0"):
        failures.append("iter86 provider cost must be zero")
    if summary.get("row_execution_in_this_gate") != 0:
        failures.append("iter86 row execution must be zero")
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
        "metric: `task_native_score_share_delta_with_receipt_gates`",
        "provider calls in this gate: `0`",
        "provider spend in this gate: `$0.00000000`",
        "row execution in this gate: `0`",
        "next-step decision: `pre_register_bounded_paid_discriminating_metric_execution`",
        "not a benchmark result",
        "state-of-the-art result",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "committed iter83 metadata",
        "does not collapse back to the saturated verified-completion",
        "mixed-direction diagnostic evidence",
        "No benchmark,",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "discriminating metric backtest: pass",
        "provider_calls_in_this_gate=0",
        "provider_spend_in_this_gate_usd=0.00000000",
        "row_execution_in_this_gate=0",
        "metric_collapsed_to_completion_boolean=false",
        "next_step_decision=pre_register_bounded_paid_discriminating_metric_execution",
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
        print("iter86 discriminating metric backtest audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter86 discriminating metric backtest audit: clean pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
