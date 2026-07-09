#!/usr/bin/env python3
"""Audit iter54 provider pair executor recovery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter54_provider_pair_executor_recovery")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
REPORT = PROOF / "executor_readiness_report.json"
PLAN = PROOF / "executor_readiness_plan.json"
COMMANDS = PROOF / "command_manifest.json"
OVERLAYS = PROOF / "overlay_copy_manifest.json"
SUMMARY = PROOF / "run_summary.json"
RECEIPT = PROOF / "valid" / "receipt_provider_pair_executor_recovery.json"
NEXT_GATE = Path(
    "experiments/iter55_provider_compatible_paid_execution_after_executor_recovery/HYPOTHESIS.md"
)
READY_PAIR_IDS = {
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
}
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"-----BEGIN PRIVATE KEY-----"),
]


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be an object")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_report(failures: list[str]) -> None:
    report = load_json(REPORT)
    expected = {
        "schema_version": "telos.provider_pair_executor_recovery.report.v1",
        "status": "pass",
        "experiment_id": "iter54_provider_pair_executor_recovery",
        "condition_plan_status": "condition_separated_ready",
        "executor_plan_status": "executor_readiness_ready",
        "provider_command_executed": False,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
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
    if set(report.get("selected_pair_ids", [])) != READY_PAIR_IDS:
        failures.append("report selected pair ids changed")
    if report.get("codeclash", {}).get("pinned_commit_present") is not True:
        failures.append("pinned CodeClash checkout must be ready")
    docker = report.get("docker", {})
    if docker.get("docker_daemon_ready") is not True:
        failures.append("Docker daemon readiness must be true")
    if docker.get("preferred_cli_ready") is not True:
        failures.append("preferred Docker CLI must be ready")
    if docker.get("path_cli_target_is_current_app") is not False:
        failures.append("PATH Docker symlink caveat should be recorded as false")
    if report.get("overlay_copy", {}).get("all_hashes_match") is not True:
        failures.append("overlay copy hashes must match")


def audit_plan_and_commands(failures: list[str]) -> None:
    plan = load_json(PLAN)
    commands = load_json(COMMANDS)
    overlays = load_json(OVERLAYS)
    if plan.get("status") != "executor_readiness_ready":
        failures.append("executor plan must be ready")
    if set(plan.get("selected_pair_ids", [])) != READY_PAIR_IDS:
        failures.append("executor plan selected pair ids changed")
    if plan.get("provider_command_executed") is not False:
        failures.append("executor plan must not execute provider commands")
    if commands.get("provider_command_executed") is not False:
        failures.append("command manifest must not execute provider commands")
    command_rows = commands.get("commands", [])
    if len(command_rows) != 2:
        failures.append("command manifest must contain exactly two commands")
    for row in command_rows:
        if row.get("pair_id") not in READY_PAIR_IDS:
            failures.append(f"unexpected command pair id: {row.get('pair_id')}")
        if row.get("executed") is not False:
            failures.append("command rows must remain unexecuted")
        if "uv run codeclash run configs/test/telos_battlesnake_vertex_gemini_" not in row.get(
            "command", ""
        ):
            failures.append(f"command does not bind recovered overlay: {row}")
    if overlays.get("copied_file_count") != 6:
        failures.append("overlay copy should include six unique files")
    if overlays.get("all_hashes_match") is not True:
        failures.append("overlay hashes must match")


def audit_summary_and_text(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    expected = {
        "schema_version": "telos.provider_pair_executor_recovery.summary.v1",
        "status": "pass",
        "experiment_id": "iter54_provider_pair_executor_recovery",
        "pinned_codeclash_checkout_ready": True,
        "docker_daemon_ready": True,
        "path_docker_symlink_current": False,
        "overlay_copy_hashes_match": True,
        "provider_command_executed": False,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "redaction_scan_passed": True,
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
    for rel_path, digest in summary.get("artifact_hashes", {}).items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"summary artifact missing: {rel_path}")
        elif sha256(path) != digest:
            failures.append(f"summary artifact hash mismatch: {rel_path}")
    try:
        receipt = load_receipt(RECEIPT)
        if receipt.status != "pass":
            failures.append(f"receipt status expected pass, got {receipt.status}")
    except ProofValidationError as exc:
        failures.append(f"receipt validation failed: {exc}")
    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`.",
        "provider commands executed: `false`",
        "No benchmark result is claimed.",
        "No model-superiority or state-of-the-art result is claimed.",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")


def audit_secrets(failures: list[str]) -> None:
    for path in [REPORT, PLAN, COMMANDS, OVERLAYS, SUMMARY, RESULT]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"secret-like residue in {path}")
                break


def main() -> int:
    failures: list[str] = []
    for path in [REPORT, PLAN, COMMANDS, OVERLAYS, SUMMARY, RESULT, RECEIPT, NEXT_GATE]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")
    if not failures:
        audit_report(failures)
        audit_plan_and_commands(failures)
        audit_summary_and_text(failures)
        audit_secrets(failures)
    if failures:
        print("iter54 provider pair executor recovery audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter54 provider pair executor recovery audit: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
