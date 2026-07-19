"""Checks for the deterministic retained-experiment index."""

from pathlib import Path
import subprocess

import pytest

from scripts import experiment_index


ROOT = Path(__file__).resolve().parents[1]


def test_committed_experiment_index_is_current() -> None:
    assert experiment_index.read_index() == experiment_index.build_index()


def test_every_retained_hypothesis_and_result_is_indexed() -> None:
    index = experiment_index.read_index()
    for name, has_hypothesis, has_result in experiment_index.experiment_records():
        assert f"../experiments/{name}/" in index
        if has_hypothesis:
            assert f"../experiments/{name}/HYPOTHESIS.md" in index
        if has_result:
            assert f"../experiments/{name}/RESULT.md" in index


def test_readme_links_the_experiment_index() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/EXPERIMENT_INDEX.md" in readme


def test_directory_without_top_level_record_remains_visible(tmp_path: Path) -> None:
    directory = tmp_path / "experiments/source_snapshots"
    directory.mkdir(parents=True)

    records = experiment_index.experiment_records(tmp_path)
    rendered = experiment_index.build_index(tmp_path)

    assert records == [("source_snapshots", False, False)]
    assert "directory retained; no top-level hypothesis or result retained" in rendered
    assert "artifacts: none" in rendered


def test_untracked_record_is_not_silently_omitted(tmp_path: Path) -> None:
    directory = tmp_path / "experiments/iter239_untracked"
    directory.mkdir(parents=True)
    (directory / "HYPOTHESIS.md").write_text("fixture\n", encoding="utf-8")

    assert experiment_index.experiment_records(tmp_path) == [
        ("iter239_untracked", True, False)
    ]


def test_direct_child_symlink_fails(tmp_path: Path) -> None:
    experiments = tmp_path / "experiments"
    experiments.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "HYPOTHESIS.md").write_text("fixture\n", encoding="utf-8")
    (experiments / "iter239_external").symlink_to(outside, target_is_directory=True)

    with pytest.raises(
        experiment_index.ExperimentIndexError,
        match="direct child must be a real directory",
    ):
        experiment_index.experiment_records(tmp_path)


def test_unsafe_direct_child_name_fails(tmp_path: Path) -> None:
    directory = tmp_path / "experiments" / "iter239_bad)name"
    directory.mkdir(parents=True)

    with pytest.raises(
        experiment_index.ExperimentIndexError,
        match="unsafe direct-child name",
    ):
        experiment_index.experiment_records(tmp_path)


@pytest.mark.parametrize("artifact", ("HYPOTHESIS.md", "RESULT.md"))
def test_record_symlink_fails(tmp_path: Path, artifact: str) -> None:
    directory = tmp_path / "experiments/iter239_link"
    directory.mkdir(parents=True)
    outside = tmp_path / "outside.md"
    outside.write_text("fixture\n", encoding="utf-8")
    (directory / artifact).symlink_to(outside)

    with pytest.raises(
        experiment_index.ExperimentIndexError,
        match="regular non-symlink mode-100644",
    ):
        experiment_index.experiment_records(tmp_path)


@pytest.mark.parametrize("artifact", ("HYPOTHESIS.md", "RESULT.md"))
def test_record_worktree_mode_must_be_100644(
    tmp_path: Path,
    artifact: str,
) -> None:
    directory = tmp_path / "experiments/iter239_mode"
    directory.mkdir(parents=True)
    path = directory / artifact
    path.write_text("fixture\n", encoding="utf-8")
    path.chmod(0o755)

    with pytest.raises(
        experiment_index.ExperimentIndexError,
        match="mode-100644",
    ):
        experiment_index.experiment_records(tmp_path)


def test_record_git_index_mode_must_be_100644(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    directory = tmp_path / "experiments/iter239_index_mode"
    directory.mkdir(parents=True)
    path = directory / "HYPOTHESIS.md"
    path.write_text("fixture\n", encoding="utf-8")
    path.chmod(0o755)
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "experiments/iter239_index_mode/HYPOTHESIS.md"],
        check=True,
    )
    path.chmod(0o644)

    with pytest.raises(
        experiment_index.ExperimentIndexError,
        match="Git index mode must be 100644",
    ):
        experiment_index.experiment_records(tmp_path)


def test_numeric_ordering_is_deterministic_with_tie_break(tmp_path: Path) -> None:
    experiments = tmp_path / "experiments"
    experiments.mkdir()
    for name in ("iter10_z", "iter2_z", "iter02_a", "support", "iter1_z"):
        directory = experiments / name
        directory.mkdir()
        (directory / "HYPOTHESIS.md").write_text("fixture\n", encoding="utf-8")

    assert [row[0] for row in experiment_index.experiment_records(tmp_path)] == [
        "iter1_z",
        "iter02_a",
        "iter2_z",
        "iter10_z",
        "support",
    ]


def _write_temp_index(root: Path) -> Path:
    (root / "experiments/source_snapshots").mkdir(parents=True)
    index = root / "docs/EXPERIMENT_INDEX.md"
    index.parent.mkdir()
    index.write_text(experiment_index.build_index(root), encoding="utf-8")
    return index


def test_generated_index_symlink_fails_even_with_expected_bytes(
    tmp_path: Path,
) -> None:
    index = _write_temp_index(tmp_path)
    outside = tmp_path / "external-index.md"
    outside.write_bytes(index.read_bytes())
    index.unlink()
    index.symlink_to(outside)

    with pytest.raises(
        experiment_index.ExperimentIndexError,
        match="regular non-symlink mode-100644",
    ):
        experiment_index.read_index(tmp_path)


def test_generated_index_worktree_mode_must_be_100644(tmp_path: Path) -> None:
    index = _write_temp_index(tmp_path)
    index.chmod(0o755)

    with pytest.raises(
        experiment_index.ExperimentIndexError,
        match="mode-100644",
    ):
        experiment_index.read_index(tmp_path)


def test_generated_index_git_mode_must_be_100644(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    index = _write_temp_index(tmp_path)
    index.chmod(0o755)
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "docs/EXPERIMENT_INDEX.md"],
        check=True,
    )
    index.chmod(0o644)

    with pytest.raises(
        experiment_index.ExperimentIndexError,
        match="index Git mode must be 100644",
    ):
        experiment_index.read_index(tmp_path)
