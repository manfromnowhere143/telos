#!/usr/bin/env python3
"""Audit iter46 execution-with-assembled-executor proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
PREFLIGHT = PROOF / "preflight.json"
REPORT = PROOF / "execution_report.json"
SUMMARY = PROOF / "run_summary.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECEIPT = (
    PROOF
    / "valid"
    / "receipt_public_task_protocol_effect_execution_with_assembled_executor.json"
)
ITER47 = Path("experiments/iter47_provider_task_condition_command_binding_recovery/HYPOTHESIS.md")
REQUIRED_BLOCKERS = {
    "provider_overlay_not_bound_to_pair_commands",
    "recovered_harness_full_execution_disabled",
    "recovered_harness_requires_future_task_condition_gate",
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
            "telos.public_task_protocol_effect_execution_with_assembled_executor.preflight.v1"
        ),
        "status": "blocked",
        "experiment_id": "iter46_public_task_protocol_effect_execution_with_assembled_executor",
        "planned_task_condition_pairs": 6,
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": 6,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "credential_material_logged": False,
        "project_identifier_logged": False,
        "account_identifier_logged": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "failures": [],
    }
    for key, value in expected.items():
        if preflight.get(key) != value:
            failures.append(f"preflight {key} expected {value!r}, got {preflight.get(key)!r}")
    blockers = set(preflight.get("blockers", []))
    if not REQUIRED_BLOCKERS <= blockers:
        failures.append(f"preflight missing blockers: {sorted(REQUIRED_BLOCKERS - blockers)}")
    checks = preflight.get("checks", {})
    if checks.get("iter45_manifest_status") != "dry_run_ready":
        failures.append("iter45 manifest status must be dry_run_ready")
    if checks.get("pair_commands_bind_provider_overlay") is not False:
        failures.append("pair commands must show provider overlay binding gap")
    if checks.get("harness_full_protocol_effect_execution_enabled") is not False:
        failures.append("harness full execution flag must remain false")
    if checks.get("harness_requires_future_task_condition_gate") is not True:
        failures.append("harness future-gate flag must remain true")


def audit_report(failures: list[str]) -> None:
    report = load_json(REPORT)
    expected = {
        "schema_version": (
            "telos.public_task_protocol_effect_execution_with_assembled_executor.report.v1"
        ),
        "status": "blocked",
        "experiment_id": "iter46_public_task_protocol_effect_execution_with_assembled_executor",
        "planned_task_condition_pairs": 6,
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": 6,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "failures": [],
        "next_gate": ITER47.as_posix(),
    }
    for key, value in expected.items():
        if report.get(key) != value:
            failures.append(f"report {key} expected {value!r}, got {report.get(key)!r}")
    rows = report.get("condition_rows", [])
    if len(rows) != 2:
        failures.append("report must include two condition rows")
    for row in rows:
        if row.get("planned_task_count") != 3:
            failures.append(f"condition row planned count changed: {row}")
        if row.get("attempted_task_count") != 0 or row.get("blocked_task_count") != 3:
            failures.append(f"condition row must be fully blocked: {row}")
    if report.get("metrics", {}).get("primary", {}).get("value") is not None:
        failures.append("primary metric must remain uncomputed")


def audit_summary(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    expected = {
        "schema_version": (
            "telos.public_task_protocol_effect_execution_with_assembled_executor.summary.v1"
        ),
        "status": "blocked",
        "experiment_id": "iter46_public_task_protocol_effect_execution_with_assembled_executor",
        "planned_task_condition_pairs": 6,
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": 6,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "clean_pass": False,
        "blocked_result": True,
        "quality_failure": False,
        "failures": [],
        "next_gate": ITER47.as_posix(),
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {summary.get(key)!r}")
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
        "public task protocol-effect execution with assembled executor: blocked",
        "attempted_task_condition_pairs=0",
        "provider_model_api_calls=0",
        "provider_spend_usd=0.0",
        "cloud_runner_started=false",
        "sentinel_named_resources_modified=false",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `BLOCKED`",
        "provider-backed command binding is not concrete",
        "No benchmark result is claimed",
        "No provider-backed completion metric is inferred",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in ["blocked before provider execution", "No provider model calls occurred"]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.status != "blocked":
        failures.append("receipt status must be blocked")
    expected_id = "iter46-public-task-protocol-effect-execution-with-assembled-executor-blocked"
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
    for path in [RESULT, PREFLIGHT, REPORT, SUMMARY, COMMAND_OUTPUT, REVIEW, RECEIPT, ITER47]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_preflight(failures)
        audit_report(failures)
        audit_summary(failures)
        audit_text_and_receipt(failures)
        audit_secret_residue(failures)

    if failures:
        print("public task protocol-effect execution with assembled executor audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("public task protocol-effect execution with assembled executor audit: clean blocked result")
    return 0


if __name__ == "__main__":
    sys.exit(main())
