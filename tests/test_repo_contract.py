from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_core_research_files_exist() -> None:
    required = [
        "README.md",
        "PREREGISTRATION.md",
        "CONTINUITY.md",
        "HANDOFF.md",
        "docs/ARCHITECTURE.md",
        "docs/RELATED_WORK.md",
        "docs/REPORT.md",
        "experiments/iter00_target_survey/HYPOTHESIS.md",
        "protocol/proof.schema.json",
    ]
    for relative in required:
        assert (ROOT / relative).exists(), relative


def test_readme_names_the_first_gate_and_scopes_historical_results() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "iter00_target_survey" in readme
    assert "At the iter165 boundary, a bounded paired single-model judge result existed" in readme
    assert "No leaderboard, public benchmark score, model-comparison result," in readme
    assert "precision result beyond the explicitly bounded denominators" in readme
