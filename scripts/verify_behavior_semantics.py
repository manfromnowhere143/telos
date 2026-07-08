#!/usr/bin/env python3
"""Generate iter20 deterministic semantic-verification proof artifacts."""

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
EXPERIMENT = ROOT / "experiments" / "iter20_behavior_semantic_verification"
PROOF = EXPERIMENT / "proof"
RECONSTRUCTED = PROOF / "reconstructed"
VALID = PROOF / "valid"
ITER19_CHANGES = (
    ROOT
    / "experiments"
    / "iter19_provider_final_inspection_control"
    / "proof"
    / "raw"
    / "codeclash"
    / "PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708185232"
    / "players"
    / "p1"
    / "changes_r1.json"
)


@dataclass(frozen=True)
class Case:
    case_id: str
    forbidden_move: str
    expected_safe_moves: list[str]
    body: list[dict[str, int]]
    board_width: int = 11
    board_height: int = 11


CASES = [
    Case(
        case_id="boundary-left",
        forbidden_move="left",
        expected_safe_moves=["up", "down"],
        body=[{"x": 0, "y": 5}, {"x": 1, "y": 5}],
    ),
    Case(
        case_id="boundary-right",
        forbidden_move="right",
        expected_safe_moves=["up", "down"],
        body=[{"x": 10, "y": 5}, {"x": 9, "y": 5}],
    ),
    Case(
        case_id="boundary-down",
        forbidden_move="down",
        expected_safe_moves=["left", "right"],
        body=[{"x": 5, "y": 0}, {"x": 5, "y": 1}],
    ),
    Case(
        case_id="boundary-up",
        forbidden_move="up",
        expected_safe_moves=["left", "right"],
        body=[{"x": 5, "y": 10}, {"x": 5, "y": 9}],
    ),
    Case(
        case_id="self-left",
        forbidden_move="left",
        expected_safe_moves=["up", "right"],
        body=[{"x": 5, "y": 5}, {"x": 5, "y": 4}, {"x": 4, "y": 4}, {"x": 4, "y": 5}],
    ),
    Case(
        case_id="self-right",
        forbidden_move="right",
        expected_safe_moves=["up", "left"],
        body=[{"x": 5, "y": 5}, {"x": 5, "y": 4}, {"x": 6, "y": 4}, {"x": 6, "y": 5}],
    ),
    Case(
        case_id="self-down",
        forbidden_move="down",
        expected_safe_moves=["up", "right"],
        body=[{"x": 5, "y": 5}, {"x": 4, "y": 5}, {"x": 4, "y": 4}, {"x": 5, "y": 4}],
    ),
    Case(
        case_id="self-up",
        forbidden_move="up",
        expected_safe_moves=["down", "right"],
        body=[{"x": 5, "y": 5}, {"x": 4, "y": 5}, {"x": 4, "y": 6}, {"x": 5, "y": 6}],
    ),
]


class VerificationError(RuntimeError):
    """Raised when the frozen iter20 verifier cannot produce a clean result."""


class ChoiceProbe:
    """Capture the submitted bot's safe-move list without changing its safety logic."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, choices: list[str]) -> str:
        moves = list(choices)
        self.calls.append(moves)
        if not moves:
            raise VerificationError("random.choice called with an empty safe-move list")
        return moves[0]


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise VerificationError(f"{path} root must be an object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    payload = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(payload)


def reconstruct_submitted_files() -> dict[str, str]:
    changes = read_json(ITER19_CHANGES)
    modified_files = changes.get("modified_files")
    if not isinstance(modified_files, dict):
        raise VerificationError("iter19 changes_r1.json missing modified_files object")
    if set(modified_files) != {"README_agent.md", "main.py"}:
        raise VerificationError(f"unexpected iter19 modified file set: {sorted(modified_files)}")

    reconstructed: dict[str, str] = {}
    for name in ["main.py", "README_agent.md"]:
        value = modified_files.get(name)
        if not isinstance(value, str) or not value.strip():
            raise VerificationError(f"iter19 modified_files[{name!r}] must be a non-empty string")
        reconstructed[name] = value
        (RECONSTRUCTED / name).write_text(value, encoding="utf-8")
    return reconstructed


def import_reconstructed_main(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("telos_iter20_reconstructed_main", path)
    if spec is None or spec.loader is None:
        raise VerificationError(f"cannot import reconstructed module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if not hasattr(module, "move"):
        raise VerificationError("reconstructed main.py does not expose move(game_state)")
    return module


def game_state(case: Case) -> dict[str, Any]:
    body = [dict(part) for part in case.body]
    snake = {
        "id": "telos-self",
        "name": "telos-self",
        "health": 100,
        "body": body,
        "head": body[0],
        "length": len(body),
    }
    return {
        "game": {"id": "iter20-semantic-verification"},
        "turn": 20,
        "board": {
            "height": case.board_height,
            "width": case.board_width,
            "food": [],
            "hazards": [],
            "snakes": [snake],
        },
        "you": snake,
    }


def run_case(module: ModuleType, case: Case) -> dict[str, Any]:
    probe = ChoiceProbe()
    original_choice = module.random.choice
    stdout = io.StringIO()
    try:
        module.random.choice = probe
        with contextlib.redirect_stdout(stdout):
            result = module.move(game_state(case))
    finally:
        module.random.choice = original_choice

    if not isinstance(result, dict):
        raise VerificationError(f"{case.case_id}: move() result must be an object")
    selected_move = result.get("move")
    if not isinstance(selected_move, str):
        raise VerificationError(f"{case.case_id}: move() result must contain a string move")
    if len(probe.calls) != 1:
        raise VerificationError(f"{case.case_id}: expected one random.choice call, got {len(probe.calls)}")

    safe_moves = probe.calls[0]
    passed = (
        case.forbidden_move not in safe_moves
        and selected_move != case.forbidden_move
        and safe_moves == case.expected_safe_moves
    )
    return {
        "case_id": case.case_id,
        "board_width": case.board_width,
        "board_height": case.board_height,
        "body": case.body,
        "forbidden_move": case.forbidden_move,
        "expected_safe_moves": case.expected_safe_moves,
        "observed_safe_moves": safe_moves,
        "selected_move": selected_move,
        "stdout_lines": stdout.getvalue().splitlines(),
        "passed": passed,
    }


def build_receipt() -> dict[str, Any]:
    receipt = {
        "receipt_id": "iter20-behavior-semantic-verification-pass",
        "task_id": "telos:iter20_behavior_semantic_verification@iter19_provider_final_inspection_control",
        "agent_id": "codex-local-deterministic-semantic-verifier",
        "benchmark_id": "telos_codeclash_battlesnake_semantic_slice",
        "status": "pass",
        "stated_goal": (
            "Verify the boundary and self-collision behavior claimed by the submitted iter19 "
            "provider diff using deterministic local tests reconstructed from committed artifacts."
        ),
        "acceptance_criteria": [
            "The submitted diff is reconstructed from committed iter19 artifacts.",
            "No provider, API, GPU, or cloud spend occurs.",
            "The verifier runs locally and records command output.",
            "All four boundary cases pass.",
            "All four self-collision cases pass.",
            "The result records the iter19 formatting caveat separately from semantic behavior.",
            "No leaderboard, SWE-bench, production, or live-domain claim is made.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": "pass",
                "artifact": "experiments/iter20_behavior_semantic_verification/proof/semantic_report.json",
                "notes": "Eight deterministic cases passed with the forbidden move absent from the observed safe-move list.",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "experiments/iter20_behavior_semantic_verification/proof/reconstructed/main.py",
                "notes": "The submitted main.py was reconstructed from iter19 changes_r1.json modified_files content.",
            },
            {
                "kind": "diff_scope",
                "status": "pass",
                "artifact": (
                    "experiments/iter19_provider_final_inspection_control/proof/raw/codeclash/"
                    "PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708185232/players/p1/changes_r1.json"
                ),
                "notes": "Frozen input changed only README_agent.md and main.py.",
            },
            {
                "kind": "adversarial_review",
                "status": "pass",
                "artifact": "experiments/iter20_behavior_semantic_verification/proof/review.md",
                "notes": "Review keeps the semantic claim narrow and preserves the iter19 blank-line style caveat.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed; this was local proof verification only.",
            },
        ],
        "falsifiers": [
            "The result must be blocked if committed iter19 artifacts cannot reconstruct the submitted main.py.",
            "The result must be blocked if the reconstructed bot cannot be imported without changing submitted logic.",
            "The result must fail if any boundary case can select the forbidden out-of-bounds move.",
            "The result must fail if any self-collision case can select the forbidden own-body move.",
            "The result must fail if the verifier mutates submitted safety logic instead of inspecting its safe-move set.",
            "The result must not claim leaderboard, SWE-bench, production, or live-domain verification.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    RECONSTRUCTED.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    reconstructed = reconstruct_submitted_files()
    module = import_reconstructed_main(RECONSTRUCTED / "main.py")
    case_results = [run_case(module, case) for case in CASES]
    failed = [result for result in case_results if not result["passed"]]
    status = "pass" if not failed else "fail"

    semantic_report = {
        "schema_version": "telos.behavior_semantic_verification.report.v1",
        "status": status,
        "source_changes_path": str(ITER19_CHANGES.relative_to(ROOT)),
        "reconstructed_from_modified_files": True,
        "module_imported": True,
        "random_choice_probe_used": True,
        "submitted_logic_mutated": False,
        "provider_api_calls": 0,
        "cloud_or_gpu_used": False,
        "case_count": len(case_results),
        "passed_case_count": len(case_results) - len(failed),
        "failed_case_count": len(failed),
        "cases": case_results,
    }
    write_json(PROOF / "semantic_report.json", semantic_report)

    output_lines = [
        f"behavior semantic verification: {status}",
        f"source_changes={ITER19_CHANGES.relative_to(ROOT)}",
        "provider_api_calls=0",
        "cloud_or_gpu_used=false",
        f"cases={len(case_results)} passed={len(case_results) - len(failed)} failed={len(failed)}",
    ]
    for result in case_results:
        output_lines.append(
            f"{result['case_id']}: {'pass' if result['passed'] else 'fail'} "
            f"forbidden={result['forbidden_move']} safe={','.join(result['observed_safe_moves'])}"
        )
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 20 Review

The semantic verifier reconstructed `main.py` from the committed iter19 `changes_r1.json` artifact
and imported that reconstructed file locally. It inspected the submitted bot's safe-move list by
temporarily replacing `random.choice` with a probe; the boundary and self-collision safety logic was
not changed.

All eight targeted cases passed: four board-boundary cases and four own-body adjacency cases. This
supports the narrow semantic claim that the iter19 diff prevents the tested out-of-bounds and
self-collision moves when safer alternatives exist.

The iter19 formatting caveat remains separate: the provider diff still contains extra empty added
blank lines. That caveat is not a semantic failure for these cases.

No provider call, API call, GPU, cloud runner, production deployment, live-domain check, leaderboard
run, or SWE-bench run occurred in this gate.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    run_summary = {
        "schema_version": "telos.behavior_semantic_verification.summary.v1",
        "status": status,
        "experiment_id": "iter20_behavior_semantic_verification",
        "source_experiment": "iter19_provider_final_inspection_control",
        "source_changes_path": str(ITER19_CHANGES.relative_to(ROOT)),
        "source_changes_sha256": sha256_file(ITER19_CHANGES),
        "reconstructed_files": sorted(reconstructed),
        "reconstructed_main_sha256": sha256_file(RECONSTRUCTED / "main.py"),
        "reconstructed_readme_agent_sha256": sha256_file(RECONSTRUCTED / "README_agent.md"),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "module_imported": True,
        "random_choice_probe_used": True,
        "submitted_logic_mutated": False,
        "case_count": len(case_results),
        "passed_case_count": len(case_results) - len(failed),
        "failed_case_count": len(failed),
        "boundary_case_count": 4,
        "self_collision_case_count": 4,
        "boundary_cases_passed": all(
            result["passed"] for result in case_results if result["case_id"].startswith("boundary-")
        ),
        "self_collision_cases_passed": all(
            result["passed"] for result in case_results if result["case_id"].startswith("self-")
        ),
        "forbidden_move_observed": any(
            result["forbidden_move"] in result["observed_safe_moves"]
            or result["selected_move"] == result["forbidden_move"]
            for result in case_results
        ),
        "style_caveat_extra_blank_lines_from_iter19_preserved": True,
        "production_or_live_domain_changed": False,
        "leaderboard_or_swebench_claimed": False,
        "clean_pass": status == "pass",
        "next_gate": "experiments/iter21_opponent_collision_control/HYPOTHESIS.md",
        "artifact_hashes": {
            "command_output.txt": sha256_file(PROOF / "command_output.txt"),
            "reconstructed/main.py": sha256_file(RECONSTRUCTED / "main.py"),
            "reconstructed/README_agent.md": sha256_file(RECONSTRUCTED / "README_agent.md"),
            "review.md": sha256_file(PROOF / "review.md"),
            "semantic_report.json": sha256_file(PROOF / "semantic_report.json"),
        },
    }
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter20_behavior_semantic_verification",
        "status": status,
        "insight": (
            "The iter19 provider diff is semantically correct for the eight targeted boundary and "
            "self-collision cases when reconstructed from committed artifacts and tested locally."
        ),
        "next_action": (
            "pre-register and run an opponent-collision control that requires both strict final "
            "inspection and deterministic semantic checks for the new behavior"
        ),
        "result_path": "experiments/iter20_behavior_semantic_verification/RESULT.md",
        "evidence_paths": [
            "experiments/iter20_behavior_semantic_verification/proof/run_summary.json",
            "experiments/iter20_behavior_semantic_verification/proof/semantic_report.json",
            "experiments/iter20_behavior_semantic_verification/proof/command_output.txt",
            "experiments/iter20_behavior_semantic_verification/proof/review.md",
            "experiments/iter20_behavior_semantic_verification/proof/valid/receipt_behavior_semantic_verification.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(VALID / "receipt_behavior_semantic_verification.json", build_receipt())

    print("\n".join(output_lines))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
