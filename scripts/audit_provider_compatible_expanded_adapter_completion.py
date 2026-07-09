#!/usr/bin/env python3
"""Audit iter70 provider-compatible expanded adapter completion artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter70_provider_compatible_expanded_adapter_completion")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
REPORT = PROOF / "adapter_completion_report.json"
SUMMARY = PROOF / "run_summary.json"
RECEIPT = PROOF / "valid" / "receipt_provider_compatible_expanded_adapter_completion.json"
NEXT_GATE = Path("experiments/iter71_provider_compatible_expanded_slice_after_adapter_completion/HYPOTHESIS.md")
EXPECTED_DUMMY_SHA256 = "b8e856447fc71c79bb5e042dc530127480d670d84fd51c03e2c2e7f58c630e97"
EXPECTED_OVERLAYS = [
    "recovered_overlay/configs/test/telos_dummy_vertex_baseline.yaml",
    "recovered_overlay/configs/test/telos_dummy_vertex_receipt_enforced.yaml",
    "recovered_overlay/configs/test/telos_battlesnake_edit_vertex_baseline.yaml",
    "recovered_overlay/configs/test/telos_battlesnake_edit_vertex_receipt_enforced.yaml",
    "recovered_overlay/configs/mini/telos_vertex_gemini_dummy_baseline_agent.yaml",
    "recovered_overlay/configs/mini/telos_vertex_gemini_dummy_receipt_enforced_agent.yaml",
    "recovered_overlay/configs/mini/telos_vertex_gemini_edit_baseline_agent.yaml",
    "recovered_overlay/configs/mini/telos_vertex_gemini_edit_receipt_enforced_agent.yaml",
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
        REPORT,
        SUMMARY,
        PROOF / "command_output.txt",
        PROOF / "review.md",
        PROOF / "learning_record.json",
        RECEIPT,
        NEXT_GATE,
        *[PROOF / rel_path for rel_path in EXPECTED_OVERLAYS],
    ]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")


def audit_report_summary(failures: list[str]) -> None:
    report = load_json(REPORT)
    summary = load_json(SUMMARY)
    if report.get("schema_version") != "telos.provider_compatible_expanded_adapter_completion.report.v1":
        failures.append("unexpected report schema")
    if summary.get("schema_version") != "telos.provider_compatible_expanded_adapter_completion.summary.v1":
        failures.append("unexpected summary schema")
    if report.get("status") != "pass" or summary.get("status") != "pass":
        failures.append("iter70 must publish a pass result")
    if summary.get("clean_pass") is not True:
        failures.append("clean_pass must be true")
    if summary.get("blocked_result") is not False or summary.get("quality_failure") is not False:
        failures.append("blocked/quality booleans are inconsistent")
    if report.get("blockers") != [] or summary.get("blockers") != []:
        failures.append("iter70 pass must have no blockers")
    if report.get("failures") != [] or summary.get("failures") != []:
        failures.append("iter70 pass must have no failures")
    if report.get("iter69_status") != "pass" or summary.get("iter69_status") != "pass":
        failures.append("iter69 prerequisite must be pass")
    if report.get("iter69_dummy_source_sha256") != EXPECTED_DUMMY_SHA256:
        failures.append("iter69 dummy source hash mismatch")
    if report.get("iter68_dummy_residual_rejection_present") is not True:
        failures.append("iter68 Dummy residual rejection must be present")
    if summary.get("next_gate") != str(NEXT_GATE):
        failures.append("next gate changed")

    for key, expected in [
        ("planned_adapter_row_count", 4),
        ("dummy_adapter_row_count", 2),
        ("deterministic_edit_adapter_row_count", 2),
        ("written_overlay_file_count", 8),
        ("provider_api_calls", 0),
        ("provider_spend_usd", 0.0),
        ("row_execution_allowed", False),
        ("gpu_used", False),
        ("cloud_runner_started", False),
        ("sentinel_named_resources_modified", False),
        ("production_or_live_domain_changed", False),
        ("benchmark_result_claimed", False),
        ("leaderboard_or_swebench_result_claimed", False),
        ("model_superiority_claimed", False),
        ("state_of_the_art_result_claimed", False),
        ("generated_adapters_are_planning_evidence_only", True),
        ("generated_adapters_are_execution_results", False),
        ("next_paid_gate_authorized", False),
    ]:
        if summary.get(key) != expected:
            failures.append(f"summary {key} expected {expected!r}, got {summary.get(key)!r}")
        if key in report and report.get(key) != expected:
            failures.append(f"report {key} expected {expected!r}, got {report.get(key)!r}")

    if sorted(report.get("written_overlay_files", [])) != sorted(EXPECTED_OVERLAYS):
        failures.append("written overlay file list mismatch")

    rows = report.get("planned_adapter_rows", [])
    if len(rows) != 4:
        failures.append("expected four planned adapter rows")
    for row in rows:
        pair_id = row.get("pair_id", "<missing>")
        for key in [
            "future_execution_command",
            "future_artifact_plan",
            "cost_capture_plan",
            "receipt_validation_plan",
            "redaction_plan",
            "teardown_plan",
            "source_config_path",
            "source_config_sha256",
            "provider_overlay_config",
            "provider_agent_config",
            "provider_model_config",
        ]:
            if not row.get(key):
                failures.append(f"{pair_id} missing {key}")
        if row.get("generated_adapter_planning_evidence_only") is not True:
            failures.append(f"{pair_id} missing planning-only flag")
        if row.get("execution_result") is not False:
            failures.append(f"{pair_id} must not be execution result")
        if "uv run codeclash run" not in row.get("future_execution_command", ""):
            failures.append(f"{pair_id} missing CodeClash future command")
        if row.get("condition_id") == "telos_receipt_enforced_completion_evidence":
            receipt_plan = row.get("receipt_validation_plan", {})
            if receipt_plan.get("required_before_acceptance") is not True:
                failures.append(f"{pair_id} receipt validation must be required")

    if summary.get("redaction_scan_passed") is not True or summary.get("redaction_findings") != []:
        failures.append("redaction scan must pass with no findings")
    for rel_path, digest in summary.get("artifact_hashes", {}).items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"summary hash path missing: {rel_path}")
        elif sha256(path) != digest:
            failures.append(f"summary hash mismatch: {rel_path}")


def audit_receipt_and_text(failures: list[str]) -> None:
    try:
        receipt = load_receipt(RECEIPT)
    except ProofValidationError as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.status != "pass":
        failures.append("receipt status must be pass")

    result = RESULT.read_text(encoding="utf-8")
    review = (PROOF / "review.md").read_text(encoding="utf-8")
    command_output = (PROOF / "command_output.txt").read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`.",
        "planning evidence only",
        "generated adapter files are execution evidence: `false`",
        "This is not a benchmark result",
        "state-of-the-art result",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "committed source evidence only",
        "not execution evidence",
        "strict interpretation boundary",
        "No provider model call",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "provider_api_calls=0",
        "provider_spend_usd=0.00",
        "planned_adapter_row_count=4",
        "dummy_adapter_row_count=2",
        "deterministic_edit_adapter_row_count=2",
        "generated_adapters_are_execution_results=false",
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
        audit_report_summary(failures)
        audit_receipt_and_text(failures)
        audit_redaction(failures)
    if failures:
        print("iter70 provider-compatible expanded adapter completion audit FAILED")
        for failure in failures:
            print(f" - {failure}")
        return 1
    print("iter70 provider-compatible expanded adapter completion audit: clean pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
