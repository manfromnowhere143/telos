#!/usr/bin/env python3
"""Audit iter73 expanded receipt-prompt recovery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter73_expanded_receipt_prompt_recovery_after_paid_block")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
REPORT = PROOF / "expanded_receipt_prompt_recovery_report.json"
DIAGNOSIS = PROOF / "receipt_failure_diagnosis.json"
FIXTURE_REPORT = PROOF / "fixture_validation_report.json"
RECEIPT = PROOF / "valid" / "receipt_expanded_receipt_prompt_recovery_after_paid_block.json"
ITER72_PROOF = Path("experiments/iter72_provider_compatible_expanded_paid_execution_after_slice_refreeze/proof")
ITER72_SUMMARY = ITER72_PROOF / "run_summary.json"
ITER72_REPORT = ITER72_PROOF / "protocol_effect_report.json"
NEXT_GATE = Path(
    "experiments/iter74_provider_compatible_expanded_paid_retry_after_receipt_prompt_recovery/"
    "HYPOTHESIS.md"
)
PAIR_DUMMY = "telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml"
PAIR_EDIT = "telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml"
EXPECTED_MISSING = {
    PAIR_DUMMY: [
        "acceptance_criteria",
        "agent_id",
        "benchmark_id",
        "evidence",
        "falsifiers",
        "receipt_id",
        "stated_goal",
        "task_id",
    ],
    PAIR_EDIT: [
        "acceptance_criteria",
        "agent_id",
        "benchmark_id",
        "evidence",
        "falsifiers",
        "receipt_id",
        "stated_goal",
        "status",
        "task_id",
    ],
}
EXPECTED_UNEXPECTED = {
    PAIR_DUMMY: [],
    PAIR_EDIT: ["receipt"],
}
EXPECTED_CANDIDATE_FIELDS = {
    PAIR_DUMMY: ["sha256", "status"],
    PAIR_EDIT: ["receipt", "sha256"],
}
EXPECTED_OVERLAYS = [
    PROOF / "recovered_overlay/configs/mini/telos_vertex_gemini_dummy_receipt_enforced_agent.yaml",
    PROOF / "recovered_overlay/configs/mini/telos_vertex_gemini_edit_receipt_enforced_agent.yaml",
]
EXPECTED_TEMPLATES = [
    PROOF / "recovered_overlay/receipt_templates/dummy_receipt_template.json",
    PROOF / "recovered_overlay/receipt_templates/deterministic_edit_receipt_template.json",
]
EXPECTED_VALID_FIXTURES = [
    PROOF / "fixture_receipts/valid/dummy_valid_receipt.json",
    PROOF / "fixture_receipts/valid/deterministic_edit_valid_receipt.json",
]
EXPECTED_INVALID_FIXTURE = PROOF / "fixture_receipts/invalid/missing_sha256_receipt.json"
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
        PROOF / "command_output.txt",
        PROOF / "review.md",
        PROOF / "learning_record.json",
        RECEIPT,
        *EXPECTED_OVERLAYS,
        *EXPECTED_TEMPLATES,
        *EXPECTED_VALID_FIXTURES,
        EXPECTED_INVALID_FIXTURE,
    ]:
        if not path.exists():
            failures.append(f"missing required artifact: {path}")


def audit_summary_report_diagnosis(failures: list[str]) -> None:
    summary = load_json(SUMMARY)
    report = load_json(REPORT)
    diagnosis = load_json(DIAGNOSIS)
    fixture = load_json(FIXTURE_REPORT)

    expected_schemas = {
        "summary": "telos.expanded_receipt_prompt_recovery.summary.v1",
        "report": "telos.expanded_receipt_prompt_recovery.report.v1",
        "diagnosis": "telos.expanded_receipt_prompt_recovery.diagnosis.v1",
        "fixture": "telos.expanded_receipt_prompt_recovery.fixture_validation.v1",
    }
    packets = {
        "summary": summary,
        "report": report,
        "diagnosis": diagnosis,
        "fixture": fixture,
    }
    for name, expected in expected_schemas.items():
        if packets[name].get("schema_version") != expected:
            failures.append(f"unexpected {name} schema")
    if summary.get("experiment_id") != EXPERIMENT.name or report.get("experiment_id") != EXPERIMENT.name:
        failures.append("experiment id mismatch")
    if summary.get("status") != "pass" or report.get("status") != "pass":
        failures.append("iter73 must publish a clean local pass")
    if summary.get("clean_pass") is not True:
        failures.append("summary clean_pass must be true")
    if summary.get("blocked_result") is not False or summary.get("quality_failure") is not False:
        failures.append("summary blocked/quality booleans are inconsistent")
    if summary.get("blockers") != [] or report.get("blockers") != []:
        failures.append("iter73 pass must have no blockers")
    if summary.get("failures") != [] or report.get("failures") != []:
        failures.append("iter73 pass must have no failures")

    for packet_name, packet in [("summary", summary), ("report", report)]:
        if packet.get("iter72_status") != "blocked":
            failures.append(f"{packet_name} iter72_status must be blocked")
        if packet.get("iter72_provider_api_calls") != 17:
            failures.append(f"{packet_name} iter72 call count changed")
        if abs(float(packet.get("iter72_provider_cost_usd", -1.0)) - 0.057646) > 1e-9:
            failures.append(f"{packet_name} iter72 cost changed")
        if packet.get("recovered_prompt_count") != 2:
            failures.append(f"{packet_name} recovered prompt count must be 2")
        if packet.get("recovered_prompt_required_fields_present") is not True:
            failures.append(f"{packet_name} recovered prompts must include all required fields")
        if packet.get("recovered_prompt_digest_rule_present") is not True:
            failures.append(f"{packet_name} recovered prompts must include digest rule")
        if packet.get("local_valid_fixtures_passed") is not True:
            failures.append(f"{packet_name} local valid fixtures must pass")
        if packet.get("local_malformed_fixture_failed") is not True:
            failures.append(f"{packet_name} local malformed fixture must fail")
        for key in [
            "paid_row_execution_occurred",
            "row_execution_allowed",
            "gpu_used",
            "cloud_runner_started",
            "sentinel_named_resources_modified",
            "production_or_live_domain_changed",
            "benchmark_result_claimed",
            "leaderboard_or_swebench_result_claimed",
            "model_superiority_claimed",
            "state_of_the_art_result_claimed",
        ]:
            if packet.get(key) is not False:
                failures.append(f"{packet_name} {key} must be false")
        if packet.get("provider_api_calls") != 0:
            failures.append(f"{packet_name} provider_api_calls must be zero")
        if float(packet.get("provider_spend_usd", -1.0)) != 0.0:
            failures.append(f"{packet_name} provider_spend_usd must be zero")
        if packet.get("redaction_scan_passed") is not True or packet.get("redaction_findings") != []:
            failures.append(f"{packet_name} redaction scan must pass")

    if summary.get("next_gate") != str(NEXT_GATE):
        failures.append("summary next gate changed")
    if summary.get("missing_required_fields_by_pair") != EXPECTED_MISSING:
        failures.append("summary missing fields by pair changed")
    if report.get("missing_required_fields_by_pair") != EXPECTED_MISSING:
        failures.append("report missing fields by pair changed")
    if summary.get("unexpected_fields_by_pair") != EXPECTED_UNEXPECTED:
        failures.append("summary unexpected fields by pair changed")
    if report.get("unexpected_fields_by_pair") != EXPECTED_UNEXPECTED:
        failures.append("report unexpected fields by pair changed")

    if report.get("iter72_receipt_validation", {}).get("returncode") != 0:
        failures.append("iter72 receipt validation prerequisite must pass")
    if report.get("iter72_audit", {}).get("returncode") != 0:
        failures.append("iter72 audit prerequisite must pass")
    if diagnosis.get("all_candidates_classified_schema_incomplete") is not True:
        failures.append("all candidates must be classified schema_incomplete")
    if diagnosis.get("source_iter72_summary_sha256") != sha256(ITER72_SUMMARY):
        failures.append("iter72 summary hash mismatch")
    if diagnosis.get("source_iter72_report_sha256") != sha256(ITER72_REPORT):
        failures.append("iter72 report hash mismatch")

    diagnoses = {
        item.get("pair_id"): item
        for item in diagnosis.get("candidate_diagnoses", [])
        if isinstance(item, dict)
    }
    if set(diagnoses) != set(EXPECTED_MISSING):
        failures.append("diagnosis pair set changed")
    for pair_id, expected_missing in EXPECTED_MISSING.items():
        item = diagnoses.get(pair_id, {})
        if item.get("classification") != "schema_incomplete":
            failures.append(f"{pair_id} classification changed")
        if item.get("candidate_equals_invalid_artifact") is not True:
            failures.append(f"{pair_id} candidate must match invalid artifact")
        if item.get("candidate_fields") != EXPECTED_CANDIDATE_FIELDS[pair_id]:
            failures.append(f"{pair_id} candidate fields changed")
        if item.get("missing_required_fields") != expected_missing:
            failures.append(f"{pair_id} missing fields changed")
        if item.get("unexpected_fields_under_schema") != EXPECTED_UNEXPECTED[pair_id]:
            failures.append(f"{pair_id} unexpected fields changed")
        if item.get("missing_fields_match_expected") is not True:
            failures.append(f"{pair_id} missing field expectation flag must be true")
        if item.get("unexpected_fields_match_expected") is not True:
            failures.append(f"{pair_id} unexpected field expectation flag must be true")
        if item.get("diagnosis_validation", {}).get("returncode") != 1:
            failures.append(f"{pair_id} diagnosis validation must fail closed")
        if "missing fields:" not in item.get("validator_error", ""):
            failures.append(f"{pair_id} validator error missing expected text")
        if item.get("iter72_receipt_valid") is not False:
            failures.append(f"{pair_id} iter72 receipt must remain invalid")
        if item.get("iter72_verified_completion_evidence") is not False:
            failures.append(f"{pair_id} must not count as verified completion")

    if fixture.get("validator_result", {}).get("returncode") != 0:
        failures.append("fixture validator command must pass")
    if fixture.get("valid_fixtures_passed") is not True:
        failures.append("valid fixtures must pass")
    if fixture.get("malformed_fixture_failed") is not True:
        failures.append("malformed fixture must fail")
    if fixture.get("malformed_observed_error") != "missing fields: sha256":
        failures.append("malformed fixture error changed")

    for rel_path, expected_hash in summary.get("artifact_hashes", {}).items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"summary hash path missing: {rel_path}")
        elif sha256(path) != expected_hash:
            failures.append(f"summary hash mismatch: {rel_path}")


def audit_overlays_and_fixtures(failures: list[str]) -> None:
    for overlay_path in EXPECTED_OVERLAYS:
        text = overlay_path.read_text(encoding="utf-8")
        for field in REQUIRED_FIELDS:
            if field not in text:
                failures.append(f"{overlay_path} missing receipt field {field}")
        for required in [
            "hashlib.sha256",
            "sort_keys=True",
            'separators=(",", ":")',
            'if k != "sha256"',
            "Do not add top-level fields",
            "goal",
            "receipt",
            "files_changed",
            "evidence_artifacts",
            "telos_completion_receipt.json",
            "validate_receipts.py",
        ]:
            if required not in text:
                failures.append(f"{overlay_path} missing instruction {required}")
    dummy_overlay = EXPECTED_OVERLAYS[0].read_text(encoding="utf-8")
    edit_overlay = EXPECTED_OVERLAYS[1].read_text(encoding="utf-8")
    if "configs/test/dummy.yaml" not in dummy_overlay:
        failures.append("Dummy overlay missing public config binding")
    if "telos_marker.py" not in edit_overlay:
        failures.append("deterministic-edit overlay missing edit target")

    for path in [*EXPECTED_TEMPLATES, *EXPECTED_VALID_FIXTURES]:
        try:
            load_receipt(path)
        except ProofValidationError as exc:
            failures.append(f"{path} failed receipt validation: {exc}")
    try:
        load_receipt(EXPECTED_INVALID_FIXTURE)
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
        "paid row execution: `false`",
        "recovered prompt count: `2`",
        "local valid fixtures passed: `true`",
        "local malformed fixture failed: `true`",
        "This is not a benchmark result",
        "state-of-the-art result",
    ]:
        if required not in result:
            failures.append(f"RESULT.md missing required text: {required}")
    for required in [
        "did not call a provider model",
        "does not change the iter72 blocked result",
        "does not authorize benchmark",
        "missing `acceptance_criteria, agent_id, benchmark_id",
    ]:
        if required not in review:
            failures.append(f"review.md missing required text: {required}")
    for required in [
        "expanded receipt prompt recovery after paid block: pass",
        "provider_api_calls=0",
        "provider_spend_usd=0.00",
        "paid_row_execution_occurred=false",
        "recovered_prompt_count=2",
        "local_valid_fixtures_passed=true",
        "local_malformed_fixture_failed=true",
        "redaction_scan_passed=true",
        "blockers=",
        "failures=",
    ]:
        if required not in command_output:
            failures.append(f"command output missing required line: {required}")
    for forbidden in [
        "This is a benchmark result",
        "This is a state-of-the-art result",
        "This is a model-superiority result",
        "This is a leaderboard result",
        "Telos improves benchmark performance",
    ]:
        if forbidden in result or forbidden in review:
            failures.append(f"claim boundary regression: {forbidden}")


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
        audit_summary_report_diagnosis(failures)
        audit_overlays_and_fixtures(failures)
        audit_receipt_and_text(failures)
        audit_secrets(failures)
    if failures:
        print("iter73 expanded receipt prompt recovery audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1
    print("iter73 expanded receipt prompt recovery audit: clean pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
