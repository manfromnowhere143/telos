#!/usr/bin/env python3
"""Audit the iter45 public task-condition executor-assembly proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter45_public_task_condition_executor_assembly")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
MANIFEST = PROOF / "executor_manifest.json"
SUMMARY = PROOF / "run_summary.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECEIPT = PROOF / "valid" / "receipt_public_task_condition_executor_assembly.json"
ITER46 = Path(
    "experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor/HYPOTHESIS.md"
)
EXPECTED_CONDITIONS = {
    "baseline_agent_completion_evidence",
    "telos_receipt_enforced_completion_evidence",
}
REQUIRED_PAIR_FIELDS = {
    "artifact_plan",
    "cost_capture_plan",
    "redaction_plan",
    "receipt_plan",
    "metric_destinations",
    "lifecycle_plan",
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


def audit_manifest(failures: list[str]) -> None:
    manifest = load_json(MANIFEST)
    expected = {
        "schema_version": "telos.public_task_condition_executor_manifest.v1",
        "status": "dry_run_ready",
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "full_execution_enabled": False,
        "requires_future_gate_for_provider_execution": True,
        "task_count": 3,
        "condition_count": 2,
        "planned_task_condition_pairs": 6,
        "next_gate": ITER46.as_posix(),
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            failures.append(f"manifest {key} expected {value!r}, got {manifest.get(key)!r}")

    pairs = manifest.get("pairs", [])
    if not isinstance(pairs, list) or len(pairs) != 6:
        failures.append("manifest must contain exactly six pairs")
        return

    pair_ids = [pair.get("pair_id") for pair in pairs if isinstance(pair, dict)]
    if len(set(pair_ids)) != 6:
        failures.append("manifest pair ids must be unique")
    if manifest.get("pair_ids") != pair_ids:
        failures.append("manifest pair_ids must match pairs")
    if {pair.get("condition_id") for pair in pairs} != EXPECTED_CONDITIONS:
        failures.append("manifest condition ids changed")
    if len({pair.get("task_id") for pair in pairs}) != 3:
        failures.append("manifest must contain three task ids")

    controls = manifest.get("controls", {})
    for key in [
        "iter43_harness_recovery_passed",
        "iter43_lifecycle_vm_deleted",
        "iter44_blocked_before_provider_execution",
        "provider_execution_forbidden_in_this_gate",
        "cloud_runner_start_forbidden_in_this_gate",
    ]:
        if controls.get(key) is not True:
            failures.append(f"manifest control {key} must be true")
    if controls.get("exact_pair_count_required") != 6:
        failures.append("exact pair count control must be 6")
    if controls.get("duplicate_pair_ids_allowed") is not False:
        failures.append("duplicate pair ids must be forbidden")

    for pair in pairs:
        missing = sorted(REQUIRED_PAIR_FIELDS - set(pair))
        if missing:
            failures.append(f"{pair.get('pair_id')} missing required fields: {', '.join(missing)}")
        if pair.get("dry_run_only_in_iter45") is not True:
            failures.append(f"{pair.get('pair_id')} must be dry-run only")
        if pair.get("full_execution_enabled") is not False:
            failures.append(f"{pair.get('pair_id')} must not enable full execution")
        for field in REQUIRED_PAIR_FIELDS:
            if not pair.get(field):
                failures.append(f"{pair.get('pair_id')} {field} must be non-empty")
        metrics = pair.get("metric_destinations", {})
        if "verified_completion_rate" not in metrics.get("primary", ""):
            failures.append(f"{pair.get('pair_id')} missing primary metric destination")
        if len(metrics.get("secondary", [])) != 9:
            failures.append(f"{pair.get('pair_id')} must include nine secondary metrics")

    claim_boundary = manifest.get("claim_boundary", {})
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
        "schema_version": "telos.public_task_condition_executor_assembly.summary.v1",
        "status": "pass",
        "experiment_id": "iter45_public_task_condition_executor_assembly",
        "planned_task_condition_pairs": 6,
        "task_count": 3,
        "condition_count": 2,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "full_execution_enabled": False,
        "requires_future_gate_for_provider_execution": True,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "clean_pass": True,
        "blocked_result": False,
        "quality_failure": False,
        "failures": [],
        "next_gate": ITER46.as_posix(),
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {summary.get(key)!r}")
    if len(summary.get("pair_ids", [])) != 6 or len(set(summary.get("pair_ids", []))) != 6:
        failures.append("summary must contain six unique pair ids")

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
        "public task-condition executor assembly: pass",
        "planned_task_condition_pairs=6",
        "provider_model_api_calls=0",
        "provider_spend_usd=0.0",
        "cloud_runner_started=false",
        "full_execution_enabled=false",
        "requires_future_gate_for_provider_execution=true",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`",
        "planned task-condition pairs: `6`",
        "No benchmark result is claimed",
        "No provider execution is inferred from the dry-run manifest",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in ["dry-run-only result", "No provider model call occurred"]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.status != "pass":
        failures.append("receipt status must be pass")
    if receipt.receipt_id != "iter45-public-task-condition-executor-assembly-pass":
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
    for path in [RESULT, MANIFEST, SUMMARY, COMMAND_OUTPUT, REVIEW, RECEIPT, ITER46]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")

    if not failures:
        audit_manifest(failures)
        audit_summary(failures)
        audit_text_and_receipt(failures)
        audit_secret_residue(failures)

    if failures:
        print("public task-condition executor assembly audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("public task-condition executor assembly audit: clean pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
