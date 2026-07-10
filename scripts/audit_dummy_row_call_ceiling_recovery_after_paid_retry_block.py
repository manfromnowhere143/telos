#!/usr/bin/env python3
"""Audit iter79 Dummy row call-ceiling recovery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter79_dummy_row_call_ceiling_recovery_after_paid_retry_block")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
PREREQ = PROOF / "prerequisite_validation.json"
CLASSIFICATION = PROOF / "dummy_call_ceiling_classification.json"
RETENTION = PROOF / "deterministic_edit_retention.json"
PLAN = PROOF / "recovery_plan.json"
RECEIPT = PROOF / "valid" / "receipt_dummy_row_call_ceiling_recovery_after_paid_retry_block.json"
ITER78_PROOF = Path("experiments/iter78_provider_compatible_expanded_paid_retry_after_adc_recovery/proof")
ITER78_SUMMARY = ITER78_PROOF / "run_summary.json"
ITER78_REPORT = ITER78_PROOF / "protocol_effect_report.json"
NEXT_GATE = (
    "experiments/iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery/"
    "HYPOTHESIS.md"
)
DUMMY_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-dummy-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
]
DETERMINISTIC_EDIT_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
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
        CLASSIFICATION,
        RETENTION,
        PLAN,
        PROOF / "command_output.txt",
        PROOF / "review.md",
        PROOF / "learning_record.json",
        RECEIPT,
    ]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")


def audit_packets(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    prereq = load_json(PREREQ)
    classification = load_json(CLASSIFICATION)
    retention = load_json(RETENTION)
    plan = load_json(PLAN)
    iter78_summary = load_json(ITER78_SUMMARY)
    iter78_report = load_json(ITER78_REPORT)

    expected_schemas = {
        "summary": (
            summary,
            "telos.dummy_row_call_ceiling_recovery.summary.v1",
        ),
        "prereq": (
            prereq,
            "telos.dummy_row_call_ceiling_recovery.prerequisite_validation.v1",
        ),
        "classification": (
            classification,
            "telos.dummy_row_call_ceiling_recovery.classification.v1",
        ),
        "retention": (
            retention,
            "telos.dummy_row_call_ceiling_recovery.deterministic_edit_retention.v1",
        ),
        "plan": (
            plan,
            "telos.dummy_row_call_ceiling_recovery.recovery_plan.v1",
        ),
    }
    for name, (packet, schema) in expected_schemas.items():
        if packet.get("schema_version") != schema:
            failures.append(f"unexpected {name} schema")
        if packet.get("experiment_id") != EXPERIMENT.name:
            failures.append(f"{name} experiment id mismatch")

    if summary.get("status") != "pass":
        failures.append("iter79 must pass after classifying the blocker")
    if summary.get("clean_pass") is not True:
        failures.append("summary clean_pass must be true")
    if summary.get("blocked_result") is not False or summary.get("quality_failure") is not False:
        failures.append("summary blocked/quality flags must be false")
    if summary.get("blockers") != [] or summary.get("failures") != []:
        failures.append("pass must have no blockers or failures")

    if prereq.get("clean_prerequisites") is not True:
        failures.append("iter78 prerequisites must be clean")
    if prereq.get("iter78_status") != "blocked":
        failures.append("iter78 status must remain blocked")
    if prereq.get("iter78_blocked_result") is not True:
        failures.append("iter78 blocked flag must be true")
    if prereq.get("iter78_quality_failure") is not False:
        failures.append("iter78 must not be a quality failure")
    if prereq.get("iter78_receipt_validation_returncode") != 0:
        failures.append("iter78 receipt validation must pass")
    if prereq.get("iter78_audit_returncode") != 0:
        failures.append("iter78 audit must pass")
    if prereq.get("iter78_executed_pair_count") != 4:
        failures.append("iter78 executed pair count changed")
    if prereq.get("iter78_provider_api_calls") != 9:
        failures.append("iter78 provider call count changed")
    if abs(float(prereq.get("iter78_provider_cost_usd", -1.0)) - 0.039876) > 1e-9:
        failures.append("iter78 provider cost changed")
    if prereq.get("iter78_blockers") != ["provider_command_nonzero_returncode"]:
        failures.append("iter78 blocker classification changed")
    if prereq.get("iter78_failures") != []:
        failures.append("iter78 failures must remain empty")
    if prereq.get("source_iter78_summary_sha256") != sha256(ITER78_SUMMARY):
        failures.append("iter78 summary hash mismatch")
    if prereq.get("source_iter78_report_sha256") != sha256(ITER78_REPORT):
        failures.append("iter78 report hash mismatch")

    rows_by_pair = {
        item.get("pair_id"): item
        for item in classification.get("rows", [])
        if isinstance(item, dict)
    }
    if classification.get("dummy_pair_ids") != DUMMY_PAIR_IDS:
        failures.append("Dummy pair ids changed")
    if set(rows_by_pair) != set(DUMMY_PAIR_IDS):
        failures.append("classification rows must contain exactly the two Dummy rows")
    if classification.get("all_dummy_failures_classified") is not True:
        failures.append("all Dummy failures must be classified")
    alternatives = classification.get("alternative_failure_modes_excluded", {})
    for key in ["receipt_schema", "adc_or_provider_access", "overlay_materialization"]:
        if alternatives.get(key) is not True:
            failures.append(f"alternative failure mode not excluded: {key}")

    for pair_id in DUMMY_PAIR_IDS:
        item = rows_by_pair.get(pair_id, {})
        if item.get("classification") != "per_row_global_call_ceiling":
            failures.append(f"{pair_id} classification changed")
        if item.get("classified") is not True:
            failures.append(f"{pair_id} must be classified")
        if item.get("public_config") != "configs/test/dummy.yaml":
            failures.append(f"{pair_id} public config changed")
        if item.get("analysis_stratum") != "dummy_minimal_adapter_validation":
            failures.append(f"{pair_id} analysis stratum changed")
        if item.get("command_returncode") != 1:
            failures.append(f"{pair_id} command return code must be 1")
        if item.get("command_timed_out") is not False:
            failures.append(f"{pair_id} command must not time out")
        if item.get("verified_completion_evidence") is not False:
            failures.append(f"{pair_id} must not verify completion in iter78")
        if item.get("raw_evidence_present") is not True:
            failures.append(f"{pair_id} raw evidence must be present")
        if item.get("stderr_contains_global_call_limit") is not True:
            failures.append(f"{pair_id} stderr must contain global call limit")
        if item.get("observed_global_call_limit") != 8:
            failures.append(f"{pair_id} observed call limit must be 8")
        if "Global cost/call limit exceeded:" not in item.get("global_limit_line", ""):
            failures.append(f"{pair_id} global limit line missing")
        for key in [
            "receipt_schema_excluded",
            "adc_or_provider_access_excluded",
            "overlay_materialization_excluded",
        ]:
            if item.get(key) is not True:
                failures.append(f"{pair_id} did not exclude {key}")
        stderr_path = Path(str(item.get("source_command_stderr", "")))
        execution_path = Path(str(item.get("source_command_execution", "")))
        if not stderr_path.exists():
            failures.append(f"{pair_id} source stderr path missing")
        elif item.get("source_command_stderr_sha256") != sha256(stderr_path):
            failures.append(f"{pair_id} source stderr hash mismatch")
        if not execution_path.exists():
            failures.append(f"{pair_id} source command execution path missing")
        elif item.get("source_command_execution_sha256") != sha256(execution_path):
            failures.append(f"{pair_id} source command execution hash mismatch")

    if rows_by_pair.get(DUMMY_PAIR_IDS[0], {}).get("receipt_required") is not False:
        failures.append("baseline Dummy receipt must not be required")
    if rows_by_pair.get(DUMMY_PAIR_IDS[1], {}).get("receipt_required") is not True:
        failures.append("Telos Dummy receipt must be required")
    if rows_by_pair.get(DUMMY_PAIR_IDS[1], {}).get("receipt_valid") is not True:
        failures.append("Telos Dummy receipt must be valid")

    if retention.get("retained_pair_ids") != DETERMINISTIC_EDIT_PAIR_IDS:
        failures.append("deterministic-edit retained pair ids changed")
    if retention.get("retained_rows_rerun") is not False:
        failures.append("deterministic-edit rows must not be rerun")
    if retention.get("adapter_rows_executed_in_this_gate") != 0:
        failures.append("iter79 must execute zero rows")
    if retention.get("deterministic_edit_baseline_verified_completion_evidence") is not True:
        failures.append("deterministic-edit baseline must remain verified")
    if retention.get("deterministic_edit_telos_verified_completion_evidence") is not True:
        failures.append("deterministic-edit Telos must remain verified")
    if retention.get("deterministic_edit_delta_telos_minus_baseline") != 0:
        failures.append("deterministic-edit delta must remain zero")
    if retention.get("cross_task_surface_pooling_authorized") is not False:
        failures.append("cross-task pooling must remain unauthorized")

    if plan.get("next_gate") != NEXT_GATE:
        failures.append("next gate changed")
    if plan.get("paid_retry_scope") != "dummy_only":
        failures.append("next paid retry must be Dummy-only")
    if plan.get("adapter_rows_to_execute") != 2:
        failures.append("next paid retry must execute exactly two Dummy rows")
    if plan.get("selected_pair_ids") != DUMMY_PAIR_IDS:
        failures.append("next paid retry selected pair ids changed")
    if plan.get("deterministic_edit_pair_ids_retained_not_rerun") != DETERMINISTIC_EDIT_PAIR_IDS:
        failures.append("deterministic-edit retention in plan changed")
    if plan.get("retained_battlesnake_rows_rerun") is not False:
        failures.append("BattleSnake rows must not rerun")
    if plan.get("previous_per_row_call_limit") != 8:
        failures.append("previous per-row call limit changed")
    if plan.get("recommended_per_row_call_limit") != 16:
        failures.append("recommended per-row call limit must be 16")
    if plan.get("provider_call_ceiling") != 32:
        failures.append("provider call ceiling must remain 32")
    if float(plan.get("provider_spend_ceiling_usd", -1.0)) != 5.0:
        failures.append("provider spend ceiling must be tightened to 5")
    if float(plan.get("per_row_spend_limit_usd", -1.0)) != 2.5:
        failures.append("per-row spend limit must remain 2.5")
    if plan.get("preserves_or_tightens_total_ceiling") is not True:
        failures.append("plan must preserve or tighten total ceilings")
    for key in [
        "requires_provider_calls_in_this_gate",
        "requires_gpu",
        "requires_cloud_runner",
        "requires_sentinel_mutation",
    ]:
        if plan.get(key) is not False:
            failures.append(f"plan {key} must be false")

    for packet_name, packet in [("summary", summary), ("plan", plan)]:
        if packet.get("provider_api_calls", 0) != 0 and packet_name == "summary":
            failures.append("summary provider calls must be zero")
        if float(packet.get("provider_spend_usd", 0.0)) != 0.0 and packet_name == "summary":
            failures.append("summary provider spend must be zero")
    for key in [
        "adapter_rows_executed",
        "provider_api_calls",
    ]:
        if summary.get(key) != 0:
            failures.append(f"summary {key} must be zero")
    if float(summary.get("provider_spend_usd", -1.0)) != 0.0:
        failures.append("summary provider_spend_usd must be zero")
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
    if summary.get("next_gate") != NEXT_GATE:
        failures.append("summary next gate changed")
    if summary.get("redaction_scan_passed") is not True or summary.get("redaction_findings") != []:
        failures.append("summary redaction scan must pass")
    if iter78_summary.get("status") != "blocked" or iter78_report.get("status") != "blocked":
        failures.append("iter78 source packets must remain blocked")

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
        "Iteration 79 Result",
        "Dummy rows classified: `true`",
        "classification: `per_row_global_call_ceiling`",
        "provider API calls in this gate: `0`",
        "state-of-the-art result",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "committed iter78 artifacts only",
        "per-row global call-ceiling blockers",
        "deterministic-edit baseline and Telos rows",
        "Dummy-only",
        "no benchmark/model/SOTA claim",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "dummy row call-ceiling recovery: pass",
        "iter78_receipt_validation_returncode=0",
        "iter78_audit_returncode=0",
        "dummy_rows_classified=true",
        "adapter_rows_executed=0",
        "provider_api_calls=0",
        "provider_spend_usd=0.00000000",
        f"next_gate={NEXT_GATE}",
        "benchmark_model_sota_claim=false",
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
        print("iter79 Dummy row call-ceiling recovery audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter79 Dummy row call-ceiling recovery audit: clean recovery packet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
