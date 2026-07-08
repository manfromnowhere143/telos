#!/usr/bin/env python3
"""Audit the iter20 deterministic behavior-semantic verification proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter20_behavior_semantic_verification")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
REPORT = PROOF / "semantic_report.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECONSTRUCTED_MAIN = PROOF / "reconstructed" / "main.py"
RECONSTRUCTED_README = PROOF / "reconstructed" / "README_agent.md"
RECEIPT = PROOF / "valid" / "receipt_behavior_semantic_verification.json"
ITER19_CHANGES = Path(
    "experiments/iter19_provider_final_inspection_control/proof/raw/codeclash/"
    "PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708185232/players/p1/changes_r1.json"
)
ITER21 = Path("experiments/iter21_opponent_collision_control/HYPOTHESIS.md")

EXPECTED_CASES = {
    "boundary-left": ("left", ["up", "down"]),
    "boundary-right": ("right", ["up", "down"]),
    "boundary-down": ("down", ["left", "right"]),
    "boundary-up": ("up", ["left", "right"]),
    "self-left": ("left", ["up", "right"]),
    "self-right": ("right", ["up", "left"]),
    "self-down": ("down", ["up", "right"]),
    "self-up": ("up", ["down", "right"]),
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
        "schema_version": "telos.behavior_semantic_verification.summary.v1",
        "status": "pass",
        "experiment_id": "iter20_behavior_semantic_verification",
        "source_experiment": "iter19_provider_final_inspection_control",
        "source_changes_path": ITER19_CHANGES.as_posix(),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "module_imported": True,
        "random_choice_probe_used": True,
        "submitted_logic_mutated": False,
        "case_count": 8,
        "passed_case_count": 8,
        "failed_case_count": 0,
        "boundary_case_count": 4,
        "self_collision_case_count": 4,
        "boundary_cases_passed": True,
        "self_collision_cases_passed": True,
        "forbidden_move_observed": False,
        "style_caveat_extra_blank_lines_from_iter19_preserved": True,
        "production_or_live_domain_changed": False,
        "leaderboard_or_swebench_claimed": False,
        "clean_pass": True,
        "next_gate": ITER21.as_posix(),
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"summary {key} expected {value!r}, got {data.get(key)!r}")
    if data.get("reconstructed_files") != ["README_agent.md", "main.py"]:
        failures.append("summary reconstructed_files must list README_agent.md and main.py")
    if data.get("source_changes_sha256") != sha256(ITER19_CHANGES):
        failures.append("summary source_changes_sha256 mismatch")
    if data.get("reconstructed_main_sha256") != sha256(RECONSTRUCTED_MAIN):
        failures.append("summary reconstructed_main_sha256 mismatch")
    if data.get("reconstructed_readme_agent_sha256") != sha256(RECONSTRUCTED_README):
        failures.append("summary reconstructed_readme_agent_sha256 mismatch")

    hashes = data.get("artifact_hashes", {})
    if not isinstance(hashes, dict) or not hashes:
        failures.append("summary artifact_hashes must be non-empty")
        return
    for rel_path, expected_hash in hashes.items():
        path = PROOF / rel_path
        if not path.exists():
            failures.append(f"hashed proof artifact missing: {rel_path}")
            continue
        actual_hash = sha256(path)
        if actual_hash != expected_hash:
            failures.append(f"hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}")


def audit_reconstruction(failures: list[str]) -> None:
    changes = load_json(ITER19_CHANGES)
    modified_files = changes.get("modified_files", {})
    if set(modified_files) != {"README_agent.md", "main.py"}:
        failures.append("iter19 modified file set changed")
        return
    if RECONSTRUCTED_MAIN.read_text(encoding="utf-8") != modified_files["main.py"]:
        failures.append("reconstructed main.py does not exactly match iter19 modified_files content")
    if RECONSTRUCTED_README.read_text(encoding="utf-8") != modified_files["README_agent.md"]:
        failures.append("reconstructed README_agent.md does not exactly match iter19 modified_files content")


def audit_report(failures: list[str]) -> None:
    data = load_json(REPORT)
    expected = {
        "schema_version": "telos.behavior_semantic_verification.report.v1",
        "status": "pass",
        "source_changes_path": ITER19_CHANGES.as_posix(),
        "reconstructed_from_modified_files": True,
        "module_imported": True,
        "random_choice_probe_used": True,
        "submitted_logic_mutated": False,
        "provider_api_calls": 0,
        "cloud_or_gpu_used": False,
        "case_count": 8,
        "passed_case_count": 8,
        "failed_case_count": 0,
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"report {key} expected {value!r}, got {data.get(key)!r}")

    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) != len(EXPECTED_CASES):
        failures.append("report must contain exactly eight cases")
        return
    seen = set()
    for case in cases:
        case_id = case.get("case_id")
        if case_id not in EXPECTED_CASES:
            failures.append(f"unexpected case id: {case_id!r}")
            continue
        if case_id in seen:
            failures.append(f"duplicate case id: {case_id}")
        seen.add(case_id)
        forbidden, expected_safe = EXPECTED_CASES[case_id]
        if case.get("forbidden_move") != forbidden:
            failures.append(f"{case_id}: forbidden move mismatch")
        if case.get("expected_safe_moves") != expected_safe:
            failures.append(f"{case_id}: expected safe moves mismatch")
        if case.get("observed_safe_moves") != expected_safe:
            failures.append(f"{case_id}: observed safe moves mismatch")
        if case.get("selected_move") == forbidden:
            failures.append(f"{case_id}: selected forbidden move")
        if forbidden in case.get("observed_safe_moves", []):
            failures.append(f"{case_id}: forbidden move remained in safe moves")
        if case.get("passed") is not True:
            failures.append(f"{case_id}: case did not pass")
    missing = set(EXPECTED_CASES) - seen
    if missing:
        failures.append(f"missing cases: {sorted(missing)}")


def audit_text_artifacts(failures: list[str]) -> None:
    output = COMMAND_OUTPUT.read_text(encoding="utf-8")
    for required in [
        "behavior semantic verification: pass",
        "provider_api_calls=0",
        "cloud_or_gpu_used=false",
        "cases=8 passed=8 failed=0",
        "boundary-left: pass forbidden=left safe=up,down",
        "self-up: pass forbidden=up safe=down,right",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in [
        "All eight targeted cases passed",
        "formatting caveat remains separate",
        "No provider call, API call, GPU, cloud runner",
    ]:
        if required not in review:
            failures.append(f"review missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `PASS`",
        "eight targeted cases passed",
        "zero provider spend",
        "does not claim a CodeClash leaderboard result",
        "does not claim a SWE-bench result",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")


def audit_receipt(failures: list[str]) -> None:
    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.status != "pass":
        failures.append("receipt status must be pass")
    if receipt.receipt_id != "iter20-behavior-semantic-verification-pass":
        failures.append("unexpected receipt_id")


def main() -> int:
    failures: list[str] = []
    for path in [
        RESULT,
        SUMMARY,
        REPORT,
        COMMAND_OUTPUT,
        REVIEW,
        RECONSTRUCTED_MAIN,
        RECONSTRUCTED_README,
        RECEIPT,
        ITER19_CHANGES,
        ITER21,
    ]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_summary(failures)
        audit_reconstruction(failures)
        audit_report(failures)
        audit_text_artifacts(failures)
        audit_receipt(failures)

    if failures:
        print("behavior semantic verification audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("behavior semantic verification audit: clean semantic pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
