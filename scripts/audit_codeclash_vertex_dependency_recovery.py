#!/usr/bin/env python3
"""Audit iter58 CodeClash Vertex dependency recovery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter58_codeclash_vertex_dependency_recovery")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
REPORT = PROOF / "dependency_recovery_report.json"
INSTALL = PROOF / "install_command.json"
RECEIPT = PROOF / "valid" / "receipt_codeclash_vertex_dependency_recovery.json"
NEXT_GATE = Path(
    "experiments/iter59_provider_compatible_paid_execution_after_dependency_recovery/HYPOTHESIS.md"
)
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"-----BEGIN PRIVATE KEY-----"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com"),
    re.compile(r"telos-vertex-runner"),
    re.compile(r"sunlit-unison-[A-Za-z0-9-]+"),
    re.compile(r"errorId=Ci"),
    re.compile(r'"error_info_id"\s*:\s*"Ci'),
]


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be an object")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_summary_and_report(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    report = load_json(REPORT)
    install = load_json(INSTALL)
    expected = {
        "schema_version": "telos.codeclash_vertex_dependency_recovery.summary.v1",
        "status": "pass",
        "iter57_status": "blocked",
        "missing_dependency": "google.auth",
        "before_google_auth_import": False,
        "after_google_auth_import": True,
        "install_returncode": 0,
        "codeclash_commit_matches_expected": True,
        "frozen_overlay_hashes_match": True,
        "iter54_command_manifest_unchanged": True,
        "docker_ready": True,
        "adc_access_token_available": True,
        "paid_battlesnake_command_executed": False,
        "excluded_pair_executed": False,
        "provider_model_calls": 0,
        "provider_spend_usd": 0.0,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "cloud_runner_started": False,
        "redaction_scan_passed": True,
        "redaction_findings": [],
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
    if not isinstance(summary.get("google_auth_version"), str) or not summary["google_auth_version"]:
        failures.append("summary must record installed google-auth version")
    if report.get("status") != "pass" or report.get("after_import", {}).get("available") is not True:
        failures.append("report must pass with after_import available")
    if report.get("paid_battlesnake_command_executed") is not False:
        failures.append("report must show no paid BattleSnake row execution")
    if install.get("returncode") != 0 or "google-auth" not in install.get("command", ""):
        failures.append("install command must install google-auth successfully")
    for rel_path, digest in summary.get("artifact_hashes", {}).items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"summary hash path missing: {rel_path}")
        elif sha256(path) != digest:
            failures.append(f"summary hash mismatch: {rel_path}")


def audit_receipt_and_text(failures: list[str]) -> None:
    try:
        receipt = load_receipt(RECEIPT)
        if receipt.status != "pass":
            failures.append(f"receipt status expected pass, got {receipt.status}")
    except ProofValidationError as exc:
        failures.append(f"receipt validation failed: {exc}")
    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`.",
        "`google.auth` import after recovery: `true`",
        "provider model calls: `0`",
        "No model-superiority or state-of-the-art result is claimed.",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")


def audit_secrets(failures: list[str]) -> None:
    for path in EXPERIMENT.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"secret-like or identifier residue in {path}")
                break


def main() -> int:
    failures: list[str] = []
    for path in [RESULT, SUMMARY, REPORT, INSTALL, RECEIPT, NEXT_GATE]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")
    if not failures:
        audit_summary_and_report(failures)
        audit_receipt_and_text(failures)
        audit_secrets(failures)
    if failures:
        print("iter58 CodeClash Vertex dependency recovery audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter58 CodeClash Vertex dependency recovery audit: clean pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
