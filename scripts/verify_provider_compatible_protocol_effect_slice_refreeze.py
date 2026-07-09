#!/usr/bin/env python3
"""Publish iter48 provider-compatible protocol-effect slice-refreeze artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from build_provider_compatible_protocol_effect_slice_refreeze import (
    EXPECTED_CONDITIONS,
    FUTURE_MODEL_INVOCATION_CEILING,
    FUTURE_SPEND_CEILING_USD,
    SELECTED_PUBLIC_CONFIG,
    build_refreeze,
)


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "iter48_provider_compatible_protocol_effect_slice_refreeze"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
NEXT_GATE = (
    ROOT
    / "experiments"
    / "iter49_provider_compatible_protocol_effect_execution_retry"
    / "HYPOTHESIS.md"
)
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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


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
        "receipt_id": f"iter48-provider-compatible-protocol-effect-slice-refreeze-{status}",
        "task_id": "telos:iter48_provider_compatible_protocol_effect_slice_refreeze@iter47",
        "agent_id": "codex-local-provider-compatible-slice-verifier",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Refreeze the next provider-compatible protocol-effect slice at zero spend before "
            "any provider-backed execution retry."
        ),
        "acceptance_criteria": [
            "All six original pairs remain visible as historical context.",
            "Only provider-backed command-ready pairs are selected.",
            "Every excluded pair has a concrete reason.",
            "Baseline and Telos receipt-enforced conditions remain separated and balanced.",
            "Future commands, provider overlay files, budget, artifact, cost, redaction, receipt, and metric plans are recorded.",
            "Provider calls, provider spend, cloud runner startup, GPU use, and Sentinel resource modification remain zero.",
            "No benchmark, leaderboard, SWE-bench, production, live-domain, model-superiority, or state-of-the-art result is claimed.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": (
                    "experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/"
                    "proof/provider_compatible_slice.json"
                ),
                "notes": "Machine-readable refrozen slice with selected and excluded pairs.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": (
                    "experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/"
                    "proof/run_summary.json"
                ),
                "notes": "Summary records zero spend and the bounded next gate.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": (
                    "experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/"
                    "proof/review.md"
                ),
                "notes": "Review records why four historical pairs remain excluded.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if no provider-compatible condition pair remains.",
            "The result must block if selected pairs are not condition-balanced.",
            "The result must fail if any incompatible pair is silently selected.",
            "The result must fail if provider calls, spend, cloud runner startup, GPU use, or Sentinel resource modification occurs.",
            "The result must fail if unsupported benchmark, model-superiority, production, live-domain, leaderboard, SWE-bench, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def artifact_hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path.relative_to(PROOF)): sha256_file(path) for path in paths}


def evaluate(refreeze: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    failures: list[str] = []

    if refreeze.get("original_pair_count") != 6:
        failures.append("original_pair_count_changed")
    if refreeze.get("selected_pair_count") != 2:
        blockers.append("selected_pair_count_not_two")
    if refreeze.get("excluded_pair_count") != 4:
        blockers.append("excluded_pair_count_not_four")
    if set(refreeze.get("selected_pair_ids", [])) != READY_PAIR_IDS:
        failures.append("selected_pair_ids_changed")
    if set(refreeze.get("excluded_pair_ids", [])) != EXCLUDED_PAIR_IDS:
        failures.append("excluded_pair_ids_changed")
    if refreeze.get("selected_public_configs") != [SELECTED_PUBLIC_CONFIG]:
        failures.append("selected_public_configs_changed")
    if sorted(refreeze.get("selected_condition_ids", [])) != sorted(EXPECTED_CONDITIONS):
        failures.append("selected_condition_ids_changed")
    if refreeze.get("condition_balanced") is not True:
        blockers.append("selected_pairs_not_condition_balanced")
    if not NEXT_GATE.exists():
        blockers.append("next_execution_retry_gate_missing")

    for pair in refreeze.get("selected_pairs", []):
        if pair.get("binding_status") != "provider_backed_command_ready":
            failures.append(f"{pair.get('pair_id')} selected without provider-backed binding")
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
            "metric_destinations",
        ]:
            if not pair.get(key):
                failures.append(f"{pair.get('pair_id')} missing {key}")
        command = pair.get("future_execution_command", "")
        if "telos_battlesnake_vertex_gemini_pilot.yaml" not in command:
            failures.append(f"{pair.get('pair_id')} command missing provider config")

    for pair in refreeze.get("excluded_pairs", []):
        if pair.get("binding_status") != "provider_binding_incompatible":
            failures.append(f"{pair.get('pair_id')} excluded with unexpected binding status")
        if not pair.get("exclusion_reason"):
            failures.append(f"{pair.get('pair_id')} missing exclusion reason")

    budget = refreeze.get("future_execution_budget", {})
    if budget.get("max_provider_model_invocations") != FUTURE_MODEL_INVOCATION_CEILING:
        failures.append("future model invocation ceiling changed")
    if budget.get("max_provider_spend_usd") != FUTURE_SPEND_CEILING_USD:
        failures.append("future spend ceiling changed")
    if budget.get("gpu_allowed") is not False:
        failures.append("future budget must forbid GPU")
    if budget.get("sentinel_named_resources_must_not_change") is not True:
        failures.append("future budget must preserve Sentinel isolation")

    for key, expected in [
        ("iter48_provider_model_api_calls", 0),
        ("iter48_provider_spend_usd", 0.0),
        ("cloud_runner_started", False),
        ("gpu_used", False),
        ("sentinel_named_resources_modified", False),
    ]:
        if refreeze.get(key) != expected:
            failures.append(f"{key} expected {expected!r}, got {refreeze.get(key)!r}")

    claim_boundary = refreeze.get("claim_boundary", {})
    for key in [
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "production_or_live_domain_changed",
    ]:
        if claim_boundary.get(key) is not False:
            failures.append(f"claim boundary {key} must be false")

    if failures:
        return "fail", blockers, failures
    if blockers:
        return "blocked", blockers, failures
    return "pass", blockers, failures


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    refreeze = build_refreeze()
    status, blockers, failures = evaluate(refreeze)
    refreeze["status"] = status
    refreeze["blockers"] = blockers
    refreeze["failures"] = failures
    write_json(PROOF / "provider_compatible_slice.json", refreeze)

    output_lines = [
        f"provider-compatible protocol-effect slice refreeze: {status}",
        f"original_pair_count={refreeze['original_pair_count']}",
        f"selected_pair_count={refreeze['selected_pair_count']}",
        f"excluded_pair_count={refreeze['excluded_pair_count']}",
        f"selected_public_configs={','.join(refreeze['selected_public_configs'])}",
        f"selected_condition_ids={','.join(refreeze['selected_condition_ids'])}",
        f"condition_balanced={str(refreeze['condition_balanced']).lower()}",
        "iter48_provider_model_api_calls=0",
        "iter48_provider_spend_usd=0.0",
        "cloud_runner_started=false",
        "gpu_used=false",
        "sentinel_named_resources_modified=false",
        f"future_max_provider_model_invocations={FUTURE_MODEL_INVOCATION_CEILING}",
        f"future_max_provider_spend_usd={FUTURE_SPEND_CEILING_USD}",
        f"blockers={','.join(blockers)}",
        f"failures={','.join(failures)}",
        f"next_gate={NEXT_GATE.relative_to(ROOT)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 48 Review

The provider-compatible slice refreeze selected only the two BattleSnake PvP condition pairs with
concrete Vertex provider commands. The four Dummy and deterministic-edit pairs remain visible as
historical exclusions with explicit incompatibility reasons from `iter47`.

This gate did not call a provider model, spend money, start a cloud runner, use GPU, or modify
Sentinel-named resources. The next gate is a bounded provider-compatible execution retry, not a
leaderboard, SWE-bench, production, live-domain, model-superiority, or state-of-the-art result.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    result = f"""# Iteration 48 Result - Provider-Compatible Protocol-Effect Slice Refreeze

Status: `{status.upper()}`.

## Summary

The gate refroze the next provider-compatible protocol-effect slice at zero spend.

- original task-condition pairs preserved: `6`,
- selected provider-compatible pairs: `{refreeze["selected_pair_count"]}`,
- excluded historical pairs: `{refreeze["excluded_pair_count"]}`,
- selected task surface: `{SELECTED_PUBLIC_CONFIG}`,
- selected conditions: `{", ".join(EXPECTED_CONDITIONS)}`,
- provider model API calls in this gate: `0`,
- provider spend in this gate: `$0.00`,
- cloud runner started: `false`,
- GPU used: `false`,
- Sentinel-named resources modified: `false`.

The selected slice is the BattleSnake PvP task under both baseline and Telos receipt-enforced
conditions. Dummy and deterministic-edit pairs remain excluded from provider execution until they
get compatible provider overlays or a future gate narrows them differently before data.

## What Is Now Authorized

- Pre-register and run only a bounded provider-compatible execution retry for the two selected
  BattleSnake pairs.
- Keep the next gate within `16` provider model invocations and `$10.00` maximum provider spend.
- Keep GPU forbidden and keep Sentinel-named resources untouched.

## What Remains Forbidden

- No benchmark result is claimed.
- No SWE-bench score is claimed.
- No leaderboard result is claimed.
- No production or live-domain result is claimed.
- No model-superiority or state-of-the-art result is claimed.
- No excluded Dummy or deterministic-edit pair may be silently included in the provider execution.

## Evidence

- `proof/provider_compatible_slice.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_provider_compatible_protocol_effect_slice_refreeze.json`
"""
    (EXPERIMENT / "RESULT.md").write_text(result, encoding="utf-8")

    artifact_paths = [
        PROOF / "provider_compatible_slice.json",
        PROOF / "command_output.txt",
        PROOF / "review.md",
    ]
    run_summary = {
        "schema_version": "telos.provider_compatible_protocol_effect_slice_refreeze.summary.v1",
        "status": status,
        "experiment_id": "iter48_provider_compatible_protocol_effect_slice_refreeze",
        "original_pair_count": refreeze["original_pair_count"],
        "selected_pair_count": refreeze["selected_pair_count"],
        "excluded_pair_count": refreeze["excluded_pair_count"],
        "selected_pair_ids": refreeze["selected_pair_ids"],
        "excluded_pair_ids": refreeze["excluded_pair_ids"],
        "selected_public_configs": refreeze["selected_public_configs"],
        "selected_condition_ids": refreeze["selected_condition_ids"],
        "condition_balanced": refreeze["condition_balanced"],
        "future_max_provider_model_invocations": FUTURE_MODEL_INVOCATION_CEILING,
        "future_max_provider_spend_usd": FUTURE_SPEND_CEILING_USD,
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
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": blockers,
        "failures": failures,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
        "artifact_hashes": {},
    }
    run_summary["artifact_hashes"] = artifact_hashes(artifact_paths)
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter48_provider_compatible_protocol_effect_slice_refreeze",
        "status": status,
        "insight": (
            "The next honest provider-compatible protocol-effect execution slice is the two-pair "
            "BattleSnake PvP baseline/Telos comparison; the other four historical pairs stay "
            "excluded until compatible overlays exist."
        ),
        "next_action": (
            "run the bounded provider-compatible execution retry only for the two selected "
            "BattleSnake pairs under the frozen budget and claim boundary"
        ),
        "result_path": "experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/RESULT.md",
        "evidence_paths": [
            "experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/proof/run_summary.json",
            "experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/proof/provider_compatible_slice.json",
            "experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/proof/command_output.txt",
            "experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/proof/review.md",
            "experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/proof/valid/receipt_provider_compatible_protocol_effect_slice_refreeze.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(
        VALID / "receipt_provider_compatible_protocol_effect_slice_refreeze.json",
        build_receipt(status),
    )

    print("\n".join(output_lines))
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
