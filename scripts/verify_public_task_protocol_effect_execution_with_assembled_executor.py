#!/usr/bin/env python3
"""Publish iter46 execution-with-assembled-executor artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = (
    ROOT
    / "experiments"
    / "iter46_public_task_protocol_effect_execution_with_assembled_executor"
)
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
SOURCE_MANIFEST = (
    ROOT
    / "experiments"
    / "iter45_public_task_condition_executor_assembly"
    / "proof"
    / "executor_manifest.json"
)
SOURCE_ITER43_REPORT = (
    ROOT
    / "experiments"
    / "iter43_provider_execution_harness_recovery"
    / "proof"
    / "provider_execution_harness_report.json"
)
NEXT_GATE = (
    ROOT / "experiments" / "iter47_provider_task_condition_command_binding_recovery" / "HYPOTHESIS.md"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} root must be an object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter46-public-task-protocol-effect-execution-with-assembled-executor-{status}",
        "task_id": "telos:iter46_public_task_protocol_effect_execution_with_assembled_executor@iter45",
        "agent_id": "codex-local-protocol-effect-executor",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Execute the frozen six-pair public task protocol-effect slice only if the assembled "
            "executor binds provider-backed commands concretely and the recovered harness enables execution."
        ),
        "acceptance_criteria": [
            "The iter45 executor manifest remains present and audited.",
            "Provider-backed pair commands must be concrete before any pair is run.",
            "The recovered harness must not require a future task-condition gate before execution.",
            "No provider spend, cloud runner startup, GPU use, or model invocation occurs after a blocking preflight.",
            "No benchmark, leaderboard, SWE-bench, production, live-domain, model-superiority, or state-of-the-art result is claimed.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": (
                    "experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor/"
                    "proof/preflight.json"
                ),
                "notes": "Preflight records why six-pair provider-backed execution did not start.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": (
                    "experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor/"
                    "proof/execution_report.json"
                ),
                "notes": "Execution report preserves blocked condition rows and uncomputed metrics.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": (
                    "experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor/"
                    "proof/review.md"
                ),
                "notes": "Review records the command-binding gap and claim boundary.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if provider-backed pair commands are not concrete before execution.",
            "The result must block if the recovered harness still requires a future task-condition gate.",
            "The result must fail if any task-condition pair is executed after a blocking preflight.",
            "The result must fail if provider spend, GPU use, cloud runner startup, or model calls occur after a blocking preflight.",
            "The result must fail if unsupported benchmark, model-superiority, production, live-domain, leaderboard, SWE-bench, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def build_artifact_hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path.relative_to(PROOF)): sha256_file(path) for path in paths}


def condition_rows(manifest: dict[str, Any], status: str) -> list[dict[str, Any]]:
    rows = []
    for condition_id in sorted({pair["condition_id"] for pair in manifest["pairs"]}):
        task_ids = [
            pair["task_id"] for pair in manifest["pairs"] if pair["condition_id"] == condition_id
        ]
        rows.append(
            {
                "condition_id": condition_id,
                "planned_task_count": len(task_ids),
                "planned_task_ids": task_ids,
                "attempted_task_count": 0,
                "blocked_task_count": len(task_ids) if status == "blocked" else 0,
                "verified_completion_count": 0,
                "verified_completion_rate": None,
                "status": status,
                "reason": "preflight_blocked_before_provider_command_binding",
            }
        )
    return rows


def metric_rows(status: str) -> dict[str, Any]:
    secondary = [
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
                "reason": "not computable without executed provider-backed pair artifacts",
            }
            for metric in secondary
        ],
    }


def build_preflight() -> tuple[dict[str, Any], list[str], list[str]]:
    manifest = read_json(SOURCE_MANIFEST)
    iter43_report = read_json(SOURCE_ITER43_REPORT)
    plan = iter43_report.get("provider_execution_plan", {})
    pairs = manifest.get("pairs", [])
    provider_overlays = manifest.get("provider_overlay_paths", [])
    pair_command_templates = [
        pair.get("future_execution_command_template", "") for pair in pairs if isinstance(pair, dict)
    ]

    blockers: list[str] = []
    failures: list[str] = []
    if manifest.get("planned_task_condition_pairs") != 6 or len(pairs) != 6:
        failures.append("assembled_executor_pair_count_changed")
    if manifest.get("status") != "dry_run_ready":
        blockers.append("assembled_executor_not_dry_run_ready")
    if not provider_overlays:
        blockers.append("provider_overlay_paths_missing")
    if any("telos_vertex" not in template for template in pair_command_templates):
        blockers.append("provider_overlay_not_bound_to_pair_commands")
    if plan.get("full_protocol_effect_execution_enabled") is not True:
        blockers.append("recovered_harness_full_execution_disabled")
    if plan.get("requires_future_gate_to_execute_task_condition_pairs") is not False:
        blockers.append("recovered_harness_requires_future_task_condition_gate")
    if not NEXT_GATE.exists():
        blockers.append("next_command_binding_gate_missing")

    status = "fail" if failures else "blocked" if blockers else "pass"
    preflight = {
        "schema_version": (
            "telos.public_task_protocol_effect_execution_with_assembled_executor.preflight.v1"
        ),
        "status": status,
        "experiment_id": "iter46_public_task_protocol_effect_execution_with_assembled_executor",
        "source_manifest_path": str(SOURCE_MANIFEST.relative_to(ROOT)),
        "source_iter43_report_path": str(SOURCE_ITER43_REPORT.relative_to(ROOT)),
        "planned_task_condition_pairs": len(pairs),
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": len(pairs) if status == "blocked" else 0,
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
        "checks": {
            "iter45_manifest_present": SOURCE_MANIFEST.exists(),
            "iter45_manifest_status": manifest.get("status"),
            "provider_overlay_path_count": len(provider_overlays),
            "pair_command_count": len(pair_command_templates),
            "pair_commands_bind_provider_overlay": all(
                "telos_vertex" in template for template in pair_command_templates
            ),
            "harness_full_protocol_effect_execution_enabled": plan.get(
                "full_protocol_effect_execution_enabled"
            ),
            "harness_requires_future_task_condition_gate": plan.get(
                "requires_future_gate_to_execute_task_condition_pairs"
            ),
        },
        "blockers": blockers,
        "failures": failures,
    }
    return preflight, blockers, failures


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    manifest = read_json(SOURCE_MANIFEST)
    preflight, blockers, failures = build_preflight()
    status = preflight["status"]
    planned_pairs = preflight["planned_task_condition_pairs"]

    write_json(PROOF / "preflight.json", preflight)
    execution_report = {
        "schema_version": (
            "telos.public_task_protocol_effect_execution_with_assembled_executor.report.v1"
        ),
        "status": status,
        "experiment_id": "iter46_public_task_protocol_effect_execution_with_assembled_executor",
        "planned_task_condition_pairs": planned_pairs,
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": planned_pairs if status == "blocked" else 0,
        "condition_rows": condition_rows(manifest, status),
        "metrics": metric_rows(status),
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "blockers": blockers,
        "failures": failures,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
    }
    write_json(PROOF / "execution_report.json", execution_report)

    output_lines = [
        f"public task protocol-effect execution with assembled executor: {status}",
        "planned_task_condition_pairs=6",
        "attempted_task_condition_pairs=0",
        "provider_model_api_calls=0",
        "provider_spend_usd=0.0",
        "cloud_runner_started=false",
        "gpu_used=false",
        "sentinel_named_resources_modified=false",
        f"blockers={','.join(blockers)}",
        f"failures={','.join(failures)}",
        f"next_gate={NEXT_GATE.relative_to(ROOT)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 46 Review

The execution-with-assembled-executor gate blocked before provider execution. The `iter45` manifest
correctly enumerates six frozen task-condition pairs, but its pair command templates still point to
public configs and do not bind the provider overlay into each pair command. The recovered `iter43`
harness also still marks full protocol-effect execution as disabled and requires a future
task-condition gate.

Starting a provider run from this state would not prove the pre-registered provider-backed
six-pair protocol-effect claim. The gate therefore stopped with zero attempted pairs, zero provider
model calls, zero spend, no cloud runner, no GPU, and no Sentinel-named resource modification.
No provider model calls occurred.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    result = f"""# Iteration 46 Result - Public Task Protocol-Effect Execution With Assembled Executor

Status: `{status.upper()}`.

## Summary

The gate blocked before provider execution. The assembled executor manifest exists and contains six
frozen task-condition pairs, but the provider-backed command binding is not concrete enough to run
without changing the meaning of the gate.

- planned task-condition pairs: `6`,
- attempted task-condition pairs: `0`,
- provider model API calls: `0`,
- provider spend: `$0.00`,
- cloud runner started: `false`,
- GPU used: `false`,
- Sentinel-named resources modified: `false`.

## Blockers

{chr(10).join(f"- `{blocker}`" for blocker in blockers)}

## What Is Now Authorized

- Pre-register a command-binding recovery gate that binds provider overlays and exact pair
  commands before any paid execution.
- Keep provider calls, spend, cloud runner startup, and GPU use at zero until the six-pair provider
  command surface is concrete and audited.

## What Remains Forbidden

- No benchmark result is claimed.
- No SWE-bench score is claimed.
- No leaderboard result is claimed.
- No production or live-domain result is claimed.
- No model-superiority or state-of-the-art result is claimed.
- No provider-backed completion metric is inferred from the blocked preflight.

## Evidence

- `proof/preflight.json`
- `proof/execution_report.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_public_task_protocol_effect_execution_with_assembled_executor.json`
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
            "telos.public_task_protocol_effect_execution_with_assembled_executor.summary.v1"
        ),
        "status": status,
        "experiment_id": "iter46_public_task_protocol_effect_execution_with_assembled_executor",
        "source_manifest_path": str(SOURCE_MANIFEST.relative_to(ROOT)),
        "source_manifest_sha256": sha256_file(SOURCE_MANIFEST),
        "source_iter43_report_path": str(SOURCE_ITER43_REPORT.relative_to(ROOT)),
        "source_iter43_report_sha256": sha256_file(SOURCE_ITER43_REPORT),
        "planned_task_condition_pairs": planned_pairs,
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": planned_pairs if status == "blocked" else 0,
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
        "experiment_id": "iter46_public_task_protocol_effect_execution_with_assembled_executor",
        "status": "blocked" if status == "blocked" else status,
        "insight": (
            "The dry-run executor manifest is not yet a provider-backed executor; provider overlays "
            "must be bound into exact task-condition commands before paid execution can start."
        ),
        "next_action": (
            "recover provider task-condition command binding without spend, then retry the six-pair "
            "execution only if the command surface is concrete and audited"
        ),
        "result_path": (
            "experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor/RESULT.md"
        ),
        "evidence_paths": [
            "experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor/proof/run_summary.json",
            "experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor/proof/preflight.json",
            "experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor/proof/execution_report.json",
            "experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor/proof/command_output.txt",
            "experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor/proof/review.md",
            "experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor/proof/valid/receipt_public_task_protocol_effect_execution_with_assembled_executor.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(
        VALID / "receipt_public_task_protocol_effect_execution_with_assembled_executor.json",
        build_receipt(status),
    )

    print("\n".join(output_lines))
    return 0 if status in {"blocked", "pass"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
