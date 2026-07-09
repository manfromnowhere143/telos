#!/usr/bin/env python3
"""Build the iter48 zero-spend provider-compatible slice refreeze."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMMAND_BINDING_REPORT = (
    ROOT
    / "experiments"
    / "iter47_provider_task_condition_command_binding_recovery"
    / "proof"
    / "command_binding_report.json"
)
EXECUTOR_MANIFEST = (
    ROOT
    / "experiments"
    / "iter45_public_task_condition_executor_assembly"
    / "proof"
    / "executor_manifest.json"
)
PROTOCOL_EFFECT_SLICE = (
    ROOT
    / "experiments"
    / "iter39_public_task_protocol_effect_slice"
    / "proof"
    / "protocol_effect_slice.json"
)
NEXT_EXPERIMENT = "iter49_provider_compatible_protocol_effect_execution_retry"
NEXT_GATE = ROOT / "experiments" / NEXT_EXPERIMENT / "HYPOTHESIS.md"
SELECTED_STATUS = "provider_backed_command_ready"
EXCLUDED_STATUS = "provider_binding_incompatible"
SELECTED_PUBLIC_CONFIG = "configs/test/battlesnake_pvp_test.yaml"
EXPECTED_CONDITIONS = [
    "baseline_agent_completion_evidence",
    "telos_receipt_enforced_completion_evidence",
]
FUTURE_SPEND_CEILING_USD = 10.0
FUTURE_MODEL_INVOCATION_CEILING = 16


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} root must be an object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def execution_artifact_plan(pair_id: str) -> dict[str, Any]:
    raw_root = f"experiments/{NEXT_EXPERIMENT}/proof/raw/{pair_id}"
    pair_summary = f"experiments/{NEXT_EXPERIMENT}/proof/pairs/{pair_id}.json"
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


def selected_pair(binding: dict[str, Any]) -> dict[str, Any]:
    pair_id = binding["pair_id"]
    artifact_plan = execution_artifact_plan(pair_id)
    return {
        "pair_id": pair_id,
        "task_id": binding["task_id"],
        "condition_id": binding["condition_id"],
        "public_config": binding["public_config"],
        "binding_status": binding["binding_status"],
        "provider_overlay_config": binding["provider_overlay_config"],
        "provider_agent_config": binding["provider_agent_config"],
        "provider_model_config": binding["provider_model_config"],
        "provider_cost_registry": binding["provider_cost_registry"],
        "future_execution_command": binding["future_execution_command"],
        "overlay_copy_plan": binding["overlay_copy_plan"],
        "artifact_plan": artifact_plan,
        "cost_capture_plan": {
            "required": True,
            "missing_cost_blocks_result": True,
            "primary_source": "metadata.json agents[].agent_stats",
            "secondary_source": "p1 trajectory response/cost fields when present",
        },
        "redaction_plan": {
            "scan_required": True,
            "scan_scope": [artifact_plan["raw_root"], artifact_plan["pair_summary"]],
            "forbidden_residue": [
                "credential material",
                "access tokens",
                "service-account email",
                "project identifier",
                "unredacted provider-specific private fields",
            ],
        },
        "receipt_plan": binding["receipt_expectation"],
        "runner_lifecycle_plan": binding["runner_lifecycle_expectation"],
        "metric_destinations": {
            "primary": (
                "proof/execution_report.json::condition_rows[]"
                f"[condition_id={binding['condition_id']}].verified_completion_rate"
            ),
            "secondary": [
                "proof/execution_report.json::metrics.secondary[proxy_pass_receipt_fail_rate]",
                "proof/execution_report.json::metrics.secondary[unsupported_claim_rate]",
                "proof/execution_report.json::metrics.secondary[over_edit_rate]",
                "proof/execution_report.json::metrics.secondary[evidence_missing_rate]",
                "proof/execution_report.json::metrics.secondary[audit_minutes_per_task]",
                "proof/execution_report.json::metrics.secondary[false_positive_rate]",
                "proof/execution_report.json::metrics.secondary[false_negative_rate]",
                "proof/execution_report.json::metrics.secondary[model_api_calls_per_task]",
                "proof/execution_report.json::metrics.secondary[cost_usd_per_task]",
            ],
        },
    }


def excluded_pair(binding: dict[str, Any]) -> dict[str, Any]:
    return {
        "pair_id": binding["pair_id"],
        "task_id": binding["task_id"],
        "condition_id": binding["condition_id"],
        "public_config": binding["public_config"],
        "binding_status": binding["binding_status"],
        "exclusion_reason": binding["incompatibility_reason"],
    }


def build_refreeze() -> dict[str, Any]:
    command_report = read_json(COMMAND_BINDING_REPORT)
    executor_manifest = read_json(EXECUTOR_MANIFEST)
    protocol_slice = read_json(PROTOCOL_EFFECT_SLICE)
    bindings = command_report["bindings"]
    selected = [selected_pair(binding) for binding in bindings if binding["binding_status"] == SELECTED_STATUS]
    excluded = [excluded_pair(binding) for binding in bindings if binding["binding_status"] == EXCLUDED_STATUS]
    selected_condition_ids = sorted({pair["condition_id"] for pair in selected})
    selected_public_configs = sorted({pair["public_config"] for pair in selected})
    selected_task_ids = sorted({pair["task_id"] for pair in selected})
    all_original_pair_ids = [pair["pair_id"] for pair in bindings]
    condition_balanced = selected_condition_ids == sorted(EXPECTED_CONDITIONS) and all(
        sum(1 for pair in selected if pair["condition_id"] == condition) == 1
        for condition in EXPECTED_CONDITIONS
    )

    return {
        "schema_version": "telos.provider_compatible_protocol_effect_slice_refreeze.v1",
        "status": "pass",
        "source_command_binding_report_path": str(COMMAND_BINDING_REPORT.relative_to(ROOT)),
        "source_executor_manifest_path": str(EXECUTOR_MANIFEST.relative_to(ROOT)),
        "source_protocol_effect_slice_path": str(PROTOCOL_EFFECT_SLICE.relative_to(ROOT)),
        "source_command_binding_status": command_report.get("status"),
        "source_executor_manifest_status": executor_manifest.get("status"),
        "source_protocol_effect_slice_status": protocol_slice.get("status"),
        "original_pair_count": len(bindings),
        "selected_pair_count": len(selected),
        "excluded_pair_count": len(excluded),
        "selected_task_count": len(selected_task_ids),
        "selected_condition_count": len(selected_condition_ids),
        "selected_task_ids": selected_task_ids,
        "selected_public_configs": selected_public_configs,
        "selected_condition_ids": selected_condition_ids,
        "condition_balanced": condition_balanced,
        "all_original_pair_ids": all_original_pair_ids,
        "selected_pair_ids": [pair["pair_id"] for pair in selected],
        "excluded_pair_ids": [pair["pair_id"] for pair in excluded],
        "selected_pairs": selected,
        "excluded_pairs": excluded,
        "historical_pair_bindings": [
            {
                "pair_id": binding["pair_id"],
                "public_config": binding["public_config"],
                "condition_id": binding["condition_id"],
                "binding_status": binding["binding_status"],
            }
            for binding in bindings
        ],
        "future_execution_budget": {
            "provider": "Google Vertex AI",
            "model": "gemini-3.1-pro-preview-customtools",
            "max_provider_model_invocations": FUTURE_MODEL_INVOCATION_CEILING,
            "max_provider_spend_usd": FUTURE_SPEND_CEILING_USD,
            "wall_clock_ceiling_minutes": 45,
            "gpu_allowed": False,
            "runner": "Telos-named ephemeral non-GPU runner only after preflight",
            "sentinel_named_resources_must_not_change": True,
        },
        "artifact_plan": {
            "selected_pair_artifacts": {
                pair["pair_id"]: pair["artifact_plan"] for pair in selected
            },
            "raw_artifacts_must_be_committed_or_counted_as_gaps": True,
            "binary_archives_committed": False,
        },
        "cost_call_stats_plan": {
            "required": True,
            "missing_cost_blocks_result": True,
            "primary_source": "metadata.json agents[].agent_stats",
            "secondary_source": "p1 trajectory response/cost fields when present",
            "report_exact_counts_before_percentages": True,
        },
        "redaction_plan": {
            "scan_required_before_commit": True,
            "forbidden_residue": [
                "credential material",
                "access tokens",
                "service-account email",
                "project identifier",
                "unredacted provider-specific private fields",
            ],
        },
        "receipt_plan": {
            "baseline_receipt_required_before_acceptance": False,
            "telos_receipt_required_before_acceptance": True,
            "missing_telos_receipt_counts_as_evidence_failure": True,
            "posthoc_adversarial_review_required": True,
        },
        "metric_plan": {
            "primary": "verified_completion_rate",
            "secondary": [
                "proxy_pass_receipt_fail_rate",
                "unsupported_claim_rate",
                "over_edit_rate",
                "evidence_missing_rate",
                "audit_minutes_per_task",
                "false_positive_rate",
                "false_negative_rate",
                "model_api_calls_per_task",
                "cost_usd_per_task",
            ],
            "counts_before_percentages": True,
            "baseline_and_telos_rows_separate": True,
        },
        "iter48_provider_model_api_calls": 0,
        "iter48_provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "claim_boundary": {
            "benchmark_result_claimed": False,
            "leaderboard_or_swebench_result_claimed": False,
            "model_superiority_claimed": False,
            "state_of_the_art_result_claimed": False,
            "production_or_live_domain_changed": False,
        },
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_json(args.output, build_refreeze())
    print(f"provider-compatible slice refreeze written: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
