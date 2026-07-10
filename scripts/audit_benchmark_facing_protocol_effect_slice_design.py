#!/usr/bin/env python3
"""Audit iter82 benchmark-facing protocol-effect slice design artifacts."""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter82_benchmark_facing_protocol_effect_slice_design")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
PREREQ = PROOF / "prerequisite_validation.json"
TASK_RULES = PROOF / "task_eligibility_rules.json"
CONDITION = PROOF / "condition_contract.json"
EVIDENCE = PROOF / "evidence_requirements.json"
FUTURE_PLAN = PROOF / "future_paid_run_plan.json"
FAILURE_SEMANTICS = PROOF / "failure_semantics.json"
CLAIM_BOUNDARY = PROOF / "claim_boundary.json"
REDACTION = PROOF / "redaction_scan.json"
RECEIPT = PROOF / "valid" / "receipt_benchmark_facing_protocol_effect_slice_design.json"
NEXT_GATE = Path("experiments/iter83_benchmark_facing_protocol_effect_execution_pilot/HYPOTHESIS.md")
ITER81_PROOF = Path("experiments/iter81_expanded_stratified_adapter_validation_consolidation/proof")
ITER81_SUMMARY = ITER81_PROOF / "run_summary.json"
ITER81_ACCOUNTING = ITER81_PROOF / "stratified_row_accounting.json"
ITER81_RECEIPT = (
    ITER81_PROOF / "valid" / "receipt_expanded_stratified_adapter_validation_consolidation.json"
)
ITER39_SLICE = Path(
    "experiments/iter39_public_task_protocol_effect_slice/proof/protocol_effect_slice.json"
)
ITER45_MANIFEST = Path(
    "experiments/iter45_public_task_condition_executor_assembly/proof/executor_manifest.json"
)
PAIR_IDS = [
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
        TASK_RULES,
        CONDITION,
        EVIDENCE,
        FUTURE_PLAN,
        FAILURE_SEMANTICS,
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


def audit_summary(summary: dict, failures: list[str]) -> None:
    if summary.get("schema_version") != "telos.benchmark_facing_slice_design.summary.v1":
        failures.append("unexpected summary schema")
    if summary.get("experiment_id") != EXPERIMENT.name:
        failures.append("summary experiment id mismatch")
    if summary.get("status") != "pass":
        failures.append("iter82 must pass")
    if summary.get("clean_pass") is not True:
        failures.append("summary clean_pass must be true")
    if summary.get("blocked_result") is not False or summary.get("quality_failure") is not False:
        failures.append("summary blocked/quality flags must be false")
    if summary.get("blockers") != [] or summary.get("failures") != []:
        failures.append("pass summary must not contain blockers/failures")
    expected_values = {
        "iter81_clean": True,
        "selected_task_count": 3,
        "selected_pair_count": 6,
        "future_provider_model_invocation_ceiling": 96,
        "future_per_row_call_limit": 16,
        "adapter_rows_executed_in_this_gate": 0,
        "provider_api_calls": 0,
        "provider_call_ceiling": 0,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "cross_task_surface_pooling_authorized": False,
        "aggregate_benchmark_metric_authorized": False,
        "swebench_execution_or_score_claimed": False,
        "redaction_scan_passed": True,
    }
    for key, expected in expected_values.items():
        if summary.get(key) != expected:
            failures.append(f"summary {key} changed")
    if summary.get("future_gate") != str(NEXT_GATE):
        failures.append("summary next gate changed")
    if decimal_value(summary.get("future_provider_spend_ceiling_usd")) != Decimal("10.00000000"):
        failures.append("future spend ceiling changed")
    if decimal_value(summary.get("future_per_row_spend_limit_usd")) != Decimal("2.00000000"):
        failures.append("future per-row spend ceiling changed")
    if decimal_value(summary.get("provider_cost_usd")) != Decimal("0"):
        failures.append("iter82 provider cost must be zero")
    metric = summary.get("primary_metric", {})
    if metric.get("future_row_count") != 6:
        failures.append("primary metric future row count changed")
    if metric.get("aggregate_benchmark_metric_authorized") is not False:
        failures.append("primary metric must not authorize aggregate benchmark metric")


def audit_prereq(prereq: dict, failures: list[str]) -> None:
    if prereq.get("schema_version") != (
        "telos.benchmark_facing_slice_design.prerequisite_validation.v1"
    ):
        failures.append("unexpected prereq schema")
    if prereq.get("experiment_id") != EXPERIMENT.name:
        failures.append("prereq experiment id mismatch")
    if prereq.get("clean_prerequisites") is not True:
        failures.append("iter81 prereq must be clean")
    if prereq.get("iter81_status") != "pass" or prereq.get("iter81_clean_pass") is not True:
        failures.append("iter81 status must be clean pass")
    if prereq.get("iter81_consolidated_success_pair_count") != 6:
        failures.append("iter81 consolidated row count changed")
    if prereq.get("iter81_diagnostic_blocked_pair_count") != 2:
        failures.append("iter81 diagnostic row count changed")
    if prereq.get("iter81_source_packet_total_provider_api_calls") != 23:
        failures.append("iter81 source call total changed")
    if prereq.get("iter81_source_packet_total_provider_cost_usd") != "0.12765400":
        failures.append("iter81 source cost total changed")
    if prereq.get("iter81_receipt_validation_returncode") != 0:
        failures.append("iter81 receipt validation must pass")
    if prereq.get("iter81_audit_returncode") != 0:
        failures.append("iter81 audit must pass")
    by_path = {item.get("path"): item for item in prereq.get("source_artifacts", [])}
    expected_hashes = {
        str(ITER81_SUMMARY): sha256(ITER81_SUMMARY),
        str(ITER81_ACCOUNTING): sha256(ITER81_ACCOUNTING),
        str(ITER81_RECEIPT): sha256(ITER81_RECEIPT),
    }
    for path, expected_hash in expected_hashes.items():
        if by_path.get(path, {}).get("sha256") != expected_hash:
            failures.append(f"prereq source hash mismatch: {path}")
    for command in prereq.get("command_results", []):
        if command.get("returncode") != 0 or command.get("timed_out") is not False:
            failures.append(f"prereq command failed: {command.get('command')}")


def audit_task_rules(task_rules: dict, failures: list[str]) -> None:
    if task_rules.get("schema_version") != "telos.benchmark_facing_slice_design.task_eligibility.v1":
        failures.append("unexpected task rules schema")
    if task_rules.get("experiment_id") != EXPERIMENT.name:
        failures.append("task rules experiment id mismatch")
    if task_rules.get("source_protocol_slice_sha256") != sha256(ITER39_SLICE):
        failures.append("protocol slice hash mismatch")
    if task_rules.get("source_executor_manifest_sha256") != sha256(ITER45_MANIFEST):
        failures.append("executor manifest hash mismatch")
    if task_rules.get("selected_task_count") != 3:
        failures.append("selected task count changed")
    if task_rules.get("selected_pair_count") != 6:
        failures.append("selected pair count changed")
    if task_rules.get("selected_pair_ids") != PAIR_IDS:
        failures.append("selected pair ids changed")
    if task_rules.get("cross_task_surface_pooling_authorized") is not False:
        failures.append("task rules must not authorize pooling")
    if task_rules.get("benchmark_result_authorized") is not False:
        failures.append("task rules must not authorize benchmark result")
    if task_rules.get("swebench_result_authorized") is not False:
        failures.append("task rules must not authorize SWE-bench result")
    tasks = task_rules.get("selected_tasks", [])
    public_configs = {item.get("public_config") for item in tasks if isinstance(item, dict)}
    if public_configs != {
        "configs/test/dummy.yaml",
        "configs/test/battlesnake_pvp_test.yaml",
        "configs/test/telos_battlesnake_edit_test.yaml",
    }:
        failures.append("selected public config set changed")
    exclusions = task_rules.get("exclusions", [])
    if not any("SWE-bench" in str(item.get("candidate", "")) for item in exclusions):
        failures.append("SWE-bench exclusion missing")


def audit_condition_and_requirements(condition: dict, evidence: dict, failures: list[str]) -> None:
    if condition.get("schema_version") != "telos.benchmark_facing_slice_design.condition_contract.v1":
        failures.append("unexpected condition schema")
    if condition.get("condition_count") != 2:
        failures.append("condition count changed")
    if condition.get("selected_pair_ids") != PAIR_IDS:
        failures.append("condition selected pair ids changed")
    metric = condition.get("primary_metric", {})
    if metric.get("metric_id") != "verified_completion_evidence_by_task_and_condition":
        failures.append("primary metric id changed")
    if metric.get("aggregate_benchmark_metric_authorized") is not False:
        failures.append("condition metric must not authorize aggregate benchmark metric")
    if evidence.get("schema_version") != "telos.benchmark_facing_slice_design.evidence_requirements.v1":
        failures.append("unexpected evidence schema")
    if evidence.get("future_gate") != str(NEXT_GATE):
        failures.append("evidence future gate changed")
    per_pair = evidence.get("per_pair_requirements", [])
    if [item.get("pair_id") for item in per_pair if isinstance(item, dict)] != PAIR_IDS:
        failures.append("evidence per-pair ids changed")
    for item in per_pair:
        pair_id = str(item.get("pair_id"))
        if item.get("raw_logs_required") is not True:
            failures.append(f"{pair_id} raw logs must be required")
        if item.get("metadata_required") is not True:
            failures.append(f"{pair_id} metadata must be required")
        if item.get("cost_and_call_stats_required") is not True:
            failures.append(f"{pair_id} cost/call stats must be required")
        if item.get("redaction_scan_required") is not True:
            failures.append(f"{pair_id} redaction scan must be required")
        expected_receipt = pair_id.startswith("telos-receipt-enforced-completion-evidence__")
        if item.get("telos_receipt_required_before_acceptance") is not expected_receipt:
            failures.append(f"{pair_id} receipt requirement changed")
    if evidence.get("missing_cost_or_call_stats_blocks_result") is not True:
        failures.append("missing cost/call stats must block")
    if evidence.get("missing_raw_artifacts_blocks_row") is not True:
        failures.append("missing raw artifacts must block rows")


def audit_future_plan(future_plan: dict, failures: list[str]) -> None:
    if future_plan.get("schema_version") != (
        "telos.benchmark_facing_slice_design.future_paid_run_plan.v1"
    ):
        failures.append("unexpected future plan schema")
    expected = {
        "future_gate": str(NEXT_GATE),
        "future_execution_enabled_in_iter82": False,
        "adapter_rows_to_execute_in_iter82": 0,
        "provider_model_invocations_in_iter82": 0,
        "provider_spend_in_iter82_usd": "0.00000000",
        "future_adapter_rows_to_execute": 6,
        "future_selected_pair_ids": PAIR_IDS,
        "future_provider_model_invocation_ceiling": 96,
        "future_per_row_call_limit": 16,
        "future_provider_spend_ceiling_usd": "10.00000000",
        "future_per_row_spend_limit_usd": "2.00000000",
        "future_wall_clock_ceiling_minutes": 90,
        "future_cloud_runner_startup": "forbidden",
        "future_gpu_use": "forbidden",
        "future_sentinel_named_resource_mutation": "forbidden",
        "future_production_or_live_domain_mutation": "forbidden",
        "future_benchmark_model_or_sota_claim": "forbidden",
    }
    for key, value in expected.items():
        if future_plan.get(key) != value:
            failures.append(f"future plan {key} changed")
    if not future_plan.get("stop_rules"):
        failures.append("future plan stop rules missing")
    if not future_plan.get("reporting_rules"):
        failures.append("future plan reporting rules missing")


def audit_failure_and_claims(
    failure_semantics: dict,
    claim_boundary: dict,
    summary: dict,
    failures: list[str],
) -> None:
    if failure_semantics.get("schema_version") != (
        "telos.benchmark_facing_slice_design.failure_semantics.v1"
    ):
        failures.append("unexpected failure semantics schema")
    for key in [
        "pass_semantics_for_future_gate",
        "blocked_semantics_for_future_gate",
        "null_semantics_for_future_gate",
        "quality_failure_semantics_for_future_gate",
    ]:
        if not failure_semantics.get(key):
            failures.append(f"failure semantics missing {key}")
    if claim_boundary.get("schema_version") != "telos.benchmark_facing_slice_design.claim_boundary.v1":
        failures.append("unexpected claim boundary schema")
    for packet_name, packet in [("summary", summary), ("claim_boundary", claim_boundary)]:
        for key in [
            "benchmark_result_claimed",
            "leaderboard_or_swebench_result_claimed",
            "model_superiority_claimed",
            "state_of_the_art_result_claimed",
            "production_or_live_domain_changed",
            "cross_task_surface_pooling_authorized",
        ]:
            if packet.get(key) is not False:
                failures.append(f"{packet_name} must keep {key}=false")
    if claim_boundary.get("aggregate_benchmark_metric_authorized") is not False:
        failures.append("claim boundary must not authorize aggregate metric")
    forbidden = set(claim_boundary.get("claims_forbidden", []))
    for claim in ["SWE-bench score", "state-of-the-art status", "benchmark performance"]:
        if claim not in forbidden:
            failures.append(f"forbidden claim missing: {claim}")


def audit_redaction(redaction: dict, failures: list[str]) -> None:
    if redaction.get("schema_version") != "telos.benchmark_facing_slice_design.redaction_scan.v1":
        failures.append("unexpected redaction schema")
    if redaction.get("experiment_id") != EXPERIMENT.name:
        failures.append("redaction experiment id mismatch")
    if redaction.get("passed") is not True or redaction.get("findings") != []:
        failures.append("redaction scan must pass with no findings")
    for path in text_files(EXPERIMENT):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"redaction finding in {path}")
                break


def audit_text_and_receipt(failures: list[str]) -> None:
    combined = "\n".join(
        [
            RESULT.read_text(encoding="utf-8"),
            (PROOF / "review.md").read_text(encoding="utf-8"),
            NEXT_GATE.read_text(encoding="utf-8"),
        ]
    )
    for needle in [
        "not a benchmark result",
        "SWE-bench score",
        "state-of-the-art",
        "$10.00",
        "96",
    ]:
        if needle not in combined:
            failures.append(f"missing boundary/design text: {needle}")
    try:
        receipt = load_receipt(RECEIPT)
    except (OSError, json.JSONDecodeError, ProofValidationError) as exc:
        failures.append(f"invalid receipt: {exc}")
        return
    if receipt.status != "pass":
        failures.append("receipt status must be pass")
    if receipt.receipt_id != "iter82-benchmark-facing-protocol-effect-slice-design-pass":
        failures.append("receipt id changed")


def main() -> int:
    failures: list[str] = []
    audit_required_files(failures)
    if failures:
        for failure in failures:
            print(f"iter82 audit failed: {failure}", file=sys.stderr)
        return 1

    summary = load_json(SUMMARY)
    prereq = load_json(PREREQ)
    task_rules = load_json(TASK_RULES)
    condition = load_json(CONDITION)
    evidence = load_json(EVIDENCE)
    future_plan = load_json(FUTURE_PLAN)
    failure_semantics = load_json(FAILURE_SEMANTICS)
    claim_boundary = load_json(CLAIM_BOUNDARY)
    redaction = load_json(REDACTION)

    audit_summary(summary, failures)
    audit_prereq(prereq, failures)
    audit_task_rules(task_rules, failures)
    audit_condition_and_requirements(condition, evidence, failures)
    audit_future_plan(future_plan, failures)
    audit_failure_and_claims(failure_semantics, claim_boundary, summary, failures)
    audit_redaction(redaction, failures)
    audit_text_and_receipt(failures)

    if failures:
        for failure in failures:
            print(f"iter82 audit failed: {failure}", file=sys.stderr)
        return 1
    print("iter82 benchmark-facing protocol-effect slice design audit: pass")
    print("selected_pair_count=6")
    print("future_provider_call_ceiling=96")
    print("future_provider_spend_ceiling_usd=10.00000000")
    print("provider_calls_in_this_gate=0")
    print("provider_spend_in_this_gate_usd=0.00000000")
    print(f"next_gate={NEXT_GATE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
