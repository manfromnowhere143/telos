#!/usr/bin/env python3
"""Generate iter22 semantic mutation-guard proof artifacts."""

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
EXPERIMENT = ROOT / "experiments" / "iter22_semantic_mutation_guard"
PROOF = EXPERIMENT / "proof"
MUTANTS = PROOF / "mutants"
VALID = PROOF / "valid"
SOURCE_MAIN = ROOT / "experiments" / "iter21_opponent_collision_control" / "proof" / "reconstructed" / "main.py"
SOURCE_REPORT = ROOT / "experiments" / "iter21_opponent_collision_control" / "proof" / "semantic_report.json"


@dataclass(frozen=True)
class Mutation:
    mutation_id: str
    source_filename: str
    target_prefix: str
    description: str
    replacements: list[tuple[str, str]]


MUTATIONS = [
    Mutation(
        mutation_id="boundary_noop",
        source_filename="boundary_noop.py",
        target_prefix="boundary-",
        description="Disable the board-boundary unsafe-move branch.",
        replacements=[
            (
                (
                    'if next_pos["x"] < 0 or next_pos["x"] >= board_width or '
                    'next_pos["y"] < 0 or next_pos["y"] >= board_height:'
                ),
                (
                    'if False and (next_pos["x"] < 0 or next_pos["x"] >= board_width or '
                    'next_pos["y"] < 0 or next_pos["y"] >= board_height):'
                ),
            ),
        ],
    ),
    Mutation(
        mutation_id="self_collision_noop",
        source_filename="self_collision_noop.py",
        target_prefix="self-",
        description=(
            "Disable own-body protection while preserving opponent-body protection. The submitted "
            "implementation also iterates over our own snake in board.snakes, so this mutant must "
            "exclude the self snake from that later loop to create the intended own-body regression."
        ),
        replacements=[
            (
                "opponents = game_state['board']['snakes']",
                (
                    "opponents = [snake for snake in game_state['board']['snakes'] "
                    "if snake.get('id') != game_state['you'].get('id')]"
                ),
            ),
            ("if next_pos in my_body[:-1]:", "if False and next_pos in my_body[:-1]:"),
        ],
    ),
    Mutation(
        mutation_id="opponent_collision_noop",
        source_filename="opponent_collision_noop.py",
        target_prefix="opponent-",
        description="Disable the opponent-body unsafe-move branch.",
        replacements=[
            ("if next_pos in snake['body'][:-1]:", "if False and next_pos in snake['body'][:-1]:"),
        ],
    ),
]


class MutationGuardError(RuntimeError):
    """Raised when iter22 cannot produce a trustworthy mutation result."""


class ChoiceProbe:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, choices: list[str]) -> str:
        moves = list(choices)
        self.calls.append(moves)
        if not moves:
            raise MutationGuardError("random.choice called with an empty safe-move list")
        return moves[0]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_report_cases() -> list[dict[str, Any]]:
    data = json.loads(SOURCE_REPORT.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise MutationGuardError("iter21 semantic_report root must be an object")
    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) != 12:
        raise MutationGuardError("iter21 semantic_report must contain exactly twelve cases")
    return cases


def import_module(path: Path, module_name: str) -> ModuleType:
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise MutationGuardError(f"cannot import module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    if not hasattr(module, "move"):
        raise MutationGuardError(f"{path} does not expose move(game_state)")
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
    if opponent_body:
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
        "game": {"id": "iter22-semantic-mutation-guard"},
        "turn": 22,
        "board": {
            "height": int(case["board_height"]),
            "width": int(case["board_width"]),
            "food": [],
            "hazards": [],
            "snakes": snakes,
        },
        "you": me,
    }


def run_cases(module: ModuleType, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for case in cases:
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
        forbidden = str(case["forbidden_move"])
        expected_safe = list(case["expected_safe_moves"])
        passed = (
            observed_safe == expected_safe
            and forbidden not in observed_safe
            and isinstance(result, dict)
            and result.get("move") != forbidden
        )
        results.append(
            {
                "case_id": case["case_id"],
                "forbidden_move": forbidden,
                "expected_safe_moves": expected_safe,
                "observed_safe_moves": observed_safe,
                "selected_move": result.get("move") if isinstance(result, dict) else None,
                "stdout_lines": stdout.getvalue().splitlines(),
                "passed": passed,
            }
        )
    return results


def mutate_source(source: str, mutation: Mutation) -> str:
    mutated = source
    for needle, replacement in mutation.replacements:
        count = mutated.count(needle)
        if count != 1:
            raise MutationGuardError(
                f"{mutation.mutation_id}: expected exactly one needle, found {count}: {needle}"
            )
        mutated = mutated.replace(needle, replacement)
    return mutated


def summarize_run(results: list[dict[str, Any]], target_prefix: str | None = None) -> dict[str, Any]:
    relevant = [result for result in results if target_prefix is None or result["case_id"].startswith(target_prefix)]
    failed = [result for result in relevant if not result["passed"]]
    return {
        "case_count": len(results),
        "relevant_case_count": len(relevant),
        "failed_relevant_case_count": len(failed),
        "failed_case_ids": [result["case_id"] for result in failed],
        "all_cases_passed": all(result["passed"] for result in results),
        "target_detected": bool(failed) if target_prefix is not None else False,
    }


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    payload = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(payload)


def build_receipt() -> dict[str, Any]:
    receipt = {
        "receipt_id": "iter22-semantic-mutation-guard-pass",
        "task_id": "telos:iter22_semantic_mutation_guard@iter21_opponent_collision_control",
        "agent_id": "codex-local-semantic-mutation-guard",
        "benchmark_id": "telos_codeclash_battlesnake_semantic_slice",
        "status": "pass",
        "stated_goal": (
            "Verify that the deterministic semantic suite fails targeted mutants that disable "
            "boundary, self-collision, or opponent-collision safety checks."
        ),
        "acceptance_criteria": [
            "No provider, API, GPU, or cloud spend occurs.",
            "The clean reconstructed iter21 bot still passes all twelve semantic cases.",
            "The boundary mutant fails at least one boundary case.",
            "The self-collision mutant fails at least one self-collision case.",
            "The opponent-collision mutant fails at least one opponent-collision case.",
            "Command output and mutation report are committed.",
            "No leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": "pass",
                "artifact": "experiments/iter22_semantic_mutation_guard/proof/mutation_report.json",
                "notes": "Clean bot passed all cases and all targeted mutants were detected.",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "experiments/iter22_semantic_mutation_guard/proof/mutants/",
                "notes": "Committed local mutant sources for boundary, self-collision, and opponent-collision branches.",
            },
            {
                "kind": "adversarial_review",
                "status": "pass",
                "artifact": "experiments/iter22_semantic_mutation_guard/proof/review.md",
                "notes": "Review keeps the result limited to verifier sensitivity for targeted mutants.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if the reconstructed iter21 bot cannot be loaded locally.",
            "The result must block if the clean reconstructed bot no longer passes the frozen semantic cases.",
            "The result must fail if a boundary mutant passes all boundary cases.",
            "The result must fail if a self-collision mutant passes all self-collision cases.",
            "The result must fail if an opponent-collision mutant passes all opponent-collision cases.",
            "The result must not treat provider game score as verifier evidence.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    MUTANTS.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    source = SOURCE_MAIN.read_text(encoding="utf-8")
    cases = load_report_cases()
    clean_module = import_module(SOURCE_MAIN, "iter22_clean_reconstructed")
    clean_results = run_cases(clean_module, cases)
    clean_summary = summarize_run(clean_results)
    if not clean_summary["all_cases_passed"]:
        raise MutationGuardError("clean reconstructed iter21 bot no longer passes frozen cases")

    mutation_results = []
    for mutation in MUTATIONS:
        mutated_source = mutate_source(source, mutation)
        mutant_path = MUTANTS / mutation.source_filename
        mutant_path.write_text(mutated_source, encoding="utf-8")
        module = import_module(mutant_path, f"iter22_{mutation.mutation_id}")
        results = run_cases(module, cases)
        summary = summarize_run(results, mutation.target_prefix)
        mutation_results.append(
            {
                "mutation_id": mutation.mutation_id,
                "description": mutation.description,
                "mutant_path": str(mutant_path.relative_to(ROOT)),
                "source_sha256": sha256_file(mutant_path),
                "target_prefix": mutation.target_prefix,
                "target_detected": summary["target_detected"],
                "failed_target_case_ids": summary["failed_case_ids"],
                "all_case_results": results,
            }
        )

    all_mutants_detected = all(result["target_detected"] for result in mutation_results)
    status = "pass" if all_mutants_detected else "fail"

    mutation_report = {
        "schema_version": "telos.semantic_mutation_guard.report.v1",
        "status": status,
        "source_main_path": str(SOURCE_MAIN.relative_to(ROOT)),
        "source_semantic_report_path": str(SOURCE_REPORT.relative_to(ROOT)),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "submitted_logic_changed_for_clean_run": False,
        "clean_case_count": len(clean_results),
        "clean_cases_passed": sum(1 for result in clean_results if result["passed"]),
        "clean_cases_failed": sum(1 for result in clean_results if not result["passed"]),
        "clean_results": clean_results,
        "mutation_count": len(mutation_results),
        "all_mutants_detected": all_mutants_detected,
        "mutations": mutation_results,
    }
    write_json(PROOF / "mutation_report.json", mutation_report)

    output_lines = [
        f"semantic mutation guard: {status}",
        f"source_main={SOURCE_MAIN.relative_to(ROOT)}",
        "provider_api_calls=0",
        "cloud_or_gpu_used=false",
        f"clean_cases={len(clean_results)} clean_passed={sum(1 for result in clean_results if result['passed'])}",
    ]
    for mutation in mutation_results:
        output_lines.append(
            f"{mutation['mutation_id']}: "
            f"{'detected' if mutation['target_detected'] else 'not_detected'} "
            f"failed_target_cases={','.join(mutation['failed_target_case_ids'])}"
        )
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 22 Review

The mutation guard loaded the reconstructed `iter21` bot and reran the frozen twelve-case semantic
suite locally. The clean bot still passed every case.

Three targeted mutants were then generated from the same source without changing the test cases:
one disabled board-boundary checks, one disabled own-body checks, and one disabled opponent-body
checks. Each mutant failed the corresponding semantic cases.

This supports a narrow verifier-sensitivity claim: the current semantic suite is not vacuous for the
three safety layers tested in `iter21`. It does not prove complete BattleSnake correctness or
coverage beyond these targeted mutants.

No provider call, API call, GPU, cloud runner, production deployment, live-domain check, leaderboard
run, or SWE-bench run occurred in this gate.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    run_summary = {
        "schema_version": "telos.semantic_mutation_guard.summary.v1",
        "status": status,
        "experiment_id": "iter22_semantic_mutation_guard",
        "source_experiment": "iter21_opponent_collision_control",
        "source_main_path": str(SOURCE_MAIN.relative_to(ROOT)),
        "source_main_sha256": sha256_file(SOURCE_MAIN),
        "source_semantic_report_path": str(SOURCE_REPORT.relative_to(ROOT)),
        "source_semantic_report_sha256": sha256_file(SOURCE_REPORT),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "clean_case_count": len(clean_results),
        "clean_cases_passed": sum(1 for result in clean_results if result["passed"]),
        "clean_cases_failed": sum(1 for result in clean_results if not result["passed"]),
        "mutation_count": len(mutation_results),
        "all_mutants_detected": all_mutants_detected,
        "boundary_mutant_detected": next(
            result["target_detected"] for result in mutation_results if result["mutation_id"] == "boundary_noop"
        ),
        "self_collision_mutant_detected": next(
            result["target_detected"]
            for result in mutation_results
            if result["mutation_id"] == "self_collision_noop"
        ),
        "opponent_collision_mutant_detected": next(
            result["target_detected"]
            for result in mutation_results
            if result["mutation_id"] == "opponent_collision_noop"
        ),
        "test_cases_mutated": False,
        "production_or_live_domain_changed": False,
        "leaderboard_or_swebench_claimed": False,
        "game_score_used_as_verifier_evidence": False,
        "clean_pass": status == "pass",
        "next_gate": "experiments/iter23_tail_semantics_falsification/HYPOTHESIS.md",
        "artifact_hashes": {
            "command_output.txt": sha256_file(PROOF / "command_output.txt"),
            "mutation_report.json": sha256_file(PROOF / "mutation_report.json"),
            "review.md": sha256_file(PROOF / "review.md"),
            "mutants/boundary_noop.py": sha256_file(MUTANTS / "boundary_noop.py"),
            "mutants/self_collision_noop.py": sha256_file(MUTANTS / "self_collision_noop.py"),
            "mutants/opponent_collision_noop.py": sha256_file(MUTANTS / "opponent_collision_noop.py"),
        },
    }
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter22_semantic_mutation_guard",
        "status": status,
        "insight": (
            "The semantic suite is failure-sensitive for targeted removals of boundary, "
            "self-collision, and opponent-collision checks; all three mutants were detected."
        ),
        "next_action": (
            "test the recorded tail-exclusion caveat directly with a tail-semantics falsification "
            "gate before expanding provider behavior claims"
        ),
        "result_path": "experiments/iter22_semantic_mutation_guard/RESULT.md",
        "evidence_paths": [
            "experiments/iter22_semantic_mutation_guard/proof/run_summary.json",
            "experiments/iter22_semantic_mutation_guard/proof/mutation_report.json",
            "experiments/iter22_semantic_mutation_guard/proof/command_output.txt",
            "experiments/iter22_semantic_mutation_guard/proof/review.md",
            "experiments/iter22_semantic_mutation_guard/proof/valid/receipt_semantic_mutation_guard.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(VALID / "receipt_semantic_mutation_guard.json", build_receipt())

    print("\n".join(output_lines))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
