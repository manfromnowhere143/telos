#!/usr/bin/env python3
"""Audit iter50 provider-compatible execution-wrapper recovery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt

from run_provider_compatible_protocol_effect_pairs import CAPTURE_STEP_IDS


EXPERIMENT = Path("experiments/iter50_provider_compatible_execution_wrapper_recovery")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
PLAN = PROOF / "wrapper_dry_run_plan.json"
SUMMARY = PROOF / "run_summary.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECEIPT = PROOF / "valid" / "receipt_provider_compatible_execution_wrapper_recovery.json"
WRAPPER = Path("scripts/run_provider_compatible_protocol_effect_pairs.py")
ITER51 = Path("experiments/iter51_provider_compatible_protocol_effect_execution_with_wrapper/HYPOTHESIS.md")
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


def audit_plan(failures: list[str]) -> None:
    plan = load_json(PLAN)
    expected = {
        "schema_version": "telos.provider_compatible_execution_wrapper.dry_run_plan.v1",
        "status": "dry_run_ready",
        "wrapper_path": WRAPPER.as_posix(),
        "next_execution_experiment": "iter51_provider_compatible_protocol_effect_execution_with_wrapper",
        "selected_pair_count": 2,
        "excluded_pair_count": 4,
        "dry_run_pair_plan_count": 2,
        "rejected_pair_count": 4,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "full_provider_execution_in_iter50_enabled": False,
        "future_paid_execution_requires_next_gate": True,
        "future_max_provider_model_invocations": 16,
        "future_max_provider_spend_usd": 10.0,
        "future_gpu_allowed": False,
        "future_sentinel_named_resources_must_not_change": True,
        "blockers": [],
        "failures": [],
    }
    for key, value in expected.items():
        if plan.get(key) != value:
            failures.append(f"plan {key} expected {value!r}, got {plan.get(key)!r}")
    if set(plan.get("selected_pair_ids", [])) != READY_PAIR_IDS:
        failures.append("plan selected pair ids changed")
    if set(plan.get("excluded_pair_ids", [])) != EXCLUDED_PAIR_IDS:
        failures.append("plan excluded pair ids changed")

    controls = plan.get("controls", {})
    for key in [
        "iter49_blocked_before_provider_execution",
        "iter49_zero_provider_calls",
        "iter49_zero_provider_spend",
        "excluded_pairs_rejected_by_wrapper",
        "provider_execution_forbidden_in_this_gate",
        "cloud_runner_start_forbidden_in_this_gate",
    ]:
        if controls.get(key) is not True:
            failures.append(f"control {key} must be true")
    if controls.get("provider_credentials_required_in_this_gate") is not False:
        failures.append("provider credentials must not be required in iter50")

    pair_plans = plan.get("dry_run_pair_plans", [])
    if len(pair_plans) != 2:
        failures.append("plan must include two dry-run pair plans")
    for pair in pair_plans:
        pair_id = pair.get("pair_id")
        if pair_id not in READY_PAIR_IDS:
            failures.append(f"unexpected pair id: {pair_id}")
        if pair.get("executed_in_iter50") is not False:
            failures.append(f"{pair_id} executed in iter50")
        if pair.get("dry_run_only_in_iter50") is not True:
            failures.append(f"{pair_id} must be dry-run only")
        if pair_id not in pair.get("future_execution_command", ""):
            failures.append(f"{pair_id} command missing output root")
        future_artifacts = pair.get("future_artifact_plan", {})
        if "iter51_provider_compatible_protocol_effect_execution_with_wrapper" not in future_artifacts.get("raw_root", ""):
            failures.append(f"{pair_id} future artifact root must target iter51")
        for field in [
            "source_iter48_artifact_plan",
            "future_artifact_plan",
            "cost_capture_plan",
            "redaction_plan",
            "receipt_plan",
            "runner_lifecycle_plan",
            "metric_destinations",
            "execution_steps",
        ]:
            if not pair.get(field):
                failures.append(f"{pair_id} missing {field}")
        if [step.get("step_id") for step in pair.get("execution_steps", [])] != CAPTURE_STEP_IDS:
            failures.append(f"{pair_id} execution step ids changed")
        for step in pair.get("execution_steps", []):
            if step.get("executed_in_iter50") is not False:
                failures.append(f"{pair_id}:{step.get('step_id')} executed in iter50")
            if step.get("side_effects_allowed_in_iter50") is not False:
                failures.append(f"{pair_id}:{step.get('step_id')} permits iter50 side effects")

    rejected = plan.get("rejected_excluded_pairs", [])
    if len(rejected) != 4:
        failures.append("plan must reject four excluded pairs")
    if set(pair.get("pair_id") for pair in rejected) != EXCLUDED_PAIR_IDS:
        failures.append("rejected excluded pair ids changed")
    for pair in rejected:
        if pair.get("status") != "rejected_by_wrapper":
            failures.append(f"{pair.get('pair_id')} not rejected")
        if pair.get("attempted_in_iter50") is not False:
            failures.append(f"{pair.get('pair_id')} was attempted")
        if pair.get("future_execution_command") is not None:
            failures.append(f"{pair.get('pair_id')} should not have a future command")
        if not pair.get("rejection_reason"):
            failures.append(f"{pair.get('pair_id')} missing rejection reason")

    claim_boundary = plan.get("claim_boundary", {})
    for key in [
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "production_or_live_domain_changed",
    ]:
        if claim_boundary.get(key) is not False:
            failures.append(f"claim boundary {key} must be false")


def audit_summary(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    expected = {
        "schema_version": "telos.provider_compatible_execution_wrapper_recovery.summary.v1",
        "status": "pass",
        "experiment_id": "iter50_provider_compatible_execution_wrapper_recovery",
        "wrapper_path": WRAPPER.as_posix(),
        "selected_pair_count": 2,
        "excluded_pair_count": 4,
        "dry_run_pair_plan_count": 2,
        "rejected_pair_count": 4,
        "future_max_provider_model_invocations": 16,
        "future_max_provider_spend_usd": 10.0,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "full_provider_execution_in_iter50_enabled": False,
        "future_paid_execution_requires_next_gate": True,
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
        "next_gate": ITER51.as_posix(),
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {summary.get(key)!r}")
    if set(summary.get("selected_pair_ids", [])) != READY_PAIR_IDS:
        failures.append("summary selected pair ids changed")
    if set(summary.get("excluded_pair_ids", [])) != EXCLUDED_PAIR_IDS:
        failures.append("summary excluded pair ids changed")

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
        "provider-compatible execution wrapper recovery: pass",
        "dry_run_pair_plan_count=2",
        "rejected_pair_count=4",
        "provider_model_api_calls=0",
        "provider_spend_usd=0.0",
        "cloud_runner_started=false",
        "sentinel_named_resources_modified=false",
        "full_provider_execution_in_iter50_enabled=false",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`",
        "rejected excluded historical pairs: `4`",
        "No benchmark result is claimed",
        "No provider execution is inferred from the wrapper dry run",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in ["zero-spend dry run", "no provider spend occurred"]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.status != "pass":
        failures.append("receipt status must be pass")
    expected_id = "iter50-provider-compatible-execution-wrapper-recovery-pass"
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
    for path in [RESULT, PLAN, SUMMARY, COMMAND_OUTPUT, REVIEW, RECEIPT, WRAPPER, ITER51]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_plan(failures)
        audit_summary(failures)
        audit_text_and_receipt(failures)
        audit_secret_residue(failures)

    if failures:
        print("provider-compatible execution wrapper recovery audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("provider-compatible execution wrapper recovery audit: clean wrapper pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
