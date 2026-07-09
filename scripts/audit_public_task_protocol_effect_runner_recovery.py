#!/usr/bin/env python3
"""Audit the iter41 public-task protocol-effect runner recovery proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter41_public_task_protocol_effect_runner_recovery")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
REPORT = PROOF / "runner_recovery_report.json"
SUMMARY = PROOF / "run_summary.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECEIPT = PROOF / "valid" / "receipt_public_task_protocol_effect_runner_recovery.json"
ITER42 = Path("experiments/iter42_public_task_protocol_effect_execution_retry/HYPOTHESIS.md")
CODECLASH_COMMIT = "381cdfa05a35e8acd35853b9fc7e13005121b127"
EXPECTED_RUN_IDS = [29000384304, 29000384298, 29000384382]
EXPECTED_WORKFLOWS = [
    "codeclash-smoke",
    "codeclash-agent-behavior",
    "codeclash-deterministic-edit",
]
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ANTHROPIC_API_KEY\s*=\s*\S+"),
    re.compile(r"OPENAI_API_KEY\s*=\s*\S+"),
    re.compile(r"GOOGLE_APPLICATION_CREDENTIALS\s*=\s*\S+"),
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
        "schema_version": "telos.public_task_protocol_effect_runner_recovery.report.v1",
        "status": "pass",
        "experiment_id": "iter41_public_task_protocol_effect_runner_recovery",
        "isolated_runner": "github_actions_workflow_dispatch",
        "isolated_runner_passed": True,
        "run_count": 3,
        "successful_run_count": 3,
        "pinned_codeclash_commit": CODECLASH_COMMIT,
        "pinned_codeclash_commit_verified": True,
        "docker_readiness_verified": True,
        "dependency_install_verified": True,
        "artifact_upload_verified": True,
        "artifact_destination_ready": True,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "credential_material_committed": False,
        "project_identifier_committed": False,
        "account_identifier_committed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "next_gate": ITER42.as_posix(),
    }
    for key, value in expected.items():
        if report.get(key) != value:
            failures.append(f"report {key} expected {value!r}, got {report.get(key)!r}")

    runs = report.get("runs", [])
    if [run.get("run_id") for run in runs] != EXPECTED_RUN_IDS:
        failures.append("run ids mismatch")
    if [run.get("workflow") for run in runs] != EXPECTED_WORKFLOWS:
        failures.append("workflow order mismatch")
    for run in runs:
        if run.get("conclusion") != "success":
            failures.append(f"run conclusion must be success: {run.get('run_id')}")
        if run.get("required_steps_passed") is not True:
            failures.append(f"required steps failed: {run.get('run_id')}")
        if run.get("summary_codeclash_commit") != CODECLASH_COMMIT:
            failures.append(f"CodeClash commit mismatch: {run.get('run_id')}")
        if run.get("summary_provider_cost_zero") is not True:
            failures.append(f"provider cost not zero in summary: {run.get('run_id')}")

    raw_hashes = report.get("raw_artifact_hashes", {})
    if not isinstance(raw_hashes, dict) or len(raw_hashes) < 7:
        failures.append("raw_artifact_hashes must include downloaded artifacts")
    for rel_path, expected_hash in raw_hashes.items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"missing raw hashed artifact: {rel_path}")
            continue
        actual = sha256(path)
        if actual != expected_hash:
            failures.append(f"raw hash mismatch for {rel_path}")


def audit_summary(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    expected = {
        "schema_version": "telos.public_task_protocol_effect_runner_recovery.summary.v1",
        "status": "pass",
        "experiment_id": "iter41_public_task_protocol_effect_runner_recovery",
        "isolated_runner_passed": True,
        "successful_run_count": 3,
        "pinned_codeclash_commit_verified": True,
        "docker_readiness_verified": True,
        "dependency_install_verified": True,
        "artifact_upload_verified": True,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "clean_pass": True,
        "next_gate": ITER42.as_posix(),
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {summary.get(key)!r}")
    if summary.get("run_ids") != EXPECTED_RUN_IDS:
        failures.append("summary run_ids mismatch")
    if summary.get("raw_artifact_file_count", 0) < 7:
        failures.append("summary raw_artifact_file_count too small")

    hashes = summary.get("artifact_hashes", {})
    if not isinstance(hashes, dict) or not hashes:
        failures.append("summary artifact_hashes must be non-empty")
        return
    for rel_path, expected_hash in hashes.items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"missing top-level hashed artifact: {rel_path}")
            continue
        actual = sha256(path)
        if actual != expected_hash:
            failures.append(f"top-level hash mismatch for {rel_path}")


def audit_text_and_receipt(failures: list[str]) -> None:
    output = COMMAND_OUTPUT.read_text(encoding="utf-8")
    for required in [
        "public task protocol effect runner recovery: pass",
        "isolated_runner=github_actions_workflow_dispatch",
        "successful_runs=3",
        "pinned_codeclash_commit_verified=true",
        "docker_readiness_verified=true",
        "provider_model_api_calls=0",
        "provider_spend_usd=0.0",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`",
        "Local Docker readiness remained unavailable",
        "No benchmark result is claimed",
        "No provider-backed task execution is claimed",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in ["registered isolated-runner path", "do not produce a"]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.status != "pass":
        failures.append("receipt status must be pass")
    if receipt.receipt_id != "iter41-public-task-protocol-effect-runner-recovery-pass":
        failures.append("unexpected receipt id")


def audit_secret_residue(failures: list[str]) -> None:
    for path in PROOF.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix == ".gz":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"possible secret pattern in {path}")


def main() -> int:
    failures: list[str] = []
    for path in [RESULT, REPORT, SUMMARY, COMMAND_OUTPUT, REVIEW, RECEIPT, ITER42]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_report(failures)
        audit_summary(failures)
        audit_text_and_receipt(failures)
        audit_secret_residue(failures)

    if failures:
        print("public task protocol effect runner recovery audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("public task protocol effect runner recovery audit: clean isolated-runner pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
