#!/usr/bin/env python3
"""Audit the iter26 own-tail redundancy mutation-guard proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter26_own_tail_redundancy_mutation_guard")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
REPORT = PROOF / "redundancy_report.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECEIPT = PROOF / "valid" / "receipt_own_tail_redundancy_mutation_guard.json"
COMPOUND_MUTANT = PROOF / "mutants" / "own_tail_compound_exclusion.py"
COMPOUND_MANIFEST = PROOF / "mutants" / "own_tail_compound_manifest.json"
ITER27 = Path("experiments/iter27_semantic_claim_boundary_matrix/HYPOTHESIS.md")


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
        "schema_version": "telos.own_tail_redundancy_mutation_guard.summary.v1",
        "status": "pass",
        "experiment_id": "iter26_own_tail_redundancy_mutation_guard",
        "source_experiment": "iter25_tail_safety_mutation_guard",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "tail_occupancy_assumption": "tail_remains_occupied",
        "test_cases_mutated": False,
        "compound_mutant": True,
        "clean_candidate_case_count": 4,
        "clean_candidate_cases_passed": 4,
        "clean_candidate_cases_failed": 0,
        "clean_candidate_passed": True,
        "target_case_id": "own-tail-left-occupied-risk",
        "target_detected": True,
        "target_observed_safe_moves": ["up", "left", "right"],
        "control_cases_passed": True,
        "opponent_tail_still_passed": True,
        "production_or_live_domain_changed": False,
        "leaderboard_or_swebench_claimed": False,
        "game_score_used_as_verifier_evidence": False,
        "clean_pass": True,
        "next_gate": ITER27.as_posix(),
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
        "schema_version": "telos.own_tail_redundancy_mutation_guard.report.v1",
        "status": "pass",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "tail_occupancy_assumption": "tail_remains_occupied",
        "test_cases_mutated": False,
        "compound_mutant": True,
        "clean_candidate_case_count": 4,
        "clean_candidate_passed": True,
        "target_case_id": "own-tail-left-occupied-risk",
        "target_detected": True,
        "target_observed_safe_moves": ["up", "left", "right"],
        "control_cases_passed": True,
        "opponent_tail_still_passed": True,
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"report {key} expected {value!r}, got {data.get(key)!r}")
    patches = data.get("compound_patches")
    if not isinstance(patches, list) or len(patches) != 2:
        failures.append("report compound_patches must contain two patches")


def audit_manifest(failures: list[str]) -> None:
    manifest = load_json(COMPOUND_MANIFEST)
    if manifest.get("compound_mutant") is not True:
        failures.append("compound manifest must mark compound_mutant true")
    patches = manifest.get("patches")
    if not isinstance(patches, list) or len(patches) != 2:
        failures.append("compound manifest must contain two patches")
        return
    patch_ids = {patch.get("patch_id") for patch in patches}
    expected_ids = {"direct_own_tail_exclusion", "self_snake_fallback_removed"}
    if patch_ids != expected_ids:
        failures.append(f"compound patch ids mismatch: {sorted(patch_ids)}")


def audit_text_and_receipt(failures: list[str]) -> None:
    output = COMMAND_OUTPUT.read_text(encoding="utf-8")
    for required in [
        "own-tail redundancy mutation guard: pass",
        "compound_target_detected=true",
        "compound_target_safe=up,left,right",
        "compound_controls_passed=true",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`",
        "self-snake fallback protection",
        "observed safe moves",
        "No provider model was called",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in ["compound own-tail mutant", "No provider call"]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.receipt_id != "iter26-own-tail-redundancy-mutation-guard-pass":
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
        COMPOUND_MUTANT,
        COMPOUND_MANIFEST,
        ITER27,
    ]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_summary(failures)
        audit_report(failures)
        audit_manifest(failures)
        audit_text_and_receipt(failures)
        audit_no_generated_residue(failures)

    if failures:
        print("own-tail redundancy mutation guard audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("own-tail redundancy mutation guard audit: clean compound pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
