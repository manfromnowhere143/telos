"""Adversarial tests for iter240's offline ground-truth admission gate."""

from __future__ import annotations

import ast
from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
import math
from pathlib import Path
from typing import Any

import pytest

from scripts import build_iter240_ground_truth_admission as builder
from scripts import validate_iter240_ground_truth_admission as guard


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "scripts/build_iter240_ground_truth_admission.py"
VALIDATOR_PATH = ROOT / "scripts/validate_iter240_ground_truth_admission.py"
KNOWN_BAD_PATH = (
    ROOT
    / "experiments/iter240_ground_truth_admission_design/fixtures"
    / "ground_truth_known_bad.json"
)

EXPECTED_CASE_IDS = {
    "acquisition_uses_37_over_62",
    "candidate_only_exception",
    "duplicate_result",
    "fisher_branch_missing",
    "fisher_exact_known_answers",
    "missing_result",
    "repeated_tasks_counted_as_rows",
    "selected_count_12",
    "selected_count_14",
    "selected_duplicate_row",
    "selector_integer_boolean",
    "selector_reads_status",
    "selector_uses_get",
    "source_worktree_drift",
    "zero_event_known_bounds",
    "zero_libm_bit_exact",
    "zero_n_minus_one_copied_from_n",
}


@pytest.fixture(scope="module")
def known_bad() -> dict[str, dict[str, Any]]:
    document = guard.parse_json(
        KNOWN_BAD_PATH.read_bytes(),
        source=KNOWN_BAD_PATH.relative_to(ROOT).as_posix(),
    )
    assert isinstance(document, dict)
    assert document["schema_version"] == "telos.iter240.ground_truth_known_bad.v1"
    cases = document["cases"]
    assert isinstance(cases, list)
    indexed = {case["id"]: case for case in cases}
    assert len(indexed) == len(cases)
    assert set(indexed) == EXPECTED_CASE_IDS
    return indexed


@pytest.fixture(scope="module")
def reconstructed() -> dict[str, Any]:
    """Rebuild both phases without weakening the committed-freeze production gate."""

    source_boundary = builder.preflight()
    selection_tracker = builder.SourceTracker()
    census, selected = builder.build_selection_census(
        selection_tracker,
        source_boundary,
    )
    diagnostic_tracker = builder.SourceTracker()
    manifest, taxonomy, selected_again, acquisition_inputs = builder.build_missingness(
        diagnostic_tracker,
        source_boundary,
        selected,
    )
    assert selected_again == selected
    return {
        "census": census,
        "curves": builder.build_decision_curves(
            diagnostic_tracker,
            acquisition_inputs,
        ),
        "frame": builder.build_frame(diagnostic_tracker, selected),
        "manifest": manifest,
        "selected": selected,
        "taxonomy": taxonomy,
    }


def _case(
    known_bad: dict[str, dict[str, Any]],
    case_id: str,
) -> dict[str, Any]:
    return known_bad[case_id]


def _set_path(document: dict[str, Any], path: list[str], value: Any) -> None:
    cursor: dict[str, Any] = document
    for key in path[:-1]:
        child = cursor[key]
        assert isinstance(child, dict)
        cursor = child
    cursor[path[-1]] = value


def _mutate_selected_rows(
    document: dict[str, Any],
    case: dict[str, Any],
) -> None:
    rows = document["selected_rows"]
    if case["operation"] == "drop_last":
        rows.pop()
    elif case["operation"] == "append_first":
        rows.append(deepcopy(rows[0]))
    elif case["operation"] == "replace_last_with_first":
        rows[-1] = deepcopy(rows[0])
    else:  # pragma: no cover - the fixture catalogue is closed above.
        raise AssertionError(f"unknown operation {case['operation']}")
    document["selected_count"] = case["selected_count"]
    document["unique_task_count"] = case["unique_task_count"]


def _function_node(source: str, name: str) -> ast.FunctionDef:
    matches = [
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    assert len(matches) == 1
    return matches[0]


def _contains_math_call(node: ast.AST) -> bool:
    return any(
        isinstance(item, ast.Call)
        and isinstance(item.func, ast.Attribute)
        and isinstance(item.func.value, ast.Name)
        and item.func.value.id == "math"
        for item in ast.walk(node)
    )


def _has_bit_exact_libm_comparison(source: str) -> bool:
    tree = ast.parse(source)
    libm_derived_names = {
        target.id
        for assignment in ast.walk(tree)
        if isinstance(assignment, (ast.Assign, ast.AnnAssign))
        and _contains_math_call(assignment.value)
        for target in (
            assignment.targets
            if isinstance(assignment, ast.Assign)
            else [assignment.target]
        )
        if isinstance(target, ast.Name)
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        if not any(isinstance(operator, (ast.Eq, ast.NotEq)) for operator in node.ops):
            continue
        compared_names = {
            item.id for item in ast.walk(node) if isinstance(item, ast.Name)
        }
        if _contains_math_call(node) or compared_names & libm_derived_names:
            return True
    return False


def _classify_both(log: str, arm: str) -> tuple[dict[str, Any], dict[str, Any]]:
    built = builder._scenario_arm(log, arm, source=f"fixture-{arm}")
    validated = guard.classify_arm(log, arm, f"fixture-{arm}")
    for key in ("apply_ok", "exit_code", "result_count", "valid"):
        assert built[key] == validated[key]
    return built, validated


def test_active_selector_ast_is_outcome_blind() -> None:
    source = BUILDER_PATH.read_text(encoding="utf-8")
    assert guard.validate_selector_source(source) == []
    selector = _function_node(source, "select_missing_candidates")
    literals = {
        node.value
        for node in ast.walk(selector)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert {
        "candidates",
        "certified_resolved",
        "gold_equivalent_after_terminal_lf_normalization",
        "outcome_complete",
    } <= literals


@pytest.mark.parametrize(
    "case_id",
    ["selector_reads_status", "selector_uses_get"],
)
def test_selector_ast_known_bad_sources_fail(
    known_bad: dict[str, dict[str, Any]],
    case_id: str,
) -> None:
    case = _case(known_bad, case_id)
    problems = guard.validate_selector_source(case["source"])
    assert any(case["expected_message"] in problem for problem in problems)


def test_selector_rejects_integer_boolean_stand_ins(
    known_bad: dict[str, dict[str, Any]],
) -> None:
    case = _case(known_bad, "selector_integer_boolean")
    baseline = case["candidate"]
    assert builder.select_missing_candidates({"candidates": [baseline]}) == [
        (0, baseline)
    ]
    assert guard.select_independently([baseline], source="fixture") == [(0, baseline)]

    for field, numeric in case["numeric_substitutes"].items():
        row = dict(baseline)
        row[field] = numeric
        with pytest.raises(builder.EvidenceError, match="exact boolean|not an exact boolean"):
            builder.select_missing_candidates({"candidates": [row]})
        with pytest.raises(guard.ValidationError, match=case["expected_message"]):
            guard.select_independently([row], source="fixture")


@pytest.mark.parametrize(
    "case_id",
    ["selected_count_12", "selected_count_14", "selected_duplicate_row"],
)
def test_missingness_rejects_12_14_and_duplicate_rows(
    reconstructed: dict[str, Any],
    known_bad: dict[str, dict[str, Any]],
    case_id: str,
) -> None:
    case = _case(known_bad, case_id)
    manifest = deepcopy(reconstructed["manifest"])
    _mutate_selected_rows(manifest, case)
    with pytest.raises(guard.ValidationError, match=case["expected_message"]):
        guard.validate_missingness(
            reconstructed["census"],
            manifest,
            reconstructed["taxonomy"],
        )

    census = deepcopy(reconstructed["census"])
    _mutate_selected_rows(census, case)
    with pytest.raises(
        guard.ValidationError,
        match="committed selection census differs",
    ):
        guard.validate_missingness(
            census,
            reconstructed["manifest"],
            reconstructed["taxonomy"],
        )


def test_candidate_only_exception_is_not_a_valid_differential(
    known_bad: dict[str, dict[str, Any]],
) -> None:
    case = _case(known_bad, "candidate_only_exception")
    candidate, _ = _classify_both(case["candidate_log"], "variant")
    accepted, _ = _classify_both(case["gold_log"], "gold")
    assert candidate["valid"] is False
    assert candidate["result_count"] == 0
    assert accepted["valid"] is True
    assert accepted["result_count"] == 1


@pytest.mark.parametrize("case_id", ["missing_result", "duplicate_result"])
def test_missing_or_duplicate_result_is_invalid(
    known_bad: dict[str, dict[str, Any]],
    case_id: str,
) -> None:
    case = _case(known_bad, case_id)
    built, validated = _classify_both(case["log"], case["arm"])
    assert built["result_count"] == case["expected_result_count"]
    assert validated["result_count"] == case["expected_result_count"]
    assert built["valid"] is False
    assert validated["valid"] is False


def test_source_tracker_rejects_worktree_drift(
    known_bad: dict[str, dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    case = _case(known_bad, "source_worktree_drift")
    relative = Path(case["path"])
    absolute = tmp_path / relative
    absolute.parent.mkdir(parents=True)
    absolute.write_bytes(case["worktree"].encode("utf-8"))
    oid = "a" * 40
    listing = f"100644 blob {oid}\t{relative.as_posix()}\n".encode("utf-8")

    def fake_git(*arguments: str, input_bytes: bytes | None = None) -> bytes:
        assert input_bytes is None
        if arguments[0] == "ls-tree":
            return listing
        if arguments == ("cat-file", "blob", oid):
            return case["committed"].encode("utf-8")
        raise AssertionError(f"unexpected git call: {arguments}")

    monkeypatch.setattr(builder, "ROOT", tmp_path)
    monkeypatch.setattr(builder, "_git", fake_git)
    with pytest.raises(builder.EvidenceError, match=case["expected_message"]):
        builder.SourceTracker().read_bytes(relative)


def test_frame_retains_candidate_rows_but_clusters_tasks(
    reconstructed: dict[str, Any],
    known_bad: dict[str, dict[str, Any]],
) -> None:
    frame = reconstructed["frame"]
    rows = frame["rows"]
    task_ids = {row["task_id"] for row in rows}
    assert len(rows) == frame["candidate_row_count"] == 55
    assert len(task_ids) == frame["unique_task_count"] == 37
    assert frame["strata"] == {
        "operational_positive": {"candidate_rows": 17, "unique_tasks": 12},
        "hard_control": {"candidate_rows": 25, "unique_tasks": 14},
        "fresh_missing": {"candidate_rows": 13, "unique_tasks": 13},
    }
    assert frame["cross_stratum_task_overlap"] == [
        "django__django-11964",
        "pydata__xarray-7233",
    ]

    missing_keys = [
        (row["source_run"], row["instance_id"])
        for row in reconstructed["manifest"]["selected_rows"]
    ]
    guard.validate_frame(frame, missing_keys)
    bad = deepcopy(frame)
    case = _case(known_bad, "repeated_tasks_counted_as_rows")
    bad["unique_task_count"] = case["unique_task_count"]
    with pytest.raises(guard.ValidationError, match=case["expected_message"]):
        guard.validate_frame(bad, missing_keys)


def test_acquisition_keeps_37_over_64_distinct_from_37_over_62(
    reconstructed: dict[str, Any],
    known_bad: dict[str, dict[str, Any]],
) -> None:
    curves = reconstructed["curves"]
    acquisition = curves["acquisition_sensitivity"]
    assert acquisition["historical_certification_yield"]["certified"] == 37
    assert acquisition["historical_certification_yield"]["denominator"] == 64
    assert acquisition["conditional_solution_patch_diagnostic"] == {
        "certified": 37,
        "denominator": 62,
        "forbidden_as_acquisition_input": True,
        "interpretation": "conditional on a solution-producing patch",
    }
    guard.validate_curves(curves)

    bad = deepcopy(curves)
    case = _case(known_bad, "acquisition_uses_37_over_62")
    _set_path(bad, case["path"], case["value"])
    with pytest.raises(guard.ValidationError, match=case["expected_message"]):
        guard.validate_curves(bad)


def test_fisher_exact_known_answers(
    known_bad: dict[str, dict[str, Any]],
) -> None:
    case = _case(known_bad, "fisher_exact_known_answers")
    for answer in case["answers"]:
        expected = Fraction(answer["numerator"], answer["denominator"])
        assert builder._fisher_lower_tail(answer["x"]) == expected
        assert guard._fisher(answer["x"]) == expected


def test_fisher_grid_retains_every_missingness_branch(
    reconstructed: dict[str, Any],
    known_bad: dict[str, dict[str, Any]],
) -> None:
    branches = reconstructed["curves"]["missingness_branches"]
    assert [row["fresh_operational_positive_count"] for row in branches] == list(
        range(14)
    )
    bad = deepcopy(reconstructed["curves"])
    case = _case(known_bad, "fisher_branch_missing")
    bad["missingness_branches"] = [
        row
        for row in bad["missingness_branches"]
        if row["fresh_operational_positive_count"] != case["drop_x"]
    ]
    with pytest.raises(guard.ValidationError, match=case["expected_message"]):
        guard.validate_curves(bad)


def test_zero_event_bounds_and_registered_tolerance(
    known_bad: dict[str, dict[str, Any]],
) -> None:
    case = _case(known_bad, "zero_event_known_bounds")
    for n_text, rendered in case["expected_bounds"].items():
        n = int(n_text)
        expected = builder._zero_event_bound(n)
        assert builder._decimal_string(expected) == rendered
        guard._assert_close(rendered, guard._zero(n), f"n={n}")

    expected = guard._zero(59)
    close_but_not_equal = expected + Decimal("0.0000000000000000005")
    assert close_but_not_equal != expected
    guard._assert_close(format(close_but_not_equal, "f"), expected, "tolerance")
    too_far = expected + Decimal("0.0000000000000000007")
    with pytest.raises(guard.ValidationError, match="registered tolerance"):
        guard._assert_close(format(too_far, "f"), expected, "tolerance")


def test_zero_event_crossing_checks_n_minus_one(
    reconstructed: dict[str, Any],
    known_bad: dict[str, dict[str, Any]],
) -> None:
    bad = deepcopy(reconstructed["curves"])
    case = _case(known_bad, "zero_n_minus_one_copied_from_n")
    crossing = next(
        row
        for row in bad["zero_event_upper_bounds"]["threshold_crossings"]
        if row["threshold"] == case["threshold"]
    )
    crossing["upper_bound_at_n_minus_one"] = crossing["upper_bound_at_n"]
    with pytest.raises(guard.ValidationError, match=case["expected_message"]):
        guard.validate_curves(bad)


def test_zero_event_code_avoids_bit_exact_libm_trap(
    known_bad: dict[str, dict[str, Any]],
) -> None:
    case = _case(known_bad, "zero_libm_bit_exact")
    assert _has_bit_exact_libm_comparison(case["source"]) is True

    builder_source = BUILDER_PATH.read_text(encoding="utf-8")
    validator_source = VALIDATOR_PATH.read_text(encoding="utf-8")
    assert _contains_math_call(
        _function_node(builder_source, "_zero_event_bound")
    ) is False
    assert _contains_math_call(_function_node(validator_source, "_zero")) is False
    assert _has_bit_exact_libm_comparison(
        ast.unparse(_function_node(validator_source, "_assert_close"))
    ) is False

    n = case["n"]
    canonical = Decimal(builder._decimal_string(builder._zero_event_bound(n)))
    libm_rendering = Decimal(f"{1.0 - math.pow(0.05, 1.0 / n):.18f}")
    assert libm_rendering != canonical
