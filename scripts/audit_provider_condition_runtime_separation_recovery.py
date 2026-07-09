#!/usr/bin/env python3
"""Audit iter52 provider condition-runtime separation recovery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter52_provider_condition_runtime_separation_recovery")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
PLAN = PROOF / "condition_runtime_separation_plan.json"
REPORT = PROOF / "condition_runtime_separation_report.json"
SUMMARY = PROOF / "run_summary.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECEIPT = PROOF / "valid" / "receipt_provider_condition_runtime_separation_recovery.json"
NEXT_GATE = Path(
    "experiments/"
    "iter53_provider_compatible_protocol_effect_execution_after_condition_recovery/"
    "HYPOTHESIS.md"
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
REQUIRED_ITER51_BLOCKERS = {
    "wrapper_execution_mode_absent",
    "base_provider_harness_full_execution_disabled",
    "base_provider_harness_still_requires_future_task_condition_gate",
    "telos_condition_runtime_not_distinct_from_baseline",
}
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


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be an object")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_plan(failures: list[str]) -> None:
    plan = load_json(PLAN)
    expected = {
        "schema_version": "telos.provider_condition_runtime_separation.plan.v1",
        "status": "condition_separated_ready",
        "wrapper_path": "scripts/run_provider_compatible_protocol_effect_pairs.py",
        "next_execution_experiment": (
            "iter53_provider_compatible_protocol_effect_execution_after_condition_recovery"
        ),
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
    if plan.get("selected_pair_ids") != READY_PAIR_IDS:
        failures.append("plan selected pair ids changed")
    if plan.get("excluded_pair_ids") != EXCLUDED_PAIR_IDS:
        failures.append("plan excluded pair ids changed")

    modes = plan.get("wrapper_execution_modes", {})
    if modes.get("default") != "dry-run":
        failures.append("wrapper default mode must be dry-run")
    if modes.get("available") != ["dry-run", "condition-separated-plan", "execute"]:
        failures.append("wrapper modes must expose dry-run, condition-separated-plan, execute")
    if modes.get("execute_mode_available") is not True:
        failures.append("wrapper execute mode must be visible")
    if modes.get("provider_execution_enabled_by_default") is not False:
        failures.append("provider execution must be disabled by default")
    if modes.get("execute_requires_allow_provider_execution") is not True:
        failures.append("execute mode must require an explicit allow gate")

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
            failures.append(f"condition separation check must be true: {key}")

    pair_plans = plan.get("condition_pair_plans", [])
    if not isinstance(pair_plans, list) or len(pair_plans) != 2:
        failures.append("plan must include exactly two condition pair plans")
    else:
        commands = {pair.get("future_execution_command_without_output_root") for pair in pair_plans}
        overlays = {pair.get("provider_overlay_config") for pair in pair_plans}
        agents = {pair.get("provider_agent_config") for pair in pair_plans}
        models = {pair.get("provider_model_config") for pair in pair_plans}
        if len(commands) != 2:
            failures.append("condition commands must differ beyond output root")
        if len(overlays) != 2:
            failures.append("provider overlays must differ between conditions")
        if len(agents) != 2:
            failures.append("provider agent prompts must differ between conditions")
        if len(models) != 1:
            failures.append("provider model config must stay identical")

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
            failures.append("missing one baseline and one Telos row")
        else:
            telos_receipt = telos[0].get("receipt_validation_plan", {})
            baseline_receipt = baseline[0].get("receipt_validation_plan", {})
            if telos_receipt.get("required_before_acceptance") is not True:
                failures.append("Telos row must require receipt before acceptance")
            if not telos_receipt.get("receipt_path"):
                failures.append("Telos row missing receipt path")
            validation_command = telos_receipt.get("validation_command")
            if not validation_command or "validate_receipts.py" not in validation_command:
                failures.append("Telos row missing concrete receipt validation command")
            if telos_receipt.get("verified_completion_requires_receipt_validation") is not True:
                failures.append("Telos verified completion must require receipt validation")
            if baseline_receipt.get("required_before_acceptance") is not False:
                failures.append("baseline row must not require receipt before acceptance")

        for pair in pair_plans:
            pair_id = pair.get("pair_id")
            if pair_id not in READY_PAIR_IDS:
                failures.append(f"unexpected pair id: {pair_id}")
            if pair.get("executed_in_iter52") is not False:
                failures.append(f"{pair_id} must not execute in iter52")
            if pair.get("dry_run_only_in_iter52") is not True:
                failures.append(f"{pair_id} must be dry-run only in iter52")
            for key in [
                "provider_overlay_config",
                "provider_agent_config",
                "provider_model_config",
                "provider_cost_registry",
            ]:
                rel_path = pair.get(key)
                if not rel_path or not Path(rel_path).exists():
                    failures.append(f"{pair_id} missing {key}: {rel_path}")

    rejected = plan.get("rejected_excluded_pairs", [])
    if not isinstance(rejected, list) or len(rejected) != 4:
        failures.append("plan must reject four excluded pairs")
    else:
        if [pair.get("pair_id") for pair in rejected] != EXCLUDED_PAIR_IDS:
            failures.append("rejected pair ids changed")
        for pair in rejected:
            if pair.get("status") != "rejected_by_wrapper":
                failures.append(f"{pair.get('pair_id')} must be rejected by wrapper")
            if pair.get("attempted_in_iter52") is not False:
                failures.append(f"{pair.get('pair_id')} must not be attempted in iter52")
            if pair.get("future_execution_command") is not None:
                failures.append(f"{pair.get('pair_id')} must not have a future command")

    claim_boundary = plan.get("claim_boundary", {})
    for key in [
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "production_or_live_domain_changed",
    ]:
        if claim_boundary.get(key) is not False:
            failures.append(f"plan claim boundary {key} must be false")


def audit_report(failures: list[str]) -> None:
    report = load_json(REPORT)
    expected = {
        "schema_version": "telos.provider_condition_runtime_separation_recovery.report.v1",
        "status": "pass",
        "experiment_id": "iter52_provider_condition_runtime_separation_recovery",
        "selected_pair_count": 2,
        "excluded_pair_count": 4,
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
        "blockers": [],
        "failures": [],
        "next_gate": NEXT_GATE.as_posix(),
    }
    for key, value in expected.items():
        if report.get(key) != value:
            failures.append(f"report {key} expected {value!r}, got {report.get(key)!r}")
    if report.get("selected_pair_ids") != READY_PAIR_IDS:
        failures.append("report selected pair ids changed")
    if report.get("excluded_pair_ids") != EXCLUDED_PAIR_IDS:
        failures.append("report excluded pair ids changed")
    if report.get("secret_scan_passed") is not True:
        failures.append("report secret scan must pass")
    rows = report.get("condition_rows", [])
    if len(rows) != 2:
        failures.append("report must include two condition rows")
    if not report.get("recovered_overlay_files"):
        failures.append("report must list recovered overlay files")


def audit_summary(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    expected = {
        "schema_version": "telos.provider_condition_runtime_separation_recovery.summary.v1",
        "status": "pass",
        "experiment_id": "iter52_provider_condition_runtime_separation_recovery",
        "selected_pair_count": 2,
        "excluded_pair_count": 4,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "full_provider_execution_in_iter52_enabled": False,
        "provider_execution_enabled_by_default": False,
        "wrapper_execute_mode_available": True,
        "condition_separation_ready": True,
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
        "clean_pass": True,
        "blocked_result": False,
        "quality_failure": False,
        "blockers": [],
        "failures": [],
        "next_gate": NEXT_GATE.as_posix(),
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {summary.get(key)!r}")
    if summary.get("selected_pair_ids") != READY_PAIR_IDS:
        failures.append("summary selected pair ids changed")
    if summary.get("excluded_pair_ids") != EXCLUDED_PAIR_IDS:
        failures.append("summary excluded pair ids changed")
    hashes = summary.get("artifact_hashes", {})
    if not isinstance(hashes, dict) or not hashes:
        failures.append("summary artifact_hashes must be non-empty")
        return
    for rel_path, expected_hash in hashes.items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"hashed artifact missing: {rel_path}")
            continue
        actual_hash = sha256(path)
        if actual_hash != expected_hash:
            failures.append(f"hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}")


def audit_text_and_receipt(failures: list[str]) -> None:
    output = COMMAND_OUTPUT.read_text(encoding="utf-8")
    for required in [
        "provider condition runtime separation recovery: pass",
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
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`",
        "zero-spend condition separation",
        "No benchmark result",
        "model-superiority result",
        "state-of-the-art result",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in [
        "not a benchmark result",
        "dry-run remains",
        "concrete `python3 scripts/validate_receipts.py` command",
    ]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.status != "pass":
        failures.append("receipt status must be pass")
    expected_id = "iter52-provider-condition-runtime-separation-recovery-pass"
    if receipt.receipt_id != expected_id:
        failures.append("unexpected receipt id")


def audit_overlay_files(failures: list[str]) -> None:
    required_files = [
        PROOF / "recovered_overlay/configs/test/telos_battlesnake_vertex_gemini_baseline.yaml",
        PROOF
        / "recovered_overlay/configs/test/telos_battlesnake_vertex_gemini_receipt_enforced.yaml",
        PROOF / "recovered_overlay/configs/mini/telos_vertex_gemini_baseline_agent.yaml",
        PROOF
        / "recovered_overlay/configs/mini/telos_vertex_gemini_receipt_enforced_agent.yaml",
        PROOF / "recovered_overlay/configs/mini/telos_vertex_gemini_3_1_pro_customtools.yaml",
        PROOF / "recovered_overlay/configs/mini/telos_litellm_cost_registry_entry.json",
    ]
    for path in required_files:
        if not path.exists():
            failures.append(f"missing recovered overlay file: {path}")
    if failures:
        return
    baseline = required_files[0].read_text(encoding="utf-8")
    telos = required_files[1].read_text(encoding="utf-8")
    baseline_agent = required_files[2].read_text(encoding="utf-8")
    telos_agent = required_files[3].read_text(encoding="utf-8")
    if "Do not create a Telos proof receipt" not in baseline:
        failures.append("baseline overlay must explicitly avoid receipt creation")
    if "valid Telos receipt" not in telos:
        failures.append("Telos overlay must require a valid receipt")
    if "This is the baseline condition" not in baseline_agent:
        failures.append("baseline agent prompt missing baseline condition text")
    if "This is the Telos receipt-enforced condition" not in telos_agent:
        failures.append("Telos agent prompt missing receipt-enforced condition text")
    if baseline == telos:
        failures.append("baseline and Telos test overlays must differ")
    if baseline_agent == telos_agent:
        failures.append("baseline and Telos agent prompts must differ")


def audit_secret_residue(failures: list[str]) -> None:
    for path in PROOF.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"possible secret or account/project identifier in {path}")


def audit_next_gate(failures: list[str]) -> None:
    text = NEXT_GATE.read_text(encoding="utf-8")
    for required in [
        "provider model invocations: `<= 16`",
        "provider spend: `<= $10.00`",
        "GPU use: forbidden",
        "Sentinel-named resource mutation: forbidden",
        "All four historical Dummy/deterministic-edit pairs remain rejected",
        "It may not claim a benchmark result",
    ]:
        if required not in text:
            failures.append(f"next gate missing: {required}")


def main() -> int:
    failures: list[str] = []
    for path in [
        RESULT,
        PLAN,
        REPORT,
        SUMMARY,
        COMMAND_OUTPUT,
        REVIEW,
        RECEIPT,
        NEXT_GATE,
    ]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_plan(failures)
        audit_report(failures)
        audit_summary(failures)
        audit_text_and_receipt(failures)
        audit_overlay_files(failures)
        audit_secret_residue(failures)
        audit_next_gate(failures)

    if failures:
        print("provider condition runtime separation recovery audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("provider condition runtime separation recovery audit: clean pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
