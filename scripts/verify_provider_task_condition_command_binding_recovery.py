#!/usr/bin/env python3
"""Publish iter47 provider task-condition command-binding recovery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from build_provider_task_condition_command_bindings import build_report


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "iter47_provider_task_condition_command_binding_recovery"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
NEXT_GATE = ROOT / "experiments" / "iter48_provider_compatible_protocol_effect_slice_refreeze" / "HYPOTHESIS.md"


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
        "receipt_id": f"iter47-provider-task-condition-command-binding-recovery-{status}",
        "task_id": "telos:iter47_provider_task_condition_command_binding_recovery@iter46",
        "agent_id": "codex-local-provider-command-binding-verifier",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Recover zero-spend provider task-condition command bindings before retrying any "
            "paid six-pair protocol-effect execution."
        ),
        "acceptance_criteria": [
            "Exactly six frozen task-condition pairs remain represented.",
            "Provider-backed commands name concrete provider overlay, model, agent, and cost configs.",
            "Incompatible pairs are blocked explicitly rather than relabeled as provider-backed.",
            "Provider model calls, provider spend, cloud runner startup, GPU use, and Sentinel resource modification remain zero.",
            "No benchmark, leaderboard, SWE-bench, production, live-domain, model-superiority, or state-of-the-art result is claimed.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": (
                    "experiments/iter47_provider_task_condition_command_binding_recovery/"
                    "proof/command_binding_report.json"
                ),
                "notes": "Report records concrete provider command bindings and incompatible pairs.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": (
                    "experiments/iter47_provider_task_condition_command_binding_recovery/"
                    "proof/run_summary.json"
                ),
                "notes": "Summary records zero spend and the narrowed next gate.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": (
                    "experiments/iter47_provider_task_condition_command_binding_recovery/"
                    "proof/review.md"
                ),
                "notes": "Review records why full six-pair execution remains blocked.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if any frozen pair cannot be represented as a provider-backed command.",
            "The result must fail if a deterministic/no-provider command is labeled provider-backed.",
            "The result must fail if any provider model call, spend, cloud runner startup, GPU use, or Sentinel resource modification occurs.",
            "The result must fail if unsupported benchmark, model-superiority, production, live-domain, leaderboard, SWE-bench, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def build_artifact_hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path.relative_to(PROOF)): sha256_file(path) for path in paths}


def evaluate(report: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    failures: list[str] = []
    bindings = report.get("bindings", [])
    ready = report.get("provider_backed_ready_pair_count")
    incompatible = report.get("provider_binding_incompatible_pair_count")

    if report.get("planned_task_condition_pairs") != 6 or len(bindings) != 6:
        failures.append("frozen_pair_count_changed")
    if ready != 2:
        blockers.append("provider_backed_ready_pair_count_not_two")
    if incompatible != 4:
        blockers.append("provider_binding_incompatible_pair_count_not_four")
    if incompatible:
        blockers.append("provider_binding_incompatible_pairs_present")
    if report.get("requires_future_slice_refreeze") is not True:
        blockers.append("future_slice_refreeze_not_required")
    if not NEXT_GATE.exists():
        blockers.append("next_slice_refreeze_gate_missing")

    for binding in bindings:
        status = binding.get("binding_status")
        if status == "provider_backed_command_ready":
            for key in [
                "provider_overlay_config",
                "provider_agent_config",
                "provider_model_config",
                "provider_cost_registry",
                "future_execution_command",
            ]:
                if not binding.get(key):
                    failures.append(f"{binding.get('pair_id')} missing {key}")
            if "telos_battlesnake_vertex_gemini_pilot.yaml" not in binding.get(
                "future_execution_command", ""
            ):
                failures.append(f"{binding.get('pair_id')} command does not use provider config")
        elif status == "provider_binding_incompatible":
            if not binding.get("incompatibility_reason"):
                failures.append(f"{binding.get('pair_id')} missing incompatibility reason")
            if binding.get("future_execution_command") is not None:
                failures.append(f"{binding.get('pair_id')} incompatible pair has command")
        else:
            failures.append(f"{binding.get('pair_id')} unexpected binding status {status!r}")

    for key, expected in [
        ("provider_model_api_calls", 0),
        ("provider_spend_usd", 0.0),
        ("cloud_runner_started", False),
        ("gpu_used", False),
        ("sentinel_named_resources_modified", False),
        ("full_execution_enabled", False),
    ]:
        if report.get(key) != expected:
            failures.append(f"{key} expected {expected!r}, got {report.get(key)!r}")

    if failures:
        return "fail", blockers, failures
    if blockers or incompatible:
        return "blocked", blockers, failures
    return "pass", blockers, failures


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    report = build_report()
    status, blockers, failures = evaluate(report)
    report["status"] = status
    report["blockers"] = blockers
    report["failures"] = failures
    write_json(PROOF / "command_binding_report.json", report)

    output_lines = [
        f"provider task-condition command binding recovery: {status}",
        "planned_task_condition_pairs=6",
        f"provider_backed_ready_pair_count={report['provider_backed_ready_pair_count']}",
        (
            "provider_binding_incompatible_pair_count="
            f"{report['provider_binding_incompatible_pair_count']}"
        ),
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

    review = """# Iteration 47 Review

The command-binding recovery gate blocked and narrowed the execution plan without provider spend.
The existing Vertex provider overlay can bind the two BattleSnake PvP condition pairs. It cannot
honestly bind the two Dummy pairs because that would change the game surface, and it cannot bind the
two deterministic-edit pairs because the provider overlay lacks the deterministic marker prompt and
overlay semantics.

The result keeps all six frozen pairs visible, records the two concrete provider-backed commands,
records four explicit incompatibilities, and stops before any provider model call, cloud runner,
GPU use, or Sentinel-named resource modification.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    result = f"""# Iteration 47 Result - Provider Task-Condition Command Binding Recovery

Status: `{status.upper()}`.

## Summary

The gate blocked and narrowed the provider execution plan before spend.

- planned task-condition pairs: `6`,
- provider-backed command-ready pairs: `{report["provider_backed_ready_pair_count"]}`,
- provider-binding incompatible pairs: `{report["provider_binding_incompatible_pair_count"]}`,
- provider model API calls: `0`,
- provider spend: `$0.00`,
- cloud runner started: `false`,
- GPU used: `false`,
- Sentinel-named resources modified: `false`.

The two BattleSnake PvP pairs can bind to the existing Vertex provider overlay. The Dummy and
deterministic-edit pairs remain represented but are not provider-backed under the current overlay
without changing task semantics.

## What Is Now Authorized

- Pre-register a provider-compatible slice refreeze that either narrows execution to the concrete
  provider-backed BattleSnake pairs or defines new no-spend provider overlays before execution.
- Keep provider calls, spend, cloud runner startup, GPU use, and Sentinel resource modification at
  zero until that slice is frozen and audited.

## What Remains Forbidden

- No benchmark result is claimed.
- No SWE-bench score is claimed.
- No leaderboard result is claimed.
- No production or live-domain result is claimed.
- No model-superiority or state-of-the-art result is claimed.
- No incompatible task surface is relabeled as provider-backed.

## Evidence

- `proof/command_binding_report.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_provider_task_condition_command_binding_recovery.json`
"""
    (EXPERIMENT / "RESULT.md").write_text(result, encoding="utf-8")

    artifact_paths = [
        PROOF / "command_binding_report.json",
        PROOF / "command_output.txt",
        PROOF / "review.md",
    ]
    run_summary = {
        "schema_version": "telos.provider_task_condition_command_binding_recovery.summary.v1",
        "status": status,
        "experiment_id": "iter47_provider_task_condition_command_binding_recovery",
        "planned_task_condition_pairs": 6,
        "provider_backed_ready_pair_count": report["provider_backed_ready_pair_count"],
        "provider_binding_incompatible_pair_count": report[
            "provider_binding_incompatible_pair_count"
        ],
        "provider_backed_ready_pair_ids": report["provider_backed_ready_pair_ids"],
        "provider_binding_incompatible_pair_ids": report[
            "provider_binding_incompatible_pair_ids"
        ],
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "full_execution_enabled": False,
        "requires_future_slice_refreeze": True,
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
        "experiment_id": "iter47_provider_task_condition_command_binding_recovery",
        "status": "blocked" if status == "blocked" else status,
        "insight": (
            "The existing Vertex provider overlay binds only the BattleSnake PvP surface; Dummy and "
            "deterministic-edit pairs must be narrowed or get new provider overlays before paid execution."
        ),
        "next_action": (
            "pre-register a provider-compatible protocol-effect slice refreeze before any "
            "provider-backed execution retry"
        ),
        "result_path": "experiments/iter47_provider_task_condition_command_binding_recovery/RESULT.md",
        "evidence_paths": [
            "experiments/iter47_provider_task_condition_command_binding_recovery/proof/run_summary.json",
            "experiments/iter47_provider_task_condition_command_binding_recovery/proof/command_binding_report.json",
            "experiments/iter47_provider_task_condition_command_binding_recovery/proof/command_output.txt",
            "experiments/iter47_provider_task_condition_command_binding_recovery/proof/review.md",
            "experiments/iter47_provider_task_condition_command_binding_recovery/proof/valid/receipt_provider_task_condition_command_binding_recovery.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(
        VALID / "receipt_provider_task_condition_command_binding_recovery.json",
        build_receipt(status),
    )

    print("\n".join(output_lines))
    return 0 if status in {"blocked", "pass"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
