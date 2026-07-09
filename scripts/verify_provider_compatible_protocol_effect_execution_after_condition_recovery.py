#!/usr/bin/env python3
"""Publish iter53 provider-compatible execution-after-condition-recovery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any

from run_ephemeral_vertex_codeclash_provider import build_harness_report
from run_provider_compatible_protocol_effect_pairs import (
    EXCLUDED_PAIR_IDS,
    READY_PAIR_IDS,
    build_condition_separated_plan,
)


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter53_provider_compatible_protocol_effect_execution_after_condition_recovery"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
SOURCE_ITER52_SUMMARY = (
    ROOT / "experiments" / "iter52_provider_condition_runtime_separation_recovery" / "proof" / "run_summary.json"
)
SOURCE_ITER52_PLAN = (
    ROOT
    / "experiments"
    / "iter52_provider_condition_runtime_separation_recovery"
    / "proof"
    / "condition_runtime_separation_plan.json"
)
SOURCE_SLICE = (
    ROOT
    / "experiments"
    / "iter48_provider_compatible_protocol_effect_slice_refreeze"
    / "proof"
    / "provider_compatible_slice.json"
)
PRIOR_PROVIDER_PROOF = ROOT / "experiments" / "iter21_opponent_collision_control" / "proof"
WRAPPER = ROOT / "scripts" / "run_provider_compatible_protocol_effect_pairs.py"
BASE_HARNESS = ROOT / "scripts" / "run_ephemeral_vertex_codeclash_provider.py"
CODECLASH_CACHE = Path("/tmp/telos-codeclash")
CODECLASH_COMMIT = "381cdfa05a35e8acd35853b9fc7e13005121b127"
NEXT_GATE = ROOT / "experiments" / "iter54_provider_pair_executor_recovery" / "HYPOTHESIS.md"
SECRET_SAFE_TIMEOUT_SECONDS = 10
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


def run_command(args: list[str], timeout: int = SECRET_SAFE_TIMEOUT_SECONDS) -> dict[str, Any]:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"returncode": None, "timed_out": True, "stdout_present": False}
    return {
        "returncode": result.returncode,
        "timed_out": False,
        "stdout_present": bool(result.stdout.strip()),
    }


def docker_state() -> dict[str, Any]:
    if shutil.which("docker") is None:
        return {
            "cli_present": False,
            "daemon_ready": False,
            "probe_timed_out": False,
        }
    probe = run_command(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=10)
    return {
        "cli_present": True,
        "daemon_ready": probe["returncode"] == 0 and probe["stdout_present"] is True,
        "probe_timed_out": bool(probe["timed_out"]),
    }


def codeclash_cache_state() -> dict[str, Any]:
    state: dict[str, Any] = {
        "cache_path": str(CODECLASH_CACHE),
        "checkout_present": CODECLASH_CACHE.is_dir(),
        "expected_commit": CODECLASH_COMMIT,
        "pinned_commit_present": False,
        "commit_identifier_logged": True,
        "global_codeclash_cli_present": shutil.which("codeclash") is not None,
    }
    if not CODECLASH_CACHE.is_dir():
        return state
    result = subprocess.run(
        ["git", "-C", str(CODECLASH_CACHE), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
        timeout=SECRET_SAFE_TIMEOUT_SECONDS,
    )
    state["pinned_commit_present"] = (
        result.returncode == 0 and result.stdout.strip() == CODECLASH_COMMIT
    )
    return state


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter53-provider-compatible-protocol-effect-execution-after-condition-recovery-{status}",
        "task_id": "telos:iter53_provider_compatible_protocol_effect_execution_after_condition_recovery@iter52",
        "agent_id": "codex-local-provider-compatible-execution-preflight",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Execute the two provider-compatible BattleSnake condition rows only if iter52 condition "
            "separation, provider readiness, CodeClash runner readiness, wrapper execution, cost "
            "capture, raw-artifact retention, receipt validation, redaction, and lifecycle controls "
            "are all ready before provider calls."
        ),
        "acceptance_criteria": [
            "Iter52 condition-runtime separation is a committed pass.",
            "Exactly two selected BattleSnake rows remain planned and all four excluded historical pairs remain unattempted.",
            "Provider calls do not start unless a committed pair executor can run the separated rows.",
            "Provider model invocations remain at or below 16 and provider spend remains at or below $10.00.",
            "No GPU is requested or used, no Sentinel-named resource is modified, and no production or live-domain behavior changes.",
            "The Telos row cannot count as verified completion without a valid receipt.",
            "No benchmark, leaderboard, SWE-bench, production, live-domain, model-superiority, or state-of-the-art result is claimed.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": (
                    "experiments/iter53_provider_compatible_protocol_effect_execution_after_condition_recovery/"
                    "proof/preflight.json"
                ),
                "notes": "Preflight records why the paid two-row execution did not start.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": (
                    "experiments/iter53_provider_compatible_protocol_effect_execution_after_condition_recovery/"
                    "proof/execution_report.json"
                ),
                "notes": "Execution report preserves blocked rows and uncomputed metrics.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": (
                    "experiments/iter53_provider_compatible_protocol_effect_execution_after_condition_recovery/"
                    "proof/review.md"
                ),
                "notes": "Review records the executor and runner-readiness gap.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if iter52 proof is missing, failed, blocked, or not validated.",
            "The result must block if the committed wrapper still cannot execute pair rows.",
            "The result must block if pinned CodeClash and Docker runner readiness are not cleanly available.",
            "The result must block if the base harness still declares full protocol-effect execution disabled.",
            "The result must fail if provider calls, spend, cloud runner startup, GPU use, Sentinel resource modification, or excluded-pair execution occurs after a blocking preflight.",
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
                break
    return not findings, findings


def metric_rows(status: str) -> dict[str, Any]:
    return {
        "primary": {
            "metric_id": "verified_completion_rate",
            "status": status,
            "exact_counts_available": False,
            "value": None,
            "reason": "no provider-compatible condition row executed",
        },
        "secondary": [
            {
                "metric_id": metric,
                "status": status,
                "value": None,
                "reason": "not computable without executed provider-backed pair artifacts",
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


def condition_rows(plan: dict[str, Any], status: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pair in plan.get("condition_pair_plans", []):
        rows.append(
            {
                "pair_id": pair.get("pair_id"),
                "task_id": pair.get("task_id"),
                "condition_id": pair.get("condition_id"),
                "runtime_condition_label": pair.get("runtime_condition_label"),
                "planned": True,
                "attempted": False,
                "blocked": status == "blocked",
                "verified_completion": None,
                "verified_completion_reason": "uncomputed_without_provider_execution",
                "provider_model_api_calls": 0,
                "provider_spend_usd": 0.0,
                "receipt_required_before_acceptance": pair.get(
                    "receipt_validation_plan", {}
                ).get("required_before_acceptance"),
                "future_execution_command": pair.get("future_execution_command"),
                "block_reason": "provider_pair_executor_not_recovered_before_execution",
            }
        )
    return rows


def build_preflight() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[str], list[str]]:
    iter52_summary = read_json(SOURCE_ITER52_SUMMARY)
    iter52_plan = read_json(SOURCE_ITER52_PLAN)
    slice_data = read_json(SOURCE_SLICE)
    condition_plan = build_condition_separated_plan()
    harness_report = build_harness_report(
        prior_proof=PRIOR_PROVIDER_PROOF,
        execute_lifecycle_probe=False,
        zone="us-central1-a",
    )
    provider_plan = harness_report.get("provider_execution_plan", {})
    docker = docker_state()
    codeclash_cache = codeclash_cache_state()
    wrapper_text = WRAPPER.read_text(encoding="utf-8") if WRAPPER.exists() else ""
    wrapper_execute_not_implemented = (
        "provider execution is intentionally not implemented in the iter52 recovery wrapper"
        in wrapper_text
    )

    blockers: list[str] = []
    failures: list[str] = []

    if iter52_summary.get("status") != "pass":
        blockers.append("iter52_summary_not_pass")
    if iter52_plan.get("status") != "condition_separated_ready":
        blockers.append("iter52_condition_plan_not_ready")
    if condition_plan.get("status") != "condition_separated_ready":
        blockers.append("condition_separated_plan_not_ready")
    if condition_plan.get("selected_pair_ids") != READY_PAIR_IDS:
        failures.append("selected_pair_ids_changed")
    if condition_plan.get("excluded_pair_ids") != EXCLUDED_PAIR_IDS:
        failures.append("excluded_pair_ids_changed")
    if slice_data.get("selected_pair_ids") != READY_PAIR_IDS:
        failures.append("source_slice_selected_pair_ids_changed")
    if not WRAPPER.exists():
        blockers.append("wrapper_script_missing")
    if wrapper_execute_not_implemented:
        blockers.append("wrapper_execute_pair_intentionally_not_implemented")
    if provider_plan.get("full_protocol_effect_execution_enabled") is not True:
        blockers.append("base_provider_harness_full_execution_disabled")
    if provider_plan.get("requires_future_gate_to_execute_task_condition_pairs") is not False:
        blockers.append("base_provider_harness_still_requires_future_task_condition_gate")
    if not codeclash_cache.get("pinned_commit_present"):
        blockers.append("pinned_codeclash_checkout_not_ready")
    if not docker.get("daemon_ready"):
        blockers.append("docker_daemon_not_ready")
    if docker.get("probe_timed_out"):
        blockers.append("docker_probe_timed_out")

    gcloud = harness_report.get("gcloud_readiness", {})
    if not gcloud.get("gcloud_present"):
        blockers.append("gcloud_missing")
    if gcloud.get("active_account_count", 0) < 1:
        blockers.append("gcloud_active_account_missing")
    if not gcloud.get("project_configured"):
        blockers.append("gcloud_project_missing")
    services = gcloud.get("services_enabled", {})
    for service in ["aiplatform.googleapis.com", "compute.googleapis.com", "iam.googleapis.com"]:
        if services.get(service) is not True:
            blockers.append(f"gcloud_service_not_enabled:{service}")
    if gcloud.get("dedicated_runner_visible_count") != 1:
        blockers.append("dedicated_runner_service_account_not_unique")

    status = "fail" if failures else "blocked" if blockers else "pass"
    preflight = {
        "schema_version": (
            "telos.provider_compatible_protocol_effect_execution_after_condition_recovery.preflight.v1"
        ),
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "source_iter52_summary_path": str(SOURCE_ITER52_SUMMARY.relative_to(ROOT)),
        "source_iter52_summary_sha256": sha256_file(SOURCE_ITER52_SUMMARY),
        "source_iter52_plan_path": str(SOURCE_ITER52_PLAN.relative_to(ROOT)),
        "source_iter52_plan_sha256": sha256_file(SOURCE_ITER52_PLAN),
        "source_slice_path": str(SOURCE_SLICE.relative_to(ROOT)),
        "source_slice_sha256": sha256_file(SOURCE_SLICE),
        "wrapper_script_path": str(WRAPPER.relative_to(ROOT)),
        "wrapper_script_sha256": sha256_file(WRAPPER),
        "base_harness_path": str(BASE_HARNESS.relative_to(ROOT)),
        "base_harness_sha256": sha256_file(BASE_HARNESS),
        "selected_pair_count": 2,
        "selected_pair_ids": READY_PAIR_IDS,
        "excluded_pair_count": 4,
        "excluded_pair_ids": EXCLUDED_PAIR_IDS,
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
            "iter52_summary_passed": iter52_summary.get("status") == "pass",
            "iter52_condition_plan_ready": iter52_plan.get("status")
            == "condition_separated_ready",
            "condition_plan_rebuilt_ready": condition_plan.get("status")
            == "condition_separated_ready",
            "exact_two_pairs_planned": condition_plan.get("selected_pair_ids") == READY_PAIR_IDS,
            "exact_four_exclusions_visible": condition_plan.get("excluded_pair_ids")
            == EXCLUDED_PAIR_IDS,
            "excluded_pairs_rejected_by_wrapper": condition_plan.get("rejected_pair_count") == 4,
            "baseline_and_telos_runtime_conditions_distinct": condition_plan.get(
                "condition_separation_checks", {}
            ).get("runtime_commands_distinct_beyond_output_root"),
            "telos_receipt_validation_required": condition_plan.get(
                "condition_separation_checks", {}
            ).get("telos_receipt_required_before_acceptance"),
            "wrapper_execute_mode_visible": condition_plan.get("wrapper_execution_modes", {}).get(
                "execute_mode_available"
            ),
            "wrapper_execute_pair_implemented": not wrapper_execute_not_implemented,
            "base_provider_harness_full_execution_enabled": provider_plan.get(
                "full_protocol_effect_execution_enabled"
            ),
            "base_provider_harness_requires_future_gate": provider_plan.get(
                "requires_future_gate_to_execute_task_condition_pairs"
            ),
            "pinned_codeclash_checkout_ready": codeclash_cache.get("pinned_commit_present"),
            "docker_daemon_ready": docker.get("daemon_ready"),
            "provider_credentials_visible_without_logging_identity": gcloud.get(
                "active_account_count", 0
            )
            > 0,
            "dedicated_runner_visible_without_logging_identity": gcloud.get(
                "dedicated_runner_visible_count"
            )
            == 1,
            "harness_dry_run_lifecycle_probe_mode": harness_report.get(
                "lifecycle_probe", {}
            ).get("mode"),
            "harness_dry_run_model_calls": harness_report.get("provider_model_api_calls"),
            "harness_dry_run_task_pairs_executed": harness_report.get(
                "full_task_condition_pairs_executed"
            ),
        },
        "docker": docker,
        "codeclash_cache": codeclash_cache,
        "gcloud_readiness": gcloud,
        "provider_execution_plan": provider_plan,
        "blockers": blockers,
        "failures": failures,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
    }
    return preflight, harness_report, condition_plan, blockers, failures


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    preflight, harness_report, condition_plan, blockers, failures = build_preflight()
    status = preflight["status"]

    write_json(PROOF / "preflight.json", preflight)
    write_json(PROOF / "harness_dry_run_report.json", harness_report)
    write_json(PROOF / "condition_runtime_plan_recheck.json", condition_plan)

    execution_report = {
        "schema_version": (
            "telos.provider_compatible_protocol_effect_execution_after_condition_recovery.report.v1"
        ),
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "planned_task_condition_pairs": 2,
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": 2 if status == "blocked" else 0,
        "excluded_task_condition_pairs_attempted": 0,
        "condition_rows": condition_rows(condition_plan, status),
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

    artifact_paths = [
        PROOF / "preflight.json",
        PROOF / "harness_dry_run_report.json",
        PROOF / "condition_runtime_plan_recheck.json",
        PROOF / "execution_report.json",
    ]
    scan_passed, scan_findings = secret_scan(artifact_paths)

    output_lines = [
        f"provider-compatible protocol-effect execution after condition recovery: {status}",
        f"source_iter52_summary={SOURCE_ITER52_SUMMARY.relative_to(ROOT)}",
        "planned_task_condition_pairs=2",
        "attempted_task_condition_pairs=0",
        "provider_model_api_calls=0",
        "provider_spend_usd=0.0",
        "cloud_runner_started=false",
        "gpu_used=false",
        "sentinel_named_resources_modified=false",
        f"docker_daemon_ready={str(preflight['checks']['docker_daemon_ready']).lower()}",
        f"pinned_codeclash_checkout_ready={str(preflight['checks']['pinned_codeclash_checkout_ready']).lower()}",
        f"wrapper_execute_pair_implemented={str(preflight['checks']['wrapper_execute_pair_implemented']).lower()}",
        f"blockers={','.join(blockers)}",
        f"failures={','.join(failures)}",
        f"next_gate={NEXT_GATE.relative_to(ROOT)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 53 Review

The paid two-row provider-compatible protocol-effect execution did not start. Iter52 remains a
clean condition-separation pass: the baseline and Telos rows have distinct runtime overlays,
prompts, commands, and a Telos receipt-validation path before acceptance.

The execution gate still lacks a committed pair executor. The wrapper exposes an execution mode,
but `execute_pair` intentionally raises instead of running CodeClash. The reusable provider harness
also still declares full protocol-effect execution disabled and requires a future task-condition
gate. This shell did not have a pinned `/tmp/telos-codeclash` checkout ready, and Docker readiness
did not produce a clean daemon-ready result before the timeout boundary.

Provider account/service readiness was visible without logging account, project, service-account,
VM, or zone identifiers. No provider model call occurred, no cloud runner started, no GPU was used,
and no Sentinel-named resource was modified. This is a blocked execution result, not a benchmark
null and not a model-result claim.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    result_md = f"""# Iteration 53 Result - Provider-Compatible Protocol-Effect Execution After Condition Recovery

Status: `{status.upper()}`.

## Summary

The bounded two-row paid pilot stopped before provider execution. Iter52 condition separation is
still valid, but the executable runner path is not recovered enough to start model calls.

- planned provider-compatible condition rows: `2`,
- attempted condition rows: `0`,
- excluded historical pairs attempted: `0`,
- provider model API calls: `0`,
- provider spend: `$0.00`,
- cloud runner started: `false`,
- GPU used: `false`,
- Sentinel-named resources modified: `false`.

## Blockers

{chr(10).join(f"- `{blocker}`" for blocker in blockers)}

## What Is Now Authorized

- Pre-register and recover a provider pair executor that can clone or verify the pinned CodeClash
  checkout, copy the iter52 overlays, prove Docker/runner readiness, materialize exact commands,
  and preserve raw artifact, cost, redaction, receipt, and teardown controls before any paid retry.

## What Remains Forbidden

- No benchmark result is claimed.
- No SWE-bench score is claimed.
- No leaderboard result is claimed.
- No production or live-domain result is claimed.
- No model-superiority or state-of-the-art result is claimed.
- No provider-backed protocol-effect metric is inferred from the blocked preflight.

## Evidence

- `proof/preflight.json`
- `proof/harness_dry_run_report.json`
- `proof/condition_runtime_plan_recheck.json`
- `proof/execution_report.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_provider_compatible_protocol_effect_execution_after_condition_recovery.json`
"""
    (EXPERIMENT / "RESULT.md").write_text(result_md, encoding="utf-8")

    artifact_paths.extend([PROOF / "command_output.txt", PROOF / "review.md"])
    run_summary = {
        "schema_version": (
            "telos.provider_compatible_protocol_effect_execution_after_condition_recovery.summary.v1"
        ),
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "source_iter52_summary_path": str(SOURCE_ITER52_SUMMARY.relative_to(ROOT)),
        "source_iter52_summary_sha256": sha256_file(SOURCE_ITER52_SUMMARY),
        "source_iter52_plan_path": str(SOURCE_ITER52_PLAN.relative_to(ROOT)),
        "source_iter52_plan_sha256": sha256_file(SOURCE_ITER52_PLAN),
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
        "redaction_scan_passed": scan_passed,
        "redaction_findings": scan_findings,
        "clean_pass": False,
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
        "experiment_id": EXPERIMENT_ID,
        "status": "blocked" if status == "blocked" else status,
        "insight": (
            "Condition separation is ready, but paid provider-compatible execution still needs a "
            "committed pair executor plus pinned CodeClash and Docker runner readiness before model "
            "calls can start."
        ),
        "next_action": (
            "recover a zero-spend provider pair executor that proves pinned CodeClash checkout, "
            "overlay copy, exact command materialization, Docker readiness, artifact capture, "
            "cost parsing, receipt validation, redaction, and teardown controls"
        ),
        "result_path": (
            "experiments/iter53_provider_compatible_protocol_effect_execution_after_condition_recovery/RESULT.md"
        ),
        "evidence_paths": [
            "experiments/iter53_provider_compatible_protocol_effect_execution_after_condition_recovery/proof/run_summary.json",
            "experiments/iter53_provider_compatible_protocol_effect_execution_after_condition_recovery/proof/preflight.json",
            "experiments/iter53_provider_compatible_protocol_effect_execution_after_condition_recovery/proof/execution_report.json",
            "experiments/iter53_provider_compatible_protocol_effect_execution_after_condition_recovery/proof/command_output.txt",
            "experiments/iter53_provider_compatible_protocol_effect_execution_after_condition_recovery/proof/review.md",
            "experiments/iter53_provider_compatible_protocol_effect_execution_after_condition_recovery/proof/valid/receipt_provider_compatible_protocol_effect_execution_after_condition_recovery.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(
        VALID / "receipt_provider_compatible_protocol_effect_execution_after_condition_recovery.json",
        build_receipt(status),
    )

    print("\n".join(output_lines))
    return 0 if status in {"blocked", "pass"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
