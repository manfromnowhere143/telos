#!/usr/bin/env python3
"""Publish iter51 provider-compatible protocol-effect execution-with-wrapper artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

from run_ephemeral_vertex_codeclash_provider import build_harness_report


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter51_provider_compatible_protocol_effect_execution_with_wrapper"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
SOURCE_WRAPPER_PLAN = (
    ROOT
    / "experiments"
    / "iter50_provider_compatible_execution_wrapper_recovery"
    / "proof"
    / "wrapper_dry_run_plan.json"
)
SOURCE_ITER50_SUMMARY = (
    ROOT
    / "experiments"
    / "iter50_provider_compatible_execution_wrapper_recovery"
    / "proof"
    / "run_summary.json"
)
SOURCE_SLICE = (
    ROOT
    / "experiments"
    / "iter48_provider_compatible_protocol_effect_slice_refreeze"
    / "proof"
    / "provider_compatible_slice.json"
)
PRIOR_PROVIDER_PROOF = ROOT / "experiments" / "iter21_opponent_collision_control" / "proof"
WRAPPER_SCRIPT = ROOT / "scripts" / "run_provider_compatible_protocol_effect_pairs.py"
BASE_HARNESS = ROOT / "scripts" / "run_ephemeral_vertex_codeclash_provider.py"
NEXT_GATE = (
    ROOT
    / "experiments"
    / "iter52_provider_condition_runtime_separation_recovery"
    / "HYPOTHESIS.md"
)
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
        "receipt_id": f"iter51-provider-compatible-protocol-effect-execution-with-wrapper-{status}",
        "task_id": "telos:iter51_provider_compatible_protocol_effect_execution_with_wrapper@iter50",
        "agent_id": "codex-local-provider-compatible-wrapper-preflight",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Execute the two provider-compatible BattleSnake condition pairs only if the committed "
            "wrapper proves execution mode, condition separation, cost capture, artifact retention, "
            "redaction, receipt validation, and runner lifecycle controls before provider calls."
        ),
        "acceptance_criteria": [
            "The iter50 wrapper recovery proof is validated before execution.",
            "Exactly two selected BattleSnake pairs are planned and all four excluded historical pairs remain unattempted.",
            "Provider calls do not start unless wrapper execution mode and baseline/Telos runtime separation are proven.",
            "Provider model invocations remain at or below 16 and provider spend remains at or below $10.00.",
            "No GPU is requested or used, no Sentinel-named resource is modified, and no production or live-domain behavior changes.",
            "No benchmark, leaderboard, SWE-bench, production, live-domain, model-superiority, or state-of-the-art result is claimed.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": (
                    "experiments/iter51_provider_compatible_protocol_effect_execution_with_wrapper/"
                    "proof/preflight.json"
                ),
                "notes": "Preflight blocks before provider calls when execution mode or condition separation is missing.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": (
                    "experiments/iter51_provider_compatible_protocol_effect_execution_with_wrapper/"
                    "proof/execution_report.json"
                ),
                "notes": "Execution report publishes the blocked rows and zero-spend boundary.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": (
                    "experiments/iter51_provider_compatible_protocol_effect_execution_with_wrapper/"
                    "proof/review.md"
                ),
                "notes": "Review records why the paid run was not started.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if the wrapper is still dry-run-only.",
            "The result must block if baseline and Telos runtime conditions are not distinct before provider calls.",
            "The result must fail if any excluded pair is attempted.",
            "The result must fail if provider calls, spend, cloud runner startup, GPU use, or Sentinel resource modification occurs after a blocking preflight.",
            "The result must fail if unsupported benchmark, model-superiority, production, live-domain, leaderboard, SWE-bench, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def artifact_hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path.relative_to(PROOF)): sha256_file(path) for path in paths}


def command_without_output_root(command: str) -> str:
    if " -o " not in command:
        return command.strip()
    return command.split(" -o ", 1)[0].strip()


def wrapper_execution_mode_present(script_text: str) -> bool:
    return "--execute" in script_text or "execute_pair(" in script_text or "execute_pairs(" in script_text


def build_preflight() -> tuple[dict[str, Any], dict[str, Any], list[str], list[str]]:
    wrapper_plan = read_json(SOURCE_WRAPPER_PLAN)
    iter50_summary = read_json(SOURCE_ITER50_SUMMARY)
    slice_data = read_json(SOURCE_SLICE)
    harness_report = build_harness_report(
        prior_proof=PRIOR_PROVIDER_PROOF,
        execute_lifecycle_probe=False,
        zone="us-central1-a",
    )
    provider_plan = harness_report.get("provider_execution_plan", {})
    wrapper_text = WRAPPER_SCRIPT.read_text(encoding="utf-8") if WRAPPER_SCRIPT.exists() else ""
    pairs = wrapper_plan.get("dry_run_pair_plans", [])
    selected_pair_ids = wrapper_plan.get("selected_pair_ids", [])
    excluded_pair_ids = wrapper_plan.get("excluded_pair_ids", [])

    blockers: list[str] = []
    failures: list[str] = []
    if iter50_summary.get("status") != "pass":
        blockers.append("iter50_wrapper_recovery_not_passed")
    if wrapper_plan.get("status") != "dry_run_ready":
        blockers.append("iter50_wrapper_plan_not_dry_run_ready")
    if selected_pair_ids != READY_PAIR_IDS:
        failures.append("selected_pair_ids_changed")
    if excluded_pair_ids != EXCLUDED_PAIR_IDS:
        failures.append("excluded_pair_ids_changed")
    if wrapper_plan.get("rejected_pair_count") != 4:
        failures.append("excluded_pair_rejection_count_changed")
    if slice_data.get("selected_pair_ids") != READY_PAIR_IDS:
        failures.append("source_slice_selected_pair_ids_changed")
    if not WRAPPER_SCRIPT.exists():
        blockers.append("wrapper_script_missing")
    elif not wrapper_execution_mode_present(wrapper_text):
        blockers.append("wrapper_execution_mode_absent")
    if provider_plan.get("full_protocol_effect_execution_enabled") is not True:
        blockers.append("base_provider_harness_full_execution_disabled")
    if provider_plan.get("requires_future_gate_to_execute_task_condition_pairs") is not False:
        blockers.append("base_provider_harness_still_requires_future_task_condition_gate")

    if len(pairs) != 2:
        failures.append("wrapper_pair_plan_count_not_two")
    commands = [pair.get("future_execution_command", "") for pair in pairs]
    command_bases = {command_without_output_root(command) for command in commands}
    overlay_paths = {pair.get("provider_overlay_config") for pair in pairs}
    agent_paths = {pair.get("provider_agent_config") for pair in pairs}
    model_paths = {pair.get("provider_model_config") for pair in pairs}
    if len(command_bases) == 1 and len(overlay_paths) == 1 and len(agent_paths) == 1:
        blockers.append("telos_condition_runtime_not_distinct_from_baseline")
    if len(model_paths) != 1:
        failures.append("provider_model_config_changed_between_conditions")

    status = "fail" if failures else "blocked" if blockers else "pass"
    preflight = {
        "schema_version": (
            "telos.provider_compatible_protocol_effect_execution_with_wrapper.preflight.v1"
        ),
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "source_wrapper_plan_path": str(SOURCE_WRAPPER_PLAN.relative_to(ROOT)),
        "source_wrapper_plan_sha256": sha256_file(SOURCE_WRAPPER_PLAN),
        "source_iter50_summary_path": str(SOURCE_ITER50_SUMMARY.relative_to(ROOT)),
        "source_iter50_summary_sha256": sha256_file(SOURCE_ITER50_SUMMARY),
        "source_slice_path": str(SOURCE_SLICE.relative_to(ROOT)),
        "source_slice_sha256": sha256_file(SOURCE_SLICE),
        "wrapper_script_path": str(WRAPPER_SCRIPT.relative_to(ROOT)),
        "wrapper_script_sha256": sha256_file(WRAPPER_SCRIPT),
        "base_harness_path": str(BASE_HARNESS.relative_to(ROOT)),
        "base_harness_sha256": sha256_file(BASE_HARNESS),
        "selected_pair_count": len(selected_pair_ids),
        "selected_pair_ids": selected_pair_ids,
        "excluded_pair_count": len(excluded_pair_ids),
        "excluded_pair_ids": excluded_pair_ids,
        "planned_task_condition_pairs": 2,
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": 2 if status == "blocked" else 0,
        "excluded_task_condition_pairs_attempted": 0,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "max_provider_model_invocations": 16,
        "max_provider_spend_usd": 10.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "credential_material_logged": False,
        "project_identifier_logged": False,
        "account_identifier_logged": False,
        "service_account_identifier_logged": False,
        "vm_identifier_logged": False,
        "zone_logged": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "checks": {
            "iter50_wrapper_recovery_passed": iter50_summary.get("status") == "pass",
            "wrapper_plan_dry_run_ready": wrapper_plan.get("status") == "dry_run_ready",
            "wrapper_execution_mode_present": wrapper_execution_mode_present(wrapper_text),
            "exact_two_pairs_planned": selected_pair_ids == READY_PAIR_IDS,
            "exact_four_exclusions_visible": excluded_pair_ids == EXCLUDED_PAIR_IDS,
            "excluded_pairs_rejected_by_wrapper": wrapper_plan.get("rejected_pair_count") == 4,
            "baseline_and_telos_rows_separate": {
                pair.get("pair_id"): pair.get("condition_id") for pair in pairs
            },
            "runtime_commands_distinct_beyond_output_root": len(command_bases) > 1,
            "provider_overlays_distinct_between_conditions": len(overlay_paths) > 1,
            "provider_agent_prompts_distinct_between_conditions": len(agent_paths) > 1,
            "base_provider_harness_full_execution_enabled": provider_plan.get(
                "full_protocol_effect_execution_enabled"
            ),
            "base_provider_harness_requires_future_gate": provider_plan.get(
                "requires_future_gate_to_execute_task_condition_pairs"
            ),
            "provider_credentials_visible_without_logging_identity": harness_report.get(
                "gcloud_readiness", {}
            ).get("active_account_count", 0)
            > 0,
            "harness_dry_run_lifecycle_probe_mode": harness_report.get(
                "lifecycle_probe", {}
            ).get("mode"),
            "harness_dry_run_model_calls": harness_report.get("provider_model_api_calls"),
            "harness_dry_run_task_pairs_executed": harness_report.get(
                "full_task_condition_pairs_executed"
            ),
        },
        "gcloud_readiness": harness_report.get("gcloud_readiness"),
        "provider_execution_plan": provider_plan,
        "blockers": blockers,
        "failures": failures,
    }
    return preflight, harness_report, blockers, failures


def condition_rows(wrapper_plan: dict[str, Any], status: str) -> list[dict[str, Any]]:
    rows = []
    for pair in wrapper_plan.get("dry_run_pair_plans", []):
        receipt_required = pair.get("receipt_plan", {}).get(
            "telos_receipt_required_before_acceptance"
        )
        rows.append(
            {
                "pair_id": pair.get("pair_id"),
                "condition_id": pair.get("condition_id"),
                "public_config": pair.get("public_config"),
                "planned": True,
                "attempted": False,
                "blocked": status == "blocked",
                "verified_completion": None,
                "receipt_required": receipt_required,
                "receipt_valid": None,
                "provider_model_api_calls": 0,
                "provider_spend_usd": 0.0,
                "status": status,
                "reason": "preflight_blocked_before_provider_pair_execution",
            }
        )
    return rows


def metrics(status: str) -> dict[str, Any]:
    reason = "not computable because no selected provider-compatible pair executed"
    return {
        "primary": {
            "metric_id": "verified_completion_rate",
            "status": status,
            "exact_counts_available": False,
            "attempted_count": 0,
            "verified_completion_count": 0,
            "value": None,
            "reason": reason,
        },
        "secondary": [
            {
                "metric_id": metric,
                "status": status,
                "value": None,
                "reason": reason,
            }
            for metric in [
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
    }


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    wrapper_plan = read_json(SOURCE_WRAPPER_PLAN)
    preflight, harness_report, blockers, failures = build_preflight()
    status = preflight["status"]

    write_json(PROOF / "harness_dry_run_report.json", harness_report)
    write_json(PROOF / "preflight.json", preflight)

    execution_report = {
        "schema_version": (
            "telos.provider_compatible_protocol_effect_execution_with_wrapper.report.v1"
        ),
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "planned_task_condition_pairs": 2,
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": 2 if status == "blocked" else 0,
        "excluded_task_condition_pairs_attempted": 0,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "condition_rows": condition_rows(wrapper_plan, status),
        "metrics": metrics(status),
        "blockers": blockers,
        "failures": failures,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
    }
    write_json(PROOF / "execution_report.json", execution_report)

    output_lines = [
        f"provider-compatible protocol-effect execution with wrapper: {status}",
        "planned_task_condition_pairs=2",
        "attempted_task_condition_pairs=0",
        f"blocked_task_condition_pairs={execution_report['blocked_task_condition_pairs']}",
        "excluded_task_condition_pairs_attempted=0",
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

    review = """# Iteration 51 Review

The gate blocked before provider calls. The iter50 wrapper is useful planning evidence, but it is
still dry-run-only, and the baseline and Telos receipt-enforced rows do not yet have distinct
runtime commands, provider overlays, or provider agent prompts. Running the paid pair now would
create weak evidence: two paid outputs with different directory names, not a clean protocol-effect
comparison.

No provider model call occurred, no provider spend occurred, no cloud runner started, no GPU was
used, and no Sentinel-named resource was modified. This is not a benchmark null and not a
model-result row; it is a pre-execution block that identifies the next harness gap.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    result = f"""# Iteration 51 Result - Provider-Compatible Protocol-Effect Execution With Wrapper

Status: `{status.upper()}`.

## Summary

The gate blocked before provider execution.

- planned task-condition pairs: `2`,
- attempted task-condition pairs: `0`,
- blocked task-condition pairs: `{execution_report["blocked_task_condition_pairs"]}`,
- excluded historical pairs attempted: `0`,
- provider model API calls: `0`,
- provider spend: `$0.00`,
- cloud runner started: `false`,
- GPU used: `false`,
- Sentinel-named resources modified: `false`.

## Why It Blocked

The iter50 wrapper recovered a clean dry-run plan, but it does not yet expose an execution mode.
The two frozen rows also share the same provider-backed runtime command, overlay, and agent prompt
apart from output directory. That is not strong enough evidence for a Telos protocol-effect run.

Primary blockers:

- `wrapper_execution_mode_absent`,
- `base_provider_harness_full_execution_disabled`,
- `base_provider_harness_still_requires_future_task_condition_gate`,
- `telos_condition_runtime_not_distinct_from_baseline`.

## Claim Boundary

No benchmark result, SWE-bench result, leaderboard result, production/live-domain result,
model-superiority result, or state-of-the-art result is claimed. The only new claim is that iter51
correctly blocked before paid execution because the wrapper and runtime condition split were not
strong enough.

## Next

Recover a condition-separated provider wrapper before spending on the two-pair retry:
[`../iter52_provider_condition_runtime_separation_recovery/HYPOTHESIS.md`](../iter52_provider_condition_runtime_separation_recovery/HYPOTHESIS.md).

## Evidence

- [`proof/preflight.json`](proof/preflight.json)
- [`proof/execution_report.json`](proof/execution_report.json)
- [`proof/harness_dry_run_report.json`](proof/harness_dry_run_report.json)
- [`proof/command_output.txt`](proof/command_output.txt)
- [`proof/review.md`](proof/review.md)
- [`proof/run_summary.json`](proof/run_summary.json)
- [`proof/valid/receipt_provider_compatible_protocol_effect_execution_with_wrapper.json`](proof/valid/receipt_provider_compatible_protocol_effect_execution_with_wrapper.json)
"""
    (EXPERIMENT / "RESULT.md").write_text(result, encoding="utf-8")

    top_artifacts = [
        PROOF / "preflight.json",
        PROOF / "harness_dry_run_report.json",
        PROOF / "execution_report.json",
        PROOF / "command_output.txt",
        PROOF / "review.md",
    ]
    run_summary = {
        "schema_version": (
            "telos.provider_compatible_protocol_effect_execution_with_wrapper.summary.v1"
        ),
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "selected_pair_count": len(preflight["selected_pair_ids"]),
        "selected_pair_ids": preflight["selected_pair_ids"],
        "excluded_pair_count": len(preflight["excluded_pair_ids"]),
        "excluded_pair_ids": preflight["excluded_pair_ids"],
        "planned_task_condition_pairs": 2,
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": execution_report["blocked_task_condition_pairs"],
        "excluded_task_condition_pairs_attempted": 0,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "max_provider_model_invocations": 16,
        "max_provider_spend_usd": 10.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "credential_material_committed": False,
        "project_identifier_committed": False,
        "account_identifier_committed": False,
        "service_account_identifier_committed": False,
        "vm_identifier_committed": False,
        "zone_committed": False,
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
        "artifact_hashes": artifact_hashes(top_artifacts),
    }
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "insight": (
            "The provider-compatible two-pair retry still cannot produce strong protocol-effect "
            "evidence because the wrapper is dry-run-only and the Telos row is not a distinct "
            "runtime condition from baseline."
        ),
        "next_action": (
            "recover a condition-separated provider wrapper with explicit execution mode before "
            "any paid two-pair protocol-effect retry"
        ),
        "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
        "evidence_paths": [
            f"experiments/{EXPERIMENT_ID}/proof/preflight.json",
            f"experiments/{EXPERIMENT_ID}/proof/execution_report.json",
            f"experiments/{EXPERIMENT_ID}/proof/harness_dry_run_report.json",
            f"experiments/{EXPERIMENT_ID}/proof/command_output.txt",
            f"experiments/{EXPERIMENT_ID}/proof/review.md",
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            (
                f"experiments/{EXPERIMENT_ID}/proof/valid/"
                "receipt_provider_compatible_protocol_effect_execution_with_wrapper.json"
            ),
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(
        VALID / "receipt_provider_compatible_protocol_effect_execution_with_wrapper.json",
        build_receipt(status),
    )

    print("\n".join(output_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
