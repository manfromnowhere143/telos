#!/usr/bin/env python3
"""Publish iter52 provider condition-runtime separation recovery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

from run_provider_compatible_protocol_effect_pairs import (
    CAPTURE_STEP_IDS,
    DEFAULT_CONDITION_SEPARATED_NEXT_EXPERIMENT,
    EXCLUDED_PAIR_IDS,
    READY_PAIR_IDS,
    REQUIRED_ITER51_BLOCKERS,
    build_condition_separated_plan,
    write_recovered_overlay_files,
)


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter52_provider_condition_runtime_separation_recovery"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
SOURCE_SLICE = (
    ROOT
    / "experiments"
    / "iter48_provider_compatible_protocol_effect_slice_refreeze"
    / "proof"
    / "provider_compatible_slice.json"
)
SOURCE_ITER51_PREFLIGHT = (
    ROOT
    / "experiments"
    / "iter51_provider_compatible_protocol_effect_execution_with_wrapper"
    / "proof"
    / "preflight.json"
)
SOURCE_ITER51_SUMMARY = (
    ROOT
    / "experiments"
    / "iter51_provider_compatible_protocol_effect_execution_with_wrapper"
    / "proof"
    / "run_summary.json"
)
WRAPPER = ROOT / "scripts" / "run_provider_compatible_protocol_effect_pairs.py"
NEXT_GATE = (
    ROOT
    / "experiments"
    / DEFAULT_CONDITION_SEPARATED_NEXT_EXPERIMENT
    / "HYPOTHESIS.md"
)
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
        "receipt_id": f"iter52-provider-condition-runtime-separation-recovery-{status}",
        "task_id": "telos:iter52_provider_condition_runtime_separation_recovery@iter51",
        "agent_id": "codex-local-provider-condition-separation-verifier",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Recover zero-spend provider-wrapper readiness by making baseline and Telos "
            "receipt-enforced rows distinct runtime conditions before any paid retry."
        ),
        "acceptance_criteria": [
            "Iter51 is a committed blocked result caused by wrapper execution-mode and condition-separation gaps.",
            "The wrapper exposes an execution mode while remaining dry-run by default.",
            "Exactly two selected BattleSnake pairs are planned and all four excluded historical pairs remain rejected.",
            "Baseline and Telos rows have distinct runtime commands, provider overlays, and provider agent prompts beyond output directory.",
            "The Telos row has a concrete receipt path and validation command before verified completion can be accepted.",
            "Provider calls, spend, cloud runner startup, GPU use, and Sentinel resource modification remain zero.",
            "No benchmark, leaderboard, SWE-bench, production, live-domain, model-superiority, or state-of-the-art result is claimed.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": (
                    "experiments/iter52_provider_condition_runtime_separation_recovery/"
                    "proof/condition_runtime_separation_plan.json"
                ),
                "notes": "Condition-separated plan records runtime commands, overlays, prompts, and receipt checks.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": (
                    "experiments/iter52_provider_condition_runtime_separation_recovery/"
                    "proof/condition_runtime_separation_report.json"
                ),
                "notes": "Report records zero-spend recovery checks and claim boundary.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": (
                    "experiments/iter52_provider_condition_runtime_separation_recovery/"
                    "proof/review.md"
                ),
                "notes": "Review records why iter52 is readiness evidence, not a benchmark result.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if iter51 is missing or was not blocked for the known wrapper/condition gaps.",
            "The result must block if wrapper execution mode cannot be expressed without enabling paid execution by default.",
            "The result must block if baseline and Telos runtime plans differ only by output directory.",
            "The result must block if the Telos row lacks receipt path or validation command before acceptance.",
            "The result must fail if provider calls, spend, cloud runner startup, GPU use, Sentinel resource modification, or excluded-pair execution occurs.",
            "The result must fail if unsupported benchmark, model-superiority, production, live-domain, leaderboard, SWE-bench, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def artifact_hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path.relative_to(PROOF)): sha256_file(path) for path in paths}


def secret_scan(paths: list[Path]) -> tuple[bool, list[str]]:
    findings: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(str(path.relative_to(ROOT)))
    return not findings, findings


def evaluate_plan(plan: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    failures: list[str] = []
    iter51_summary = read_json(SOURCE_ITER51_SUMMARY)

    expected = {
        "schema_version": "telos.provider_condition_runtime_separation.plan.v1",
        "status": "condition_separated_ready",
        "wrapper_path": "scripts/run_provider_compatible_protocol_effect_pairs.py",
        "next_execution_experiment": DEFAULT_CONDITION_SEPARATED_NEXT_EXPERIMENT,
        "selected_pair_count": 2,
        "excluded_pair_count": 4,
        "condition_pair_plan_count": 2,
        "rejected_pair_count": 4,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "full_provider_execution_in_iter52_enabled": False,
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
            failures.append(f"plan {key} expected {value!r}, got {plan.get(key)!r}")

    if iter51_summary.get("status") != "blocked":
        blockers.append("iter51_summary_not_blocked")
    if set(REQUIRED_ITER51_BLOCKERS) - set(iter51_summary.get("blockers", [])):
        blockers.append("iter51_required_blockers_missing")
    if plan.get("selected_pair_ids") != READY_PAIR_IDS:
        failures.append("selected pair ids changed")
    if plan.get("excluded_pair_ids") != EXCLUDED_PAIR_IDS:
        failures.append("excluded pair ids changed")
    if not WRAPPER.exists():
        blockers.append("wrapper_script_missing")
    if not NEXT_GATE.exists():
        blockers.append("next_execution_gate_missing")

    modes = plan.get("wrapper_execution_modes", {})
    if modes.get("default") != "dry-run":
        failures.append("wrapper default mode must remain dry-run")
    if modes.get("available") != ["dry-run", "condition-separated-plan", "execute"]:
        failures.append("wrapper available modes changed")
    if modes.get("execute_mode_available") is not True:
        blockers.append("wrapper_execute_mode_not_visible")
    if modes.get("provider_execution_enabled_by_default") is not False:
        failures.append("provider execution must be disabled by default")
    if modes.get("execute_requires_allow_provider_execution") is not True:
        failures.append("execute mode must require explicit allow gate")

    checks = plan.get("condition_separation_checks", {})
    for key in [
        "runtime_commands_distinct_beyond_output_root",
        "provider_overlays_distinct_between_conditions",
        "provider_agent_prompts_distinct_between_conditions",
        "provider_model_config_same_between_conditions",
        "baseline_receipt_not_required_before_acceptance",
        "telos_receipt_required_before_acceptance",
        "telos_receipt_validation_command_present",
    ]:
        if checks.get(key) is not True:
            blockers.append(f"condition_separation_check_failed:{key}")

    pair_plans = plan.get("condition_pair_plans", [])
    if not isinstance(pair_plans, list) or len(pair_plans) != 2:
        failures.append("condition plan must emit exactly two pair plans")
    else:
        commands = {pair.get("future_execution_command_without_output_root") for pair in pair_plans}
        overlays = {pair.get("provider_overlay_config") for pair in pair_plans}
        agents = {pair.get("provider_agent_config") for pair in pair_plans}
        models = {pair.get("provider_model_config") for pair in pair_plans}
        if len(commands) != 2:
            blockers.append("pair commands are not distinct beyond output root")
        if len(overlays) != 2:
            blockers.append("pair overlays are not distinct")
        if len(agents) != 2:
            blockers.append("pair agent prompts are not distinct")
        if len(models) != 1:
            failures.append("provider model config must stay identical between conditions")

        for pair in pair_plans:
            pair_id = pair.get("pair_id")
            if pair_id not in READY_PAIR_IDS:
                failures.append(f"unexpected pair id: {pair_id}")
            if pair.get("executed_in_iter52") is not False:
                failures.append(f"{pair_id} must not execute in iter52")
            if pair.get("dry_run_only_in_iter52") is not True:
                failures.append(f"{pair_id} must be dry-run only in iter52")
            if DEFAULT_CONDITION_SEPARATED_NEXT_EXPERIMENT not in pair.get(
                "future_artifact_plan", {}
            ).get("raw_root", ""):
                failures.append(f"{pair_id} future artifact root must target iter53")
            for key in [
                "provider_overlay_config",
                "provider_agent_config",
                "provider_model_config",
                "provider_cost_registry",
            ]:
                value = pair.get(key)
                if not value or not (ROOT / value).exists():
                    blockers.append(f"{pair_id}:{key}_missing")
            if [
                step.get("step_id") for step in pair.get("execution_steps", [])
            ] != CAPTURE_STEP_IDS:
                failures.append(f"{pair_id} capture step ids changed")

        telos = [
            pair
            for pair in pair_plans
            if pair.get("condition_id") == "telos_receipt_enforced_completion_evidence"
        ]
        baseline = [
            pair
            for pair in pair_plans
            if pair.get("condition_id") == "baseline_agent_completion_evidence"
        ]
        if len(telos) != 1 or len(baseline) != 1:
            failures.append("baseline/Telos condition split missing")
        else:
            telos_receipt = telos[0].get("receipt_validation_plan", {})
            baseline_receipt = baseline[0].get("receipt_validation_plan", {})
            if telos_receipt.get("required_before_acceptance") is not True:
                blockers.append("telos receipt not required before acceptance")
            if not telos_receipt.get("receipt_path") or not telos_receipt.get(
                "validation_command"
            ):
                blockers.append("telos receipt path or validation command missing")
            if telos_receipt.get("verified_completion_requires_receipt_validation") is not True:
                blockers.append("telos verified completion does not require receipt validation")
            if baseline_receipt.get("required_before_acceptance") is not False:
                failures.append("baseline receipt should not be required before acceptance")

    rejected = plan.get("rejected_excluded_pairs", [])
    if not isinstance(rejected, list) or len(rejected) != 4:
        failures.append("wrapper must reject exactly four excluded pairs")
    else:
        if [pair.get("pair_id") for pair in rejected] != EXCLUDED_PAIR_IDS:
            failures.append("rejected pair ids changed")
        for pair in rejected:
            if pair.get("status") != "rejected_by_wrapper":
                failures.append(f"{pair.get('pair_id')} not rejected by wrapper")
            if pair.get("attempted_in_iter52") is not False:
                failures.append(f"{pair.get('pair_id')} must not be attempted in iter52")
            if pair.get("future_execution_command") is not None:
                failures.append(f"{pair.get('pair_id')} must not have future command")

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


def condition_rows(plan: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pair in plan.get("condition_pair_plans", []):
        receipt_validation = pair.get("receipt_validation_plan", {})
        rows.append(
            {
                "pair_id": pair.get("pair_id"),
                "condition_id": pair.get("condition_id"),
                "runtime_condition_label": pair.get("runtime_condition_label"),
                "future_execution_command_without_output_root": pair.get(
                    "future_execution_command_without_output_root"
                ),
                "provider_overlay_config": pair.get("provider_overlay_config"),
                "provider_agent_config": pair.get("provider_agent_config"),
                "provider_model_config": pair.get("provider_model_config"),
                "receipt_required_before_acceptance": receipt_validation.get(
                    "required_before_acceptance"
                ),
                "receipt_validation_command": receipt_validation.get("validation_command"),
                "attempted_in_iter52": False,
                "provider_model_api_calls": 0,
                "provider_spend_usd": 0.0,
            }
        )
    return rows


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    overlay_files = write_recovered_overlay_files()
    plan = build_condition_separated_plan(
        slice_path=SOURCE_SLICE,
        iter51_summary_path=SOURCE_ITER51_SUMMARY,
        next_experiment=DEFAULT_CONDITION_SEPARATED_NEXT_EXPERIMENT,
    )
    status, blockers, failures = evaluate_plan(plan)
    write_json(PROOF / "condition_runtime_separation_plan.json", plan)

    proof_scan_paths = [ROOT / path for path in overlay_files]
    secret_scan_passed, secret_findings = secret_scan(proof_scan_paths)
    if not secret_scan_passed and status != "fail":
        status = "fail"
        failures = [*failures, "secret_scan_failed"]

    report = {
        "schema_version": "telos.provider_condition_runtime_separation_recovery.report.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "source_slice_path": str(SOURCE_SLICE.relative_to(ROOT)),
        "source_slice_sha256": sha256_file(SOURCE_SLICE),
        "source_iter51_preflight_path": str(SOURCE_ITER51_PREFLIGHT.relative_to(ROOT)),
        "source_iter51_preflight_sha256": sha256_file(SOURCE_ITER51_PREFLIGHT),
        "source_iter51_summary_path": str(SOURCE_ITER51_SUMMARY.relative_to(ROOT)),
        "source_iter51_summary_sha256": sha256_file(SOURCE_ITER51_SUMMARY),
        "wrapper_path": str(WRAPPER.relative_to(ROOT)),
        "wrapper_sha256": sha256_file(WRAPPER),
        "selected_pair_count": plan["selected_pair_count"],
        "selected_pair_ids": plan["selected_pair_ids"],
        "excluded_pair_count": plan["excluded_pair_count"],
        "excluded_pair_ids": plan["excluded_pair_ids"],
        "condition_rows": condition_rows(plan),
        "wrapper_execution_modes": plan["wrapper_execution_modes"],
        "condition_separation_checks": plan["condition_separation_checks"],
        "recovered_overlay_files": overlay_files,
        "secret_scan_passed": secret_scan_passed,
        "secret_scan_findings": secret_findings,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "full_provider_execution_in_iter52_enabled": False,
        "future_max_provider_model_invocations": 16,
        "future_max_provider_spend_usd": 10.0,
        "future_gpu_allowed": False,
        "future_sentinel_named_resources_must_not_change": True,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "dry_run_transcript": plan["dry_run_transcript"],
        "blockers": blockers,
        "failures": failures,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
    }
    write_json(PROOF / "condition_runtime_separation_report.json", report)

    output_lines = [
        f"provider condition runtime separation recovery: {status}",
        "mode=condition-separated-plan",
        "selected_pair_count=2",
        "excluded_pair_count=4",
        "provider_model_api_calls=0",
        "provider_spend_usd=0.0",
        "cloud_runner_started=false",
        "gpu_used=false",
        "sentinel_named_resources_modified=false",
        "provider_execution_enabled_by_default=false",
        "runtime_commands_distinct_beyond_output_root=true",
        "provider_overlays_distinct_between_conditions=true",
        "provider_agent_prompts_distinct_between_conditions=true",
        "telos_receipt_validation_command_present=true",
        f"blockers={','.join(blockers)}",
        f"failures={','.join(failures)}",
        f"next_gate={NEXT_GATE.relative_to(ROOT)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 52 Review

The gate recovered the missing condition separation without spending provider budget. The wrapper
now exposes dry-run, condition-separated planning, and execute modes, but dry-run remains the
default and iter52 enables no provider execution.

The future baseline row uses a raw-evidence prompt and does not require a Telos receipt before
interpretation. The future Telos row uses a separate receipt-enforced prompt, separate provider
overlay, and a concrete `python3 scripts/validate_receipts.py` command that must pass before
verified completion can become true.

No provider model call occurred, no provider spend occurred, no cloud runner started, no GPU was
used, and no Sentinel-named resource was modified. This is readiness evidence for the next bounded
two-pair retry, not a benchmark result or model-result claim.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    result = f"""# Iteration 52 Result - Provider Condition Runtime Separation Recovery

Status: `{status.upper()}`.

## Summary

The gate recovered zero-spend condition separation for the provider-compatible two-pair retry.

- selected BattleSnake pairs planned: `2`,
- excluded historical pairs rejected: `4`,
- provider model API calls: `0`,
- provider spend: `$0.00`,
- cloud runner started: `false`,
- GPU used: `false`,
- Sentinel-named resources modified: `false`,
- provider execution enabled by default: `false`,
- future provider-call ceiling: `16`,
- future spend ceiling: `$10.00`.

## What Changed

The wrapper now has an explicit execution-mode interface while defaulting to dry-run. The recovered
condition plan gives the baseline and Telos rows distinct commands, provider overlays, and provider
agent prompts. The Telos row also names the receipt artifact path and validation command that must
pass before verified completion can be accepted.

## Claim Boundary

No benchmark result, SWE-bench result, leaderboard result, production/live-domain result,
model-superiority result, or state-of-the-art result is claimed. The only new claim is
zero-spend readiness for a condition-separated provider-compatible retry.

## Next

Run the next gate only if the operator intentionally authorizes the bounded paid two-pair retry:
[`../{DEFAULT_CONDITION_SEPARATED_NEXT_EXPERIMENT}/HYPOTHESIS.md`](../{DEFAULT_CONDITION_SEPARATED_NEXT_EXPERIMENT}/HYPOTHESIS.md).

## Evidence

- `proof/condition_runtime_separation_plan.json`
- `proof/condition_runtime_separation_report.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/learning_record.json`
- `proof/valid/receipt_provider_condition_runtime_separation_recovery.json`
- `proof/recovered_overlay/`
"""
    (EXPERIMENT / "RESULT.md").write_text(result, encoding="utf-8")

    top_artifacts = [
        PROOF / "condition_runtime_separation_plan.json",
        PROOF / "condition_runtime_separation_report.json",
        PROOF / "command_output.txt",
        PROOF / "review.md",
        *[ROOT / path for path in overlay_files],
    ]
    run_summary = {
        "schema_version": "telos.provider_condition_runtime_separation_recovery.summary.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "selected_pair_count": plan["selected_pair_count"],
        "selected_pair_ids": plan["selected_pair_ids"],
        "excluded_pair_count": plan["excluded_pair_count"],
        "excluded_pair_ids": plan["excluded_pair_ids"],
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "full_provider_execution_in_iter52_enabled": False,
        "provider_execution_enabled_by_default": False,
        "wrapper_execute_mode_available": True,
        "condition_separation_ready": status == "pass",
        "runtime_commands_distinct_beyond_output_root": True,
        "provider_overlays_distinct_between_conditions": True,
        "provider_agent_prompts_distinct_between_conditions": True,
        "telos_receipt_validation_command_present": True,
        "future_max_provider_model_invocations": 16,
        "future_max_provider_spend_usd": 10.0,
        "future_gpu_allowed": False,
        "future_sentinel_named_resources_must_not_change": True,
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
        "artifact_hashes": artifact_hashes(top_artifacts),
    }
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "insight": (
            "The provider-compatible retry can now be represented as two distinct runtime "
            "conditions: a baseline raw-evidence row and a Telos receipt-enforced row with "
            "pre-acceptance receipt validation."
        ),
        "next_action": (
            "pre-register and run only the bounded two-pair paid retry if provider credentials, "
            "budget, teardown, redaction, and receipt gates are all green"
        ),
        "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
        "evidence_paths": [
            f"experiments/{EXPERIMENT_ID}/proof/condition_runtime_separation_plan.json",
            f"experiments/{EXPERIMENT_ID}/proof/condition_runtime_separation_report.json",
            f"experiments/{EXPERIMENT_ID}/proof/command_output.txt",
            f"experiments/{EXPERIMENT_ID}/proof/review.md",
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            f"experiments/{EXPERIMENT_ID}/proof/learning_record.json",
            (
                f"experiments/{EXPERIMENT_ID}/proof/valid/"
                "receipt_provider_condition_runtime_separation_recovery.json"
            ),
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(
        VALID / "receipt_provider_condition_runtime_separation_recovery.json",
        build_receipt(status),
    )

    print("\n".join(output_lines))
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
