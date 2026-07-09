#!/usr/bin/env python3
"""Audit the iter44 execution-after-harness-recovery proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery")
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
    / "receipt_public_task_protocol_effect_execution_after_harness_recovery.json"
)
ITER45 = Path("experiments/iter45_public_task_condition_executor_assembly/HYPOTHESIS.md")
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
            "telos.public_task_protocol_effect_execution_after_harness_recovery.preflight.v1"
        ),
        "status": "blocked",
        "experiment_id": "iter44_public_task_protocol_effect_execution_after_harness_recovery",
        "planned_task_condition_pairs": 6,
        "attempted_task_condition_pairs": 0,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "credential_material_logged": False,
        "project_identifier_logged": False,
        "account_identifier_logged": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
    }
    for key, value in expected.items():
        if preflight.get(key) != value:
            failures.append(f"preflight {key} expected {value!r}, got {preflight.get(key)!r}")

    blockers = preflight.get("blockers", [])
    for required in [
        "full_protocol_effect_execution_disabled_in_recovered_harness",
        "harness_requires_future_task_condition_gate",
    ]:
        if required not in blockers:
            failures.append(f"preflight missing blocker: {required}")
    if preflight.get("failures") != []:
        failures.append("preflight failures must be empty for blocked result")

    checks = preflight.get("checks", {})
    if checks.get("iter43_harness_recovery_passed") is not True:
        failures.append("iter43 harness recovery must be accepted")
    if checks.get("iter43_lifecycle_vm_deleted") is not True:
        failures.append("iter43 lifecycle deletion must remain visible")
    if checks.get("harness_full_protocol_effect_execution_enabled") is not False:
        failures.append("harness full execution flag must be false")
    if checks.get("baseline_and_telos_conditions_present") is not True:
        failures.append("baseline and Telos conditions must remain present")
    if checks.get("executable_task_count") != 3:
        failures.append("executable task count must remain 3")

    cloud = preflight.get("cloud_counts", {})
    for key in ["vm_identifiers_logged", "project_identifier_logged", "account_identifier_logged"]:
        if cloud.get(key) is not False:
            failures.append(f"cloud count {key} must be false")


def audit_report(failures: list[str]) -> None:
    report = load_json(REPORT)
    expected = {
        "schema_version": (
            "telos.public_task_protocol_effect_execution_after_harness_recovery.report.v1"
        ),
        "status": "blocked",
        "experiment_id": "iter44_public_task_protocol_effect_execution_after_harness_recovery",
        "planned_task_condition_pairs": 6,
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": 6,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "failures": [],
        "next_gate": ITER45.as_posix(),
    }
    for key, value in expected.items():
        if report.get(key) != value:
            failures.append(f"report {key} expected {value!r}, got {report.get(key)!r}")
    rows = report.get("condition_rows", [])
    if len(rows) != 2:
        failures.append("report must keep two condition rows")
    for row in rows:
        if row.get("planned_task_count") != 3 or row.get("attempted_task_count") != 0:
            failures.append(f"invalid condition row counts: {row}")
        if row.get("blocked_task_count") != 3 or row.get("status") != "blocked":
            failures.append(f"condition row must be blocked: {row}")
    if report.get("metrics", {}).get("primary", {}).get("value") is not None:
        failures.append("primary metric must be uncomputed")


def audit_summary(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    expected = {
        "schema_version": (
            "telos.public_task_protocol_effect_execution_after_harness_recovery.summary.v1"
        ),
        "status": "blocked",
        "experiment_id": "iter44_public_task_protocol_effect_execution_after_harness_recovery",
        "planned_task_condition_pairs": 6,
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": 6,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "credential_material_committed": False,
        "project_identifier_committed": False,
        "account_identifier_committed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "clean_pass": False,
        "blocked_result": True,
        "quality_failure": False,
        "failures": [],
        "next_gate": ITER45.as_posix(),
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {summary.get(key)!r}")
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
        "public task protocol-effect execution after harness recovery: blocked",
        "provider_model_api_calls=0",
        "provider_spend_usd=0.0",
        "cloud_runner_started=false",
        "attempted_task_condition_pairs=0",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `BLOCKED`",
        "full protocol-effect execution disabled",
        "No benchmark result is claimed",
        "What Remains Forbidden",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in ["blocked before provider execution", "zero provider model calls"]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.status != "blocked":
        failures.append("receipt status must be blocked")
    if receipt.receipt_id != "iter44-public-task-protocol-effect-execution-after-harness-blocked":
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
    for path in [RESULT, PREFLIGHT, REPORT, SUMMARY, COMMAND_OUTPUT, REVIEW, RECEIPT, ITER45]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_preflight(failures)
        audit_report(failures)
        audit_summary(failures)
        audit_text_and_receipt(failures)
        audit_secret_residue(failures)

    if failures:
        print("public task protocol-effect execution after harness recovery audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("public task protocol-effect execution after harness recovery audit: clean blocked result")
    return 0


if __name__ == "__main__":
    sys.exit(main())
