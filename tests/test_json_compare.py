from __future__ import annotations

import math

import pytest

from telos.json_compare import (
    DEFAULT_FLOAT_ABS_TOL,
    DEFAULT_FLOAT_REL_TOL,
    compare_json,
)


def test_nested_json_values_match_without_object_key_order() -> None:
    actual = {"rows": [{"ok": True, "score": 0.25}], "count": 1}
    expected = {"count": 1, "rows": [{"score": 0.25, "ok": True}]}

    assert compare_json(actual, expected) == []


def test_float_comparison_forgives_platform_ulp_drift() -> None:
    expected = 0.0026736527246468
    actual = math.nextafter(math.nextafter(expected, math.inf), math.inf)

    assert actual != expected
    assert compare_json(actual, expected) == []


def test_float_comparison_rejects_reported_digit_tampering() -> None:
    problems = compare_json(0.0026737, 0.0026736)

    assert problems
    assert "beyond float tolerance" in problems[0]
    assert 1e-16 < DEFAULT_FLOAT_REL_TOL < 1e-4
    assert DEFAULT_FLOAT_ABS_TOL < 1e-4


@pytest.mark.parametrize(
    ("actual", "expected"),
    [
        (62, 62.0),
        (62.0, 62),
        ("0.5", 0.5),
        (0.5, "0.5"),
        (True, 1),
        (1, True),
        (False, 0.0),
        (None, "null"),
    ],
)
def test_cross_type_changes_never_receive_numeric_tolerance(
    actual: object,
    expected: object,
) -> None:
    problems = compare_json(actual, expected)

    assert problems
    assert "JSON type changed" in problems[0]


def test_non_float_json_leaves_stay_exact() -> None:
    assert compare_json(62, 63)
    assert compare_json(True, False)
    assert compare_json("supported", "unsupported")
    assert compare_json(None, None) == []


def test_object_and_array_shape_changes_report_the_exact_path() -> None:
    missing = compare_json({"row": {"n": 1}}, {"row": {"n": 1, "u": 0}})
    unexpected = compare_json({"row": {"n": 1, "u": 0}}, {"row": {"n": 1}})
    length = compare_json({"row": [1]}, {"row": [1, 2]})

    assert missing == ["root.row.u: missing from actual value"]
    assert unexpected == ["root.row.u: unexpected in actual value"]
    assert length == ["root.row: array length changed (1 != 2)"]


@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan])
def test_non_finite_values_are_rejected_as_non_json(value: float) -> None:
    assert compare_json(value, value) == [
        "root: non-finite floats are not valid JSON values"
    ]


def test_non_json_container_type_is_rejected() -> None:
    assert compare_json((1, 2), (1, 2)) == ["root: unsupported JSON type tuple"]
