#!/usr/bin/env python3
"""Dry-run wrapper for the provider-compatible two-pair protocol-effect slice."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SLICE = (
    ROOT
    / "experiments"
    / "iter48_provider_compatible_protocol_effect_slice_refreeze"
    / "proof"
    / "provider_compatible_slice.json"
)
SOURCE_ITER49_PREFLIGHT = (
    ROOT
    / "experiments"
    / "iter49_provider_compatible_protocol_effect_execution_retry"
    / "proof"
    / "preflight.json"
)
DEFAULT_NEXT_EXPERIMENT = "iter51_provider_compatible_protocol_effect_execution_with_wrapper"
READY_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
]
EXCLUDED_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-dummy-yaml",
    "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
]
CAPTURE_STEP_IDS = [
    "validate_pair_selection",
    "prepare_telos_non_gpu_runner",
    "copy_provider_overlay",
    "sync_codeclash_environment",
    "run_codeclash_provider_command",
    "copy_raw_artifacts",
    "parse_provider_cost_and_calls",
    "run_redaction_scan",
    "validate_telos_receipt_when_required",
    "teardown_telos_runner",
]


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} root must be an object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def future_artifact_plan(pair: dict[str, Any], next_experiment: str) -> dict[str, Any]:
    pair_id = pair["pair_id"]
    raw_root = f"experiments/{next_experiment}/proof/raw/{pair_id}"
    pair_summary = f"experiments/{next_experiment}/proof/pairs/{pair_id}.json"
    return {
        "raw_root": raw_root,
        "pair_summary": pair_summary,
        "required_text_artifacts": [
            f"{raw_root}/codeclash_run.log",
            f"{raw_root}/metadata.json",
            f"{raw_root}/redaction_scan.json",
        ],
        "optional_text_artifacts": [
            f"{raw_root}/players/p1/p1_r1.traj.json",
            f"{raw_root}/players/p1/changes_r1.json",
            f"{raw_root}/players/p2/changes_r1.json",
        ],
        "binary_archives_committed": False,
    }


def future_redaction_plan(pair: dict[str, Any], next_experiment: str) -> dict[str, Any]:
    artifact_plan = future_artifact_plan(pair, next_experiment)
    return {
        "scan_required": True,
        "scan_scope": [artifact_plan["raw_root"], artifact_plan["pair_summary"]],
        "forbidden_residue": [
            "credential material",
            "access tokens",
            "service-account email",
            "project identifier",
            "unredacted provider-specific private fields",
        ],
    }


def execution_steps(pair: dict[str, Any], next_experiment: str) -> list[dict[str, Any]]:
    artifact_plan = future_artifact_plan(pair, next_experiment)
    return [
        {
            "step_id": "validate_pair_selection",
            "purpose": "confirm the pair id is one of the two iter48-selected BattleSnake pairs",
            "executed_in_iter50": False,
            "dry_run_only_in_iter50": True,
            "side_effects_allowed_in_iter50": False,
        },
        {
            "step_id": "prepare_telos_non_gpu_runner",
            "purpose": "prepare a Telos-named non-GPU runner only in the future execution gate",
            "executed_in_iter50": False,
            "dry_run_only_in_iter50": True,
            "side_effects_allowed_in_iter50": False,
        },
        {
            "step_id": "copy_provider_overlay",
            "purpose": "copy provider overlay files into the pinned CodeClash checkout",
            "required_files": pair.get("overlay_copy_plan", {}).get("required_files", []),
            "executed_in_iter50": False,
            "dry_run_only_in_iter50": True,
            "side_effects_allowed_in_iter50": False,
        },
        {
            "step_id": "sync_codeclash_environment",
            "purpose": "run the pinned CodeClash dependency sync before execution",
            "future_command": "uv sync",
            "executed_in_iter50": False,
            "dry_run_only_in_iter50": True,
            "side_effects_allowed_in_iter50": False,
        },
        {
            "step_id": "run_codeclash_provider_command",
            "purpose": "run the exact provider-backed CodeClash command for this pair",
            "future_command": pair["future_execution_command"],
            "executed_in_iter50": False,
            "dry_run_only_in_iter50": True,
            "side_effects_allowed_in_iter50": False,
        },
        {
            "step_id": "copy_raw_artifacts",
            "purpose": "copy raw logs, metadata, trajectories, and changes into the proof packet",
            "future_destination": artifact_plan["raw_root"],
            "executed_in_iter50": False,
            "dry_run_only_in_iter50": True,
            "side_effects_allowed_in_iter50": False,
        },
        {
            "step_id": "parse_provider_cost_and_calls",
            "purpose": "parse model API call count and provider cost from committed metadata",
            "source": pair.get("cost_capture_plan", {}).get("primary_source"),
            "executed_in_iter50": False,
            "dry_run_only_in_iter50": True,
            "side_effects_allowed_in_iter50": False,
        },
        {
            "step_id": "run_redaction_scan",
            "purpose": "scan committed pair artifacts before publication",
            "scan_scope": future_redaction_plan(pair, next_experiment)["scan_scope"],
            "executed_in_iter50": False,
            "dry_run_only_in_iter50": True,
            "side_effects_allowed_in_iter50": False,
        },
        {
            "step_id": "validate_telos_receipt_when_required",
            "purpose": "validate Telos receipt before accepting Telos-enforced row completion",
            "receipt_required": pair.get("receipt_plan", {}).get(
                "telos_receipt_required_before_acceptance"
            ),
            "executed_in_iter50": False,
            "dry_run_only_in_iter50": True,
            "side_effects_allowed_in_iter50": False,
        },
        {
            "step_id": "teardown_telos_runner",
            "purpose": "delete any Telos runner started by the future execution gate",
            "executed_in_iter50": False,
            "dry_run_only_in_iter50": True,
            "side_effects_allowed_in_iter50": False,
        },
    ]


def pair_plan(pair: dict[str, Any], next_experiment: str) -> dict[str, Any]:
    return {
        "pair_id": pair["pair_id"],
        "task_id": pair["task_id"],
        "public_config": pair["public_config"],
        "condition_id": pair["condition_id"],
        "binding_status": pair["binding_status"],
        "dry_run_only_in_iter50": True,
        "executed_in_iter50": False,
        "future_execution_command": pair["future_execution_command"],
        "provider_overlay_config": pair["provider_overlay_config"],
        "provider_agent_config": pair["provider_agent_config"],
        "provider_model_config": pair["provider_model_config"],
        "provider_cost_registry": pair["provider_cost_registry"],
        "overlay_copy_plan": pair["overlay_copy_plan"],
        "source_iter48_artifact_plan": pair["artifact_plan"],
        "future_artifact_plan": future_artifact_plan(pair, next_experiment),
        "cost_capture_plan": pair["cost_capture_plan"],
        "redaction_plan": future_redaction_plan(pair, next_experiment),
        "receipt_plan": pair["receipt_plan"],
        "runner_lifecycle_plan": pair["runner_lifecycle_plan"],
        "metric_destinations": {
            "primary": (
                f"experiments/{next_experiment}/proof/execution_report.json::"
                f"condition_rows[][pair_id={pair['pair_id']}].verified_completion"
            ),
            "secondary": [
                f"experiments/{next_experiment}/proof/execution_report.json::"
                f"metrics.secondary[{metric_id}]"
                for metric_id in [
                    "proxy_pass_receipt_fail_rate",
                    "unsupported_claim_rate",
                    "over_edit_rate",
                    "evidence_missing_rate",
                    "audit_minutes_per_task",
                    "false_positive_rate",
                    "false_negative_rate",
                    "model_api_calls_per_pair",
                    "cost_usd_per_pair",
                ]
            ],
        },
        "execution_steps": execution_steps(pair, next_experiment),
    }


def rejected_pair(pair: dict[str, Any]) -> dict[str, Any]:
    return {
        "pair_id": pair["pair_id"],
        "task_id": pair["task_id"],
        "public_config": pair["public_config"],
        "condition_id": pair["condition_id"],
        "binding_status": pair["binding_status"],
        "status": "rejected_by_wrapper",
        "attempted_in_iter50": False,
        "future_execution_command": None,
        "rejection_reason": pair["exclusion_reason"],
    }


def build_dry_run_plan(
    slice_path: Path = SOURCE_SLICE,
    iter49_preflight_path: Path = SOURCE_ITER49_PREFLIGHT,
    next_experiment: str = DEFAULT_NEXT_EXPERIMENT,
) -> dict[str, Any]:
    slice_data = read_json(slice_path)
    iter49_preflight = read_json(iter49_preflight_path)
    selected_pairs = slice_data.get("selected_pairs", [])
    excluded_pairs = slice_data.get("excluded_pairs", [])
    selected_pair_ids = [pair.get("pair_id") for pair in selected_pairs]
    excluded_pair_ids = [pair.get("pair_id") for pair in excluded_pairs]
    failures: list[str] = []
    blockers: list[str] = []

    if iter49_preflight.get("status") != "blocked":
        blockers.append("iter49_preflight_not_blocked")
    for key, expected in [
        ("provider_model_api_calls", 0),
        ("provider_spend_usd", 0.0),
        ("cloud_runner_started", False),
        ("gpu_used", False),
        ("sentinel_named_resources_modified", False),
    ]:
        if iter49_preflight.get(key) != expected:
            failures.append(f"iter49_{key}_expected_{expected!r}")

    if selected_pair_ids != READY_PAIR_IDS:
        failures.append("selected_pair_ids_changed")
    if excluded_pair_ids != EXCLUDED_PAIR_IDS:
        failures.append("excluded_pair_ids_changed")
    if len(selected_pair_ids) != len(set(selected_pair_ids)):
        failures.append("selected_pair_ids_not_unique")
    if len(excluded_pair_ids) != len(set(excluded_pair_ids)):
        failures.append("excluded_pair_ids_not_unique")

    pair_plans = [pair_plan(pair, next_experiment) for pair in selected_pairs]
    rejected_pairs = [rejected_pair(pair) for pair in excluded_pairs]

    for plan in pair_plans:
        for key in [
            "provider_overlay_config",
            "provider_agent_config",
            "provider_model_config",
            "provider_cost_registry",
        ]:
            value = plan.get(key)
            if not value or not (ROOT / value).exists():
                blockers.append(f"{plan.get('pair_id')}:{key}_missing")
        if [step.get("step_id") for step in plan.get("execution_steps", [])] != CAPTURE_STEP_IDS:
            failures.append(f"{plan.get('pair_id')}:capture_steps_changed")

    budget = slice_data.get("future_execution_budget", {})
    return {
        "schema_version": "telos.provider_compatible_execution_wrapper.dry_run_plan.v1",
        "status": "dry_run_ready" if not failures and not blockers else "blocked",
        "wrapper_path": "scripts/run_provider_compatible_protocol_effect_pairs.py",
        "source_slice_path": str(slice_path.relative_to(ROOT)),
        "source_iter49_preflight_path": str(iter49_preflight_path.relative_to(ROOT)),
        "next_execution_experiment": next_experiment,
        "selected_pair_count": len(pair_plans),
        "selected_pair_ids": selected_pair_ids,
        "excluded_pair_count": len(rejected_pairs),
        "excluded_pair_ids": excluded_pair_ids,
        "dry_run_pair_plan_count": len(pair_plans),
        "rejected_pair_count": len(rejected_pairs),
        "dry_run_pair_plans": pair_plans,
        "rejected_excluded_pairs": rejected_pairs,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "full_provider_execution_in_iter50_enabled": False,
        "future_paid_execution_requires_next_gate": True,
        "future_max_provider_model_invocations": budget.get("max_provider_model_invocations"),
        "future_max_provider_spend_usd": budget.get("max_provider_spend_usd"),
        "future_gpu_allowed": budget.get("gpu_allowed"),
        "future_sentinel_named_resources_must_not_change": budget.get(
            "sentinel_named_resources_must_not_change"
        ),
        "controls": {
            "iter49_blocked_before_provider_execution": iter49_preflight.get("status")
            == "blocked",
            "iter49_zero_provider_calls": iter49_preflight.get("provider_model_api_calls") == 0,
            "iter49_zero_provider_spend": iter49_preflight.get("provider_spend_usd") == 0.0,
            "exact_selected_pair_count_required": 2,
            "exact_excluded_pair_count_required": 4,
            "duplicate_pair_ids_allowed": False,
            "excluded_pairs_rejected_by_wrapper": len(rejected_pairs) == 4
            and all(pair["status"] == "rejected_by_wrapper" for pair in rejected_pairs),
            "provider_execution_forbidden_in_this_gate": True,
            "cloud_runner_start_forbidden_in_this_gate": True,
            "provider_credentials_required_in_this_gate": False,
        },
        "claim_boundary": {
            "benchmark_result_claimed": False,
            "leaderboard_or_swebench_result_claimed": False,
            "model_superiority_claimed": False,
            "state_of_the_art_result_claimed": False,
            "production_or_live_domain_changed": False,
        },
        "blockers": blockers,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slice", type=Path, default=SOURCE_SLICE)
    parser.add_argument("--iter49-preflight", type=Path, default=SOURCE_ITER49_PREFLIGHT)
    parser.add_argument("--next-experiment", default=DEFAULT_NEXT_EXPERIMENT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    plan = build_dry_run_plan(
        slice_path=args.slice,
        iter49_preflight_path=args.iter49_preflight,
        next_experiment=args.next_experiment,
    )
    write_json(args.output, plan)
    print(
        "provider-compatible wrapper dry run: "
        f"status={plan['status']} "
        f"selected={plan['dry_run_pair_plan_count']} "
        f"rejected={plan['rejected_pair_count']} "
        "model_calls=0 spend=0.0 cloud_runner_started=false"
    )
    return 0 if plan["status"] == "dry_run_ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
