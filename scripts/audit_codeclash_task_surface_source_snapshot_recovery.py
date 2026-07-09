#!/usr/bin/env python3
"""Audit iter69 CodeClash task-surface source snapshot recovery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter69_codeclash_task_surface_source_snapshot_recovery")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
REPORT = PROOF / "source_snapshot_report.json"
SUMMARY = PROOF / "run_summary.json"
RECEIPT = PROOF / "valid" / "receipt_codeclash_task_surface_source_snapshot_recovery.json"
PROOF_SNAPSHOT = PROOF / "source_snapshots/codeclash/configs/test/dummy.yaml"
CANONICAL_SNAPSHOT = Path("experiments/source_snapshots/codeclash/configs/test/dummy.yaml")
NEXT_GATE = Path("experiments/iter70_provider_compatible_expanded_adapter_completion/HYPOTHESIS.md")
EXPECTED_COMMIT = "381cdfa05a35e8acd35853b9fc7e13005121b127"
EXPECTED_SHA256 = "b8e856447fc71c79bb5e042dc530127480d670d84fd51c03e2c2e7f58c630e97"
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


def text_files(path: Path) -> list[Path]:
    return [
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file() and candidate.suffix in TEXT_SUFFIXES
    ]


def audit_required_files(failures: list[str]) -> None:
    for path in [
        RESULT,
        REPORT,
        SUMMARY,
        PROOF / "command_output.txt",
        PROOF / "review.md",
        PROOF / "learning_record.json",
        RECEIPT,
        PROOF_SNAPSHOT,
        CANONICAL_SNAPSHOT,
        NEXT_GATE,
    ]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")


def audit_report_summary(failures: list[str]) -> None:
    report = load_json(REPORT)
    summary = load_json(SUMMARY)
    if report.get("schema_version") != "telos.codeclash_task_surface_source_snapshot_recovery.report.v1":
        failures.append("unexpected report schema")
    if summary.get("schema_version") != "telos.codeclash_task_surface_source_snapshot_recovery.summary.v1":
        failures.append("unexpected summary schema")
    if report.get("status") != "pass" or summary.get("status") != "pass":
        failures.append("iter69 must publish a pass result")
    if summary.get("clean_pass") is not True:
        failures.append("clean_pass must be true")
    if summary.get("blocked_result") is not False or summary.get("quality_failure") is not False:
        failures.append("blocked/quality booleans are inconsistent")
    if report.get("blockers") != [] or summary.get("blockers") != []:
        failures.append("iter69 pass must have no blockers")
    if report.get("failures") != [] or summary.get("failures") != []:
        failures.append("iter69 pass must have no failures")
    if report.get("iter68_status") != "blocked":
        failures.append("iter68 prerequisite must be blocked")
    if report.get("iter68_blocker_committed_dummy_source_surface_missing") is not True:
        failures.append("iter68 source-snapshot blocker must be recorded")
    if summary.get("next_gate") != str(NEXT_GATE):
        failures.append("next gate changed")

    checkout = report.get("codeclash_checkout", {})
    if checkout.get("actual_commit") != EXPECTED_COMMIT:
        failures.append("unexpected CodeClash commit")
    if checkout.get("commit_matches_expected") is not True:
        failures.append("CodeClash commit must match expected")
    if checkout.get("source_status_lines") != []:
        failures.append("Dummy source path must be clean in the pinned checkout")
    if checkout.get("working_tree_source_matches_blob") is not True:
        failures.append("working-tree source must match the pinned Git blob")

    snapshots = report.get("snapshots", [])
    if len(snapshots) != 1:
        failures.append("expected exactly one source snapshot")
        return
    snapshot = snapshots[0]
    for key in [
        "source_blob_sha256",
        "canonical_snapshot_sha256",
        "proof_snapshot_sha256",
    ]:
        if snapshot.get(key) != EXPECTED_SHA256:
            failures.append(f"{key} expected {EXPECTED_SHA256}, got {snapshot.get(key)}")
    for key in [
        "canonical_hash_matches_source",
        "proof_hash_matches_source",
        "canonical_hash_matches_proof",
        "task_surface_evidence_only",
    ]:
        if snapshot.get(key) is not True:
            failures.append(f"snapshot {key} must be true")
    if snapshot.get("execution_result") is not False:
        failures.append("snapshot must not be presented as execution result")

    if sha256(CANONICAL_SNAPSHOT) != EXPECTED_SHA256:
        failures.append("canonical source snapshot hash mismatch")
    if sha256(PROOF_SNAPSHOT) != EXPECTED_SHA256:
        failures.append("proof source snapshot hash mismatch")
    if CANONICAL_SNAPSHOT.read_text(encoding="utf-8") != PROOF_SNAPSHOT.read_text(encoding="utf-8"):
        failures.append("canonical and proof source snapshots differ")

    for key, expected in [
        ("provider_api_calls", 0),
        ("provider_spend_usd", 0.0),
        ("row_execution_allowed", False),
        ("gpu_used", False),
        ("cloud_runner_started", False),
        ("sentinel_named_resources_modified", False),
        ("production_or_live_domain_changed", False),
        ("benchmark_result_claimed", False),
        ("leaderboard_or_swebench_result_claimed", False),
        ("model_superiority_claimed", False),
        ("state_of_the_art_result_claimed", False),
        ("copied_source_files_are_task_surface_evidence_only", True),
        ("copied_source_files_are_execution_results", False),
        ("next_paid_gate_authorized", False),
    ]:
        if summary.get(key) != expected:
            failures.append(f"summary {key} expected {expected!r}, got {summary.get(key)!r}")
        if key in report and report.get(key) != expected:
            failures.append(f"report {key} expected {expected!r}, got {report.get(key)!r}")

    if summary.get("redaction_scan_passed") is not True or summary.get("redaction_findings") != []:
        failures.append("redaction scan must pass with no findings")
    for rel_path, digest in summary.get("artifact_hashes", {}).items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"summary hash path missing: {rel_path}")
        elif sha256(path) != digest:
            failures.append(f"summary hash mismatch: {rel_path}")
    if summary.get("canonical_source_snapshot_sha256") != EXPECTED_SHA256:
        failures.append("canonical_source_snapshot_sha256 mismatch")


def audit_receipt_and_text(failures: list[str]) -> None:
    try:
        receipt = load_receipt(RECEIPT)
    except ProofValidationError as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.status != "pass":
        failures.append("receipt status must be pass")

    result = RESULT.read_text(encoding="utf-8")
    review = (PROOF / "review.md").read_text(encoding="utf-8")
    command_output = (PROOF / "command_output.txt").read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`.",
        "source evidence for `configs/test/dummy.yaml`",
        "copied source is execution evidence: `false`",
        "This is not a benchmark result",
        "state-of-the-art result",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "recovers only source-task evidence",
        "hash equality",
        "not execution evidence",
        "No provider model call",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "provider_api_calls=0",
        "provider_spend_usd=0.00",
        f"snapshot_sha256={EXPECTED_SHA256}",
        "task_surface_evidence_only=true",
        "copied_source_files_are_execution_results=false",
    ]:
        if required not in command_output:
            failures.append(f"command output missing required line: {required}")


def audit_redaction(failures: list[str]) -> None:
    findings = []
    for path in [CANONICAL_SNAPSHOT, *text_files(EXPERIMENT)]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(str(path))
                break
    if findings:
        failures.append(f"secret/redaction patterns found: {findings}")


def main() -> int:
    failures: list[str] = []
    audit_required_files(failures)
    if not failures:
        audit_report_summary(failures)
        audit_receipt_and_text(failures)
        audit_redaction(failures)
    if failures:
        print("iter69 CodeClash task-surface source snapshot recovery audit FAILED")
        for failure in failures:
            print(f" - {failure}")
        return 1
    print("iter69 CodeClash task-surface source snapshot recovery audit: clean pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
