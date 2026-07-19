#!/usr/bin/env python3
"""Index retained top-level directories under Telos's experiments/ tree."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import stat
import subprocess


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs/EXPERIMENT_INDEX.md"
ITERATION_NAME = re.compile(r"^iter(\d+)(?:_|$)")
SAFE_DIRECTORY_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
GIT_OBJECT_ID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
GIT_MODE = re.compile(r"^[0-7]{6}$")


class ExperimentIndexError(ValueError):
    """Raised when a retained experiment path is not safe to index."""


def experiment_sort_key(path: Path) -> tuple[int, int, bytes]:
    match = ITERATION_NAME.match(path.name)
    if match is None:
        return (1, 0, path.name.encode("utf-8"))
    return (0, int(match.group(1)), path.name.encode("utf-8"))


def _git(
    root: Path,
    *arguments: str,
    input_bytes: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    """Run a local-only Git query without ambient Git or credential state."""

    environment = {
        key: os.environ[key]
        for key in ("PATH", "SYSTEMROOT", "TEMP", "TMP", "TMPDIR")
        if key in os.environ
    }
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "LC_ALL": "C",
        }
    )
    try:
        return subprocess.run(
            [
                "git",
                "-c",
                "credential.helper=",
                "-c",
                "credential.interactive=never",
                "-c",
                "core.hooksPath=/dev/null",
                "-c",
                "core.fsmonitor=false",
                "-C",
                str(root),
                *arguments,
            ],
            capture_output=True,
            check=False,
            env=environment,
            input=input_bytes,
            stdin=subprocess.DEVNULL if input_bytes is None else None,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ExperimentIndexError("local Git inspection failed") from error


def _repository_has_head(root: Path) -> bool:
    repository = _git(root, "rev-parse", "--is-inside-work-tree")
    if repository.returncode != 0 or repository.stdout != b"true\n":
        return False
    head = _git(root, "rev-parse", "--verify", "--quiet", "HEAD^{commit}")
    return head.returncode == 0


def _nul_delimited_entries(
    payload: bytes,
    *,
    relative: str,
    source: str,
) -> list[bytes]:
    if not payload:
        return []
    if not payload.endswith(b"\0"):
        raise ExperimentIndexError(
            f"{relative}: malformed non-NUL-terminated {source} output"
        )
    entries = payload[:-1].split(b"\0")
    if any(not entry for entry in entries):
        raise ExperimentIndexError(
            f"{relative}: malformed empty {source} entry"
        )
    return entries


def _parse_head_entry(
    entry: bytes,
    *,
    requested: set[str],
) -> tuple[str, str, str]:
    try:
        metadata, observed = entry.split(b"\t", 1)
        fields = metadata.split(b" ")
        if len(fields) != 3:
            raise ValueError("unexpected HEAD metadata field count")
        mode = fields[0].decode("ascii")
        object_type = fields[1].decode("ascii")
        object_id = fields[2].decode("ascii")
        observed_path = observed.decode("utf-8")
    except (UnicodeDecodeError, ValueError) as error:
        raise ExperimentIndexError(
            "committed HEAD: malformed or non-UTF-8 entry"
        ) from error
    if observed_path not in requested:
        raise ExperimentIndexError(
            f"{observed_path}: committed HEAD returned an unexpected literal path"
        )
    if GIT_MODE.fullmatch(mode) is None:
        raise ExperimentIndexError(
            f"{observed_path}: malformed committed HEAD mode"
        )
    if GIT_OBJECT_ID.fullmatch(object_id) is None:
        raise ExperimentIndexError(
            f"{observed_path}: malformed committed HEAD object identifier"
        )
    if object_type != "blob":
        raise ExperimentIndexError(
            f"{observed_path}: committed HEAD entry must be a blob"
        )
    return observed_path, mode, object_id


def _head_entries(
    root: Path,
    relatives: list[str],
) -> dict[str, tuple[str, str]]:
    if not relatives:
        return {}
    result = _git(
        root,
        "ls-tree",
        "-z",
        "--full-tree",
        "HEAD",
        "--",
        *(f":(literal){relative}" for relative in relatives),
    )
    if result.returncode != 0:
        if not _repository_has_head(root):
            return {}
        raise ExperimentIndexError(
            f"{relatives[0]}: could not inspect committed HEAD entries"
        )
    requested = set(relatives)
    if len(requested) != len(relatives):
        raise ExperimentIndexError("duplicate committed HEAD path request")
    raw_entries = _nul_delimited_entries(
        result.stdout,
        relative=relatives[0],
        source="committed HEAD",
    )
    entries: dict[str, tuple[str, str]] = {}
    for raw_entry in raw_entries:
        observed_path, mode, object_id = _parse_head_entry(
            raw_entry,
            requested=requested,
        )
        if observed_path in entries:
            raise ExperimentIndexError(
                f"{observed_path}: ambiguous committed HEAD entry"
            )
        entries[observed_path] = (mode, object_id)
    return entries


def _head_entry(root: Path, relative: str) -> tuple[str, str] | None:
    return _head_entries(root, [relative]).get(relative)


def _parse_index_entry(
    entry: bytes,
    *,
    requested: set[str],
) -> tuple[str, str, str, str]:
    try:
        metadata, observed = entry.split(b"\t", 1)
        fields = metadata.split(b" ")
        if len(fields) != 3:
            raise ValueError("unexpected index metadata field count")
        mode = fields[0].decode("ascii")
        object_id = fields[1].decode("ascii")
        stage = fields[2].decode("ascii")
        observed_path = observed.decode("utf-8")
    except (UnicodeDecodeError, ValueError) as error:
        raise ExperimentIndexError(
            "Git index: malformed or non-UTF-8 entry"
        ) from error
    if observed_path not in requested:
        raise ExperimentIndexError(
            f"{observed_path}: Git index returned an unexpected literal path"
        )
    if GIT_MODE.fullmatch(mode) is None:
        raise ExperimentIndexError(
            f"{observed_path}: malformed Git index mode"
        )
    if GIT_OBJECT_ID.fullmatch(object_id) is None:
        raise ExperimentIndexError(
            f"{observed_path}: malformed Git index object identifier"
        )
    if stage not in {"0", "1", "2", "3"}:
        raise ExperimentIndexError(
            f"{observed_path}: malformed Git index stage"
        )
    return observed_path, mode, object_id, stage


def _raw_index_entries(
    root: Path,
    relatives: list[str],
) -> dict[str, list[tuple[str, str, str]]]:
    if not relatives:
        return {}
    result = _git(
        root,
        "ls-files",
        "--stage",
        "-z",
        "--",
        *(f":(literal){relative}" for relative in relatives),
    )
    if result.returncode != 0:
        raise ExperimentIndexError(
            f"{relatives[0]}: could not inspect Git index entries"
        )
    requested = set(relatives)
    if len(requested) != len(relatives):
        raise ExperimentIndexError("duplicate Git index path request")
    raw_entries = _nul_delimited_entries(
        result.stdout,
        relative=relatives[0],
        source="Git index",
    )
    entries: dict[str, list[tuple[str, str, str]]] = {}
    for raw_entry in raw_entries:
        observed_path, mode, object_id, stage = _parse_index_entry(
            raw_entry,
            requested=requested,
        )
        entries.setdefault(observed_path, []).append((mode, object_id, stage))
    return entries


def _require_stage_zero_index_entry(
    relative: str,
    entries: list[tuple[str, str, str]] | None,
) -> tuple[str, str]:
    if not entries:
        raise ExperimentIndexError(
            f"{relative}: committed HEAD record is missing from the Git index"
        )
    if len(entries) != 1:
        raise ExperimentIndexError(
            f"{relative}: ambiguous or conflicted Git index entries"
        )
    mode, object_id, stage = entries[0]
    if stage != "0":
        raise ExperimentIndexError(
            f"{relative}: Git index entry is unmerged at stage {stage}"
        )
    return mode, object_id


def _index_entry(root: Path, relative: str) -> tuple[str, str]:
    entries = _raw_index_entries(root, [relative])
    return _require_stage_zero_index_entry(relative, entries.get(relative))


def _committed_blobs(root: Path, object_ids: list[str]) -> dict[str, bytes]:
    unique_ids = list(dict.fromkeys(object_ids))
    if not unique_ids:
        return {}
    query = "".join(f"{object_id}\n" for object_id in unique_ids).encode("ascii")
    result = _git(root, "cat-file", "--batch", input_bytes=query)
    if result.returncode != 0:
        raise ExperimentIndexError("could not read committed HEAD blobs")
    blobs: dict[str, bytes] = {}
    cursor = 0
    for expected in unique_ids:
        newline = result.stdout.find(b"\n", cursor)
        if newline < 0:
            raise ExperimentIndexError("truncated Git cat-file batch header")
        fields = result.stdout[cursor:newline].split(b" ")
        try:
            observed, object_type, raw_size = fields
            size = int(raw_size)
        except (TypeError, ValueError) as error:
            raise ExperimentIndexError(
                "malformed Git cat-file batch header"
            ) from error
        if observed != expected.encode("ascii") or object_type != b"blob" or size < 0:
            raise ExperimentIndexError("unexpected Git cat-file batch object")
        start = newline + 1
        end = start + size
        if end >= len(result.stdout) or result.stdout[end : end + 1] != b"\n":
            raise ExperimentIndexError("truncated Git cat-file batch blob")
        blobs[expected] = result.stdout[start:end]
        cursor = end + 1
    if cursor != len(result.stdout):
        raise ExperimentIndexError("unexpected trailing Git cat-file batch bytes")
    return blobs


def _worktree_bytes(path: Path, relative: str, label: str) -> bytes | None:
    try:
        before = path.lstat()
    except FileNotFoundError:
        return None
    except OSError as error:
        raise ExperimentIndexError(
            f"{relative}: could not inspect {label}"
        ) from error
    if (
        not stat.S_ISREG(before.st_mode)
        or path.is_symlink()
        or stat.S_IMODE(before.st_mode) != 0o644
    ):
        raise ExperimentIndexError(
            f"{relative}: {label} must be a regular non-symlink mode-100644 file"
        )
    try:
        payload = path.read_bytes()
        after = path.lstat()
    except OSError as error:
        raise ExperimentIndexError(f"{relative}: could not read {label}") from error
    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_size,
        before.st_mtime_ns,
    )
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_size,
        after.st_mtime_ns,
    )
    if identity_after != identity_before or not stat.S_ISREG(after.st_mode):
        raise ExperimentIndexError(
            f"{relative}: {label} changed while it was inspected"
        )
    return payload


def _committed_clean_files(
    root: Path,
    paths: list[Path],
    *,
    label: str,
    allow_uncommitted: bool,
) -> dict[str, bytes]:
    relatives = [path.relative_to(root).as_posix() for path in paths]
    if len(set(relatives)) != len(relatives):
        raise ExperimentIndexError(f"duplicate {label} path request")
    worktrees = {
        relative: _worktree_bytes(path, relative, label)
        for path, relative in zip(paths, relatives, strict=True)
    }
    head_entries = _head_entries(root, relatives)

    committed_relatives: list[str] = []
    for relative in relatives:
        head_entry = head_entries.get(relative)
        if head_entry is None:
            if not allow_uncommitted:
                if worktrees[relative] is None:
                    raise ExperimentIndexError(
                        f"{relative}: {label} is absent and is not committed in HEAD"
                    )
                raise ExperimentIndexError(
                    f"{relative}: {label} is not committed in HEAD"
                )
            continue
        head_mode, _ = head_entry
        if head_mode != "100644":
            raise ExperimentIndexError(
                f"{relative}: committed HEAD mode must be 100644, "
                f"observed {head_mode}"
            )
        if worktrees[relative] is None:
            raise ExperimentIndexError(
                f"{relative}: committed HEAD record is absent from the worktree"
            )
        committed_relatives.append(relative)

    raw_index_entries = _raw_index_entries(root, committed_relatives)
    head_objects: list[str] = []
    for relative in committed_relatives:
        index_mode, index_object = _require_stage_zero_index_entry(
            relative,
            raw_index_entries.get(relative),
        )
        if index_mode != "100644":
            raise ExperimentIndexError(
                f"{relative}: Git index mode must be 100644, "
                f"observed {index_mode}"
            )
        head_object = head_entries[relative][1]
        if index_object != head_object:
            raise ExperimentIndexError(
                f"{relative}: Git index object differs from committed HEAD blob"
            )
        head_objects.append(head_object)

    committed_blobs = _committed_blobs(root, head_objects)
    retained: dict[str, bytes] = {}
    for relative in committed_relatives:
        head_object = head_entries[relative][1]
        payload = worktrees[relative]
        if payload is None:  # pragma: no cover - rejected above
            raise ExperimentIndexError(
                f"{relative}: committed HEAD record is absent from the worktree"
            )
        if payload != committed_blobs[head_object]:
            raise ExperimentIndexError(
                f"{relative}: worktree bytes differ from committed HEAD blob"
            )
        retained[relative] = payload
    return retained


def _retained_artifact(root: Path, path: Path) -> bool:
    relative = path.relative_to(root).as_posix()
    return relative in _committed_clean_files(
        root,
        [path],
        label="retained record",
        allow_uncommitted=True,
    )


def _retained_artifacts(root: Path, paths: list[Path]) -> list[bool]:
    retained = _committed_clean_files(
        root,
        paths,
        label="retained record",
        allow_uncommitted=True,
    )
    return [path.relative_to(root).as_posix() in retained for path in paths]


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

    sorted_directories = sorted(directories, key=experiment_sort_key)
    artifact_paths = [
        path
        for directory in sorted_directories
        for path in (directory / "HYPOTHESIS.md", directory / "RESULT.md")
    ]
    retained = iter(_retained_artifacts(root, artifact_paths))
    for directory in sorted_directories:
        hypothesis = next(retained)
        result = next(retained)
        records.append((directory.name, hypothesis, result))
    return records


def read_index(root: Path = ROOT) -> str:
    """Read the canonical index only when it is clean and committed in HEAD."""

    docs = root / "docs"
    _require_real_directory(docs, "docs/")
    index = docs / "EXPERIMENT_INDEX.md"
    relative = index.relative_to(root).as_posix()
    retained = _committed_clean_files(
        root,
        [index],
        label="index",
        allow_uncommitted=False,
    )
    payload = retained[relative]
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ExperimentIndexError(
            "docs/EXPERIMENT_INDEX.md: committed index is not UTF-8"
        ) from error


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
