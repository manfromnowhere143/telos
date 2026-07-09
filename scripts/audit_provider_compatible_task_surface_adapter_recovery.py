#!/usr/bin/env python3
"""Audit iter68 provider-compatible task-surface adapter recovery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter68_provider_compatible_task_surface_adapter_recovery")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
REPORT = PROOF / "adapter_recovery_report.json"
SUMMARY = PROOF / "run_summary.json"
RECEIPT = PROOF / "valid" / "receipt_provider_compatible_task_surface_adapter_recovery.json"
NEXT_GATE = Path("experiments/iter69_codeclash_task_surface_source_snapshot_recovery/HYPOTHESIS.md")
EXPECTED_BLOCKERS = [
    "committed_dummy_source_surface_missing",
    "expanded_slice_adapter_set_incomplete",
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
        PROOF / "recovered_overlay/configs/test/telos_battlesnake_edit_vertex_baseline.yaml",
        PROOF / "recovered_overlay/configs/test/telos_battlesnake_edit_vertex_receipt_enforced.yaml",
        PROOF / "recovered_overlay/configs/mini/telos_vertex_gemini_edit_baseline_agent.yaml",
        PROOF / "recovered_overlay/configs/mini/telos_vertex_gemini_edit_receipt_enforced_agent.yaml",
    ]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")


def audit_report_summary(failures: list[str]) -> None:
    report = load_json(REPORT)
    summary = load_json(SUMMARY)
    if report.get("schema_version") != "telos.provider_compatible_task_surface_adapter_recovery.report.v1":
        failures.append("unexpected report schema")
    if summary.get("schema_version") != "telos.provider_compatible_task_surface_adapter_recovery.summary.v1":
        failures.append("unexpected summary schema")
    if report.get("status") != "blocked" or summary.get("status") != "blocked":
        failures.append("iter68 must publish a blocked result")
    if summary.get("clean_pass") is not False or summary.get("blocked_result") is not True:
        failures.append("blocked summary booleans are inconsistent")
    if summary.get("quality_failure") is not False:
        failures.append("quality_failure must be false")
    if summary.get("blockers") != EXPECTED_BLOCKERS:
        failures.append(f"summary blockers changed: {summary.get('blockers')}")
    if report.get("blockers") != EXPECTED_BLOCKERS:
        failures.append(f"report blockers changed: {report.get('blockers')}")
    if report.get("iter67_status") != "blocked":
        failures.append("iter67 prerequisite must be blocked")
    if report.get("iter67_decision") != "no_expanded_slice_currently_justified":
        failures.append("iter67 decision changed")
    if report.get("recovered_adapter_row_count") != 2:
        failures.append("deterministic-edit adapter should emit two planned rows")
    if report.get("residual_rejection_count") != 2:
        failures.append("Dummy residual rejection should include two rows")
    if summary.get("next_paid_gate_authorized") is not False:
        failures.append("iter68 must not authorize a paid gate")
    if summary.get("next_gate") != str(NEXT_GATE):
        failures.append("next gate changed")

    for key, expected in [
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
    ]:
        if summary.get(key) != expected:
            failures.append(f"summary {key} expected {expected!r}, got {summary.get(key)!r}")
        if key in report and report.get(key) != expected:
            failures.append(f"report {key} expected {expected!r}, got {report.get(key)!r}")

    target_surfaces = {item.get("public_config"): item for item in report.get("target_surfaces", [])}
    dummy = target_surfaces.get("configs/test/dummy.yaml", {})
    edit = target_surfaces.get("configs/test/telos_battlesnake_edit_test.yaml", {})
    if dummy.get("committed_source_present") is not False:
        failures.append("Dummy source must remain missing in iter68")
    if edit.get("committed_source_present") is not True:
        failures.append("deterministic-edit source must be present")
    for row in report.get("recovered_adapter_rows", []):
        for key in [
            "future_execution_command",
            "future_artifact_plan",
            "cost_capture_plan",
            "redaction_plan",
            "provider_overlay_config",
            "provider_agent_config",
            "provider_model_config",
        ]:
            if not row.get(key):
                failures.append(f"{row.get('pair_id')} missing {key}")
    for row in report.get("residual_rejections", []):
        if "No committed source snapshot" not in row.get("rejection_reason", ""):
            failures.append(f"{row.get('pair_id')} missing precise source-snapshot rejection")

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
    if receipt.status != "blocked":
        failures.append("receipt status must be blocked")

    result = RESULT.read_text(encoding="utf-8")
    review = (PROOF / "review.md").read_text(encoding="utf-8")
    command_output = (PROOF / "command_output.txt").read_text(encoding="utf-8")
    for required in [
        "Status: `BLOCKED`.",
        "Dummy source config is only named by prior manifests",
        "This is not a benchmark result",
        "state-of-the-art result",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "correctly refuses to expand",
        "lacks committed source content",
        "No provider model call",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "provider_api_calls=0",
        "provider_spend_usd=0.00",
        "recovered_adapter_row_count=2",
        "residual_rejection_count=2",
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
        print("iter68 provider-compatible task-surface adapter recovery audit FAILED")
        for failure in failures:
            print(f" - {failure}")
        return 1
    print("iter68 provider-compatible task-surface adapter recovery audit: clean blocked result")
    return 0


if __name__ == "__main__":
    sys.exit(main())
