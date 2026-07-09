#!/usr/bin/env python3
"""Audit the iter43 provider execution harness recovery proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter43_provider_execution_harness_recovery")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
REPORT = PROOF / "provider_execution_harness_report.json"
SUMMARY = PROOF / "run_summary.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECEIPT = PROOF / "valid" / "receipt_provider_execution_harness_recovery.json"
HARNESS = Path("scripts/run_ephemeral_vertex_codeclash_provider.py")
ITER44 = Path(
    "experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/HYPOTHESIS.md"
)
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


def audit_report(failures: list[str]) -> None:
    report = load_json(REPORT)
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
            failures.append(f"report {key} expected {value!r}, got {report.get(key)!r}")

    readiness = report.get("gcloud_readiness", {})
    if readiness.get("running_sentinel_named_vm_count", -1) < 0:
        failures.append("sentinel VM count must be observed as a count")
    if readiness.get("running_telos_vm_count") != 0:
        failures.append("readiness running_telos_vm_count must be 0")
    if readiness.get("dedicated_runner_visible_count") != 1:
        failures.append("dedicated runner must be visible exactly once")
    for service in ["aiplatform.googleapis.com", "compute.googleapis.com", "iam.googleapis.com"]:
        if readiness.get("services_enabled", {}).get(service) is not True:
            failures.append(f"service not enabled in report: {service}")
    for key in [
        "account_identifier_logged",
        "project_identifier_logged",
        "service_account_identifier_logged",
    ]:
        if readiness.get(key) is not False:
            failures.append(f"readiness {key} must be false")

    lifecycle = report.get("lifecycle_probe", {})
    for key in ["vm_created", "serial_marker_seen", "vm_deleted", "no_gpu_requested"]:
        if lifecycle.get(key) is not True:
            failures.append(f"lifecycle {key} must be true")
    if lifecycle.get("model_call_made") is not False:
        failures.append("lifecycle must not make a model call")
    if lifecycle.get("full_task_condition_pair_executed") is not False:
        failures.append("lifecycle must not execute a full task-condition pair")
    if lifecycle.get("running_telos_vm_count_before") != 0:
        failures.append("lifecycle running_telos_vm_count_before must be 0")
    if lifecycle.get("running_telos_vm_count_after") != 0:
        failures.append("lifecycle running_telos_vm_count_after must be 0")
    if lifecycle.get("cloud_runner_estimated_spend_bound_usd", 999) > 1:
        failures.append("lifecycle spend bound must be <= 1")
    for key in ["zone_logged", "vm_identifier_logged", "service_account_identifier_logged"]:
        if lifecycle.get(key) is not False:
            failures.append(f"lifecycle {key} must be false")

    prior = report.get("prior_provider_artifact_summary", {})
    for key in [
        "cost_capture_parser_validated",
        "raw_artifact_retention_validated",
        "provider_private_fields_redacted",
    ]:
        if prior.get(key) is not True:
            failures.append(f"prior artifact {key} must be true")
    if prior.get("model_api_calls_reported", 0) <= 0:
        failures.append("prior cost parser must report positive API calls")
    if prior.get("model_cost_reported_usd", -1) < 0:
        failures.append("prior cost parser must report non-negative cost")

    scan = report.get("redaction_scan", {})
    if scan.get("secret_scan_passed") is not True:
        failures.append("redaction scan must pass")
    if scan.get("secret_or_identifier_hits") != []:
        failures.append("redaction scan hits must be empty")

    plan = report.get("provider_execution_plan", {})
    if plan.get("full_protocol_effect_execution_enabled") is not False:
        failures.append("full protocol execution must remain disabled")
    if plan.get("requires_future_gate_to_execute_task_condition_pairs") is not True:
        failures.append("plan must require a future gate for task-condition execution")


def audit_summary(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    expected = {
        "schema_version": "telos.provider_execution_harness_recovery.summary.v1",
        "status": "pass",
        "experiment_id": "iter43_provider_execution_harness_recovery",
        "harness_path": HARNESS.as_posix(),
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "gpu_used": False,
        "no_gpu_requested": True,
        "full_task_condition_pairs_executed": 0,
        "lifecycle_vm_created": True,
        "lifecycle_serial_marker_seen": True,
        "lifecycle_vm_deleted": True,
        "running_telos_vm_count_before": 0,
        "running_telos_vm_count_after": 0,
        "dedicated_runner_visible_count": 1,
        "cost_capture_parser_validated": True,
        "raw_artifact_retention_validated": True,
        "redaction_scan_passed": True,
        "secret_or_identifier_hits": [],
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
        "clean_pass": True,
        "blocked_result": False,
        "quality_failure": False,
        "blockers": [],
        "failures": [],
        "next_gate": ITER44.as_posix(),
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {summary.get(key)!r}")
    if summary.get("cloud_runner_estimated_spend_bound_usd", 999) > 1:
        failures.append("summary cloud runner spend bound must be <= 1")

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
        "provider execution harness recovery: pass",
        "provider_model_api_calls=0",
        "provider_spend_usd=0.0",
        "lifecycle_vm_created=true",
        "lifecycle_vm_deleted=true",
        "running_telos_vm_count_after=0",
        "full_task_condition_pairs_executed=0",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`",
        "No account identifier",
        "No benchmark result is claimed",
        "What Remains Forbidden",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in ["harness recovery only", "zero provider model calls"]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.status != "pass":
        failures.append("receipt status must be pass")
    if receipt.receipt_id != "iter43-provider-execution-harness-recovery-pass":
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
    for path in [RESULT, REPORT, SUMMARY, COMMAND_OUTPUT, REVIEW, RECEIPT, HARNESS, ITER44]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_report(failures)
        audit_summary(failures)
        audit_text_and_receipt(failures)
        audit_secret_residue(failures)

    if failures:
        print("provider execution harness recovery audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("provider execution harness recovery audit: clean harness pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
