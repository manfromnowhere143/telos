#!/usr/bin/env python3
"""Audit the iter24 tail-safety control proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter24_tail_safety_control")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
REPORT = PROOF / "tail_safety_report.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
CANDIDATE_MAIN = PROOF / "candidate" / "main.py"
CANDIDATE_MANIFEST = PROOF / "candidate" / "patch_manifest.json"
RECEIPT = PROOF / "valid" / "receipt_tail_safety_control.json"
ITER25 = Path("experiments/iter25_tail_safety_mutation_guard/HYPOTHESIS.md")

EXPECTED_CASES = [
    "own-tail-left-occupied-risk",
    "opponent-tail-left-occupied-risk",
    "own-non-tail-left-control",
    "opponent-non-tail-left-control",
]


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
        "schema_version": "telos.tail_safety_control.summary.v1",
        "status": "pass",
        "experiment_id": "iter24_tail_safety_control",
        "source_experiment": "iter23_tail_semantics_falsification",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "tail_occupancy_assumption": "tail_remains_occupied",
        "original_logic_id": "original_iter21",
        "original_submitted_logic_mutated": False,
        "original_tail_failure_preserved": True,
        "candidate_logic_id": "changed_candidate_tail_occupied",
        "candidate_logic_changed": True,
        "changed_candidate_not_presented_as_original": True,
        "candidate_main_path": CANDIDATE_MAIN.as_posix(),
        "case_count_per_logic": 4,
        "candidate_passed_case_count": 4,
        "candidate_failed_case_count": 0,
        "candidate_tail_cases_passed": True,
        "candidate_control_cases_passed": True,
        "candidate_forbidden_tail_move_observed_safe": False,
        "production_or_live_domain_changed": False,
        "leaderboard_or_swebench_claimed": False,
        "game_score_used_as_verifier_evidence": False,
        "clean_pass": True,
        "next_gate": ITER25.as_posix(),
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {data.get(key)!r}")
    if data.get("candidate_main_sha256") != sha256(CANDIDATE_MAIN):
        failures.append("summary candidate_main_sha256 mismatch")
    if data.get("candidate_patch_manifest_sha256") != sha256(CANDIDATE_MANIFEST):
        failures.append("summary candidate_patch_manifest_sha256 mismatch")

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
        "schema_version": "telos.tail_safety_control.report.v1",
        "status": "pass",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "tail_occupancy_assumption": "tail_remains_occupied",
        "original_submitted_logic_mutated": False,
        "candidate_logic_changed": True,
        "changed_candidate_not_presented_as_original": True,
        "original_tail_failure_preserved": True,
        "candidate_clean_pass": True,
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"report {key} expected {value!r}, got {data.get(key)!r}")

    original = data.get("original", {})
    candidate = data.get("candidate", {})
    if original.get("failed_case_ids") != EXPECTED_CASES[:2]:
        failures.append("original failed case ids must preserve iter23 tail failures")
    if original.get("passed_case_count") != 2 or original.get("failed_case_count") != 2:
        failures.append("original pass/fail counts mismatch")
    if candidate.get("passed_case_count") != 4 or candidate.get("failed_case_count") != 0:
        failures.append("candidate pass/fail counts mismatch")
    if candidate.get("forbidden_tail_move_observed_safe") is not False:
        failures.append("candidate must not leave forbidden tail moves safe")

    cases = candidate.get("cases")
    if not isinstance(cases, list) or [case.get("case_id") for case in cases] != EXPECTED_CASES:
        failures.append("candidate cases must match expected order")
        return
    for case in cases:
        case_id = case.get("case_id")
        if case.get("passed") is not True:
            failures.append(f"{case_id}: candidate case must pass")
        if case.get("observed_safe_moves") != ["up", "right"]:
            failures.append(f"{case_id}: candidate safe moves mismatch")
        if case.get("forbidden_move_observed_safe") is not False:
            failures.append(f"{case_id}: forbidden move must be blocked")


def audit_candidate_manifest(failures: list[str]) -> None:
    manifest = load_json(CANDIDATE_MANIFEST)
    if manifest.get("candidate_not_original_submission") is not True:
        failures.append("candidate manifest must state candidate is not original submission")
    if manifest.get("tail_occupancy_assumption") != "tail_remains_occupied":
        failures.append("candidate manifest must record tail_remains_occupied")
    patches = manifest.get("patches")
    if not isinstance(patches, list) or len(patches) != 2:
        failures.append("candidate manifest must contain two patches")
        return
    replacements = {patch.get("replacement") for patch in patches}
    if replacements != {"if next_pos in my_body:", "if next_pos in snake['body']:"}:
        failures.append("candidate replacements mismatch")


def audit_text_and_receipt(failures: list[str]) -> None:
    output = COMMAND_OUTPUT.read_text(encoding="utf-8")
    for required in [
        "tail safety control: pass",
        "original_cases=4 passed=2 failed=2",
        "candidate_cases=4 passed=4 failed=0",
        "candidate own-tail-left-occupied-risk: pass forbidden=left safe=up,right",
        "candidate opponent-tail-left-occupied-risk: pass forbidden=left safe=up,right",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`",
        "`changed_candidate_tail_occupied`",
        "It is not",
        "the original `iter21` submission",
        "No provider model was called",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in [
        "tested a changed candidate separately",
        "not presented as the original provider-submitted logic",
    ]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.receipt_id != "iter24-tail-safety-control-pass":
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
        CANDIDATE_MAIN,
        CANDIDATE_MANIFEST,
        RECEIPT,
        ITER25,
    ]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_summary(failures)
        audit_report(failures)
        audit_candidate_manifest(failures)
        audit_text_and_receipt(failures)
        audit_no_generated_residue(failures)

    if failures:
        print("tail safety control audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("tail safety control audit: clean candidate pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
