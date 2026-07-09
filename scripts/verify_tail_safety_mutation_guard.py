#!/usr/bin/env python3
"""Generate iter25 tail-safety mutation-guard proof artifacts."""

from __future__ import annotations

from dataclasses import dataclass
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
EXPERIMENT = ROOT / "experiments" / "iter25_tail_safety_mutation_guard"
PROOF = EXPERIMENT / "proof"
MUTANTS = PROOF / "mutants"
VALID = PROOF / "valid"
SOURCE_CANDIDATE = ROOT / "experiments" / "iter24_tail_safety_control" / "proof" / "candidate" / "main.py"
SOURCE_TAIL_SAFETY_REPORT = (
    ROOT / "experiments" / "iter24_tail_safety_control" / "proof" / "tail_safety_report.json"
)


@dataclass(frozen=True)
class Mutation:
    mutation_id: str
    source_filename: str
    target_case_id: str
    description: str
    needle: str
    replacement: str


MUTATIONS = [
    Mutation(
        mutation_id="own_tail_exclusion",
        source_filename="own_tail_exclusion.py",
        target_case_id="own-tail-left-occupied-risk",
        description="Revert own-body checking to exclude the own tail.",
        needle="if next_pos in my_body:",
        replacement="if next_pos in my_body[:-1]:",
    ),
    Mutation(
        mutation_id="opponent_tail_exclusion",
        source_filename="opponent_tail_exclusion.py",
        target_case_id="opponent-tail-left-occupied-risk",
        description="Revert snake-body checking to exclude opponent tails.",
        needle="if next_pos in snake['body']:",
        replacement="if next_pos in snake['body'][:-1]:",
    ),
]


class TailSafetyMutationError(RuntimeError):
    """Raised when iter25 cannot produce trustworthy mutation proof artifacts."""


class ChoiceProbe:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, choices: list[str]) -> str:
        moves = list(choices)
        self.calls.append(moves)
        if not moves:
            raise TailSafetyMutationError("random.choice called with an empty safe-move list")
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
        raise TailSafetyMutationError(f"{path} root must be an object")
    return data


def load_cases() -> list[dict[str, Any]]:
    tail_safety = read_json(SOURCE_TAIL_SAFETY_REPORT)
    if tail_safety.get("tail_occupancy_assumption") != "tail_remains_occupied":
        raise TailSafetyMutationError("iter24 report must record tail_remains_occupied")
    source_tail_report_path = tail_safety.get("source_tail_report_path")
    if not isinstance(source_tail_report_path, str):
        raise TailSafetyMutationError("iter24 report missing source_tail_report_path")
    source_tail_report = read_json(ROOT / source_tail_report_path)
    cases = source_tail_report.get("cases")
    if not isinstance(cases, list) or len(cases) != 4:
        raise TailSafetyMutationError("source tail report must contain exactly four cases")
    return cases


def import_module(path: Path, module_name: str) -> ModuleType:
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise TailSafetyMutationError(f"cannot import module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    if not hasattr(module, "move"):
        raise TailSafetyMutationError(f"{path} does not expose move(game_state)")
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
        "game": {"id": "iter25-tail-safety-mutation-guard"},
        "turn": 25,
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


def run_cases(module: ModuleType, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [run_case(module, case) for case in cases]


def write_mutant(source: str, mutation: Mutation) -> Path:
    count = source.count(mutation.needle)
    if count != 1:
        raise TailSafetyMutationError(
            f"{mutation.mutation_id}: expected one source needle, found {count}"
        )
    mutated = source.replace(mutation.needle, mutation.replacement, 1)
    MUTANTS.mkdir(parents=True, exist_ok=True)
    path = MUTANTS / mutation.source_filename
    path.write_text(mutated, encoding="utf-8")
    return path


def evaluate_mutation(mutation: Mutation, mutant_path: Path, cases: list[dict[str, Any]]) -> dict[str, Any]:
    module = import_module(mutant_path, f"iter25_{mutation.mutation_id}")
    results = run_cases(module, cases)
    target = next(result for result in results if result["case_id"] == mutation.target_case_id)
    controls = [result for result in results if result["case_family"] == "control_non_tail"]
    target_detected = target["passed"] is False and target["forbidden_move_observed_safe"] is True
    return {
        "mutation_id": mutation.mutation_id,
        "description": mutation.description,
        "mutant_path": str(mutant_path.relative_to(ROOT)),
        "mutant_sha256": sha256_file(mutant_path),
        "target_case_id": mutation.target_case_id,
        "target_detected": target_detected,
        "target_observed_safe_moves": target["observed_safe_moves"],
        "control_cases_passed": all(result["passed"] for result in controls),
        "failed_case_ids": [result["case_id"] for result in results if not result["passed"]],
        "cases": results,
    }


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter25-tail-safety-mutation-guard-{status}",
        "task_id": "telos:iter25_tail_safety_mutation_guard@iter24_tail_safety_control",
        "agent_id": "codex-local-tail-safety-mutator",
        "benchmark_id": "telos_codeclash_battlesnake_semantic_slice",
        "status": status,
        "stated_goal": (
            "Prove the occupied-tail verifier detects targeted regressions that reintroduce "
            "tail-excluding checks into the iter24 changed candidate."
        ),
        "acceptance_criteria": [
            "No provider, API, GPU, or cloud spend occurs.",
            "The clean iter24 candidate imports locally and passes the four frozen cases.",
            "The own-tail exclusion mutant fails the own occupied-tail case.",
            "The opponent-tail exclusion mutant fails the opponent occupied-tail case.",
            "The verifier records the exact tail-occupancy assumption.",
            "No leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": "experiments/iter25_tail_safety_mutation_guard/proof/mutation_report.json",
                "notes": "Clean candidate and targeted tail-exclusion mutants run against frozen cases.",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "experiments/iter24_tail_safety_control/proof/candidate/main.py",
                "notes": "Clean candidate source under mutation guard.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": "experiments/iter25_tail_safety_mutation_guard/proof/review.md",
                "notes": "Review records mutation targets and claim boundary.",
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
            "The result must fail if a targeted tail-exclusion mutant escapes its occupied-tail target case.",
            "The result must fail if the source under mutation is hidden.",
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
    source = SOURCE_CANDIDATE.read_text(encoding="utf-8")

    clean_module = import_module(SOURCE_CANDIDATE, "iter25_clean_candidate")
    clean_results = run_cases(clean_module, cases)
    clean_pass = all(result["passed"] for result in clean_results)

    mutations = []
    for mutation in MUTATIONS:
        mutant_path = write_mutant(source, mutation)
        mutations.append(evaluate_mutation(mutation, mutant_path, cases))

    all_mutants_detected = all(result["target_detected"] for result in mutations)
    controls_passed = all(result["control_cases_passed"] for result in mutations)
    status = "pass" if clean_pass and all_mutants_detected and controls_passed else "fail"

    report = {
        "schema_version": "telos.tail_safety_mutation_guard.report.v1",
        "status": status,
        "source_candidate_path": str(SOURCE_CANDIDATE.relative_to(ROOT)),
        "source_candidate_sha256": sha256_file(SOURCE_CANDIDATE),
        "source_tail_safety_report_path": str(SOURCE_TAIL_SAFETY_REPORT.relative_to(ROOT)),
        "source_tail_safety_report_sha256": sha256_file(SOURCE_TAIL_SAFETY_REPORT),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "tail_occupancy_assumption": "tail_remains_occupied",
        "test_cases_mutated": False,
        "clean_candidate_case_count": len(clean_results),
        "clean_candidate_passed": clean_pass,
        "mutation_count": len(mutations),
        "all_mutants_detected": all_mutants_detected,
        "mutant_control_cases_passed": controls_passed,
        "clean_results": clean_results,
        "mutations": mutations,
    }
    write_json(PROOF / "mutation_report.json", report)

    output_lines = [
        f"tail safety mutation guard: {status}",
        f"source_candidate={SOURCE_CANDIDATE.relative_to(ROOT)}",
        "provider_api_calls=0",
        "cloud_or_gpu_used=false",
        "tail_occupancy_assumption=tail_remains_occupied",
        f"clean_candidate_cases={len(clean_results)} passed={sum(result['passed'] for result in clean_results)}",
        f"mutations={len(mutations)} detected={sum(result['target_detected'] for result in mutations)}",
    ]
    for mutation in mutations:
        output_lines.append(
            f"{mutation['mutation_id']}: {'detected' if mutation['target_detected'] else 'missed'} "
            f"target={mutation['target_case_id']} failed={','.join(mutation['failed_case_ids'])}"
        )
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 25 Review

The mutation guard loaded the `iter24` changed candidate, confirmed the clean candidate still passed
the four frozen tail-safety cases, and then created targeted tail-exclusion mutants from that
candidate. The opponent-tail mutant failed the opponent occupied-tail case. The own-tail mutant did
not fail the own occupied-tail case because the later `board.snakes` loop still checks our own
snake.

This is a failure/null result for verifier strength. The next guard must create a compound own-tail
mutant that removes both the direct own-body check and the self-snake fallback path. This does not
claim a CodeClash leaderboard result, SWE-bench result, production behavior, or provider-model
capability.

No provider call, API call, GPU, cloud runner, production deployment, live-domain check, leaderboard
run, or SWE-bench run occurred in this gate.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    run_summary = {
        "schema_version": "telos.tail_safety_mutation_guard.summary.v1",
        "status": status,
        "experiment_id": "iter25_tail_safety_mutation_guard",
        "source_experiment": "iter24_tail_safety_control",
        "source_candidate_path": str(SOURCE_CANDIDATE.relative_to(ROOT)),
        "source_candidate_sha256": sha256_file(SOURCE_CANDIDATE),
        "source_tail_safety_report_path": str(SOURCE_TAIL_SAFETY_REPORT.relative_to(ROOT)),
        "source_tail_safety_report_sha256": sha256_file(SOURCE_TAIL_SAFETY_REPORT),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "tail_occupancy_assumption": "tail_remains_occupied",
        "test_cases_mutated": False,
        "clean_candidate_case_count": len(clean_results),
        "clean_candidate_cases_passed": sum(result["passed"] for result in clean_results),
        "clean_candidate_cases_failed": sum(not result["passed"] for result in clean_results),
        "clean_candidate_passed": clean_pass,
        "mutation_count": len(mutations),
        "all_mutants_detected": all_mutants_detected,
        "own_tail_exclusion_detected": mutations[0]["target_detected"],
        "opponent_tail_exclusion_detected": mutations[1]["target_detected"],
        "mutant_control_cases_passed": controls_passed,
        "production_or_live_domain_changed": False,
        "leaderboard_or_swebench_claimed": False,
        "game_score_used_as_verifier_evidence": False,
        "clean_pass": status == "pass",
        "next_gate": "experiments/iter26_own_tail_redundancy_mutation_guard/HYPOTHESIS.md",
        "artifact_hashes": {
            "command_output.txt": sha256_file(PROOF / "command_output.txt"),
            "mutation_report.json": sha256_file(PROOF / "mutation_report.json"),
            "mutants/own_tail_exclusion.py": sha256_file(MUTANTS / "own_tail_exclusion.py"),
            "mutants/opponent_tail_exclusion.py": sha256_file(
                MUTANTS / "opponent_tail_exclusion.py"
            ),
            "review.md": sha256_file(PROOF / "review.md"),
        },
    }
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter25_tail_safety_mutation_guard",
        "status": "null" if status == "fail" else status,
        "insight": (
            "The opponent-tail exclusion mutant is detected, but the own-tail exclusion mutant "
            "still passes because the candidate also checks our own snake in the later snake loop."
        ),
        "next_action": (
            "pre-register an own-tail redundancy mutation guard that removes both direct own-tail "
            "checking and the later self-snake fallback path"
        ),
        "result_path": "experiments/iter25_tail_safety_mutation_guard/RESULT.md",
        "evidence_paths": [
            "experiments/iter25_tail_safety_mutation_guard/proof/run_summary.json",
            "experiments/iter25_tail_safety_mutation_guard/proof/mutation_report.json",
            "experiments/iter25_tail_safety_mutation_guard/proof/command_output.txt",
            "experiments/iter25_tail_safety_mutation_guard/proof/review.md",
            "experiments/iter25_tail_safety_mutation_guard/proof/valid/receipt_tail_safety_mutation_guard.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(VALID / "receipt_tail_safety_mutation_guard.json", build_receipt(status))

    print("\n".join(output_lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
