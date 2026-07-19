#!/usr/bin/env python3
"""Index retained top-level directories under Telos's experiments/ tree."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import stat
import subprocess


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs/EXPERIMENT_INDEX.md"
ITERATION_NAME = re.compile(r"^iter(\d+)(?:_|$)")
SAFE_DIRECTORY_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


class ExperimentIndexError(ValueError):
    """Raised when a retained experiment path is not safe to index."""


def experiment_sort_key(path: Path) -> tuple[int, int, bytes]:
    match = ITERATION_NAME.match(path.name)
    if match is None:
        return (1, 0, path.name.encode("utf-8"))
    return (0, int(match.group(1)), path.name.encode("utf-8"))


def _tracked_git_mode(root: Path, relative: str) -> str | None:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "ls-files",
            "--stage",
            "-z",
            "--",
            f":(literal){relative}",
        ],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    entries = [entry for entry in result.stdout.split(b"\0") if entry]
    if not entries:
        return None
    if len(entries) != 1:
        raise ExperimentIndexError(f"{relative}: ambiguous Git index entry")
    try:
        metadata, observed = entries[0].split(b"\t", 1)
        mode, _, stage = metadata.decode("ascii").split()
        observed_path = observed.decode("utf-8")
    except (UnicodeDecodeError, ValueError) as error:
        raise ExperimentIndexError(
            f"{relative}: unreadable Git index entry"
        ) from error
    if stage != "0" or observed_path != relative:
        raise ExperimentIndexError(f"{relative}: ambiguous Git index entry")
    return mode


def _retained_artifact(root: Path, path: Path) -> bool:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    relative = path.relative_to(root).as_posix()
    if (
        not stat.S_ISREG(metadata.st_mode)
        or path.is_symlink()
        or stat.S_IMODE(metadata.st_mode) != 0o644
    ):
        raise ExperimentIndexError(
            f"{relative}: retained record must be a regular non-symlink mode-100644 file"
        )
    tracked_mode = _tracked_git_mode(root, relative)
    if tracked_mode is not None and tracked_mode != "100644":
        raise ExperimentIndexError(
            f"{relative}: retained record Git index mode must be 100644"
        )
    return True


def _require_real_directory(path: Path, label: str) -> None:
    try:
        metadata = path.lstat()
    except OSError as error:
        raise ExperimentIndexError(f"{label}: directory is absent") from error
    if not stat.S_ISDIR(metadata.st_mode) or path.is_symlink():
        raise ExperimentIndexError(f"{label}: must be a real directory")


def experiment_records(root: Path = ROOT) -> list[tuple[str, bool, bool]]:
    records: list[tuple[str, bool, bool]] = []
    experiments = root / "experiments"
    _require_real_directory(experiments, "experiments/")

    directories = list(experiments.iterdir())
    for directory in directories:
        if SAFE_DIRECTORY_NAME.fullmatch(directory.name) is None:
            raise ExperimentIndexError(
                f"experiments/{directory.name}: unsafe direct-child name"
            )
        metadata = directory.lstat()
        if not stat.S_ISDIR(metadata.st_mode) or directory.is_symlink():
            raise ExperimentIndexError(
                f"experiments/{directory.name}: direct child must be a real directory"
            )

    for directory in sorted(directories, key=experiment_sort_key):
        hypothesis = _retained_artifact(root, directory / "HYPOTHESIS.md")
        result = _retained_artifact(root, directory / "RESULT.md")
        records.append((directory.name, hypothesis, result))
    return records


def read_index(root: Path = ROOT) -> str:
    """Read the canonical index only through real mode-100644 repository paths."""

    docs = root / "docs"
    _require_real_directory(docs, "docs/")
    index = docs / "EXPERIMENT_INDEX.md"
    try:
        metadata = index.lstat()
    except OSError as error:
        raise ExperimentIndexError(
            "docs/EXPERIMENT_INDEX.md: index is absent"
        ) from error
    if (
        not stat.S_ISREG(metadata.st_mode)
        or index.is_symlink()
        or stat.S_IMODE(metadata.st_mode) != 0o644
    ):
        raise ExperimentIndexError(
            "docs/EXPERIMENT_INDEX.md: index must be a regular non-symlink "
            "mode-100644 file"
        )
    tracked_mode = _tracked_git_mode(root, "docs/EXPERIMENT_INDEX.md")
    if tracked_mode is not None and tracked_mode != "100644":
        raise ExperimentIndexError(
            "docs/EXPERIMENT_INDEX.md: index Git mode must be 100644"
        )
    return index.read_text(encoding="utf-8")


def build_index(root: Path = ROOT) -> str:
    lines = [
        "# Telos experiment index",
        "",
        "This is a deterministic discoverability index over retained top-level",
        "directories under `experiments/`. It is not the current operational baton,",
        "a scientific summary, or evidence that a hypothesis passed. Read each linked",
        "hypothesis and result with its recorded status, limitations, and successors.",
        "",
        "Current authority remains [`mission/current.json`](../mission/current.json).",
        "",
        "## Retained records",
        "",
    ]
    for name, has_hypothesis, has_result in experiment_records(root):
        artifacts = []
        if has_hypothesis:
            artifacts.append(f"[hypothesis](../experiments/{name}/HYPOTHESIS.md)")
        if has_result:
            artifacts.append(f"[result](../experiments/{name}/RESULT.md)")
        record_state = (
            "hypothesis and result retained"
            if has_hypothesis and has_result
            else "hypothesis only; no top-level result retained"
            if has_hypothesis
            else "result only; no top-level hypothesis retained"
            if has_result
            else "directory retained; no top-level hypothesis or result retained"
        )
        artifact_text = ", ".join(artifacts) if artifacts else "none"
        lines.append(
            f"- [`{name}`](../experiments/{name}/) — record state: "
            f"{record_state}; artifacts: "
            + artifact_text
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        expected = build_index()
    except ExperimentIndexError as error:
        print(f"experiment index unsafe: {error}")
        return 1
    if args.write:
        try:
            _require_real_directory(INDEX.parent, "docs/")
            if INDEX.exists() or INDEX.is_symlink():
                read_index()
        except ExperimentIndexError as error:
            print(f"experiment index unsafe: {error}")
            return 1
        INDEX.write_text(expected, encoding="utf-8")
        print(f"wrote {INDEX.relative_to(ROOT)}")
        return 0
    try:
        actual = read_index()
    except ExperimentIndexError as error:
        print(f"experiment index unsafe: {error}")
        return 1
    if actual != expected:
        print(f"experiment index differs: {INDEX.relative_to(ROOT)}")
        return 1
    print(
        "experiment index: "
        f"{len(experiment_records())} retained top-level directories indexed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
