#!/usr/bin/env python3
"""Build the dry-run executor manifest for the public task-condition slice."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SLICE = (
    ROOT
    / "experiments"
    / "iter39_public_task_protocol_effect_slice"
    / "proof"
    / "protocol_effect_slice.json"
)
SOURCE_ITER43_SUMMARY = (
    ROOT
    / "experiments"
    / "iter43_provider_execution_harness_recovery"
    / "proof"
    / "run_summary.json"
)
SOURCE_ITER44_SUMMARY = (
    ROOT
    / "experiments"
    / "iter44_public_task_protocol_effect_execution_after_harness_recovery"
    / "proof"
    / "run_summary.json"
)
PROVIDER_OVERLAY_ROOT = (
    ROOT / "experiments" / "iter09_provider_model_pilot_smoke" / "proof" / "overlay"
)
HARNESS = ROOT / "scripts" / "run_ephemeral_vertex_codeclash_provider.py"
NEXT_EXPERIMENT = "iter46_public_task_protocol_effect_execution_with_assembled_executor"


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} root must be an object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def condition_requirements(condition: dict[str, Any]) -> dict[str, Any]:
    condition_id = condition["condition_id"]
    telos_enforced = condition_id == "telos_receipt_enforced_completion_evidence"
    return {
        "telos_receipt_required_before_acceptance": telos_enforced,
        "posthoc_adversarial_review_required": True,
        "missing_receipt_counts_as_evidence_failure": telos_enforced,
        "raw_completion_evidence_interpretable_without_receipt": not telos_enforced,
        "required_outputs": condition["required_outputs"],
        "failure_rule": condition["failure_rule"],
    }


def pair_record(
    task: dict[str, Any],
    condition: dict[str, Any],
    secondary_metrics: list[dict[str, Any]],
) -> dict[str, Any]:
    task_slug = slug(task["task_id"].replace("codeclash:", ""))
    condition_slug = slug(condition["condition_id"])
    pair_id = f"{condition_slug}__{task_slug}"
    raw_root = (
        f"experiments/{NEXT_EXPERIMENT}/proof/raw/{pair_id}"
    )
    summary_path = f"experiments/{NEXT_EXPERIMENT}/proof/pairs/{pair_id}.json"
    return {
        "pair_id": pair_id,
        "task_id": task["task_id"],
        "task_family": task["task_family"],
        "condition_id": condition["condition_id"],
        "condition_description": condition["description"],
        "source_commit_sha": task["source_commit_sha"],
        "public_config": task["public_config"],
        "overlay_paths": task.get("overlay_paths", []),
        "dry_run_only_in_iter45": True,
        "full_execution_enabled": False,
        "future_execution_command_template": (
            "uv run codeclash run {public_config} -o {pair_output_root}"
        ),
        "future_execution_command_arguments": {
            "public_config": task["public_config"],
            "pair_output_root": f"/tmp/telos-codeclash-protocol-effect/{pair_id}",
        },
        "artifact_plan": {
            "raw_root": raw_root,
            "pair_summary": summary_path,
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
        },
        "cost_capture_plan": {
            "required": True,
            "primary_source": "metadata.json agents[].agent_stats",
            "secondary_source": "p1 trajectory response/cost fields when present",
            "missing_cost_blocks_result": True,
        },
        "redaction_plan": {
            "scan_required": True,
            "scan_scope": [raw_root, summary_path],
            "forbidden_residue": [
                "credential material",
                "access tokens",
                "service-account email",
                "project identifier",
                "unredacted provider-specific private fields",
            ],
        },
        "receipt_plan": condition_requirements(condition),
        "metric_destinations": {
            "primary": (
                "proof/execution_report.json::condition_rows[]"
                f"[condition_id={condition['condition_id']}].verified_completion_rate"
            ),
            "secondary": [
                f"proof/execution_report.json::metrics.secondary[{metric['metric_id']}]"
                for metric in secondary_metrics
            ],
        },
        "lifecycle_plan": {
            "runner": "ephemeral_gce_vm_dedicated_service_account",
            "no_gpu_requested": True,
            "create_runner_before_execution": True,
            "delete_runner_after_execution": True,
            "record_running_telos_vm_count_after": True,
        },
    }


def build_manifest() -> dict[str, Any]:
    slice_data = read_json(SOURCE_SLICE)
    iter43_summary = read_json(SOURCE_ITER43_SUMMARY)
    iter44_summary = read_json(SOURCE_ITER44_SUMMARY)
    secondary_metrics = slice_data["metrics"]["secondary"]
    pairs = [
        pair_record(task, condition, secondary_metrics)
        for condition in slice_data["conditions"]
        for task in slice_data["executable_tasks"]
    ]
    return {
        "schema_version": "telos.public_task_condition_executor_manifest.v1",
        "status": "dry_run_ready",
        "source_slice_path": str(SOURCE_SLICE.relative_to(ROOT)),
        "source_iter43_summary_path": str(SOURCE_ITER43_SUMMARY.relative_to(ROOT)),
        "source_iter44_summary_path": str(SOURCE_ITER44_SUMMARY.relative_to(ROOT)),
        "harness_path": str(HARNESS.relative_to(ROOT)),
        "provider_overlay_paths": [
            str(path.relative_to(ROOT))
            for path in sorted(PROVIDER_OVERLAY_ROOT.rglob("*"))
            if path.is_file()
        ],
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "full_execution_enabled": False,
        "requires_future_gate_for_provider_execution": True,
        "task_count": len(slice_data["executable_tasks"]),
        "condition_count": len(slice_data["conditions"]),
        "planned_task_condition_pairs": len(pairs),
        "pair_ids": [pair["pair_id"] for pair in pairs],
        "pairs": pairs,
        "controls": {
            "iter43_harness_recovery_passed": iter43_summary.get("status") == "pass",
            "iter43_lifecycle_vm_deleted": iter43_summary.get("lifecycle_vm_deleted") is True,
            "iter44_blocked_before_provider_execution": iter44_summary.get("status") == "blocked",
            "exact_pair_count_required": 6,
            "duplicate_pair_ids_allowed": False,
            "provider_execution_forbidden_in_this_gate": True,
            "cloud_runner_start_forbidden_in_this_gate": True,
        },
        "claim_boundary": {
            "benchmark_result_claimed": False,
            "leaderboard_or_swebench_result_claimed": False,
            "model_superiority_claimed": False,
            "state_of_the_art_result_claimed": False,
            "production_or_live_domain_changed": False,
        },
        "next_gate": (
            f"experiments/{NEXT_EXPERIMENT}/HYPOTHESIS.md"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_json(args.output, build_manifest())
    print(f"executor manifest written: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
