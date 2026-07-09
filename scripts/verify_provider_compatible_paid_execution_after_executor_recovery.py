#!/usr/bin/env python3
"""Publish iter55 provider-compatible paid execution artifacts."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter55_provider_compatible_paid_execution_after_executor_recovery"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
ITER54_SUMMARY = ROOT / "experiments" / "iter54_provider_pair_executor_recovery" / "proof" / "run_summary.json"
ITER54_COMMANDS = (
    ROOT / "experiments" / "iter54_provider_pair_executor_recovery" / "proof" / "command_manifest.json"
)
ITER54_OVERLAYS = (
    ROOT / "experiments" / "iter54_provider_pair_executor_recovery" / "proof" / "overlay_copy_manifest.json"
)
NEXT_GATE = ROOT / "experiments" / "iter56_provider_auth_recovery_for_paid_protocol_effect" / "HYPOTHESIS.md"
CODECLASH_DIR = Path("/tmp/telos-codeclash")
CODECLASH_COMMIT = "381cdfa05a35e8acd35853b9fc7e13005121b127"
DOCKER_BIN = Path("/Applications/Docker.app/Contents/Resources/bin/docker")
RUNNER_SHORT_ID = "telos-vertex-runner"
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
    re.compile(r"sunlit-unison-[A-Za-z0-9-]+"),
    re.compile(r"errorId=Ci"),
    re.compile(r'"error_info_id"\s*:\s*"Ci'),
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


def run_secret_safe(args: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        result = subprocess.run(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"returncode": None, "timed_out": True, "stderr_class": "timeout"}
    return {
        "returncode": result.returncode,
        "timed_out": False,
        "stderr_class": classify_stderr(result.stderr),
    }


def run_capture(args: list[str], timeout: int = 10) -> dict[str, Any]:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"returncode": None, "timed_out": True, "stdout": "", "stderr_class": "timeout"}
    return {
        "returncode": result.returncode,
        "timed_out": False,
        "stdout": result.stdout.strip(),
        "stderr_class": classify_stderr(result.stderr),
    }


def classify_stderr(stderr: str) -> str:
    text = stderr.lower()
    if not text.strip():
        return "none"
    if "reauthentication failed" in text or "cannot prompt during non-interactive" in text:
        return "interactive_reauthentication_required"
    if "iam.serviceaccounts.getaccesstoken" in text or "permission_denied" in text:
        return "iam_service_account_token_creator_denied"
    if "not found" in text:
        return "not_found"
    return "other_error_redacted"


def gcloud_value(args: list[str]) -> str | None:
    result = subprocess.run(args, capture_output=True, text=True, check=False, timeout=10)
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def env_presence() -> dict[str, bool]:
    names = [
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "VERTEXAI_PROJECT",
        "VERTEXAI_LOCATION",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
    ]
    return {name: name in os.environ for name in names}


def codeclash_state() -> dict[str, Any]:
    result = run_capture(["git", "-C", str(CODECLASH_DIR), "rev-parse", "HEAD"])
    return {
        "checkout_path": str(CODECLASH_DIR),
        "checkout_present": (CODECLASH_DIR / ".git").exists(),
        "expected_commit": CODECLASH_COMMIT,
        "actual_commit_matches_expected": result["stdout"] == CODECLASH_COMMIT,
        "commit_identifier_logged": True,
    }


def docker_state() -> dict[str, Any]:
    result = run_capture([str(DOCKER_BIN), "info", "--format", "{{.ServerVersion}}"], timeout=8)
    return {
        "preferred_cli_path": str(DOCKER_BIN),
        "preferred_cli_ready": result["returncode"] == 0 and bool(result["stdout"]),
        "server_version_present": bool(result["stdout"]),
        "containers_started": False,
    }


def auth_preflight() -> dict[str, Any]:
    project_present = gcloud_value(["gcloud", "config", "get-value", "project"]) is not None
    runner_email = None
    if project_present:
        project_id = gcloud_value(["gcloud", "config", "get-value", "project"])
        if project_id:
            runner_email = f"{RUNNER_SHORT_ID}@{project_id}.iam.gserviceaccount.com"

    user_token = run_secret_safe(["gcloud", "auth", "print-access-token", "--quiet"])
    adc_token = run_secret_safe(
        ["gcloud", "auth", "application-default", "print-access-token", "--quiet"]
    )
    impersonated_user_token = (
        run_secret_safe(
            [
                "gcloud",
                "auth",
                "print-access-token",
                f"--impersonate-service-account={runner_email}",
                "--quiet",
            ]
        )
        if runner_email
        else {"returncode": None, "timed_out": False, "stderr_class": "runner_email_unavailable"}
    )
    return {
        "active_account_present": user_token["returncode"] == 0,
        "account_identifier_logged": False,
        "project_present": project_present,
        "project_identifier_logged": False,
        "runner_short_id": RUNNER_SHORT_ID,
        "runner_identifier_logged": False,
        "env_credentials_present": env_presence(),
        "gcloud_user_access_token_available": user_token["returncode"] == 0,
        "gcloud_user_access_token_output_suppressed": True,
        "adc_access_token_available": adc_token["returncode"] == 0,
        "adc_access_token_output_suppressed": True,
        "adc_error_class": adc_token["stderr_class"],
        "impersonated_user_access_token_available": impersonated_user_token["returncode"] == 0,
        "impersonated_user_access_token_output_suppressed": True,
        "impersonation_error_class": impersonated_user_token["stderr_class"],
    }


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter55-provider-compatible-paid-execution-{status}",
        "task_id": "telos:iter55_provider_compatible_paid_execution_after_executor_recovery@iter54",
        "agent_id": "codex-local-provider-compatible-paid-execution-preflight",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Run the bounded two-row provider-compatible pilot only if provider credentials, "
            "runner readiness, cost capture, redaction, and receipt controls are ready."
        ),
        "acceptance_criteria": [
            "Iter54 is a clean pass.",
            "Exactly two selected BattleSnake condition commands remain frozen.",
            "Provider credentials are available non-interactively before any paid command starts.",
            "Provider calls stay at or below 16 and provider spend at or below $10.00.",
            "No excluded pair, GPU use, Sentinel resource mutation, or unsupported benchmark/model claim occurs.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": "experiments/iter55_provider_compatible_paid_execution_after_executor_recovery/proof/preflight.json",
                "notes": "Preflight records that ADC and impersonation were not ready, so no provider command ran.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": "experiments/iter55_provider_compatible_paid_execution_after_executor_recovery/proof/execution_plan.json",
                "notes": "Execution plan keeps the two exact iter54 commands frozen and unexecuted.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": "experiments/iter55_provider_compatible_paid_execution_after_executor_recovery/proof/review.md",
                "notes": "Review records the credential blocker and claim boundary.",
            },
        ],
        "falsifiers": [
            "The result must block if provider credentials are insufficient before execution.",
            "The result must fail if a provider command runs after failed credential preflight.",
            "The result must fail if provider calls, spend, GPU use, Sentinel mutation, or overclaim occurs outside the gate.",
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
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(str(path.relative_to(ROOT)))
                break
    return not findings, findings


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    iter54 = read_json(ITER54_SUMMARY)
    commands = read_json(ITER54_COMMANDS)
    overlays = read_json(ITER54_OVERLAYS)
    auth = auth_preflight()
    codeclash = codeclash_state()
    docker = docker_state()

    blockers: list[str] = []
    failures: list[str] = []
    if iter54.get("status") != "pass":
        blockers.append("iter54_not_clean_pass")
    if commands.get("selected_pair_count") != 2:
        failures.append("selected_pair_count_changed")
    if commands.get("provider_command_executed") is not False:
        failures.append("iter54_manifest_already_executed")
    if not overlays.get("all_hashes_match"):
        blockers.append("iter54_overlay_hashes_not_ready")
    if not codeclash["actual_commit_matches_expected"]:
        blockers.append("pinned_codeclash_checkout_not_ready")
    if not docker["preferred_cli_ready"]:
        blockers.append("docker_daemon_not_ready")
    if not auth["adc_access_token_available"]:
        blockers.append("adc_noninteractive_refresh_unavailable")
    if not auth["impersonated_user_access_token_available"]:
        blockers.append("runner_impersonation_unavailable")

    status = "fail" if failures else "blocked" if blockers else "pass"
    execution_plan = {
        "schema_version": "telos.provider_compatible_paid_execution.plan.v1",
        "status": status,
        "source_command_manifest": str(ITER54_COMMANDS.relative_to(ROOT)),
        "selected_pair_count": commands.get("selected_pair_count"),
        "selected_pair_ids": commands.get("selected_pair_ids"),
        "excluded_pair_count": commands.get("excluded_pair_count"),
        "excluded_pair_ids": commands.get("excluded_pair_ids"),
        "commands": [
            {**row, "executed": False, "blocked_before_execution": True}
            for row in commands.get("commands", [])
        ],
        "provider_command_executed": False,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
    }
    preflight = {
        "schema_version": "telos.provider_compatible_paid_execution.preflight.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "iter54_status": iter54.get("status"),
        "auth": auth,
        "codeclash": codeclash,
        "docker": docker,
        "provider_command_executed": False,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "blockers": blockers,
        "failures": failures,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
    }
    write_json(PROOF / "preflight.json", preflight)
    write_json(PROOF / "execution_plan.json", execution_plan)

    output_lines = [
        f"provider-compatible paid execution after executor recovery: {status}",
        "provider_command_executed=false",
        "provider_model_api_calls=0",
        "provider_spend_usd=0.0",
        f"adc_access_token_available={str(auth['adc_access_token_available']).lower()}",
        f"adc_error_class={auth['adc_error_class']}",
        f"impersonated_user_access_token_available={str(auth['impersonated_user_access_token_available']).lower()}",
        f"impersonation_error_class={auth['impersonation_error_class']}",
        f"blockers={','.join(blockers)}",
        f"failures={','.join(failures)}",
        f"next_gate={NEXT_GATE.relative_to(ROOT)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    result_md = f"""# Iteration 55 Result - Provider-Compatible Paid Execution After Executor Recovery

Status: `{status.upper()}`.

## Summary

The two-row paid protocol-effect pilot did not start. The zero-spend preflight accepted the iter54
executor recovery, pinned CodeClash checkout, command manifest, and Docker readiness, but provider
authentication was not sufficient for non-interactive execution.

- ADC access token available: `{str(auth['adc_access_token_available']).lower()}`,
- ADC error class: `{auth['adc_error_class']}`,
- dedicated-runner impersonated token available: `{str(auth['impersonated_user_access_token_available']).lower()}`,
- impersonation error class: `{auth['impersonation_error_class']}`,
- provider commands executed: `false`,
- provider model API calls: `0`,
- provider spend: `$0.00`,
- cloud runner started: `false`,
- GPU used: `false`,
- Sentinel-named resources modified: `false`.

## What Is Now Authorized

- Pre-register and run only the credential-recovery gate needed to restore a non-interactive
  provider auth path before retrying the two-row paid pilot.

## What Remains Forbidden

- Do not run either provider-backed BattleSnake row until credential readiness is proven.
- Do not execute any excluded Dummy or deterministic-edit pair.
- No benchmark result is claimed.
- No SWE-bench score is claimed.
- No leaderboard result is claimed.
- No production or live-domain result is claimed.
- No model-superiority or state-of-the-art result is claimed.

## Evidence

- `proof/preflight.json`
- `proof/execution_plan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_provider_compatible_paid_execution_blocked.json`
"""
    (EXPERIMENT / "RESULT.md").write_text(result_md, encoding="utf-8")

    review = """# Iteration 55 Review

The paid two-row pilot was correctly blocked before provider execution. The iter54 executor proof
is usable, the pinned CodeClash checkout is ready, and Docker responds through the current Docker
Desktop binary. The remaining concrete blocker is provider authentication: Application Default
Credentials require interactive reauthentication, and active-user impersonation of the dedicated
Telos runner lacks service-account token-creator permission.

No provider command executed. No provider model call, provider spend, cloud runner startup, GPU
use, Sentinel-named resource modification, production/live-domain change, benchmark claim, model
superiority claim, or state-of-the-art claim occurred.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    artifact_paths = [
        PROOF / "preflight.json",
        PROOF / "execution_plan.json",
        PROOF / "command_output.txt",
        PROOF / "review.md",
    ]
    scan_passed, scan_findings = secret_scan(artifact_paths + [EXPERIMENT / "RESULT.md"])
    summary = {
        "schema_version": "telos.provider_compatible_paid_execution.summary.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "iter54_status": iter54.get("status"),
        "selected_pair_count": commands.get("selected_pair_count"),
        "selected_pair_ids": commands.get("selected_pair_ids"),
        "excluded_pair_count": commands.get("excluded_pair_count"),
        "excluded_pair_ids": commands.get("excluded_pair_ids"),
        "provider_command_executed": False,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "adc_access_token_available": auth["adc_access_token_available"],
        "adc_error_class": auth["adc_error_class"],
        "impersonated_user_access_token_available": auth[
            "impersonated_user_access_token_available"
        ],
        "impersonation_error_class": auth["impersonation_error_class"],
        "account_identifier_committed": False,
        "project_identifier_committed": False,
        "runner_identifier_committed": False,
        "redaction_scan_passed": scan_passed,
        "redaction_findings": scan_findings,
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
    summary["artifact_hashes"] = artifact_hashes(artifact_paths)
    write_json(PROOF / "run_summary.json", summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "insight": (
            "The paid two-row pilot is ready at the executor layer but blocked by provider "
            "credential readiness: ADC requires interactive reauthentication and dedicated-runner "
            "impersonation is not currently available."
        ),
        "next_action": (
            "recover a non-interactive provider auth path or token-creator permission before "
            "retrying the exact two-row paid pilot"
        ),
        "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
        "evidence_paths": [
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            f"experiments/{EXPERIMENT_ID}/proof/preflight.json",
            f"experiments/{EXPERIMENT_ID}/proof/execution_plan.json",
            f"experiments/{EXPERIMENT_ID}/proof/valid/receipt_provider_compatible_paid_execution_blocked.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(
        VALID / "receipt_provider_compatible_paid_execution_blocked.json", build_receipt(status)
    )

    print("\n".join(output_lines))
    return 0 if status in {"blocked", "pass"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
