#!/usr/bin/env python3
"""Audit the iter22 semantic mutation-guard proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter22_semantic_mutation_guard")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
REPORT = PROOF / "mutation_report.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECEIPT = PROOF / "valid" / "receipt_semantic_mutation_guard.json"
MUTANTS = PROOF / "mutants"
ITER23 = Path("experiments/iter23_tail_semantics_falsification/HYPOTHESIS.md")

EXPECTED_MUTANTS = {
    "boundary_noop": ["boundary-left", "boundary-right", "boundary-down", "boundary-up"],
    "self_collision_noop": ["self-left", "self-right", "self-down", "self-up"],
    "opponent_collision_noop": ["opponent-left", "opponent-right", "opponent-down", "opponent-up"],
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
        "schema_version": "telos.semantic_mutation_guard.summary.v1",
        "status": "pass",
        "experiment_id": "iter22_semantic_mutation_guard",
        "source_experiment": "iter21_opponent_collision_control",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "clean_case_count": 12,
        "clean_cases_passed": 12,
        "clean_cases_failed": 0,
        "mutation_count": 3,
        "all_mutants_detected": True,
        "boundary_mutant_detected": True,
        "self_collision_mutant_detected": True,
        "opponent_collision_mutant_detected": True,
        "test_cases_mutated": False,
        "production_or_live_domain_changed": False,
        "leaderboard_or_swebench_claimed": False,
        "game_score_used_as_verifier_evidence": False,
        "clean_pass": True,
        "next_gate": ITER23.as_posix(),
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
            failures.append(f"hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}")


def audit_report(failures: list[str]) -> None:
    data = load_json(REPORT)
    expected = {
        "schema_version": "telos.semantic_mutation_guard.report.v1",
        "status": "pass",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "submitted_logic_changed_for_clean_run": False,
        "clean_case_count": 12,
        "clean_cases_passed": 12,
        "clean_cases_failed": 0,
        "mutation_count": 3,
        "all_mutants_detected": True,
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"report {key} expected {value!r}, got {data.get(key)!r}")
    clean_results = data.get("clean_results")
    if not isinstance(clean_results, list) or len(clean_results) != 12:
        failures.append("report clean_results must contain twelve cases")
    elif not all(result.get("passed") is True for result in clean_results):
        failures.append("clean results must all pass")

    mutations = data.get("mutations")
    if not isinstance(mutations, list) or len(mutations) != len(EXPECTED_MUTANTS):
        failures.append("report must contain three mutations")
        return
    seen = set()
    for mutation in mutations:
        mutation_id = mutation.get("mutation_id")
        if mutation_id not in EXPECTED_MUTANTS:
            failures.append(f"unexpected mutation id: {mutation_id!r}")
            continue
        seen.add(mutation_id)
        if mutation.get("target_detected") is not True:
            failures.append(f"{mutation_id}: target was not detected")
        if mutation.get("failed_target_case_ids") != EXPECTED_MUTANTS[mutation_id]:
            failures.append(f"{mutation_id}: failed target cases mismatch")
        mutant_path = mutation.get("mutant_path")
        if not isinstance(mutant_path, str) or not Path(mutant_path).exists():
            failures.append(f"{mutation_id}: mutant path missing")
    missing = set(EXPECTED_MUTANTS) - seen
    if missing:
        failures.append(f"missing mutations: {sorted(missing)}")


def audit_text_and_receipt(failures: list[str]) -> None:
    output = COMMAND_OUTPUT.read_text(encoding="utf-8")
    for required in [
        "semantic mutation guard: pass",
        "boundary_noop: detected",
        "self_collision_noop: detected",
        "opponent_collision_noop: detected",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`",
        "All three mutants were detected",
        "No provider model was called",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in ["The clean bot still passed every case", "Each mutant failed"]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.receipt_id != "iter22-semantic-mutation-guard-pass":
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
    for path in [
        RESULT,
        SUMMARY,
        REPORT,
        COMMAND_OUTPUT,
        REVIEW,
        RECEIPT,
        MUTANTS / "boundary_noop.py",
        MUTANTS / "self_collision_noop.py",
        MUTANTS / "opponent_collision_noop.py",
        ITER23,
    ]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_summary(failures)
        audit_report(failures)
        audit_text_and_receipt(failures)
        audit_no_generated_residue(failures)

    if failures:
        print("semantic mutation guard audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("semantic mutation guard audit: clean mutation pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
