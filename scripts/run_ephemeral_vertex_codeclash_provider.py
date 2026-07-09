#!/usr/bin/env python3
"""Reusable secret-safe harness for Telos Vertex/CodeClash provider execution.

This module is intentionally split from any full protocol-effect run.  It can
prove provider-runner readiness and artifact controls without executing the
frozen baseline/Telos task-condition pairs.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CODECLASH_COMMIT = "381cdfa05a35e8acd35853b9fc7e13005121b127"
RUNNER_SHORT_ID = "telos-vertex-runner"
MODEL_ID = "gemini-3.1-pro-preview-customtools"
REGION = "global"
FROZEN_CONFIGS = [
    "configs/test/dummy.yaml",
    "configs/test/battlesnake_pvp_test.yaml",
    "configs/test/telos_battlesnake_edit_test.yaml",
]
REQUIRED_SERVICES = [
    "aiplatform.googleapis.com",
    "compute.googleapis.com",
    "iam.googleapis.com",
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


@dataclass(frozen=True)
class CommandResult:
    returncode: int | None
    timed_out: bool
    stdout: str
    stderr: str


def run(args: list[str], timeout: int = 30) -> CommandResult:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return CommandResult(returncode=None, timed_out=True, stdout="", stderr="")
    return CommandResult(
        returncode=result.returncode,
        timed_out=False,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def nonempty_count(text: str) -> int:
    return len([line for line in text.splitlines() if line.strip()])


def gcloud_readiness() -> dict[str, Any]:
    state: dict[str, Any] = {
        "gcloud_present": shutil.which("gcloud") is not None,
        "gcloud_version_ready": False,
        "active_account_count": 0,
        "project_configured": False,
        "services_enabled": {service: False for service in REQUIRED_SERVICES},
        "dedicated_runner_short_id": RUNNER_SHORT_ID,
        "dedicated_runner_visible_count": 0,
        "running_vm_count": 0,
        "running_telos_vm_count": 0,
        "running_sentinel_named_vm_count": 0,
        "account_identifier_logged": False,
        "project_identifier_logged": False,
        "service_account_identifier_logged": False,
    }
    if not state["gcloud_present"]:
        return state

    version = run(["gcloud", "--version"], timeout=10)
    state["gcloud_version_ready"] = version.returncode == 0

    auth = run(
        [
            "gcloud",
            "auth",
            "list",
            "--filter=status:ACTIVE",
            "--format=value(account)",
        ],
        timeout=15,
    )
    if auth.returncode == 0:
        state["active_account_count"] = nonempty_count(auth.stdout)

    project = run(["gcloud", "config", "get-value", "project"], timeout=10)
    project_value = project.stdout.strip()
    state["project_configured"] = (
        project.returncode == 0 and bool(project_value) and project_value != "(unset)"
    )
    if not state["project_configured"]:
        return state

    for service in REQUIRED_SERVICES:
        service_result = run(
            [
                "gcloud",
                "services",
                "list",
                "--enabled",
                f"--filter=name:{service}",
                "--format=value(name)",
            ],
            timeout=20,
        )
        state["services_enabled"][service] = (
            service_result.returncode == 0 and service in service_result.stdout
        )

    runner = run(
        [
            "gcloud",
            "iam",
            "service-accounts",
            "list",
            f"--filter=email~^{RUNNER_SHORT_ID}@",
            "--format=value(email)",
        ],
        timeout=20,
    )
    if runner.returncode == 0:
        state["dedicated_runner_visible_count"] = nonempty_count(runner.stdout)

    running = run(
        [
            "gcloud",
            "compute",
            "instances",
            "list",
            "--filter=status:RUNNING",
            "--format=value(name)",
        ],
        timeout=20,
    )
    if running.returncode == 0:
        state["running_vm_count"] = nonempty_count(running.stdout)

    telos = run(
        [
            "gcloud",
            "compute",
            "instances",
            "list",
            "--filter=name~^telos-.* AND status:RUNNING",
            "--format=value(name)",
        ],
        timeout=20,
    )
    if telos.returncode == 0:
        state["running_telos_vm_count"] = nonempty_count(telos.stdout)

    sentinel = run(
        [
            "gcloud",
            "compute",
            "instances",
            "list",
            "--filter=name~^sentinel-.* AND status:RUNNING",
            "--format=value(name)",
        ],
        timeout=20,
    )
    if sentinel.returncode == 0:
        state["running_sentinel_named_vm_count"] = nonempty_count(sentinel.stdout)

    return state


def runner_service_account_email() -> str | None:
    result = run(
        [
            "gcloud",
            "iam",
            "service-accounts",
            "list",
            f"--filter=email~^{RUNNER_SHORT_ID}@",
            "--format=value(email)",
        ],
        timeout=20,
    )
    if result.returncode != 0:
        return None
    values = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if len(values) != 1:
        return None
    return values[0]


def scan_text_tree(root: Path) -> dict[str, Any]:
    hits: list[str] = []
    checked = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix in {".gz", ".zip", ".tar"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        checked += 1
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                hits.append(str(path.relative_to(ROOT)))
                break
    return {
        "checked_text_file_count": checked,
        "secret_or_identifier_hits": hits,
        "secret_scan_passed": not hits and checked > 0,
    }


def prior_provider_artifact_summary(prior_proof: Path) -> dict[str, Any]:
    raw_summary_path = prior_proof / "raw_summary.json"
    run_summary_path = prior_proof / "run_summary.json"
    preflight_path = prior_proof / "preflight.json"
    raw_summary = json.loads(raw_summary_path.read_text(encoding="utf-8"))
    run_summary = json.loads(run_summary_path.read_text(encoding="utf-8"))
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    p1_model_stats = raw_summary.get("p1_model_stats", {})
    api_calls = p1_model_stats.get("api_calls")
    cost = p1_model_stats.get("instance_cost")
    trajectory_paths = raw_summary.get("p1_trajectory_paths", [])
    change_paths = raw_summary.get("p1_change_files", [])
    required_paths = [raw_summary_path, run_summary_path, preflight_path]
    required_paths.extend(prior_proof / path for path in trajectory_paths)
    required_paths.extend(prior_proof / path for path in change_paths)
    existing_required = [path for path in required_paths if path.exists()]
    return {
        "prior_proof_path": str(prior_proof.relative_to(ROOT)),
        "preflight_status": preflight.get("status"),
        "preflight_http_status": preflight.get("http_status"),
        "run_exit_code": raw_summary.get("run_exit_code"),
        "model_api_calls_reported": api_calls,
        "model_cost_reported_usd": cost,
        "p1_exit_status": raw_summary.get("p1_exit_status"),
        "trajectory_path_count": len(trajectory_paths),
        "change_path_count": len(change_paths),
        "required_artifact_count": len(required_paths),
        "required_artifact_existing_count": len(existing_required),
        "cost_capture_parser_validated": (
            isinstance(api_calls, int)
            and api_calls > 0
            and isinstance(cost, int | float)
            and cost >= 0
        ),
        "raw_artifact_retention_validated": len(required_paths) == len(existing_required),
        "credential_material_committed": run_summary.get("credential_material_committed"),
        "project_identifier_committed": run_summary.get("project_identifier_committed"),
        "account_identifier_committed": run_summary.get("account_identifier_committed"),
        "provider_private_fields_redacted": run_summary.get("provider_private_fields_redacted"),
        "raw_binary_round_archive_committed": run_summary.get("raw_binary_round_archive_committed"),
    }


def provider_execution_plan() -> dict[str, Any]:
    return {
        "schema_version": "telos.provider_execution_harness.plan.v1",
        "provider": "Google Vertex AI",
        "model_id": MODEL_ID,
        "region": REGION,
        "runner": "ephemeral_gce_vm_dedicated_service_account",
        "runner_short_id": RUNNER_SHORT_ID,
        "codeclash_commit": CODECLASH_COMMIT,
        "frozen_configs": FROZEN_CONFIGS,
        "full_protocol_effect_execution_enabled": False,
        "requires_future_gate_to_execute_task_condition_pairs": True,
        "captures": [
            "preflight_response",
            "run_exit_code",
            "raw_codeclash_logs",
            "agent_trajectory",
            "changes_json",
            "api_call_count",
            "model_cost_usd",
            "artifact_hashes",
            "redaction_scan",
            "runner_lifecycle",
        ],
    }


def lifecycle_probe(zone: str, execute: bool) -> dict[str, Any]:
    probe: dict[str, Any] = {
        "schema_version": "telos.provider_execution_harness.lifecycle_probe.v1",
        "mode": "execute" if execute else "dry_run",
        "zone_logged": False,
        "vm_identifier_logged": False,
        "service_account_identifier_logged": False,
        "no_gpu_requested": True,
        "model_call_made": False,
        "full_task_condition_pair_executed": False,
        "vm_created": False,
        "serial_marker_seen": False,
        "vm_deleted": False,
        "delete_attempted": False,
        "running_telos_vm_count_before": None,
        "running_telos_vm_count_after": None,
        "cloud_runner_estimated_spend_bound_usd": 0.0 if not execute else 0.10,
    }
    readiness = gcloud_readiness()
    probe["running_telos_vm_count_before"] = readiness["running_telos_vm_count"]
    if not execute:
        probe["vm_deleted"] = True
        probe["running_telos_vm_count_after"] = readiness["running_telos_vm_count"]
        return probe

    service_account = runner_service_account_email()
    if service_account is None:
        probe["blocked_reason"] = "dedicated_runner_service_account_not_unique"
        probe["running_telos_vm_count_after"] = readiness["running_telos_vm_count"]
        return probe

    marker = "TELOS_ITER43_LIFECYCLE_READY"
    instance_name = f"telos-iter43-harness-{secrets.token_hex(4)}"
    startup_script = f"#!/bin/sh\necho {marker}\n"
    create_args = [
        "gcloud",
        "compute",
        "instances",
        "create",
        instance_name,
        "--quiet",
        f"--zone={zone}",
        "--machine-type=e2-micro",
        "--image-family=ubuntu-2404-lts-amd64",
        "--image-project=ubuntu-os-cloud",
        f"--service-account={service_account}",
        "--scopes=https://www.googleapis.com/auth/cloud-platform",
        "--no-address",
        f"--metadata=startup-script={startup_script}",
    ]
    maybe_created = False
    try:
        created = run(create_args, timeout=180)
        probe["vm_created"] = created.returncode == 0
        probe["create_returncode_zero"] = created.returncode == 0
        probe["create_timed_out"] = created.timed_out
        maybe_created = created.returncode == 0 or created.timed_out
        if probe["vm_created"]:
            for _ in range(12):
                serial = run(
                    [
                        "gcloud",
                        "compute",
                        "instances",
                        "get-serial-port-output",
                        instance_name,
                        f"--zone={zone}",
                    ],
                    timeout=30,
                )
                if serial.returncode == 0 and marker in serial.stdout:
                    probe["serial_marker_seen"] = True
                    break
                time.sleep(5)
    finally:
        if maybe_created:
            probe["delete_attempted"] = True
            deleted = run(
                [
                    "gcloud",
                    "compute",
                    "instances",
                    "delete",
                    instance_name,
                    "--quiet",
                    f"--zone={zone}",
                ],
                timeout=180,
            )
            probe["vm_deleted"] = deleted.returncode == 0
            probe["delete_returncode_zero"] = deleted.returncode == 0
            probe["delete_timed_out"] = deleted.timed_out

    after = gcloud_readiness()
    probe["running_telos_vm_count_after"] = after["running_telos_vm_count"]
    return probe


def build_harness_report(prior_proof: Path, execute_lifecycle_probe: bool, zone: str) -> dict[str, Any]:
    readiness = gcloud_readiness()
    prior_summary = prior_provider_artifact_summary(prior_proof)
    redaction_scan = scan_text_tree(prior_proof)
    lifecycle = lifecycle_probe(zone=zone, execute=execute_lifecycle_probe)
    return {
        "schema_version": "telos.provider_execution_harness.report.v1",
        "harness_path": "scripts/run_ephemeral_vertex_codeclash_provider.py",
        "provider_execution_plan": provider_execution_plan(),
        "gcloud_readiness": readiness,
        "prior_provider_artifact_summary": prior_summary,
        "redaction_scan": redaction_scan,
        "lifecycle_probe": lifecycle,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "full_task_condition_pairs_executed": 0,
        "credential_material_logged": False,
        "project_identifier_logged": False,
        "account_identifier_logged": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prior-proof",
        type=Path,
        default=ROOT / "experiments" / "iter21_opponent_collision_control" / "proof",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--zone", default="us-central1-a")
    parser.add_argument("--execute-lifecycle-probe", action="store_true")
    args = parser.parse_args()

    report = build_harness_report(
        prior_proof=args.prior_proof,
        execute_lifecycle_probe=args.execute_lifecycle_probe,
        zone=args.zone,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "provider harness report: "
        f"mode={report['lifecycle_probe']['mode']} "
        f"model_calls={report['provider_model_api_calls']} "
        f"task_pairs={report['full_task_condition_pairs_executed']} "
        f"vm_created={str(report['lifecycle_probe']['vm_created']).lower()} "
        f"vm_deleted={str(report['lifecycle_probe']['vm_deleted']).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
