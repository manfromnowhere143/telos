#!/usr/bin/env python3
"""Audit the iter35 release-manifest self-coverage proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter35_release_manifest_self_coverage_guard")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
REPORT = PROOF / "self_coverage_report.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECEIPT = PROOF / "valid" / "receipt_release_manifest_self_coverage_guard.json"
ITER36 = Path("experiments/iter36_release_manifest_self_coverage_negative_guard/HYPOTHESIS.md")

EXPECTED_GATES = [
    "iter31_claim_boundary_release_manifest",
    "iter32_claim_boundary_release_manifest_negative_guard",
    "iter33_release_manifest_public_sync_guard",
    "iter34_release_manifest_public_sync_negative_guard",
]
EXPECTED_FAILED_OR_NULL = [
    "iter23_original_occupied_tail_falsification",
    "iter25_tail_safety_mutation_guard_miss",
]
EXPECTED_CHANGED_CANDIDATE = ["iter24_changed_candidate_occupied_tail_control"]


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
        "schema_version": "telos.release_manifest_self_coverage_guard.summary.v1",
        "status": "pass",
        "experiment_id": "iter35_release_manifest_self_coverage_guard",
        "source_experiment": "iter31_claim_boundary_release_manifest",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "covered_gate_count": 4,
        "covered_gate_ids": EXPECTED_GATES,
        "self_coverage_valid": True,
        "self_coverage_failure_count": 0,
        "self_coverage_failures": [],
        "self_verification_gates_clean": True,
        "failed_or_null_claim_ids": EXPECTED_FAILED_OR_NULL,
        "failed_null_gates_visible": True,
        "changed_candidate_claim_ids": EXPECTED_CHANGED_CANDIDATE,
        "changed_candidate_boundary_visible": True,
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "model_superiority_claimed": False,
        "clean_pass": True,
        "next_gate": ITER36.as_posix(),
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {data.get(key)!r}")
    if data.get("proof_artifact_count", 0) < 20:
        failures.append("summary proof_artifact_count must cover source proof packets")

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
        "schema_version": "telos.release_manifest_self_coverage_guard.report.v1",
        "status": "pass",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "covered_gate_ids": EXPECTED_GATES,
        "covered_gate_count": 4,
        "self_verification_gates_clean": True,
        "failed_or_null_claim_ids": EXPECTED_FAILED_OR_NULL,
        "failed_null_gates_visible": True,
        "changed_candidate_claim_ids": EXPECTED_CHANGED_CANDIDATE,
        "changed_candidate_boundary_visible": True,
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "model_superiority_claimed": False,
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"report {key} expected {value!r}, got {data.get(key)!r}")
    gates = data.get("covered_gates")
    if not isinstance(gates, list) or len(gates) != len(EXPECTED_GATES):
        failures.append("report covered_gates must contain four entries")
        return
    by_id = {gate.get("experiment_id"): gate for gate in gates}
    if set(by_id) != set(EXPECTED_GATES):
        failures.append(f"covered gate ids mismatch: {sorted(by_id)}")
        return
    for gate_id in EXPECTED_GATES:
        gate = by_id[gate_id]
        if gate.get("status") != "pass" or gate.get("clean_local_pass") is not True:
            failures.append(f"{gate_id}: gate must be a clean local pass")
        for item_key in ["hypothesis", "result", "summary", "primary_report", "receipt"]:
            item = gate.get(item_key, {})
            rel_path = item.get("path")
            path = Path(rel_path or "")
            if not path.exists():
                failures.append(f"{gate_id}: missing {item_key}: {rel_path}")
                continue
            if item.get("sha256") != sha256(path):
                failures.append(f"{gate_id}: stale {item_key} hash")
        artifacts = gate.get("proof_artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            failures.append(f"{gate_id}: proof_artifacts must be non-empty")
            continue
        for artifact in artifacts:
            rel_path = artifact.get("path")
            path = Path(rel_path or "")
            if not path.exists():
                failures.append(f"{gate_id}: missing proof artifact: {rel_path}")
                continue
            if artifact.get("sha256") != sha256(path):
                failures.append(f"{gate_id}: stale proof artifact hash: {rel_path}")


def audit_text_and_receipt(failures: list[str]) -> None:
    output = COMMAND_OUTPUT.read_text(encoding="utf-8")
    for required in [
        "release manifest self coverage guard: pass",
        "provider_api_calls=0",
        "cloud_or_gpu_used=false",
        "self_verification_gates_clean=true",
        "failed_null_gates_visible=true",
        "self_coverage_failures=",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`",
        "iter31",
        "iter34",
        "iter23",
        "iter25",
        "No provider model was called",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in ["self-coverage guard indexes", "No provider call"]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.receipt_id != "iter35-release-manifest-self-coverage-guard-pass":
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
    for path in [RESULT, SUMMARY, REPORT, COMMAND_OUTPUT, REVIEW, RECEIPT, ITER36]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_summary(failures)
        audit_report(failures)
        audit_text_and_receipt(failures)
        audit_no_generated_residue(failures)

    if failures:
        print("release manifest self coverage guard audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("release manifest self coverage guard audit: clean self-coverage pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
