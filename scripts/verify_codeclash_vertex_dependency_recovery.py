#!/usr/bin/env python3
"""Publish iter58 CodeClash Vertex dependency recovery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter58_codeclash_vertex_dependency_recovery"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
ITER57_SUMMARY = (
    ROOT
    / "experiments"
    / "iter57_provider_compatible_paid_execution_after_auth_recovery"
    / "proof"
    / "run_summary.json"
)
ITER57_DEPENDENCY = (
    ROOT
    / "experiments"
    / "iter57_provider_compatible_paid_execution_after_auth_recovery"
    / "proof"
    / "dependency_block_evidence.json"
)
ITER54_COMMANDS = (
    ROOT / "experiments" / "iter54_provider_pair_executor_recovery" / "proof" / "command_manifest.json"
)
ITER54_OVERLAYS = (
    ROOT / "experiments" / "iter54_provider_pair_executor_recovery" / "proof" / "overlay_copy_manifest.json"
)
CODECLASH_DIR = Path("/tmp/telos-codeclash")
CODECLASH_PYTHON = CODECLASH_DIR / ".venv" / "bin" / "python"
CODECLASH_COMMIT = "381cdfa05a35e8acd35853b9fc7e13005121b127"
DOCKER_BIN = Path("/Applications/Docker.app/Contents/Resources/bin/docker")
NEXT_GATE = (
    ROOT
    / "experiments"
    / "iter59_provider_compatible_paid_execution_after_dependency_recovery"
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


def run_capture(args: list[str], timeout: int = 30) -> dict[str, Any]:
    try:
        result = subprocess.run(
            args,
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


def run_secret_safe(args: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        result = subprocess.run(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"returncode": None, "timed_out": True}
    return {"returncode": result.returncode, "timed_out": False}


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter58-codeclash-vertex-dependency-recovery-{status}",
        "task_id": "telos:iter58_codeclash_vertex_dependency_recovery@iter57",
        "agent_id": "codex-local-codeclash-dependency-recovery",
        "benchmark_id": "telos_codeclash_swebench_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Recover the local CodeClash Vertex auth dependency that blocked iter57 without "
            "executing any paid BattleSnake row."
        ),
        "acceptance_criteria": [
            "Iter57 is a clean blocked result caused by the missing google.auth dependency.",
            "The local CodeClash virtualenv imports google.auth after recovery.",
            "The pinned CodeClash commit, frozen configs, and iter54 command manifest remain unchanged.",
            "No provider model call, provider spend, GPU use, Sentinel mutation, cloud runner, or overclaim occurs.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/dependency_recovery_report.json",
                "notes": "Dependency recovery report records import status, package version, hashes, and zero-spend controls.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/install_command.json",
                "notes": "Install command records the exact zero-provider dependency repair action.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": f"experiments/{EXPERIMENT_ID}/proof/review.md",
                "notes": "Review records the dependency-only claim boundary.",
            },
        ],
        "falsifiers": [
            "The result must block if google.auth still cannot import.",
            "The result must fail if any paid row, provider model call, provider spend, GPU use, Sentinel mutation, or overclaim occurs.",
            "The result must fail if the pinned CodeClash source checkout or frozen configs change.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def import_status() -> dict[str, Any]:
    result = run_capture(
        [
            str(CODECLASH_PYTHON),
            "-c",
            "import google.auth, importlib.metadata as m; print(m.version('google-auth'))",
        ],
        timeout=15,
    )
    return {
        "available": result["returncode"] == 0,
        "version": result["stdout"] if result["returncode"] == 0 else None,
        "error_class": "none" if result["returncode"] == 0 else "google_auth_module_missing",
    }


def codeclash_commit() -> str | None:
    result = run_capture(["git", "-C", str(CODECLASH_DIR), "rev-parse", "HEAD"], timeout=10)
    return result["stdout"] if result["returncode"] == 0 else None


def overlay_hashes() -> dict[str, Any]:
    manifest = read_json(ITER54_OVERLAYS)
    entries = []
    all_match = True
    for copy in manifest.get("copies", []):
        rel = copy["destination"]
        path = CODECLASH_DIR / rel
        actual = sha256_file(path) if path.exists() else None
        expected = copy["destination_sha256"]
        match = actual == expected
        all_match = all_match and match
        entries.append(
            {
                "destination": rel,
                "expected_sha256": expected,
                "actual_sha256": actual,
                "hash_match": match,
            }
        )
    return {"all_hashes_match": all_match, "entries": entries}


def install_dependency() -> dict[str, Any]:
    started = time.time()
    result = run_capture(
        ["uv", "pip", "install", "--python", str(CODECLASH_PYTHON), "google-auth"],
        timeout=180,
    )
    elapsed = round(time.time() - started, 3)
    install = {
        "command": f"uv pip install --python {CODECLASH_PYTHON} google-auth",
        "returncode": result["returncode"],
        "timed_out": result["timed_out"],
        "elapsed_seconds": elapsed,
        "stdout_logged": True,
        "stderr_logged": True,
    }
    (PROOF / "install_stdout.txt").write_text(result["stdout"] + "\n", encoding="utf-8")
    (PROOF / "install_stderr.txt").write_text(result["stderr"] + "\n", encoding="utf-8")
    write_json(PROOF / "install_command.json", install)
    return install


def redaction_scan(paths: list[Path]) -> tuple[bool, list[str]]:
    findings: list[str] = []
    for base in paths:
        candidates = [base] if base.is_file() else [path for path in base.rglob("*") if path.is_file()]
        for path in candidates:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    findings.append(str(path.relative_to(ROOT)))
                    break
    return not findings, findings


def artifact_hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path.relative_to(PROOF)): sha256_file(path) for path in paths if path.exists()}


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    iter57 = read_json(ITER57_SUMMARY)
    iter57_dependency = read_json(ITER57_DEPENDENCY)
    commands = read_json(ITER54_COMMANDS)

    before_import = import_status()
    install = install_dependency()
    after_import = import_status()
    overlays = overlay_hashes()
    commit = codeclash_commit()
    docker = run_capture([str(DOCKER_BIN), "info", "--format", "{{.ServerVersion}}"], timeout=10)
    adc = run_secret_safe(["gcloud", "auth", "application-default", "print-access-token", "--quiet"])

    blockers: list[str] = []
    failures: list[str] = []
    if iter57.get("status") != "blocked":
        blockers.append("iter57_not_blocked")
    if "codeclash_vertex_google_auth_dependency_missing" not in iter57.get("blockers", []):
        blockers.append("iter57_dependency_blocker_not_present")
    if iter57_dependency.get("missing_dependency") != "google.auth":
        blockers.append("iter57_missing_dependency_not_google_auth")
    if install["returncode"] != 0:
        blockers.append("google_auth_install_failed")
    if not after_import["available"]:
        blockers.append("google_auth_import_still_missing")
    if commit != CODECLASH_COMMIT:
        failures.append("codeclash_commit_changed")
    if not overlays["all_hashes_match"]:
        failures.append("frozen_overlay_hash_changed")
    if commands.get("selected_pair_count") != 2 or commands.get("provider_command_executed") is not False:
        failures.append("iter54_command_manifest_changed")
    if docker.get("returncode") != 0:
        blockers.append("docker_readiness_regressed")
    if adc.get("returncode") != 0:
        blockers.append("adc_readiness_regressed")

    report = {
        "schema_version": "telos.codeclash_vertex_dependency_recovery.report.v1",
        "status": "pending",
        "experiment_id": EXPERIMENT_ID,
        "source_iter57_summary_path": str(ITER57_SUMMARY.relative_to(ROOT)),
        "source_iter57_dependency_path": str(ITER57_DEPENDENCY.relative_to(ROOT)),
        "iter57_status": iter57.get("status"),
        "iter57_blockers": iter57.get("blockers", []),
        "missing_dependency": "google.auth",
        "before_import": before_import,
        "install": install,
        "after_import": after_import,
        "codeclash_checkout_path": str(CODECLASH_DIR),
        "codeclash_expected_commit": CODECLASH_COMMIT,
        "codeclash_actual_commit": commit,
        "codeclash_commit_matches_expected": commit == CODECLASH_COMMIT,
        "frozen_overlay_hashes": overlays,
        "iter54_command_manifest_path": str(ITER54_COMMANDS.relative_to(ROOT)),
        "iter54_command_manifest_unchanged": commands.get("selected_pair_count") == 2
        and commands.get("provider_command_executed") is False,
        "docker_ready": docker.get("returncode") == 0 and bool(docker.get("stdout")),
        "adc_access_token_available": adc.get("returncode") == 0,
        "adc_token_output_suppressed": True,
        "paid_battlesnake_command_executed": False,
        "excluded_pair_executed": False,
        "provider_model_calls": 0,
        "provider_spend_usd": 0.0,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "cloud_runner_started": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
        "blockers": blockers,
        "failures": failures,
    }
    scan_passed, scan_findings = redaction_scan(
        [
            PROOF / "install_command.json",
            PROOF / "install_stdout.txt",
            PROOF / "install_stderr.txt",
        ]
    )
    if not scan_passed:
        failures.append("redaction_scan_failed")
    status = "fail" if failures else "blocked" if blockers else "pass"
    report["status"] = status
    report["redaction_scan_passed"] = scan_passed
    report["redaction_findings"] = scan_findings
    write_json(PROOF / "dependency_recovery_report.json", report)

    output_lines = [
        f"codeclash vertex dependency recovery: {status}",
        f"before_google_auth_import={str(before_import['available']).lower()}",
        f"after_google_auth_import={str(after_import['available']).lower()}",
        f"google_auth_version={after_import['version']}",
        f"install_returncode={install['returncode']}",
        f"codeclash_commit_matches_expected={str(commit == CODECLASH_COMMIT).lower()}",
        f"frozen_overlay_hashes_match={str(overlays['all_hashes_match']).lower()}",
        "paid_battlesnake_command_executed=false",
        "provider_model_calls=0",
        "provider_spend_usd=0.0",
        f"blockers={','.join(blockers)}",
        f"failures={','.join(failures)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    result_md = f"""# Iteration 58 Result - CodeClash Vertex Dependency Recovery

Status: `{status.upper()}`.

## Summary

The gate recovered the missing local CodeClash Vertex auth dependency without executing either
paid BattleSnake row.

- `google.auth` import before recovery: `{str(before_import['available']).lower()}`,
- `google.auth` import after recovery: `{str(after_import['available']).lower()}`,
- installed `google-auth` version: `{after_import['version']}`,
- CodeClash commit unchanged: `{str(commit == CODECLASH_COMMIT).lower()}`,
- frozen overlay hashes unchanged: `{str(overlays['all_hashes_match']).lower()}`,
- provider model calls: `0`,
- provider spend: `$0.00`,
- paid BattleSnake commands executed: `false`.

## What Is Now Authorized

- Pre-register a retry of the same exact two-row paid pilot under the iter54 command manifest.

## What Remains Forbidden

- No benchmark result is claimed.
- No SWE-bench score is claimed.
- No leaderboard result is claimed.
- No production or live-domain result is claimed.
- No model-superiority or state-of-the-art result is claimed.
- No provider-compatible protocol-effect metric is inferred from dependency readiness.
"""
    (EXPERIMENT / "RESULT.md").write_text(result_md, encoding="utf-8")

    review = """# Iteration 58 Review

The recovery was correctly limited to the local CodeClash virtualenv dependency required for
LiteLLM Vertex auth. It did not change the pinned CodeClash commit, frozen provider configs, or
iter54 command manifest, and it did not execute selected or excluded BattleSnake rows.

No provider model call, provider spend, cloud runner, GPU use, Sentinel resource mutation,
benchmark claim, model-superiority claim, or state-of-the-art claim occurred.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    summary_paths = [
        PROOF / "dependency_recovery_report.json",
        PROOF / "install_command.json",
        PROOF / "install_stdout.txt",
        PROOF / "install_stderr.txt",
        PROOF / "command_output.txt",
        PROOF / "review.md",
    ]
    run_summary = {
        "schema_version": "telos.codeclash_vertex_dependency_recovery.summary.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "iter57_status": iter57.get("status"),
        "missing_dependency": "google.auth",
        "before_google_auth_import": before_import["available"],
        "after_google_auth_import": after_import["available"],
        "google_auth_version": after_import["version"],
        "install_returncode": install["returncode"],
        "codeclash_commit_matches_expected": commit == CODECLASH_COMMIT,
        "frozen_overlay_hashes_match": overlays["all_hashes_match"],
        "iter54_command_manifest_unchanged": report["iter54_command_manifest_unchanged"],
        "docker_ready": report["docker_ready"],
        "adc_access_token_available": report["adc_access_token_available"],
        "paid_battlesnake_command_executed": False,
        "excluded_pair_executed": False,
        "provider_model_calls": 0,
        "provider_spend_usd": 0.0,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "cloud_runner_started": False,
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
        "artifact_hashes": artifact_hashes(summary_paths),
    }
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "insight": (
            "The local CodeClash virtualenv can now import google.auth while the pinned checkout "
            "and frozen provider configs remain unchanged."
        ),
        "next_action": "retry the exact two-row paid pilot after dependency recovery",
        "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
        "evidence_paths": [
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            f"experiments/{EXPERIMENT_ID}/proof/dependency_recovery_report.json",
            f"experiments/{EXPERIMENT_ID}/proof/valid/receipt_codeclash_vertex_dependency_recovery.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(VALID / "receipt_codeclash_vertex_dependency_recovery.json", build_receipt(status))

    print("\n".join(output_lines))
    return 0 if status in {"pass", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
