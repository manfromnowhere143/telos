#!/usr/bin/env python3
"""Publish iter49 provider-compatible protocol-effect execution-retry artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from run_ephemeral_vertex_codeclash_provider import build_harness_report


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "iter49_provider_compatible_protocol_effect_execution_retry"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
SOURCE_SLICE = (
    ROOT
    / "experiments"
    / "iter48_provider_compatible_protocol_effect_slice_refreeze"
    / "proof"
    / "provider_compatible_slice.json"
)
SOURCE_ITER48_SUMMARY = (
    ROOT
    / "experiments"
    / "iter48_provider_compatible_protocol_effect_slice_refreeze"
    / "proof"
    / "run_summary.json"
)
PRIOR_PROVIDER_PROOF = ROOT / "experiments" / "iter21_opponent_collision_control" / "proof"
BASE_HARNESS = ROOT / "scripts" / "run_ephemeral_vertex_codeclash_provider.py"
EXECUTION_WRAPPER = ROOT / "scripts" / "run_provider_compatible_protocol_effect_pairs.py"
NEXT_GATE = (
    ROOT
    / "experiments"
    / "iter50_provider_compatible_execution_wrapper_recovery"
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


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter49-provider-compatible-protocol-effect-execution-retry-{status}",
        "task_id": "telos:iter49_provider_compatible_protocol_effect_execution_retry@iter48",
        "agent_id": "codex-local-provider-compatible-execution-preflight",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Retry the provider-compatible protocol-effect execution only for the two frozen "
            "BattleSnake pairs if preflight proves an execution wrapper is present and safe."
        ),
        "acceptance_criteria": [
            "The iter48 provider-compatible slice exists, passed, and selects exactly two BattleSnake pairs.",
            "The four excluded Dummy and deterministic-edit pairs remain excluded and visible.",
            "Provider, runner, overlay, cost, artifact, receipt, and redaction preflight evidence is recorded.",
            "Provider calls do not start if the full task-pair execution wrapper is absent.",
            "No provider model call, spend, cloud runner startup, GPU use, Sentinel resource modification, or live-domain change occurs after a blocking preflight.",
            "No benchmark, leaderboard, SWE-bench, production, live-domain, model-superiority, or state-of-the-art result is claimed.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": (
                    "experiments/iter49_provider_compatible_protocol_effect_execution_retry/"
                    "proof/preflight.json"
                ),
                "notes": "Preflight records slice, wrapper, provider-harness, and no-spend checks.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": (
                    "experiments/iter49_provider_compatible_protocol_effect_execution_retry/"
                    "proof/execution_report.json"
                ),
                "notes": "Execution report publishes blocked rows and uncomputed metrics.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": (
                    "experiments/iter49_provider_compatible_protocol_effect_execution_retry/"
                    "proof/review.md"
                ),
                "notes": "Review records why provider calls were not started.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if the iter48 refrozen slice or audit evidence is missing.",
            "The result must block if the two-pair execution wrapper is missing.",
            "The result must block if the existing provider harness still disables full task-condition execution.",
            "The result must fail if an excluded pair is attempted.",
            "The result must fail if any provider model call, spend, cloud runner startup, GPU use, or Sentinel resource modification occurs after a blocking preflight.",
            "The result must fail if unsupported benchmark, model-superiority, production, live-domain, leaderboard, SWE-bench, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def artifact_hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path.relative_to(PROOF)): sha256_file(path) for path in paths}


def condition_rows(slice_data: dict[str, Any], status: str) -> list[dict[str, Any]]:
    rows = []
    selected_pairs = slice_data.get("selected_pairs", [])
    for pair in selected_pairs:
        rows.append(
            {
                "pair_id": pair.get("pair_id"),
                "condition_id": pair.get("condition_id"),
                "public_config": pair.get("public_config"),
                "planned": True,
                "attempted": False,
                "blocked": status == "blocked",
                "verified_completion": None,
                "receipt_valid": None,
                "provider_model_api_calls": 0,
                "provider_spend_usd": 0.0,
                "status": status,
                "reason": "preflight_blocked_before_provider_pair_execution",
            }
        )
    return rows


def metric_rows(status: str) -> dict[str, Any]:
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


def build_preflight() -> tuple[dict[str, Any], dict[str, Any], list[str], list[str]]:
    slice_data = read_json(SOURCE_SLICE)
    iter48_summary = read_json(SOURCE_ITER48_SUMMARY)
    harness_report = build_harness_report(
        prior_proof=PRIOR_PROVIDER_PROOF,
        execute_lifecycle_probe=False,
        zone="us-central1-a",
    )
    plan = harness_report.get("provider_execution_plan", {})
    selected_pair_ids = slice_data.get("selected_pair_ids", [])
    excluded_pair_ids = slice_data.get("excluded_pair_ids", [])

    blockers: list[str] = []
    failures: list[str] = []
    if iter48_summary.get("status") != "pass":
        blockers.append("iter48_refrozen_slice_not_passed")
    if selected_pair_ids != READY_PAIR_IDS:
        failures.append("selected_pair_ids_changed")
    if excluded_pair_ids != EXCLUDED_PAIR_IDS:
        failures.append("excluded_pair_ids_changed")
    if slice_data.get("selected_pair_count") != 2:
        failures.append("selected_pair_count_not_two")
    if slice_data.get("excluded_pair_count") != 4:
        failures.append("excluded_pair_count_not_four")
    if not BASE_HARNESS.exists():
        blockers.append("base_provider_harness_missing")
    if not EXECUTION_WRAPPER.exists():
        blockers.append("provider_compatible_execution_wrapper_missing")
    if plan.get("full_protocol_effect_execution_enabled") is not True:
        blockers.append("existing_provider_harness_full_execution_disabled")
    if plan.get("requires_future_gate_to_execute_task_condition_pairs") is not False:
        blockers.append("existing_provider_harness_requires_future_task_condition_gate")

    for pair in slice_data.get("selected_pairs", []):
        pair_id = pair.get("pair_id")
        command = pair.get("future_execution_command", "")
        if pair.get("binding_status") != "provider_backed_command_ready":
            failures.append(f"{pair_id}:binding_not_provider_ready")
        if pair_id not in command:
            failures.append(f"{pair_id}:command_missing_pair_output_root")
        for key in [
            "provider_overlay_config",
            "provider_agent_config",
            "provider_model_config",
            "provider_cost_registry",
        ]:
            value = pair.get(key)
            if not value or not (ROOT / value).exists():
                blockers.append(f"{pair_id}:{key}_missing")

    status = "fail" if failures else "blocked" if blockers else "pass"
    preflight = {
        "schema_version": (
            "telos.provider_compatible_protocol_effect_execution_retry.preflight.v1"
        ),
        "status": status,
        "experiment_id": "iter49_provider_compatible_protocol_effect_execution_retry",
        "source_slice_path": str(SOURCE_SLICE.relative_to(ROOT)),
        "source_slice_sha256": sha256_file(SOURCE_SLICE),
        "source_iter48_summary_path": str(SOURCE_ITER48_SUMMARY.relative_to(ROOT)),
        "source_iter48_summary_sha256": sha256_file(SOURCE_ITER48_SUMMARY),
        "base_harness_path": str(BASE_HARNESS.relative_to(ROOT)),
        "base_harness_sha256": sha256_file(BASE_HARNESS),
        "required_execution_wrapper_path": str(EXECUTION_WRAPPER.relative_to(ROOT)),
        "required_execution_wrapper_present": EXECUTION_WRAPPER.exists(),
        "selected_pair_count": slice_data.get("selected_pair_count"),
        "selected_pair_ids": selected_pair_ids,
        "excluded_pair_count": slice_data.get("excluded_pair_count"),
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
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "checks": {
            "iter48_refrozen_slice_passed": iter48_summary.get("status") == "pass",
            "selected_pair_commands_present": all(
                bool(pair.get("future_execution_command"))
                for pair in slice_data.get("selected_pairs", [])
            ),
            "selected_pairs_provider_backed": all(
                pair.get("binding_status") == "provider_backed_command_ready"
                for pair in slice_data.get("selected_pairs", [])
            ),
            "excluded_pairs_visible": len(excluded_pair_ids) == 4,
            "base_provider_harness_present": BASE_HARNESS.exists(),
            "base_provider_harness_full_execution_enabled": plan.get(
                "full_protocol_effect_execution_enabled"
            ),
            "base_provider_harness_requires_future_gate": plan.get(
                "requires_future_gate_to_execute_task_condition_pairs"
            ),
            "provider_compatible_execution_wrapper_present": EXECUTION_WRAPPER.exists(),
            "harness_dry_run_lifecycle_probe_mode": harness_report.get(
                "lifecycle_probe", {}
            ).get("mode"),
            "harness_dry_run_model_calls": harness_report.get("provider_model_api_calls"),
            "harness_dry_run_task_pairs_executed": harness_report.get(
                "full_task_condition_pairs_executed"
            ),
            "harness_dry_run_cloud_runner_estimated_spend_bound_usd": harness_report.get(
                "lifecycle_probe", {}
            ).get("cloud_runner_estimated_spend_bound_usd"),
            "prior_provider_cost_capture_parser_validated": harness_report.get(
                "prior_provider_artifact_summary", {}
            ).get("cost_capture_parser_validated"),
            "prior_provider_raw_artifact_retention_validated": harness_report.get(
                "prior_provider_artifact_summary", {}
            ).get("raw_artifact_retention_validated"),
            "prior_provider_redaction_scan_passed": harness_report.get(
                "redaction_scan", {}
            ).get("secret_scan_passed"),
        },
        "gcloud_readiness": harness_report.get("gcloud_readiness"),
        "provider_execution_plan": plan,
        "blockers": blockers,
        "failures": failures,
    }
    return preflight, harness_report, blockers, failures


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    slice_data = read_json(SOURCE_SLICE)
    preflight, harness_report, blockers, failures = build_preflight()
    status = preflight["status"]

    write_json(PROOF / "harness_dry_run_report.json", harness_report)
    write_json(PROOF / "preflight.json", preflight)

    execution_report = {
        "schema_version": (
            "telos.provider_compatible_protocol_effect_execution_retry.report.v1"
        ),
        "status": status,
        "experiment_id": "iter49_provider_compatible_protocol_effect_execution_retry",
        "planned_task_condition_pairs": 2,
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": 2 if status == "blocked" else 0,
        "excluded_task_condition_pairs_attempted": 0,
        "condition_rows": condition_rows(slice_data, status),
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
        f"provider-compatible protocol-effect execution retry: {status}",
        "planned_task_condition_pairs=2",
        "attempted_task_condition_pairs=0",
        f"blocked_task_condition_pairs={2 if status == 'blocked' else 0}",
        "excluded_task_condition_pairs_attempted=0",
        "provider_model_api_calls=0",
        "provider_spend_usd=0.0",
        "cloud_runner_started=false",
        "gpu_used=false",
        "sentinel_named_resources_modified=false",
        f"required_execution_wrapper_present={str(EXECUTION_WRAPPER.exists()).lower()}",
        f"blockers={','.join(blockers)}",
        f"failures={','.join(failures)}",
        f"next_gate={NEXT_GATE.relative_to(ROOT)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 49 Review

The provider-compatible execution retry blocked before provider calls. The `iter48` refrozen slice
remains valid and selects exactly the two BattleSnake PvP pairs, but there is not yet a committed
provider-compatible two-pair execution wrapper. The reusable provider harness also still records
full protocol-effect execution as disabled and says a future gate is required before
task-condition pairs run.

This is an infrastructure block, not a benchmark null and not a model result. No selected pair ran,
no excluded Dummy or deterministic-edit pair ran, no provider model call occurred, no spend
occurred, no cloud runner started, no GPU was used, and no Sentinel-named resource was modified.

The next gate must recover a committed wrapper that can execute exactly the two selected
BattleSnake pairs, preserve raw artifacts, parse provider calls and cost, validate Telos receipts
where required, delete any Telos runner it starts, and keep all unsupported benchmark/model claims
forbidden.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    result = f"""# Iteration 49 Result - Provider-Compatible Protocol-Effect Execution Retry

Status: `{status.upper()}`.

## Summary

The gate blocked before provider execution. The `iter48` slice selects exactly two provider-ready
BattleSnake PvP pairs, but the repository does not yet contain the dedicated execution wrapper
needed to run those two pairs safely. The existing reusable provider harness still disables full
task-condition execution.

- planned provider-compatible task-condition pairs: `2`,
- attempted task-condition pairs: `0`,
- blocked task-condition pairs: `{2 if status == "blocked" else 0}`,
- excluded Dummy/deterministic-edit pairs attempted: `0`,
- provider model API calls: `0`,
- provider spend: `$0.00`,
- cloud runner started: `false`,
- GPU used: `false`,
- Sentinel-named resources modified: `false`,
- benchmark/model result claimed: `false`.

## Blockers

{chr(10).join(f"- `{blocker}`" for blocker in blockers)}

## What Is Now Authorized

- Pre-register and recover a provider-compatible execution wrapper for exactly the two selected
  BattleSnake pairs.
- Keep provider model calls, provider spend, cloud runner startup, and GPU use at zero until the
  wrapper can be audited before paid execution.
- Keep all four excluded historical pairs visible and unattempted.

## What Remains Forbidden

- No benchmark result is claimed.
- No SWE-bench score is claimed.
- No leaderboard result is claimed.
- No production or live-domain result is claimed.
- No model-superiority or state-of-the-art result is claimed.
- No provider execution may start without a committed wrapper that preserves cost, raw artifacts,
  receipts, redaction, and runner lifecycle evidence.

## Evidence

- `proof/preflight.json`
- `proof/harness_dry_run_report.json`
- `proof/execution_report.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_provider_compatible_protocol_effect_execution_retry.json`
"""
    (EXPERIMENT / "RESULT.md").write_text(result, encoding="utf-8")

    artifact_paths = [
        PROOF / "preflight.json",
        PROOF / "harness_dry_run_report.json",
        PROOF / "execution_report.json",
        PROOF / "command_output.txt",
        PROOF / "review.md",
    ]
    run_summary = {
        "schema_version": "telos.provider_compatible_protocol_effect_execution_retry.summary.v1",
        "status": status,
        "experiment_id": "iter49_provider_compatible_protocol_effect_execution_retry",
        "source_slice_path": str(SOURCE_SLICE.relative_to(ROOT)),
        "source_slice_sha256": sha256_file(SOURCE_SLICE),
        "source_iter48_summary_path": str(SOURCE_ITER48_SUMMARY.relative_to(ROOT)),
        "source_iter48_summary_sha256": sha256_file(SOURCE_ITER48_SUMMARY),
        "base_harness_path": str(BASE_HARNESS.relative_to(ROOT)),
        "base_harness_sha256": sha256_file(BASE_HARNESS),
        "required_execution_wrapper_path": str(EXECUTION_WRAPPER.relative_to(ROOT)),
        "required_execution_wrapper_present": EXECUTION_WRAPPER.exists(),
        "selected_pair_count": 2,
        "selected_pair_ids": READY_PAIR_IDS,
        "excluded_pair_count": 4,
        "excluded_pair_ids": EXCLUDED_PAIR_IDS,
        "planned_task_condition_pairs": 2,
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": 2 if status == "blocked" else 0,
        "excluded_task_condition_pairs_attempted": 0,
        "max_provider_model_invocations": 16,
        "max_provider_spend_usd": 10.0,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
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
        "experiment_id": "iter49_provider_compatible_protocol_effect_execution_retry",
        "status": "blocked" if status == "blocked" else status,
        "insight": (
            "The provider-compatible two-pair slice is ready, but paid execution must still block "
            "until a committed wrapper can run exactly those pairs and preserve cost, raw artifact, "
            "receipt, redaction, and lifecycle evidence."
        ),
        "next_action": (
            "recover a zero-spend provider-compatible execution wrapper before retrying the two-pair "
            "provider run"
        ),
        "result_path": (
            "experiments/iter49_provider_compatible_protocol_effect_execution_retry/RESULT.md"
        ),
        "evidence_paths": [
            "experiments/iter49_provider_compatible_protocol_effect_execution_retry/proof/run_summary.json",
            "experiments/iter49_provider_compatible_protocol_effect_execution_retry/proof/preflight.json",
            "experiments/iter49_provider_compatible_protocol_effect_execution_retry/proof/harness_dry_run_report.json",
            "experiments/iter49_provider_compatible_protocol_effect_execution_retry/proof/execution_report.json",
            "experiments/iter49_provider_compatible_protocol_effect_execution_retry/proof/command_output.txt",
            "experiments/iter49_provider_compatible_protocol_effect_execution_retry/proof/review.md",
            "experiments/iter49_provider_compatible_protocol_effect_execution_retry/proof/valid/receipt_provider_compatible_protocol_effect_execution_retry.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(
        VALID / "receipt_provider_compatible_protocol_effect_execution_retry.json",
        build_receipt(status),
    )

    print("\n".join(output_lines))
    return 0 if status in {"blocked", "pass"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
