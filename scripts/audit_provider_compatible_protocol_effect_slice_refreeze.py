#!/usr/bin/env python3
"""Audit iter48 provider-compatible protocol-effect slice-refreeze artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter48_provider_compatible_protocol_effect_slice_refreeze")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SLICE = PROOF / "provider_compatible_slice.json"
SUMMARY = PROOF / "run_summary.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECEIPT = PROOF / "valid" / "receipt_provider_compatible_protocol_effect_slice_refreeze.json"
ITER49 = Path("experiments/iter49_provider_compatible_protocol_effect_execution_retry/HYPOTHESIS.md")
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
EXPECTED_CONDITIONS = {
    "baseline_agent_completion_evidence",
    "telos_receipt_enforced_completion_evidence",
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


def audit_slice(failures: list[str]) -> None:
    data = load_json(SLICE)
    expected = {
        "schema_version": "telos.provider_compatible_protocol_effect_slice_refreeze.v1",
        "status": "pass",
        "source_command_binding_status": "blocked",
        "source_executor_manifest_status": "dry_run_ready",
        "source_protocol_effect_slice_status": "selected",
        "original_pair_count": 6,
        "selected_pair_count": 2,
        "excluded_pair_count": 4,
        "selected_task_count": 1,
        "selected_condition_count": 2,
        "selected_public_configs": ["configs/test/battlesnake_pvp_test.yaml"],
        "condition_balanced": True,
        "iter48_provider_model_api_calls": 0,
        "iter48_provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "blockers": [],
        "failures": [],
        "next_gate": ITER49.as_posix(),
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"slice {key} expected {value!r}, got {data.get(key)!r}")
    if set(data.get("selected_pair_ids", [])) != READY_PAIR_IDS:
        failures.append("selected pair ids changed")
    if set(data.get("excluded_pair_ids", [])) != EXCLUDED_PAIR_IDS:
        failures.append("excluded pair ids changed")
    if set(data.get("selected_condition_ids", [])) != EXPECTED_CONDITIONS:
        failures.append("selected condition ids changed")
    if len(data.get("all_original_pair_ids", [])) != 6:
        failures.append("all original pair ids must preserve six pairs")

    budget = data.get("future_execution_budget", {})
    if budget.get("max_provider_model_invocations") != 16:
        failures.append("future invocation ceiling must be 16")
    if budget.get("max_provider_spend_usd") != 10.0:
        failures.append("future spend ceiling must be 10.0")
    if budget.get("gpu_allowed") is not False:
        failures.append("future budget must forbid GPU")
    if budget.get("sentinel_named_resources_must_not_change") is not True:
        failures.append("future budget must preserve Sentinel isolation")

    for pair in data.get("selected_pairs", []):
        pair_id = pair.get("pair_id")
        if pair_id not in READY_PAIR_IDS:
            failures.append(f"unexpected selected pair: {pair_id}")
        if pair.get("binding_status") != "provider_backed_command_ready":
            failures.append(f"{pair_id} must be provider-backed ready")
        for key in [
            "provider_overlay_config",
            "provider_agent_config",
            "provider_model_config",
            "provider_cost_registry",
            "future_execution_command",
            "artifact_plan",
            "cost_capture_plan",
            "redaction_plan",
            "receipt_plan",
            "runner_lifecycle_plan",
            "metric_destinations",
        ]:
            if not pair.get(key):
                failures.append(f"{pair_id} missing {key}")
        command = pair.get("future_execution_command", "")
        if "telos_battlesnake_vertex_gemini_pilot.yaml" not in command:
            failures.append(f"{pair_id} command missing provider config")
        if pair_id not in command:
            failures.append(f"{pair_id} command missing pair output root")

    for pair in data.get("excluded_pairs", []):
        pair_id = pair.get("pair_id")
        if pair_id not in EXCLUDED_PAIR_IDS:
            failures.append(f"unexpected excluded pair: {pair_id}")
        if pair.get("binding_status") != "provider_binding_incompatible":
            failures.append(f"{pair_id} excluded without incompatible binding")
        if not pair.get("exclusion_reason"):
            failures.append(f"{pair_id} missing exclusion reason")

    claim_boundary = data.get("claim_boundary", {})
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
        "schema_version": "telos.provider_compatible_protocol_effect_slice_refreeze.summary.v1",
        "status": "pass",
        "experiment_id": "iter48_provider_compatible_protocol_effect_slice_refreeze",
        "original_pair_count": 6,
        "selected_pair_count": 2,
        "excluded_pair_count": 4,
        "selected_public_configs": ["configs/test/battlesnake_pvp_test.yaml"],
        "selected_condition_ids": sorted(EXPECTED_CONDITIONS),
        "condition_balanced": True,
        "future_max_provider_model_invocations": 16,
        "future_max_provider_spend_usd": 10.0,
        "iter48_provider_model_api_calls": 0,
        "iter48_provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
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
        "next_gate": ITER49.as_posix(),
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
        "provider-compatible protocol-effect slice refreeze: pass",
        "original_pair_count=6",
        "selected_pair_count=2",
        "excluded_pair_count=4",
        "condition_balanced=true",
        "iter48_provider_model_api_calls=0",
        "iter48_provider_spend_usd=0.0",
        "future_max_provider_model_invocations=16",
        "future_max_provider_spend_usd=10.0",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`",
        "selected provider-compatible pairs: `2`",
        "excluded historical pairs: `4`",
        "No excluded Dummy or deterministic-edit pair may be silently included",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in ["selected only the two BattleSnake", "four Dummy and deterministic-edit"]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.status != "pass":
        failures.append("receipt status must be pass")
    expected_id = "iter48-provider-compatible-protocol-effect-slice-refreeze-pass"
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
    for path in [RESULT, SLICE, SUMMARY, COMMAND_OUTPUT, REVIEW, RECEIPT, ITER49]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_slice(failures)
        audit_summary(failures)
        audit_text_and_receipt(failures)
        audit_secret_residue(failures)

    if failures:
        print("provider-compatible protocol-effect slice refreeze audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("provider-compatible protocol-effect slice refreeze audit: clean pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
