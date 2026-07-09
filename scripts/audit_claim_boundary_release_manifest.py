#!/usr/bin/env python3
"""Audit the iter31 claim-boundary release manifest proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter31_claim_boundary_release_manifest")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
MANIFEST = PROOF / "claim_boundary_release_manifest.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECEIPT = PROOF / "valid" / "receipt_claim_boundary_release_manifest.json"
ITER32 = Path("experiments/iter32_claim_boundary_release_manifest_negative_guard/HYPOTHESIS.md")

EXPECTED_FAILED_OR_NULL = [
    "iter23_original_occupied_tail_falsification",
    "iter25_tail_safety_mutation_guard_miss",
]
EXPECTED_CHANGED_CANDIDATE = ["iter24_changed_candidate_occupied_tail_control"]
EXPECTED_SOURCE_ARTIFACTS = {
    "claim_boundary_matrix",
    "public_claim_surface_report",
    "negative_guard_report",
    "schema_guard_report",
}
EXPECTED_FORBIDDEN = {
    "codeclash_leaderboard_result",
    "swebench_result",
    "production_or_live_domain_result",
    "model_superiority_result",
    "provider_game_score_as_verifier_evidence",
    "original_iter21_occupied_tail_safety",
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
        "schema_version": "telos.claim_boundary_release_manifest.summary.v1",
        "status": "pass",
        "experiment_id": "iter31_claim_boundary_release_manifest",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "manifest_valid": True,
        "manifest_failure_count": 0,
        "manifest_failures": [],
        "failed_or_null_claim_ids": EXPECTED_FAILED_OR_NULL,
        "changed_candidate_claim_ids": EXPECTED_CHANGED_CANDIDATE,
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "model_superiority_claimed": False,
        "clean_pass": True,
        "next_gate": ITER32.as_posix(),
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {data.get(key)!r}")
    if data.get("artifact_count", 0) < 20:
        failures.append("summary artifact_count must cover matrix row evidence")

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


def audit_manifest(failures: list[str]) -> None:
    data = load_json(MANIFEST)
    expected = {
        "schema_version": "telos.claim_boundary_release_manifest.v1",
        "status": "pass",
        "experiment_id": "iter31_claim_boundary_release_manifest",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "forbidden_claims_made": [],
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "model_superiority_claimed": False,
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"manifest {key} expected {value!r}, got {data.get(key)!r}")

    source_ids = {artifact.get("artifact_id") for artifact in data.get("source_artifacts", [])}
    if source_ids != EXPECTED_SOURCE_ARTIFACTS:
        failures.append(f"manifest source artifact ids mismatch: {sorted(source_ids)}")
    for artifact in data.get("source_artifacts", []):
        path = Path(artifact.get("path", ""))
        if not path.exists():
            failures.append(f"source artifact missing: {path}")
            continue
        if artifact.get("sha256") != sha256(path):
            failures.append(f"source artifact hash mismatch: {path}")
        if artifact.get("status") != "pass":
            failures.append(f"source artifact status must be pass: {path}")

    index = data.get("artifact_index", [])
    if not isinstance(index, list) or len(index) < 20:
        failures.append("manifest artifact_index must cover row evidence artifacts")
    seen = set()
    for artifact in index:
        rel_path = artifact.get("path")
        if not isinstance(rel_path, str) or not rel_path:
            failures.append("artifact_index path must be a non-empty string")
            continue
        if rel_path in seen:
            failures.append(f"duplicate artifact_index path: {rel_path}")
        seen.add(rel_path)
        path = Path(rel_path)
        if not path.exists():
            failures.append(f"artifact_index path missing: {rel_path}")
            continue
        if artifact.get("sha256") != sha256(path):
            failures.append(f"artifact_index hash mismatch: {rel_path}")

    matrix = data.get("claim_boundary_matrix", {})
    if matrix.get("failed_or_null_claim_ids") != EXPECTED_FAILED_OR_NULL:
        failures.append("manifest failed_or_null_claim_ids mismatch")
    if matrix.get("changed_candidate_claim_ids") != EXPECTED_CHANGED_CANDIDATE:
        failures.append("manifest changed_candidate_claim_ids mismatch")
    if matrix.get("original_iter21_occupied_tail_safety_claimed") is not False:
        failures.append("original iter21 occupied-tail safety must not be claimed")
    if matrix.get("failed_null_gates_hidden") is not False:
        failures.append("failed/null gates must not be hidden")

    failed_rows = data.get("failed_or_null_rows", [])
    if [row.get("claim_id") for row in failed_rows] != EXPECTED_FAILED_OR_NULL:
        failures.append("manifest failed_or_null_rows mismatch")
    for row in failed_rows:
        if row.get("failure_visible") is not True or row.get("status") != "null":
            failures.append(f"failed/null row not visible as null: {row.get('claim_id')}")

    changed_rows = data.get("changed_candidate_rows", [])
    if [row.get("claim_id") for row in changed_rows] != EXPECTED_CHANGED_CANDIDATE:
        failures.append("manifest changed_candidate_rows mismatch")
    for row in changed_rows:
        if row.get("changed_candidate") is not True or row.get("original_provider_logic") is not False:
            failures.append(f"changed candidate row conflated: {row.get('claim_id')}")

    if set(data.get("forbidden_claim_classes", [])) != EXPECTED_FORBIDDEN:
        failures.append("manifest forbidden_claim_classes mismatch")
    if data.get("public_claim_surface", {}).get("failed_null_gates_visible") is not True:
        failures.append("public claim surface must keep failed/null gates visible")
    if data.get("negative_guard", {}).get("fixtures_failed_as_expected") is not True:
        failures.append("negative guard fixtures must fail as expected")
    if data.get("schema_guard", {}).get("real_matrix_valid") is not True:
        failures.append("schema guard must validate real matrix")
    if data.get("schema_guard", {}).get("fixtures_failed_as_expected") is not True:
        failures.append("schema guard fixtures must fail as expected")


def audit_text_and_receipt(failures: list[str]) -> None:
    output = COMMAND_OUTPUT.read_text(encoding="utf-8")
    for required in [
        "claim boundary release manifest: pass",
        "provider_api_calls=0",
        "cloud_or_gpu_used=false",
        "failed_or_null=iter23_original_occupied_tail_falsification,iter25_tail_safety_mutation_guard_miss",
        "changed_candidate=iter24_changed_candidate_occupied_tail_control",
        "manifest_failures=",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`",
        "iter23",
        "iter25",
        "changed `iter24` candidate",
        "No provider model was called",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in ["release manifest indexes", "No provider call"]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.receipt_id != "iter31-claim-boundary-release-manifest-pass":
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
    for path in [RESULT, SUMMARY, MANIFEST, COMMAND_OUTPUT, REVIEW, RECEIPT, ITER32]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_summary(failures)
        audit_manifest(failures)
        audit_text_and_receipt(failures)
        audit_no_generated_residue(failures)

    if failures:
        print("claim boundary release manifest audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("claim boundary release manifest audit: clean manifest pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
