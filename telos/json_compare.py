"""Strict, platform-aware comparison for values decoded from JSON.

JSON types are part of the evidence contract.  Float tolerance therefore applies
only when both values are floats; it must never turn an integer, boolean, string,
or null into a numeric match.  The default tolerance is intentionally wide
enough for cross-platform ``libm`` drift and narrow enough to reject changes in
reported digits.
"""

from __future__ import annotations

import math

DEFAULT_FLOAT_REL_TOL = 1e-9
DEFAULT_FLOAT_ABS_TOL = 1e-12

_JSON_TYPES = (dict, list, str, int, float, bool, type(None))


def compare_json(
    actual: object,
    expected: object,
    *,
    path: str = "root",
    float_rel_tol: float = DEFAULT_FLOAT_REL_TOL,
    float_abs_tol: float = DEFAULT_FLOAT_ABS_TOL,
) -> list[str]:
    """Return path-qualified mismatches between two JSON-compatible values.

    Objects are compared without regard to key order and arrays retain order.
    Only float-versus-float leaves use ``math.isclose``.  All cross-type changes
    fail before Python's coercive equality rules (for example ``True == 1``)
    can apply.
    """

    actual_type = type(actual)
    expected_type = type(expected)
    if actual_type is not expected_type:
        return [
            f"{path}: JSON type changed "
            f"({actual_type.__name__} != {expected_type.__name__})"
        ]
    if actual_type not in _JSON_TYPES:
        return [f"{path}: unsupported JSON type {actual_type.__name__}"]

    if actual_type is dict:
        actual_object = actual
        expected_object = expected
        invalid_keys = [
            repr(key)
            for key in [*actual_object, *expected_object]
            if type(key) is not str
        ]
        if invalid_keys:
            return [f"{path}: JSON object keys must be strings: {sorted(set(invalid_keys))}"]

        problems: list[str] = []
        for key in sorted(set(actual_object) | set(expected_object)):
            if key not in actual_object:
                problems.append(f"{path}.{key}: missing from actual value")
            elif key not in expected_object:
                problems.append(f"{path}.{key}: unexpected in actual value")
            else:
                problems.extend(
                    compare_json(
                        actual_object[key],
                        expected_object[key],
                        path=f"{path}.{key}",
                        float_rel_tol=float_rel_tol,
                        float_abs_tol=float_abs_tol,
                    )
                )
        return problems

    if actual_type is list:
        actual_array = actual
        expected_array = expected
        if len(actual_array) != len(expected_array):
            return [
                f"{path}: array length changed "
                f"({len(actual_array)} != {len(expected_array)})"
            ]
        problems = []
        for index, (actual_item, expected_item) in enumerate(
            zip(actual_array, expected_array, strict=True)
        ):
            problems.extend(
                compare_json(
                    actual_item,
                    expected_item,
                    path=f"{path}[{index}]",
                    float_rel_tol=float_rel_tol,
                    float_abs_tol=float_abs_tol,
                )
            )
        return problems

    if actual_type is float:
        if not math.isfinite(actual) or not math.isfinite(expected):
            return [f"{path}: non-finite floats are not valid JSON values"]
        if math.isclose(
            actual,
            expected,
            rel_tol=float_rel_tol,
            abs_tol=float_abs_tol,
        ):
            return []
        return [f"{path}: {actual!r} != {expected!r} beyond float tolerance"]

    return [] if actual == expected else [f"{path}: {actual!r} != {expected!r}"]
