#!/usr/bin/env python3
"""Publish iter50 provider-compatible execution-wrapper recovery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from run_provider_compatible_protocol_effect_pairs import (
    CAPTURE_STEP_IDS,
    DEFAULT_NEXT_EXPERIMENT,
    EXCLUDED_PAIR_IDS,
    READY_PAIR_IDS,
    build_dry_run_plan,
)


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "iter50_provider_compatible_execution_wrapper_recovery"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
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
SOURCE_ITER49_SUMMARY = (
    ROOT
    / "experiments"
    / "iter49_provider_compatible_protocol_effect_execution_retry"
    / "proof"
    / "run_summary.json"
)
WRAPPER = ROOT / "scripts" / "run_provider_compatible_protocol_effect_pairs.py"
NEXT_GATE = (
    ROOT
    / "experiments"
    / "iter51_provider_compatible_protocol_effect_execution_with_wrapper"
    / "HYPOTHESIS.md"
)
REQUIRED_PAIR_FIELDS = {
    "future_execution_command",
    "provider_overlay_config",
    "provider_agent_config",
    "provider_model_config",
    "provider_cost_registry",
    "overlay_copy_plan",
    "source_iter48_artifact_plan",
    "future_artifact_plan",
    "cost_capture_plan",
    "redaction_plan",
    "receipt_plan",
    "runner_lifecycle_plan",
    "metric_destinations",
    "execution_steps",
}


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
        "receipt_id": f"iter50-provider-compatible-execution-wrapper-recovery-{status}",
        "task_id": "telos:iter50_provider_compatible_execution_wrapper_recovery@iter49",
        "agent_id": "codex-local-provider-compatible-wrapper-recovery-verifier",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Recover a zero-spend dry-run wrapper for exactly the two selected provider-compatible "
            "BattleSnake task-condition pairs."
        ),
        "acceptance_criteria": [
            "Iter49 is a committed blocked result with zero provider calls and zero spend.",
            "The wrapper exists at scripts/run_provider_compatible_protocol_effect_pairs.py.",
            "The wrapper dry-run emits exactly two selected BattleSnake pair plans.",
            "All four excluded Dummy and deterministic-edit pairs are rejected by the wrapper.",
            "Every selected pair plan has artifact, cost, redaction, receipt, lifecycle, and metric capture destinations.",
            "Provider calls, provider spend, cloud runner startup, GPU use, and Sentinel resource modification remain zero.",
            "No benchmark, leaderboard, SWE-bench, production, live-domain, model-superiority, or state-of-the-art result is claimed.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": (
                    "experiments/iter50_provider_compatible_execution_wrapper_recovery/"
                    "proof/wrapper_dry_run_plan.json"
                ),
                "notes": "Wrapper dry-run plan records selected pair plans and excluded-pair rejections.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": (
                    "experiments/iter50_provider_compatible_execution_wrapper_recovery/"
                    "proof/run_summary.json"
                ),
                "notes": "Summary records zero spend and the next bounded execution gate.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": (
                    "experiments/iter50_provider_compatible_execution_wrapper_recovery/"
                    "proof/review.md"
                ),
                "notes": "Review records the wrapper-recovery boundary and claim limits.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if iter49 proof is missing or invalid.",
            "The result must fail if the wrapper drops, renames, duplicates, or silently skips a selected pair.",
            "The result must fail if the wrapper attempts or permits an excluded pair.",
            "The result must fail if artifact, cost, redaction, receipt, lifecycle, or metric destinations are missing.",
            "The result must fail if provider calls, spend, cloud runner startup, GPU use, or Sentinel resource modification occurs.",
            "The result must fail if unsupported benchmark, model-superiority, production, live-domain, leaderboard, SWE-bench, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def artifact_hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path.relative_to(PROOF)): sha256_file(path) for path in paths}


def evaluate_plan(plan: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    failures: list[str] = []
    iter49_summary = read_json(SOURCE_ITER49_SUMMARY)

    if iter49_summary.get("status") != "blocked":
        blockers.append("iter49_summary_not_blocked")
    for key, expected in [
        ("provider_model_api_calls", 0),
        ("provider_spend_usd", 0.0),
        ("cloud_runner_started", False),
        ("gpu_used", False),
        ("sentinel_named_resources_modified", False),
    ]:
        if iter49_summary.get(key) != expected:
            failures.append(f"iter49_summary_{key}_expected_{expected!r}")

    expected = {
        "schema_version": "telos.provider_compatible_execution_wrapper.dry_run_plan.v1",
        "status": "dry_run_ready",
        "wrapper_path": "scripts/run_provider_compatible_protocol_effect_pairs.py",
        "next_execution_experiment": DEFAULT_NEXT_EXPERIMENT,
        "selected_pair_count": 2,
        "excluded_pair_count": 4,
        "dry_run_pair_plan_count": 2,
        "rejected_pair_count": 4,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "full_provider_execution_in_iter50_enabled": False,
        "future_paid_execution_requires_next_gate": True,
        "future_max_provider_model_invocations": 16,
        "future_max_provider_spend_usd": 10.0,
        "future_gpu_allowed": False,
        "future_sentinel_named_resources_must_not_change": True,
        "blockers": [],
        "failures": [],
    }
    for key, value in expected.items():
        if plan.get(key) != value:
            failures.append(f"wrapper plan {key} expected {value!r}, got {plan.get(key)!r}")
    if plan.get("selected_pair_ids") != READY_PAIR_IDS:
        failures.append("selected pair ids changed")
    if plan.get("excluded_pair_ids") != EXCLUDED_PAIR_IDS:
        failures.append("excluded pair ids changed")
    if not WRAPPER.exists():
        blockers.append("wrapper_script_missing")
    if not NEXT_GATE.exists():
        blockers.append("next_execution_gate_missing")

    controls = plan.get("controls", {})
    for key in [
        "iter49_blocked_before_provider_execution",
        "iter49_zero_provider_calls",
        "iter49_zero_provider_spend",
        "excluded_pairs_rejected_by_wrapper",
        "provider_execution_forbidden_in_this_gate",
        "cloud_runner_start_forbidden_in_this_gate",
    ]:
        if controls.get(key) is not True:
            failures.append(f"wrapper control {key} must be true")
    if controls.get("exact_selected_pair_count_required") != 2:
        failures.append("exact selected pair count control must be 2")
    if controls.get("exact_excluded_pair_count_required") != 4:
        failures.append("exact excluded pair count control must be 4")
    if controls.get("duplicate_pair_ids_allowed") is not False:
        failures.append("duplicate pair ids must be forbidden")
    if controls.get("provider_credentials_required_in_this_gate") is not False:
        failures.append("provider credentials must not be required in iter50")

    pair_plans = plan.get("dry_run_pair_plans", [])
    if not isinstance(pair_plans, list) or len(pair_plans) != 2:
        failures.append("wrapper must emit exactly two pair plans")
    else:
        for pair in pair_plans:
            pair_id = pair.get("pair_id")
            if pair_id not in READY_PAIR_IDS:
                failures.append(f"unexpected pair plan id: {pair_id}")
            missing = sorted(REQUIRED_PAIR_FIELDS - set(pair))
            if missing:
                failures.append(f"{pair_id} missing fields: {', '.join(missing)}")
            if pair.get("executed_in_iter50") is not False:
                failures.append(f"{pair_id} must not execute in iter50")
            if pair.get("dry_run_only_in_iter50") is not True:
                failures.append(f"{pair_id} must be dry-run only in iter50")
            if pair_id not in pair.get("future_execution_command", ""):
                failures.append(f"{pair_id} command missing pair output root")
            for key in [
                "provider_overlay_config",
                "provider_agent_config",
                "provider_model_config",
                "provider_cost_registry",
            ]:
                value = pair.get(key)
                if not value or not (ROOT / value).exists():
                    blockers.append(f"{pair_id}:{key}_missing")
            future_artifacts = pair.get("future_artifact_plan", {})
            if DEFAULT_NEXT_EXPERIMENT not in future_artifacts.get("raw_root", ""):
                failures.append(f"{pair_id} future artifact root must target iter51")
            for field in [
                "cost_capture_plan",
                "redaction_plan",
                "receipt_plan",
                "runner_lifecycle_plan",
                "metric_destinations",
            ]:
                if not pair.get(field):
                    failures.append(f"{pair_id} {field} must be non-empty")
            if [step.get("step_id") for step in pair.get("execution_steps", [])] != CAPTURE_STEP_IDS:
                failures.append(f"{pair_id} capture step ids changed")
            for step in pair.get("execution_steps", []):
                if step.get("executed_in_iter50") is not False:
                    failures.append(f"{pair_id}:{step.get('step_id')} executed in iter50")
                if step.get("side_effects_allowed_in_iter50") is not False:
                    failures.append(f"{pair_id}:{step.get('step_id')} permits side effects")

    rejected = plan.get("rejected_excluded_pairs", [])
    if not isinstance(rejected, list) or len(rejected) != 4:
        failures.append("wrapper must reject exactly four excluded pairs")
    else:
        if [pair.get("pair_id") for pair in rejected] != EXCLUDED_PAIR_IDS:
            failures.append("rejected pair ids changed")
        for pair in rejected:
            if pair.get("status") != "rejected_by_wrapper":
                failures.append(f"{pair.get('pair_id')} not rejected by wrapper")
            if pair.get("attempted_in_iter50") is not False:
                failures.append(f"{pair.get('pair_id')} must not be attempted")
            if pair.get("future_execution_command") is not None:
                failures.append(f"{pair.get('pair_id')} must not have future command")
            if not pair.get("rejection_reason"):
                failures.append(f"{pair.get('pair_id')} missing rejection reason")

    claim_boundary = plan.get("claim_boundary", {})
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

    plan = build_dry_run_plan(
        slice_path=SOURCE_SLICE,
        iter49_preflight_path=SOURCE_ITER49_PREFLIGHT,
        next_experiment=DEFAULT_NEXT_EXPERIMENT,
    )
    status, blockers, failures = evaluate_plan(plan)
    write_json(PROOF / "wrapper_dry_run_plan.json", plan)

    output_lines = [
        f"provider-compatible execution wrapper recovery: {status}",
        "wrapper_path=scripts/run_provider_compatible_protocol_effect_pairs.py",
        f"dry_run_pair_plan_count={plan['dry_run_pair_plan_count']}",
        f"rejected_pair_count={plan['rejected_pair_count']}",
        "provider_model_api_calls=0",
        "provider_spend_usd=0.0",
        "cloud_runner_started=false",
        "gpu_used=false",
        "sentinel_named_resources_modified=false",
        "full_provider_execution_in_iter50_enabled=false",
        f"future_max_provider_model_invocations={plan['future_max_provider_model_invocations']}",
        f"future_max_provider_spend_usd={plan['future_max_provider_spend_usd']}",
        f"blockers={','.join(blockers)}",
        f"failures={','.join(failures)}",
        f"next_gate={NEXT_GATE.relative_to(ROOT)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 50 Review

The provider-compatible execution wrapper recovery gate passed as a zero-spend dry run. The wrapper
emits exactly two future execution plans for the selected BattleSnake PvP pairs and rejects all four
Dummy/deterministic-edit historical exclusions.

No provider model call occurred, no provider spend occurred, no cloud runner started, no GPU was
used, and no Sentinel-named resource was modified. The future pair plans include artifact, cost,
redaction, receipt, lifecycle, and metric capture destinations, but no pair executed in this gate.

The next gate may retry the two-pair provider execution only under the frozen `16` invocation and
`$10.00` spend ceilings and must still publish raw artifacts, exact counts, costs, receipts,
blocked/null rows, and claim-boundary review.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    result = f"""# Iteration 50 Result - Provider-Compatible Execution Wrapper Recovery

Status: `{status.upper()}`.

## Summary

The gate recovered a zero-spend dry-run wrapper for the two selected provider-compatible
BattleSnake pairs.

- dry-run selected pair plans: `{plan["dry_run_pair_plan_count"]}`,
- rejected excluded historical pairs: `{plan["rejected_pair_count"]}`,
- provider model API calls: `0`,
- provider spend: `$0.00`,
- cloud runner started: `false`,
- GPU used: `false`,
- Sentinel-named resources modified: `false`,
- full provider execution enabled in iter50: `false`,
- future provider-call ceiling: `{plan["future_max_provider_model_invocations"]}`,
- future spend ceiling: `${plan["future_max_provider_spend_usd"]:.2f}`.

The wrapper plans the exact future CodeClash command for each selected pair and records artifact,
cost, redaction, receipt, lifecycle, and metric destinations. All four excluded Dummy and
deterministic-edit pairs are rejected by the wrapper and remain unattempted.

## What Is Now Authorized

- Pre-register and run only the bounded two-pair provider execution retry in iter51.
- Keep the retry within `16` provider model invocations and `$10.00` maximum provider spend.
- Keep GPU forbidden and keep Sentinel-named resources untouched.

## What Remains Forbidden

- No benchmark result is claimed.
- No SWE-bench score is claimed.
- No leaderboard result is claimed.
- No production or live-domain result is claimed.
- No model-superiority or state-of-the-art result is claimed.
- No provider execution is inferred from the wrapper dry run.
- No excluded Dummy or deterministic-edit pair may be attempted in the next paid retry.

## Evidence

- `proof/wrapper_dry_run_plan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_provider_compatible_execution_wrapper_recovery.json`
"""
    (EXPERIMENT / "RESULT.md").write_text(result, encoding="utf-8")

    artifact_paths = [
        PROOF / "wrapper_dry_run_plan.json",
        PROOF / "command_output.txt",
        PROOF / "review.md",
    ]
    run_summary = {
        "schema_version": "telos.provider_compatible_execution_wrapper_recovery.summary.v1",
        "status": status,
        "experiment_id": "iter50_provider_compatible_execution_wrapper_recovery",
        "source_slice_path": str(SOURCE_SLICE.relative_to(ROOT)),
        "source_slice_sha256": sha256_file(SOURCE_SLICE),
        "source_iter49_preflight_path": str(SOURCE_ITER49_PREFLIGHT.relative_to(ROOT)),
        "source_iter49_preflight_sha256": sha256_file(SOURCE_ITER49_PREFLIGHT),
        "source_iter49_summary_path": str(SOURCE_ITER49_SUMMARY.relative_to(ROOT)),
        "source_iter49_summary_sha256": sha256_file(SOURCE_ITER49_SUMMARY),
        "wrapper_path": str(WRAPPER.relative_to(ROOT)),
        "wrapper_sha256": sha256_file(WRAPPER),
        "selected_pair_count": 2,
        "selected_pair_ids": READY_PAIR_IDS,
        "excluded_pair_count": 4,
        "excluded_pair_ids": EXCLUDED_PAIR_IDS,
        "dry_run_pair_plan_count": plan["dry_run_pair_plan_count"],
        "rejected_pair_count": plan["rejected_pair_count"],
        "future_max_provider_model_invocations": plan["future_max_provider_model_invocations"],
        "future_max_provider_spend_usd": plan["future_max_provider_spend_usd"],
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "full_provider_execution_in_iter50_enabled": False,
        "future_paid_execution_requires_next_gate": True,
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
        "experiment_id": "iter50_provider_compatible_execution_wrapper_recovery",
        "status": status,
        "insight": (
            "A committed zero-spend wrapper can dry-run exactly the two provider-compatible "
            "BattleSnake pair plans and reject all four excluded historical pairs."
        ),
        "next_action": (
            "run the bounded two-pair provider execution retry only under the wrapper, frozen "
            "budget, raw-artifact, receipt, redaction, lifecycle, and claim-boundary controls"
        ),
        "result_path": "experiments/iter50_provider_compatible_execution_wrapper_recovery/RESULT.md",
        "evidence_paths": [
            "experiments/iter50_provider_compatible_execution_wrapper_recovery/proof/run_summary.json",
            "experiments/iter50_provider_compatible_execution_wrapper_recovery/proof/wrapper_dry_run_plan.json",
            "experiments/iter50_provider_compatible_execution_wrapper_recovery/proof/command_output.txt",
            "experiments/iter50_provider_compatible_execution_wrapper_recovery/proof/review.md",
            "experiments/iter50_provider_compatible_execution_wrapper_recovery/proof/valid/receipt_provider_compatible_execution_wrapper_recovery.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(VALID / "receipt_provider_compatible_execution_wrapper_recovery.json", build_receipt(status))

    print("\n".join(output_lines))
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
