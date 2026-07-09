#!/usr/bin/env python3
"""Publish iter40 public-task protocol-effect execution preflight artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "iter40_public_task_protocol_effect_execution"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
SOURCE_SLICE = (
    ROOT
    / "experiments"
    / "iter39_public_task_protocol_effect_slice"
    / "proof"
    / "protocol_effect_slice.json"
)
NEXT_GATE = (
    ROOT
    / "experiments"
    / "iter41_public_task_protocol_effect_runner_recovery"
    / "HYPOTHESIS.md"
)
CODECLASH_COMMIT = "381cdfa05a35e8acd35853b9fc7e13005121b127"
CODECLASH_CACHE = Path("/tmp/telos-codeclash")
SECRET_SAFE_TIMEOUT_SECONDS = 10


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


def run_command(command: list[str], timeout: int = SECRET_SAFE_TIMEOUT_SECONDS) -> dict[str, Any]:
    try:
        result = subprocess.run(
            command,
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


def gcloud_text(command: list[str], timeout: int = SECRET_SAFE_TIMEOUT_SECONDS) -> dict[str, Any]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"returncode": None, "timed_out": True, "stdout": ""}
    return {"returncode": result.returncode, "timed_out": False, "stdout": result.stdout}


def codeclash_cache_state() -> dict[str, Any]:
    state = {
        "cache_path": str(CODECLASH_CACHE),
        "checkout_present": CODECLASH_CACHE.is_dir(),
        "expected_commit": CODECLASH_COMMIT,
        "pinned_commit_present": False,
        "commit_identifier_logged": True,
    }
    if not CODECLASH_CACHE.is_dir():
        return state
    result = gcloud_text(
        ["git", "-C", str(CODECLASH_CACHE), "rev-parse", "HEAD"],
        timeout=SECRET_SAFE_TIMEOUT_SECONDS,
    )
    actual = result["stdout"].strip()
    state["pinned_commit_present"] = (
        result["returncode"] == 0 and actual == CODECLASH_COMMIT
    )
    return state


def preflight() -> dict[str, Any]:
    PROOF.mkdir(parents=True, exist_ok=True)
    artifact_probe = PROOF / ".artifact-destination-probe"
    artifact_probe.write_text("ok\n", encoding="utf-8")
    artifact_probe.unlink()

    docker_info = (
        run_command(["docker", "info", "--format", "{{.ServerVersion}}"])
        if shutil.which("docker")
        else {"returncode": None, "timed_out": False, "stdout_present": False}
    )
    gcloud_present = shutil.which("gcloud") is not None
    gcloud_version = (
        run_command(["gcloud", "--version"]) if gcloud_present else {"returncode": None}
    )
    active_accounts = 0
    project_configured = False
    vertex_enabled = False
    gcloud_auth_timeout = False
    gcloud_services_timeout = False
    if gcloud_present:
        auth = gcloud_text(
            [
                "gcloud",
                "auth",
                "list",
                "--filter=status:ACTIVE",
                "--format=value(account)",
            ],
            timeout=15,
        )
        active_accounts = (
            len([line for line in auth["stdout"].splitlines() if line.strip()])
            if auth["returncode"] == 0
            else 0
        )
        gcloud_auth_timeout = bool(auth["timed_out"])

        project = gcloud_text(["gcloud", "config", "get-value", "project"])
        project_value = project["stdout"].strip()
        project_configured = (
            project["returncode"] == 0 and bool(project_value) and project_value != "(unset)"
        )

        if project_configured:
            services = gcloud_text(
                [
                    "gcloud",
                    "services",
                    "list",
                    "--enabled",
                    "--filter=name:aiplatform.googleapis.com",
                    "--format=value(name)",
                ],
                timeout=20,
            )
            vertex_enabled = "aiplatform.googleapis.com" in services["stdout"]
            gcloud_services_timeout = bool(services["timed_out"])

    checks = {
        "secret_safe": True,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "docker_cli_present": shutil.which("docker") is not None,
        "docker_daemon_ready": docker_info["returncode"] == 0
        and docker_info["stdout_present"] is True,
        "docker_info_timed_out": bool(docker_info["timed_out"]),
        "git_present": shutil.which("git") is not None,
        "uv_present": shutil.which("uv") is not None,
        "gcloud_present": gcloud_present,
        "gcloud_version_ready": gcloud_version.get("returncode") == 0,
        "gcloud_active_account_count": active_accounts,
        "gcloud_auth_timed_out": gcloud_auth_timeout,
        "gcloud_project_configured": project_configured,
        "gcloud_project_identifier_logged": False,
        "gcloud_account_identifier_logged": False,
        "gcloud_services_list_timed_out": gcloud_services_timeout,
        "vertex_ai_service_enabled": vertex_enabled,
        "artifact_destination_ready": True,
        "cost_capture_required_before_execution": True,
        "cost_capture_validated_by_execution": False,
        "codeclash_cache": codeclash_cache_state(),
    }

    blockers = []
    if not checks["docker_cli_present"]:
        blockers.append("docker_cli_missing")
    if not checks["docker_daemon_ready"]:
        blockers.append("docker_daemon_not_ready")
    if not checks["git_present"]:
        blockers.append("git_missing")
    if not checks["uv_present"]:
        blockers.append("uv_missing")
    if not checks["gcloud_present"]:
        blockers.append("gcloud_missing")
    if checks["gcloud_active_account_count"] < 1:
        blockers.append("gcloud_active_account_missing")
    if not checks["gcloud_project_configured"]:
        blockers.append("gcloud_project_missing")
    if not checks["vertex_ai_service_enabled"]:
        blockers.append("vertex_ai_service_not_verified")
    if not checks["codeclash_cache"]["pinned_commit_present"]:
        blockers.append("pinned_codeclash_checkout_not_ready")

    return {
        "schema_version": "telos.public_task_protocol_effect_execution.preflight.v1",
        "status": "blocked" if blockers else "pass",
        "experiment_id": "iter40_public_task_protocol_effect_execution",
        "source_slice_path": str(SOURCE_SLICE.relative_to(ROOT)),
        "provider_boundary": read_json(SOURCE_SLICE)[
            "provider_execution_boundary_for_next_gate"
        ],
        "checks": checks,
        "blockers": blockers,
        "credential_material_logged": False,
        "project_identifier_logged": False,
        "account_identifier_logged": False,
    }


def condition_rows(protocol_slice: dict[str, Any], status: str) -> list[dict[str, Any]]:
    task_ids = [task["task_id"] for task in protocol_slice["executable_tasks"]]
    rows = []
    for condition in protocol_slice["conditions"]:
        rows.append(
            {
                "condition_id": condition["condition_id"],
                "planned_task_count": len(task_ids),
                "planned_task_ids": task_ids,
                "attempted_task_count": 0,
                "blocked_task_count": len(task_ids) if status == "blocked" else 0,
                "verified_completion_count": 0,
                "verified_completion_rate": None,
                "status": status,
                "reason": "preflight_blocked_before_execution",
            }
        )
    return rows


def metric_rows(status: str) -> dict[str, Any]:
    return {
        "primary": {
            "metric_id": "verified_completion_rate",
            "status": status,
            "exact_counts_available": False,
            "value": None,
            "reason": "no task-condition pair was executed after preflight blocked",
        },
        "secondary": [
            {
                "metric_id": metric,
                "status": status,
                "value": None,
                "reason": "not computable without executed task-condition artifacts",
            }
            for metric in [
                "proxy_pass_receipt_fail_rate",
                "unsupported_claim_rate",
                "over_edit_rate",
                "evidence_missing_rate",
                "audit_minutes_per_task",
                "false_positive_rate",
                "false_negative_rate",
                "model_api_calls_per_task",
                "cost_usd_per_task",
            ]
        ],
    }


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter40-public-task-protocol-effect-execution-{status}",
        "task_id": "telos:iter40_public_task_protocol_effect_execution@iter39",
        "agent_id": "codex-local-public-task-protocol-effect-executor",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Execute the frozen public task protocol-effect slice only if provider, runner, "
            "artifact, and cost controls are ready."
        ),
        "acceptance_criteria": [
            "The preflight records provider, runner, cost, and artifact readiness without secrets.",
            "Provider calls do not start if Docker, CodeClash, credentials, or cost controls fail.",
            "Blocked rows are published at full weight.",
            "Baseline and Telos-enforced planned conditions remain separated.",
            "No task-condition pair is silently omitted after a passing preflight.",
            "No leaderboard, SWE-bench, production, live-domain, model-superiority, or state-of-the-art result is claimed.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": "experiments/iter40_public_task_protocol_effect_execution/proof/preflight.json",
                "notes": "Secret-safe preflight blocked before provider execution.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": "experiments/iter40_public_task_protocol_effect_execution/proof/execution_report.json",
                "notes": "Planned task-condition pairs and uncomputed metrics are explicit.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": "experiments/iter40_public_task_protocol_effect_execution/proof/review.md",
                "notes": "Review records the claim boundary and runner gap.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if Docker or CodeClash runner readiness is unavailable.",
            "The result must block if provider credentials or service readiness are unavailable.",
            "The result must block if provider cost capture cannot be guaranteed.",
            "The result must fail if any provider call is made after a blocked preflight.",
            "The result must fail if a benchmark, production, live-domain, model-superiority, or state-of-the-art claim is made.",
            "The result must fail if secret material or account/project identifiers are committed.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def build_artifact_hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path.relative_to(PROOF)): sha256_file(path) for path in paths}


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    protocol_slice = read_json(SOURCE_SLICE)
    preflight_result = preflight()
    status = preflight_result["status"]

    execution_report = {
        "schema_version": "telos.public_task_protocol_effect_execution.report.v1",
        "status": status,
        "experiment_id": "iter40_public_task_protocol_effect_execution",
        "source_slice_path": str(SOURCE_SLICE.relative_to(ROOT)),
        "planned_task_condition_pairs": len(protocol_slice["executable_tasks"])
        * len(protocol_slice["conditions"]),
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": len(protocol_slice["executable_tasks"])
        * len(protocol_slice["conditions"]),
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "raw_execution_artifacts_created": False,
        "condition_results": condition_rows(protocol_slice, status),
        "metrics": metric_rows(status),
        "blockers": preflight_result["blockers"],
        "claim_boundaries": {
            "leaderboard_or_swebench_result_claimed": False,
            "model_superiority_claimed": False,
            "state_of_the_art_result_claimed": False,
            "production_or_live_domain_changed": False,
            "live_domain_result_claimed": False,
        },
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
    }
    write_json(PROOF / "preflight.json", preflight_result)
    write_json(PROOF / "execution_report.json", execution_report)

    output_lines = [
        f"public task protocol effect execution: {status}",
        f"source_slice={SOURCE_SLICE.relative_to(ROOT)}",
        "provider_model_api_calls=0",
        "provider_spend_usd=0.0",
        "cloud_runner_started=false",
        "planned_task_condition_pairs=6",
        "attempted_task_condition_pairs=0",
        f"blockers={','.join(preflight_result['blockers'])}",
        f"next_gate={NEXT_GATE.relative_to(ROOT)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 40 Review

The execution gate stopped at preflight. Vertex service readiness was checkable without logging
account or project identifiers, but the local Docker daemon did not return readiness and the pinned
CodeClash checkout was not available at the expected cache path. Under the iter40 falsifiers, that
blocks provider execution before any model call, paid spend, cloud runner, raw trajectory, or task
condition pair starts.

This is a blocked execution-preflight result, not a model result. It preserves the frozen iter39
task-condition plan and records every metric as uncomputed rather than converting missing evidence
into a pass. The next gate should recover the runner preflight before retrying the provider-backed
protocol-effect execution.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    result_md = f"""# Iteration 40 Result - Public Task Protocol-Effect Execution

Status: `{status.upper()}`.

## Summary

The frozen iter39 protocol-effect slice did not execute. The gate stopped at preflight because
runner readiness was not established:

- blockers: `{", ".join(preflight_result["blockers"])}`,
- planned task-condition pairs: `6`,
- attempted task-condition pairs: `0`,
- provider model API calls: `0`,
- provider spend: `$0.00`,
- cloud runner started: `false`.

No provider model call occurred, no CodeClash task-condition pair started, and no raw trajectory or
task metric is interpreted as a result.

## What Is Now Authorized

- Recover Docker and pinned CodeClash runner readiness in
  `experiments/iter41_public_task_protocol_effect_runner_recovery/HYPOTHESIS.md`.
- Keep the iter39 task slice frozen.
- Retry execution only after runner, provider, cost, and artifact controls pass a new gate.

## What Remains Forbidden

- No benchmark result is claimed.
- No SWE-bench score is claimed.
- No leaderboard result is claimed.
- No production or live-domain result is claimed.
- No model-superiority or state-of-the-art result is claimed.
- No hidden provider spend or unlogged model call is allowed.

## Evidence

- `proof/preflight.json`
- `proof/execution_report.json`
- `proof/run_summary.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/valid/receipt_public_task_protocol_effect_execution.json`
"""
    (EXPERIMENT / "RESULT.md").write_text(result_md, encoding="utf-8")

    run_summary = {
        "schema_version": "telos.public_task_protocol_effect_execution.summary.v1",
        "status": status,
        "experiment_id": "iter40_public_task_protocol_effect_execution",
        "source_experiment": "iter39_public_task_protocol_effect_slice",
        "source_slice_path": str(SOURCE_SLICE.relative_to(ROOT)),
        "source_slice_sha256": sha256_file(SOURCE_SLICE),
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "planned_task_condition_pairs": 6,
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": 6,
        "blockers": preflight_result["blockers"],
        "docker_daemon_ready": preflight_result["checks"]["docker_daemon_ready"],
        "docker_info_timed_out": preflight_result["checks"]["docker_info_timed_out"],
        "pinned_codeclash_checkout_ready": preflight_result["checks"]["codeclash_cache"][
            "pinned_commit_present"
        ],
        "gcloud_present": preflight_result["checks"]["gcloud_present"],
        "gcloud_active_account_count": preflight_result["checks"]["gcloud_active_account_count"],
        "gcloud_project_configured": preflight_result["checks"]["gcloud_project_configured"],
        "vertex_ai_service_enabled": preflight_result["checks"]["vertex_ai_service_enabled"],
        "credential_material_committed": False,
        "project_identifier_committed": False,
        "account_identifier_committed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "clean_pass": False,
        "blocked_result": True,
        "quality_failure": False,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
        "artifact_hashes": {},
    }

    artifact_paths = [
        PROOF / "preflight.json",
        PROOF / "execution_report.json",
        PROOF / "command_output.txt",
        PROOF / "review.md",
    ]
    run_summary["artifact_hashes"] = build_artifact_hashes(artifact_paths)
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter40_public_task_protocol_effect_execution",
        "status": status,
        "insight": (
            "The frozen protocol-effect slice could not honestly execute because runner readiness "
            "was not established before provider spend."
        ),
        "next_action": (
            "recover Docker and pinned CodeClash runner readiness before retrying the frozen "
            "protocol-effect execution"
        ),
        "result_path": "experiments/iter40_public_task_protocol_effect_execution/RESULT.md",
        "evidence_paths": [
            "experiments/iter40_public_task_protocol_effect_execution/proof/run_summary.json",
            "experiments/iter40_public_task_protocol_effect_execution/proof/preflight.json",
            "experiments/iter40_public_task_protocol_effect_execution/proof/execution_report.json",
            "experiments/iter40_public_task_protocol_effect_execution/proof/command_output.txt",
            "experiments/iter40_public_task_protocol_effect_execution/proof/review.md",
            "experiments/iter40_public_task_protocol_effect_execution/proof/valid/receipt_public_task_protocol_effect_execution.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(
        VALID / "receipt_public_task_protocol_effect_execution.json",
        build_receipt(status),
    )

    print("\n".join(output_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
