#!/usr/bin/env python3
"""Audit iter47 provider task-condition command-binding recovery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter47_provider_task_condition_command_binding_recovery")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
REPORT = PROOF / "command_binding_report.json"
SUMMARY = PROOF / "run_summary.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECEIPT = PROOF / "valid" / "receipt_provider_task_condition_command_binding_recovery.json"
ITER48 = Path("experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/HYPOTHESIS.md")
READY_PAIR_IDS = {
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
}
INCOMPATIBLE_PAIR_IDS = {
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


def audit_report(failures: list[str]) -> None:
    report = load_json(REPORT)
    expected = {
        "schema_version": "telos.provider_task_condition_command_binding_report.v1",
        "status": "blocked",
        "planned_task_condition_pairs": 6,
        "provider_backed_ready_pair_count": 2,
        "provider_binding_incompatible_pair_count": 4,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "full_execution_enabled": False,
        "requires_future_slice_refreeze": True,
        "failures": [],
        "next_gate": ITER48.as_posix(),
    }
    for key, value in expected.items():
        if report.get(key) != value:
            failures.append(f"report {key} expected {value!r}, got {report.get(key)!r}")
    if set(report.get("provider_backed_ready_pair_ids", [])) != READY_PAIR_IDS:
        failures.append("provider-backed ready pair ids changed")
    if set(report.get("provider_binding_incompatible_pair_ids", [])) != INCOMPATIBLE_PAIR_IDS:
        failures.append("provider-binding incompatible pair ids changed")
    if "provider_binding_incompatible_pairs_present" not in report.get("blockers", []):
        failures.append("report missing incompatible-pairs blocker")
    bindings = report.get("bindings", [])
    if len(bindings) != 6:
        failures.append("report must include six bindings")
        return
    for binding in bindings:
        pair_id = binding.get("pair_id")
        status = binding.get("binding_status")
        if pair_id in READY_PAIR_IDS:
            if status != "provider_backed_command_ready":
                failures.append(f"{pair_id} should be provider-backed ready")
            for key in [
                "provider_overlay_config",
                "provider_agent_config",
                "provider_model_config",
                "provider_cost_registry",
                "future_execution_command",
            ]:
                if not binding.get(key):
                    failures.append(f"{pair_id} missing {key}")
            if "telos_battlesnake_vertex_gemini_pilot.yaml" not in binding.get(
                "future_execution_command", ""
            ):
                failures.append(f"{pair_id} missing provider config command")
        elif pair_id in INCOMPATIBLE_PAIR_IDS:
            if status != "provider_binding_incompatible":
                failures.append(f"{pair_id} should be incompatible")
            if not binding.get("incompatibility_reason"):
                failures.append(f"{pair_id} missing incompatibility reason")
            if binding.get("future_execution_command") is not None:
                failures.append(f"{pair_id} incompatible binding has execution command")
        else:
            failures.append(f"unexpected pair id: {pair_id}")
    claim_boundary = report.get("claim_boundary", {})
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
        "schema_version": "telos.provider_task_condition_command_binding_recovery.summary.v1",
        "status": "blocked",
        "experiment_id": "iter47_provider_task_condition_command_binding_recovery",
        "planned_task_condition_pairs": 6,
        "provider_backed_ready_pair_count": 2,
        "provider_binding_incompatible_pair_count": 4,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "full_execution_enabled": False,
        "requires_future_slice_refreeze": True,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "clean_pass": False,
        "blocked_result": True,
        "quality_failure": False,
        "failures": [],
        "next_gate": ITER48.as_posix(),
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {summary.get(key)!r}")
    if set(summary.get("provider_backed_ready_pair_ids", [])) != READY_PAIR_IDS:
        failures.append("summary provider-backed pair ids changed")
    if set(summary.get("provider_binding_incompatible_pair_ids", [])) != INCOMPATIBLE_PAIR_IDS:
        failures.append("summary incompatible pair ids changed")
    if "provider_binding_incompatible_pairs_present" not in summary.get("blockers", []):
        failures.append("summary missing incompatible-pairs blocker")
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
        "provider task-condition command binding recovery: blocked",
        "planned_task_condition_pairs=6",
        "provider_backed_ready_pair_count=2",
        "provider_binding_incompatible_pair_count=4",
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
        "provider-backed command-ready pairs: `2`",
        "provider-binding incompatible pairs: `4`",
        "No incompatible task surface is relabeled as provider-backed",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in ["blocked and narrowed", "two concrete provider-backed commands"]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.status != "blocked":
        failures.append("receipt status must be blocked")
    expected_id = "iter47-provider-task-condition-command-binding-recovery-blocked"
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
    for path in [RESULT, REPORT, SUMMARY, COMMAND_OUTPUT, REVIEW, RECEIPT, ITER48]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_report(failures)
        audit_summary(failures)
        audit_text_and_receipt(failures)
        audit_secret_residue(failures)

    if failures:
        print("provider task-condition command binding recovery audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("provider task-condition command binding recovery audit: clean blocked result")
    return 0


if __name__ == "__main__":
    sys.exit(main())
