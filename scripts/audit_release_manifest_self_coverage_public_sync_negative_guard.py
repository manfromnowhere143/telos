#!/usr/bin/env python3
"""Audit the iter38 self-coverage public-sync negative guard proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter38_release_manifest_self_coverage_public_sync_negative_guard")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
REPORT = PROOF / "negative_guard_report.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECEIPT = PROOF / "valid" / "receipt_release_manifest_self_coverage_public_sync_negative_guard.json"
FIXTURES = PROOF / "fixtures"
ITER39 = Path("experiments/iter39_public_task_protocol_effect_slice/HYPOTHESIS.md")

EXPECTED_FIXTURES = {
    "missing_release_manifest_reference": [
        "required_snippets:README.md",
        "required_snippets:docs/REPORT.md",
        "required_snippets:docs/NEXT_PHASE.md",
        "required_snippets:CONTINUITY.md",
        "manifest_referenced_everywhere",
    ],
    "missing_self_coverage_report_reference": [
        "required_snippets:README.md",
        "required_snippets:docs/REPORT.md",
        "required_snippets:docs/NEXT_PHASE.md",
        "required_snippets:CONTINUITY.md",
        "self_coverage_referenced_everywhere",
    ],
    "missing_self_coverage_negative_guard_reference": [
        "required_snippets:README.md",
        "required_snippets:docs/REPORT.md",
        "required_snippets:docs/NEXT_PHASE.md",
        "required_snippets:CONTINUITY.md",
        "negative_report_referenced_everywhere",
    ],
    "hidden_failed_nulls": ["required_snippets:docs/NEXT_PHASE.md", "failed_null_rows_visible"],
    "candidate_original_conflation": ["changed_candidate_boundary_visible"],
    "forbidden_benchmark_or_runtime_claim": [
        "forbidden_claims:README.md",
        "forbidden_claims:docs/REPORT.md",
        "forbidden_claims:docs/NEXT_PHASE.md",
        "forbidden_claims:CONTINUITY.md",
    ],
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
        "schema_version": "telos.release_manifest_self_coverage_public_sync_negative_guard.summary.v1",
        "status": "pass",
        "experiment_id": "iter38_release_manifest_self_coverage_public_sync_negative_guard",
        "source_experiment": "iter37_release_manifest_self_coverage_public_sync_guard",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "real_public_prose_passed": True,
        "fixture_count": 6,
        "fixtures_failed_as_expected": True,
        "failed_fixture_ids": [],
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "model_superiority_claimed": False,
        "clean_pass": True,
        "next_gate": ITER39.as_posix(),
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
        "schema_version": "telos.release_manifest_self_coverage_public_sync_negative_guard.report.v1",
        "status": "pass",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "real_public_prose_passed": True,
        "real_failed_check_ids": [],
        "fixture_count": 6,
        "fixtures_failed_as_expected": True,
        "failed_fixture_ids": [],
        "source_iter37_status": "pass",
        "source_iter37_clean_pass": True,
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "model_superiority_claimed": False,
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"report {key} expected {value!r}, got {data.get(key)!r}")
    fixtures = data.get("fixtures")
    if not isinstance(fixtures, list) or len(fixtures) != len(EXPECTED_FIXTURES):
        failures.append("report fixtures must contain six entries")
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


def audit_fixture_files(failures: list[str]) -> None:
    for fixture_id in EXPECTED_FIXTURES:
        for rel_path in ["README.md", "docs/REPORT.md", "docs/NEXT_PHASE.md", "CONTINUITY.md"]:
            path = FIXTURES / fixture_id / f"{rel_path.replace('/', '__')}.txt"
            if not path.exists():
                failures.append(f"missing fixture file: {path}")


def audit_text_and_receipt(failures: list[str]) -> None:
    output = COMMAND_OUTPUT.read_text(encoding="utf-8")
    for required in [
        "release manifest self coverage public sync negative guard: pass",
        "real_public_prose_passed=true",
        "fixtures=6 failed_as_expected=6",
        "missing_release_manifest_reference: pass",
        "missing_self_coverage_report_reference: pass",
        "missing_self_coverage_negative_guard_reference: pass",
        "hidden_failed_nulls: pass",
        "candidate_original_conflation: pass",
        "forbidden_benchmark_or_runtime_claim: pass",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`",
        "missing_self_coverage_report_reference",
        "forbidden_benchmark_or_runtime_claim",
        "No provider model was called",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in ["six generated", "No provider call"]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    expected_id = "iter38-release-manifest-self-coverage-public-sync-negative-guard-pass"
    if receipt.receipt_id != expected_id:
        failures.append("unexpected receipt id")
    if receipt.status != "pass":
        failures.append("receipt status must be pass")


def audit_no_generated_residue(failures: list[str]) -> None:
    for path in PROOF.rglob("*"):
        if not path.is_file():
            continue
        if path.name.endswith((".pyc", ".tar", ".gz", ".zip")) or "__pycache__" in path.parts:
            failures.append(f"forbidden generated/binary artifact committed: {path}")


def main() -> int:
    failures: list[str] = []
    for path in [RESULT, SUMMARY, REPORT, COMMAND_OUTPUT, REVIEW, RECEIPT, FIXTURES, ITER39]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_summary(failures)
        audit_report(failures)
        audit_fixture_files(failures)
        audit_text_and_receipt(failures)
        audit_no_generated_residue(failures)

    if failures:
        print("release manifest self coverage public sync negative guard audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("release manifest self coverage public sync negative guard audit: clean fixture pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
