#!/usr/bin/env python3
"""Generate iter23 tail-semantics falsification proof artifacts."""

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
EXPERIMENT = ROOT / "experiments" / "iter23_tail_semantics_falsification"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
SOURCE_MAIN = ROOT / "experiments" / "iter21_opponent_collision_control" / "proof" / "reconstructed" / "main.py"
SOURCE_REPORT = ROOT / "experiments" / "iter21_opponent_collision_control" / "proof" / "semantic_report.json"


@dataclass(frozen=True)
class Case:
    case_id: str
    case_family: str
    forbidden_move: str
    expected_safe_moves_if_tail_occupied: list[str]
    self_body: list[dict[str, int]]
    opponent_body: list[dict[str, int]] | None = None
    tail_occupancy_assumption: str = "tail_remains_occupied"
    board_width: int = 11
    board_height: int = 11


CASES = [
    Case(
        case_id="own-tail-left-occupied-risk",
        case_family="own_tail",
        forbidden_move="left",
        expected_safe_moves_if_tail_occupied=["up", "right"],
        self_body=[
            {"x": 5, "y": 5},
            {"x": 5, "y": 4},
            {"x": 4, "y": 4},
            {"x": 4, "y": 5},
        ],
    ),
    Case(
        case_id="opponent-tail-left-occupied-risk",
        case_family="opponent_tail",
        forbidden_move="left",
        expected_safe_moves_if_tail_occupied=["up", "right"],
        self_body=[
            {"x": 5, "y": 5},
            {"x": 5, "y": 4},
        ],
        opponent_body=[
            {"x": 3, "y": 5},
            {"x": 3, "y": 4},
            {"x": 4, "y": 5},
        ],
    ),
    Case(
        case_id="own-non-tail-left-control",
        case_family="control_non_tail",
        forbidden_move="left",
        expected_safe_moves_if_tail_occupied=["up", "right"],
        self_body=[
            {"x": 5, "y": 5},
            {"x": 5, "y": 4},
            {"x": 4, "y": 4},
            {"x": 4, "y": 5},
            {"x": 4, "y": 6},
        ],
    ),
    Case(
        case_id="opponent-non-tail-left-control",
        case_family="control_non_tail",
        forbidden_move="left",
        expected_safe_moves_if_tail_occupied=["up", "right"],
        self_body=[
            {"x": 5, "y": 5},
            {"x": 5, "y": 4},
        ],
        opponent_body=[
            {"x": 3, "y": 5},
            {"x": 4, "y": 5},
            {"x": 4, "y": 4},
        ],
    ),
]


class ChoiceProbe:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, choices: list[str]) -> str:
        moves = list(choices)
        self.calls.append(moves)
        if not moves:
            raise RuntimeError("random.choice called with an empty safe-move list")
        return moves[0]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def import_module(path: Path) -> ModuleType:
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("iter23_reconstructed_tail_semantics", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import reconstructed module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if not hasattr(module, "move"):
        raise RuntimeError("reconstructed main.py does not expose move(game_state)")
    return module


def game_state(case: Case) -> dict[str, Any]:
    self_body = [dict(part) for part in case.self_body]
    me = {
        "id": "me",
        "name": "me",
        "health": 100,
        "body": self_body,
        "head": self_body[0],
        "length": len(self_body),
    }
    snakes = [me]
    if case.opponent_body is not None:
        opponent_body = [dict(part) for part in case.opponent_body]
        snakes.append(
            {
                "id": "opp",
                "name": "opp",
                "health": 100,
                "body": opponent_body,
                "head": opponent_body[0],
                "length": len(opponent_body),
            }
        )
    return {
        "game": {"id": "iter23-tail-semantics"},
        "turn": 23,
        "board": {
            "height": case.board_height,
            "width": case.board_width,
            "food": [],
            "hazards": [],
            "snakes": snakes,
        },
        "you": me,
    }


def run_case(module: ModuleType, case: Case) -> dict[str, Any]:
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
    forbidden_safe = case.forbidden_move in observed_safe
    selected_forbidden = isinstance(result, dict) and result.get("move") == case.forbidden_move
    passed = (
        observed_safe == case.expected_safe_moves_if_tail_occupied
        and not forbidden_safe
        and not selected_forbidden
    )
    return {
        "case_id": case.case_id,
        "case_family": case.case_family,
        "tail_occupancy_assumption": case.tail_occupancy_assumption,
        "forbidden_move": case.forbidden_move,
        "expected_safe_moves_if_tail_occupied": case.expected_safe_moves_if_tail_occupied,
        "observed_safe_moves": observed_safe,
        "selected_move": result.get("move") if isinstance(result, dict) else None,
        "forbidden_move_observed_safe": forbidden_safe,
        "forbidden_move_selected": selected_forbidden,
        "self_body": case.self_body,
        "opponent_body": case.opponent_body,
        "stdout_lines": stdout.getvalue().splitlines(),
        "passed": passed,
    }


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": "iter23-tail-semantics-falsification-fail",
        "task_id": "telos:iter23_tail_semantics_falsification@iter21_opponent_collision_control",
        "agent_id": "codex-local-tail-semantics-verifier",
        "benchmark_id": "telos_codeclash_battlesnake_semantic_slice",
        "status": status,
        "stated_goal": (
            "Test whether the reconstructed iter21 bot treats occupied self and opponent tail cells "
            "as unsafe under an explicit tail-remains-occupied assumption."
        ),
        "acceptance_criteria": [
            "No provider, API, GPU, or cloud spend occurs.",
            "The reconstructed bot imports locally.",
            "The verifier records the exact tail-occupancy assumption.",
            "The submitted bot does not select an occupied self-tail or opponent-tail cell when safer alternatives exist.",
            "Command output and proof artifacts are committed.",
            "No leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": "experiments/iter23_tail_semantics_falsification/proof/tail_semantics_report.json",
                "notes": "Occupied-tail risk cases expose whether the forbidden tail move remains in the observed safe-move list.",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "experiments/iter21_opponent_collision_control/proof/reconstructed/main.py",
                "notes": "Frozen reconstructed iter21 bot under test.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": "experiments/iter23_tail_semantics_falsification/proof/review.md",
                "notes": "Review records the tail-occupancy assumption and claim boundary.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if the reconstructed iter21 bot cannot be loaded locally.",
            "The result must block if the harness cannot encode a tail-occupancy assumption without changing submitted logic.",
            "The result must fail if the bot can select an occupied self-tail cell when safer alternatives exist.",
            "The result must fail if the bot can select an occupied opponent-tail cell when safer alternatives exist.",
            "The result must not hide the tail-assumption boundary.",
            "The result must not treat provider game score as verifier evidence.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    module = import_module(SOURCE_MAIN)
    results = [run_case(module, case) for case in CASES]
    failed = [result for result in results if not result["passed"]]
    status = "pass" if not failed else "fail"

    report = {
        "schema_version": "telos.tail_semantics_falsification.report.v1",
        "status": status,
        "source_main_path": str(SOURCE_MAIN.relative_to(ROOT)),
        "source_semantic_report_path": str(SOURCE_REPORT.relative_to(ROOT)),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "tail_occupancy_assumption": "tail_remains_occupied",
        "submitted_logic_mutated": False,
        "case_count": len(results),
        "passed_case_count": len(results) - len(failed),
        "failed_case_count": len(failed),
        "failed_case_ids": [result["case_id"] for result in failed],
        "own_tail_risk_detected": any(
            result["case_family"] == "own_tail" and result["forbidden_move_observed_safe"]
            for result in results
        ),
        "opponent_tail_risk_detected": any(
            result["case_family"] == "opponent_tail" and result["forbidden_move_observed_safe"]
            for result in results
        ),
        "non_tail_controls_passed": all(
            result["passed"] for result in results if result["case_family"] == "control_non_tail"
        ),
        "cases": results,
    }
    write_json(PROOF / "tail_semantics_report.json", report)

    output_lines = [
        f"tail semantics falsification: {status}",
        f"source_main={SOURCE_MAIN.relative_to(ROOT)}",
        "provider_api_calls=0",
        "cloud_or_gpu_used=false",
        "tail_occupancy_assumption=tail_remains_occupied",
        f"cases={len(results)} passed={len(results) - len(failed)} failed={len(failed)}",
    ]
    for result in results:
        output_lines.append(
            f"{result['case_id']}: {'pass' if result['passed'] else 'fail'} "
            f"forbidden={result['forbidden_move']} safe={','.join(result['observed_safe_moves'])}"
        )
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 23 Review

The tail-semantics harness loaded the reconstructed `iter21` bot and ran local cases under the
explicit assumption `tail_remains_occupied`. The submitted bot excludes tails from both self and
opponent body checks, so the occupied-tail risk cases leave the forbidden tail move in the observed
safe-move list.

The non-tail controls still pass. The failure is narrow: it does not invalidate the `iter21`
non-tail body collision result, but it does falsify any broader claim that the submitted bot avoids
all occupied tail cells.

No provider call, API call, GPU, cloud runner, production deployment, live-domain check, leaderboard
run, or SWE-bench run occurred in this gate.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    run_summary = {
        "schema_version": "telos.tail_semantics_falsification.summary.v1",
        "status": status,
        "experiment_id": "iter23_tail_semantics_falsification",
        "source_experiment": "iter21_opponent_collision_control",
        "source_main_path": str(SOURCE_MAIN.relative_to(ROOT)),
        "source_main_sha256": sha256_file(SOURCE_MAIN),
        "source_semantic_report_path": str(SOURCE_REPORT.relative_to(ROOT)),
        "source_semantic_report_sha256": sha256_file(SOURCE_REPORT),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "tail_occupancy_assumption": "tail_remains_occupied",
        "submitted_logic_mutated": False,
        "case_count": len(results),
        "passed_case_count": len(results) - len(failed),
        "failed_case_count": len(failed),
        "failed_case_ids": [result["case_id"] for result in failed],
        "own_tail_risk_detected": report["own_tail_risk_detected"],
        "opponent_tail_risk_detected": report["opponent_tail_risk_detected"],
        "non_tail_controls_passed": report["non_tail_controls_passed"],
        "production_or_live_domain_changed": False,
        "leaderboard_or_swebench_claimed": False,
        "game_score_used_as_verifier_evidence": False,
        "clean_pass": status == "pass",
        "quality_failure": status == "fail",
        "next_gate": "experiments/iter24_tail_safety_control/HYPOTHESIS.md",
        "artifact_hashes": {
            "command_output.txt": sha256_file(PROOF / "command_output.txt"),
            "review.md": sha256_file(PROOF / "review.md"),
            "tail_semantics_report.json": sha256_file(PROOF / "tail_semantics_report.json"),
        },
    }
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter23_tail_semantics_falsification",
        "status": "null" if status == "fail" else status,
        "insight": (
            "Under an explicit occupied-tail assumption, the reconstructed iter21 bot leaves "
            "occupied self-tail and opponent-tail moves in the safe-move list while non-tail "
            "controls still pass."
        ),
        "next_action": (
            "pre-register a tail-safety control that either models tail occupancy explicitly or "
            "keeps the claim limited to non-tail body segments"
        ),
        "result_path": "experiments/iter23_tail_semantics_falsification/RESULT.md",
        "evidence_paths": [
            "experiments/iter23_tail_semantics_falsification/proof/run_summary.json",
            "experiments/iter23_tail_semantics_falsification/proof/tail_semantics_report.json",
            "experiments/iter23_tail_semantics_falsification/proof/command_output.txt",
            "experiments/iter23_tail_semantics_falsification/proof/review.md",
            "experiments/iter23_tail_semantics_falsification/proof/valid/receipt_tail_semantics_falsification.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(VALID / "receipt_tail_semantics_falsification.json", build_receipt(status))

    print("\n".join(output_lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
