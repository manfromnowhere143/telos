#!/usr/bin/env python3
"""Audit iter64 provider-compatible paid execution artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter64_provider_compatible_paid_execution_after_access_path_recovery")
PROOF = EXPERIMENT / "proof"
RAW = PROOF / "raw"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
REPORT = PROOF / "protocol_effect_report.json"
PREFLIGHT = PROOF / "preflight.json"
RECEIPT = PROOF / "valid" / "receipt_provider_compatible_paid_execution_after_access_path_recovery.json"
BASELINE_PAIR = "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml"
TELOS_PAIR = "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml"
SELECTED_PAIRS = [BASELINE_PAIR, TELOS_PAIR]
VALID_STATUSES = {"pass", "blocked", "fail"}
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"Bearer\s+(?!\$\{TELOS_VERTEX_BEARER_TOKEN\}|\[REDACTED_BEARER_TOKEN\])\S+"),
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
        PREFLIGHT,
        PROOF / "runtime_access_path_binding.json",
        PROOF / "runtime_access_path_model_config.yaml",
        PROOF / "overlay_materialization_manifest.json",
        PROOF / "command_output.txt",
        PROOF / "review.md",
        PROOF / "learning_record.json",
        RECEIPT,
    ]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")


def audit_summary_and_report(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    report = load_json(REPORT)
    preflight = load_json(PREFLIGHT)
    binding = load_json(PROOF / "runtime_access_path_binding.json")
    overlay = load_json(PROOF / "overlay_materialization_manifest.json")

    status = summary.get("status")
    if status not in VALID_STATUSES:
        failures.append(f"invalid summary status: {status!r}")
        return
    if report.get("status") != status:
        failures.append(f"report status {report.get('status')!r} does not match summary {status!r}")
    if summary.get("experiment_id") != EXPERIMENT.name or report.get("experiment_id") != EXPERIMENT.name:
        failures.append("experiment id mismatch")
    if summary.get("schema_version") != "telos.provider_compatible_paid_execution.summary.v1":
        failures.append("unexpected summary schema")
    if report.get("schema_version") != "telos.provider_compatible_paid_execution.report.v1":
        failures.append("unexpected report schema")

    expected_false = [
        "gpu_used",
        "sentinel_named_resources_modified",
        "cloud_runner_started",
        "teardown_required",
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "production_or_live_domain_changed",
    ]
    for key in expected_false:
        if summary.get(key) is not False:
            failures.append(f"summary {key} must be false")
        if key in report and report.get(key) is not False:
            failures.append(f"report {key} must be false")

    if summary.get("provider_call_ceiling") != 16 or report.get("provider_call_ceiling") != 16:
        failures.append("provider call ceiling must remain 16")
    if summary.get("provider_spend_ceiling_usd") != 10.0 or report.get("provider_spend_ceiling_usd") != 10.0:
        failures.append("provider spend ceiling must remain 10.0")
    if float(summary.get("provider_cost_usd", 0.0)) > 10.0 and "provider_spend_ceiling_exceeded" not in summary.get("failures", []):
        failures.append("cost exceeded ceiling without recorded failure")
    if int(summary.get("provider_api_calls", 0)) > 16 and "provider_call_ceiling_exceeded" not in summary.get("failures", []):
        failures.append("call count exceeded ceiling without recorded failure")
    if summary.get("redaction_scan_passed") is not True or summary.get("redaction_findings") != []:
        failures.append("redaction scan must pass with no findings before publication")

    if preflight.get("iter63_status") != "pass" or preflight.get("iter63_clean_pass") is not True:
        failures.append("preflight must prove iter63 was a clean access-path recovery pass")
    if preflight.get("iter63_blocker_classification") != "access_path_recovered":
        failures.append("preflight must prove iter63 recovered the access path")
    if preflight.get("iter63_direct_rest_probe_status") != "pass":
        failures.append("preflight must prove iter63 direct REST probe passed")
    if preflight.get("iter63_litellm_parity_probe_status") != "pass":
        failures.append("preflight must prove iter63 LiteLLM parity probe passed")
    if preflight.get("iter63_receipt_validation_returncode") != 0:
        failures.append("preflight must revalidate the iter63 receipt")
    for key in [
        "iter63_status",
        "iter63_clean_pass",
        "iter63_blocker_classification",
        "iter63_direct_rest_probe_status",
        "iter63_litellm_parity_probe_status",
        "iter63_receipt_validation_returncode",
        "runtime_overlay_all_materialized",
        "runtime_overlay_copied_hashes_match",
        "runtime_model_config_materialized",
        "runtime_model_config_has_secret_values_only_in_tmp",
        "runtime_env_values_committed",
    ]:
        if summary.get(key) != preflight.get(key) and key != "runtime_env_values_committed":
            failures.append(f"summary/preflight mismatch for {key}")
    if summary.get("runtime_env_values_committed") is not False:
        failures.append("runtime env values must not be committed")
    if binding.get("token_committed") is not False or binding.get("project_identifier_committed") is not False:
        failures.append("runtime binding must not commit token or project identifiers")
    if binding.get("credential_material_committed") is not False:
        failures.append("runtime binding must not commit credential material")
    if overlay.get("all_materialized") != preflight.get("runtime_overlay_all_materialized"):
        failures.append("overlay materialization/preflight mismatch")
    if overlay.get("runtime_model_config_has_secret_values_only_in_tmp") != preflight.get(
        "runtime_model_config_has_secret_values_only_in_tmp"
    ):
        failures.append("runtime model config secret-boundary mismatch")
    if preflight.get("runtime_overlay_all_materialized") is not True:
        if status != "blocked" or "runtime_overlay_not_materialized" not in summary.get("blockers", []):
            failures.append("runtime overlay regression must publish as the named blocker")
    if preflight.get("selected_pair_ids") != SELECTED_PAIRS:
        failures.append("preflight selected pairs changed")
    if preflight.get("excluded_pair_selected") is not False:
        failures.append("preflight selected an excluded pair")
    if preflight.get("codeclash_commit_matches_expected") is not True:
        failures.append("preflight must prove the pinned CodeClash commit")
    if preflight.get("codeclash_google_auth_import_ready") is not True:
        if status != "blocked" or "codeclash_vertex_google_auth_dependency_missing" not in summary.get("blockers", []):
            failures.append("google.auth import regression must publish as the named blocker")

    row_results = report.get("row_results", [])
    if not isinstance(row_results, list):
        failures.append("row_results must be a list")
        row_results = []
    row_ids = [row.get("pair_id") for row in row_results if isinstance(row, dict)]
    if summary.get("executed_pair_ids") != row_ids or report.get("executed_pair_ids") != row_ids:
        failures.append("executed pair ids must match row_results order")
    if summary.get("executed_pair_count") != len(row_ids) or report.get("executed_pair_count") != len(row_ids):
        failures.append("executed pair count mismatch")
    recovered_row_ids = [
        row.get("pair_id")
        for row in row_results
        if isinstance(row, dict) and row.get("recovered_after_verifier_crash") is True
    ]
    if summary.get("recovered_after_verifier_crash_pair_ids") != recovered_row_ids:
        failures.append("summary recovered pair ids must match row results")
    if report.get("recovered_after_verifier_crash_pair_ids") != recovered_row_ids:
        failures.append("report recovered pair ids must match row results")
    if summary.get("verifier_crash_recovery_used") != bool(recovered_row_ids):
        failures.append("summary verifier recovery flag mismatch")
    if report.get("verifier_crash_recovery_used") != bool(recovered_row_ids):
        failures.append("report verifier recovery flag mismatch")
    if summary.get("excluded_pair_executed") is not False or report.get("excluded_pair_executed") is not False:
        failures.append("excluded pairs must remain unexecuted")

    metric = summary.get("primary_metric", {})
    expected_metric_keys = {
        "baseline_verified_completion_evidence",
        "telos_verified_completion_evidence",
        "verified_completion_evidence_delta_telos_minus_baseline",
    }
    if set(metric) != expected_metric_keys:
        failures.append(f"primary metric keys changed: {sorted(metric)}")

    if status == "pass":
        if row_ids != SELECTED_PAIRS:
            failures.append("pass requires exactly the two selected pair ids")
        if summary.get("clean_pass") is not True or summary.get("blocked_result") is not False or summary.get("quality_failure") is not False:
            failures.append("pass status booleans are inconsistent")
        if summary.get("blockers") != [] or summary.get("failures") != []:
            failures.append("pass must have no blockers or failures")
        telos_row = next((row for row in row_results if row.get("pair_id") == TELOS_PAIR), {})
        if telos_row.get("receipt_validation_returncode") is None:
            failures.append("Telos receipt validation must run before completion evidence is accepted")
    elif status == "blocked":
        if summary.get("clean_pass") is not False or summary.get("blocked_result") is not True or summary.get("quality_failure") is not False:
            failures.append("blocked status booleans are inconsistent")
        if not summary.get("blockers"):
            failures.append("blocked result must name at least one blocker")
        if summary.get("failures") != []:
            failures.append("blocked result must not hide failures")
    elif status == "fail":
        if summary.get("clean_pass") is not False or summary.get("blocked_result") is not False or summary.get("quality_failure") is not True:
            failures.append("fail status booleans are inconsistent")
        if not summary.get("failures"):
            failures.append("fail result must name at least one failure")

    for rel_path, digest in summary.get("artifact_hashes", {}).items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"summary hash path missing: {rel_path}")
        elif sha256(path) != digest:
            failures.append(f"summary hash mismatch: {rel_path}")


def audit_receipt_and_text(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    status = summary.get("status")
    try:
        receipt = load_receipt(RECEIPT)
        if receipt.status != status:
            failures.append(f"receipt status {receipt.status!r} does not match {status!r}")
    except ProofValidationError as exc:
        failures.append(f"receipt validation failed: {exc}")

    result = RESULT.read_text(encoding="utf-8")
    review = (PROOF / "review.md").read_text(encoding="utf-8")
    command_output = (PROOF / "command_output.txt").read_text(encoding="utf-8")
    for required in [
        f"Status: `{str(status).upper()}`.",
        "provider API calls:",
        "runtime env values committed: `false`",
        "verifier-crash recovery used:",
        "It is not a benchmark result",
        "state-of-the-art result",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for forbidden in [
        "This is a benchmark result",
        "This is a state-of-the-art result",
        "This is a model-superiority result",
        "This is a leaderboard result",
    ]:
        if forbidden in result or forbidden in review:
            failures.append(f"claim boundary regression: {forbidden}")
    if f"provider-compatible paid execution after access path recovery: {status}" not in command_output:
        failures.append("command output missing status line")


def audit_raw_artifacts(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    report = load_json(REPORT)
    if summary.get("executed_pair_count", 0) == 0:
        return
    for row in report.get("row_results", []):
        if not isinstance(row, dict):
            failures.append("row result must be an object")
            continue
        pair_id = row.get("pair_id")
        raw_dir = RAW / str(pair_id)
        for required in ["command_execution.json", "command_stdout.txt", "command_stderr.txt", "raw_manifest.json"]:
            if not (raw_dir / required).exists():
                failures.append(f"{pair_id} missing raw artifact {required}")
        if row.get("raw_evidence_present") is True:
            for required in ["metadata.json", "players/p1/p1_r1.traj.json"]:
                if not (raw_dir / required).exists():
                    failures.append(f"{pair_id} marked raw evidence present but missing {required}")
        if pair_id == TELOS_PAIR and row.get("receipt_validation_returncode") is not None:
            if not (
                raw_dir / "valid" / "telos_completion_receipt.json"
            ).exists() and not (
                raw_dir / "invalid" / "telos_completion_receipt.json"
            ).exists():
                failures.append("Telos row receipt validation ran without committed valid/invalid receipt artifact")


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
        audit_summary_and_report(failures)
        audit_receipt_and_text(failures)
        audit_raw_artifacts(failures)
        audit_secrets(failures)
    if failures:
        print("iter64 provider-compatible paid execution after access path recovery audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter64 provider-compatible paid execution after access path recovery audit: clean artifact packet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
