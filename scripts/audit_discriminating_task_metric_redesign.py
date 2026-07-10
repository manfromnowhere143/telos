#!/usr/bin/env python3
"""Audit iter85 discriminating task/metric redesign artifacts."""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter85_discriminating_task_metric_redesign")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
PREREQ = PROOF / "prerequisite_validation.json"
CRITIQUE = PROOF / "saturation_critique.json"
FIELD_INVENTORY = PROOF / "source_field_inventory.json"
METRIC = PROOF / "metric_contract.json"
TASK_RULES = PROOF / "task_eligibility_rules.json"
FUTURE_PLAN = PROOF / "future_gate_plan.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary.json"
REDACTION = PROOF / "redaction_scan.json"
RECEIPT = PROOF / "valid" / "receipt_discriminating_task_metric_redesign.json"
NEXT_GATE = Path("experiments/iter86_discriminating_metric_backtest_on_committed_artifacts/HYPOTHESIS.md")
ITER84_PROOF = Path("experiments/iter84_benchmark_facing_null_signal_adjudication/proof")
ITER84_SUMMARY = ITER84_PROOF / "run_summary.json"
ITER84_CLASSIFICATION = ITER84_PROOF / "null_signal_classification.json"
ITER84_DECISION = ITER84_PROOF / "next_step_decision.json"
ITER84_ROW_ACCOUNTING = ITER84_PROOF / "row_accounting.json"
ITER84_RECEIPT = ITER84_PROOF / "valid" / "receipt_benchmark_facing_null_signal_adjudication.json"
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
        CRITIQUE,
        FIELD_INVENTORY,
        METRIC,
        TASK_RULES,
        FUTURE_PLAN,
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


def audit_prereq(prereq: dict, failures: list[str]) -> None:
    if prereq.get("schema_version") != "telos.discriminating_task_metric.prerequisite_validation.v1":
        failures.append("unexpected prereq schema")
    if prereq.get("experiment_id") != EXPERIMENT.name:
        failures.append("prereq experiment id mismatch")
    if prereq.get("clean_prerequisites") is not True:
        failures.append("iter84 prerequisites must be clean")
    expected_values = {
        "iter84_status": "pass",
        "iter84_clean_pass": True,
        "iter84_classification": "verified_completion_metric_saturated",
        "iter84_next_step_decision": "redesign_task_metric",
        "iter84_all_task_surface_deltas_zero": True,
        "iter84_provider_api_calls": 0,
        "iter84_row_execution_in_gate": 0,
        "iter84_receipt_validation_returncode": 0,
        "iter84_audit_returncode": 0,
        "provider_calls_in_this_gate": 0,
        "row_execution_in_this_gate": 0,
    }
    for key, expected in expected_values.items():
        if prereq.get(key) != expected:
            failures.append(f"prereq {key} changed")
    if decimal_value(prereq.get("iter84_provider_cost_usd")) != Decimal("0"):
        failures.append("iter84 provider cost must be zero")
    if decimal_value(prereq.get("provider_spend_in_this_gate_usd")) != Decimal("0"):
        failures.append("iter85 prereq spend must be zero")
    expected_hashes = {
        str(ITER84_SUMMARY): sha256(ITER84_SUMMARY),
        str(ITER84_CLASSIFICATION): sha256(ITER84_CLASSIFICATION),
        str(ITER84_DECISION): sha256(ITER84_DECISION),
        str(ITER84_ROW_ACCOUNTING): sha256(ITER84_ROW_ACCOUNTING),
        str(ITER84_RECEIPT): sha256(ITER84_RECEIPT),
    }
    by_path = {item.get("path"): item for item in prereq.get("source_artifacts", [])}
    for path, expected_hash in expected_hashes.items():
        if by_path.get(path, {}).get("sha256") != expected_hash:
            failures.append(f"iter84 source hash mismatch: {path}")
    for command in prereq.get("command_results", []):
        if command.get("returncode") != 0 or command.get("timed_out") is not False:
            failures.append(f"prereq command failed: {command.get('command')}")


def audit_packets(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    prereq = load_json(PREREQ)
    critique = load_json(CRITIQUE)
    field_inventory = load_json(FIELD_INVENTORY)
    metric = load_json(METRIC)
    task_rules = load_json(TASK_RULES)
    future_plan = load_json(FUTURE_PLAN)
    boundary = load_json(CLAIM_BOUNDARY)
    redaction = load_json(REDACTION)
    expected_schemas = {
        "summary": (summary, "telos.discriminating_task_metric.summary.v1"),
        "prereq": (prereq, "telos.discriminating_task_metric.prerequisite_validation.v1"),
        "critique": (critique, "telos.discriminating_task_metric.saturation_critique.v1"),
        "field_inventory": (
            field_inventory,
            "telos.discriminating_task_metric.source_field_inventory.v1",
        ),
        "metric": (metric, "telos.discriminating_task_metric.metric_contract.v1"),
        "task_rules": (task_rules, "telos.discriminating_task_metric.task_eligibility.v1"),
        "future_plan": (future_plan, "telos.discriminating_task_metric.future_gate_plan.v1"),
        "boundary": (boundary, "telos.discriminating_task_metric.claim_boundary.v1"),
        "redaction": (redaction, "telos.discriminating_task_metric.redaction_scan.v1"),
    }
    for name, (packet, schema) in expected_schemas.items():
        if packet.get("schema_version") != schema:
            failures.append(f"unexpected {name} schema")
        if packet.get("experiment_id") != EXPERIMENT.name:
            failures.append(f"{name} experiment id mismatch")

    audit_prereq(prereq, failures)

    if summary.get("status") != "pass":
        failures.append("iter85 must pass as zero-spend redesign")
    if summary.get("clean_pass") is not True:
        failures.append("summary clean_pass must be true")
    if summary.get("blocked_result") is not False or summary.get("quality_failure") is not False:
        failures.append("summary blocked/quality flags must be false")
    if summary.get("blockers") != [] or summary.get("failures") != []:
        failures.append("pass summary must not contain blockers/failures")
    if summary.get("candidate_metric_id") != METRIC_ID:
        failures.append("summary candidate metric changed")
    if summary.get("candidate_metric_not_verified_completion_boolean") is not True:
        failures.append("summary metric must not be completion boolean")
    if summary.get("candidate_metric_field_available_for_all_rows") is not True:
        failures.append("candidate metric fields must be available for all rows")
    if summary.get("candidate_metric_nonconstant_on_source_fields") is not True:
        failures.append("candidate metric source fields must be nonconstant")
    if summary.get("source_rows_inventoried") != 6:
        failures.append("source row inventory count must be 6")
    if summary.get("metric_backtest_result_claimed") is not False:
        failures.append("iter85 must not claim metric backtest result")
    if summary.get("future_gate") != str(NEXT_GATE):
        failures.append("summary next gate changed")
    if summary.get("future_gate_type") != "zero_spend_metric_backtest":
        failures.append("summary future gate type changed")
    if summary.get("future_paid_execution_authorized_by_this_gate") is not False:
        failures.append("iter85 must not authorize paid execution")
    if summary.get("future_paid_execution_pre_registered") is not False:
        failures.append("iter85 must not pre-register paid execution")

    if critique.get("saturated_metric_id") != "verified_completion_evidence_by_task_and_condition":
        failures.append("critique saturated metric changed")
    if "task-native outcome fields" not in " ".join(critique.get("why_saturated", [])):
        failures.append("critique must mention ignored task-native outcome fields")
    if metric.get("metric_id") != METRIC_ID:
        failures.append("metric contract id changed")
    if metric.get("primary_metric_not_verified_completion_boolean") is not True:
        failures.append("metric contract must reject completion boolean as primary")
    if metric.get("future_backtest_required_before_paid_execution") is not True:
        failures.append("metric contract must require backtest before paid execution")
    if metric.get("future_paid_execution_authorized_by_this_gate") is not False:
        failures.append("metric contract must not authorize paid execution")
    extractor = metric.get("score_extractor", {})
    if extractor.get("controlled_player_mapping") != "the single config.players entry with agent == 'mini'":
        failures.append("controlled-player mapping changed")
    if "verified-completion boolean as primary metric" not in metric.get("forbidden_fallbacks", []):
        failures.append("metric contract missing completion fallback ban")

    if field_inventory.get("row_count") != 6:
        failures.append("field inventory row count must be 6")
    if field_inventory.get("expected_row_count") != 6:
        failures.append("field inventory expected count must be 6")
    if field_inventory.get("candidate_metric_field_available_for_all_rows") is not True:
        failures.append("field inventory must be computable for all rows")
    if field_inventory.get("candidate_metric_nonconstant_on_source_fields") is not True:
        failures.append("field inventory must show nonconstant source fields")
    if len(field_inventory.get("paired_task_preview", [])) != 3:
        failures.append("field inventory must contain three paired previews")
    for row in field_inventory.get("rows", []):
        if row.get("controlled_player") != "p1":
            failures.append(f"unexpected controlled player for {row.get('pair_id')}")
        if row.get("controlled_player_agent") != "mini":
            failures.append(f"unexpected controlled player agent for {row.get('pair_id')}")
        metadata_path = Path(str(row.get("metadata_path")))
        if not metadata_path.exists():
            failures.append(f"metadata path missing: {metadata_path}")
        elif row.get("metadata_sha256") != sha256(metadata_path):
            failures.append(f"metadata hash mismatch: {metadata_path}")
        if decimal_value(row.get("all_player_score_total")) <= Decimal("0"):
            failures.append(f"nonpositive score total for {row.get('pair_id')}")
    preview_tasks = {row.get("task_surface") for row in field_inventory.get("paired_task_preview", [])}
    if preview_tasks != {"dummy", "battlesnake", "deterministic_edit"}:
        failures.append("paired preview task set changed")

    if task_rules.get("selected_task_count") != 3:
        failures.append("task eligibility selected count must be 3")
    if task_rules.get("future_paid_execution_authorized_by_this_gate") is not False:
        failures.append("task eligibility must not authorize paid execution")
    if task_rules.get("aggregate_benchmark_metric_authorized") is not False:
        failures.append("task eligibility must not authorize aggregate benchmark metric")
    if future_plan.get("next_gate") != str(NEXT_GATE):
        failures.append("future plan next gate changed")
    if future_plan.get("next_gate_pre_registered") is not True:
        failures.append("future plan next gate must be pre-registered")
    if future_plan.get("future_paid_execution_pre_registered") is not False:
        failures.append("future plan must not pre-register paid execution")
    if future_plan.get("future_paid_run_ceiling_authorized") is not False:
        failures.append("future plan must not authorize paid-run ceiling")
    hard = future_plan.get("iter86_hard_ceilings", {})
    if hard.get("provider_model_invocations") != 0:
        failures.append("iter86 provider calls must be zero")
    if decimal_value(hard.get("provider_spend_usd")) != Decimal("0"):
        failures.append("iter86 provider spend must be zero")
    if hard.get("codeclash_row_execution") != 0:
        failures.append("iter86 row execution must be zero")

    for key in [
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "swebench_execution_or_score_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "production_or_live_domain_changed",
        "cross_task_surface_pooling_authorized",
        "aggregate_benchmark_metric_authorized",
        "future_paid_execution_authorized_by_this_gate",
    ]:
        if boundary.get(key) is not False:
            failures.append(f"claim boundary {key} must be false")
        if key in summary and summary.get(key) is not False:
            failures.append(f"summary {key} must be false")
    for key in ["gpu_used", "cloud_runner_started", "sentinel_named_resources_modified"]:
        if summary.get(key) is not False:
            failures.append(f"summary {key} must be false")
    if summary.get("provider_api_calls") != 0:
        failures.append("iter85 provider calls must be zero")
    if decimal_value(summary.get("provider_cost_usd")) != Decimal("0"):
        failures.append("iter85 provider cost must be zero")
    if summary.get("row_execution_in_this_gate") != 0:
        failures.append("iter85 row execution must be zero")
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
        "redesigned metric: `task_native_score_share_delta_with_receipt_gates`",
        "provider calls in this gate: `0`",
        "provider spend in this gate: `$0.00000000`",
        "row execution in this gate: `0`",
        "future paid execution authorized by this gate: `false`",
        "not a benchmark result",
        "state-of-the-art result",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "real null/no-signal result",
        "verified-completion boolean saturated",
        "future paid execution authorized by iter85: `false`",
        "zero-spend backtest",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "discriminating task/metric redesign: pass",
        "provider_calls_in_this_gate=0",
        "provider_spend_in_this_gate_usd=0.00000000",
        "row_execution_in_this_gate=0",
        "metric_id=task_native_score_share_delta_with_receipt_gates",
        "future_paid_execution_authorized_by_this_gate=false",
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
        print("iter85 discriminating task/metric redesign audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter85 discriminating task/metric redesign audit: clean pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
