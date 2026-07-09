#!/usr/bin/env python3
"""Audit the iter30 boundary-matrix schema guard proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter30_boundary_matrix_schema_guard")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
REPORT = PROOF / "schema_guard_report.json"
SCHEMA = PROOF / "claim_boundary_matrix.schema.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECEIPT = PROOF / "valid" / "receipt_boundary_matrix_schema_guard.json"
FIXTURES = PROOF / "fixtures"
ITER31 = Path("experiments/iter31_claim_boundary_release_manifest/HYPOTHESIS.md")

EXPECTED_FIXTURES = {
    "missing_evidence_path": ["missing_evidence_path"],
    "invalid_status": ["invalid_status"],
    "original_candidate_conflation": ["original_candidate_conflation"],
    "missing_required_exclusion": ["missing_required_exclusion"],
    "hidden_failed_null_rows": ["hidden_failed_null_rows"],
}


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be an object")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_summary(failures: list[str]) -> None:
    data = load_json(SUMMARY)
    expected = {
        "schema_version": "telos.boundary_matrix_schema_guard.summary.v1",
        "status": "pass",
        "experiment_id": "iter30_boundary_matrix_schema_guard",
        "source_experiment": "iter27_semantic_claim_boundary_matrix",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "real_matrix_valid": True,
        "fixture_count": 5,
        "fixtures_failed_as_expected": True,
        "failed_fixture_ids": [],
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "clean_pass": True,
        "next_gate": ITER31.as_posix(),
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {data.get(key)!r}")

    hashes = data.get("artifact_hashes", {})
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


def audit_schema(failures: list[str]) -> None:
    data = load_json(SCHEMA)
    expected = {
        "schema_version": "telos.boundary_matrix_schema_guard.schema.v1",
        "validated_schema": "telos.semantic_claim_boundary_matrix.v1",
        "validator": "scripts/verify_boundary_matrix_schema_guard.py",
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"schema {key} expected {value!r}, got {data.get(key)!r}")
    for field in [
        "root_required_fields",
        "row_required_fields",
        "valid_row_statuses",
        "required_exclusions",
        "required_invariants",
    ]:
        if not isinstance(data.get(field), list) or not data[field]:
            failures.append(f"schema {field} must be a non-empty list")
    for required in [
        "evidence_paths_exist",
        "original_provider_logic_and_changed_candidate_are_disjoint",
        "failed_or_null_rows_are_listed_and_failure_visible",
    ]:
        if required not in data.get("required_invariants", []):
            failures.append(f"schema missing invariant: {required}")


def audit_report(failures: list[str]) -> None:
    data = load_json(REPORT)
    expected = {
        "schema_version": "telos.boundary_matrix_schema_guard.report.v1",
        "status": "pass",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "real_matrix_valid": True,
        "real_matrix_error_codes": [],
        "fixture_count": 5,
        "fixtures_failed_as_expected": True,
        "failed_fixture_ids": [],
        "source_negative_guard_status": "pass",
        "source_negative_guard_fixtures_failed_as_expected": True,
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"report {key} expected {value!r}, got {data.get(key)!r}")
    fixtures = data.get("fixtures")
    if not isinstance(fixtures, list) or len(fixtures) != len(EXPECTED_FIXTURES):
        failures.append("report fixtures must contain five entries")
        return
    by_id = {fixture.get("fixture_id"): fixture for fixture in fixtures}
    if set(by_id) != set(EXPECTED_FIXTURES):
        failures.append(f"fixture ids mismatch: {sorted(by_id)}")
        return
    for fixture_id, expected_codes in EXPECTED_FIXTURES.items():
        fixture = by_id[fixture_id]
        if fixture.get("status") != "pass":
            failures.append(f"{fixture_id}: fixture must pass as expected-detected")
        if fixture.get("expected_error_codes") != expected_codes:
            failures.append(f"{fixture_id}: expected codes mismatch")
        observed = fixture.get("observed_error_codes")
        for code in expected_codes:
            if code not in observed:
                failures.append(f"{fixture_id}: missing observed error code {code}")
        fixture_path = fixture.get("fixture_path")
        if not isinstance(fixture_path, str) or not Path(fixture_path).exists():
            failures.append(f"{fixture_id}: fixture path missing")


def audit_text_and_receipt(failures: list[str]) -> None:
    output = COMMAND_OUTPUT.read_text(encoding="utf-8")
    for required in [
        "boundary matrix schema guard: pass",
        "real_matrix_valid=true",
        "fixtures=5 failed_as_expected=5",
        "missing_evidence_path: pass",
        "invalid_status: pass",
        "original_candidate_conflation: pass",
        "missing_required_exclusion: pass",
        "hidden_failed_null_rows: pass",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`",
        "missing_evidence_path",
        "hidden_failed_null_rows",
        "No provider model was called",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in ["five generated malformed", "No provider call"]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.receipt_id != "iter30-boundary-matrix-schema-guard-pass":
        failures.append("unexpected receipt id")
    if receipt.status != "pass":
        failures.append("receipt status must be pass")


def audit_fixture_files(failures: list[str]) -> None:
    for fixture_id in EXPECTED_FIXTURES:
        path = FIXTURES / f"{fixture_id}.json"
        if not path.exists():
            failures.append(f"missing fixture file: {path}")


def audit_no_generated_residue(failures: list[str]) -> None:
    for path in PROOF.rglob("*"):
        if not path.is_file():
            continue
        if path.name.endswith((".pyc", ".tar", ".gz", ".zip")) or "__pycache__" in path.parts:
            failures.append(f"forbidden generated/binary artifact committed: {path}")


def main() -> int:
    failures: list[str] = []
    for path in [RESULT, SUMMARY, REPORT, SCHEMA, COMMAND_OUTPUT, REVIEW, RECEIPT, FIXTURES, ITER31]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_summary(failures)
        audit_schema(failures)
        audit_report(failures)
        audit_text_and_receipt(failures)
        audit_fixture_files(failures)
        audit_no_generated_residue(failures)

    if failures:
        print("boundary matrix schema guard audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("boundary matrix schema guard audit: clean schema-fixture pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
