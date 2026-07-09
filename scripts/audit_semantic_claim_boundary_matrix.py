#!/usr/bin/env python3
"""Audit the iter27 semantic claim-boundary matrix proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter27_semantic_claim_boundary_matrix")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
MATRIX = PROOF / "claim_boundary_matrix.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECEIPT = PROOF / "valid" / "receipt_semantic_claim_boundary_matrix.json"
ITER28 = Path("experiments/iter28_public_claim_surface_guard/HYPOTHESIS.md")

EXPECTED_EXPERIMENTS = [
    "iter20_behavior_semantic_verification",
    "iter21_opponent_collision_control",
    "iter22_semantic_mutation_guard",
    "iter23_tail_semantics_falsification",
    "iter24_tail_safety_control",
    "iter25_tail_safety_mutation_guard",
    "iter26_own_tail_redundancy_mutation_guard",
]
EXPECTED_NULLS = [
    "iter23_original_occupied_tail_falsification",
    "iter25_tail_safety_mutation_guard_miss",
]
REQUIRED_EXCLUSIONS = {
    "no_codeclash_leaderboard_claim",
    "no_swebench_claim",
    "no_production_or_live_domain_claim",
    "no_model_superiority_claim",
    "no_provider_game_score_as_verifier_evidence",
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
        "schema_version": "telos.semantic_claim_boundary_matrix.summary.v1",
        "status": "pass",
        "experiment_id": "iter27_semantic_claim_boundary_matrix",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "included_experiments": EXPECTED_EXPERIMENTS,
        "row_count": 7,
        "failed_or_null_claim_ids": EXPECTED_NULLS,
        "changed_candidate_claim_ids": ["iter24_changed_candidate_occupied_tail_control"],
        "original_iter21_occupied_tail_safety_claimed": False,
        "failed_null_gates_hidden": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "clean_pass": True,
        "next_gate": ITER28.as_posix(),
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


def audit_matrix(failures: list[str]) -> None:
    data = load_json(MATRIX)
    expected = {
        "schema_version": "telos.semantic_claim_boundary_matrix.v1",
        "status": "pass",
        "experiment_id": "iter27_semantic_claim_boundary_matrix",
        "included_experiments": EXPECTED_EXPERIMENTS,
        "row_count": 7,
        "failed_or_null_claim_ids": EXPECTED_NULLS,
        "original_iter21_occupied_tail_safety_claimed": False,
        "failed_null_gates_hidden": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"matrix {key} expected {value!r}, got {data.get(key)!r}")

    rows = data.get("rows")
    if not isinstance(rows, list) or len(rows) != 7:
        failures.append("matrix rows must contain seven entries")
        return
    row_ids = {row.get("claim_id") for row in rows}
    if set(EXPECTED_NULLS) - row_ids:
        failures.append("matrix missing expected null rows")
    for row in rows:
        claim_id = row.get("claim_id")
        if row.get("original_provider_logic") and row.get("changed_candidate"):
            failures.append(f"{claim_id}: original/candidate conflation")
        exclusions = set(row.get("does_not_claim", []))
        missing = REQUIRED_EXCLUSIONS - exclusions
        if missing:
            failures.append(f"{claim_id}: missing exclusions {sorted(missing)}")
        for path in row.get("evidence_paths", []):
            if not Path(path).exists():
                failures.append(f"{claim_id}: missing evidence path {path}")

    iter23 = next(row for row in rows if row.get("claim_id") == EXPECTED_NULLS[0])
    if iter23.get("status") != "null" or iter23.get("failure_visible") is not True:
        failures.append("iter23 must remain visible as null/failure")
    iter24 = next(row for row in rows if row.get("claim_id") == "iter24_changed_candidate_occupied_tail_control")
    if iter24.get("changed_candidate") is not True or iter24.get("original_provider_logic") is not False:
        failures.append("iter24 must be marked changed candidate only")


def audit_text_and_receipt(failures: list[str]) -> None:
    output = COMMAND_OUTPUT.read_text(encoding="utf-8")
    for required in [
        "semantic claim boundary matrix: pass",
        "rows=7",
        "failed_or_null=iter23_original_occupied_tail_falsification,iter25_tail_safety_mutation_guard_miss",
        "original_iter21_occupied_tail_safety_claimed=false",
        "failed_null_gates_hidden=false",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`",
        "original `iter21` occupied-tail safety is not claimed",
        "changed `iter24` candidate",
        "No provider model was called",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in ["Original provider-submitted logic", "No provider call"]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.receipt_id != "iter27-semantic-claim-boundary-matrix-pass":
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
    for path in [RESULT, SUMMARY, MATRIX, COMMAND_OUTPUT, REVIEW, RECEIPT, ITER28]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_summary(failures)
        audit_matrix(failures)
        audit_text_and_receipt(failures)
        audit_no_generated_residue(failures)

    if failures:
        print("semantic claim boundary matrix audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("semantic claim boundary matrix audit: clean boundary pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
