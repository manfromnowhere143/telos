#!/usr/bin/env python3
"""Audit iter77 runtime ADC recheck artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter77_runtime_adc_recheck_after_application_default_login")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
REPORT = PROOF / "runtime_adc_recheck_report.json"
PREFLIGHT = PROOF / "preflight.json"
RECEIPT = PROOF / "valid" / "receipt_runtime_adc_recheck_after_application_default_login.json"
CODECLASH_COMMIT = "381cdfa05a35e8acd35853b9fc7e13005121b127"
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
    if summary.get("schema_version") != "telos.runtime_adc_recheck_after_application_default_login.summary.v1":
        failures.append("unexpected summary schema")
    if report.get("schema_version") != "telos.runtime_adc_recheck_after_application_default_login.report.v1":
        failures.append("unexpected report schema")
    if preflight.get("schema_version") != "telos.runtime_adc_recheck_after_application_default_login.preflight.v1":
        failures.append("unexpected preflight schema")
    if summary.get("experiment_id") != EXPERIMENT.name or report.get("experiment_id") != EXPERIMENT.name:
        failures.append("experiment id mismatch")

    status = summary.get("status")
    if status not in {"pass", "blocked", "fail"}:
        failures.append(f"invalid summary status: {status!r}")
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
        failures.append("pass status must have no blockers or failures")
    if status == "blocked" and not summary.get("blockers"):
        failures.append("blocked status must name blockers")
    if status == "fail" and not summary.get("failures"):
        failures.append("fail status must name failures")

    for packet_name, packet in [("summary", summary), ("report", report), ("preflight", preflight)]:
        if packet.get("iter76_receipt_validation_returncode") != 0:
            failures.append(f"{packet_name} iter76 receipt validation must pass")
        if packet.get("iter76_audit_returncode") != 0:
            failures.append(f"{packet_name} iter76 audit must pass")
        if packet.get("provider_model_calls") != 0:
            failures.append(f"{packet_name} provider calls must be zero")
        if float(packet.get("provider_spend_usd", 0.0)) != 0.0:
            failures.append(f"{packet_name} provider spend must be zero")
        if packet.get("adapter_rows_executed") != 0:
            failures.append(f"{packet_name} adapter row execution must be zero")
        for key in [
            "gpu_used",
            "cloud_runner_started",
            "sentinel_named_resources_modified",
            "production_or_live_domain_changed",
            "benchmark_result_claimed",
            "leaderboard_or_swebench_result_claimed",
            "model_superiority_claimed",
            "state_of_the_art_result_claimed",
        ]:
            if key in packet and packet.get(key) is not False:
                failures.append(f"{packet_name} {key} must be false")

    if preflight.get("iter76_status") != "blocked" or preflight.get("iter76_blocked_result") is not True:
        failures.append("preflight must prove iter76 clean blocked status")
    if preflight.get("codeclash_actual_commit") != CODECLASH_COMMIT:
        failures.append("CodeClash commit changed")
    if preflight.get("codeclash_commit_matches_expected") is not True:
        failures.append("CodeClash commit must match expected")
    for packet_name, packet in [("summary", summary), ("report", report), ("preflight", preflight)]:
        if packet.get("gcloud_project_stdout_suppressed") is not True:
            failures.append(f"{packet_name} must suppress gcloud project stdout")
        if packet.get("gcloud_project_identifier_committed") is not False and "gcloud_project_identifier_committed" in packet:
            failures.append(f"{packet_name} must not commit project identifier")
        if packet.get("adc_token_output_suppressed") is not True:
            failures.append(f"{packet_name} must suppress ADC token stdout")
        if packet.get("adc_token_committed") is not False:
            failures.append(f"{packet_name} must not commit ADC token")
        if packet.get("credential_material_committed") is not False and "credential_material_committed" in packet:
            failures.append(f"{packet_name} must not commit credential material")

    if status == "pass":
        for key in [
            "codeclash_commit_matches_expected",
            "docker_ready",
            "codeclash_google_auth_import_ready",
            "gcloud_project_available",
            "adc_access_token_available",
        ]:
            if summary.get(key) is not True:
                failures.append(f"pass requires summary {key}=true")
    if status == "blocked" and summary.get("adc_access_token_available") is not True:
        if "adc_auth_unavailable" not in summary.get("blockers", []):
            failures.append("ADC block must name adc_auth_unavailable")
    if summary.get("redaction_scan_passed") is not True or summary.get("redaction_findings") != []:
        failures.append("summary redaction scan must pass")
    if report.get("redaction_scan_passed") is not True or report.get("redaction_findings") != []:
        failures.append("report redaction scan must pass")
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
        "Iteration 77 Result",
        "gcloud project output committed: `false`",
        "ADC token output committed: `false`",
        "provider calls: `0`",
        "state-of-the-art result",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "local runtime ADC recheck probes",
        "suppressed stdout",
        "committed no token",
        "provider calls: `0`",
        "No benchmark, SWE-bench, leaderboard",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "runtime adc recheck after Application Default Credentials login:",
        "iter76_receipt_validation_returncode=0",
        "iter76_audit_returncode=0",
        "gcloud_project_stdout_suppressed=true",
        "adc_token_output_suppressed=true",
        "provider_model_calls=0",
        "provider_spend_usd=0.00000000",
        "adapter_rows_executed=0",
    ]:
        if required not in command_output:
            failures.append(f"command output missing required line: {required}")
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
        print("iter77 runtime ADC recheck audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter77 runtime ADC recheck audit: clean artifact packet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
