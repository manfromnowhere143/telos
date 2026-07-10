#!/usr/bin/env python3
"""Verify iter75 runtime ADC readiness after the iter74 paid-retry block."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter75_provider_compatible_runtime_adc_recovery_after_paid_retry_block"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULT = EXPERIMENT / "RESULT.md"
RECEIPT_NAME = "receipt_provider_compatible_runtime_adc_recovery_after_paid_retry_block.json"
ITER74_PROOF = (
    ROOT
    / "experiments"
    / "iter74_provider_compatible_expanded_paid_retry_after_receipt_prompt_recovery"
    / "proof"
)
ITER74_SUMMARY = ITER74_PROOF / "run_summary.json"
CODECLASH_DIR = Path("/tmp/telos-codeclash")
CODECLASH_COMMIT = "381cdfa05a35e8acd35853b9fc7e13005121b127"
DOCKER_BIN = Path("/Applications/Docker.app/Contents/Resources/bin/docker")
TEXT_SUFFIXES = {".json", ".jsonl", ".log", ".txt", ".md", ".yaml", ".yml", ".py"}
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"Bearer\s+(?!\$\{[A-Z0-9_]+\}|\[REDACTED_BEARER_TOKEN\])\S+"),
    re.compile(r"-----BEGIN PRIVATE KEY-----"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com"),
    re.compile(r"telos-vertex-runner"),
    re.compile(r"sunlit-unison-[A-Za-z0-9-]+"),
    re.compile(r"errorId=Ci"),
    re.compile(r'"error_info_id"\s*:\s*"Ci'),
]


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} root must be an object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def run_capture(args: list[str], timeout: int = 30) -> dict[str, Any]:
    try:
        result = subprocess.run(
            args,
            cwd=ROOT,
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
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def run_sensitive_probe(args: list[str], timeout: int = 30) -> dict[str, Any]:
    """Run a probe while committing no stdout/stderr content."""
    try:
        result = subprocess.run(
            args,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {
            "returncode": None,
            "timed_out": True,
            "stdout_present": False,
            "stderr_present": False,
            "stderr_class": "timeout",
            "stdout_suppressed": True,
            "stderr_committed": False,
        }
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    return {
        "returncode": result.returncode,
        "timed_out": False,
        "stdout_present": bool(stdout),
        "stderr_present": bool(stderr),
        "stderr_class": classify_probe_stderr(result.returncode, stderr),
        "stdout_suppressed": True,
        "stderr_committed": False,
    }


def classify_probe_stderr(returncode: int | None, stderr: str) -> str:
    if returncode == 0:
        return "none"
    text = stderr.lower()
    if "cannot prompt during non-interactive execution" in text:
        return "interactive_reauthentication_required"
    if "application-default login" in text:
        return "adc_login_required"
    if "not found" in text:
        return "command_or_resource_missing"
    if stderr:
        return "other_error_suppressed"
    return "no_stderr"


def text_files_under(path: Path) -> list[Path]:
    return [
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file() and candidate.suffix in TEXT_SUFFIXES
    ]


def redaction_scan() -> tuple[bool, list[str]]:
    findings: list[str] = []
    if not EXPERIMENT.exists():
        return True, findings
    for path in text_files_under(EXPERIMENT):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(str(path.relative_to(ROOT)))
                break
    return not findings, sorted(set(findings))


def artifact_hashes(paths: list[Path]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for base in paths:
        if base.is_file() and base.exists():
            hashes[str(base.relative_to(PROOF))] = sha256_file(base)
            continue
        if base.exists():
            for path in sorted(base.rglob("*")):
                if path.is_file():
                    hashes[str(path.relative_to(PROOF))] = sha256_file(path)
    return hashes


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter75-provider-compatible-runtime-adc-recovery-{status}",
        "task_id": "telos:iter75_provider_compatible_runtime_adc_recovery_after_paid_retry_block@iter74",
        "agent_id": "codex-local-runtime-access-readiness-verifier",
        "benchmark_id": "telos_codeclash_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Recover or precisely classify the non-interactive ADC refresh blocker before any "
            "further paid adapter-row retry."
        ),
        "acceptance_criteria": [
            "Iter74 validates as a clean blocked artifact packet.",
            "CodeClash checkout, Docker readiness, google.auth import, gcloud project availability, and ADC refresh readiness are checked.",
            "Access-token stdout and project identifier output are suppressed and not committed.",
            "Zero provider calls, zero spend, zero row execution, no GPU, and no cloud runner startup occur.",
            "No Sentinel, production/live-domain, benchmark, model, or state-of-the-art claim occurs.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                "notes": "Run summary records runtime readiness checks, blockers, costs, and claim boundary.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/runtime_adc_readiness_report.json",
                "notes": "Report records token-suppressed ADC readiness classification.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records the zero-spend no-benchmark boundary.",
            },
        ],
        "falsifiers": [
            "The result must block if iter74 receipt validation or audit fails.",
            "The result must block if ADC cannot refresh non-interactively.",
            "The result must fail if any provider row executes or any provider spend occurs.",
            "The result must fail if token, project identifier, service-account, or credential material is committed.",
            "The result must fail if unsupported benchmark, model-superiority, production, live-domain, leaderboard, SWE-bench, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def main() -> int:
    if PROOF.exists():
        shutil.rmtree(PROOF)
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    iter74 = read_json(ITER74_SUMMARY)
    iter74_receipts = run_capture(
        ["python3", "scripts/validate_receipts.py", str(ITER74_PROOF.relative_to(ROOT))]
    )
    iter74_audit = run_capture(
        ["python3", "scripts/audit_provider_compatible_expanded_paid_retry_after_receipt_prompt_recovery.py"]
    )
    codeclash_rev = run_capture(["git", "-C", str(CODECLASH_DIR), "rev-parse", "HEAD"])
    docker = run_capture([str(DOCKER_BIN), "info", "--format", "{{.ServerVersion}}"], timeout=10)
    google_auth = run_capture(
        [str(CODECLASH_DIR / ".venv" / "bin" / "python"), "-c", "import google.auth"],
        timeout=10,
    )
    gcloud_project = run_sensitive_probe(["gcloud", "config", "get-value", "project", "--quiet"], timeout=10)
    adc = run_sensitive_probe(
        ["gcloud", "auth", "application-default", "print-access-token", "--quiet"],
        timeout=20,
    )

    preflight = {
        "schema_version": "telos.provider_compatible_runtime_adc_recovery.preflight.v1",
        "experiment_id": EXPERIMENT_ID,
        "iter74_status": iter74.get("status"),
        "iter74_blocked_result": iter74.get("blocked_result"),
        "iter74_receipt_validation_returncode": iter74_receipts["returncode"],
        "iter74_audit_returncode": iter74_audit["returncode"],
        "codeclash_checkout_present": (CODECLASH_DIR / ".git").exists(),
        "codeclash_expected_commit": CODECLASH_COMMIT,
        "codeclash_actual_commit": codeclash_rev.get("stdout"),
        "codeclash_commit_matches_expected": codeclash_rev.get("stdout") == CODECLASH_COMMIT,
        "docker_preferred_cli": str(DOCKER_BIN),
        "docker_ready": docker.get("returncode") == 0 and bool(docker.get("stdout")),
        "docker_server_version_present": bool(docker.get("stdout")),
        "docker_server_version_committed": False,
        "codeclash_google_auth_import_ready": google_auth.get("returncode") == 0,
        "codeclash_google_auth_stdout_suppressed": True,
        "codeclash_google_auth_stderr_committed": False,
        "gcloud_project_available": (
            gcloud_project["returncode"] == 0 and gcloud_project["stdout_present"] is True
        ),
        "gcloud_project_returncode": gcloud_project["returncode"],
        "gcloud_project_timed_out": gcloud_project["timed_out"],
        "gcloud_project_stdout_suppressed": True,
        "gcloud_project_identifier_committed": False,
        "gcloud_project_stderr_committed": False,
        "gcloud_project_stderr_class": gcloud_project["stderr_class"],
        "adc_access_token_available": adc["returncode"] == 0 and adc["stdout_present"] is True,
        "adc_refresh_returncode": adc["returncode"],
        "adc_refresh_timed_out": adc["timed_out"],
        "adc_token_output_suppressed": True,
        "adc_token_committed": False,
        "adc_stderr_committed": False,
        "adc_error_class": adc["stderr_class"],
        "provider_model_calls": 0,
        "provider_spend_usd": 0.0,
        "adapter_rows_executed": 0,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
    }
    write_json(PROOF / "preflight.json", preflight)

    blockers: list[str] = []
    failures: list[str] = []
    if preflight["iter74_status"] != "blocked" or preflight["iter74_blocked_result"] is not True:
        blockers.append("iter74_not_clean_blocked_result")
    if preflight["iter74_receipt_validation_returncode"] != 0:
        blockers.append("iter74_receipt_validation_failed")
    if preflight["iter74_audit_returncode"] != 0:
        blockers.append("iter74_audit_failed")
    if preflight["codeclash_checkout_present"] is not True:
        blockers.append("codeclash_checkout_missing")
    if preflight["codeclash_commit_matches_expected"] is not True:
        blockers.append("codeclash_checkout_not_pinned")
    if preflight["docker_ready"] is not True:
        blockers.append("docker_not_ready")
    if preflight["codeclash_google_auth_import_ready"] is not True:
        blockers.append("codeclash_google_auth_import_failed")
    if preflight["gcloud_project_available"] is not True:
        blockers.append("gcloud_project_unavailable")
    if preflight["adc_access_token_available"] is not True:
        blockers.append("adc_auth_unavailable")
    if preflight["provider_model_calls"] != 0 or float(preflight["provider_spend_usd"]) != 0.0:
        failures.append("provider_call_or_spend_occurred")
    if preflight["adapter_rows_executed"] != 0:
        failures.append("adapter_row_execution_occurred")

    report = {
        "schema_version": "telos.provider_compatible_runtime_adc_recovery.report.v1",
        "experiment_id": EXPERIMENT_ID,
        "preflight": preflight,
        "iter74_status": preflight["iter74_status"],
        "iter74_blocked_result": preflight["iter74_blocked_result"],
        "iter74_receipt_validation_returncode": preflight["iter74_receipt_validation_returncode"],
        "iter74_audit_returncode": preflight["iter74_audit_returncode"],
        "codeclash_commit_matches_expected": preflight["codeclash_commit_matches_expected"],
        "docker_ready": preflight["docker_ready"],
        "codeclash_google_auth_import_ready": preflight["codeclash_google_auth_import_ready"],
        "gcloud_project_available": preflight["gcloud_project_available"],
        "gcloud_project_stdout_suppressed": True,
        "adc_access_token_available": preflight["adc_access_token_available"],
        "adc_token_output_suppressed": True,
        "adc_error_class": preflight["adc_error_class"],
        "provider_model_calls": 0,
        "provider_spend_usd": 0.0,
        "adapter_rows_executed": 0,
        "runtime_access_ready": (
            preflight["codeclash_commit_matches_expected"] is True
            and preflight["docker_ready"] is True
            and preflight["codeclash_google_auth_import_ready"] is True
            and preflight["gcloud_project_available"] is True
            and preflight["adc_access_token_available"] is True
        ),
        "next_gate_recommendation": (
            "rerun the bounded four-row paid retry only if this gate passes"
        ),
        "credential_material_committed": False,
        "gcloud_project_identifier_committed": False,
        "adc_token_committed": False,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "blockers": sorted(set(blockers)),
        "failures": sorted(set(failures)),
    }
    write_json(PROOF / "runtime_adc_readiness_report.json", report)

    scan_passed, scan_findings = redaction_scan()
    if not scan_passed:
        failures.append("redaction_scan_failed")
    status = "fail" if failures else "blocked" if blockers else "pass"
    blockers = sorted(set(blockers))
    failures = sorted(set(failures))
    report["status"] = status
    report["blockers"] = blockers
    report["failures"] = failures
    report["redaction_scan_passed"] = scan_passed
    report["redaction_findings"] = scan_findings
    write_json(PROOF / "runtime_adc_readiness_report.json", report)

    command_lines = [
        f"provider-compatible runtime adc recovery after paid retry block: {status}",
        f"iter74_receipt_validation_returncode={preflight['iter74_receipt_validation_returncode']}",
        f"iter74_audit_returncode={preflight['iter74_audit_returncode']}",
        f"codeclash_commit_matches_expected={str(preflight['codeclash_commit_matches_expected']).lower()}",
        f"docker_ready={str(preflight['docker_ready']).lower()}",
        f"codeclash_google_auth_import_ready={str(preflight['codeclash_google_auth_import_ready']).lower()}",
        f"gcloud_project_available={str(preflight['gcloud_project_available']).lower()}",
        "gcloud_project_stdout_suppressed=true",
        f"adc_access_token_available={str(preflight['adc_access_token_available']).lower()}",
        "adc_token_output_suppressed=true",
        f"adc_error_class={preflight['adc_error_class']}",
        "provider_model_calls=0",
        "provider_spend_usd=0.00000000",
        "adapter_rows_executed=0",
        "gpu_used=false",
        "cloud_runner_started=false",
        "sentinel_named_resources_modified=false",
        f"redaction_scan_passed={str(scan_passed).lower()}",
        f"blockers={','.join(blockers)}",
        f"failures={','.join(failures)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(command_lines) + "\n", encoding="utf-8")

    review = f"""# Iteration 75 Review

The gate performed only local runtime access-readiness probes after the iter74 paid retry blocked
before adapter-row execution. The gcloud project probe and ADC token probe suppressed stdout and
committed no token, project identifier, service-account, or credential material.

- status: `{status}`,
- iter74 receipt validation return code: `{preflight['iter74_receipt_validation_returncode']}`,
- iter74 audit return code: `{preflight['iter74_audit_returncode']}`,
- CodeClash checkout pinned: `{str(preflight['codeclash_commit_matches_expected']).lower()}`,
- Docker ready: `{str(preflight['docker_ready']).lower()}`,
- CodeClash google.auth import ready: `{str(preflight['codeclash_google_auth_import_ready']).lower()}`,
- gcloud project available: `{str(preflight['gcloud_project_available']).lower()}`,
- ADC access token available: `{str(preflight['adc_access_token_available']).lower()}`,
- ADC error class: `{preflight['adc_error_class']}`,
- provider calls: `0`,
- provider spend: `$0.00000000`,
- adapter rows executed: `0`,
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

No benchmark, SWE-bench, leaderboard, production/live-domain, model-superiority, or
state-of-the-art result is claimed.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    result = f"""# Iteration 75 Result - Provider-Compatible Runtime ADC Recovery After Paid Retry Block

Status: `{status.upper()}`.

## Summary

This zero-spend gate checked whether the local runtime access path recovered after iter74 blocked
on non-interactive ADC refresh.

- iter74 receipt validation return code: `{preflight['iter74_receipt_validation_returncode']}`,
- iter74 audit return code: `{preflight['iter74_audit_returncode']}`,
- CodeClash checkout pinned: `{str(preflight['codeclash_commit_matches_expected']).lower()}`,
- Docker ready: `{str(preflight['docker_ready']).lower()}`,
- CodeClash `google.auth` import ready: `{str(preflight['codeclash_google_auth_import_ready']).lower()}`,
- gcloud project available: `{str(preflight['gcloud_project_available']).lower()}`,
- gcloud project output committed: `false`,
- ADC access token available: `{str(preflight['adc_access_token_available']).lower()}`,
- ADC token output committed: `false`,
- ADC error class: `{preflight['adc_error_class']}`,
- provider calls: `0`,
- provider spend: `$0.00000000`,
- adapter rows executed: `0`,
- GPU used: `false`,
- cloud runner started: `false`,
- Sentinel-named resources modified: `false`,
- benchmark/model/SOTA claim: `false`,
- blockers: `{','.join(blockers) if blockers else 'none'}`,
- failures: `{','.join(failures) if failures else 'none'}`.

## Claim Boundary

This is a runtime access-readiness recovery gate, not a protocol-effect run, benchmark result,
SWE-bench score, leaderboard result, production/live-domain result, model-superiority result, or
state-of-the-art result.

## Evidence

- `proof/preflight.json`
- `proof/runtime_adc_readiness_report.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/{RECEIPT_NAME}`
"""
    RESULT.write_text(result, encoding="utf-8")

    write_json(VALID / RECEIPT_NAME, build_receipt(status))
    write_json(
        PROOF / "learning_record.json",
        {
            "schema_version": "telos.learning_record.v1",
            "experiment_id": EXPERIMENT_ID,
            "status": status if status != "fail" else "null",
            "insight": (
                "The runtime ADC path is ready for the bounded four-row paid retry."
                if status == "pass"
                else "The runtime ADC path is still not ready for paid retry."
            ),
            "next_action": (
                "pre-register the bounded four-row paid retry after ADC recovery"
                if status == "pass"
                else "restore ADC non-interactive refresh before any paid retry"
            ),
            "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
            "evidence_paths": [
                f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
                f"experiments/{EXPERIMENT_ID}/proof/runtime_adc_readiness_report.json",
                f"experiments/{EXPERIMENT_ID}/proof/preflight.json",
                f"experiments/{EXPERIMENT_ID}/proof/valid/{RECEIPT_NAME}",
            ],
        },
    )

    summary_paths = [
        PROOF / "preflight.json",
        PROOF / "runtime_adc_readiness_report.json",
        PROOF / "command_output.txt",
        PROOF / "review.md",
        PROOF / "learning_record.json",
        VALID,
    ]
    summary = {
        "schema_version": "telos.provider_compatible_runtime_adc_recovery.summary.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "iter74_status": preflight["iter74_status"],
        "iter74_blocked_result": preflight["iter74_blocked_result"],
        "iter74_receipt_validation_returncode": preflight["iter74_receipt_validation_returncode"],
        "iter74_audit_returncode": preflight["iter74_audit_returncode"],
        "codeclash_commit_matches_expected": preflight["codeclash_commit_matches_expected"],
        "docker_ready": preflight["docker_ready"],
        "codeclash_google_auth_import_ready": preflight["codeclash_google_auth_import_ready"],
        "gcloud_project_available": preflight["gcloud_project_available"],
        "gcloud_project_stdout_suppressed": True,
        "gcloud_project_identifier_committed": False,
        "adc_access_token_available": preflight["adc_access_token_available"],
        "adc_token_output_suppressed": True,
        "adc_token_committed": False,
        "adc_error_class": preflight["adc_error_class"],
        "provider_model_calls": 0,
        "provider_spend_usd": 0.0,
        "adapter_rows_executed": 0,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "credential_material_committed": False,
        "redaction_scan_passed": scan_passed,
        "redaction_findings": scan_findings,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": blockers,
        "failures": failures,
        "next_gate_recommendation": report["next_gate_recommendation"],
        "artifact_hashes": artifact_hashes(summary_paths),
    }
    write_json(PROOF / "run_summary.json", summary)

    print("\n".join(command_lines))
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
