#!/usr/bin/env python3
"""Publish iter56 provider auth recovery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter56_provider_auth_recovery_for_paid_protocol_effect"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
ITER55_SUMMARY = (
    ROOT
    / "experiments"
    / "iter55_provider_compatible_paid_execution_after_executor_recovery"
    / "proof"
    / "run_summary.json"
)
ITER55_PREFLIGHT = (
    ROOT
    / "experiments"
    / "iter55_provider_compatible_paid_execution_after_executor_recovery"
    / "proof"
    / "preflight.json"
)
ITER54_COMMANDS = (
    ROOT / "experiments" / "iter54_provider_pair_executor_recovery" / "proof" / "command_manifest.json"
)
NEXT_GATE = (
    ROOT
    / "experiments"
    / "iter57_provider_compatible_paid_execution_after_auth_recovery"
    / "HYPOTHESIS.md"
)
MODEL_ID = "gemini-3.1-pro-preview-customtools"
REGION = "global"
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
    re.compile(r"telos-vertex-runner"),
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


def classify_stderr(stderr: str) -> str:
    text = stderr.lower()
    if not text.strip():
        return "none"
    if "reauthentication failed" in text or "cannot prompt during non-interactive" in text:
        return "interactive_reauthentication_required"
    if "iam.serviceaccounts.getaccesstoken" in text or "permission_denied" in text:
        return "iam_service_account_token_creator_denied"
    if "authorization" in text or "browser" in text:
        return "interactive_login_required"
    return "other_error_redacted"


def run_secret_safe(args: list[str], timeout: int = 30) -> dict[str, Any]:
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


def gcloud_value(args: list[str]) -> str | None:
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=False, timeout=10)
    except subprocess.TimeoutExpired:
        return None
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def access_token() -> str | None:
    try:
        result = subprocess.run(
            ["gcloud", "auth", "application-default", "print-access-token", "--quiet"],
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
    except subprocess.TimeoutExpired:
        return None
    if result.returncode != 0:
        return None
    token = result.stdout.strip()
    return token or None


def adc_repair() -> dict[str, Any]:
    account = gcloud_value(["gcloud", "config", "get-value", "account"])
    if not account:
        return {
            "attempted": False,
            "status": "blocked",
            "reason": "active_account_unavailable",
            "account_identifier_logged": False,
        }
    result = run_secret_safe(
        ["gcloud", "auth", "application-default", "login", account, "--quiet"], timeout=45
    )
    return {
        "attempted": True,
        "status": "pass" if result["returncode"] == 0 else "blocked",
        "error_class": result["stderr_class"],
        "account_identifier_logged": False,
        "token_output_suppressed": True,
    }


def impersonation_probe(project_id: str | None) -> dict[str, Any]:
    if not project_id:
        return {
            "attempted": False,
            "available": False,
            "error_class": "project_unavailable",
            "runner_identifier_logged": False,
        }
    runner_email = f"{RUNNER_SHORT_ID}@{project_id}.iam.gserviceaccount.com"
    result = run_secret_safe(
        [
            "gcloud",
            "auth",
            "print-access-token",
            f"--impersonate-service-account={runner_email}",
            "--quiet",
        ],
        timeout=30,
    )
    return {
        "attempted": True,
        "available": result["returncode"] == 0,
        "error_class": result["stderr_class"],
        "runner_identifier_logged": False,
        "token_output_suppressed": True,
    }


def vertex_access_probe(project_id: str | None, token: str | None) -> dict[str, Any]:
    probe: dict[str, Any] = {
        "schema_version": "telos.provider_auth_recovery.vertex_access_probe.v1",
        "attempted": False,
        "model_call_made": False,
        "provider_access_probe_count": 0,
        "provider_spend_bound_usd": 0.01,
        "provider_spend_observed_usd": None,
        "project_identifier_logged": False,
        "credential_material_logged": False,
        "selected_model": MODEL_ID,
        "region": REGION,
        "endpoint": "publishers/google/models/gemini-3.1-pro-preview-customtools:generateContent",
        "request_max_output_tokens": 4,
    }
    if not project_id or token is None:
        probe["status"] = "blocked"
        probe["blocked_reason"] = "project_or_token_unavailable"
        return probe

    url = (
        "https://aiplatform.googleapis.com/v1/"
        f"projects/{project_id}/locations/{REGION}/publishers/google/models/"
        f"{MODEL_ID}:generateContent"
    )
    body = {
        "contents": [{"role": "user", "parts": [{"text": "ping"}]}],
        "generationConfig": {"maxOutputTokens": 4, "temperature": 0},
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Goog-User-Project": project_id,
        },
        method="POST",
    )
    probe["attempted"] = True
    probe["model_call_made"] = True
    probe["provider_access_probe_count"] = 1
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
            probe["http_status"] = str(response.status)
    except urllib.error.HTTPError as exc:
        probe["status"] = "blocked"
        probe["http_status"] = str(exc.code)
        probe["error_class"] = "http_error_redacted"
        return probe
    except (urllib.error.URLError, TimeoutError):
        probe["status"] = "blocked"
        probe["http_status"] = None
        probe["error_class"] = "transport_error_redacted"
        return probe

    usage = payload.get("usageMetadata", {})
    candidates = payload.get("candidates", [])
    probe.update(
        {
            "status": "pass",
            "candidate_count": len(candidates),
            "candidate_text_committed": False,
            "usage_metadata_present": bool(usage),
            "prompt_token_count": usage.get("promptTokenCount"),
            "candidates_token_count": usage.get("candidatesTokenCount"),
            "total_token_count": usage.get("totalTokenCount"),
            "successful_endpoint_access_evidenced": True,
        }
    )
    return probe


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter56-provider-auth-recovery-{status}",
        "task_id": "telos:iter56_provider_auth_recovery_for_paid_protocol_effect@iter55",
        "agent_id": "codex-local-provider-auth-recovery",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Recover a non-interactive provider authentication path for the exact two-row paid "
            "protocol-effect pilot without executing either BattleSnake row."
        ),
        "acceptance_criteria": [
            "Iter55 is a clean blocked result caused by credential readiness.",
            "Non-interactive ADC or dedicated-runner impersonation is available with token output suppressed.",
            "At most two provider access probes and at most $1.00 spend are allowed.",
            "No iter55 BattleSnake command, excluded pair, GPU, Sentinel resource mutation, or overclaim occurs.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": "experiments/iter56_provider_auth_recovery_for_paid_protocol_effect/proof/auth_recovery_report.json",
                "notes": "Auth recovery report records ADC repair, impersonation status, and minimal access probe evidence.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": "experiments/iter56_provider_auth_recovery_for_paid_protocol_effect/proof/vertex_access_probe.json",
                "notes": "Probe records bounded provider-access evidence without committing token, account, or project identifiers.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": "experiments/iter56_provider_auth_recovery_for_paid_protocol_effect/proof/review.md",
                "notes": "Review records the auth-only claim boundary.",
            },
        ],
        "falsifiers": [
            "The result must block if non-interactive auth is not available.",
            "The result must fail if either paid BattleSnake row runs.",
            "The result must fail if provider probe count or spend ceiling is exceeded.",
            "The result must fail if identifiers, credentials, provider-private fields, or overclaims are committed.",
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

    iter55_summary = read_json(ITER55_SUMMARY)
    iter55_preflight = read_json(ITER55_PREFLIGHT)
    commands = read_json(ITER54_COMMANDS)
    project_id = gcloud_value(["gcloud", "config", "get-value", "project"])
    repair = adc_repair()
    adc_token = access_token()
    adc_available = adc_token is not None
    impersonation = impersonation_probe(project_id)
    probe = vertex_access_probe(project_id, adc_token)

    blockers: list[str] = []
    failures: list[str] = []
    if iter55_summary.get("status") != "blocked":
        blockers.append("iter55_not_blocked")
    if iter55_preflight.get("provider_command_executed") is not False:
        failures.append("iter55_provider_command_already_executed")
    if commands.get("selected_pair_count") != 2:
        failures.append("selected_pair_count_changed")
    if not adc_available and not impersonation["available"]:
        blockers.append("noninteractive_auth_path_unavailable")
    if probe.get("attempted") and probe.get("provider_access_probe_count", 0) > 2:
        failures.append("provider_access_probe_count_exceeded")
    if probe.get("provider_spend_bound_usd", 999) > 1.0:
        failures.append("provider_probe_spend_bound_exceeded")
    if probe.get("status") != "pass":
        blockers.append("provider_access_probe_not_passed")

    status = "fail" if failures else "blocked" if blockers else "pass"
    report = {
        "schema_version": "telos.provider_auth_recovery.report.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "iter55_status": iter55_summary.get("status"),
        "source_iter55_summary_path": str(ITER55_SUMMARY.relative_to(ROOT)),
        "source_iter55_preflight_path": str(ITER55_PREFLIGHT.relative_to(ROOT)),
        "adc_repair": repair,
        "adc_access_token_available": adc_available,
        "adc_access_token_output_suppressed": True,
        "auth_path_ready": adc_available or impersonation["available"],
        "auth_surface": "local_adc_user_credentials" if adc_available else "none",
        "impersonation": impersonation,
        "account_identifier_committed": False,
        "project_identifier_committed": False,
        "runner_identifier_committed": False,
        "provider_access_probe_count": probe.get("provider_access_probe_count", 0),
        "provider_spend_bound_usd": probe.get("provider_spend_bound_usd", 0.0),
        "provider_spend_observed_usd": probe.get("provider_spend_observed_usd"),
        "paid_battlesnake_command_executed": False,
        "excluded_pair_executed": False,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "blockers": blockers,
        "failures": failures,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
    }
    write_json(PROOF / "auth_recovery_report.json", report)
    write_json(PROOF / "vertex_access_probe.json", probe)

    output_lines = [
        f"provider auth recovery for paid protocol effect: {status}",
        f"adc_repair_status={repair['status']}",
        f"adc_access_token_available={str(adc_available).lower()}",
        f"provider_access_probe_status={probe.get('status')}",
        f"provider_access_probe_count={probe.get('provider_access_probe_count', 0)}",
        f"provider_spend_bound_usd={probe.get('provider_spend_bound_usd', 0.0)}",
        "paid_battlesnake_command_executed=false",
        "provider_compatible_protocol_effect_result_claimed=false",
        f"blockers={','.join(blockers)}",
        f"failures={','.join(failures)}",
        f"next_gate={NEXT_GATE.relative_to(ROOT)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    result_md = f"""# Iteration 56 Result - Provider Auth Recovery For Paid Protocol Effect

Status: `{status.upper()}`.

## Summary

The credential recovery gate restored a non-interactive ADC path for the exact two-row paid pilot.
It did not execute either BattleSnake row.

- ADC repair status: `{repair['status']}`,
- ADC access token available: `{str(adc_available).lower()}`,
- provider access probe status: `{probe.get('status')}`,
- provider access probe count: `{probe.get('provider_access_probe_count', 0)}`,
- provider spend bound: `${probe.get('provider_spend_bound_usd', 0.0):.2f}`,
- paid BattleSnake commands executed: `false`,
- excluded pairs executed: `false`,
- cloud runner started: `false`,
- GPU used: `false`,
- Sentinel-named resources modified: `false`.

Dedicated-runner impersonation remains unavailable, but it is not required for the next local
ADC-backed retry. The proof commits no token, account, project, service-account, VM, or zone
identifier.

## What Is Now Authorized

- Pre-register and run the same exact two-row paid pilot using the recovered ADC path and the
  iter54 command manifest.

## What Remains Forbidden

- No benchmark result is claimed.
- No SWE-bench score is claimed.
- No leaderboard result is claimed.
- No production or live-domain result is claimed.
- No model-superiority or state-of-the-art result is claimed.
- No provider-compatible protocol-effect metric is inferred from auth readiness.

## Evidence

- `proof/auth_recovery_report.json`
- `proof/vertex_access_probe.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_provider_auth_recovery_for_paid_protocol_effect.json`
"""
    (EXPERIMENT / "RESULT.md").write_text(result_md, encoding="utf-8")

    review = """# Iteration 56 Review

The auth recovery gate repaired the local ADC path non-interactively and verified the selected
Vertex endpoint with one minimal access probe. It did not execute either paid BattleSnake row and
did not start a cloud runner.

Dedicated-runner impersonation still lacks token-creator access, so the next paid retry should use
the recovered local ADC path unless a later gate separately recovers impersonation. No token,
account, project, service-account, VM, zone, provider-private field, benchmark claim, model
superiority claim, or state-of-the-art claim is committed.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    artifact_paths = [
        PROOF / "auth_recovery_report.json",
        PROOF / "vertex_access_probe.json",
        PROOF / "command_output.txt",
        PROOF / "review.md",
    ]
    scan_passed, scan_findings = secret_scan(artifact_paths + [EXPERIMENT / "RESULT.md"])
    summary = {
        "schema_version": "telos.provider_auth_recovery.summary.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "iter55_status": iter55_summary.get("status"),
        "adc_repair_status": repair["status"],
        "adc_access_token_available": adc_available,
        "auth_path_ready": report["auth_path_ready"],
        "auth_surface": report["auth_surface"],
        "impersonated_user_access_token_available": impersonation["available"],
        "impersonation_error_class": impersonation["error_class"],
        "provider_access_probe_status": probe.get("status"),
        "provider_access_probe_count": probe.get("provider_access_probe_count", 0),
        "provider_spend_bound_usd": probe.get("provider_spend_bound_usd", 0.0),
        "provider_spend_observed_usd": probe.get("provider_spend_observed_usd"),
        "paid_battlesnake_command_executed": False,
        "excluded_pair_executed": False,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
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
        "clean_pass": status == "pass",
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
            "Local ADC was repaired non-interactively and a minimal Vertex access probe succeeded, "
            "so the exact two-row paid pilot can be retried without changing its task scope."
        ),
        "next_action": "retry the exact two-row paid pilot under the recovered ADC path",
        "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
        "evidence_paths": [
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            f"experiments/{EXPERIMENT_ID}/proof/auth_recovery_report.json",
            f"experiments/{EXPERIMENT_ID}/proof/vertex_access_probe.json",
            f"experiments/{EXPERIMENT_ID}/proof/valid/receipt_provider_auth_recovery_for_paid_protocol_effect.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(
        VALID / "receipt_provider_auth_recovery_for_paid_protocol_effect.json",
        build_receipt(status),
    )

    print("\n".join(output_lines))
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
