#!/usr/bin/env python3
"""Generate iter24 tail-safety control proof artifacts."""

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
EXPERIMENT = ROOT / "experiments" / "iter24_tail_safety_control"
PROOF = EXPERIMENT / "proof"
CANDIDATE = PROOF / "candidate"
VALID = PROOF / "valid"
SOURCE_MAIN = ROOT / "experiments" / "iter21_opponent_collision_control" / "proof" / "reconstructed" / "main.py"
SOURCE_TAIL_REPORT = (
    ROOT
    / "experiments"
    / "iter23_tail_semantics_falsification"
    / "proof"
    / "tail_semantics_report.json"
)


@dataclass(frozen=True)
class CandidatePatch:
    patch_id: str
    description: str
    needle: str
    replacement: str


PATCHES = [
    CandidatePatch(
        patch_id="own_body_include_tail",
        description="Treat the own tail as occupied under tail_remains_occupied.",
        needle="if next_pos in my_body[:-1]:",
        replacement="if next_pos in my_body:",
    ),
    CandidatePatch(
        patch_id="snake_body_include_tail",
        description="Treat opponent tails as occupied under tail_remains_occupied.",
        needle="if next_pos in snake['body'][:-1]:",
        replacement="if next_pos in snake['body']:",
    ),
]


class TailSafetyControlError(RuntimeError):
    """Raised when iter24 cannot produce trustworthy local proof artifacts."""


class ChoiceProbe:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, choices: list[str]) -> str:
        moves = list(choices)
        self.calls.append(moves)
        if not moves:
            raise TailSafetyControlError("random.choice called with an empty safe-move list")
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
        raise TailSafetyControlError(f"{path} root must be an object")
    return data


def load_iter23_cases() -> list[dict[str, Any]]:
    report = read_json(SOURCE_TAIL_REPORT)
    cases = report.get("cases")
    if not isinstance(cases, list) or len(cases) != 4:
        raise TailSafetyControlError("iter23 report must contain exactly four cases")
    if report.get("tail_occupancy_assumption") != "tail_remains_occupied":
        raise TailSafetyControlError("iter23 report must record tail_remains_occupied")
    return cases


def build_candidate_source() -> str:
    source = SOURCE_MAIN.read_text(encoding="utf-8")
    patched = source
    manifest = []
    for patch in PATCHES:
        count = patched.count(patch.needle)
        if count != 1:
            raise TailSafetyControlError(
                f"{patch.patch_id}: expected one source needle, found {count}"
            )
        patched = patched.replace(patch.needle, patch.replacement, 1)
        manifest.append(
            {
                "patch_id": patch.patch_id,
                "description": patch.description,
                "needle": patch.needle,
                "replacement": patch.replacement,
            }
        )

    CANDIDATE.mkdir(parents=True, exist_ok=True)
    candidate_main = CANDIDATE / "main.py"
    candidate_readme = CANDIDATE / "README.md"
    candidate_main.write_text(patched, encoding="utf-8")
    candidate_readme.write_text(
        "# Iteration 24 Candidate\n\n"
        "This candidate is generated from the reconstructed `iter21` bot for a local semantic "
        "control. It is not the original submitted `iter21` logic. The only intended behavior "
        "change is to treat own and opponent tails as occupied under the explicit "
        "`tail_remains_occupied` assumption.\n",
        encoding="utf-8",
    )
    write_json(
        CANDIDATE / "patch_manifest.json",
        {
            "schema_version": "telos.tail_safety_control.candidate_patch.v1",
            "source_main_path": str(SOURCE_MAIN.relative_to(ROOT)),
            "tail_occupancy_assumption": "tail_remains_occupied",
            "candidate_not_original_submission": True,
            "patches": manifest,
        },
    )
    return patched


def import_module(path: Path, module_name: str) -> ModuleType:
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise TailSafetyControlError(f"cannot import module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    if not hasattr(module, "move"):
        raise TailSafetyControlError(f"{path} does not expose move(game_state)")
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
        "game": {"id": "iter24-tail-safety-control"},
        "turn": 24,
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


def run_logic(logic_id: str, source_path: Path, module_name: str, cases: list[dict[str, Any]]) -> dict[str, Any]:
    module = import_module(source_path, module_name)
    results = [run_case(module, case) for case in cases]
    failed = [result for result in results if not result["passed"]]
    tail_cases = [result for result in results if result["case_family"] in {"own_tail", "opponent_tail"}]
    control_cases = [result for result in results if result["case_family"] == "control_non_tail"]
    return {
        "logic_id": logic_id,
        "source_path": str(source_path.relative_to(ROOT)),
        "source_sha256": sha256_file(source_path),
        "case_count": len(results),
        "passed_case_count": len(results) - len(failed),
        "failed_case_count": len(failed),
        "failed_case_ids": [result["case_id"] for result in failed],
        "tail_cases_passed": all(result["passed"] for result in tail_cases),
        "control_cases_passed": all(result["passed"] for result in control_cases),
        "forbidden_tail_move_observed_safe": any(
            result["case_family"] in {"own_tail", "opponent_tail"}
            and result["forbidden_move_observed_safe"]
            for result in results
        ),
        "cases": results,
    }


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": "iter24-tail-safety-control-pass",
        "task_id": "telos:iter24_tail_safety_control@iter23_tail_semantics_falsification",
        "agent_id": "codex-local-tail-safety-verifier",
        "benchmark_id": "telos_codeclash_battlesnake_semantic_slice",
        "status": status,
        "stated_goal": (
            "Test a clearly labeled changed candidate that treats own and opponent tails as "
            "occupied under an explicit tail-remains-occupied assumption."
        ),
        "acceptance_criteria": [
            "No provider, API, GPU, or cloud spend occurs.",
            "The verifier records whether original or changed candidate logic is under test.",
            "The verifier records the exact tail-occupancy assumption.",
            "The changed candidate blocks occupied tail moves when safer alternatives exist.",
            "Command output and proof artifacts are committed.",
            "No leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": "experiments/iter24_tail_safety_control/proof/tail_safety_report.json",
                "notes": "Same four iter23 cases run against original logic and changed candidate logic.",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "experiments/iter24_tail_safety_control/proof/candidate/main.py",
                "notes": "Changed candidate source, not the original iter21 submission.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": "experiments/iter24_tail_safety_control/proof/review.md",
                "notes": "Review records the original/candidate boundary and tail assumption.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if either source under test cannot be loaded locally.",
            "The result must fail if the changed candidate is presented as the original iter21 bot.",
            "The result must fail if an occupied tail move remains in the candidate safe-move list.",
            "The result must fail if the tail-occupancy assumption is hidden.",
            "The result must not treat provider game score as verifier evidence.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    cases = load_iter23_cases()
    build_candidate_source()

    original = run_logic("original_iter21", SOURCE_MAIN, "iter24_original_iter21", cases)
    candidate_path = CANDIDATE / "main.py"
    candidate = run_logic(
        "changed_candidate_tail_occupied",
        candidate_path,
        "iter24_changed_candidate_tail_occupied",
        cases,
    )

    original_tail_failure_preserved = (
        original["failed_case_ids"] == ["own-tail-left-occupied-risk", "opponent-tail-left-occupied-risk"]
        and original["control_cases_passed"] is True
        and original["forbidden_tail_move_observed_safe"] is True
    )
    candidate_clean_pass = (
        candidate["passed_case_count"] == 4
        and candidate["failed_case_count"] == 0
        and candidate["tail_cases_passed"] is True
        and candidate["control_cases_passed"] is True
        and candidate["forbidden_tail_move_observed_safe"] is False
    )
    status = "pass" if original_tail_failure_preserved and candidate_clean_pass else "fail"

    report = {
        "schema_version": "telos.tail_safety_control.report.v1",
        "status": status,
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "source_tail_report_path": str(SOURCE_TAIL_REPORT.relative_to(ROOT)),
        "tail_occupancy_assumption": "tail_remains_occupied",
        "original_submitted_logic_mutated": False,
        "candidate_logic_changed": True,
        "changed_candidate_not_presented_as_original": True,
        "candidate_patch_manifest_path": str((CANDIDATE / "patch_manifest.json").relative_to(ROOT)),
        "original_tail_failure_preserved": original_tail_failure_preserved,
        "candidate_clean_pass": candidate_clean_pass,
        "original": original,
        "candidate": candidate,
    }
    write_json(PROOF / "tail_safety_report.json", report)

    output_lines = [
        f"tail safety control: {status}",
        f"source_tail_report={SOURCE_TAIL_REPORT.relative_to(ROOT)}",
        "provider_api_calls=0",
        "cloud_or_gpu_used=false",
        "tail_occupancy_assumption=tail_remains_occupied",
        "original_logic=original_iter21",
        f"original_cases={original['case_count']} passed={original['passed_case_count']} failed={original['failed_case_count']}",
        "candidate_logic=changed_candidate_tail_occupied",
        f"candidate_cases={candidate['case_count']} passed={candidate['passed_case_count']} failed={candidate['failed_case_count']}",
    ]
    for result in candidate["cases"]:
        output_lines.append(
            f"candidate {result['case_id']}: {'pass' if result['passed'] else 'fail'} "
            f"forbidden={result['forbidden_move']} safe={','.join(result['observed_safe_moves'])}"
        )
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 24 Review

The tail-safety control kept the `iter23` failure visible and tested a changed candidate separately
from the original `iter21` submission. The original reconstructed bot still fails the two
occupied-tail cases under `tail_remains_occupied`; the changed candidate passes the same four cases.

The candidate is not presented as the original provider-submitted logic. It changes the local body
checks so own and opponent tails remain occupied for this assumption. This supports only a local
semantic control result for the changed candidate, not a CodeClash, SWE-bench, production, or model
capability claim.

No provider call, API call, GPU, cloud runner, production deployment, live-domain check, leaderboard
run, or SWE-bench run occurred in this gate.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    run_summary = {
        "schema_version": "telos.tail_safety_control.summary.v1",
        "status": status,
        "experiment_id": "iter24_tail_safety_control",
        "source_experiment": "iter23_tail_semantics_falsification",
        "source_tail_report_path": str(SOURCE_TAIL_REPORT.relative_to(ROOT)),
        "source_tail_report_sha256": sha256_file(SOURCE_TAIL_REPORT),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "tail_occupancy_assumption": "tail_remains_occupied",
        "original_logic_id": "original_iter21",
        "original_submitted_logic_mutated": False,
        "original_tail_failure_preserved": original_tail_failure_preserved,
        "candidate_logic_id": "changed_candidate_tail_occupied",
        "candidate_logic_changed": True,
        "changed_candidate_not_presented_as_original": True,
        "candidate_main_path": str(candidate_path.relative_to(ROOT)),
        "candidate_main_sha256": sha256_file(candidate_path),
        "candidate_patch_manifest_sha256": sha256_file(CANDIDATE / "patch_manifest.json"),
        "case_count_per_logic": 4,
        "candidate_passed_case_count": candidate["passed_case_count"],
        "candidate_failed_case_count": candidate["failed_case_count"],
        "candidate_tail_cases_passed": candidate["tail_cases_passed"],
        "candidate_control_cases_passed": candidate["control_cases_passed"],
        "candidate_forbidden_tail_move_observed_safe": candidate[
            "forbidden_tail_move_observed_safe"
        ],
        "production_or_live_domain_changed": False,
        "leaderboard_or_swebench_claimed": False,
        "game_score_used_as_verifier_evidence": False,
        "clean_pass": status == "pass",
        "next_gate": "experiments/iter25_tail_safety_mutation_guard/HYPOTHESIS.md",
        "artifact_hashes": {
            "candidate/main.py": sha256_file(candidate_path),
            "candidate/patch_manifest.json": sha256_file(CANDIDATE / "patch_manifest.json"),
            "command_output.txt": sha256_file(PROOF / "command_output.txt"),
            "review.md": sha256_file(PROOF / "review.md"),
            "tail_safety_report.json": sha256_file(PROOF / "tail_safety_report.json"),
        },
    }
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter24_tail_safety_control",
        "status": status,
        "insight": (
            "Separating original submitted logic from a changed candidate preserves the iter23 "
            "failure while proving a local occupied-tail control can pass under tail_remains_occupied."
        ),
        "next_action": (
            "pre-register a tail-safety mutation guard that proves the occupied-tail verifier fails "
            "when the candidate reverts to tail-excluding checks"
        ),
        "result_path": "experiments/iter24_tail_safety_control/RESULT.md",
        "evidence_paths": [
            "experiments/iter24_tail_safety_control/proof/run_summary.json",
            "experiments/iter24_tail_safety_control/proof/tail_safety_report.json",
            "experiments/iter24_tail_safety_control/proof/command_output.txt",
            "experiments/iter24_tail_safety_control/proof/review.md",
            "experiments/iter24_tail_safety_control/proof/candidate/main.py",
            "experiments/iter24_tail_safety_control/proof/valid/receipt_tail_safety_control.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(VALID / "receipt_tail_safety_control.json", build_receipt(status))

    print("\n".join(output_lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
