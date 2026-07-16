from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from scripts import run_ci_closure
from scripts.validate_detector_methodology_correction import normalize_prose

ROOT = Path(__file__).resolve().parents[1]

# The exact sentence whose line wrap broke the iter214 handoff seal in one session and
# iter219's publication CI in the next.
WRAPPED = (
    "The standing detector correction also remains binding: the property instrument is a "
    "locator-assisted,\ngold-validated property pipeline, not an independent detector.\n"
)


# --------------------------------------------------------------------------- #
# C1 — required-phrase scanning must test meaning, not line width.
# --------------------------------------------------------------------------- #


def test_the_exact_wrap_that_failed_ci_twice_now_normalizes() -> None:
    assert "locator-assisted, gold-validated" in normalize_prose(WRAPPED)


def test_normalizer_strips_blockquote_markers() -> None:
    assert normalize_prose("> locator-assisted,\n> gold-validated pipeline") == (
        "locator-assisted, gold-validated pipeline"
    )


def test_normalizer_preserves_ordinary_prose() -> None:
    assert normalize_prose("plain\nwrapped text") == "plain wrapped text"


def test_normalizer_does_not_invent_a_missing_phrase() -> None:
    # Normalization must only forgive formatting, never absence.  If the methodology text
    # is genuinely gone, the scan must still fail.
    absent = "The property instrument is an independent detector.\n"
    assert "locator-assisted, gold-validated" not in normalize_prose(absent)


def test_normalizer_does_not_join_across_a_paragraph_into_a_false_match() -> None:
    # "locator-assisted," ending one sentence and "gold-validated" opening an unrelated one
    # would be a false positive if normalization were naive about ordering; it is not, but
    # pin the behaviour so a future edit cannot silently loosen it.
    text = "ends with locator-assisted, gold-validated begins here"
    assert "locator-assisted, gold-validated" in normalize_prose(text)


def test_live_detector_guard_passes_on_the_committed_handoff() -> None:
    result = subprocess.run(
        ["python3", "scripts/validate_detector_methodology_correction.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


# --------------------------------------------------------------------------- #
# C2 — local closure must be derived from CI, never hand-listed.
# --------------------------------------------------------------------------- #


def test_closure_commands_are_derived_from_the_workflow_not_hard_coded() -> None:
    commands = run_ci_closure.declared_commands()
    document = yaml.safe_load(run_ci_closure.WORKFLOW.read_text(encoding="utf-8"))
    declared_steps = {
        step.get("name", "")
        for step in document["jobs"]["verify"]["steps"]
        if step.get("run") and step.get("name") not in run_ci_closure.SKIP_STEP_NAMES
    }

    assert declared_steps == {name for name, _ in commands}


def test_closure_includes_the_guard_that_iter219_never_ran() -> None:
    commands = [command for _, command in run_ci_closure.declared_commands()]
    assert any("validate_detector_methodology_correction.py" in c for c in commands)


def test_closure_is_far_larger_than_a_hand_written_list() -> None:
    # Iter219's local closure ran roughly seven guards and called itself complete.
    assert len(run_ci_closure.declared_commands()) > 200


def test_closure_preserves_environment_overrides_from_the_workflow() -> None:
    # `env -u OPENAI_API_KEY ... TELOS_NAT_REUSE_JUDGES=1 python3 x.py` must survive as one
    # command; dropping the prefix would make provider-free guards fail or, worse, run hot.
    commands = [command for _, command in run_ci_closure.declared_commands()]
    reuse = [c for c in commands if "run_iter200_blind_judge.py" in c]

    assert reuse, "the blind-judge reuse guard must be discovered"
    assert all("TELOS_NAT_REUSE_JUDGES=1" in c for c in reuse)
    assert all("env -u" in c for c in reuse)


def test_closure_skips_only_non_guard_steps() -> None:
    assert run_ci_closure.SKIP_STEP_NAMES == {
        "Install verification tools",
        "Full clean-tree guard",
    }


def test_closure_reports_a_failing_guard(tmp_path) -> None:
    workflow = tmp_path / "ci.yml"
    workflow.write_text(
        yaml.safe_dump(
            {
                "jobs": {
                    "verify": {
                        "steps": [
                            {"name": "Passing guard", "run": "true"},
                            {"name": "Failing guard", "run": "false"},
                        ]
                    }
                }
            }
        )
    )
    commands = run_ci_closure.declared_commands(workflow)
    failures = run_ci_closure.run(commands)

    assert [name for name, _, _ in failures] == ["Failing guard"]


def test_closure_returns_empty_when_every_command_passes(tmp_path) -> None:
    workflow = tmp_path / "ci.yml"
    workflow.write_text(
        yaml.safe_dump({"jobs": {"verify": {"steps": [{"name": "ok", "run": "true"}]}}})
    )
    assert run_ci_closure.run(run_ci_closure.declared_commands(workflow)) == []


# --------------------------------------------------------------------------- #
# Iter219's evidence must be untouched by this recovery.
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "path",
    [
        "experiments/iter219_temporal_consequence_test_yield/HYPOTHESIS.md",
        "experiments/iter219_temporal_consequence_test_yield/RESULT.md",
        "experiments/iter219_temporal_consequence_test_yield/proof/yield_report.json",
        "experiments/iter219_temporal_consequence_test_yield/proof/analysis_amendment.json",
    ],
)
def test_iter219_evidence_is_byte_identical_to_its_seal(path: str) -> None:
    sealed = subprocess.run(
        ["git", "show", f"11e335e82100319a4f5f47d86eaea0c8e81edbbc:{path}"],
        cwd=ROOT,
        capture_output=True,
    )
    assert sealed.returncode == 0, sealed.stderr.decode()
    assert (ROOT / path).read_bytes() == sealed.stdout, f"{path} changed during recovery"
