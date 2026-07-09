#!/usr/bin/env python3
"""Audit iter57 provider-compatible paid execution artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter57_provider_compatible_paid_execution_after_auth_recovery")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
REPORT = PROOF / "protocol_effect_report.json"
PREFLIGHT = PROOF / "preflight.json"
DEPENDENCY = PROOF / "dependency_block_evidence.json"
RECEIPT = PROOF / "valid" / "receipt_provider_compatible_paid_execution_after_auth_recovery.json"
BASELINE_PAIR = "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml"
TELOS_PAIR = "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml"
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
TEXT_SUFFIXES = {".json", ".jsonl", ".log", ".txt", ".md", ".yaml", ".yml", ".py"}


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be an object")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix in TEXT_SUFFIXES else []
    return [candidate for candidate in path.rglob("*") if candidate.is_file() and candidate.suffix in TEXT_SUFFIXES]


def audit_summary_and_report(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    report = load_json(REPORT)
    dependency = load_json(DEPENDENCY)
    preflight = load_json(PREFLIGHT)
    expected_summary = {
        "schema_version": "telos.provider_compatible_paid_execution.summary.v1",
        "status": "blocked",
        "executed_pair_count": 0,
        "executed_pair_ids": [],
        "attempted_pair_ids": [BASELINE_PAIR],
        "excluded_pair_executed": False,
        "provider_api_calls": 0,
        "provider_call_ceiling": 16,
        "provider_cost_usd": 0,
        "provider_spend_ceiling_usd": 10.0,
        "gpu_used": False,
        "sentinel_named_resources_modified": False,
        "cloud_runner_started": False,
        "teardown_required": False,
        "redaction_scan_passed": True,
        "redaction_findings": [],
        "clean_pass": False,
        "blocked_result": True,
        "quality_failure": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "production_or_live_domain_changed": False,
        "blockers": ["codeclash_vertex_google_auth_dependency_missing"],
        "failures": [],
    }
    for key, value in expected_summary.items():
        if summary.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {summary.get(key)!r}")
    metric = summary.get("primary_metric", {})
    if metric != {
        "baseline_verified_completion_evidence": False,
        "telos_verified_completion_evidence": False,
        "verified_completion_evidence_delta_telos_minus_baseline": 0,
    }:
        failures.append(f"unexpected primary metric: {metric!r}")
    if report.get("status") != "blocked" or report.get("provider_api_calls") != 0:
        failures.append("report must be blocked with zero provider calls")
    if report.get("executed_pair_count") != 0 or report.get("attempted_pair_ids") != [BASELINE_PAIR]:
        failures.append("report must record only the interrupted baseline attempt")
    if preflight.get("iter56_status") != "pass" or preflight.get("iter56_receipt_validation_returncode") != 0:
        failures.append("preflight must prove iter56 passed and receipt validation ran")
    if preflight.get("codeclash_google_auth_import_ready") is not False:
        failures.append("preflight must record missing google.auth dependency")
    if preflight.get("adc_access_token_available") is not True or preflight.get("docker_ready") is not True:
        failures.append("preflight must keep ADC and Docker readiness separate from dependency blocker")
    expected_dependency = {
        "schema_version": "telos.provider_compatible_paid_execution.dependency_block.v1",
        "attempted_pair_id": BASELINE_PAIR,
        "telos_pair_attempted": False,
        "missing_dependency": "google.auth",
        "missing_dependency_seen_in_log": True,
        "provider_api_calls_observed_in_partial_metadata": 0,
        "provider_cost_usd_observed_in_partial_metadata": 0.0,
    }
    for key, value in expected_dependency.items():
        if dependency.get(key) != value:
            failures.append(f"dependency {key} expected {value!r}, got {dependency.get(key)!r}")
    copied = set(dependency.get("copied_raw_files", []))
    for required in {"metadata.json", "everything.log", "rounds/round_0/results.json"}:
        if required not in copied:
            failures.append(f"dependency evidence missing copied raw file: {required}")
    hashes = summary.get("artifact_hashes", {})
    for rel_path, digest in hashes.items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"summary hash path missing: {rel_path}")
        elif sha256(path) != digest:
            failures.append(f"summary hash mismatch: {rel_path}")


def audit_receipt_and_text(failures: list[str]) -> None:
    try:
        receipt = load_receipt(RECEIPT)
        if receipt.status != "blocked":
            failures.append(f"receipt status expected blocked, got {receipt.status}")
    except ProofValidationError as exc:
        failures.append(f"receipt validation failed: {exc}")
    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `BLOCKED`.",
        "could not import `google.auth`",
        "provider API calls: `0`",
        "It is not a benchmark result",
        "state-of-the-art result",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    review = (PROOF / "review.md").read_text(encoding="utf-8")
    if TELOS_PAIR not in review and "Telos selected row" not in review:
        failures.append("review must record that the Telos row was not attempted")


def audit_secrets(failures: list[str]) -> None:
    for path in text_files(EXPERIMENT):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"secret-like or identifier residue in {path}")
                break


def main() -> int:
    failures: list[str] = []
    for path in [RESULT, SUMMARY, REPORT, PREFLIGHT, DEPENDENCY, RECEIPT]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")
    if not failures:
        audit_summary_and_report(failures)
        audit_receipt_and_text(failures)
        audit_secrets(failures)
    if failures:
        print("iter57 provider-compatible paid execution audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter57 provider-compatible paid execution audit: clean blocked result")
    return 0


if __name__ == "__main__":
    sys.exit(main())
