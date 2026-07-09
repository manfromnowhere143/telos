#!/usr/bin/env python3
"""Audit iter67 provider-compatible expanded-slice refreeze artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


ROOT = Path.cwd()
EXPERIMENT = Path("experiments/iter67_provider_compatible_expanded_slice_refreeze")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SURVEY = PROOF / "task_surface_survey.json"
DECISION = PROOF / "expanded_slice_decision.json"
SUMMARY = PROOF / "run_summary.json"
RECEIPT = PROOF / "valid" / "receipt_provider_compatible_expanded_slice_refreeze.json"
NEXT_GATE = Path("experiments/iter68_provider_compatible_task_surface_adapter_recovery/HYPOTHESIS.md")
READY_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml",
]
REJECTED_PAIR_IDS = [
    "baseline-agent-completion-evidence__configs-test-dummy-yaml",
    "baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml",
    "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml",
]
PRIMARY_METRIC = {
    "baseline_verified_completion_evidence": True,
    "telos_verified_completion_evidence": True,
    "verified_completion_evidence_delta_telos_minus_baseline": 0,
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
        SURVEY,
        DECISION,
        SUMMARY,
        PROOF / "command_output.txt",
        PROOF / "review.md",
        PROOF / "learning_record.json",
        RECEIPT,
        NEXT_GATE,
    ]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")


def audit_summary_survey_decision(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    survey = load_json(SURVEY)
    decision = load_json(DECISION)

    if summary.get("schema_version") != "telos.provider_compatible_expanded_slice_refreeze.summary.v1":
        failures.append("unexpected summary schema")
    if survey.get("schema_version") != "telos.provider_compatible_expanded_slice_refreeze.survey.v1":
        failures.append("unexpected survey schema")
    if decision.get("schema_version") != "telos.provider_compatible_expanded_slice_refreeze.decision.v1":
        failures.append("unexpected decision schema")
    if summary.get("experiment_id") != EXPERIMENT.name:
        failures.append("experiment id mismatch")
    if summary.get("status") != "blocked" or survey.get("status") != "blocked" or decision.get("status") != "blocked":
        failures.append("iter67 must publish a blocked no-expansion decision")
    if summary.get("clean_pass") is not False or summary.get("blocked_result") is not True:
        failures.append("blocked summary booleans are inconsistent")
    if summary.get("quality_failure") is not False:
        failures.append("quality_failure must be false")
    if summary.get("failures") != [] or decision.get("failures") != []:
        failures.append("blocked decision must not contain quality failures")

    expected_blockers = [
        "expanded_task_surface_adapter_missing",
        "no_candidate_pair_beyond_existing_two_has_provider_ready_binding",
    ]
    if summary.get("blockers") != expected_blockers or decision.get("blockers") != expected_blockers:
        failures.append("blocked reasons changed")
    if summary.get("iter66_primary_metric") != PRIMARY_METRIC:
        failures.append("iter66 primary metric changed")
    if summary.get("iter66_receipt_validation_returncode") != 0:
        failures.append("iter66 receipt validation must pass")
    if summary.get("iter66_audit_returncode") != 0:
        failures.append("iter66 audit must pass")
    if summary.get("candidate_public_config_count") != 3:
        failures.append("candidate public config count changed")
    if summary.get("candidate_pair_count") != 6:
        failures.append("candidate pair count changed")
    if summary.get("provider_ready_pair_count") != 2:
        failures.append("provider-ready pair count changed")
    if summary.get("incompatible_pair_count") != 4:
        failures.append("incompatible pair count changed")
    if summary.get("expanded_slice_decision") != "no_expanded_slice_currently_justified":
        failures.append("expanded slice decision changed")
    if summary.get("proposed_expanded_slice_pair_ids") != []:
        failures.append("no expanded rows may be selected in iter67")
    if summary.get("retained_existing_two_row_slice_pair_ids") != READY_PAIR_IDS:
        failures.append("retained two-row slice changed")
    if summary.get("excluded_pair_ids") != REJECTED_PAIR_IDS:
        failures.append("excluded pair ids changed")

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
    ]:
        if summary.get(key) != expected:
            failures.append(f"summary {key} expected {expected!r}, got {summary.get(key)!r}")

    if decision.get("next_paid_gate_authorized") is not False:
        failures.append("iter67 must not authorize a larger paid gate")
    if decision.get("next_recovery_gate") != str(NEXT_GATE):
        failures.append("next recovery gate changed")
    if len(decision.get("existing_two_row_command_plan", [])) != 2:
        failures.append("existing two-row command plan must contain two rows")
    for row in decision.get("existing_two_row_command_plan", []):
        for key in [
            "future_execution_command",
            "provider_overlay_config",
            "provider_agent_config",
            "provider_model_config",
            "future_artifact_plan",
            "receipt_validation_plan",
            "redaction_plan",
            "cost_capture_plan",
        ]:
            if not row.get(key):
                failures.append(f"{row.get('pair_id')} missing {key}")
    if len(decision.get("excluded_pairs", [])) != 4:
        failures.append("decision must include four excluded pairs")
    for row in decision.get("excluded_pairs", []):
        if not row.get("exclusion_reason"):
            failures.append(f"{row.get('pair_id')} missing exclusion reason")

    surfaces = survey.get("available_task_surfaces", [])
    if len(surfaces) != 3:
        failures.append("survey must include three committed public task surfaces")
    if not any(
        item.get("public_config") == "configs/test/battlesnake_pvp_test.yaml"
        and item.get("provider_ready_pair_count") == 2
        for item in surfaces
    ):
        failures.append("BattleSnake PvP ready surface missing from survey")
    if sum(1 for row in survey.get("candidate_pairs", []) if row.get("compatibility_status") == "provider_binding_incompatible") != 4:
        failures.append("survey must expose four incompatible candidate pairs")
    if survey.get("local_codeclash_survey", {}).get("used_for_selection") is not False:
        failures.append("local CodeClash checkout must not be used for selection")

    if summary.get("redaction_scan_passed") is not True or summary.get("redaction_findings") != []:
        failures.append("redaction scan must pass with no findings")
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
        "Status: `BLOCKED`.",
        "expanded slice decision: `no_expanded_slice_currently_justified`",
        "This is not a benchmark result",
        "state-of-the-art result",
        "provider-compatible adapters",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "correctly blocks",
        "zero Telos-minus-baseline verified-completion delta",
        "made no provider call",
        "not a benchmark/model/state-of-the-art claim",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "provider_api_calls=0",
        "provider_spend_usd=0.00",
        "expanded_slice_decision=no_expanded_slice_currently_justified",
        "next_gate=experiments/iter68_provider_compatible_task_surface_adapter_recovery/HYPOTHESIS.md",
    ]:
        if required not in command_output:
            failures.append(f"command output missing required line: {required}")


def audit_redaction(failures: list[str]) -> None:
    findings = []
    for path in text_files(EXPERIMENT):
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
        audit_summary_survey_decision(failures)
        audit_receipt_and_text(failures)
        audit_redaction(failures)

    if failures:
        print("iter67 provider-compatible expanded slice refreeze audit FAILED")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("iter67 provider-compatible expanded slice refreeze audit: clean blocked decision")
    return 0


if __name__ == "__main__":
    sys.exit(main())
