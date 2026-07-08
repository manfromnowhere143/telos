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


def test_readme_names_the_first_gate_without_claiming_results() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "iter00_target_survey" in readme
    assert "No result is claimed yet" in readme
