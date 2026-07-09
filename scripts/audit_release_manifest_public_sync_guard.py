#!/usr/bin/env python3
"""Audit the iter33 release-manifest public-sync proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter33_release_manifest_public_sync_guard")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
REPORT = PROOF / "public_sync_report.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECEIPT = PROOF / "valid" / "receipt_release_manifest_public_sync_guard.json"
ITER34 = Path("experiments/iter34_release_manifest_public_sync_negative_guard/HYPOTHESIS.md")

EXPECTED_PUBLIC_FILES = ["README.md", "docs/REPORT.md", "docs/NEXT_PHASE.md", "CONTINUITY.md"]
EXPECTED_CHECK_COUNT = 16


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
        "schema_version": "telos.release_manifest_public_sync_guard.summary.v1",
        "status": "pass",
        "experiment_id": "iter33_release_manifest_public_sync_guard",
        "source_experiment": "iter31_claim_boundary_release_manifest",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "checked_public_files": EXPECTED_PUBLIC_FILES,
        "check_count": EXPECTED_CHECK_COUNT,
        "failed_check_count": 0,
        "failed_check_ids": [],
        "release_manifest_referenced": True,
        "failed_null_gates_visible": True,
        "changed_candidate_boundary_visible": True,
        "original_iter21_occupied_tail_safety_claimed": False,
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "model_superiority_claimed": False,
        "clean_pass": True,
        "next_gate": ITER34.as_posix(),
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
        "schema_version": "telos.release_manifest_public_sync_guard.report.v1",
        "status": "pass",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "checked_public_files": EXPECTED_PUBLIC_FILES,
        "check_count": EXPECTED_CHECK_COUNT,
        "failed_check_count": 0,
        "failed_check_ids": [],
        "release_manifest_referenced": True,
        "failed_null_gates_visible": True,
        "changed_candidate_boundary_visible": True,
        "original_iter21_occupied_tail_safety_claimed": False,
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "model_superiority_claimed": False,
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"report {key} expected {value!r}, got {data.get(key)!r}")
    checks = data.get("checks")
    if not isinstance(checks, list) or len(checks) != EXPECTED_CHECK_COUNT:
        failures.append(f"report checks must contain {EXPECTED_CHECK_COUNT} entries")
        return
    if any(check.get("status") != "pass" for check in checks):
        failures.append("all report checks must pass")
    check_ids = {check.get("check_id") for check in checks}
    for required in [
        "manifest_referenced_everywhere",
        "failed_null_rows_visible",
        "changed_candidate_boundary_visible",
        "original_iter21_tail_safety_not_claimed",
        "no_benchmark_or_production_claims",
    ]:
        if required not in check_ids:
            failures.append(f"report missing check: {required}")


def audit_public_prose(failures: list[str]) -> None:
    manifest_path = (
        "experiments/iter31_claim_boundary_release_manifest/proof/"
        "claim_boundary_release_manifest.json"
    )
    for rel_path in EXPECTED_PUBLIC_FILES:
        text = Path(rel_path).read_text(encoding="utf-8")
        expected_path = f"../{manifest_path}" if rel_path.startswith("docs/") else manifest_path
        if expected_path not in text:
            failures.append(f"{rel_path}: missing release manifest reference")


def audit_text_and_receipt(failures: list[str]) -> None:
    output = COMMAND_OUTPUT.read_text(encoding="utf-8")
    for required in [
        "release manifest public sync guard: pass",
        "files=4 checks=16 failed=0",
        "release_manifest_referenced=true",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`",
        "release manifest",
        "iter23",
        "iter25",
        "No provider model was called",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in ["public-sync guard checked", "No provider call"]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.receipt_id != "iter33-release-manifest-public-sync-guard-pass":
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
    for path in [RESULT, SUMMARY, REPORT, COMMAND_OUTPUT, REVIEW, RECEIPT, ITER34]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_summary(failures)
        audit_report(failures)
        audit_public_prose(failures)
        audit_text_and_receipt(failures)
        audit_no_generated_residue(failures)

    if failures:
        print("release manifest public sync guard audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("release manifest public sync guard audit: clean public-sync pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
