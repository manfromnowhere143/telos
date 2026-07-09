#!/usr/bin/env python3
"""Audit iter71 provider-compatible expanded-slice artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter71_provider_compatible_expanded_slice_after_adapter_completion")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
CANDIDATES = PROOF / "candidate_rows.json"
DECISION = PROOF / "expanded_slice_decision.json"
SUMMARY = PROOF / "run_summary.json"
RECEIPT = (
    PROOF / "valid" / "receipt_provider_compatible_expanded_slice_after_adapter_completion.json"
)
NEXT_GATE = Path(
    "experiments/iter72_provider_compatible_expanded_paid_execution_after_slice_refreeze/"
    "HYPOTHESIS.md"
)
EXPECTED_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "baseline-agent-completion-evidence__configs-test-dummy-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
    "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
]
EXPECTED_ADAPTER_PAIR_IDS = EXPECTED_PAIR_IDS[2:]
EXPECTED_EXISTING_PAIR_IDS = EXPECTED_PAIR_IDS[:2]
EXPECTED_CONDITIONS = {
    "baseline_agent_completion_evidence",
    "telos_receipt_enforced_completion_evidence",
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
        CANDIDATES,
        DECISION,
        SUMMARY,
        PROOF / "command_output.txt",
        PROOF / "review.md",
        PROOF / "learning_record.json",
        RECEIPT,
        NEXT_GATE,
    ]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")


def audit_summary_decision_candidates(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    decision = load_json(DECISION)
    candidates = load_json(CANDIDATES)

    if summary.get("schema_version") != (
        "telos.provider_compatible_expanded_slice_after_adapter_completion.summary.v1"
    ):
        failures.append("unexpected summary schema")
    if decision.get("schema_version") != (
        "telos.provider_compatible_expanded_slice_after_adapter_completion.decision.v1"
    ):
        failures.append("unexpected decision schema")
    if candidates.get("schema_version") != (
        "telos.provider_compatible_expanded_slice_after_adapter_completion.candidate_rows.v1"
    ):
        failures.append("unexpected candidates schema")
    for packet_name, packet in [
        ("summary", summary),
        ("decision", decision),
        ("candidates", candidates),
    ]:
        if packet.get("status") != "pass":
            failures.append(f"{packet_name} must publish pass")
    if summary.get("clean_pass") is not True:
        failures.append("summary clean_pass must be true")
    if summary.get("blocked_result") is not False or summary.get("quality_failure") is not False:
        failures.append("summary blocked/quality booleans are inconsistent")
    if summary.get("blockers") != [] or decision.get("blockers") != []:
        failures.append("iter71 pass must have no blockers")
    if summary.get("failures") != [] or decision.get("failures") != []:
        failures.append("iter71 pass must have no failures")

    expected_values = {
        "iter70_status": "pass",
        "iter70_planned_adapter_row_count": 4,
        "iter70_receipt_validation_returncode": 0,
        "iter70_audit_returncode": 0,
        "iter66_status": "pass",
        "selected_row_count": 6,
        "excluded_row_count": 0,
        "existing_executed_retained_row_count": 2,
        "adapter_planned_selected_row_count": 4,
        "expanded_slice_decision": "stratified_six_row_slice_refrozen",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "row_execution_allowed": False,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "slice_selection_evidence_not_execution_evidence": True,
        "redaction_scan_passed": True,
        "next_gate": NEXT_GATE.as_posix(),
    }
    for key, expected in expected_values.items():
        if summary.get(key) != expected:
            failures.append(f"summary {key} expected {expected!r}, got {summary.get(key)!r}")
        if key in decision and decision.get(key) != expected:
            failures.append(f"decision {key} expected {expected!r}, got {decision.get(key)!r}")

    if summary.get("redaction_findings") != [] or decision.get("redaction_findings") != []:
        failures.append("redaction findings must be empty")
    if summary.get("iter66_primary_metric") != {
        "baseline_verified_completion_evidence": True,
        "telos_verified_completion_evidence": True,
        "verified_completion_evidence_delta_telos_minus_baseline": 0,
    }:
        failures.append("iter66 primary metric changed")

    selected_pair_ids = summary.get("selected_pair_ids", [])
    if selected_pair_ids != EXPECTED_PAIR_IDS:
        failures.append("selected pair ids changed")
    if summary.get("excluded_pair_ids") != []:
        failures.append("excluded pair ids must be empty after iter70 adapter completion")

    boundary = summary.get("analysis_boundary", {})
    if boundary.get("slice_type") != "stratified_provider_compatible_protocol_effect_slice":
        failures.append("analysis boundary slice type changed")
    if boundary.get("aggregate_primary_metric_authorized") is not False:
        failures.append("aggregate primary metric must be forbidden")
    if boundary.get("cross_task_surface_pooling_authorized") is not False:
        failures.append("cross-surface pooling must be forbidden")
    if len(boundary.get("task_surface_strata", [])) != 3:
        failures.append("three analysis strata must be recorded")

    next_gate = summary.get("next_paid_gate_plan", {})
    if next_gate.get("next_paid_gate_authorized") is not True:
        failures.append("next paid gate should be authorized as a pre-registration")
    if next_gate.get("execution_scope") != "adapter_planned_rows_only":
        failures.append("next gate execution scope changed")
    if next_gate.get("row_execution_count") != 4:
        failures.append("next gate row execution count must be four")
    if next_gate.get("row_execution_pair_ids") != EXPECTED_ADAPTER_PAIR_IDS:
        failures.append("next gate adapter row ids changed")
    if next_gate.get("retained_existing_execution_pair_ids") != EXPECTED_EXISTING_PAIR_IDS:
        failures.append("next gate retained existing ids changed")
    if next_gate.get("max_provider_model_invocations") != 32:
        failures.append("next provider invocation ceiling must be 32")
    if next_gate.get("max_provider_spend_usd") != 10.0:
        failures.append("next spend ceiling must be 10.0")
    for key in [
        "gpu_allowed",
        "cloud_runner_start_allowed",
        "production_or_live_domain_change_allowed",
        "aggregate_benchmark_or_model_claim_authorized",
    ]:
        if next_gate.get(key) is not False:
            failures.append(f"next gate {key} must be false")
    if next_gate.get("sentinel_named_resources_must_not_change") is not True:
        failures.append("next gate must preserve Sentinel isolation")

    rows = candidates.get("candidate_rows", [])
    if len(rows) != 6:
        failures.append("candidate packet must contain six rows")
    if [row.get("pair_id") for row in rows] != EXPECTED_PAIR_IDS:
        failures.append("candidate row order changed")
    if len(candidates.get("candidate_decisions", [])) != 6:
        failures.append("six candidate decisions required")
    if candidates.get("excluded_rows") != []:
        failures.append("excluded rows must be empty")
    for row in rows:
        pair_id = row.get("pair_id", "<missing>")
        if row.get("decision") != "include":
            failures.append(f"{pair_id} must be included")
        if row.get("condition_id") not in EXPECTED_CONDITIONS:
            failures.append(f"{pair_id} condition changed")
        for key in [
            "source_evidence",
            "adapter_evidence",
            "future_execution_command",
            "future_artifact_plan",
            "cost_capture_plan",
            "receipt_validation_plan",
            "redaction_plan",
            "teardown_plan",
        ]:
            if not row.get(key):
                failures.append(f"{pair_id} missing {key}")
        if "uv run codeclash run" not in row.get("future_execution_command", ""):
            failures.append(f"{pair_id} command must be a CodeClash run")
        if pair_id in EXPECTED_ADAPTER_PAIR_IDS:
            if row.get("selection_status") != "included_pending_execution":
                failures.append(f"{pair_id} must be pending execution")
            if row.get("adapter_evidence", {}).get("generated_adapter_planning_evidence_only") is not True:
                failures.append(f"{pair_id} must preserve planning-only adapter flag")
            if row.get("adapter_evidence", {}).get("execution_result") is not False:
                failures.append(f"{pair_id} must not be execution evidence")
            if f"experiments/{NEXT_GATE.parent.name}/proof/raw/{pair_id}" not in str(
                row.get("future_artifact_plan", {})
            ):
                failures.append(f"{pair_id} artifact plan must point at iter72")
        else:
            if row.get("selection_status") != "included_existing_execution_evidence":
                failures.append(f"{pair_id} must be retained existing evidence")
            if row.get("rerun_in_next_paid_gate") is not False:
                failures.append(f"{pair_id} must not rerun in next paid gate")

    for rel_path, expected_hash in summary.get("artifact_hashes", {}).items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"hashed artifact missing: {rel_path}")
        elif sha256(path) != expected_hash:
            failures.append(f"hash mismatch for {rel_path}")


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
        "stratified evidence plan",
        "selected rows in the stratified slice: `6`",
        "This is slice selection evidence, not execution evidence",
        "state-of-the-art result",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "stratified plan",
        "forbidding cross-surface pooling",
        "Dummy remains a minimal adapter-validation",
        "No provider model call",
        "state-of-the-art claim occurred",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "provider_api_calls=0",
        "provider_spend_usd=0.00",
        "selected_row_count=6",
        "adapter_planned_selected_row_count=4",
        "existing_executed_retained_row_count=2",
        "expanded_slice_decision=stratified_six_row_slice_refrozen",
        "slice_selection_evidence_not_execution_evidence=true",
        "next_provider_invocation_ceiling=32",
        "next_spend_ceiling_usd=10.00",
    ]:
        if required not in command_output:
            failures.append(f"command output missing required line: {required}")


def audit_redaction(failures: list[str]) -> None:
    findings = []
    for path in text_files(EXPERIMENT):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(str(path))
                break
    if findings:
        failures.append(f"secret/redaction patterns found: {findings}")


def main() -> int:
    failures: list[str] = []
    audit_required_files(failures)
    if not failures:
        audit_summary_decision_candidates(failures)
        audit_receipt_and_text(failures)
        audit_redaction(failures)
    if failures:
        print("iter71 provider-compatible expanded slice after adapter completion audit FAILED")
        for failure in failures:
            print(f" - {failure}")
        return 1
    print("iter71 provider-compatible expanded slice after adapter completion audit: clean pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
