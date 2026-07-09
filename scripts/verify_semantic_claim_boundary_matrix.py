#!/usr/bin/env python3
"""Generate iter27 semantic claim-boundary matrix proof artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "iter27_semantic_claim_boundary_matrix"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"

SUMMARY_PATHS = {
    "iter20_behavior_semantic_verification": Path(
        "experiments/iter20_behavior_semantic_verification/proof/run_summary.json"
    ),
    "iter21_opponent_collision_control": Path(
        "experiments/iter21_opponent_collision_control/proof/run_summary.json"
    ),
    "iter22_semantic_mutation_guard": Path(
        "experiments/iter22_semantic_mutation_guard/proof/run_summary.json"
    ),
    "iter23_tail_semantics_falsification": Path(
        "experiments/iter23_tail_semantics_falsification/proof/run_summary.json"
    ),
    "iter24_tail_safety_control": Path(
        "experiments/iter24_tail_safety_control/proof/run_summary.json"
    ),
    "iter25_tail_safety_mutation_guard": Path(
        "experiments/iter25_tail_safety_mutation_guard/proof/run_summary.json"
    ),
    "iter26_own_tail_redundancy_mutation_guard": Path(
        "experiments/iter26_own_tail_redundancy_mutation_guard/proof/run_summary.json"
    ),
}

REQUIRED_EXCLUSIONS = [
    "no_codeclash_leaderboard_claim",
    "no_swebench_claim",
    "no_production_or_live_domain_claim",
    "no_model_superiority_claim",
    "no_provider_game_score_as_verifier_evidence",
]


class ClaimMatrixError(RuntimeError):
    """Raised when iter27 cannot produce a trustworthy claim-boundary matrix."""


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
        raise ClaimMatrixError(f"{path} root must be an object")
    return data


def existing(paths: list[str]) -> list[str]:
    missing = [path for path in paths if not (ROOT / path).exists()]
    if missing:
        raise ClaimMatrixError(f"missing evidence paths: {missing}")
    return paths


def load_summaries() -> dict[str, dict[str, Any]]:
    summaries = {}
    for experiment_id, path in SUMMARY_PATHS.items():
        data = read_json(ROOT / path)
        if data.get("experiment_id") != experiment_id:
            raise ClaimMatrixError(f"{path} experiment_id mismatch")
        summaries[experiment_id] = data
    return summaries


def row(
    *,
    claim_id: str,
    experiment_id: str,
    subject_type: str,
    subject_id: str,
    status: str,
    claim: str,
    boundary: str,
    evidence_paths: list[str],
    does_not_claim: list[str],
    source_summary: dict[str, Any],
    failure_visible: bool = False,
    changed_candidate: bool = False,
    original_provider_logic: bool = False,
    verifier_strength_evidence: bool = False,
) -> dict[str, Any]:
    if status not in {"pass", "null", "blocked", "pending"}:
        raise ClaimMatrixError(f"{claim_id}: invalid matrix status {status}")
    for field_name, value in {
        "claim_id": claim_id,
        "experiment_id": experiment_id,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "claim": claim,
        "boundary": boundary,
    }.items():
        if not value:
            raise ClaimMatrixError(f"{claim_id}: {field_name} must be non-empty")

    summary_path = SUMMARY_PATHS[experiment_id].as_posix()
    paths = existing([summary_path, *evidence_paths])
    exclusions = sorted(set(REQUIRED_EXCLUSIONS + does_not_claim))
    if original_provider_logic and changed_candidate:
        raise ClaimMatrixError(f"{claim_id}: original and changed candidate flags conflict")

    return {
        "claim_id": claim_id,
        "experiment_id": experiment_id,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "status": status,
        "source_summary_status": source_summary.get("status"),
        "source_summary_clean_pass": source_summary.get("clean_pass"),
        "claim": claim,
        "boundary": boundary,
        "failure_visible": failure_visible,
        "changed_candidate": changed_candidate,
        "original_provider_logic": original_provider_logic,
        "verifier_strength_evidence": verifier_strength_evidence,
        "evidence_paths": paths,
        "does_not_claim": exclusions,
    }


def build_matrix(summaries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = [
        row(
            claim_id="iter20_original_boundary_self_semantics",
            experiment_id="iter20_behavior_semantic_verification",
            subject_type="reconstructed_original_provider_logic",
            subject_id="iter19_provider_submitted_bot",
            status="pass",
            claim=(
                "The reconstructed iter19 submitted bot passed local boundary and "
                "self-collision semantic cases."
            ),
            boundary=(
                "Local deterministic semantic cases only; no opponent-body, occupied-tail, "
                "benchmark, or production claim."
            ),
            evidence_paths=[
                "experiments/iter20_behavior_semantic_verification/RESULT.md",
                "experiments/iter20_behavior_semantic_verification/proof/semantic_report.json",
                "experiments/iter20_behavior_semantic_verification/proof/valid/receipt_behavior_semantic_verification.json",
            ],
            does_not_claim=["opponent_body_safety", "occupied_tail_safety"],
            source_summary=summaries["iter20_behavior_semantic_verification"],
            original_provider_logic=True,
        ),
        row(
            claim_id="iter21_original_opponent_body_semantics",
            experiment_id="iter21_opponent_collision_control",
            subject_type="reconstructed_original_provider_logic",
            subject_id="iter21_provider_submitted_bot",
            status="pass",
            claim=(
                "The reconstructed iter21 submitted bot passed local boundary, self-collision, "
                "and opponent-body semantic cases."
            ),
            boundary=(
                "Tails were excluded from the collision checks; this does not claim occupied-tail "
                "safety."
            ),
            evidence_paths=[
                "experiments/iter21_opponent_collision_control/RESULT.md",
                "experiments/iter21_opponent_collision_control/proof/semantic_report.json",
                "experiments/iter21_opponent_collision_control/proof/valid/receipt_opponent_collision_control.json",
            ],
            does_not_claim=["occupied_tail_safety"],
            source_summary=summaries["iter21_opponent_collision_control"],
            original_provider_logic=True,
        ),
        row(
            claim_id="iter22_original_semantic_mutation_guard",
            experiment_id="iter22_semantic_mutation_guard",
            subject_type="verifier_harness",
            subject_id="iter21_semantic_suite",
            status="pass",
            claim=(
                "Targeted boundary, self-collision, and opponent-collision mutants were detected "
                "by the local semantic suite."
            ),
            boundary=(
                "Mutation guard covers the targeted non-tail semantic families only; it does not "
                "prove occupied-tail safety."
            ),
            evidence_paths=[
                "experiments/iter22_semantic_mutation_guard/RESULT.md",
                "experiments/iter22_semantic_mutation_guard/proof/mutation_report.json",
                "experiments/iter22_semantic_mutation_guard/proof/valid/receipt_semantic_mutation_guard.json",
            ],
            does_not_claim=["occupied_tail_safety", "complete_semantic_coverage"],
            source_summary=summaries["iter22_semantic_mutation_guard"],
            verifier_strength_evidence=True,
        ),
        row(
            claim_id="iter23_original_occupied_tail_falsification",
            experiment_id="iter23_tail_semantics_falsification",
            subject_type="reconstructed_original_provider_logic",
            subject_id="iter21_provider_submitted_bot",
            status="null",
            claim=(
                "Under tail_remains_occupied, occupied self-tail and opponent-tail moves remained "
                "in the original safe-move list."
            ),
            boundary=(
                "This is a failure/null result for occupied-tail safety on the original iter21 "
                "logic; non-tail controls still passed."
            ),
            evidence_paths=[
                "experiments/iter23_tail_semantics_falsification/RESULT.md",
                "experiments/iter23_tail_semantics_falsification/proof/tail_semantics_report.json",
                "experiments/iter23_tail_semantics_falsification/proof/valid/receipt_tail_semantics_falsification.json",
            ],
            does_not_claim=["original_iter21_occupied_tail_safety"],
            source_summary=summaries["iter23_tail_semantics_falsification"],
            failure_visible=True,
            original_provider_logic=True,
        ),
        row(
            claim_id="iter24_changed_candidate_occupied_tail_control",
            experiment_id="iter24_tail_safety_control",
            subject_type="changed_candidate",
            subject_id="changed_candidate_tail_occupied",
            status="pass",
            claim=(
                "A clearly labeled changed candidate passed the occupied-tail and non-tail local "
                "cases under tail_remains_occupied."
            ),
            boundary=(
                "Candidate source is not the original provider submission and must not be "
                "described as historical iter21 behavior."
            ),
            evidence_paths=[
                "experiments/iter24_tail_safety_control/RESULT.md",
                "experiments/iter24_tail_safety_control/proof/tail_safety_report.json",
                "experiments/iter24_tail_safety_control/proof/candidate/main.py",
                "experiments/iter24_tail_safety_control/proof/valid/receipt_tail_safety_control.json",
            ],
            does_not_claim=["original_iter21_occupied_tail_safety"],
            source_summary=summaries["iter24_tail_safety_control"],
            changed_candidate=True,
        ),
        row(
            claim_id="iter25_tail_safety_mutation_guard_miss",
            experiment_id="iter25_tail_safety_mutation_guard",
            subject_type="verifier_harness",
            subject_id="iter24_candidate_tail_mutation_guard",
            status="null",
            claim=(
                "The opponent-tail mutant was detected, but the direct own-tail mutant was missed "
                "because the self-snake fallback path still protected the tail."
            ),
            boundary=(
                "This is a failure/null result for the full mutation-guard bar, not a clean "
                "verifier-strength pass."
            ),
            evidence_paths=[
                "experiments/iter25_tail_safety_mutation_guard/RESULT.md",
                "experiments/iter25_tail_safety_mutation_guard/proof/mutation_report.json",
                "experiments/iter25_tail_safety_mutation_guard/proof/valid/receipt_tail_safety_mutation_guard.json",
            ],
            does_not_claim=["full_tail_mutation_guard_strength"],
            source_summary=summaries["iter25_tail_safety_mutation_guard"],
            failure_visible=True,
            verifier_strength_evidence=True,
        ),
        row(
            claim_id="iter26_compound_own_tail_redundancy_guard",
            experiment_id="iter26_own_tail_redundancy_mutation_guard",
            subject_type="verifier_harness",
            subject_id="iter24_candidate_compound_own_tail_guard",
            status="pass",
            claim=(
                "A compound own-tail mutant that removed both direct own-body checking and the "
                "self-snake fallback was detected by the occupied-tail verifier."
            ),
            boundary=(
                "Verifier-strength evidence for this compound own-tail regression only; not a "
                "benchmark or production claim."
            ),
            evidence_paths=[
                "experiments/iter26_own_tail_redundancy_mutation_guard/RESULT.md",
                "experiments/iter26_own_tail_redundancy_mutation_guard/proof/redundancy_report.json",
                "experiments/iter26_own_tail_redundancy_mutation_guard/proof/valid/receipt_own_tail_redundancy_mutation_guard.json",
            ],
            does_not_claim=["general_battlesnake_strength", "complete_semantic_coverage"],
            source_summary=summaries["iter26_own_tail_redundancy_mutation_guard"],
            verifier_strength_evidence=True,
        ),
    ]

    matrix = {
        "schema_version": "telos.semantic_claim_boundary_matrix.v1",
        "status": "pass",
        "experiment_id": "iter27_semantic_claim_boundary_matrix",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "included_experiments": list(SUMMARY_PATHS),
        "row_count": len(rows),
        "failed_or_null_claim_ids": [
            item["claim_id"] for item in rows if item["status"] in {"null", "blocked"}
        ],
        "changed_candidate_claim_ids": [
            item["claim_id"] for item in rows if item["changed_candidate"]
        ],
        "original_provider_logic_claim_ids": [
            item["claim_id"] for item in rows if item["original_provider_logic"]
        ],
        "verifier_strength_claim_ids": [
            item["claim_id"] for item in rows if item["verifier_strength_evidence"]
        ],
        "original_iter21_occupied_tail_safety_claimed": False,
        "failed_null_gates_hidden": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "rows": rows,
    }
    validate_matrix(matrix)
    return matrix


def validate_matrix(matrix: dict[str, Any]) -> None:
    expected_experiments = set(SUMMARY_PATHS)
    row_experiments = {row["experiment_id"] for row in matrix["rows"]}
    if row_experiments != expected_experiments:
        raise ClaimMatrixError(
            f"matrix experiment coverage mismatch: {sorted(row_experiments)}"
        )
    if matrix["row_count"] != len(matrix["rows"]):
        raise ClaimMatrixError("row_count mismatch")
    if "iter23_original_occupied_tail_falsification" not in matrix["failed_or_null_claim_ids"]:
        raise ClaimMatrixError("iter23 failure/null row must remain visible")
    if "iter25_tail_safety_mutation_guard_miss" not in matrix["failed_or_null_claim_ids"]:
        raise ClaimMatrixError("iter25 failure/null row must remain visible")
    if matrix["original_iter21_occupied_tail_safety_claimed"] is not False:
        raise ClaimMatrixError("matrix must not claim original iter21 occupied-tail safety")
    if matrix["failed_null_gates_hidden"] is not False:
        raise ClaimMatrixError("matrix must not hide failed/null gates")
    for item in matrix["rows"]:
        if item["original_provider_logic"] and item["changed_candidate"]:
            raise ClaimMatrixError(f"{item['claim_id']}: conflates original and candidate logic")
        for path in item["evidence_paths"]:
            if not (ROOT / path).exists():
                raise ClaimMatrixError(f"{item['claim_id']}: missing evidence path {path}")
        missing_exclusions = set(REQUIRED_EXCLUSIONS) - set(item["does_not_claim"])
        if missing_exclusions:
            raise ClaimMatrixError(
                f"{item['claim_id']}: missing exclusions {sorted(missing_exclusions)}"
            )


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter27-semantic-claim-boundary-matrix-{status}",
        "task_id": "telos:iter27_semantic_claim_boundary_matrix@iter20_iter26_semantic_chain",
        "agent_id": "codex-local-claim-boundary-matrix",
        "benchmark_id": "telos_codeclash_battlesnake_semantic_slice",
        "status": status,
        "stated_goal": (
            "Publish a machine-checkable matrix separating original provider logic, changed "
            "candidates, failed/null gates, and verifier-strength evidence."
        ),
        "acceptance_criteria": [
            "No provider, API, GPU, or cloud spend occurs.",
            "The matrix includes iter20 through iter26.",
            "Failed/null gates remain visible as failed/null.",
            "Original provider logic and changed candidate logic are not conflated.",
            "Evidence paths exist for every non-pending row.",
            "No leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.",
        ],
        "evidence": [
            {
                "kind": "artifact",
                "status": status,
                "artifact": "experiments/iter27_semantic_claim_boundary_matrix/proof/claim_boundary_matrix.json",
                "notes": "Machine-readable claim-boundary matrix for iter20 through iter26.",
            },
            {
                "kind": "test",
                "status": status,
                "artifact": "experiments/iter27_semantic_claim_boundary_matrix/proof/run_summary.json",
                "notes": "Summary records coverage and no-overclaim invariants.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": "experiments/iter27_semantic_claim_boundary_matrix/proof/review.md",
                "notes": "Review states the matrix boundaries in prose.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if required prior proof artifacts are missing.",
            "The result must fail if failed/null gates are hidden or relabeled as clean passes.",
            "The result must fail if original provider logic and changed candidate logic are conflated.",
            "The result must fail if the matrix implies original iter21 occupied-tail safety.",
            "The result must not treat provider game score as verifier evidence.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    summaries = load_summaries()
    matrix = build_matrix(summaries)
    status = "pass"
    write_json(PROOF / "claim_boundary_matrix.json", matrix)

    output_lines = [
        f"semantic claim boundary matrix: {status}",
        "provider_api_calls=0",
        "cloud_or_gpu_used=false",
        f"included_experiments={','.join(matrix['included_experiments'])}",
        f"rows={matrix['row_count']}",
        f"failed_or_null={','.join(matrix['failed_or_null_claim_ids'])}",
        "original_iter21_occupied_tail_safety_claimed=false",
        "failed_null_gates_hidden=false",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 27 Review

The claim-boundary matrix covers `iter20` through `iter26` and keeps the evidence chain separated by
subject under test. Original provider-submitted logic, changed candidate logic, and verifier-strength
evidence are distinct rows. The `iter23` occupied-tail falsification and the `iter25` mutation-guard
miss remain visible as null/failure evidence.

The matrix does not claim that the original `iter21` bot was occupied-tail safe. It assigns the
occupied-tail pass to the changed `iter24` candidate only, and assigns mutation-strength claims to
the verifier harness rows only.

No provider call, API call, GPU, cloud runner, production deployment, live-domain check, leaderboard
run, or SWE-bench run occurred in this gate.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    run_summary = {
        "schema_version": "telos.semantic_claim_boundary_matrix.summary.v1",
        "status": status,
        "experiment_id": "iter27_semantic_claim_boundary_matrix",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "included_experiments": matrix["included_experiments"],
        "row_count": matrix["row_count"],
        "failed_or_null_claim_ids": matrix["failed_or_null_claim_ids"],
        "changed_candidate_claim_ids": matrix["changed_candidate_claim_ids"],
        "original_provider_logic_claim_ids": matrix["original_provider_logic_claim_ids"],
        "verifier_strength_claim_ids": matrix["verifier_strength_claim_ids"],
        "original_iter21_occupied_tail_safety_claimed": False,
        "failed_null_gates_hidden": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "clean_pass": True,
        "next_gate": "experiments/iter28_public_claim_surface_guard/HYPOTHESIS.md",
        "artifact_hashes": {
            "claim_boundary_matrix.json": sha256_file(PROOF / "claim_boundary_matrix.json"),
            "command_output.txt": sha256_file(PROOF / "command_output.txt"),
            "review.md": sha256_file(PROOF / "review.md"),
        },
    }
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter27_semantic_claim_boundary_matrix",
        "status": status,
        "insight": (
            "The semantic evidence chain can be represented as a matrix that keeps original "
            "provider logic, changed candidates, failed/null gates, and verifier-strength evidence "
            "separate."
        ),
        "next_action": (
            "pre-register a public claim-surface guard that checks README and report prose against "
            "the claim-boundary matrix"
        ),
        "result_path": "experiments/iter27_semantic_claim_boundary_matrix/RESULT.md",
        "evidence_paths": [
            "experiments/iter27_semantic_claim_boundary_matrix/proof/run_summary.json",
            "experiments/iter27_semantic_claim_boundary_matrix/proof/claim_boundary_matrix.json",
            "experiments/iter27_semantic_claim_boundary_matrix/proof/command_output.txt",
            "experiments/iter27_semantic_claim_boundary_matrix/proof/review.md",
            "experiments/iter27_semantic_claim_boundary_matrix/proof/valid/receipt_semantic_claim_boundary_matrix.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(VALID / "receipt_semantic_claim_boundary_matrix.json", build_receipt(status))

    print("\n".join(output_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
