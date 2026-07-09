#!/usr/bin/env python3
"""Audit iter56 provider auth recovery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter56_provider_auth_recovery_for_paid_protocol_effect")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
REPORT = PROOF / "auth_recovery_report.json"
PROBE = PROOF / "vertex_access_probe.json"
SUMMARY = PROOF / "run_summary.json"
RECEIPT = PROOF / "valid" / "receipt_provider_auth_recovery_for_paid_protocol_effect.json"
NEXT_GATE = Path(
    "experiments/iter57_provider_compatible_paid_execution_after_auth_recovery/HYPOTHESIS.md"
)
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"),
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


def audit_report_and_probe(failures: list[str]) -> None:
    report = load_json(REPORT)
    probe = load_json(PROBE)
    expected = {
        "schema_version": "telos.provider_auth_recovery.report.v1",
        "status": "pass",
        "iter55_status": "blocked",
        "adc_access_token_available": True,
        "adc_access_token_output_suppressed": True,
        "auth_path_ready": True,
        "auth_surface": "local_adc_user_credentials",
        "provider_access_probe_count": 1,
        "provider_spend_bound_usd": 0.01,
        "provider_spend_observed_usd": None,
        "paid_battlesnake_command_executed": False,
        "excluded_pair_executed": False,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "account_identifier_committed": False,
        "project_identifier_committed": False,
        "runner_identifier_committed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "blockers": [],
        "failures": [],
        "next_gate": NEXT_GATE.as_posix(),
    }
    for key, value in expected.items():
        if report.get(key) != value:
            failures.append(f"report {key} expected {value!r}, got {report.get(key)!r}")
    if report.get("adc_repair", {}).get("status") != "pass":
        failures.append("ADC repair status must pass")
    if report.get("impersonation", {}).get("available") is not False:
        failures.append("impersonation should remain unavailable and documented")
    if "runner_short_id" in report.get("impersonation", {}):
        failures.append("impersonation report must not commit the runner short identifier")
    probe_expected = {
        "schema_version": "telos.provider_auth_recovery.vertex_access_probe.v1",
        "status": "pass",
        "attempted": True,
        "model_call_made": True,
        "provider_access_probe_count": 1,
        "provider_spend_bound_usd": 0.01,
        "provider_spend_observed_usd": None,
        "project_identifier_logged": False,
        "credential_material_logged": False,
        "selected_model": "gemini-3.1-pro-preview-customtools",
        "region": "global",
        "http_status": "200",
        "request_max_output_tokens": 4,
        "candidate_count": 1,
        "candidate_text_committed": False,
        "usage_metadata_present": True,
        "successful_endpoint_access_evidenced": True,
    }
    for key, value in probe_expected.items():
        if probe.get(key) != value:
            failures.append(f"probe {key} expected {value!r}, got {probe.get(key)!r}")
    if not isinstance(probe.get("total_token_count"), int) or probe["total_token_count"] <= 0:
        failures.append("probe total token count must be positive")


def audit_summary(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    expected = {
        "schema_version": "telos.provider_auth_recovery.summary.v1",
        "status": "pass",
        "iter55_status": "blocked",
        "adc_repair_status": "pass",
        "adc_access_token_available": True,
        "auth_path_ready": True,
        "auth_surface": "local_adc_user_credentials",
        "impersonated_user_access_token_available": False,
        "impersonation_error_class": "iam_service_account_token_creator_denied",
        "provider_access_probe_status": "pass",
        "provider_access_probe_count": 1,
        "provider_spend_bound_usd": 0.01,
        "provider_spend_observed_usd": None,
        "paid_battlesnake_command_executed": False,
        "excluded_pair_executed": False,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "account_identifier_committed": False,
        "project_identifier_committed": False,
        "runner_identifier_committed": False,
        "redaction_scan_passed": True,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "clean_pass": True,
        "blocked_result": False,
        "quality_failure": False,
        "blockers": [],
        "failures": [],
        "next_gate": NEXT_GATE.as_posix(),
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {summary.get(key)!r}")
    for rel_path, digest in summary.get("artifact_hashes", {}).items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"summary artifact missing: {rel_path}")
        elif sha256(path) != digest:
            failures.append(f"summary artifact hash mismatch: {rel_path}")


def audit_receipt_and_text(failures: list[str]) -> None:
    try:
        receipt = load_receipt(RECEIPT)
        if receipt.status != "pass":
            failures.append(f"receipt status expected pass, got {receipt.status}")
    except ProofValidationError as exc:
        failures.append(f"receipt validation failed: {exc}")
    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`.",
        "paid BattleSnake commands executed: `false`",
        "No benchmark result is claimed.",
        "No model-superiority or state-of-the-art result is claimed.",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")


def audit_secrets(failures: list[str]) -> None:
    for path in [REPORT, PROBE, SUMMARY, RESULT, PROOF / "review.md", PROOF / "command_output.txt"]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"secret-like or identifier residue in {path}")
                break


def main() -> int:
    failures: list[str] = []
    for path in [REPORT, PROBE, SUMMARY, RESULT, RECEIPT, NEXT_GATE]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")
    if not failures:
        audit_report_and_probe(failures)
        audit_summary(failures)
        audit_receipt_and_text(failures)
        audit_secrets(failures)
    if failures:
        print("iter56 provider auth recovery audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter56 provider auth recovery audit: clean pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
