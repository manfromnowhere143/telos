#!/usr/bin/env python3
"""Audit the iter23 tail-semantics falsification proof bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import ProofValidationError, load_receipt


EXPERIMENT = Path("experiments/iter23_tail_semantics_falsification")
PROOF = EXPERIMENT / "proof"
RESULT = EXPERIMENT / "RESULT.md"
SUMMARY = PROOF / "run_summary.json"
REPORT = PROOF / "tail_semantics_report.json"
COMMAND_OUTPUT = PROOF / "command_output.txt"
REVIEW = PROOF / "review.md"
RECEIPT = PROOF / "valid" / "receipt_tail_semantics_falsification.json"
ITER24 = Path("experiments/iter24_tail_safety_control/HYPOTHESIS.md")

TAIL_RISK_CASE_IDS = [
    "own-tail-left-occupied-risk",
    "opponent-tail-left-occupied-risk",
]
TAIL_RISK_CASES = set(TAIL_RISK_CASE_IDS)
CONTROL_CASE_IDS = [
    "own-non-tail-left-control",
    "opponent-non-tail-left-control",
]
CONTROL_CASES = set(CONTROL_CASE_IDS)


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
        "schema_version": "telos.tail_semantics_falsification.summary.v1",
        "status": "fail",
        "experiment_id": "iter23_tail_semantics_falsification",
        "source_experiment": "iter21_opponent_collision_control",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "tail_occupancy_assumption": "tail_remains_occupied",
        "submitted_logic_mutated": False,
        "case_count": 4,
        "passed_case_count": 2,
        "failed_case_count": 2,
        "failed_case_ids": TAIL_RISK_CASE_IDS,
        "own_tail_risk_detected": True,
        "opponent_tail_risk_detected": True,
        "non_tail_controls_passed": True,
        "production_or_live_domain_changed": False,
        "leaderboard_or_swebench_claimed": False,
        "game_score_used_as_verifier_evidence": False,
        "clean_pass": False,
        "quality_failure": True,
        "next_gate": ITER24.as_posix(),
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
        "schema_version": "telos.tail_semantics_falsification.report.v1",
        "status": "fail",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "tail_occupancy_assumption": "tail_remains_occupied",
        "submitted_logic_mutated": False,
        "case_count": 4,
        "passed_case_count": 2,
        "failed_case_count": 2,
        "failed_case_ids": TAIL_RISK_CASE_IDS,
        "own_tail_risk_detected": True,
        "opponent_tail_risk_detected": True,
        "non_tail_controls_passed": True,
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"report {key} expected {value!r}, got {data.get(key)!r}")

    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) != 4:
        failures.append("report cases must contain four cases")
        return

    seen = set()
    for case in cases:
        case_id = case.get("case_id")
        seen.add(case_id)
        if case.get("tail_occupancy_assumption") != "tail_remains_occupied":
            failures.append(f"{case_id}: missing tail_remains_occupied assumption")
        if case_id in TAIL_RISK_CASES:
            if case.get("passed") is not False:
                failures.append(f"{case_id}: tail risk case must fail")
            if case.get("forbidden_move_observed_safe") is not True:
                failures.append(f"{case_id}: forbidden tail move must remain observed safe")
            if case.get("observed_safe_moves") != ["up", "left", "right"]:
                failures.append(f"{case_id}: unexpected safe-move list")
        elif case_id in CONTROL_CASES:
            if case.get("passed") is not True:
                failures.append(f"{case_id}: control case must pass")
            if case.get("forbidden_move_observed_safe") is not False:
                failures.append(f"{case_id}: forbidden non-tail move must be blocked")
            if case.get("observed_safe_moves") != ["up", "right"]:
                failures.append(f"{case_id}: unexpected safe-move list")
        else:
            failures.append(f"unexpected case id: {case_id!r}")

    expected_seen = TAIL_RISK_CASES | CONTROL_CASES
    if seen != expected_seen:
        failures.append(
            f"case ids mismatch: expected {sorted(expected_seen)}, got {sorted(seen)}"
        )


def audit_text_and_receipt(failures: list[str]) -> None:
    output = COMMAND_OUTPUT.read_text(encoding="utf-8")
    for required in [
        "tail semantics falsification: fail",
        "tail_occupancy_assumption=tail_remains_occupied",
        "cases=4 passed=2 failed=2",
        "own-tail-left-occupied-risk: fail forbidden=left safe=up,left,right",
        "opponent-tail-left-occupied-risk: fail forbidden=left safe=up,left,right",
        "own-non-tail-left-control: pass forbidden=left safe=up,right",
        "opponent-non-tail-left-control: pass forbidden=left safe=up,right",
    ]:
        if required not in output:
            failures.append(f"command output missing: {required}")

    result = RESULT.read_text(encoding="utf-8")
    for required in [
        "Status: `FAIL`",
        "`tail_remains_occupied`",
        "both occupied-tail risk cases left",
        "forbidden `left` move",
        "No provider model was called",
    ]:
        if required not in result:
            failures.append(f"result missing: {required}")

    review = REVIEW.read_text(encoding="utf-8")
    for required in [
        "explicit assumption `tail_remains_occupied`",
        "occupied-tail risk cases leave the forbidden tail move",
    ]:
        if required not in review:
            failures.append(f"review missing: {required}")

    try:
        receipt = load_receipt(RECEIPT)
    except (ProofValidationError, json.JSONDecodeError) as exc:
        failures.append(f"receipt invalid: {exc}")
        return
    if receipt.receipt_id != "iter23-tail-semantics-falsification-fail":
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
    for path in [RESULT, SUMMARY, REPORT, COMMAND_OUTPUT, REVIEW, RECEIPT, ITER24]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if not failures:
        audit_summary(failures)
        audit_report(failures)
        audit_text_and_receipt(failures)
        audit_no_generated_residue(failures)

    if failures:
        print("tail semantics falsification audit failed:")
        for failure in failures:
            print(" -", failure)
        return 1

    print("tail semantics falsification audit: clean failure publication")
    return 0


if __name__ == "__main__":
    sys.exit(main())
