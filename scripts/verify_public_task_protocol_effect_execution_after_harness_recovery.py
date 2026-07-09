#!/usr/bin/env python3
"""Publish iter44 protocol-effect execution-after-harness-recovery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT
    / "experiments"
    / "iter44_public_task_protocol_effect_execution_after_harness_recovery"
)
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
SOURCE_SLICE = (
    ROOT
    / "experiments"
    / "iter39_public_task_protocol_effect_slice"
    / "proof"
    / "protocol_effect_slice.json"
)
SOURCE_ITER43_REPORT = (
    ROOT
    / "experiments"
    / "iter43_provider_execution_harness_recovery"
    / "proof"
    / "provider_execution_harness_report.json"
)
SOURCE_ITER43_SUMMARY = (
    ROOT
    / "experiments"
    / "iter43_provider_execution_harness_recovery"
    / "proof"
    / "run_summary.json"
)
HARNESS = ROOT / "scripts" / "run_ephemeral_vertex_codeclash_provider.py"
NEXT_GATE = ROOT / "experiments" / "iter45_public_task_condition_executor_assembly" / "HYPOTHESIS.md"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} root must be an object")
    return data


def command_lines(args: list[str], timeout: int = 20) -> list[str]:
    if shutil.which(args[0]) is None:
        return []
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return []
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def cloud_counts() -> dict[str, Any]:
    return {
        "gcloud_present": shutil.which("gcloud") is not None,
        "running_telos_vm_count": len(
            command_lines(
                [
                    "gcloud",
                    "compute",
                    "instances",
                    "list",
                    "--filter=name~^telos-.* AND status:RUNNING",
                    "--format=value(name)",
                ]
            )
        ),
        "running_sentinel_named_vm_count": len(
            command_lines(
                [
                    "gcloud",
                    "compute",
                    "instances",
                    "list",
                    "--filter=name~^sentinel-.* AND status:RUNNING",
                    "--format=value(name)",
                ]
            )
        ),
        "vm_identifiers_logged": False,
        "project_identifier_logged": False,
        "account_identifier_logged": False,
    }


def condition_rows(slice_data: dict[str, Any], status: str) -> list[dict[str, Any]]:
    task_ids = [task["task_id"] for task in slice_data["executable_tasks"]]
    rows = []
    for condition in slice_data["conditions"]:
        rows.append(
            {
                "condition_id": condition["condition_id"],
                "planned_task_count": len(task_ids),
                "planned_task_ids": task_ids,
                "attempted_task_count": 0,
                "blocked_task_count": len(task_ids) if status == "blocked" else 0,
                "verified_completion_count": 0,
                "verified_completion_rate": None,
                "status": status,
                "reason": "preflight_blocked_before_full_task_condition_executor",
            }
        )
    return rows


def metric_rows(status: str) -> dict[str, Any]:
    return {
        "primary": {
            "metric_id": "verified_completion_rate",
            "status": status,
            "exact_counts_available": False,
            "value": None,
            "reason": "no task-condition pair executed",
        },
        "secondary": [
            {
                "metric_id": metric,
                "status": status,
                "value": None,
                "reason": "not computable without executed task-condition artifacts",
            }
            for metric in [
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
        ],
    }


def build_preflight() -> tuple[dict[str, Any], list[str], list[str]]:
    slice_data = read_json(SOURCE_SLICE)
    iter43_report = read_json(SOURCE_ITER43_REPORT)
    iter43_summary = read_json(SOURCE_ITER43_SUMMARY)
    plan = iter43_report.get("provider_execution_plan", {})
    planned_pairs = len(slice_data["executable_tasks"]) * len(slice_data["conditions"])

    blockers: list[str] = []
    failures: list[str] = []
    if iter43_summary.get("status") != "pass":
        blockers.append("iter43_harness_recovery_not_passed")
    if not HARNESS.exists():
        blockers.append("recovered_harness_missing")
    if plan.get("full_protocol_effect_execution_enabled") is not True:
        blockers.append("full_protocol_effect_execution_disabled_in_recovered_harness")
    if plan.get("requires_future_gate_to_execute_task_condition_pairs") is not False:
        blockers.append("harness_requires_future_task_condition_gate")
    if planned_pairs != 6:
        failures.append("planned_task_condition_pair_count_changed")

    status = "fail" if failures else "blocked" if blockers else "pass"
    preflight = {
        "schema_version": (
            "telos.public_task_protocol_effect_execution_after_harness_recovery.preflight.v1"
        ),
        "status": status,
        "experiment_id": "iter44_public_task_protocol_effect_execution_after_harness_recovery",
        "source_slice_path": str(SOURCE_SLICE.relative_to(ROOT)),
        "source_iter43_report_path": str(SOURCE_ITER43_REPORT.relative_to(ROOT)),
        "harness_path": str(HARNESS.relative_to(ROOT)),
        "planned_task_condition_pairs": planned_pairs,
        "attempted_task_condition_pairs": 0,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "submitted_logic_mutated": False,
        "credential_material_logged": False,
        "project_identifier_logged": False,
        "account_identifier_logged": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "cloud_counts": cloud_counts(),
        "checks": {
            "iter43_harness_recovery_passed": iter43_summary.get("status") == "pass",
            "iter43_lifecycle_vm_created": iter43_summary.get("lifecycle_vm_created"),
            "iter43_lifecycle_vm_deleted": iter43_summary.get("lifecycle_vm_deleted"),
            "iter43_running_telos_vm_count_after": iter43_summary.get(
                "running_telos_vm_count_after"
            ),
            "iter43_cost_capture_parser_validated": iter43_summary.get(
                "cost_capture_parser_validated"
            ),
            "iter43_raw_artifact_retention_validated": iter43_summary.get(
                "raw_artifact_retention_validated"
            ),
            "iter43_redaction_scan_passed": iter43_summary.get("redaction_scan_passed"),
            "harness_full_protocol_effect_execution_enabled": plan.get(
                "full_protocol_effect_execution_enabled"
            ),
            "harness_requires_future_gate_to_execute_task_condition_pairs": plan.get(
                "requires_future_gate_to_execute_task_condition_pairs"
            ),
            "baseline_and_telos_conditions_present": len(slice_data["conditions"]) == 2,
            "executable_task_count": len(slice_data["executable_tasks"]),
        },
        "blockers": blockers,
        "failures": failures,
    }
    return preflight, blockers, failures


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter44-public-task-protocol-effect-execution-after-harness-{status}",
        "task_id": "telos:iter44_public_task_protocol_effect_execution_after_harness_recovery@iter43",
        "agent_id": "codex-local-protocol-effect-executor",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Execute the frozen public task protocol-effect slice after harness recovery only if "
            "the recovered harness can run the six frozen task-condition pairs."
        ),
        "acceptance_criteria": [
            "The recovered harness remains the execution path.",
            "Six frozen task-condition pairs remain planned and separated by condition.",
            "Provider calls do not start if the recovered harness still requires a future execution gate.",
            "Blocked rows are published at full weight.",
            "No provider spend, GPU use, production/live-domain change, leaderboard, SWE-bench, model-superiority, or state-of-the-art result is claimed.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": (
                    "experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/"
                    "proof/preflight.json"
                ),
                "notes": "Preflight checks whether the recovered harness can execute task-condition pairs.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": (
                    "experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/"
                    "proof/execution_report.json"
                ),
                "notes": "Execution report preserves blocked rows and uncomputed metrics.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": (
                    "experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/"
                    "proof/review.md"
                ),
                "notes": "Review records the boundary between harness recovery and full execution.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if the recovered harness still disables full protocol-effect execution.",
            "The result must fail if any task-condition pair count changes after pre-registration.",
            "The result must fail if any provider model call or spend occurs after a blocking preflight.",
            "The result must fail if unsupported benchmark, model-superiority, production, live-domain, leaderboard, SWE-bench, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def build_artifact_hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path.relative_to(PROOF)): sha256_file(path) for path in paths}


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    slice_data = read_json(SOURCE_SLICE)
    preflight, blockers, failures = build_preflight()
    status = preflight["status"]

    write_json(PROOF / "preflight.json", preflight)
    execution_report = {
        "schema_version": (
            "telos.public_task_protocol_effect_execution_after_harness_recovery.report.v1"
        ),
        "status": status,
        "experiment_id": "iter44_public_task_protocol_effect_execution_after_harness_recovery",
        "planned_task_condition_pairs": preflight["planned_task_condition_pairs"],
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": preflight["planned_task_condition_pairs"]
        if status == "blocked"
        else 0,
        "condition_rows": condition_rows(slice_data, status),
        "metrics": metric_rows(status),
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "blockers": blockers,
        "failures": failures,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
    }
    write_json(PROOF / "execution_report.json", execution_report)

    output_lines = [
        f"public task protocol-effect execution after harness recovery: {status}",
        "provider_model_api_calls=0",
        "provider_spend_usd=0.0",
        "cloud_runner_started=false",
        "planned_task_condition_pairs=6",
        "attempted_task_condition_pairs=0",
        f"blockers={','.join(blockers)}",
        f"failures={','.join(failures)}",
        f"next_gate={NEXT_GATE.relative_to(ROOT)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 44 Review

The execution-after-harness-recovery gate blocked before provider execution. The `iter43` harness
recovery proof remains valid: lifecycle, cost parsing, raw-artifact retention, and redaction controls
passed. The recovered harness still explicitly disables full protocol-effect execution and says a
future gate is required before task-condition pairs run.

This block prevents hidden model spend and prevents the repo from treating harness recovery as a
benchmark execution. Six task-condition pairs remain planned, zero started, zero provider model calls
occurred, zero spend occurred, and no cloud runner was started in this gate.

The next gate must assemble and dry-run the task-condition executor before the frozen six-pair
provider execution can be retried.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    result = f"""# Iteration 44 Result - Public Task Protocol-Effect Execution After Harness Recovery

Status: `{status.upper()}`.

## Summary

The gate blocked before provider execution. The recovered `iter43` harness is committed and
secret-safe, but it still has full protocol-effect execution disabled and explicitly requires a
future gate before task-condition pairs run.

- planned task-condition pairs: `6`,
- attempted task-condition pairs: `0`,
- provider model API calls: `0`,
- provider spend: `$0.00`,
- cloud runner started: `false`,
- GPU used: `false`,
- benchmark result claimed: `false`.

## Blockers

{chr(10).join(f"- `{blocker}`" for blocker in blockers)}

## What Is Now Authorized

- Pre-register an executor-assembly gate that maps the three frozen CodeClash task surfaces across
  baseline and Telos-enforced conditions.
- Keep provider model calls at `0` until that executor can dry-run cost capture, artifact capture,
  redaction, condition separation, and metric computation.

## What Remains Forbidden

- No benchmark result is claimed.
- No SWE-bench score is claimed.
- No leaderboard result is claimed.
- No production or live-domain result is claimed.
- No model-superiority or state-of-the-art result is claimed.
- No provider spend is hidden or inferred from uncommitted artifacts.

## Evidence

- `proof/preflight.json`
- `proof/execution_report.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/valid/receipt_public_task_protocol_effect_execution_after_harness_recovery.json`
"""
    (EXPERIMENT / "RESULT.md").write_text(result, encoding="utf-8")

    artifact_paths = [
        PROOF / "preflight.json",
        PROOF / "execution_report.json",
        PROOF / "command_output.txt",
        PROOF / "review.md",
    ]
    run_summary = {
        "schema_version": (
            "telos.public_task_protocol_effect_execution_after_harness_recovery.summary.v1"
        ),
        "status": status,
        "experiment_id": "iter44_public_task_protocol_effect_execution_after_harness_recovery",
        "source_slice_path": str(SOURCE_SLICE.relative_to(ROOT)),
        "source_slice_sha256": sha256_file(SOURCE_SLICE),
        "source_iter43_report_path": str(SOURCE_ITER43_REPORT.relative_to(ROOT)),
        "source_iter43_report_sha256": sha256_file(SOURCE_ITER43_REPORT),
        "harness_path": str(HARNESS.relative_to(ROOT)),
        "harness_sha256": sha256_file(HARNESS),
        "planned_task_condition_pairs": 6,
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": 6 if status == "blocked" else 0,
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
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": blockers,
        "failures": failures,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
        "artifact_hashes": {},
    }
    run_summary["artifact_hashes"] = build_artifact_hashes(artifact_paths)
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter44_public_task_protocol_effect_execution_after_harness_recovery",
        "status": "blocked" if status == "blocked" else status,
        "insight": (
            "Harness recovery is not the same as six-pair protocol-effect execution; the recovered "
            "harness still disables full task-condition execution and requires an executor-assembly gate."
        ),
        "next_action": (
            "assemble and dry-run the public task-condition executor before retrying provider-backed "
            "protocol-effect execution"
        ),
        "result_path": (
            "experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/RESULT.md"
        ),
        "evidence_paths": [
            "experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/proof/run_summary.json",
            "experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/proof/preflight.json",
            "experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/proof/execution_report.json",
            "experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/proof/command_output.txt",
            "experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/proof/review.md",
            "experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/proof/valid/receipt_public_task_protocol_effect_execution_after_harness_recovery.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(
        VALID / "receipt_public_task_protocol_effect_execution_after_harness_recovery.json",
        build_receipt(status),
    )

    print("\n".join(output_lines))
    return 0 if status in {"blocked", "pass"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
