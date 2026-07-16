#!/usr/bin/env python3
"""Audit iter65 receipt-schema prompt-alignment artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


ROOT = Path.cwd()
EXPERIMENT = Path("experiments/iter65_receipt_schema_prompt_alignment")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
REPORT = PROOF / "receipt_schema_alignment_report.json"
DIAGNOSIS = PROOF / "receipt_failure_diagnosis.json"
FIXTURE_REPORT = PROOF / "fixture_validation_report.json"
OVERLAY = PROOF / "recovered_overlay" / "configs" / "mini" / "telos_vertex_gemini_receipt_enforced_agent.yaml"
TEMPLATE = PROOF / "recovered_overlay" / "receipt_template.json"
VALID_FIXTURE = PROOF / "fixture_receipts" / "valid" / "local_valid_receipt.json"
INVALID_FIXTURE = PROOF / "fixture_receipts" / "invalid" / "missing_sha256_receipt.json"
RECEIPT = PROOF / "valid" / "receipt_receipt_schema_prompt_alignment.json"
ITER64_PROOF = Path("experiments/iter64_provider_compatible_paid_execution_after_access_path_recovery/proof")
ITER64_CANDIDATE = (
    ITER64_PROOF
    / "raw"
    / "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml"
    / "telos_completion_receipt_candidate.json"
)
SCHEMA = Path("protocol/proof.schema.json")
PROOF_MODULE = Path("telos/proof.py")
VALIDATOR = Path("scripts/validate_receipts.py")
ITER65_SOURCE_COMMIT = "40cdf2d5bbbd4d9ccd22aebb54cf04606ed90702"
EXPECTED_MISSING = [
    "agent_id",
    "benchmark_id",
    "evidence",
    "receipt_id",
    "sha256",
    "stated_goal",
    "status",
    "task_id",
]
REQUIRED_FIELDS = [
    "receipt_id",
    "task_id",
    "agent_id",
    "benchmark_id",
    "status",
    "stated_goal",
    "acceptance_criteria",
    "evidence",
    "falsifiers",
    "sha256",
]
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


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be an object")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def historical_sha256(commit: str, path: Path) -> str:
    """Hash a source file exactly as it existed in the sealed historical commit."""

    result = subprocess.run(
        ["git", "show", f"{commit}:{path.as_posix()}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        diagnostic = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            f"cannot read historical source blob {commit}:{path}: {diagnostic}"
        )
    return hashlib.sha256(result.stdout).hexdigest()


def text_files(path: Path) -> list[Path]:
    return [
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file() and candidate.suffix in TEXT_SUFFIXES
    ]


def audit_required_files(failures: list[str]) -> None:
    for path in [
        RESULT,
        SUMMARY,
        REPORT,
        DIAGNOSIS,
        FIXTURE_REPORT,
        OVERLAY,
        TEMPLATE,
        VALID_FIXTURE,
        INVALID_FIXTURE,
        PROOF / "command_output.txt",
        PROOF / "review.md",
        PROOF / "learning_record.json",
        RECEIPT,
    ]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")


def audit_summary_report_and_diagnosis(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    report = load_json(REPORT)
    diagnosis = load_json(DIAGNOSIS)
    fixture = load_json(FIXTURE_REPORT)

    if summary.get("schema_version") != "telos.receipt_schema_prompt_alignment.summary.v1":
        failures.append("unexpected summary schema")
    if report.get("schema_version") != "telos.receipt_schema_prompt_alignment.report.v1":
        failures.append("unexpected report schema")
    if diagnosis.get("schema_version") != "telos.receipt_schema_prompt_alignment.diagnosis.v1":
        failures.append("unexpected diagnosis schema")
    if fixture.get("schema_version") != "telos.receipt_schema_prompt_alignment.fixture_validation.v1":
        failures.append("unexpected fixture report schema")
    if summary.get("experiment_id") != EXPERIMENT.name or report.get("experiment_id") != EXPERIMENT.name:
        failures.append("experiment id mismatch")
    if summary.get("status") != report.get("status"):
        failures.append("summary/report status mismatch")

    status = summary.get("status")
    if status != "pass":
        failures.append(f"iter65 expected a clean local pass, got {status!r}")
    if summary.get("clean_pass") is not True or summary.get("blocked_result") is not False:
        failures.append("summary pass booleans are inconsistent")
    if summary.get("quality_failure") is not False:
        failures.append("quality_failure must be false")
    if summary.get("blockers") != [] or summary.get("failures") != []:
        failures.append("clean pass must have no blockers or failures")

    for key in [
        "gpu_used",
        "cloud_runner_started",
        "sentinel_named_resources_modified",
        "production_or_live_domain_changed",
        "excluded_pair_executed",
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
    ]:
        if summary.get(key) is not False:
            failures.append(f"summary {key} must be false")
        if report.get(key) is not False:
            failures.append(f"report {key} must be false")
    if summary.get("provider_api_calls") != 0 or report.get("provider_api_calls") != 0:
        failures.append("provider_api_calls must be zero")
    if summary.get("provider_spend_usd") != 0.0 or report.get("provider_spend_usd") != 0.0:
        failures.append("provider_spend_usd must be zero")

    for key in [
        "iter64_receipt_failure_classification",
        "missing_required_fields",
        "unexpected_fields_under_schema",
        "recovered_prompt_required_fields_present",
        "recovered_prompt_digest_rule_present",
        "local_valid_fixture_passed",
        "local_malformed_fixture_failed",
        "redaction_scan_passed",
        "redaction_findings",
    ]:
        if summary.get(key) != report.get(key):
            failures.append(f"summary/report mismatch for {key}")

    if summary.get("iter64_receipt_failure_classification") != "schema_incomplete":
        failures.append("iter64 receipt classification must be schema_incomplete")
    if summary.get("missing_required_fields") != EXPECTED_MISSING:
        failures.append("missing required field list changed")
    if sorted(summary.get("unexpected_fields_under_schema", [])) != [
        "evidence_artifacts",
        "files_changed",
        "files_intentionally_left_unchanged",
        "goal",
    ]:
        failures.append("unexpected iter64 candidate fields changed")
    if diagnosis.get("missing_required_fields") != EXPECTED_MISSING:
        failures.append("diagnosis missing fields changed")
    if diagnosis.get("candidate_equals_invalid_artifact") is not True:
        failures.append("diagnosis must prove candidate equals invalid artifact content")
    if diagnosis.get("classification") != "schema_incomplete":
        failures.append("diagnosis classification mismatch")
    try:
        historical_source_hashes = {
            "schema_sha256": historical_sha256(ITER65_SOURCE_COMMIT, SCHEMA),
            "proof_module_sha256": historical_sha256(
                ITER65_SOURCE_COMMIT, PROOF_MODULE
            ),
            "validator_sha256": historical_sha256(ITER65_SOURCE_COMMIT, VALIDATOR),
        }
    except RuntimeError as exc:
        failures.append(str(exc))
    else:
        for field, expected in historical_source_hashes.items():
            if diagnosis.get(field) != expected:
                failures.append(f"historical {field.removesuffix('_sha256')} hash mismatch")
    if diagnosis.get("iter64_candidate_sha256") != sha256(ITER64_CANDIDATE):
        failures.append("iter64 candidate hash mismatch")
    diagnosis_validation = diagnosis.get("diagnosis_validation", {})
    if diagnosis_validation.get("returncode") != 1:
        failures.append("diagnosis validation must fail on the iter64 candidate")
    if "missing fields: agent_id, benchmark_id, evidence" not in diagnosis_validation.get("stdout", ""):
        failures.append("diagnosis validation output missing expected error")

    if fixture.get("validator_result", {}).get("returncode") != 0:
        failures.append("fixture validator command must pass")
    if fixture.get("valid_fixture_passed") is not True:
        failures.append("valid fixture must pass")
    if fixture.get("malformed_fixture_failed") is not True:
        failures.append("malformed fixture must fail")
    if fixture.get("malformed_observed_error") != "missing fields: sha256":
        failures.append("malformed fixture error changed")
    if summary.get("redaction_scan_passed") is not True or summary.get("redaction_findings") != []:
        failures.append("redaction scan must pass with no findings")

    for rel_path, digest in summary.get("artifact_hashes", {}).items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"summary hash path missing: {rel_path}")
        elif sha256(path) != digest:
            failures.append(f"summary hash mismatch: {rel_path}")


def audit_overlay_and_fixtures(failures: list[str]) -> None:
    overlay = OVERLAY.read_text(encoding="utf-8")
    for field in REQUIRED_FIELDS:
        if field not in overlay:
            failures.append(f"overlay missing required receipt field: {field}")
    for required in [
        "hashlib.sha256",
        "sort_keys=True",
        'separators=(",", ":")',
        'if k != "sha256"',
        "Do not add top-level fields",
        "goal",
        "files_changed",
        "evidence_artifacts",
    ]:
        if required not in overlay:
            failures.append(f"overlay missing required instruction: {required}")
    try:
        load_receipt(VALID_FIXTURE)
    except ProofValidationError as exc:
        failures.append(f"valid fixture failed receipt validation: {exc}")
    try:
        load_receipt(TEMPLATE)
    except ProofValidationError as exc:
        failures.append(f"receipt template failed receipt validation: {exc}")
    try:
        load_receipt(INVALID_FIXTURE)
    except ProofValidationError as exc:
        if str(exc) != "missing fields: sha256":
            failures.append(f"invalid fixture failed for unexpected reason: {exc}")
    else:
        failures.append("invalid fixture unexpectedly passed")


def audit_receipt_and_text(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    try:
        receipt = load_receipt(RECEIPT)
    except ProofValidationError as exc:
        failures.append(f"gate receipt invalid: {exc}")
        return
    if receipt.status != summary.get("status"):
        failures.append("gate receipt status mismatch")

    result = RESULT.read_text(encoding="utf-8")
    review = (PROOF / "review.md").read_text(encoding="utf-8")
    command_output = (PROOF / "command_output.txt").read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`.",
        "provider API calls: `0`",
        "provider spend: `$0.00`",
        "It is not a benchmark result",
        "state-of-the-art result",
        "only authorizes the claim",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for forbidden in [
        "This is a benchmark result",
        "This is a state-of-the-art result",
        "This is a model-superiority result",
        "This is a leaderboard result",
        "Telos improves benchmark performance",
    ]:
        if forbidden in result or forbidden in review:
            failures.append(f"claim boundary regression: {forbidden}")
    if "receipt schema prompt alignment: pass" not in command_output:
        failures.append("command output missing status line")


def audit_secrets(failures: list[str]) -> None:
    for path in text_files(EXPERIMENT):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"secret-like or identifier residue in {path}")
                break


def main() -> int:
    failures: list[str] = []
    audit_required_files(failures)
    if not failures:
        audit_summary_report_and_diagnosis(failures)
        audit_overlay_and_fixtures(failures)
        audit_receipt_and_text(failures)
        audit_secrets(failures)
    if failures:
        print("iter65 receipt schema prompt alignment audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter65 receipt schema prompt alignment audit: clean artifact packet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
