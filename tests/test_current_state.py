"""Tests for the mutable Telos current-state pointer."""

from __future__ import annotations

import json
from pathlib import Path

from scripts import validate_current_state as guard


def _fixture(tmp_path: Path) -> dict:
    paths = (
        "experiments/iter237_truth_maintenance_gate/HYPOTHESIS.md",
        "docs/HANDOFF-2026-07-19-iter237.md",
        "docs/TELOS-AUDIT-2026-07-19.md",
    )
    for relative in paths:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")

    current = {
        "schema_version": "telos.current.v1",
        "updated": "2026-07-19",
        "status": "running",
        "active_gate": paths[0],
        "current_handoff": paths[1],
        "current_audit": paths[2],
        "paper_revision": "July 19, 2026",
        "scientific_status": "blocked pending independent ground truth",
        "next_authorized_action": "complete iter237 truth maintenance",
        "claim_boundary": "cross-solver recurrence on one fixed cohort only",
        "historical_surfaces": ["HANDOFF.md", "mission/loop.json"],
    }
    (tmp_path / "mission").mkdir(parents=True, exist_ok=True)
    (tmp_path / "mission/current.json").write_text(
        json.dumps(current), encoding="utf-8"
    )
    (tmp_path / "AGENTS.md").write_text(
        "Read `mission/current.json`, then its `current_handoff`; "
        "HANDOFF.md and mission/loop.json are historical.\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text(
        "\n".join((paths[0], paths[1], paths[2])) + "\n", encoding="utf-8"
    )
    (tmp_path / "paper").mkdir(parents=True, exist_ok=True)
    (tmp_path / "paper/telos.tex").write_text(
        r"\date{July 19, 2026}" + "\n", encoding="utf-8"
    )
    (tmp_path / paths[1]).write_text(
        "\n".join(
            (
                paths[0],
                paths[2],
                current["scientific_status"],
                current["next_authorized_action"],
            )
        )
        + "\n",
        encoding="utf-8",
    )
    return current


def test_known_good_current_state(tmp_path: Path) -> None:
    _fixture(tmp_path)
    assert guard.validate(root=tmp_path) == []


def test_stale_active_gate_fails(tmp_path: Path) -> None:
    current = _fixture(tmp_path)
    current["active_gate"] = "experiments/iter222_old/HYPOTHESIS.md"
    (tmp_path / "mission/current.json").write_text(json.dumps(current), encoding="utf-8")
    failures = guard.validate(root=tmp_path)
    assert any("active_gate does not name a file" in failure for failure in failures)


def test_bootstrap_that_ignores_pointer_fails(tmp_path: Path) -> None:
    _fixture(tmp_path)
    (tmp_path / "AGENTS.md").write_text("Read HANDOFF.md.\n", encoding="utf-8")
    failures = guard.validate(root=tmp_path)
    assert any("mission/current.json" in failure for failure in failures)


def test_paper_revision_drift_fails(tmp_path: Path) -> None:
    _fixture(tmp_path)
    (tmp_path / "paper/telos.tex").write_text(
        r"\date{July 16, 2026}" + "\n", encoding="utf-8"
    )
    failures = guard.validate(root=tmp_path)
    assert "paper revision does not match mission/current.json" in failures


def test_handoff_must_bind_next_action(tmp_path: Path) -> None:
    current = _fixture(tmp_path)
    handoff = tmp_path / current["current_handoff"]
    handoff.write_text("incomplete handoff\n", encoding="utf-8")
    failures = guard.validate(root=tmp_path)
    assert "current handoff does not bind next_authorized_action" in failures


def test_repository_current_state_passes() -> None:
    assert guard.validate() == []
