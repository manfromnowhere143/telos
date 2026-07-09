#!/usr/bin/env python3
"""Audit iter66 provider-compatible paid execution after receipt prompt alignment."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment")
PROOF = EXPERIMENT / "proof"
RAW = PROOF / "raw"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
REPORT = PROOF / "protocol_effect_report.json"
PREFLIGHT = PROOF / "preflight.json"
OVERLAY = PROOF / "overlay_materialization_manifest.json"
RECEIPT = PROOF / "valid" / "receipt_provider_compatible_paid_execution_after_receipt_prompt_alignment.json"
ITER65_OVERLAY = (
    Path("experiments/iter65_receipt_schema_prompt_alignment/proof/recovered_overlay/configs/mini")
    / "telos_vertex_gemini_receipt_enforced_agent.yaml"
)
BASELINE_PAIR = "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml"
TELOS_PAIR = "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml"
SELECTED_PAIRS = [BASELINE_PAIR, TELOS_PAIR]
TEXT_SUFFIXES = {".json", ".jsonl", ".log", ".txt", ".md", ".yaml", ".yml", ".py"}
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


def audit_summary_report_and_preflight(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    report = load_json(REPORT)
    preflight = load_json(PREFLIGHT)
    overlay = load_json(OVERLAY)

    if summary.get("schema_version") != "telos.provider_compatible_paid_execution.summary.v1":
        failures.append("unexpected summary schema")
    if report.get("schema_version") != "telos.provider_compatible_paid_execution.report.v1":
        failures.append("unexpected report schema")
    if preflight.get("schema_version") != "telos.provider_compatible_paid_execution.preflight.v1":
        failures.append("unexpected preflight schema")
    if summary.get("experiment_id") != EXPERIMENT.name or report.get("experiment_id") != EXPERIMENT.name:
        failures.append("experiment id mismatch")
    if summary.get("status") != "pass" or report.get("status") != "pass":
        failures.append("iter66 must publish a clean pass")
    if summary.get("clean_pass") is not True or summary.get("blocked_result") is not False:
        failures.append("summary pass booleans are inconsistent")
    if summary.get("quality_failure") is not False:
        failures.append("quality_failure must be false")
    if summary.get("blockers") != [] or summary.get("failures") != []:
        failures.append("clean pass must not contain blockers or failures")

    for key in [
        "gpu_used",
        "sentinel_named_resources_modified",
        "cloud_runner_started",
        "teardown_required",
        "benchmark_result_claimed",
        "leaderboard_or_swebench_result_claimed",
        "model_superiority_claimed",
        "state_of_the_art_result_claimed",
        "production_or_live_domain_changed",
    ]:
        if summary.get(key) is not False:
            failures.append(f"summary {key} must be false")
        if report.get(key) is not False:
            failures.append(f"report {key} must be false")

    if summary.get("iter64_status") != "pass" or summary.get("iter64_clean_pass") is not True:
        failures.append("iter64 prerequisite must be a clean pass")
    if summary.get("iter64_receipt_validation_returncode") != 0:
        failures.append("iter64 receipt validation must pass")
    if summary.get("iter64_audit_returncode") != 0:
        failures.append("iter64 audit must pass")
    if summary.get("iter65_status") != "pass" or summary.get("iter65_clean_pass") is not True:
        failures.append("iter65 prerequisite must be a clean pass")
    if summary.get("iter65_receipt_failure_classification") != "schema_incomplete":
        failures.append("iter65 classification must remain schema_incomplete")
    if summary.get("iter65_receipt_validation_returncode") != 0:
        failures.append("iter65 receipt validation must pass")
    if summary.get("iter65_audit_returncode") != 0:
        failures.append("iter65 audit must pass")
    if summary.get("iter65_recovered_overlay_sha256") != sha256(ITER65_OVERLAY):
        failures.append("iter65 recovered overlay hash mismatch")

    if summary.get("executed_pair_ids") != SELECTED_PAIRS:
        failures.append("executed pair ids changed")
    if summary.get("executed_pair_count") != 2 or report.get("executed_pair_count") != 2:
        failures.append("exactly two selected rows must execute")
    if summary.get("excluded_pair_executed") is not False or report.get("excluded_pair_executed") is not False:
        failures.append("excluded pairs must remain unexecuted")
    if summary.get("verifier_crash_recovery_used") is not False:
        failures.append("iter66 must not use verifier-crash recovery")
    if summary.get("provider_api_calls") != 8 or report.get("provider_api_calls") != 8:
        failures.append("provider API call count changed")
    if abs(float(summary.get("provider_cost_usd", -1.0)) - 0.059378) > 1e-9:
        failures.append("provider cost changed")
    if summary.get("provider_call_ceiling") != 16 or summary.get("provider_spend_ceiling_usd") != 10.0:
        failures.append("provider ceilings changed")
    if summary.get("redaction_scan_passed") is not True or summary.get("redaction_findings") != []:
        failures.append("redaction scan must pass with no findings")

    metric = summary.get("primary_metric", {})
    if metric != {
        "baseline_verified_completion_evidence": True,
        "telos_verified_completion_evidence": True,
        "verified_completion_evidence_delta_telos_minus_baseline": 0,
    }:
        failures.append(f"primary metric changed: {metric}")

    copies = overlay.get("copies", [])
    telos_overlay = [
        item
        for item in copies
        if item.get("destination") == "configs/mini/telos_vertex_gemini_receipt_enforced_agent.yaml"
    ]
    if len(telos_overlay) != 1:
        failures.append("expected exactly one Telos receipt-agent overlay copy")
    elif telos_overlay[0].get("materialization") != "copied_iter65_recovered_overlay":
        failures.append("Telos receipt-agent overlay must come from iter65 recovered overlay")
    elif telos_overlay[0].get("source_sha256") != sha256(ITER65_OVERLAY):
        failures.append("Telos receipt-agent overlay source hash mismatch")
    if overlay.get("all_materialized") is not True or overlay.get("copied_hashes_match") is not True:
        failures.append("overlay materialization must pass with matching hashes")
    if overlay.get("runtime_model_config_has_secret_values_only_in_tmp") is not True:
        failures.append("runtime model config secret boundary must hold")

    row_results = report.get("row_results", [])
    if len(row_results) != 2:
        failures.append("row_results must contain exactly two rows")
    rows = {row.get("pair_id"): row for row in row_results if isinstance(row, dict)}
    baseline = rows.get(BASELINE_PAIR, {})
    telos = rows.get(TELOS_PAIR, {})
    if baseline.get("verified_completion_evidence") is not True:
        failures.append("baseline verified completion evidence must be true")
    if baseline.get("receipt_validation_returncode") is not None:
        failures.append("baseline must not require receipt validation")
    if telos.get("verified_completion_evidence") is not True:
        failures.append("Telos verified completion evidence must be true")
    if telos.get("receipt_valid") is not True or telos.get("receipt_validation_returncode") != 0:
        failures.append("Telos receipt must validate before completion is accepted")
    for pair_id, row in rows.items():
        raw_dir = RAW / pair_id
        for required in ["command_execution.json", "command_stdout.txt", "command_stderr.txt", "raw_manifest.json"]:
            if not (raw_dir / required).exists():
                failures.append(f"{pair_id} missing raw artifact {required}")
        if row.get("raw_evidence_present") is True:
            for required in ["metadata.json", "players/p1/p1_r1.traj.json"]:
                if not (raw_dir / required).exists():
                    failures.append(f"{pair_id} marked raw evidence present but missing {required}")

    for rel_path, digest in summary.get("artifact_hashes", {}).items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"summary hash path missing: {rel_path}")
        elif sha256(path) != digest:
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
        "Status: `PASS`.",
        "provider API calls: `8`",
        "provider cost from CodeClash metadata: `$0.05937800`",
        "Telos-minus-baseline verified-completion delta: `0`",
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
        "Telos outperforms baseline",
    ]:
        if forbidden in result or forbidden in review:
            failures.append(f"claim boundary regression: {forbidden}")
    if "provider-compatible paid execution after receipt prompt alignment: pass" not in command_output:
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
        audit_summary_report_and_preflight(failures)
        audit_receipt_and_text(failures)
        audit_secrets(failures)
    if failures:
        print("iter66 provider-compatible paid execution after receipt prompt alignment audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter66 provider-compatible paid execution after receipt prompt alignment audit: clean artifact packet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
