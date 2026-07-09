#!/usr/bin/env python3
"""Audit the iter42 public-task protocol-effect execution-retry proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter42_public_task_protocol_effect_execution_retry")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
PREFLIGHT = PROOF / "preflight.json"
REPORT = PROOF / "execution_retry_report.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECEIPT = PROOF / "valid" / "receipt_public_task_protocol_effect_execution_retry.json"
ITER43 = Path("experiments/iter43_provider_execution_harness_recovery/HYPOTHESIS.md")
EXPECTED_BLOCKERS = {
    "provider_capable_github_workflow_missing",
    "github_provider_secret_boundary_missing",
    "committed_provider_execution_harness_missing",
    "cost_capture_harness_not_validated",
    "raw_artifact_redaction_harness_not_validated",
    "ephemeral_runner_lifecycle_harness_not_validated",
    "provider_capable_isolated_runner_unavailable",
}
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


def audit_summary(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    expected = {
        "schema_version": "telos.public_task_protocol_effect_execution_retry.summary.v1",
        "status": "blocked",
        "experiment_id": "iter42_public_task_protocol_effect_execution_retry",
        "provider_execution_harness_recovered": False,
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "planned_task_condition_pairs": 6,
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": 6,
        "github_provider_secret_name_count": 0,
        "github_provider_workflow_count": 0,
        "committed_provider_execution_harness_present": False,
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
        "next_gate": ITER43.as_posix(),
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {summary.get(key)!r}")

    if summary.get("iter41_runner_recovery_accepted") is not True:
        failures.append("summary must accept iter41 runner recovery")
    if not EXPECTED_BLOCKERS.issubset(set(summary.get("blockers", []))):
        failures.append("summary missing expected provider-harness blockers")

    hashes = summary.get("artifact_hashes", {})
    if not isinstance(hashes, dict) or not hashes:
        failures.append("summary artifact_hashes must be non-empty")
        return
    for rel_path, expected_hash in hashes.items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"hashed artifact missing: {rel_path}")
            continue
        actual_hash = sha256(path)
        if actual_hash != expected_hash:
            failures.append(
                f"hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}"
            )


def audit_preflight(failures: list[str]) -> None:
    preflight = load_json(PREFLIGHT)
    if preflight.get("status") != "blocked":
        failures.append("preflight status must be blocked")
    for key in [
        "credential_material_logged",
        "project_identifier_logged",
        "account_identifier_logged",
    ]:
        if preflight.get(key) is not False:
            failures.append(f"preflight {key} must be false")

    checks = preflight.get("checks", {})
    if checks.get("provider_model_api_calls") != 0:
        failures.append("preflight provider_model_api_calls must be 0")
    if checks.get("provider_spend_usd") != 0.0:
        failures.append("preflight provider_spend_usd must be 0.0")
    if checks.get("cloud_runner_started") is not False:
        failures.append("preflight cloud_runner_started must be false")

    github = checks.get("github_actions", {})
    if github.get("isolated_runner_recovered") is not True:
        failures.append("iter41 isolated runner recovery must be accepted")
    if github.get("workflow_state", {}).get("provider_capable_workflow_count") != 0:
        failures.append("provider-capable GitHub workflow count must be 0")
    if github.get("secret_state", {}).get("provider_secret_name_count") != 0:
        failures.append("provider GitHub secret count must be 0")

    harness = checks.get("committed_harness", {})
    if harness.get("committed_provider_execution_harness_present") is not False:
        failures.append("committed provider execution harness must be absent")
    if harness.get("cost_capture_harness_validated") is not False:
        failures.append("cost capture harness must not be marked validated")
    if harness.get("raw_artifact_redaction_harness_validated") is not False:
        failures.append("redaction harness must not be marked validated")
    if harness.get("ephemeral_runner_lifecycle_harness_validated") is not False:
        failures.append("runner lifecycle harness must not be marked validated")

    previous = checks.get("previous_provider_evidence", {})
    if previous.get("available") is not True:
        failures.append("prior provider evidence should be referenced")
    if previous.get("treated_as_reusable_execution_harness") is not False:
        failures.append("prior provider evidence must not be treated as the reusable harness")

    if not EXPECTED_BLOCKERS.issubset(set(preflight.get("blockers", []))):
        failures.append("preflight missing expected provider-harness blockers")


def audit_report(failures: list[str]) -> None:
    report = load_json(REPORT)
    expected = {
        "schema_version": "telos.public_task_protocol_effect_execution_retry.report.v1",
        "status": "blocked",
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "planned_task_condition_pairs": 6,
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": 6,
        "raw_execution_artifacts_created": False,
        "provider_execution_harness_recovered": False,
        "iter41_runner_recovery_accepted": True,
        "next_gate": ITER43.as_posix(),
    }
    for key, value in expected.items():
        if report.get(key) != value:
            failures.append(f"report {key} expected {value!r}, got {report.get(key)!r}")

    rows = report.get("condition_results", [])
    if len(rows) != 2:
        failures.append("expected two condition rows")
    for row in rows:
        if row.get("attempted_task_count") != 0:
            failures.append(f"condition attempted_task_count must be 0: {row}")
        if row.get("verified_completion_rate") is not None:
            failures.append(f"condition verified_completion_rate must be null: {row}")
        if row.get("reason") != "provider_execution_harness_blocked_before_execution":
            failures.append(f"unexpected condition blocked reason: {row}")

    claims = report.get("claim_boundaries", {})
    for key in [
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "production_or_live_domain_changed",
        "live_domain_result_claimed",
    ]:
        if claims.get(key) is not False:
            failures.append(f"claim boundary {key} must be false")


def audit_text_and_receipt(failures: list[str]) -> None:
    output = COMMAND_OUTPUT.read_text(encoding="utf-8")
    for required in [
        "public task protocol effect execution retry: blocked",
        "provider_model_api_calls=0",
        "provider_spend_usd=0.0",
        "cloud_runner_started=false",
        "isolated_runner_recovered=true",
        "attempted_task_condition_pairs=0",
        "committed_provider_execution_harness_missing",
        "provider_capable_isolated_runner_unavailable",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `BLOCKED`",
        "provider-capable GitHub workflow: `missing`",
        "No benchmark result is claimed",
        "What Remains Forbidden",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in ["stopped at preflight", "No task-condition pair started"]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.status != "blocked":
        failures.append("receipt status must be blocked")
    if receipt.receipt_id != "iter42-public-task-protocol-effect-execution-retry-blocked":
        failures.append("unexpected receipt id")


def audit_no_secret_residue(failures: list[str]) -> None:
    for path in PROOF.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"possible secret pattern in {path}")


def main() -> int:
    failures: list[str] = []
    for path in [RESULT, SUMMARY, PREFLIGHT, REPORT, COMMAND_OUTPUT, REVIEW, RECEIPT, ITER43]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_summary(failures)
        audit_preflight(failures)
        audit_report(failures)
        audit_text_and_receipt(failures)
        audit_no_secret_residue(failures)

    if failures:
        print("public task protocol effect execution retry audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("public task protocol effect execution retry audit: clean blocked preflight")
    return 0


if __name__ == "__main__":
    sys.exit(main())
