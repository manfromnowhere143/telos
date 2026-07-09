#!/usr/bin/env python3
"""Audit iter51 provider-compatible protocol-effect execution-with-wrapper artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter51_provider_compatible_protocol_effect_execution_with_wrapper")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
PREFLIGHT = PROOF / "preflight.json"
HARNESS_REPORT = PROOF / "harness_dry_run_report.json"
REPORT = PROOF / "execution_report.json"
SUMMARY = PROOF / "run_summary.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECEIPT = (
    PROOF
    / "valid"
    / "receipt_provider_compatible_protocol_effect_execution_with_wrapper.json"
)
NEXT_GATE = Path("experiments/iter52_provider_condition_runtime_separation_recovery/HYPOTHESIS.md")
READY_PAIR_IDS = {
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
}
EXCLUDED_PAIR_IDS = {
    "baseline-agent-completion-evidence__configs-test-dummy-yaml",
    "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
}
REQUIRED_BLOCKERS = {
    "wrapper_execution_mode_absent",
    "base_provider_harness_full_execution_disabled",
    "base_provider_harness_still_requires_future_task_condition_gate",
    "telos_condition_runtime_not_distinct_from_baseline",
}
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"-----BEGIN PRIVATE KEY-----"),
    re.compile(r"ANTHROPIC_API_KEY\s*=\s*\S+"),
    re.compile(r"OPENAI_API_KEY\s*=\s*\S+"),
    re.compile(r"GOOGLE_API_KEY\s*=\s*\S+"),
    re.compile(r"GEMINI_API_KEY\s*=\s*\S+"),
    re.compile(r"GOOGLE_APPLICATION_CREDENTIALS\s*=\s*\S+"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com"),
]


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be an object")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_preflight(failures: list[str]) -> None:
    preflight = load_json(PREFLIGHT)
    expected = {
        "schema_version": (
            "telos.provider_compatible_protocol_effect_execution_with_wrapper.preflight.v1"
        ),
        "status": "blocked",
        "experiment_id": "iter51_provider_compatible_protocol_effect_execution_with_wrapper",
        "selected_pair_count": 2,
        "excluded_pair_count": 4,
        "planned_task_condition_pairs": 2,
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": 2,
        "excluded_task_condition_pairs_attempted": 0,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "max_provider_model_invocations": 16,
        "max_provider_spend_usd": 10.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "credential_material_logged": False,
        "project_identifier_logged": False,
        "account_identifier_logged": False,
        "service_account_identifier_logged": False,
        "vm_identifier_logged": False,
        "zone_logged": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
    }
    for key, value in expected.items():
        if preflight.get(key) != value:
            failures.append(f"preflight {key} expected {value!r}, got {preflight.get(key)!r}")
    if set(preflight.get("selected_pair_ids", [])) != READY_PAIR_IDS:
        failures.append("preflight selected pair ids changed")
    if set(preflight.get("excluded_pair_ids", [])) != EXCLUDED_PAIR_IDS:
        failures.append("preflight excluded pair ids changed")
    blockers = set(preflight.get("blockers", []))
    missing_blockers = sorted(REQUIRED_BLOCKERS - blockers)
    if missing_blockers:
        failures.append("preflight missing blockers: " + ", ".join(missing_blockers))
    if preflight.get("failures") != []:
        failures.append("preflight failures must be empty for blocked result")

    checks = preflight.get("checks", {})
    for key in [
        "iter50_wrapper_recovery_passed",
        "wrapper_plan_dry_run_ready",
        "exact_two_pairs_planned",
        "exact_four_exclusions_visible",
        "excluded_pairs_rejected_by_wrapper",
    ]:
        if checks.get(key) is not True:
            failures.append(f"preflight check {key} must be true")
    for key in [
        "wrapper_execution_mode_present",
        "runtime_commands_distinct_beyond_output_root",
        "provider_overlays_distinct_between_conditions",
        "provider_agent_prompts_distinct_between_conditions",
        "base_provider_harness_full_execution_enabled",
    ]:
        if checks.get(key) is not False:
            failures.append(f"preflight check {key} must be false")
    if checks.get("base_provider_harness_requires_future_gate") is not True:
        failures.append("base harness future-gate flag must remain true")
    if checks.get("harness_dry_run_lifecycle_probe_mode") != "dry_run":
        failures.append("harness dry-run lifecycle mode must be dry_run")
    if checks.get("harness_dry_run_model_calls") != 0:
        failures.append("harness dry run must make zero model calls")
    if checks.get("harness_dry_run_task_pairs_executed") != 0:
        failures.append("harness dry run must execute zero task pairs")


def audit_harness_report(failures: list[str]) -> None:
    report = load_json(HARNESS_REPORT)
    expected = {
        "schema_version": "telos.provider_execution_harness.report.v1",
        "harness_path": "scripts/run_ephemeral_vertex_codeclash_provider.py",
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "full_task_condition_pairs_executed": 0,
        "credential_material_logged": False,
        "project_identifier_logged": False,
        "account_identifier_logged": False,
    }
    for key, value in expected.items():
        if report.get(key) != value:
            failures.append(f"harness report {key} expected {value!r}, got {report.get(key)!r}")
    lifecycle = report.get("lifecycle_probe", {})
    if lifecycle.get("mode") != "dry_run":
        failures.append("harness lifecycle probe must be dry_run")
    if lifecycle.get("vm_created") is not False:
        failures.append("harness dry run must not create a VM")
    if lifecycle.get("model_call_made") is not False:
        failures.append("harness dry run must not call a model")
    if lifecycle.get("full_task_condition_pair_executed") is not False:
        failures.append("harness dry run must not execute a task-condition pair")
    scan = report.get("redaction_scan", {})
    if scan.get("secret_scan_passed") is not True:
        failures.append("harness redaction scan must pass")


def audit_execution_report(failures: list[str]) -> None:
    report = load_json(REPORT)
    expected = {
        "schema_version": (
            "telos.provider_compatible_protocol_effect_execution_with_wrapper.report.v1"
        ),
        "status": "blocked",
        "experiment_id": "iter51_provider_compatible_protocol_effect_execution_with_wrapper",
        "planned_task_condition_pairs": 2,
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": 2,
        "excluded_task_condition_pairs_attempted": 0,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "failures": [],
        "next_gate": NEXT_GATE.as_posix(),
    }
    for key, value in expected.items():
        if report.get(key) != value:
            failures.append(f"execution report {key} expected {value!r}, got {report.get(key)!r}")
    if not REQUIRED_BLOCKERS <= set(report.get("blockers", [])):
        failures.append("execution report missing required blockers")
    rows = report.get("condition_rows", [])
    if len(rows) != 2:
        failures.append("execution report must include two condition rows")
    for row in rows:
        if row.get("pair_id") not in READY_PAIR_IDS:
            failures.append(f"unexpected condition row pair id: {row.get('pair_id')}")
        if row.get("attempted") is not False or row.get("blocked") is not True:
            failures.append(f"condition row must be blocked and unattempted: {row}")
        if row.get("provider_model_api_calls") != 0 or row.get("provider_spend_usd") != 0.0:
            failures.append(f"condition row must record zero provider spend/calls: {row}")
    if report.get("metrics", {}).get("primary", {}).get("value") is not None:
        failures.append("primary metric must be uncomputed")


def audit_summary(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    expected = {
        "schema_version": (
            "telos.provider_compatible_protocol_effect_execution_with_wrapper.summary.v1"
        ),
        "status": "blocked",
        "experiment_id": "iter51_provider_compatible_protocol_effect_execution_with_wrapper",
        "selected_pair_count": 2,
        "excluded_pair_count": 4,
        "planned_task_condition_pairs": 2,
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": 2,
        "excluded_task_condition_pairs_attempted": 0,
        "max_provider_model_invocations": 16,
        "max_provider_spend_usd": 10.0,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "credential_material_committed": False,
        "project_identifier_committed": False,
        "account_identifier_committed": False,
        "service_account_identifier_committed": False,
        "vm_identifier_committed": False,
        "zone_committed": False,
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
    for key, value in expected.items():
        if summary.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {summary.get(key)!r}")
    if set(summary.get("selected_pair_ids", [])) != READY_PAIR_IDS:
        failures.append("summary selected pair ids changed")
    if set(summary.get("excluded_pair_ids", [])) != EXCLUDED_PAIR_IDS:
        failures.append("summary excluded pair ids changed")
    if not REQUIRED_BLOCKERS <= set(summary.get("blockers", [])):
        failures.append("summary missing required blockers")
    hashes = summary.get("artifact_hashes", {})
    if not isinstance(hashes, dict) or not hashes:
        failures.append("summary artifact_hashes must be non-empty")
        return
    for rel_path, expected_hash in hashes.items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"hashed artifact missing: {rel_path}")
            continue
        actual_hash = sha256(path)
        if actual_hash != expected_hash:
            failures.append(f"hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}")


def audit_text_and_receipt(failures: list[str]) -> None:
    output = COMMAND_OUTPUT.read_text(encoding="utf-8")
    for required in [
        "provider-compatible protocol-effect execution with wrapper: blocked",
        "planned_task_condition_pairs=2",
        "attempted_task_condition_pairs=0",
        "blocked_task_condition_pairs=2",
        "excluded_task_condition_pairs_attempted=0",
        "provider_model_api_calls=0",
        "provider_spend_usd=0.0",
        "cloud_runner_started=false",
        "gpu_used=false",
        "sentinel_named_resources_modified=false",
        "telos_condition_runtime_not_distinct_from_baseline",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `BLOCKED`",
        "blocked before provider execution",
        "wrapper recovered a clean dry-run plan",
        "No benchmark result",
        "model-superiority result",
        "state-of-the-art result",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in ["blocked before provider calls", "not a benchmark null"]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.status != "blocked":
        failures.append("receipt status must be blocked")
    expected_id = "iter51-provider-compatible-protocol-effect-execution-with-wrapper-blocked"
    if receipt.receipt_id != expected_id:
        failures.append("unexpected receipt id")


def audit_secret_residue(failures: list[str]) -> None:
    for path in PROOF.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"possible secret or account/project identifier in {path}")


def main() -> int:
    failures: list[str] = []
    for path in [
        RESULT,
        PREFLIGHT,
        HARNESS_REPORT,
        REPORT,
        SUMMARY,
        COMMAND_OUTPUT,
        REVIEW,
        RECEIPT,
        NEXT_GATE,
    ]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_preflight(failures)
        audit_harness_report(failures)
        audit_execution_report(failures)
        audit_summary(failures)
        audit_text_and_receipt(failures)
        audit_secret_residue(failures)

    if failures:
        print("provider-compatible protocol-effect execution with wrapper audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("provider-compatible protocol-effect execution with wrapper audit: clean blocked result")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
