#!/usr/bin/env python3
"""Audit the iter39 public-task protocol-effect slice proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter39_public_task_protocol_effect_slice")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
SLICE = PROOF / "protocol_effect_slice.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
SOURCES = PROOF / "sources.md"
RECEIPT = PROOF / "valid" / "receipt_public_task_protocol_effect_slice.json"
ITER40 = Path("experiments/iter40_public_task_protocol_effect_execution/HYPOTHESIS.md")

EXPECTED_TASK_IDS = [
    "codeclash:configs/test/dummy.yaml",
    "codeclash:configs/test/battlesnake_pvp_test.yaml",
    "codeclash:configs/test/telos_battlesnake_edit_test.yaml",
]
EXPECTED_SECONDARY = [
    "proxy_pass_receipt_fail_rate",
    "unsupported_claim_rate",
    "over_edit_rate",
    "evidence_missing_rate",
    "audit_minutes_per_task",
    "false_positive_rate",
    "false_negative_rate",
    "model_api_calls_per_task",
    "cost_usd_per_task",
]


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be an object")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_summary(failures: list[str]) -> None:
    data = load_json(SUMMARY)
    expected = {
        "schema_version": "telos.public_task_protocol_effect_slice.summary.v1",
        "status": "pass",
        "experiment_id": "iter39_public_task_protocol_effect_slice",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "slice_id": "telos_codeclash_swebench_protocol_effect_pilot_v1",
        "executable_task_count": 3,
        "supporting_receipt_anchor": "astropy__astropy-12907",
        "condition_count": 2,
        "planned_task_condition_pairs": 6,
        "primary_metric": "verified_completion_rate",
        "secondary_metric_count": 9,
        "next_gate": ITER40.as_posix(),
        "next_gate_dollar_ceiling_usd": 25,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "failed_check_count": 0,
        "failed_checks": [],
        "clean_pass": True,
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {data.get(key)!r}")

    hashes = data.get("artifact_hashes", {})
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
            failures.append(
                f"hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}"
            )


def audit_slice(failures: list[str]) -> None:
    data = load_json(SLICE)
    if data.get("schema_version") != "telos.public_task_protocol_effect_slice.v1":
        failures.append("slice schema_version mismatch")
    if data.get("status") != "selected":
        failures.append("slice status must be selected")
    if data.get("slice_id") != "telos_codeclash_swebench_protocol_effect_pilot_v1":
        failures.append("slice_id mismatch")

    task_ids = [task.get("task_id") for task in data.get("executable_tasks", [])]
    if task_ids != EXPECTED_TASK_IDS:
        failures.append(f"task ids mismatch: {task_ids}")
    for task in data.get("executable_tasks", []):
        if not str(task.get("public_config", "")).startswith("configs/test/"):
            failures.append(f"task public_config must be CodeClash configs/test: {task}")
        if not task.get("first_run_command"):
            failures.append(f"task missing first_run_command: {task.get('task_id')}")

    conditions = [item.get("condition_id") for item in data.get("conditions", [])]
    if conditions != [
        "baseline_agent_completion_evidence",
        "telos_receipt_enforced_completion_evidence",
    ]:
        failures.append("conditions must include baseline then Telos-enforced")

    primary = data.get("metrics", {}).get("primary", {})
    if primary.get("metric_id") != "verified_completion_rate":
        failures.append("primary metric mismatch")
    secondary = [
        metric.get("metric_id")
        for metric in data.get("metrics", {}).get("secondary", [])
    ]
    if secondary != EXPECTED_SECONDARY:
        failures.append(f"secondary metrics mismatch: {secondary}")

    boundary = data.get("provider_execution_boundary_for_next_gate", {})
    expected_boundary = {
        "next_gate_path": ITER40.as_posix(),
        "provider_authorized_only_in_next_gate": True,
        "provider_name": "Google Vertex AI",
        "model_id": "gemini-3.1-pro-preview-customtools",
        "base_model_id": "gemini-3.1-pro-preview",
        "region": "global",
        "max_model_invocations": 48,
        "dollar_ceiling_usd": 25,
        "wall_clock_ceiling_minutes": 90,
        "stop_if_cost_missing": True,
        "stop_if_credentials_or_runner_unavailable": True,
    }
    for key, value in expected_boundary.items():
        if boundary.get(key) != value:
            failures.append(f"boundary {key} expected {value!r}, got {boundary.get(key)!r}")

    claims = data.get("claim_boundaries", {})
    for key in [
        "leaderboard_or_swebench_result_claimed",
        "model_superiority_claimed",
        "production_or_live_domain_changed",
        "general_battlesnake_strength_claimed",
        "state_of_the_art_result_claimed",
    ]:
        if claims.get(key) is not False:
            failures.append(f"claim boundary {key} must be false")

    if len(data.get("negative_controls", [])) < 5:
        failures.append("negative_controls must contain at least five entries")


def audit_text_and_receipt(failures: list[str]) -> None:
    output = COMMAND_OUTPUT.read_text(encoding="utf-8")
    for required in [
        "public task protocol effect slice: pass",
        "provider_api_calls=0",
        "executable_tasks=3",
        "conditions=2",
        "primary_metric=verified_completion_rate",
        "secondary_metrics=9",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`",
        "baseline condition",
        "Telos-enforced condition",
        "No provider model was called",
        "This is not a leaderboard result",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in ["slice-selection result", "does not run a provider model"]:
        if required not in review:
            failures.append(f"review missing: {required}")

    sources = SOURCES.read_text(encoding="utf-8")
    for required in [
        "https://github.com/codeclash-ai/codeclash",
        "https://www.swebench.com/verified.html",
        "https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified",
    ]:
        if required not in sources:
            failures.append(f"sources missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.receipt_id != "iter39-public-task-protocol-effect-slice-pass":
        failures.append("unexpected receipt id")
    if receipt.status != "pass":
        failures.append("receipt status must be pass")


def audit_no_generated_residue(failures: list[str]) -> None:
    for path in PROOF.rglob("*"):
        if not path.is_file():
            continue
        if path.name.endswith((".pyc", ".tar", ".gz", ".zip")) or "__pycache__" in path.parts:
            failures.append(f"forbidden generated/binary artifact committed: {path}")


def main() -> int:
    failures: list[str] = []
    for path in [RESULT, SUMMARY, SLICE, COMMAND_OUTPUT, REVIEW, SOURCES, RECEIPT, ITER40]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_summary(failures)
        audit_slice(failures)
        audit_text_and_receipt(failures)
        audit_no_generated_residue(failures)

    if failures:
        print("public task protocol effect slice audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("public task protocol effect slice audit: clean slice pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
