#!/usr/bin/env python3
"""Audit iter72 provider-compatible expanded paid-execution artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path(
    "experiments/iter72_provider_compatible_expanded_paid_execution_after_slice_refreeze"
)
PROOF = EXPERIMENT / "proof"
RAW = PROOF / "raw"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
REPORT = PROOF / "protocol_effect_report.json"
PREFLIGHT = PROOF / "preflight.json"
OVERLAY = PROOF / "overlay_materialization_manifest.json"
RECEIPT = (
    PROOF
    / "valid"
    / "receipt_provider_compatible_expanded_paid_execution_after_slice_refreeze.json"
)
EXPECTED_SELECTED_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-dummy-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
    "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
]
EXPECTED_RETAINED_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
]
EXPECTED_BLOCKERS = [
    "provider_command_nonzero_returncode",
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml_receipt_not_valid",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml_receipt_not_valid",
]
EXPECTED_PRIMARY_METRIC = {
    "dummy_baseline_verified_completion_evidence": False,
    "dummy_telos_verified_completion_evidence": False,
    "dummy_delta_telos_minus_baseline": 0,
    "deterministic_edit_baseline_verified_completion_evidence": True,
    "deterministic_edit_telos_verified_completion_evidence": False,
    "deterministic_edit_delta_telos_minus_baseline": -1,
}
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
        SUMMARY,
        REPORT,
        PREFLIGHT,
        OVERLAY,
        PROOF / "runtime_access_path_binding.json",
        PROOF / "runtime_access_path_model_config.yaml",
        PROOF / "command_output.txt",
        PROOF / "review.md",
        PROOF / "learning_record.json",
        RECEIPT,
    ]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")
    for pair_id in EXPECTED_SELECTED_PAIR_IDS:
        raw_dir = RAW / pair_id
        if not raw_dir.exists():
            failures.append(f"missing raw packet: {raw_dir}")


def audit_summary_report_preflight(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    report = load_json(REPORT)
    preflight = load_json(PREFLIGHT)
    overlay = load_json(OVERLAY)

    expected_schemas = {
        "summary": (
            summary,
            "telos.provider_compatible_expanded_paid_execution.summary.v1",
        ),
        "report": (
            report,
            "telos.provider_compatible_expanded_paid_execution.report.v1",
        ),
        "preflight": (
            preflight,
            "telos.provider_compatible_expanded_paid_execution.preflight.v1",
        ),
    }
    for name, (packet, expected_schema) in expected_schemas.items():
        if packet.get("schema_version") != expected_schema:
            failures.append(f"unexpected {name} schema")
        if packet.get("experiment_id") not in {None, EXPERIMENT.name}:
            failures.append(f"{name} experiment id mismatch")

    for packet_name, packet in [("summary", summary), ("report", report)]:
        if packet.get("status") != "blocked":
            failures.append(f"{packet_name} must publish blocked status")
        if packet.get("blockers") != EXPECTED_BLOCKERS:
            failures.append(f"{packet_name} blockers changed")
        if packet.get("failures") != []:
            failures.append(f"{packet_name} failures must be empty for a clean block")
        for key in [
            "gpu_used",
            "cloud_runner_started",
            "sentinel_named_resources_modified",
            "production_or_live_domain_changed",
            "benchmark_result_claimed",
            "leaderboard_or_swebench_result_claimed",
            "model_superiority_claimed",
            "state_of_the_art_result_claimed",
            "cross_task_surface_pooling_authorized",
            "aggregate_benchmark_or_model_claim_authorized",
        ]:
            if key in packet and packet.get(key) is not False:
                failures.append(f"{packet_name} {key} must be false")

    if summary.get("clean_pass") is not False:
        failures.append("summary clean_pass must be false")
    if summary.get("blocked_result") is not True or summary.get("quality_failure") is not False:
        failures.append("summary blocked/quality booleans are inconsistent")
    if summary.get("selected_pair_ids") != EXPECTED_SELECTED_PAIR_IDS:
        failures.append("summary selected pair ids changed")
    if summary.get("executed_pair_ids") != EXPECTED_SELECTED_PAIR_IDS:
        failures.append("summary executed pair ids changed")
    if report.get("selected_pair_ids") != EXPECTED_SELECTED_PAIR_IDS:
        failures.append("report selected pair ids changed")
    if report.get("executed_pair_ids") != EXPECTED_SELECTED_PAIR_IDS:
        failures.append("report executed pair ids changed")
    if preflight.get("selected_pair_ids") != EXPECTED_SELECTED_PAIR_IDS:
        failures.append("preflight selected pair ids changed")
    if summary.get("executed_pair_count") != 4 or report.get("executed_pair_count") != 4:
        failures.append("exactly four adapter rows must execute")
    if summary.get("retained_existing_pair_ids") != EXPECTED_RETAINED_PAIR_IDS:
        failures.append("summary retained pair ids changed")
    if report.get("retained_existing_pair_ids") != EXPECTED_RETAINED_PAIR_IDS:
        failures.append("report retained pair ids changed")
    if preflight.get("retained_existing_pair_ids") != EXPECTED_RETAINED_PAIR_IDS:
        failures.append("preflight retained pair ids changed")

    if summary.get("provider_api_calls") != 17 or report.get("provider_api_calls") != 17:
        failures.append("provider call count changed")
    if summary.get("provider_call_ceiling") != 32 or report.get("provider_call_ceiling") != 32:
        failures.append("provider call ceiling changed")
    if summary.get("provider_api_calls", 10**9) > summary.get("provider_call_ceiling", -1):
        failures.append("provider call ceiling exceeded")
    for packet_name, packet in [("summary", summary), ("report", report)]:
        cost = float(packet.get("provider_cost_usd", -1.0))
        ceiling = float(packet.get("provider_spend_ceiling_usd", -1.0))
        if abs(cost - 0.057646) > 1e-9:
            failures.append(f"{packet_name} provider cost changed")
        if ceiling != 10.0:
            failures.append(f"{packet_name} spend ceiling changed")
        if cost > ceiling:
            failures.append(f"{packet_name} spend ceiling exceeded")
        if packet.get("per_row_call_limit") != 8:
            failures.append(f"{packet_name} per-row call limit changed")
        if float(packet.get("per_row_spend_limit_usd", -1.0)) != 2.5:
            failures.append(f"{packet_name} per-row spend limit changed")

    if summary.get("primary_metric") != EXPECTED_PRIMARY_METRIC:
        failures.append(f"summary primary metric changed: {summary.get('primary_metric')}")
    if report.get("primary_metric") != EXPECTED_PRIMARY_METRIC:
        failures.append(f"report primary metric changed: {report.get('primary_metric')}")
    if summary.get("redaction_scan_passed") is not True or summary.get("redaction_findings") != []:
        failures.append("summary redaction scan must pass with no findings")
    if report.get("redaction_scan_passed") is not True or report.get("redaction_findings") != []:
        failures.append("report redaction scan must pass with no findings")

    for key, expected in [
        ("iter71_status", "pass"),
        ("iter71_clean_pass", True),
        ("iter71_receipt_validation_returncode", 0),
        ("iter71_audit_returncode", 0),
        ("runtime_model_config_materialized", True),
        ("runtime_overlay_all_materialized", True),
        ("runtime_overlay_copied_hashes_match", True),
        ("runtime_model_config_has_secret_values_only_in_tmp", True),
        ("runtime_env_values_committed", False),
    ]:
        if summary.get(key) != expected:
            failures.append(f"summary {key} expected {expected!r}, got {summary.get(key)!r}")
        if key in preflight and preflight.get(key) != expected:
            failures.append(f"preflight {key} expected {expected!r}, got {preflight.get(key)!r}")
    if preflight.get("codeclash_commit_matches_expected") is not True:
        failures.append("CodeClash commit preflight mismatch")
    if preflight.get("docker_ready") is not True:
        failures.append("Docker preflight should be ready")
    if preflight.get("adc_access_token_available") is not True:
        failures.append("ADC token preflight should be available")
    if overlay.get("all_materialized") is not True or overlay.get("copied_hashes_match") is not True:
        failures.append("overlay materialization must pass with matching hashes")
    if overlay.get("runtime_model_config_has_secret_values_only_in_tmp") is not True:
        failures.append("overlay runtime secret boundary must hold")

    row_results = report.get("row_results", [])
    if len(row_results) != 4:
        failures.append("row_results must contain four rows")
    rows = {row.get("pair_id"): row for row in row_results if isinstance(row, dict)}
    if list(rows) != EXPECTED_SELECTED_PAIR_IDS:
        failures.append("row result order changed")
    for pair_id in EXPECTED_SELECTED_PAIR_IDS:
        row = rows.get(pair_id, {})
        if row.get("pair_id") != pair_id:
            failures.append(f"{pair_id} missing from row_results")
            continue
        if row.get("provider_api_calls", 10**9) > 8:
            failures.append(f"{pair_id} exceeded per-row call limit")
        if float(row.get("provider_cost_usd", 10**9)) > 2.5:
            failures.append(f"{pair_id} exceeded per-row spend limit")
        if row.get("raw_evidence_present") is not True:
            failures.append(f"{pair_id} must preserve raw evidence")
        raw_dir = RAW / pair_id
        for required in ["command_execution.json", "command_stdout.txt", "command_stderr.txt", "raw_manifest.json", "metadata.json"]:
            if not (raw_dir / required).exists():
                failures.append(f"{pair_id} missing raw artifact {required}")

    expected_row_values = {
        "baseline-agent-completion-evidence__configs-test-dummy-yaml": {
            "command_returncode": 1,
            "receipt_required": False,
            "receipt_valid": False,
            "verified_completion_evidence": False,
            "provider_api_calls": 5,
        },
        "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml": {
            "command_returncode": 1,
            "receipt_required": True,
            "receipt_valid": False,
            "verified_completion_evidence": False,
            "provider_api_calls": 5,
        },
        "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml": {
            "command_returncode": 0,
            "receipt_required": False,
            "receipt_valid": False,
            "verified_completion_evidence": True,
            "provider_api_calls": 2,
        },
        "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml": {
            "command_returncode": 0,
            "receipt_required": True,
            "receipt_valid": False,
            "verified_completion_evidence": False,
            "provider_api_calls": 5,
        },
    }
    for pair_id, expectations in expected_row_values.items():
        row = rows.get(pair_id, {})
        for key, expected in expectations.items():
            if row.get(key) != expected:
                failures.append(f"{pair_id} {key} expected {expected!r}, got {row.get(key)!r}")
        if row.get("receipt_required") is True:
            if row.get("receipt_candidate_found") is not True:
                failures.append(f"{pair_id} must preserve invalid receipt candidate")
            if row.get("receipt_candidate_json_parseable") is not True:
                failures.append(f"{pair_id} receipt candidate must be parseable")
            if row.get("receipt_validation_returncode") != 1:
                failures.append(f"{pair_id} receipt validation must fail closed")
            if "missing fields" not in row.get("receipt_validation_stdout", ""):
                failures.append(f"{pair_id} receipt failure reason changed")

    for rel_path, expected_hash in summary.get("artifact_hashes", {}).items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"summary hash path missing: {rel_path}")
        elif sha256(path) != expected_hash:
            failures.append(f"summary hash mismatch: {rel_path}")


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
        "Status: `BLOCKED`.",
        "executed adapter row count: `4`",
        "retained BattleSnake rows rerun: `false`",
        "provider API calls: `17`",
        "provider cost from CodeClash metadata: `$0.05764600`",
        "benchmark/model/SOTA claim: `false`",
        "It is not a benchmark result",
        "state-of-the-art result",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "four adapter-planned rows",
        "were retained as prior iter66 evidence and were not rerun",
        "validation was required",
        "status: `blocked`",
        "No benchmark, SWE-bench, leaderboard",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "provider-compatible expanded paid execution after slice refreeze: blocked",
        "selected_pair_count=4",
        "executed_pair_count=4",
        "retained_battlesnake_rows_rerun=false",
        "provider_api_calls=17",
        "provider_call_ceiling=32",
        "provider_cost_usd=0.05764600",
        "provider_spend_ceiling_usd=10.00",
        "failures=",
    ]:
        if required not in command_output:
            failures.append(f"command output missing required line: {required}")
    for forbidden in [
        "This is a benchmark result",
        "This is a state-of-the-art result",
        "This is a model-superiority result",
        "This is a leaderboard result",
        "Telos outperforms baseline",
    ]:
        if forbidden in result or forbidden in review:
            failures.append(f"claim boundary regression: {forbidden}")


def audit_invalid_receipt_candidates(failures: list[str]) -> None:
    dummy = load_json(
        RAW
        / "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml"
        / "telos_completion_receipt_candidate.json"
    )
    edit = load_json(
        RAW
        / "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml"
        / "telos_completion_receipt_candidate.json"
    )
    if sorted(dummy) != ["sha256", "status"]:
        failures.append("Dummy invalid receipt candidate shape changed")
    if sorted(edit) != ["receipt", "sha256"]:
        failures.append("deterministic-edit invalid receipt candidate shape changed")
    if not (
        RAW
        / "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml"
        / "invalid"
        / "telos_completion_receipt.json"
    ).exists():
        failures.append("Dummy invalid receipt artifact missing")
    if not (
        RAW
        / "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml"
        / "invalid"
        / "telos_completion_receipt.json"
    ).exists():
        failures.append("deterministic-edit invalid receipt artifact missing")


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
        audit_summary_report_preflight(failures)
        audit_receipt_and_text(failures)
        audit_invalid_receipt_candidates(failures)
        audit_secrets(failures)
    if failures:
        print("iter72 provider-compatible expanded paid execution audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter72 provider-compatible expanded paid execution audit: clean blocked artifact packet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
