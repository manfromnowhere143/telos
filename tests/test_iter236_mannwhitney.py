"""Equivalence tests for the iter236 pure-Python Mann-Whitney implementation.

The iter236 builder cannot import scipy: CI installs from a hash-pinned verification-only
requirements file that does not carry it. The statistic is therefore implemented in pure
Python, and these tests pin it against scipy wherever scipy is importable, so a divergence
is caught on any developer machine that has it.

Where scipy is absent the equivalence tests skip, and the fixed-value regression tests
below still run. Those encode the figures published in the iter236 RESULT, so CI cannot go
green on a silently changed statistic.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location(
    "iter236_builder", ROOT / "scripts/build_iter236_transfer_analysis.py"
)
assert _spec is not None and _spec.loader is not None
builder = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(builder)

# The cohort's actual added-source-line vectors, as published in the iter236 RESULT.
HACKED = [1, 1, 3, 4, 4, 4, 6, 7, 8, 13]

SAMPLES = [
    ([1, 2, 3, 4, 5], [6, 7, 8, 9, 10]),
    ([1, 1, 1, 2, 2], [1, 2, 2, 3, 3]),
    ([5, 3, 9, 1], [4, 4, 4, 4, 4, 4]),
    (HACKED, [1] * 30 + [2, 3, 4, 5, 6, 0, 0, 0, 9, 11, 1, 1, 2]),
]


def test_rankdata_shares_ties() -> None:
    assert builder._rankdata([10, 20, 20, 30]) == [1.0, 2.5, 2.5, 4.0]


@pytest.mark.parametrize("a,b", SAMPLES)
def test_matches_scipy_asymptotic(a: list[int], b: list[int]) -> None:
    scipy_stats = pytest.importorskip("scipy.stats")
    for continuity in (True, False):
        mine = builder._mannwhitney(a, b, continuity=continuity)
        theirs = scipy_stats.mannwhitneyu(
            a, b, alternative="greater", method="asymptotic", use_continuity=continuity
        )
        assert mine["u"] == pytest.approx(float(theirs.statistic))
        assert mine["p_greater"] == pytest.approx(float(theirs.pvalue), rel=1e-9)


@pytest.mark.parametrize("a,b", SAMPLES)
def test_matches_scipy_two_sided(a: list[int], b: list[int]) -> None:
    scipy_stats = pytest.importorskip("scipy.stats")
    mine = builder._mannwhitney(a, b)["p_two_sided"]
    theirs = float(
        scipy_stats.mannwhitneyu(a, b, alternative="two-sided", method="asymptotic").pvalue
    )
    assert mine == pytest.approx(theirs, rel=1e-9)


def test_exact_matches_scipy_untied() -> None:
    """The exact null ignores ties, so pin it on an untied sample where scipy agrees."""

    scipy_stats = pytest.importorskip("scipy.stats")
    a, b = [1, 2, 3, 4, 5], [6, 7, 8, 9, 10, 11]
    mine = builder._mannwhitney_exact_two_sided(a, b)
    theirs = float(
        scipy_stats.mannwhitneyu(a, b, alternative="two-sided", method="exact").pvalue
    )
    assert mine == pytest.approx(theirs, rel=1e-9)


def test_tolerance_forgives_one_ulp_of_platform_drift() -> None:
    """The Linux CI failure this reproduces: a correct value rejected bit-exactly."""

    import math

    value = 0.0026736527246468
    drifted = math.nextafter(math.nextafter(value, 1.0), 1.0)
    assert drifted != value
    assert builder._matches({"p": drifted}, {"p": value}, "root") == []


def test_tolerance_rejects_tampering_coarse_enough_to_change_a_digit() -> None:
    value = 0.0026736527246468
    for factor in (1.0 + 1e-8, 1.0 + 1e-4, 1.5):
        problems = builder._matches({"p": value * factor}, {"p": value}, "root")
        assert problems, f"tampering at factor {factor} was not caught"


def test_integers_and_booleans_stay_exact() -> None:
    """Counts and eligibility flags are platform-independent and get no tolerance."""

    assert builder._matches({"n": 62}, {"n": 59}, "root")
    assert builder._matches({"n": 63}, {"n": 62}, "root")
    assert builder._matches({"ok": False}, {"ok": True}, "root")
    # Python considers True == 1, but the JSON evidence contract must reject type drift.
    assert builder._matches({"ok": True}, {"ok": 1}, "root")
    assert builder._matches({"n": 62}, {"n": 62.0}, "root")
    assert builder._matches({"p": "0.5"}, {"p": 0.5}, "root")


def test_structural_changes_are_caught() -> None:
    assert builder._matches({"a": 1}, {"a": 1, "b": 2}, "root")
    assert builder._matches({"a": 1, "b": 2}, {"a": 1}, "root")
    assert builder._matches({"a": [1, 2]}, {"a": [1, 2, 3]}, "root")


def test_committed_artifact_validates() -> None:
    """The guard passes against the artifact actually committed to the repository."""

    import json

    committed = json.loads(
        (
            ROOT
            / "experiments/iter236_transfer_analysis_reconstruction/proof/transfer_analysis.json"
        ).read_text()
    )
    assert builder._matches(committed, builder.build(), "root") == []


def test_published_figures_are_pinned() -> None:
    """Regression guard on the exact values the iter236 RESULT publishes."""

    others = builder.build()["within_cohort"]
    assert others["mannwhitney_u"] == 331.0
    assert others["p_one_sided_greater"] == pytest.approx(0.0026736527246468, rel=1e-9)
    assert others["p_two_sided"] == pytest.approx(0.005347305449293, rel=1e-9)
    assert others["c8_diagnosis"]["exact_two_sided"] == pytest.approx(0.007184, rel=1e-3)
