from __future__ import annotations

from pathlib import Path
import re


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


def test_ci_fetches_history_before_validating_handoff_lineage() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    checkout = re.search(
        r"(?m)^\s*- uses: actions/checkout@[0-9a-f]{40}(?:\s+#.*)?\n"
        r"\s+with:\n"
        r"\s+fetch-depth:\s*0\s*$",
        workflow,
    )
    assert checkout is not None
    handoff_guard = workflow.index("run: python3 scripts/validate_handoff.py")
    assert checkout.start() < handoff_guard


def test_active_denominator_backfill_uses_node24_action_revisions() -> None:
    workflow = (
        ROOT / ".github/workflows/iter200-denominator-backfill.yml"
    ).read_text(encoding="utf-8")
    assert (
        "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7"
        in workflow
    )
    assert (
        "actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f # v6"
        in workflow
    )


def test_historical_design_and_learning_docs_defer_to_current_authorities() -> None:
    architecture = (ROOT / "docs/ARCHITECTURE.md").read_text(encoding="utf-8")
    learning = (ROOT / "docs/LEARNING_ENGINE.md").read_text(encoding="utf-8")
    learning_flat = " ".join(learning.split())

    assert "**Historical foundational design.**" in architecture
    assert "original design boundary" in architecture
    assert "The first benchmark target will freeze" not in architecture
    assert "Generated `HANDOFF.md` owns the current operational action" in learning_flat
    assert "authoritative next-action reader" not in learning


def test_paper_revision_date_and_build_metadata_are_reproducible() -> None:
    source = (ROOT / "paper/telos.tex").read_text(encoding="utf-8")
    readme = (ROOT / "paper/README.md").read_text(encoding="utf-8")
    readme_flat = " ".join(readme.split())

    assert r"\date{July 16, 2026}" in source
    assert r"\date{\today}" not in source
    assert "SOURCE_DATE_EPOCH=1784160000 tectonic telos.tex" in readme
    assert "Two consecutive Tectonic builds must have identical SHA-256 digests" in readme_flat
