#!/usr/bin/env python3
"""Audit the iter25 tail-safety mutation-guard proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter25_tail_safety_mutation_guard")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
REPORT = PROOF / "mutation_report.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECEIPT = PROOF / "valid" / "receipt_tail_safety_mutation_guard.json"
OWN_MUTANT = PROOF / "mutants" / "own_tail_exclusion.py"
OPPONENT_MUTANT = PROOF / "mutants" / "opponent_tail_exclusion.py"
ITER26 = Path("experiments/iter26_own_tail_redundancy_mutation_guard/HYPOTHESIS.md")


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
        "schema_version": "telos.tail_safety_mutation_guard.summary.v1",
        "status": "fail",
        "experiment_id": "iter25_tail_safety_mutation_guard",
        "source_experiment": "iter24_tail_safety_control",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "tail_occupancy_assumption": "tail_remains_occupied",
        "test_cases_mutated": False,
        "clean_candidate_case_count": 4,
        "clean_candidate_cases_passed": 4,
        "clean_candidate_cases_failed": 0,
        "clean_candidate_passed": True,
        "mutation_count": 2,
        "all_mutants_detected": False,
        "own_tail_exclusion_detected": False,
        "opponent_tail_exclusion_detected": True,
        "mutant_control_cases_passed": True,
        "production_or_live_domain_changed": False,
        "leaderboard_or_swebench_claimed": False,
        "game_score_used_as_verifier_evidence": False,
        "clean_pass": False,
        "next_gate": ITER26.as_posix(),
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
        "schema_version": "telos.tail_safety_mutation_guard.report.v1",
        "status": "fail",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "tail_occupancy_assumption": "tail_remains_occupied",
        "test_cases_mutated": False,
        "clean_candidate_case_count": 4,
        "clean_candidate_passed": True,
        "mutation_count": 2,
        "all_mutants_detected": False,
        "mutant_control_cases_passed": True,
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"report {key} expected {value!r}, got {data.get(key)!r}")

    mutations = data.get("mutations")
    if not isinstance(mutations, list) or len(mutations) != 2:
        failures.append("report mutations must contain two entries")
        return
    by_id = {mutation.get("mutation_id"): mutation for mutation in mutations}
    own = by_id.get("own_tail_exclusion")
    opponent = by_id.get("opponent_tail_exclusion")
    if not isinstance(own, dict) or not isinstance(opponent, dict):
        failures.append("missing expected mutation ids")
        return
    if own.get("target_detected") is not False or own.get("failed_case_ids") != []:
        failures.append("own_tail_exclusion must be an explicit miss")
    if own.get("target_observed_safe_moves") != ["up", "right"]:
        failures.append("own_tail_exclusion observed safe moves mismatch")
    if opponent.get("target_detected") is not True:
        failures.append("opponent_tail_exclusion must be detected")
    if opponent.get("failed_case_ids") != ["opponent-tail-left-occupied-risk"]:
        failures.append("opponent_tail_exclusion failed case mismatch")
    if opponent.get("target_observed_safe_moves") != ["up", "left", "right"]:
        failures.append("opponent_tail_exclusion observed safe moves mismatch")


def audit_text_and_receipt(failures: list[str]) -> None:
    output = COMMAND_OUTPUT.read_text(encoding="utf-8")
    for required in [
        "tail safety mutation guard: fail",
        "clean_candidate_cases=4 passed=4",
        "mutations=2 detected=1",
        "own_tail_exclusion: missed",
        "opponent_tail_exclusion: detected",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `FAIL`",
        "own-tail exclusion mutant was not detected",
        "self-snake fallback path",
        "No provider model was called",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in [
        "own-tail mutant did",
        "not fail the own occupied-tail case",
        "No provider call",
    ]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.receipt_id != "iter25-tail-safety-mutation-guard-fail":
        failures.append("unexpected receipt id")
    if receipt.status != "fail":
        failures.append("receipt status must be fail")


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
        OWN_MUTANT,
        OPPONENT_MUTANT,
        ITER26,
    ]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_summary(failures)
        audit_report(failures)
        audit_text_and_receipt(failures)
        audit_no_generated_residue(failures)

    if failures:
        print("tail safety mutation guard audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("tail safety mutation guard audit: expected own-tail miss published")
    return 0


if __name__ == "__main__":
    sys.exit(main())
