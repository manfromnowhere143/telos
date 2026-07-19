"""Checks for the deterministic retained-experiment index."""

import os
from pathlib import Path
import subprocess

import pytest

from scripts import experiment_index


ROOT = Path(__file__).resolve().parents[1]


def _git(
    root: Path,
    *arguments: str,
    input_bytes: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        input=input_bytes,
    )


def _init_repository(root: Path) -> None:
    _git(root.parent, "init", "-q", str(root))
    _git(root, "config", "user.name", "Experiment Index Test")
    _git(root, "config", "user.email", "experiment-index@example.invalid")


def _commit_all(root: Path, message: str = "fixture") -> str:
    _git(root, "add", "--all")
    _git(root, "commit", "-q", "-m", message)
    return _git(root, "rev-parse", "HEAD").stdout.decode("ascii").strip()


def _write_record(
    root: Path,
    *,
    name: str = "iter239_fixture",
    artifact: str = "HYPOTHESIS.md",
    payload: str = "fixture\n",
) -> Path:
    path = root / "experiments" / name / artifact
    path.parent.mkdir(parents=True)
    path.write_text(payload, encoding="utf-8")
    return path


def test_local_git_queries_do_not_inherit_credentials(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_run(
        command: list[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[bytes]:
        captured["command"] = command
        captured.update(kwargs)
        return subprocess.CompletedProcess(command, 0, b"", b"")

    monkeypatch.setenv("GIT_ASKPASS", "/secret/helper")
    monkeypatch.setenv("GH_TOKEN", "secret")
    monkeypatch.setattr(experiment_index.subprocess, "run", fake_run)

    result = experiment_index._git(tmp_path, "rev-parse", "--show-toplevel")

    assert result.returncode == 0
    command = captured["command"]
    assert isinstance(command, list)
    assert "credential.helper=" in command
    assert "credential.interactive=never" in command
    assert command[-2:] == ["rev-parse", "--show-toplevel"]
    environment = captured["env"]
    assert isinstance(environment, dict)
    assert "GIT_ASKPASS" not in environment
    assert "GH_TOKEN" not in environment
    assert environment["GIT_CONFIG_GLOBAL"] == os.devnull
    assert environment["GIT_CONFIG_NOSYSTEM"] == "1"
    assert environment["GIT_TERMINAL_PROMPT"] == "0"


@pytest.mark.parametrize(
    ("source", "payload", "message"),
    (
        (
            "head",
            b"100644 blob " + (b"0" * 40) + b"\texperiments/bad-\xff\0",
            "malformed or non-UTF-8",
        ),
        (
            "head",
            b"100644 blob " + (b"0" * 40) + b"\texperiments/fixture",
            "non-NUL-terminated",
        ),
        (
            "index",
            b"100644 " + (b"0" * 40) + b" 0\texperiments/bad-\xff\0",
            "malformed or non-UTF-8",
        ),
        (
            "index",
            b"not metadata\texperiments/fixture\0",
            "malformed or non-UTF-8",
        ),
    ),
)
def test_malformed_or_non_utf8_git_entries_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    source: str,
    payload: bytes,
    message: str,
) -> None:
    relative = "experiments/fixture"

    def fake_git(
        _root: Path,
        *arguments: str,
        input_bytes: bytes | None = None,
    ) -> subprocess.CompletedProcess[bytes]:
        del arguments, input_bytes
        return subprocess.CompletedProcess([], 0, payload, b"")

    monkeypatch.setattr(experiment_index, "_git", fake_git)
    with pytest.raises(experiment_index.ExperimentIndexError, match=message):
        if source == "head":
            experiment_index._head_entry(tmp_path, relative)
        else:
            experiment_index._index_entry(tmp_path, relative)


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


def test_untracked_record_is_visible_as_a_directory_but_not_retained(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "experiments/iter239_untracked"
    directory.mkdir(parents=True)
    (directory / "HYPOTHESIS.md").write_text("fixture\n", encoding="utf-8")

    assert experiment_index.experiment_records(tmp_path) == [
        ("iter239_untracked", False, False)
    ]


def test_staged_uncommitted_record_is_not_retained(tmp_path: Path) -> None:
    _init_repository(tmp_path)
    path = _write_record(tmp_path, name="iter239_staged")
    _git(tmp_path, "add", path.relative_to(tmp_path).as_posix())

    assert experiment_index.experiment_records(tmp_path) == [
        ("iter239_staged", False, False)
    ]


def test_committed_clean_record_is_retained(tmp_path: Path) -> None:
    _init_repository(tmp_path)
    _write_record(tmp_path, name="iter239_committed")
    _commit_all(tmp_path)

    assert experiment_index.experiment_records(tmp_path) == [
        ("iter239_committed", True, False)
    ]


def test_committed_record_worktree_drift_is_rejected(tmp_path: Path) -> None:
    _init_repository(tmp_path)
    path = _write_record(tmp_path, name="iter239_worktree_drift")
    _commit_all(tmp_path)
    path.write_text("changed but unstaged\n", encoding="utf-8")

    with pytest.raises(
        experiment_index.ExperimentIndexError,
        match="worktree bytes differ from committed HEAD blob",
    ):
        experiment_index.experiment_records(tmp_path)


def test_committed_record_staged_drift_is_rejected(tmp_path: Path) -> None:
    _init_repository(tmp_path)
    path = _write_record(tmp_path, name="iter239_index_drift")
    original = path.read_bytes()
    _commit_all(tmp_path)
    path.write_text("changed and staged\n", encoding="utf-8")
    _git(tmp_path, "add", path.relative_to(tmp_path).as_posix())
    path.write_bytes(original)

    with pytest.raises(
        experiment_index.ExperimentIndexError,
        match="Git index object differs from committed HEAD blob",
    ):
        experiment_index.experiment_records(tmp_path)


def test_committed_record_missing_from_worktree_is_rejected(tmp_path: Path) -> None:
    _init_repository(tmp_path)
    path = _write_record(tmp_path, name="iter239_deleted")
    _commit_all(tmp_path)
    path.unlink()

    with pytest.raises(
        experiment_index.ExperimentIndexError,
        match="committed HEAD record is absent from the worktree",
    ):
        experiment_index.experiment_records(tmp_path)


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
    _init_repository(tmp_path)
    path = _write_record(tmp_path, name="iter239_index_mode")
    _commit_all(tmp_path)
    _git(
        tmp_path,
        "update-index",
        "--chmod=+x",
        path.relative_to(tmp_path).as_posix(),
    )

    with pytest.raises(
        experiment_index.ExperimentIndexError,
        match="Git index mode must be 100644, observed 100755",
    ):
        experiment_index.experiment_records(tmp_path)


def test_record_committed_head_mode_must_be_100644(tmp_path: Path) -> None:
    _init_repository(tmp_path)
    path = _write_record(tmp_path, name="iter239_head_mode")
    _git(tmp_path, "add", path.relative_to(tmp_path).as_posix())
    _git(
        tmp_path,
        "update-index",
        "--chmod=+x",
        path.relative_to(tmp_path).as_posix(),
    )
    _git(tmp_path, "commit", "-q", "-m", "executable fixture")

    with pytest.raises(
        experiment_index.ExperimentIndexError,
        match="committed HEAD mode must be 100644, observed 100755",
    ):
        experiment_index.experiment_records(tmp_path)


def test_record_conflicted_index_is_rejected(tmp_path: Path) -> None:
    _init_repository(tmp_path)
    path = _write_record(tmp_path, name="iter239_conflict")
    _commit_all(tmp_path)
    relative = path.relative_to(tmp_path).as_posix()
    head_blob = _git(tmp_path, "rev-parse", f"HEAD:{relative}").stdout.strip()
    other_blob = _git(
        tmp_path,
        "hash-object",
        "-w",
        "--stdin",
        input_bytes=b"conflicting fixture\n",
    ).stdout.strip()
    _git(tmp_path, "update-index", "--force-remove", relative)
    index_info = (
        b"100644 " + head_blob + b" 1\t" + relative.encode("utf-8") + b"\n"
        b"100644 " + other_blob + b" 2\t" + relative.encode("utf-8") + b"\n"
    )
    _git(tmp_path, "update-index", "--index-info", input_bytes=index_info)

    with pytest.raises(
        experiment_index.ExperimentIndexError,
        match="ambiguous or conflicted Git index entries",
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


def _commit_temp_index(root: Path) -> Path:
    _init_repository(root)
    index = _write_temp_index(root)
    _commit_all(root)
    return index


def test_generated_index_must_be_committed_in_head(tmp_path: Path) -> None:
    _init_repository(tmp_path)
    _write_temp_index(tmp_path)

    with pytest.raises(
        experiment_index.ExperimentIndexError,
        match="index is not committed in HEAD",
    ):
        experiment_index.read_index(tmp_path)


def test_staged_uncommitted_generated_index_is_rejected(tmp_path: Path) -> None:
    _init_repository(tmp_path)
    index = _write_temp_index(tmp_path)
    _git(tmp_path, "add", index.relative_to(tmp_path).as_posix())

    with pytest.raises(
        experiment_index.ExperimentIndexError,
        match="index is not committed in HEAD",
    ):
        experiment_index.read_index(tmp_path)


def test_committed_clean_generated_index_is_read(tmp_path: Path) -> None:
    index = _commit_temp_index(tmp_path)

    assert experiment_index.read_index(tmp_path) == index.read_text(encoding="utf-8")


def test_generated_index_worktree_drift_is_rejected(tmp_path: Path) -> None:
    index = _commit_temp_index(tmp_path)
    index.write_text("drift\n", encoding="utf-8")

    with pytest.raises(
        experiment_index.ExperimentIndexError,
        match="worktree bytes differ from committed HEAD blob",
    ):
        experiment_index.read_index(tmp_path)


def test_generated_index_staged_drift_is_rejected(tmp_path: Path) -> None:
    index = _commit_temp_index(tmp_path)
    original = index.read_bytes()
    index.write_text("staged drift\n", encoding="utf-8")
    _git(tmp_path, "add", index.relative_to(tmp_path).as_posix())
    index.write_bytes(original)

    with pytest.raises(
        experiment_index.ExperimentIndexError,
        match="Git index object differs from committed HEAD blob",
    ):
        experiment_index.read_index(tmp_path)


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
    index = _commit_temp_index(tmp_path)
    _git(
        tmp_path,
        "update-index",
        "--chmod=+x",
        index.relative_to(tmp_path).as_posix(),
    )

    with pytest.raises(
        experiment_index.ExperimentIndexError,
        match="Git index mode must be 100644, observed 100755",
    ):
        experiment_index.read_index(tmp_path)


def test_generated_index_committed_head_mode_must_be_100644(
    tmp_path: Path,
) -> None:
    _init_repository(tmp_path)
    index = _write_temp_index(tmp_path)
    relative = index.relative_to(tmp_path).as_posix()
    _git(tmp_path, "add", relative)
    _git(tmp_path, "update-index", "--chmod=+x", relative)
    _git(tmp_path, "commit", "-q", "-m", "executable index fixture")

    with pytest.raises(
        experiment_index.ExperimentIndexError,
        match="committed HEAD mode must be 100644, observed 100755",
    ):
        experiment_index.read_index(tmp_path)
