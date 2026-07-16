from __future__ import annotations

from scripts import validate_iter208_post_seal_forensic_correction as guard


def test_iter208_preflight_guard_passes() -> None:
    assert guard.validate(preflight=True) == []


def test_iter208_delta_is_additive_to_the_iter207_seal() -> None:
    guard.validate_seal_and_experiment_delta()


def test_iter208_names_every_required_frontier_organization() -> None:
    frontier = guard._json(
        f"{guard.ITER208_PREFIX}proof/frontier_sources.json"
    )
    observed = {row["organization"] for row in frontier["sources"]}
    assert guard.REQUIRED_ORGANIZATIONS <= observed
