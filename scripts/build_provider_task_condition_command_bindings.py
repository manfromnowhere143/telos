#!/usr/bin/env python3
"""Build zero-spend provider command bindings for the iter47 recovery gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_MANIFEST = (
    ROOT
    / "experiments"
    / "iter45_public_task_condition_executor_assembly"
    / "proof"
    / "executor_manifest.json"
)
SOURCE_ITER46_SUMMARY = (
    ROOT
    / "experiments"
    / "iter46_public_task_protocol_effect_execution_with_assembled_executor"
    / "proof"
    / "run_summary.json"
)
PROVIDER_OVERLAY_ROOT = (
    ROOT / "experiments" / "iter09_provider_model_pilot_smoke" / "proof" / "overlay"
)
PROVIDER_CONFIG = (
    "experiments/iter09_provider_model_pilot_smoke/proof/overlay/"
    "configs/test/telos_battlesnake_vertex_gemini_pilot.yaml"
)
PROVIDER_AGENT_CONFIG = (
    "experiments/iter09_provider_model_pilot_smoke/proof/overlay/"
    "configs/mini/telos_vertex_gemini_agent.yaml"
)
PROVIDER_MODEL_CONFIG = (
    "experiments/iter09_provider_model_pilot_smoke/proof/overlay/"
    "configs/mini/telos_vertex_gemini_3_1_pro_customtools.yaml"
)
PROVIDER_COST_REGISTRY = (
    "experiments/iter09_provider_model_pilot_smoke/proof/overlay/"
    "configs/mini/telos_litellm_cost_registry_entry.json"
)
NEXT_EXPERIMENT = "iter48_provider_compatible_protocol_effect_slice_refreeze"


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} root must be an object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def overlay_files() -> list[str]:
    return [
        str(path.relative_to(ROOT))
        for path in sorted(PROVIDER_OVERLAY_ROOT.rglob("*"))
        if path.is_file()
    ]


def binding_for_pair(pair: dict[str, Any]) -> dict[str, Any]:
    pair_id = pair["pair_id"]
    public_config = pair["public_config"]
    raw_root = f"experiments/{NEXT_EXPERIMENT}/proof/raw/{pair_id}"
    pair_summary = f"experiments/{NEXT_EXPERIMENT}/proof/pairs/{pair_id}.json"
    base = {
        "pair_id": pair_id,
        "task_id": pair["task_id"],
        "condition_id": pair["condition_id"],
        "public_config": public_config,
        "source_pair_command_template": pair["future_execution_command_template"],
        "raw_artifact_destination": raw_root,
        "pair_summary_destination": pair_summary,
        "cost_call_stats_source": "metadata.json agents[].agent_stats and p1 trajectory cost fields",
        "redaction_scan_source": [raw_root, pair_summary],
        "receipt_expectation": pair["receipt_plan"],
        "runner_lifecycle_expectation": {
            "runner": "ephemeral_gce_vm_dedicated_service_account",
            "no_gpu_requested": True,
            "create_runner_before_execution": True,
            "delete_runner_after_execution": True,
            "record_running_telos_vm_count_after": True,
            "sentinel_named_resources_must_not_change": True,
        },
        "provider_model_api_calls_in_iter47": 0,
        "provider_spend_usd_in_iter47": 0.0,
        "cloud_runner_started_in_iter47": False,
    }

    if public_config == "configs/test/battlesnake_pvp_test.yaml":
        return {
            **base,
            "binding_status": "provider_backed_command_ready",
            "provider_overlay_config": PROVIDER_CONFIG,
            "provider_agent_config": PROVIDER_AGENT_CONFIG,
            "provider_model_config": PROVIDER_MODEL_CONFIG,
            "provider_cost_registry": PROVIDER_COST_REGISTRY,
            "future_execution_command": (
                "uv run codeclash run configs/test/telos_battlesnake_vertex_gemini_pilot.yaml "
                f"-o /tmp/telos-codeclash-protocol-effect/{pair_id}"
            ),
            "requires_overlay_copy_before_execution": True,
            "overlay_copy_plan": {
                "source_root": str(PROVIDER_OVERLAY_ROOT.relative_to(ROOT)),
                "destination_root": "pinned CodeClash checkout root",
                "required_files": overlay_files(),
            },
            "incompatibility_reason": None,
        }

    if public_config == "configs/test/dummy.yaml":
        reason = (
            "existing provider overlay is a BattleSnake game config; binding it to dummy.yaml "
            "would change the public Dummy task surface"
        )
    elif public_config == "configs/test/telos_battlesnake_edit_test.yaml":
        reason = (
            "existing provider overlay lacks the deterministic edit marker overlay and prompt "
            "semantics required by telos_battlesnake_edit_test.yaml"
        )
    else:
        reason = f"no provider overlay compatibility rule for {public_config}"

    return {
        **base,
        "binding_status": "provider_binding_incompatible",
        "provider_overlay_config": None,
        "provider_agent_config": None,
        "provider_model_config": None,
        "provider_cost_registry": None,
        "future_execution_command": None,
        "requires_overlay_copy_before_execution": False,
        "overlay_copy_plan": None,
        "incompatibility_reason": reason,
    }


def build_report() -> dict[str, Any]:
    manifest = read_json(SOURCE_MANIFEST)
    iter46_summary = read_json(SOURCE_ITER46_SUMMARY)
    bindings = [binding_for_pair(pair) for pair in manifest["pairs"]]
    ready = [binding for binding in bindings if binding["binding_status"] == "provider_backed_command_ready"]
    incompatible = [
        binding for binding in bindings if binding["binding_status"] == "provider_binding_incompatible"
    ]
    return {
        "schema_version": "telos.provider_task_condition_command_binding_report.v1",
        "status": "blocked" if incompatible else "pass",
        "source_manifest_path": str(SOURCE_MANIFEST.relative_to(ROOT)),
        "source_iter46_summary_path": str(SOURCE_ITER46_SUMMARY.relative_to(ROOT)),
        "iter46_status": iter46_summary.get("status"),
        "provider_overlay_root": str(PROVIDER_OVERLAY_ROOT.relative_to(ROOT)),
        "provider_overlay_paths": overlay_files(),
        "planned_task_condition_pairs": len(bindings),
        "provider_backed_ready_pair_count": len(ready),
        "provider_binding_incompatible_pair_count": len(incompatible),
        "provider_backed_ready_pair_ids": [binding["pair_id"] for binding in ready],
        "provider_binding_incompatible_pair_ids": [binding["pair_id"] for binding in incompatible],
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "full_execution_enabled": False,
        "requires_future_slice_refreeze": bool(incompatible),
        "bindings": bindings,
        "claim_boundary": {
            "benchmark_result_claimed": False,
            "leaderboard_or_swebench_result_claimed": False,
            "model_superiority_claimed": False,
            "state_of_the_art_result_claimed": False,
            "production_or_live_domain_changed": False,
        },
        "next_gate": f"experiments/{NEXT_EXPERIMENT}/HYPOTHESIS.md",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_json(args.output, build_report())
    print(f"provider command-binding report written: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
