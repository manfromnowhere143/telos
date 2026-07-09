#!/usr/bin/env python3
"""Audit the iter29 public claim-surface negative guard proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter29_public_claim_surface_negative_guard")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
REPORT = PROOF / "negative_guard_report.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECEIPT = PROOF / "valid" / "receipt_public_claim_surface_negative_guard.json"
FIXTURES = PROOF / "fixtures"
ITER30 = Path("experiments/iter30_boundary_matrix_schema_guard/HYPOTHESIS.md")

EXPECTED_FIXTURES = {
    "original_iter21_tail_overclaim": [
        "forbidden_claims:README.md",
        "original_iter21_occupied_tail_not_claimed",
    ],
    "hidden_nulls": [
        "required_snippets:README.md",
        "required_snippets:CONTINUITY.md",
        "matrix_nulls_visible_publicly",
    ],
    "changed_candidate_conflated": [
        "required_snippets:README.md",
        "required_snippets:docs/REPORT.md",
        "changed_candidate_boundary_visible",
    ],
    "benchmark_result_overclaim": ["forbidden_claims:README.md"],
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
        "schema_version": "telos.public_claim_surface_negative_guard.summary.v1",
        "status": "pass",
        "experiment_id": "iter29_public_claim_surface_negative_guard",
        "source_experiment": "iter28_public_claim_surface_guard",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "real_public_prose_passed": True,
        "fixture_count": 4,
        "fixtures_failed_as_expected": True,
        "failed_fixture_ids": [],
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "clean_pass": True,
        "next_gate": ITER30.as_posix(),
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


def audit_report(failures: list[str]) -> None:
    data = load_json(REPORT)
    expected = {
        "schema_version": "telos.public_claim_surface_negative_guard.report.v1",
        "status": "pass",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "real_public_prose_passed": True,
        "fixture_count": 4,
        "fixtures_failed_as_expected": True,
        "failed_fixture_ids": [],
        "iter28_status": "pass",
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"report {key} expected {value!r}, got {data.get(key)!r}")
    fixtures = data.get("fixtures")
    if not isinstance(fixtures, list) or len(fixtures) != len(EXPECTED_FIXTURES):
        failures.append("report fixtures must contain four entries")
        return
    by_id = {fixture.get("fixture_id"): fixture for fixture in fixtures}
    if set(by_id) != set(EXPECTED_FIXTURES):
        failures.append(f"fixture ids mismatch: {sorted(by_id)}")
        return
    for fixture_id, expected_checks in EXPECTED_FIXTURES.items():
        fixture = by_id[fixture_id]
        if fixture.get("status") != "pass":
            failures.append(f"{fixture_id}: fixture must pass as expected-detected")
        if fixture.get("expected_failed_checks") != expected_checks:
            failures.append(f"{fixture_id}: expected checks mismatch")
        observed = fixture.get("observed_failed_checks")
        for check_id in expected_checks:
            if check_id not in observed:
                failures.append(f"{fixture_id}: missing observed check {check_id}")


def audit_text_and_receipt(failures: list[str]) -> None:
    output = COMMAND_OUTPUT.read_text(encoding="utf-8")
    for required in [
        "public claim surface negative guard: pass",
        "real_public_prose_passed=true",
        "fixtures=4 failed_as_expected=4",
        "original_iter21_tail_overclaim: pass",
        "hidden_nulls: pass",
        "changed_candidate_conflated: pass",
        "benchmark_result_overclaim: pass",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`",
        "original_iter21_tail_overclaim",
        "benchmark_result_overclaim",
        "No provider model was called",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in ["four generated overclaim", "No provider call"]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.receipt_id != "iter29-public-claim-surface-negative-guard-pass":
        failures.append("unexpected receipt id")
    if receipt.status != "pass":
        failures.append("receipt status must be pass")


def audit_fixture_files(failures: list[str]) -> None:
    for fixture_id in EXPECTED_FIXTURES:
        for rel_path in ["README.md", "docs/REPORT.md", "docs/NEXT_PHASE.md", "CONTINUITY.md"]:
            path = FIXTURES / fixture_id / f"{rel_path.replace('/', '__')}.txt"
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
    for path in [RESULT, SUMMARY, REPORT, COMMAND_OUTPUT, REVIEW, RECEIPT, FIXTURES, ITER30]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_summary(failures)
        audit_report(failures)
        audit_text_and_receipt(failures)
        audit_fixture_files(failures)
        audit_no_generated_residue(failures)

    if failures:
        print("public claim surface negative guard audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("public claim surface negative guard audit: clean fixture pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
