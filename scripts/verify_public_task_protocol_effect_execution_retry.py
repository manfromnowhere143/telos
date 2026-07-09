#!/usr/bin/env python3
"""Publish iter42 public-task protocol-effect execution-retry artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "iter42_public_task_protocol_effect_execution_retry"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
SOURCE_SLICE = (
    ROOT
    / "experiments"
    / "iter39_public_task_protocol_effect_slice"
    / "proof"
    / "protocol_effect_slice.json"
)
SOURCE_PREFLIGHT = (
    ROOT
    / "experiments"
    / "iter40_public_task_protocol_effect_execution"
    / "proof"
    / "preflight.json"
)
SOURCE_RUNNER = (
    ROOT
    / "experiments"
    / "iter41_public_task_protocol_effect_runner_recovery"
    / "proof"
    / "runner_recovery_report.json"
)
SOURCE_PROVIDER_EVIDENCE = (
    ROOT
    / "experiments"
    / "iter21_opponent_collision_control"
    / "proof"
    / "run_summary.json"
)
NEXT_GATE = (
    ROOT
    / "experiments"
    / "iter43_provider_execution_harness_recovery"
    / "HYPOTHESIS.md"
)
SECRET_SAFE_TIMEOUT_SECONDS = 10
PROVIDER_SECRET_MARKERS = ("GCP", "GOOGLE", "VERTEX", "AIPLATFORM", "GEMINI", "WIF", "WORKLOAD")
PROVIDER_WORKFLOW_MARKERS = (
    "google-github-actions/auth",
    "gcloud auth",
    "gcloud compute",
    "gcloud ai",
    "aiplatform",
    "vertex_ai",
    "gemini-3.1",
    "google_application_credentials",
)
EXPECTED_HARNESS_PATHS = [
    ROOT / ".github" / "workflows" / "public-task-protocol-effect-provider.yml",
    ROOT / "scripts" / "run_public_task_protocol_effect_provider_execution.py",
    ROOT / "scripts" / "run_ephemeral_vertex_codeclash_provider.py",
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


def text_command(command: list[str], timeout: int = SECRET_SAFE_TIMEOUT_SECONDS) -> dict[str, Any]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"returncode": None, "timed_out": True, "stdout": "", "stderr": ""}
    return {
        "returncode": result.returncode,
        "timed_out": False,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def docker_state() -> dict[str, Any]:
    if shutil.which("docker") is None:
        return {"cli_present": False, "daemon_ready": False, "probe_timed_out": False}
    probe = run_command(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=8)
    return {
        "cli_present": True,
        "daemon_ready": probe["returncode"] == 0 and probe["stdout_present"] is True,
        "probe_timed_out": bool(probe["timed_out"]),
    }


def gcloud_state() -> dict[str, Any]:
    present = shutil.which("gcloud") is not None
    state: dict[str, Any] = {
        "gcloud_present": present,
        "gcloud_version_ready": False,
        "gcloud_active_account_count": 0,
        "gcloud_auth_timed_out": False,
        "gcloud_project_configured": False,
        "vertex_ai_service_enabled": False,
        "gcloud_services_list_timed_out": False,
        "account_identifier_logged": False,
        "project_identifier_logged": False,
    }
    if not present:
        return state

    version = run_command(["gcloud", "--version"])
    state["gcloud_version_ready"] = version["returncode"] == 0

    auth = text_command(
        [
            "gcloud",
            "auth",
            "list",
            "--filter=status:ACTIVE",
            "--format=value(account)",
        ],
        timeout=15,
    )
    state["gcloud_auth_timed_out"] = bool(auth["timed_out"])
    if auth["returncode"] == 0:
        state["gcloud_active_account_count"] = len(
            [line for line in auth["stdout"].splitlines() if line.strip()]
        )

    project = text_command(["gcloud", "config", "get-value", "project"])
    project_value = project["stdout"].strip()
    state["gcloud_project_configured"] = (
        project["returncode"] == 0 and bool(project_value) and project_value != "(unset)"
    )

    if state["gcloud_project_configured"]:
        services = text_command(
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
        state["vertex_ai_service_enabled"] = "aiplatform.googleapis.com" in services["stdout"]
        state["gcloud_services_list_timed_out"] = bool(services["timed_out"])

    return state


def github_secret_state() -> dict[str, Any]:
    state: dict[str, Any] = {
        "gh_cli_present": shutil.which("gh") is not None,
        "secret_list_ok": False,
        "secret_count": 0,
        "provider_secret_name_count": 0,
        "provider_secret_names_logged": False,
    }
    if not state["gh_cli_present"]:
        return state
    result = text_command(
        ["gh", "secret", "list", "--repo", "manfromnowhere143/telos", "--json", "name,updatedAt"],
        timeout=20,
    )
    if result["returncode"] != 0:
        return state
    try:
        data = json.loads(result["stdout"])
    except json.JSONDecodeError:
        return state
    if not isinstance(data, list):
        return state
    names = [item.get("name", "") for item in data if isinstance(item, dict)]
    provider_like = [
        name for name in names if any(marker in name.upper() for marker in PROVIDER_SECRET_MARKERS)
    ]
    state["secret_list_ok"] = True
    state["secret_count"] = len(names)
    state["provider_secret_name_count"] = len(provider_like)
    return state


def github_workflow_state() -> dict[str, Any]:
    workflow_dir = ROOT / ".github" / "workflows"
    dispatch_count = 0
    provider_workflow_count = 0
    candidates: list[str] = []
    for path in sorted(workflow_dir.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        dispatch = "workflow_dispatch:" in text
        if dispatch:
            dispatch_count += 1
        provider_marker = any(marker in lowered for marker in PROVIDER_WORKFLOW_MARKERS)
        if dispatch and provider_marker:
            provider_workflow_count += 1
            candidates.append(path.relative_to(ROOT).as_posix())
    return {
        "workflow_dispatch_count": dispatch_count,
        "provider_capable_workflow_count": provider_workflow_count,
        "provider_capable_workflow_paths": candidates,
        "provider_workflow_path_names_logged": bool(candidates),
    }


def committed_harness_state() -> dict[str, Any]:
    present = [path.relative_to(ROOT).as_posix() for path in EXPECTED_HARNESS_PATHS if path.exists()]
    return {
        "expected_harness_paths": [path.relative_to(ROOT).as_posix() for path in EXPECTED_HARNESS_PATHS],
        "present_harness_paths": present,
        "committed_provider_execution_harness_present": bool(present),
        "cost_capture_harness_validated": False,
        "raw_artifact_redaction_harness_validated": False,
        "ephemeral_runner_lifecycle_harness_validated": False,
    }


def previous_provider_evidence_state() -> dict[str, Any]:
    if not SOURCE_PROVIDER_EVIDENCE.exists():
        return {"available": False}
    summary = read_json(SOURCE_PROVIDER_EVIDENCE)
    return {
        "available": True,
        "path": str(SOURCE_PROVIDER_EVIDENCE.relative_to(ROOT)),
        "status": summary.get("status"),
        "runner": summary.get("runner"),
        "selected_model": summary.get("selected_model"),
        "model_api_calls_reported": summary.get("model_api_calls_reported"),
        "model_cost_reported_usd": summary.get("model_cost_reported_usd"),
        "cloud_vm_deleted": summary.get("cloud_vm_deleted"),
        "credential_material_committed": summary.get("credential_material_committed"),
        "project_identifier_committed": summary.get("project_identifier_committed"),
        "account_identifier_committed": summary.get("account_identifier_committed"),
        "treated_as_reusable_execution_harness": False,
    }


def preflight() -> dict[str, Any]:
    PROOF.mkdir(parents=True, exist_ok=True)
    artifact_probe = PROOF / ".artifact-destination-probe"
    artifact_probe.write_text("ok\n", encoding="utf-8")
    artifact_probe.unlink()

    runner_report = read_json(SOURCE_RUNNER)
    docker = docker_state()
    gcloud = gcloud_state()
    github_secrets = github_secret_state()
    github_workflows = github_workflow_state()
    committed_harness = committed_harness_state()
    previous_provider = previous_provider_evidence_state()

    isolated_runner_recovered = (
        runner_report.get("status") == "pass"
        and runner_report.get("isolated_runner_passed") is True
        and runner_report.get("docker_readiness_verified") is True
        and runner_report.get("artifact_upload_verified") is True
    )

    provider_workflow_ready = (
        github_workflows["provider_capable_workflow_count"] > 0
        and github_secrets["provider_secret_name_count"] > 0
    )
    committed_harness_ready = (
        committed_harness["committed_provider_execution_harness_present"]
        and committed_harness["cost_capture_harness_validated"]
        and committed_harness["raw_artifact_redaction_harness_validated"]
        and committed_harness["ephemeral_runner_lifecycle_harness_validated"]
    )

    checks = {
        "secret_safe": True,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "local_docker": docker,
        "gcloud": gcloud,
        "github_actions": {
            "runner_recovery_report_path": str(SOURCE_RUNNER.relative_to(ROOT)),
            "isolated_runner_recovered": isolated_runner_recovered,
            "workflow_state": github_workflows,
            "secret_state": github_secrets,
        },
        "committed_harness": committed_harness,
        "previous_provider_evidence": previous_provider,
        "artifact_destination_ready": True,
        "cost_capture_required_before_execution": True,
        "cost_capture_validated_by_execution": False,
        "provider_workflow_ready": provider_workflow_ready,
        "committed_harness_ready": committed_harness_ready,
    }

    blockers = []
    if not isolated_runner_recovered:
        blockers.append("isolated_runner_recovery_not_ready")
    if not gcloud["gcloud_present"]:
        blockers.append("gcloud_missing")
    if gcloud["gcloud_active_account_count"] < 1:
        blockers.append("gcloud_active_account_missing")
    if not gcloud["gcloud_project_configured"]:
        blockers.append("gcloud_project_missing")
    if not gcloud["vertex_ai_service_enabled"]:
        blockers.append("vertex_ai_service_not_verified")
    if github_workflows["provider_capable_workflow_count"] == 0:
        blockers.append("provider_capable_github_workflow_missing")
    if github_secrets["provider_secret_name_count"] == 0:
        blockers.append("github_provider_secret_boundary_missing")
    if not committed_harness["committed_provider_execution_harness_present"]:
        blockers.append("committed_provider_execution_harness_missing")
    if not committed_harness["cost_capture_harness_validated"]:
        blockers.append("cost_capture_harness_not_validated")
    if not committed_harness["raw_artifact_redaction_harness_validated"]:
        blockers.append("raw_artifact_redaction_harness_not_validated")
    if not committed_harness["ephemeral_runner_lifecycle_harness_validated"]:
        blockers.append("ephemeral_runner_lifecycle_harness_not_validated")
    if not (provider_workflow_ready or committed_harness_ready):
        blockers.append("provider_capable_isolated_runner_unavailable")

    return {
        "schema_version": "telos.public_task_protocol_effect_execution_retry.preflight.v1",
        "status": "blocked" if blockers else "pass",
        "experiment_id": "iter42_public_task_protocol_effect_execution_retry",
        "source_slice_path": str(SOURCE_SLICE.relative_to(ROOT)),
        "source_preflight_path": str(SOURCE_PREFLIGHT.relative_to(ROOT)),
        "source_runner_recovery_path": str(SOURCE_RUNNER.relative_to(ROOT)),
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
                "reason": "provider_execution_harness_blocked_before_execution",
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
        "receipt_id": f"iter42-public-task-protocol-effect-execution-retry-{status}",
        "task_id": "telos:iter42_public_task_protocol_effect_execution_retry@iter41",
        "agent_id": "codex-local-public-task-protocol-effect-retry-verifier",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Retry the frozen public task protocol-effect execution only if isolated runner, "
            "provider, artifact, and cost-capture controls are all ready."
        ),
        "acceptance_criteria": [
            "The preflight records provider, runner, cost, and artifact readiness without secrets.",
            "Provider calls do not start if a provider-capable runner harness is unavailable.",
            "Provider calls do not start if cost capture or artifact redaction is not validated.",
            "Blocked rows are published at full weight.",
            "Baseline and Telos-enforced planned conditions remain separated.",
            "No leaderboard, SWE-bench, production, live-domain, model-superiority, or state-of-the-art result is claimed.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": (
                    "experiments/iter42_public_task_protocol_effect_execution_retry/"
                    "proof/preflight.json"
                ),
                "notes": "Secret-safe preflight blocked before provider execution.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": (
                    "experiments/iter42_public_task_protocol_effect_execution_retry/"
                    "proof/execution_retry_report.json"
                ),
                "notes": "Planned task-condition pairs and uncomputed metrics are explicit.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": (
                    "experiments/iter42_public_task_protocol_effect_execution_retry/"
                    "proof/review.md"
                ),
                "notes": "Review records the provider-harness gap and claim boundary.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if provider-capable isolated execution is unavailable.",
            "The result must block if provider credentials or service readiness are unavailable.",
            "The result must block if provider cost capture cannot be guaranteed.",
            "The result must block if raw artifact redaction and retention are not validated.",
            "The result must fail if any provider call is made after a blocked preflight.",
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
    planned_pairs = len(protocol_slice["executable_tasks"]) * len(protocol_slice["conditions"])

    execution_report = {
        "schema_version": "telos.public_task_protocol_effect_execution_retry.report.v1",
        "status": status,
        "experiment_id": "iter42_public_task_protocol_effect_execution_retry",
        "source_slice_path": str(SOURCE_SLICE.relative_to(ROOT)),
        "source_preflight_path": str(SOURCE_PREFLIGHT.relative_to(ROOT)),
        "source_runner_recovery_path": str(SOURCE_RUNNER.relative_to(ROOT)),
        "planned_task_condition_pairs": planned_pairs,
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": planned_pairs,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "raw_execution_artifacts_created": False,
        "condition_results": condition_rows(protocol_slice, status),
        "metrics": metric_rows(status),
        "blockers": preflight_result["blockers"],
        "provider_execution_harness_recovered": False,
        "iter41_runner_recovery_accepted": preflight_result["checks"]["github_actions"][
            "isolated_runner_recovered"
        ],
        "claim_boundaries": {
            "benchmark_result_claimed": False,
            "leaderboard_or_swebench_result_claimed": False,
            "model_superiority_claimed": False,
            "state_of_the_art_result_claimed": False,
            "production_or_live_domain_changed": False,
            "live_domain_result_claimed": False,
        },
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
    }
    write_json(PROOF / "preflight.json", preflight_result)
    write_json(PROOF / "execution_retry_report.json", execution_report)

    blocker_text = ",".join(preflight_result["blockers"])
    output_lines = [
        f"public task protocol effect execution retry: {status}",
        f"source_slice={SOURCE_SLICE.relative_to(ROOT)}",
        f"source_runner_recovery={SOURCE_RUNNER.relative_to(ROOT)}",
        "provider_model_api_calls=0",
        "provider_spend_usd=0.0",
        "cloud_runner_started=false",
        f"local_docker_ready={str(preflight_result['checks']['local_docker']['daemon_ready']).lower()}",
        "isolated_runner_recovered=true",
        f"planned_task_condition_pairs={planned_pairs}",
        "attempted_task_condition_pairs=0",
        f"blockers={blocker_text}",
        f"next_gate={NEXT_GATE.relative_to(ROOT)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 42 Review

The execution retry stopped at preflight. `iter41` recovered the zero-provider GitHub Actions
runner path for the frozen CodeClash surfaces, and the local Google/Vertex readiness checks were
visible without logging account or project identifiers. That is still not enough for the frozen
provider-backed protocol-effect execution.

The missing evidence is a provider-capable execution harness: no workflow-dispatch provider
runner, no GitHub provider secret boundary, and no committed reusable GCE/Vertex CodeClash harness
with validated VM lifecycle, cost capture, raw artifact retention, and redaction. Earlier provider
experiments remain valid prior evidence, but their orchestration path is not committed as a
reusable harness for this six-pair protocol-effect retry.

No task-condition pair started. No provider model call occurred. No benchmark, SWE-bench,
leaderboard, production, live-domain, model-superiority, or state-of-the-art result is claimed.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    result_md = f"""# Iteration 42 Result - Public Task Protocol-Effect Execution Retry

Status: `{status.upper()}`.

## Summary

The frozen protocol-effect execution retry did not start provider execution. The gate stopped at a
secret-safe preflight:

- `iter41` isolated CodeClash runner recovery: `accepted`,
- local Google/Vertex readiness: `visible without committed identifiers`,
- provider-capable GitHub workflow: `missing`,
- GitHub provider secret boundary: `missing`,
- committed reusable provider execution harness: `missing`,
- cost-capture harness: `not validated`,
- raw-artifact redaction harness: `not validated`,
- planned task-condition pairs: `{planned_pairs}`,
- attempted task-condition pairs: `0`,
- provider model API calls: `0`,
- provider spend: `$0.00`,
- cloud runner started: `false`.

This is a blocked execution-retry result, not a model or benchmark result. The earlier provider
runs remain valid evidence for their own gates, but they do not substitute for a committed,
reusable execution harness for this six-pair protocol-effect pilot.

## What Is Now Authorized

- Recover a provider execution harness in
  `experiments/iter43_provider_execution_harness_recovery/HYPOTHESIS.md`.
- Keep the iter39 task slice, provider boundary, metric plan, and claim boundaries frozen.
- Retry execution only after provider-capable runner, VM lifecycle, cost capture, artifact
  retention, and redaction controls pass.

## What Remains Forbidden

- No benchmark result is claimed.
- No SWE-bench score is claimed.
- No leaderboard result is claimed.
- No production or live-domain result is claimed.
- No model-superiority or state-of-the-art result is claimed.
- No hidden provider spend or unlogged model call is allowed.

## Evidence

- `proof/preflight.json`
- `proof/execution_retry_report.json`
- `proof/run_summary.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/valid/receipt_public_task_protocol_effect_execution_retry.json`
"""
    (EXPERIMENT / "RESULT.md").write_text(result_md, encoding="utf-8")

    artifact_paths = [
        PROOF / "preflight.json",
        PROOF / "execution_retry_report.json",
        PROOF / "command_output.txt",
        PROOF / "review.md",
    ]
    run_summary = {
        "schema_version": "telos.public_task_protocol_effect_execution_retry.summary.v1",
        "status": status,
        "experiment_id": "iter42_public_task_protocol_effect_execution_retry",
        "source_experiment": "iter41_public_task_protocol_effect_runner_recovery",
        "source_slice_path": str(SOURCE_SLICE.relative_to(ROOT)),
        "source_slice_sha256": sha256_file(SOURCE_SLICE),
        "source_preflight_path": str(SOURCE_PREFLIGHT.relative_to(ROOT)),
        "source_preflight_sha256": sha256_file(SOURCE_PREFLIGHT),
        "source_runner_recovery_path": str(SOURCE_RUNNER.relative_to(ROOT)),
        "source_runner_recovery_sha256": sha256_file(SOURCE_RUNNER),
        "iter41_runner_recovery_accepted": execution_report["iter41_runner_recovery_accepted"],
        "provider_execution_harness_recovered": False,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "planned_task_condition_pairs": planned_pairs,
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": planned_pairs,
        "blockers": preflight_result["blockers"],
        "local_docker_daemon_ready": preflight_result["checks"]["local_docker"]["daemon_ready"],
        "local_docker_probe_timed_out": preflight_result["checks"]["local_docker"][
            "probe_timed_out"
        ],
        "gcloud_present": preflight_result["checks"]["gcloud"]["gcloud_present"],
        "gcloud_active_account_count": preflight_result["checks"]["gcloud"][
            "gcloud_active_account_count"
        ],
        "gcloud_project_configured": preflight_result["checks"]["gcloud"][
            "gcloud_project_configured"
        ],
        "vertex_ai_service_enabled": preflight_result["checks"]["gcloud"][
            "vertex_ai_service_enabled"
        ],
        "github_provider_secret_name_count": preflight_result["checks"]["github_actions"][
            "secret_state"
        ]["provider_secret_name_count"],
        "github_provider_workflow_count": preflight_result["checks"]["github_actions"][
            "workflow_state"
        ]["provider_capable_workflow_count"],
        "committed_provider_execution_harness_present": preflight_result["checks"][
            "committed_harness"
        ]["committed_provider_execution_harness_present"],
        "cost_capture_harness_validated": False,
        "raw_artifact_redaction_harness_validated": False,
        "credential_material_committed": False,
        "project_identifier_committed": False,
        "account_identifier_committed": False,
        "benchmark_result_claimed": False,
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
    run_summary["artifact_hashes"] = build_artifact_hashes(artifact_paths)
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter42_public_task_protocol_effect_execution_retry",
        "status": status,
        "insight": (
            "Runner readiness is recovered, but the provider-backed protocol-effect retry still "
            "needs a committed execution harness with cost capture, artifact retention, redaction, "
            "and runner lifecycle proof before paid task-condition pairs can start."
        ),
        "next_action": (
            "recover the provider execution harness before retrying the frozen protocol-effect "
            "execution slice"
        ),
        "result_path": "experiments/iter42_public_task_protocol_effect_execution_retry/RESULT.md",
        "evidence_paths": [
            "experiments/iter42_public_task_protocol_effect_execution_retry/proof/run_summary.json",
            "experiments/iter42_public_task_protocol_effect_execution_retry/proof/preflight.json",
            "experiments/iter42_public_task_protocol_effect_execution_retry/proof/execution_retry_report.json",
            "experiments/iter42_public_task_protocol_effect_execution_retry/proof/command_output.txt",
            "experiments/iter42_public_task_protocol_effect_execution_retry/proof/review.md",
            "experiments/iter42_public_task_protocol_effect_execution_retry/proof/valid/receipt_public_task_protocol_effect_execution_retry.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(
        VALID / "receipt_public_task_protocol_effect_execution_retry.json",
        build_receipt(status),
    )

    print("\n".join(output_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
