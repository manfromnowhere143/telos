#!/usr/bin/env python3
"""Audit iter55 provider-compatible paid execution blocked artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter55_provider_compatible_paid_execution_after_executor_recovery")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
PREFLIGHT = PROOF / "preflight.json"
PLAN = PROOF / "execution_plan.json"
SUMMARY = PROOF / "run_summary.json"
RECEIPT = PROOF / "valid" / "receipt_provider_compatible_paid_execution_blocked.json"
NEXT_GATE = Path("experiments/iter56_provider_auth_recovery_for_paid_protocol_effect/HYPOTHESIS.md")
READY_PAIR_IDS = {
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
}
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"-----BEGIN PRIVATE KEY-----"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com"),
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


def audit_preflight(failures: list[str]) -> None:
    data = load_json(PREFLIGHT)
    expected = {
        "schema_version": "telos.provider_compatible_paid_execution.preflight.v1",
        "status": "blocked",
        "iter54_status": "pass",
        "provider_command_executed": False,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "next_gate": NEXT_GATE.as_posix(),
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"preflight {key} expected {value!r}, got {data.get(key)!r}")
    auth = data.get("auth", {})
    if auth.get("active_account_present") is not True:
        failures.append("active gcloud account should be present through the token probe")
    if auth.get("gcloud_user_access_token_available") is not True:
        failures.append("gcloud user token should be available as a diagnostic")
    if auth.get("adc_access_token_available") is not False:
        failures.append("ADC token must be unavailable for this blocked result")
    if auth.get("adc_error_class") != "interactive_reauthentication_required":
        failures.append("ADC error class should record interactive reauthentication")
    if auth.get("impersonated_user_access_token_available") is not False:
        failures.append("impersonated token must be unavailable for this blocked result")
    if auth.get("impersonation_error_class") != "iam_service_account_token_creator_denied":
        failures.append("impersonation error class should record token-creator denial")
    if data.get("blockers") != [
        "adc_noninteractive_refresh_unavailable",
        "runner_impersonation_unavailable",
    ]:
        failures.append(f"unexpected blockers: {data.get('blockers')}")


def audit_plan_and_summary(failures: list[str]) -> None:
    plan = load_json(PLAN)
    summary = load_json(SUMMARY)
    if plan.get("status") != "blocked":
        failures.append("execution plan must be blocked")
    if set(plan.get("selected_pair_ids", [])) != READY_PAIR_IDS:
        failures.append("execution plan selected pair ids changed")
    if plan.get("provider_command_executed") is not False:
        failures.append("execution plan must not execute provider commands")
    for row in plan.get("commands", []):
        if row.get("executed") is not False:
            failures.append("command row unexpectedly executed")
        if row.get("blocked_before_execution") is not True:
            failures.append("command row must be blocked before execution")
    expected_summary = {
        "schema_version": "telos.provider_compatible_paid_execution.summary.v1",
        "status": "blocked",
        "iter54_status": "pass",
        "provider_command_executed": False,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "adc_access_token_available": False,
        "adc_error_class": "interactive_reauthentication_required",
        "impersonated_user_access_token_available": False,
        "impersonation_error_class": "iam_service_account_token_creator_denied",
        "account_identifier_committed": False,
        "project_identifier_committed": False,
        "runner_identifier_committed": False,
        "redaction_scan_passed": True,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "clean_pass": False,
        "blocked_result": True,
        "quality_failure": False,
        "failures": [],
        "next_gate": NEXT_GATE.as_posix(),
    }
    for key, value in expected_summary.items():
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
        if receipt.status != "blocked":
            failures.append(f"receipt status expected blocked, got {receipt.status}")
    except ProofValidationError as exc:
        failures.append(f"receipt validation failed: {exc}")
    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `BLOCKED`.",
        "provider commands executed: `false`",
        "No benchmark result is claimed.",
        "No model-superiority or state-of-the-art result is claimed.",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")


def audit_secrets(failures: list[str]) -> None:
    for path in [PREFLIGHT, PLAN, SUMMARY, RESULT, PROOF / "review.md", PROOF / "command_output.txt"]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"secret-like or identifier residue in {path}")
                break


def main() -> int:
    failures: list[str] = []
    for path in [PREFLIGHT, PLAN, SUMMARY, RESULT, RECEIPT, NEXT_GATE]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")
    if not failures:
        audit_preflight(failures)
        audit_plan_and_summary(failures)
        audit_receipt_and_text(failures)
        audit_secrets(failures)
    if failures:
        print("iter55 provider-compatible paid execution audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter55 provider-compatible paid execution audit: clean blocked result")
    return 0


if __name__ == "__main__":
    sys.exit(main())
