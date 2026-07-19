"""Focused tests for the additive iter237 scientific correction."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from scripts import validate_iter237_truth_maintenance as guard


ROOT = Path(__file__).resolve().parents[1]


def _apply_mutation(document: dict, fixture: dict) -> dict:
    mutated = deepcopy(document)
    cursor = mutated
    path = fixture["path"]
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = fixture["value"]
    return mutated


def test_expected_correction_rederives_registered_boundaries() -> None:
    correction = guard.build_expected()
    claims = correction["claims"]

    t1 = claims["T1_transfer"]
    assert t1["status"] == "untested"
    assert t1["registered_held_out_rows"] == 447
    assert t1["registered_outcome_labels"] == 0
    assert t1["registered_outcome_endpoint"] is None
    assert t1["exploratory_within_cohort"]["mannwhitney_u"] == 331.0

    t2 = claims["T2_fresh_cohort_concentration"]
    assert t2["status"] == "inconclusive"
    assert t2["total"] == {"k": 0, "N": 37, "u": 13}
    assert t2["least_favourable"] == {"numerator": 13, "denominator": 37}
    assert t2["reused_reference"] == {"k": 5, "N": 29, "u": 0}
    assert t2["registered_strict_inequality_holds"] is False

    t3 = claims["T3_cross_solver_recurrence"]
    assert [
        (row["k"], row["N"], row["u"])
        for row in t3["fixed_cohort_runs"].values()
    ] == [(5, 29, 0), (2, 25, 2), (3, 17, 2), (4, 14, 2), (1, 16, 1)]
    assert t3["patch_level_positives"] == 17
    assert t3["unique_task_identities"] == 12

    t4 = claims["T4_benchmark_labels"]
    assert t4["positive_count"] == 13
    assert t4["control_count"] == 54
    assert t4["controls"] == {
        "normalized_identical_to_accepted": 29,
        "no_divergence_on_one_retained_witness": 25,
    }
    assert t4["independent_semantic_ground_truth"] is False


def test_committed_correction_matches_rebuild() -> None:
    actual = json.loads(guard.CORRECTION.read_text(encoding="utf-8"))
    assert guard.compare_artifact(actual, guard.build_expected()) == []


def test_known_bad_transfer_promotion_fails() -> None:
    fixture = json.loads(
        (
            ROOT / "tests/fixtures/iter237_bad_correction.json"
        ).read_text(encoding="utf-8")
    )
    expected = guard.build_expected()
    bad = _apply_mutation(expected, fixture)
    failures = guard.compare_artifact(bad, expected)
    assert any("claims.T1_transfer.status" in failure for failure in failures)


def test_known_bad_source_rule_restatement_fails() -> None:
    source = (
        ROOT / "tests/fixtures/iter237_source_rule_restatement.py.txt"
    ).read_text(encoding="utf-8")
    failures = guard.validate_structural_source_rule_source(
        source,
        path="iter237_source_rule_restatement.py",
    )
    assert any("does not obtain current_included" in failure for failure in failures)


def test_active_source_rule_executes_imported_predicate() -> None:
    assert guard.validate_structural_source_rule() == []


def test_iter235_worktree_matches_registered_master_bytes() -> None:
    assert guard.validate_sealed_predecessor() == []


def test_repository_iter237_correction_passes() -> None:
    assert guard.validate() == []
