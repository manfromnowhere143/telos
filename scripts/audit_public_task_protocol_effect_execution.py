#!/usr/bin/env python3
"""Audit the iter40 public-task protocol-effect execution proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter40_public_task_protocol_effect_execution")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
PREFLIGHT = PROOF / "preflight.json"
REPORT = PROOF / "execution_report.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECEIPT = PROOF / "valid" / "receipt_public_task_protocol_effect_execution.json"
ITER41 = Path("experiments/iter41_public_task_protocol_effect_runner_recovery/HYPOTHESIS.md")


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
        "schema_version": "telos.public_task_protocol_effect_execution.summary.v1",
        "status": "blocked",
        "experiment_id": "iter40_public_task_protocol_effect_execution",
        "source_experiment": "iter39_public_task_protocol_effect_slice",
        "provider_model_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_runner_started": False,
        "planned_task_condition_pairs": 6,
        "attempted_task_condition_pairs": 0,
        "blocked_task_condition_pairs": 6,
        "clean_pass": False,
        "blocked_result": True,
        "quality_failure": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "next_gate": ITER41.as_posix(),
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {summary.get(key)!r}")

    blockers = summary.get("blockers", [])
    if "docker_daemon_not_ready" not in blockers:
        failures.append("summary must record docker_daemon_not_ready blocker")
    if "pinned_codeclash_checkout_not_ready" not in blockers:
        failures.append("summary must record pinned_codeclash_checkout_not_ready blocker")

    for key in [
        "credential_material_committed",
        "project_identifier_committed",
        "account_identifier_committed",
    ]:
        if summary.get(key) is not False:
            failures.append(f"summary {key} must be false")

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
    if preflight.get("credential_material_logged") is not False:
        failures.append("preflight must not log credential material")
    if preflight.get("project_identifier_logged") is not False:
        failures.append("preflight must not log project identifiers")
    if preflight.get("account_identifier_logged") is not False:
        failures.append("preflight must not log account identifiers")

    checks = preflight.get("checks", {})
    if checks.get("provider_model_api_calls") != 0:
        failures.append("preflight provider_model_api_calls must be 0")
    if checks.get("provider_spend_usd") != 0.0:
        failures.append("preflight provider_spend_usd must be 0.0")
    if checks.get("cloud_runner_started") is not False:
        failures.append("preflight cloud_runner_started must be false")
    if checks.get("docker_daemon_ready") is not False:
        failures.append("docker_daemon_ready must be false for this blocked proof")
    if checks.get("codeclash_cache", {}).get("pinned_commit_present") is not False:
        failures.append("pinned CodeClash checkout must not be marked ready")
    for key in ["gcloud_project_identifier_logged", "gcloud_account_identifier_logged"]:
        if checks.get(key) is not False:
            failures.append(f"preflight check {key} must be false")


def audit_report(failures: list[str]) -> None:
    report = load_json(REPORT)
    if report.get("status") != "blocked":
        failures.append("execution report status must be blocked")
    if report.get("provider_model_api_calls") != 0:
        failures.append("execution report provider_model_api_calls must be 0")
    if report.get("provider_spend_usd") != 0.0:
        failures.append("execution report provider_spend_usd must be 0.0")
    if report.get("attempted_task_condition_pairs") != 0:
        failures.append("attempted_task_condition_pairs must be 0")
    if report.get("blocked_task_condition_pairs") != 6:
        failures.append("blocked_task_condition_pairs must be 6")
    if report.get("raw_execution_artifacts_created") is not False:
        failures.append("raw_execution_artifacts_created must be false")

    rows = report.get("condition_results", [])
    if len(rows) != 2:
        failures.append("expected two condition rows")
    for row in rows:
        if row.get("attempted_task_count") != 0:
            failures.append(f"condition attempted_task_count must be 0: {row}")
        if row.get("verified_completion_rate") is not None:
            failures.append(f"condition verified_completion_rate must be null: {row}")

    claims = report.get("claim_boundaries", {})
    for key in [
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
        "public task protocol effect execution: blocked",
        "provider_model_api_calls=0",
        "provider_spend_usd=0.0",
        "cloud_runner_started=false",
        "attempted_task_condition_pairs=0",
        "docker_daemon_not_ready",
        "pinned_codeclash_checkout_not_ready",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `BLOCKED`",
        "No provider model call occurred",
        "No benchmark result is claimed",
        "What Remains Forbidden",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in ["stopped at preflight", "not a model result"]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.status != "blocked":
        failures.append("receipt status must be blocked")
    if receipt.receipt_id != "iter40-public-task-protocol-effect-execution-blocked":
        failures.append("unexpected receipt id")


def audit_no_secret_residue(failures: list[str]) -> None:
    forbidden_patterns = [
        re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
        re.compile(r"gho_[A-Za-z0-9_]{20,}"),
        re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
        re.compile(r"ANTHROPIC_API_KEY\s*=\s*\S+"),
        re.compile(r"OPENAI_API_KEY\s*=\s*\S+"),
        re.compile(r"GOOGLE_APPLICATION_CREDENTIALS\s*=\s*\S+"),
    ]
    for path in PROOF.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in forbidden_patterns:
            if pattern.search(text):
                failures.append(f"possible secret pattern in {path}")


def main() -> int:
    failures: list[str] = []
    for path in [RESULT, SUMMARY, PREFLIGHT, REPORT, COMMAND_OUTPUT, REVIEW, RECEIPT, ITER41]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_summary(failures)
        audit_preflight(failures)
        audit_report(failures)
        audit_text_and_receipt(failures)
        audit_no_secret_residue(failures)

    if failures:
        print("public task protocol effect execution audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("public task protocol effect execution audit: clean blocked preflight")
    return 0


if __name__ == "__main__":
    sys.exit(main())
