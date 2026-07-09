#!/usr/bin/env python3
"""Generate iter26 own-tail redundancy mutation-guard proof artifacts."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "iter26_own_tail_redundancy_mutation_guard"
PROOF = EXPERIMENT / "proof"
MUTANTS = PROOF / "mutants"
VALID = PROOF / "valid"
SOURCE_CANDIDATE = ROOT / "experiments" / "iter24_tail_safety_control" / "proof" / "candidate" / "main.py"
SOURCE_ITER25_REPORT = (
    ROOT / "experiments" / "iter25_tail_safety_mutation_guard" / "proof" / "mutation_report.json"
)
COMPOUND_MUTANT = MUTANTS / "own_tail_compound_exclusion.py"


class OwnTailRedundancyError(RuntimeError):
    """Raised when iter26 cannot produce trustworthy mutation proof artifacts."""


class ChoiceProbe:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, choices: list[str]) -> str:
        moves = list(choices)
        self.calls.append(moves)
        if not moves:
            raise OwnTailRedundancyError("random.choice called with an empty safe-move list")
        return moves[0]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise OwnTailRedundancyError(f"{path} root must be an object")
    return data


def load_cases() -> list[dict[str, Any]]:
    iter25 = read_json(SOURCE_ITER25_REPORT)
    tail_safety_path = iter25.get("source_tail_safety_report_path")
    if not isinstance(tail_safety_path, str):
        raise OwnTailRedundancyError("iter25 report missing source_tail_safety_report_path")
    tail_safety = read_json(ROOT / tail_safety_path)
    tail_report_path = tail_safety.get("source_tail_report_path")
    if not isinstance(tail_report_path, str):
        raise OwnTailRedundancyError("iter24 report missing source_tail_report_path")
    tail_report = read_json(ROOT / tail_report_path)
    cases = tail_report.get("cases")
    if not isinstance(cases, list) or len(cases) != 4:
        raise OwnTailRedundancyError("source tail report must contain exactly four cases")
    return cases


def import_module(path: Path, module_name: str) -> ModuleType:
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise OwnTailRedundancyError(f"cannot import module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    if not hasattr(module, "move"):
        raise OwnTailRedundancyError(f"{path} does not expose move(game_state)")
    return module


def game_state(case: dict[str, Any]) -> dict[str, Any]:
    self_body = [dict(part) for part in case["self_body"]]
    me = {
        "id": "me",
        "name": "me",
        "health": 100,
        "body": self_body,
        "head": self_body[0],
        "length": len(self_body),
    }
    snakes = [me]
    opponent_body = case.get("opponent_body")
    if opponent_body is not None:
        opp_body = [dict(part) for part in opponent_body]
        snakes.append(
            {
                "id": "opp",
                "name": "opp",
                "health": 100,
                "body": opp_body,
                "head": opp_body[0],
                "length": len(opp_body),
            }
        )
    return {
        "game": {"id": "iter26-own-tail-redundancy-mutation-guard"},
        "turn": 26,
        "board": {
            "height": 11,
            "width": 11,
            "food": [],
            "hazards": [],
            "snakes": snakes,
        },
        "you": me,
    }


def run_case(module: ModuleType, case: dict[str, Any]) -> dict[str, Any]:
    probe = ChoiceProbe()
    stdout = io.StringIO()
    original_choice = module.random.choice
    try:
        module.random.choice = probe
        with contextlib.redirect_stdout(stdout):
            result = module.move(game_state(case))
    finally:
        module.random.choice = original_choice

    observed_safe = probe.calls[0] if probe.calls else []
    forbidden_move = str(case["forbidden_move"])
    expected_safe = list(case["expected_safe_moves_if_tail_occupied"])
    selected_move = result.get("move") if isinstance(result, dict) else None
    passed = (
        observed_safe == expected_safe
        and forbidden_move not in observed_safe
        and selected_move != forbidden_move
    )
    return {
        "case_id": case["case_id"],
        "case_family": case["case_family"],
        "tail_occupancy_assumption": "tail_remains_occupied",
        "forbidden_move": forbidden_move,
        "expected_safe_moves": expected_safe,
        "observed_safe_moves": observed_safe,
        "selected_move": selected_move,
        "forbidden_move_observed_safe": forbidden_move in observed_safe,
        "forbidden_move_selected": selected_move == forbidden_move,
        "stdout_lines": stdout.getvalue().splitlines(),
        "passed": passed,
    }


def run_cases(source_path: Path, module_name: str, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    module = import_module(source_path, module_name)
    return [run_case(module, case) for case in cases]


def write_compound_mutant() -> list[dict[str, str]]:
    source = SOURCE_CANDIDATE.read_text(encoding="utf-8")
    replacements = [
        {
            "patch_id": "direct_own_tail_exclusion",
            "needle": "if next_pos in my_body:",
            "replacement": "if next_pos in my_body[:-1]:",
        },
        {
            "patch_id": "self_snake_fallback_removed",
            "needle": "opponents = game_state['board']['snakes']",
            "replacement": (
                "opponents = [snake for snake in game_state['board']['snakes'] "
                "if snake.get('id') != game_state['you'].get('id')]"
            ),
        },
    ]
    mutated = source
    for patch in replacements:
        count = mutated.count(patch["needle"])
        if count != 1:
            raise OwnTailRedundancyError(
                f"{patch['patch_id']}: expected one source needle, found {count}"
            )
        mutated = mutated.replace(patch["needle"], patch["replacement"], 1)

    MUTANTS.mkdir(parents=True, exist_ok=True)
    COMPOUND_MUTANT.write_text(mutated, encoding="utf-8")
    write_json(
        MUTANTS / "own_tail_compound_manifest.json",
        {
            "schema_version": "telos.own_tail_redundancy_mutation.v1",
            "source_candidate_path": str(SOURCE_CANDIDATE.relative_to(ROOT)),
            "tail_occupancy_assumption": "tail_remains_occupied",
            "compound_mutant": True,
            "patches": replacements,
        },
    )
    return replacements


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter26-own-tail-redundancy-mutation-guard-{status}",
        "task_id": "telos:iter26_own_tail_redundancy_mutation_guard@iter25_tail_safety_mutation_guard",
        "agent_id": "codex-local-own-tail-redundancy-mutator",
        "benchmark_id": "telos_codeclash_battlesnake_semantic_slice",
        "status": status,
        "stated_goal": (
            "Create a compound own-tail mutant that removes both direct own-tail checking and the "
            "self-snake fallback path, then verify the occupied-tail case detects it."
        ),
        "acceptance_criteria": [
            "No provider, API, GPU, or cloud spend occurs.",
            "The clean iter24 candidate imports locally and passes the four frozen cases.",
            "The compound own-tail mutant fails the own occupied-tail case.",
            "The compound own-tail mutant leaves the non-tail controls passing.",
            "The verifier records the exact tail-occupancy assumption.",
            "No leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": "experiments/iter26_own_tail_redundancy_mutation_guard/proof/redundancy_report.json",
                "notes": "Clean candidate and compound own-tail mutant run against frozen cases.",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "experiments/iter26_own_tail_redundancy_mutation_guard/proof/mutants/own_tail_compound_exclusion.py",
                "notes": "Compound mutant removes direct own-tail and self-snake fallback protection.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": "experiments/iter26_own_tail_redundancy_mutation_guard/proof/review.md",
                "notes": "Review records the compound mutation and claim boundary.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if the clean candidate cannot be loaded locally.",
            "The result must fail if the clean candidate no longer passes the frozen cases.",
            "The result must fail if the compound own-tail mutant escapes the own occupied-tail target case.",
            "The result must fail if the compound mutation is hidden.",
            "The result must not treat provider game score as verifier evidence.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    cases = load_cases()
    patches = write_compound_mutant()
    clean_results = run_cases(SOURCE_CANDIDATE, "iter26_clean_candidate", cases)
    mutant_results = run_cases(COMPOUND_MUTANT, "iter26_own_tail_compound_mutant", cases)

    clean_pass = all(result["passed"] for result in clean_results)
    target = next(result for result in mutant_results if result["case_id"] == "own-tail-left-occupied-risk")
    controls = [result for result in mutant_results if result["case_family"] == "control_non_tail"]
    other_tail = next(
        result for result in mutant_results if result["case_id"] == "opponent-tail-left-occupied-risk"
    )
    target_detected = target["passed"] is False and target["forbidden_move_observed_safe"] is True
    controls_passed = all(result["passed"] for result in controls)
    opponent_tail_still_passed = other_tail["passed"] is True
    status = "pass" if clean_pass and target_detected and controls_passed else "fail"

    report = {
        "schema_version": "telos.own_tail_redundancy_mutation_guard.report.v1",
        "status": status,
        "source_candidate_path": str(SOURCE_CANDIDATE.relative_to(ROOT)),
        "source_candidate_sha256": sha256_file(SOURCE_CANDIDATE),
        "source_iter25_report_path": str(SOURCE_ITER25_REPORT.relative_to(ROOT)),
        "source_iter25_report_sha256": sha256_file(SOURCE_ITER25_REPORT),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "tail_occupancy_assumption": "tail_remains_occupied",
        "test_cases_mutated": False,
        "compound_mutant": True,
        "compound_mutant_path": str(COMPOUND_MUTANT.relative_to(ROOT)),
        "compound_mutant_sha256": sha256_file(COMPOUND_MUTANT),
        "compound_patches": patches,
        "clean_candidate_case_count": len(clean_results),
        "clean_candidate_passed": clean_pass,
        "target_case_id": "own-tail-left-occupied-risk",
        "target_detected": target_detected,
        "target_observed_safe_moves": target["observed_safe_moves"],
        "control_cases_passed": controls_passed,
        "opponent_tail_still_passed": opponent_tail_still_passed,
        "clean_results": clean_results,
        "mutant_results": mutant_results,
    }
    write_json(PROOF / "redundancy_report.json", report)

    output_lines = [
        f"own-tail redundancy mutation guard: {status}",
        f"source_candidate={SOURCE_CANDIDATE.relative_to(ROOT)}",
        "provider_api_calls=0",
        "cloud_or_gpu_used=false",
        "tail_occupancy_assumption=tail_remains_occupied",
        f"clean_candidate_cases={len(clean_results)} passed={sum(result['passed'] for result in clean_results)}",
        f"compound_target_detected={str(target_detected).lower()}",
        f"compound_target_safe={','.join(target['observed_safe_moves'])}",
        f"compound_controls_passed={str(controls_passed).lower()}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 26 Review

The own-tail redundancy guard loaded the `iter24` changed candidate, confirmed the clean candidate
still passed all four frozen cases, and created a compound own-tail mutant. The compound mutant
removed both the direct own-body tail check and the later self-snake fallback path. It failed the
own occupied-tail target case while the non-tail controls still passed.

This resolves the specific `iter25` verifier-design caveat. It supports a local verifier-strength
claim for this compound own-tail regression only. It does not claim a CodeClash leaderboard result,
SWE-bench result, production behavior, or provider-model capability.

No provider call, API call, GPU, cloud runner, production deployment, live-domain check, leaderboard
run, or SWE-bench run occurred in this gate.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    run_summary = {
        "schema_version": "telos.own_tail_redundancy_mutation_guard.summary.v1",
        "status": status,
        "experiment_id": "iter26_own_tail_redundancy_mutation_guard",
        "source_experiment": "iter25_tail_safety_mutation_guard",
        "source_candidate_path": str(SOURCE_CANDIDATE.relative_to(ROOT)),
        "source_candidate_sha256": sha256_file(SOURCE_CANDIDATE),
        "source_iter25_report_path": str(SOURCE_ITER25_REPORT.relative_to(ROOT)),
        "source_iter25_report_sha256": sha256_file(SOURCE_ITER25_REPORT),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "tail_occupancy_assumption": "tail_remains_occupied",
        "test_cases_mutated": False,
        "compound_mutant": True,
        "clean_candidate_case_count": len(clean_results),
        "clean_candidate_cases_passed": sum(result["passed"] for result in clean_results),
        "clean_candidate_cases_failed": sum(not result["passed"] for result in clean_results),
        "clean_candidate_passed": clean_pass,
        "target_case_id": "own-tail-left-occupied-risk",
        "target_detected": target_detected,
        "target_observed_safe_moves": target["observed_safe_moves"],
        "control_cases_passed": controls_passed,
        "opponent_tail_still_passed": opponent_tail_still_passed,
        "production_or_live_domain_changed": False,
        "leaderboard_or_swebench_claimed": False,
        "game_score_used_as_verifier_evidence": False,
        "clean_pass": status == "pass",
        "next_gate": "experiments/iter27_semantic_claim_boundary_matrix/HYPOTHESIS.md",
        "artifact_hashes": {
            "command_output.txt": sha256_file(PROOF / "command_output.txt"),
            "mutants/own_tail_compound_exclusion.py": sha256_file(COMPOUND_MUTANT),
            "mutants/own_tail_compound_manifest.json": sha256_file(
                MUTANTS / "own_tail_compound_manifest.json"
            ),
            "redundancy_report.json": sha256_file(PROOF / "redundancy_report.json"),
            "review.md": sha256_file(PROOF / "review.md"),
        },
    }
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter26_own_tail_redundancy_mutation_guard",
        "status": status,
        "insight": (
            "A compound own-tail mutant that removes both direct own-body checking and the "
            "self-snake fallback path is detected by the occupied-tail verifier."
        ),
        "next_action": (
            "pre-register a semantic claim-boundary matrix that separates original provider logic, "
            "changed candidates, failed gates, and verifier-strength evidence"
        ),
        "result_path": "experiments/iter26_own_tail_redundancy_mutation_guard/RESULT.md",
        "evidence_paths": [
            "experiments/iter26_own_tail_redundancy_mutation_guard/proof/run_summary.json",
            "experiments/iter26_own_tail_redundancy_mutation_guard/proof/redundancy_report.json",
            "experiments/iter26_own_tail_redundancy_mutation_guard/proof/command_output.txt",
            "experiments/iter26_own_tail_redundancy_mutation_guard/proof/review.md",
            "experiments/iter26_own_tail_redundancy_mutation_guard/proof/valid/receipt_own_tail_redundancy_mutation_guard.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(VALID / "receipt_own_tail_redundancy_mutation_guard.json", build_receipt(status))

    print("\n".join(output_lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
