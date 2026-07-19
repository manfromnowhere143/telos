#!/usr/bin/env python3
"""Validate Telos's append-only retrospective seal registry.

The registry protects current paths from a named Git reference forward.  It
does not reinterpret a retrospective snapshot as authorship, chronology, or
scientific truth.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "mission/seal_registry.json"
sys.path.insert(0, str(ROOT))
SCHEMA_VERSION = "telos.seal-registry.v1"
MERGED_ITER237_BASELINE = "7307e0c1c4083443698cfde8f0ab20a27518717c"
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")
PROSPECTIVE_EXPERIMENT_PATH_PATTERN = re.compile(
    r"experiments/[a-z0-9][a-z0-9_-]*"
)
REGULAR_GIT_MODES = {"100644", "100755"}
SUCCESSOR_TRANSITION_TYPES = {
    "retrospective_path_snapshot",
    "successor_path_snapshot",
    "prospective_successor_authorization",
}


class SealRegistryError(ValueError):
    """Raised when a seal record or protected byte set is invalid."""


@dataclass(frozen=True)
class GitBlob:
    """One regular file in a registered Git snapshot."""

    path: str
    mode: str
    object_id: str
    byte_count: int
    sha256: str


@dataclass(frozen=True)
class GitChange:
    """One path transition between two committed Git trees."""

    old_mode: str
    new_mode: str
    old_object_id: str
    new_object_id: str
    status: str
    path: str


@dataclass(frozen=True)
class AdditiveWindow:
    """The committed interval in which one absent tree may receive new blobs."""

    path: str
    authorization_id: str
    start_commit: str | None
    end_commit: str | None


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SealRegistryError(message)


def _git(
    root: Path,
    *arguments: str,
    input_bytes: bytes | None = None,
    timeout: int = 60,
) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            ["git", *arguments],
            cwd=root,
            input=input_bytes,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise SealRegistryError(f"git command failed: {' '.join(arguments)}") from exc


def _git_checked(root: Path, *arguments: str) -> bytes:
    result = _git(root, *arguments)
    if result.returncode != 0:
        diagnostic = (result.stderr or result.stdout).decode("utf-8", errors="replace").strip()
        raise SealRegistryError(
            f"git command failed: {' '.join(arguments)}"
            + (f": {diagnostic}" if diagnostic else "")
        )
    return result.stdout


def _duplicate_rejecting_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SealRegistryError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_json_bytes(raw: bytes, *, label: str, require_canonical: bool = True) -> dict[str, Any]:
    try:
        document = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_duplicate_rejecting_object,
            parse_constant=lambda value: (_ for _ in ()).throw(
                SealRegistryError(f"non-finite JSON value in {label}: {value}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SealRegistryError(f"cannot parse canonical JSON: {label}") from exc
    _require(isinstance(document, dict), f"JSON root is not an object: {label}")
    if require_canonical:
        rendered = json.dumps(document, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        _require(raw == rendered.encode("utf-8"), f"non-canonical JSON bytes: {label}")
    return document


def _canonical_record(record: dict[str, Any]) -> bytes:
    return json.dumps(
        record,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _canonical_path(value: object, *, field: str) -> str:
    _require(isinstance(value, str) and bool(value), f"{field} must be a non-empty string")
    assert isinstance(value, str)
    _require("\\" not in value, f"{field} must use POSIX separators: {value}")
    _require(
        not any(ord(character) < 32 or ord(character) == 127 for character in value),
        f"{field} contains a control character",
    )
    path = PurePosixPath(value)
    _require(
        not path.is_absolute()
        and value == path.as_posix()
        and all(part not in {"", ".", ".."} for part in path.parts),
        f"{field} is not a canonical relative path: {value}",
    )
    return value


def _require_real_parent_directories(
    root: Path,
    relative_path: str,
    *,
    label: str,
) -> None:
    """Reject symlink or non-directory traversal below the repository boundary."""

    current = root
    for part in PurePosixPath(relative_path).parts[:-1]:
        current = current / part
        try:
            metadata = current.lstat()
        except OSError as exc:
            raise SealRegistryError(
                f"{label} parent directory cannot be inspected: {current}"
            ) from exc
        _require(
            stat.S_ISDIR(metadata.st_mode) and not current.is_symlink(),
            f"{label} parent component is not a real directory: {current}",
        )


def _prospective_experiment_path(value: object, *, field: str) -> str:
    path = _canonical_path(value, field=field)
    _require(
        PROSPECTIVE_EXPERIMENT_PATH_PATTERN.fullmatch(path) is not None,
        f"{field} must name one literal direct child of experiments",
    )
    return path


def _exact_keys(document: dict[str, Any], expected: set[str], *, label: str) -> None:
    missing = sorted(expected - set(document))
    unexpected = sorted(set(document) - expected)
    _require(not missing, f"{label} missing fields: {', '.join(missing)}")
    _require(not unexpected, f"{label} has unexpected fields: {', '.join(unexpected)}")


def _selector_paths(selector: dict[str, Any], *, label: str) -> tuple[str, tuple[str, ...]]:
    _require(isinstance(selector, dict), f"{label} selector must be an object")
    kind = selector.get("kind")
    if kind == "tree":
        _exact_keys(selector, {"kind", "path"}, label=f"{label} selector")
        return kind, (_canonical_path(selector["path"], field=f"{label}.path"),)
    if kind == "path_list":
        _exact_keys(selector, {"kind", "paths"}, label=f"{label} selector")
        paths = selector["paths"]
        _require(isinstance(paths, list) and bool(paths), f"{label}.paths must be non-empty")
        canonical = tuple(
            _canonical_path(path, field=f"{label}.paths") for path in paths
        )
        _require(list(canonical) == sorted(canonical), f"{label}.paths must be sorted")
        _require(len(canonical) == len(set(canonical)), f"{label}.paths contains duplicates")
        return kind, canonical
    raise SealRegistryError(f"{label} selector kind is invalid: {kind}")


def _parse_tree_listing(raw: bytes, *, label: str) -> list[tuple[str, str, str]]:
    entries: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for raw_record in raw.split(b"\0"):
        if not raw_record:
            continue
        try:
            metadata, raw_path = raw_record.split(b"\t", 1)
            mode, object_type, object_id = metadata.decode("ascii").split()
            path = raw_path.decode("utf-8")
        except (UnicodeDecodeError, ValueError) as exc:
            raise SealRegistryError(f"malformed or non-UTF-8 Git tree entry: {label}") from exc
        _canonical_path(path, field=f"{label} Git path")
        _require(path not in seen, f"duplicate Git path in {label}: {path}")
        seen.add(path)
        _require(
            object_type == "blob" and mode in REGULAR_GIT_MODES,
            f"{label} contains a symlink, submodule, or non-regular Git entry: {path}",
        )
        entries.append((path, mode, object_id))
    return sorted(entries)


def _parse_raw_diff(raw: bytes, *, label: str) -> list[GitChange]:
    fields = raw.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    _require(
        len(fields) % 2 == 0,
        f"malformed NUL-delimited Git transition: {label}",
    )
    changes: list[GitChange] = []
    for offset in range(0, len(fields), 2):
        try:
            metadata = fields[offset].decode("ascii").split()
            path = fields[offset + 1].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise SealRegistryError(
                f"non-UTF-8 Git transition entry: {label}"
            ) from exc
        _require(
            len(metadata) == 5 and metadata[0].startswith(":"),
            f"malformed Git transition metadata: {label}",
        )
        old_mode = metadata[0][1:]
        new_mode = metadata[1]
        old_object_id = metadata[2]
        new_object_id = metadata[3]
        status = metadata[4]
        _require(
            len(status) == 1,
            f"rename or copy detection was not disabled: {label}",
        )
        _canonical_path(path, field=f"{label} path")
        changes.append(
            GitChange(
                old_mode,
                new_mode,
                old_object_id,
                new_object_id,
                status,
                path,
            )
        )
    return changes


def _batch_blob_identities(
    root: Path,
    entries: list[tuple[str, str, str]],
) -> dict[str, tuple[int, str]]:
    object_ids = sorted({object_id for _, _, object_id in entries})
    if not object_ids:
        return {}
    request = b"".join(object_id.encode("ascii") + b"\n" for object_id in object_ids)
    response = _git(root, "cat-file", "--batch", input_bytes=request, timeout=120)
    if response.returncode != 0:
        diagnostic = response.stderr.decode("utf-8", errors="replace").strip()
        raise SealRegistryError(f"cannot read protected Git blobs: {diagnostic}")

    identities: dict[str, tuple[int, str]] = {}
    cursor = 0
    for expected_object in object_ids:
        newline = response.stdout.find(b"\n", cursor)
        _require(newline >= 0, "truncated git cat-file batch header")
        header = response.stdout[cursor:newline].decode("ascii", errors="strict").split()
        _require(len(header) == 3, "malformed git cat-file batch header")
        object_id, object_type, encoded_size = header
        _require(object_id == expected_object, "git cat-file returned objects out of order")
        _require(object_type == "blob", f"protected object is not a blob: {object_id}")
        try:
            byte_count = int(encoded_size)
        except ValueError as exc:
            raise SealRegistryError("git cat-file returned a malformed byte count") from exc
        start = newline + 1
        end = start + byte_count
        _require(
            end < len(response.stdout) and response.stdout[end : end + 1] == b"\n",
            f"truncated git cat-file blob: {object_id}",
        )
        payload = response.stdout[start:end]
        identities[object_id] = (byte_count, hashlib.sha256(payload).hexdigest())
        cursor = end + 1
    _require(cursor == len(response.stdout), "git cat-file returned unexpected trailing bytes")
    return identities


def build_manifest(
    root: Path,
    reference_commit: str,
    selector: dict[str, Any],
    *,
    label: str = "protected set",
) -> tuple[int, str, dict[str, GitBlob]]:
    """Rebuild the canonical SHA-256 manifest for one registered selector."""

    kind, paths = _selector_paths(selector, label=label)
    listing = _git_checked(
        root,
        "ls-tree",
        "-r",
        "-z",
        "--full-tree",
        reference_commit,
        "--",
        *paths,
    )
    entries = _parse_tree_listing(listing, label=label)
    if kind == "path_list":
        _require(
            {path for path, _, _ in entries} == set(paths),
            f"{label} path list is absent or resolves more than exact files",
        )
    identities = _batch_blob_identities(root, entries)

    manifest = hashlib.sha256()
    blobs: dict[str, GitBlob] = {}
    for path, mode, object_id in entries:
        byte_count, digest = identities[object_id]
        manifest.update(
            path.encode("utf-8")
            + b"\0"
            + mode.encode("ascii")
            + b"\0"
            + str(byte_count).encode("ascii")
            + b"\0"
            + digest.encode("ascii")
            + b"\n"
        )
        blobs[path] = GitBlob(path, mode, object_id, byte_count, digest)
    return len(blobs), manifest.hexdigest(), blobs


def _require_git_regular_100644(
    root: Path,
    commit: str,
    relative_path: str,
    *,
    label: str,
) -> None:
    listing = _git_checked(
        root,
        "ls-tree",
        "-r",
        "-z",
        "--full-tree",
        commit,
        "--",
        f":(literal){relative_path}",
    )
    entries = _parse_tree_listing(listing, label=label)
    _require(
        len(entries) == 1 and entries[0][0] == relative_path,
        f"{label} is absent or is not one exact regular Git blob",
    )
    _require(
        entries[0][1] == "100644",
        f"{label} Git mode must be 100644",
    )


def _parse_index(
    root: Path,
    paths: tuple[str, ...],
    *,
    label: str,
) -> dict[str, tuple[str, str]]:
    raw = _git_checked(root, "ls-files", "--stage", "-z", "--", *paths)
    result: dict[str, tuple[str, str]] = {}
    for raw_record in raw.split(b"\0"):
        if not raw_record:
            continue
        try:
            metadata, raw_path = raw_record.split(b"\t", 1)
            mode, object_id, stage = metadata.decode("ascii").split()
            path = raw_path.decode("utf-8")
        except (UnicodeDecodeError, ValueError) as exc:
            raise SealRegistryError(f"malformed Git index entry: {label}") from exc
        _canonical_path(path, field=f"{label} index path")
        _require(stage == "0", f"{label} contains a conflicted index entry: {path}")
        _require(path not in result, f"{label} contains duplicate index entries: {path}")
        _require(
            mode in REGULAR_GIT_MODES,
            f"{label} index contains a symlink, submodule, or non-regular entry: {path}",
        )
        result[path] = (mode, object_id)
    return result


def _validate_current_registry_mode(root: Path, registry_path: Path) -> bytes:
    try:
        relative = registry_path.relative_to(root).as_posix()
    except ValueError as exc:
        raise SealRegistryError("seal registry is outside repository root") from exc
    _canonical_path(relative, field="seal registry path")
    _require_real_parent_directories(root, relative, label="seal registry")
    try:
        metadata = registry_path.lstat()
    except OSError as exc:
        raise SealRegistryError("seal registry cannot be inspected") from exc
    _require(
        stat.S_ISREG(metadata.st_mode) and not registry_path.is_symlink(),
        "seal registry worktree path must be a regular file",
    )
    worktree_mode = "100755" if metadata.st_mode & 0o111 else "100644"
    _require(
        worktree_mode == "100644",
        "seal registry worktree mode must be 100644",
    )
    index = _parse_index(root, (relative,), label="seal registry")
    _require(
        set(index) == {relative},
        "seal registry must be one tracked index path",
    )
    _require(
        index[relative][0] == "100644",
        "seal registry index mode must be 100644",
    )
    try:
        raw = registry_path.read_bytes()
    except OSError as exc:
        raise SealRegistryError("seal registry cannot be read") from exc
    hashed = _git(root, "hash-object", "--stdin", input_bytes=raw)
    _require(hashed.returncode == 0, "seal registry worktree bytes cannot be hashed")
    object_id = hashed.stdout.decode("ascii").strip()
    _require(
        object_id == index[relative][1],
        "seal registry worktree bytes differ from the stage-0 index blob",
    )
    return raw


def _path_is_below(path: str, prefix: str) -> bool:
    path_parts = PurePosixPath(path).parts
    prefix_parts = PurePosixPath(prefix).parts
    return len(path_parts) > len(prefix_parts) and path_parts[: len(prefix_parts)] == prefix_parts


def _addition_is_authorized(path: str, successors: tuple[str, ...]) -> bool:
    return any(_path_is_below(path, successor) for successor in successors)


def _latest_successor_transition(
    records: list[dict[str, Any]],
) -> dict[str, Any] | None:
    return next(
        (
            record
            for record in reversed(records)
            if record.get("record_type") in SUCCESSOR_TRANSITION_TYPES
        ),
        None,
    )


def _ancestry_edges(
    root: Path,
    reference: str,
    *,
    descendant: str = "HEAD",
) -> list[tuple[str, str, tuple[str, ...]]]:
    """Return every parent edge on a reference-to-descendant ancestry path."""

    raw_lines = (
        _git_checked(
            root,
            "rev-list",
            "--reverse",
            "--topo-order",
            "--parents",
            "--ancestry-path",
            f"{reference}..{descendant}",
        )
        .decode("ascii")
        .splitlines()
    )
    parsed: list[tuple[str, tuple[str, ...]]] = []
    nodes = {reference}
    for line in raw_lines:
        fields = line.split()
        _require(bool(fields), "Git returned an empty ancestry record")
        commit = fields[0]
        parents = tuple(fields[1:])
        parsed.append((commit, parents))
        nodes.add(commit)
    edges: list[tuple[str, str, tuple[str, ...]]] = []
    for commit, parents in parsed:
        in_ancestry = tuple(parent for parent in parents if parent in nodes)
        for parent in in_ancestry:
            edges.append(
                (
                    parent,
                    commit,
                    tuple(candidate for candidate in in_ancestry if candidate != parent),
                )
            )
    return edges


def _transition_changes(
    root: Path,
    parent: str,
    child: str,
    paths: tuple[str, ...],
    *,
    label: str,
) -> list[GitChange]:
    raw = _git_checked(
        root,
        "diff-tree",
        "-r",
        "--raw",
        "-z",
        "--no-renames",
        parent,
        child,
        "--",
        *(f":(literal){path}" for path in paths),
    )
    return _parse_raw_diff(raw, label=label)


def _merge_carries_identical_addition(
    root: Path,
    change: GitChange,
    other_parents: tuple[str, ...],
) -> bool:
    """Recognize an existing blob carried through a merge from another parent."""

    if change.status != "A" or not other_parents:
        return False
    for parent in other_parents:
        listing = _git_checked(
            root,
            "ls-tree",
            "-r",
            "-z",
            "--full-tree",
            parent,
            "--",
            f":(literal){change.path}",
        )
        entries = _parse_tree_listing(
            listing,
            label=f"merge parent {parent[:12]}",
        )
        if (
            len(entries) == 1
            and entries[0][0] == change.path
            and entries[0][1] == change.new_mode
            and entries[0][2] == change.new_object_id
        ):
            return True
    return False


def _is_ancestor(
    root: Path,
    ancestor: str,
    descendant: str,
    cache: dict[tuple[str, str], bool],
) -> bool:
    key = (ancestor, descendant)
    if key not in cache:
        cache[key] = (
            _git(root, "merge-base", "--is-ancestor", ancestor, descendant).returncode
            == 0
        )
    return cache[key]


def _window_is_active_for_commit(
    root: Path,
    window: AdditiveWindow,
    commit: str,
    cache: dict[tuple[str, str], bool],
) -> bool:
    start = window.start_commit
    if start is None or not _is_ancestor(root, start, commit, cache):
        return False
    return window.end_commit is None or _is_ancestor(
        root,
        commit,
        window.end_commit,
        cache,
    )


def _verify_transition_history(
    root: Path,
    reference: str,
    protected: dict[str, Any],
    windows: tuple[AdditiveWindow, ...],
) -> None:
    """Reject even transient violations retained anywhere in descendant history."""

    set_id = str(protected.get("set_id", "protected set"))
    policy = protected["policy"]
    _, selector_paths = _selector_paths(protected["selector"], label=set_id)
    relevant_windows = tuple(
        window
        for window in windows
        if any(_path_is_below(window.path, path) for path in selector_paths)
    )
    ancestry_cache: dict[tuple[str, str], bool] = {}
    for parent, child, other_parents in _ancestry_edges(root, reference):
        changes = _transition_changes(
            root,
            parent,
            child,
            selector_paths,
            label=f"{set_id} {parent[:12]}..{child[:12]}",
        )
        for change in changes:
            if _merge_carries_identical_addition(root, change, other_parents):
                continue
            if policy != "existing_tree_immutable_registered_additions":
                raise SealRegistryError(
                    f"{set_id} protected history changed at "
                    f"{parent[:12]}..{child[:12]}: {change.status} {change.path}"
                )
            matching = [
                window
                for window in relevant_windows
                if _path_is_below(change.path, window.path)
            ]
            _require(
                len(matching) <= 1,
                f"{set_id} history matches overlapping additive authorizations: "
                f"{change.path}",
            )
            _require(
                len(matching) == 1
                and _window_is_active_for_commit(
                    root,
                    matching[0],
                    child,
                    ancestry_cache,
                ),
                f"{set_id} protected history contains an unauthorized transition at "
                f"{parent[:12]}..{child[:12]}: {change.status} {change.path}",
            )
            window = matching[0]
            _require(
                change.status == "A"
                and change.old_mode == "000000"
                and change.new_mode in REGULAR_GIT_MODES,
                f"{set_id} authorization {window.authorization_id} is additions-only; "
                f"history contains {change.status} {change.path} at "
                f"{parent[:12]}..{child[:12]}",
            )


def _verify_open_window_worktree(
    root: Path,
    window: AdditiveWindow,
) -> None:
    """Keep every committed blob immutable while admitting only brand-new files."""

    if window.start_commit is None or window.end_commit is not None:
        return
    _require(
        _git(root, "merge-base", "--is-ancestor", window.start_commit, "HEAD").returncode
        == 0,
        f"open authorization introduction is not an ancestor of HEAD: "
        f"{window.authorization_id}",
    )
    selector = {"kind": "tree", "path": window.path}
    _, _, head_blobs = build_manifest(
        root,
        "HEAD",
        selector,
        label=f"{window.authorization_id} committed additions",
    )
    index = _parse_index(
        root,
        (window.path,),
        label=f"{window.authorization_id} open authorization",
    )
    for path, blob in head_blobs.items():
        _require(
            path in index,
            f"{window.authorization_id} committed additive path was deleted: {path}",
        )
        mode, object_id = index[path]
        _require(
            mode == blob.mode and object_id == blob.object_id,
            f"{window.authorization_id} committed additive path changed in the index: "
            f"{path}",
        )
        _verify_worktree_file(
            root,
            blob,
            label=f"{window.authorization_id} committed addition",
        )

    staged_additions = sorted(set(index) - set(head_blobs))
    if staged_additions:
        entries = [
            (path, index[path][0], index[path][1])
            for path in staged_additions
        ]
        identities = _batch_blob_identities(root, entries)
        for path, mode, object_id in entries:
            byte_count, digest = identities[object_id]
            _verify_worktree_file(
                root,
                GitBlob(path, mode, object_id, byte_count, digest),
                label=f"{window.authorization_id} staged addition",
            )


def _verify_worktree_file(root: Path, blob: GitBlob, *, label: str) -> None:
    path = root / blob.path
    _require_real_parent_directories(root, blob.path, label=label)
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise SealRegistryError(f"{label} protected file is missing: {blob.path}") from exc
    _require(
        stat.S_ISREG(metadata.st_mode) and not path.is_symlink(),
        f"{label} protected path is not a regular file: {blob.path}",
    )
    current_mode = "100755" if metadata.st_mode & 0o111 else "100644"
    _require(current_mode == blob.mode, f"{label} protected mode changed: {blob.path}")
    digest = hashlib.sha256()
    byte_count = 0
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                byte_count += len(chunk)
                digest.update(chunk)
    except OSError as exc:
        raise SealRegistryError(f"{label} protected file cannot be read: {blob.path}") from exc
    _require(
        byte_count == blob.byte_count and digest.hexdigest() == blob.sha256,
        f"{label} protected bytes changed: {blob.path}",
    )


def _verify_untracked_additions(
    root: Path,
    paths: tuple[str, ...],
    successors: tuple[str, ...],
    *,
    label: str,
) -> None:
    raw = _git_checked(
        root,
        "ls-files",
        "--others",
        "--exclude-standard",
        "-z",
        "--",
        *paths,
    )
    for encoded in raw.split(b"\0"):
        if not encoded:
            continue
        try:
            path = encoded.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise SealRegistryError(f"{label} contains a non-UTF-8 untracked path") from exc
        _canonical_path(path, field=f"{label} untracked path")
        _require(
            _addition_is_authorized(path, successors),
            f"{label} contains an unauthorized untracked addition: {path}",
        )
        target = root / path
        _require_real_parent_directories(root, path, label=label)
        metadata = target.lstat()
        _require(
            stat.S_ISREG(metadata.st_mode) and not target.is_symlink(),
            f"{label} additive successor is not a regular file: {path}",
        )


def _verify_protected_set(
    root: Path,
    reference_commit: str,
    protected: dict[str, Any],
    successors: tuple[str, ...],
) -> int:
    _exact_keys(
        protected,
        {"set_id", "selector", "policy", "blob_count", "manifest_sha256"},
        label="protected set",
    )
    set_id = protected["set_id"]
    _require(isinstance(set_id, str) and bool(set_id), "protected set_id must be non-empty")
    policy = protected["policy"]
    _require(
        policy
        in {
            "existing_tree_immutable_registered_additions",
            "exact_tree",
            "exact_paths",
        },
        f"protected set policy is invalid: {set_id}",
    )
    kind, paths = _selector_paths(protected["selector"], label=str(set_id))
    if policy in {"existing_tree_immutable_registered_additions", "exact_tree"}:
        _require(kind == "tree", f"{set_id} tree policy requires a tree selector")
    if policy == "exact_paths":
        _require(kind == "path_list", f"{set_id} exact_paths requires a path_list selector")
    _require(
        isinstance(protected["blob_count"], int)
        and not isinstance(protected["blob_count"], bool)
        and protected["blob_count"] >= 1,
        f"{set_id} blob_count must be a positive integer",
    )
    _require(
        isinstance(protected["manifest_sha256"], str)
        and SHA256_PATTERN.fullmatch(protected["manifest_sha256"]) is not None,
        f"{set_id} manifest_sha256 is invalid",
    )

    count, digest, reference = build_manifest(
        root,
        reference_commit,
        protected["selector"],
        label=str(set_id),
    )
    _require(count == protected["blob_count"], f"{set_id} protected blob count differs")
    _require(digest == protected["manifest_sha256"], f"{set_id} protected manifest differs")

    index = _parse_index(root, paths, label=str(set_id))
    for path, blob in reference.items():
        _require(path in index, f"{set_id} protected index path is missing: {path}")
        mode, object_id = index[path]
        _require(mode == blob.mode, f"{set_id} protected index mode changed: {path}")
        _require(
            object_id == blob.object_id,
            f"{set_id} protected index bytes changed: {path}",
        )
        _verify_worktree_file(root, blob, label=str(set_id))

    extras = sorted(set(index) - set(reference))
    if kind == "tree":
        admitted = successors if policy == "existing_tree_immutable_registered_additions" else ()
        for path in extras:
            _require(
                _addition_is_authorized(path, admitted),
                f"{set_id} contains an unauthorized tracked addition: {path}",
            )
            _require(
                index[path][0] in REGULAR_GIT_MODES,
                f"{set_id} additive successor has an invalid Git mode: {path}",
            )
            target = root / path
            _require_real_parent_directories(root, path, label=set_id)
            metadata = target.lstat()
            _require(
                stat.S_ISREG(metadata.st_mode) and not target.is_symlink(),
                f"{set_id} additive successor is not a regular file: {path}",
            )
        _verify_untracked_additions(root, paths, admitted, label=str(set_id))
    else:
        _require(not extras, f"{set_id} exact path set contains additions")
        _verify_untracked_additions(root, paths, (), label=str(set_id))
    return count


def _validate_successors(
    root: Path,
    reference_commit: str,
    value: object,
    protected_sets: list[dict[str, Any]],
) -> tuple[str, ...]:
    _require(isinstance(value, list), "allowed_additive_successors must be an array")
    successors: list[str] = []
    for index, item in enumerate(value):
        _require(isinstance(item, dict), f"successor[{index}] must be an object")
        _exact_keys(
            item,
            {"path", "must_be_absent_at_reference", "policy"},
            label=f"successor[{index}]",
        )
        path = _canonical_path(item["path"], field=f"successor[{index}].path")
        _require(
            item["must_be_absent_at_reference"] is True,
            f"successor[{index}] must require absence at reference",
        )
        _require(
            item["policy"] == "additions_only_until_successor_seal",
            f"successor[{index}] policy differs",
        )
        present = _git(root, "cat-file", "-e", f"{reference_commit}:{path}")
        _require(
            present.returncode != 0,
            f"additive successor already exists at reference: {path}",
        )
        successors.append(path)
    _require(successors == sorted(successors), "additive successors must be sorted")
    _require(len(successors) == len(set(successors)), "duplicate additive successor path")
    for outer_index, outer in enumerate(successors):
        for inner in successors[outer_index + 1 :]:
            _require(
                not _path_is_below(inner, outer) and not _path_is_below(outer, inner),
                f"ambiguous overlapping successor paths: {outer}, {inner}",
            )

    admitting_trees: list[str] = []
    for protected in protected_sets:
        if protected.get("policy") != "existing_tree_immutable_registered_additions":
            continue
        kind, paths = _selector_paths(
            protected["selector"],
            label=str(protected.get("set_id", "protected set")),
        )
        if kind == "tree":
            admitting_trees.extend(paths)
    for successor in successors:
        _require(
            any(_path_is_below(successor, tree) for tree in admitting_trees),
            f"successor is not below a registered additive tree: {successor}",
        )
    return tuple(successors)


def _validate_snapshot_record(
    root: Path,
    record: dict[str, Any],
    *,
    enforce_project_baseline: bool,
    prospective_successors: tuple[str, ...] = (),
) -> int:
    _exact_keys(
        record,
        {
            "seal_id",
            "record_type",
            "reference_commit",
            "protected_sets",
            "allowed_additive_successors",
            "limitations",
        },
        label="snapshot record",
    )
    reference = record["reference_commit"]
    _require(
        isinstance(reference, str) and COMMIT_PATTERN.fullmatch(reference) is not None,
        "snapshot reference_commit is invalid",
    )
    if enforce_project_baseline:
        _require(
            reference == MERGED_ITER237_BASELINE,
            "first retrospective snapshot does not name merged iter237 master",
        )
    _require(
        _git(root, "merge-base", "--is-ancestor", reference, "HEAD").returncode == 0,
        f"snapshot reference is not an ancestor of HEAD: {reference}",
    )
    protected_sets = record["protected_sets"]
    _require(
        isinstance(protected_sets, list) and bool(protected_sets),
        "snapshot protected_sets must be non-empty",
    )
    _require(
        all(isinstance(item, dict) for item in protected_sets),
        "snapshot protected_sets entries must be objects",
    )
    set_ids = [item.get("set_id") for item in protected_sets]
    _require(len(set_ids) == len(set(set_ids)), "snapshot contains duplicate protected set IDs")
    successors = _validate_successors(
        root,
        reference,
        record["allowed_additive_successors"],
        protected_sets,
    )
    admitting_trees: list[str] = []
    for protected in protected_sets:
        if protected.get("policy") != "existing_tree_immutable_registered_additions":
            continue
        kind, paths = _selector_paths(
            protected["selector"],
            label=str(protected.get("set_id", "protected set")),
        )
        if kind == "tree":
            admitting_trees.extend(paths)
    for successor in prospective_successors:
        _require(
            any(_path_is_below(successor, tree) for tree in admitting_trees),
            f"prospective successor is not below a registered additive tree: {successor}",
        )
    admitted_successors = successors + prospective_successors
    _require(
        len(admitted_successors) == len(set(admitted_successors)),
        "duplicate additive successor path across baseline and prospective records",
    )
    for outer_index, outer in enumerate(admitted_successors):
        for inner in admitted_successors[outer_index + 1 :]:
            _require(
                not _path_is_below(inner, outer) and not _path_is_below(outer, inner),
                f"ambiguous overlapping successor paths: {outer}, {inner}",
            )
    limitations = record["limitations"]
    _require(
        isinstance(limitations, list)
        and len(limitations) >= 2
        and all(isinstance(item, str) and item.strip() for item in limitations),
        "snapshot limitations must contain explicit non-empty limitations",
    )
    return sum(
        _verify_protected_set(root, reference, protected, admitted_successors)
        for protected in protected_sets
    )


def _validate_successor_snapshot_record(
    root: Path,
    record: dict[str, Any],
    earlier_records: list[dict[str, Any]],
    registry_path: Path,
) -> int:
    """Freeze a previously authorized additive prefix at a later source commit."""

    _exact_keys(
        record,
        {
            "seal_id",
            "record_type",
            "predecessor_seal_id",
            "reference_commit",
            "protected_sets",
            "limitations",
        },
        label="successor snapshot record",
    )
    predecessor_id = record["predecessor_seal_id"]
    predecessors = [
        candidate
        for candidate in earlier_records
        if candidate.get("seal_id") == predecessor_id
        and candidate.get("record_type")
        in {
            "retrospective_path_snapshot",
            "prospective_successor_authorization",
        }
    ]
    _require(
        len(predecessors) == 1,
        f"successor snapshot predecessor is absent or cannot authorize a path: {predecessor_id}",
    )
    predecessor = predecessors[0]
    previous_transition = _latest_successor_transition(earlier_records)
    _require(
        previous_transition is predecessor,
        "successor snapshot must close the latest open path authorization",
    )
    if predecessor["record_type"] == "retrospective_path_snapshot":
        authorized_paths = {
            item["path"] for item in predecessor["allowed_additive_successors"]
        }
    else:
        authorized_paths = {predecessor["authorized_path"]}

    reference = record["reference_commit"]
    _require(
        isinstance(reference, str) and COMMIT_PATTERN.fullmatch(reference) is not None,
        "successor snapshot reference_commit is invalid",
    )
    _require(
        _git(root, "merge-base", "--is-ancestor", reference, "HEAD").returncode == 0,
        f"successor snapshot reference is not an ancestor of HEAD: {reference}",
    )
    if predecessor["record_type"] == "retrospective_path_snapshot":
        _require(
            _git(
                root,
                "merge-base",
                "--is-ancestor",
                predecessor["reference_commit"],
                reference,
            ).returncode
            == 0,
            "successor snapshot reference predates its authorization baseline",
        )
    else:
        authorization_introduction = _validate_registry_only_introduction(
            root,
            registry_path,
            predecessor,
            subject="prospective authorization",
        )
        _require(
            authorization_introduction is not None,
            "successor snapshot cannot close an uncommitted prospective authorization",
        )
        _require(
            _git(
                root,
                "merge-base",
                "--is-ancestor",
                authorization_introduction,
                reference,
            ).returncode
            == 0,
            "successor snapshot reference predates its prospective authorization",
        )

    protected_sets = record["protected_sets"]
    _require(
        isinstance(protected_sets, list) and bool(protected_sets),
        "successor snapshot protected_sets must be non-empty",
    )
    _require(
        all(isinstance(item, dict) for item in protected_sets),
        "successor snapshot protected_sets entries must be objects",
    )
    set_ids = [item.get("set_id") for item in protected_sets]
    _require(
        len(set_ids) == len(set(set_ids)),
        "successor snapshot contains duplicate protected set IDs",
    )
    selected_paths: set[str] = set()
    for protected in protected_sets:
        _require(
            protected.get("policy") == "exact_tree",
            "successor snapshot may contain exact_tree protected sets only",
        )
        kind, paths = _selector_paths(
            protected.get("selector"),
            label=str(protected.get("set_id", "successor protected set")),
        )
        _require(kind == "tree" and len(paths) == 1, "successor snapshot requires tree selectors")
        selected_paths.add(paths[0])
    _require(
        selected_paths and selected_paths <= authorized_paths,
        "successor snapshot protects a path not authorized by its predecessor",
    )
    if predecessor["record_type"] == "prospective_successor_authorization":
        _require(
            len(protected_sets) == 1 and selected_paths == authorized_paths,
            "prospective authorization requires one exact-tree successor seal",
        )
    for selected_path in sorted(selected_paths):
        for record_name in ("HYPOTHESIS.md", "RESULT.md"):
            _require_git_regular_100644(
                root,
                reference,
                f"{selected_path}/{record_name}",
                label=(
                    "completed successor "
                    f"{selected_path}/{record_name}"
                ),
            )

    limitations = record["limitations"]
    _require(
        isinstance(limitations, list)
        and len(limitations) >= 2
        and all(isinstance(item, str) and item.strip() for item in limitations),
        "successor snapshot limitations must contain explicit non-empty limitations",
    )
    _validate_successor_introduction(root, registry_path, record)
    return sum(
        _verify_protected_set(root, reference, protected, ())
        for protected in protected_sets
    )


def _validate_registry_only_introduction(
    root: Path,
    registry_path: Path,
    record: dict[str, Any],
    *,
    subject: str,
) -> str | None:
    """Bind a transition record to its exact one-file, direct-child commit."""

    try:
        relative = registry_path.relative_to(root).as_posix()
    except ValueError as exc:
        raise SealRegistryError("seal registry is outside repository root") from exc
    seal_id = record["seal_id"]
    expected_record = _canonical_record(record)
    commits = reversed(
        _git_checked(
            root,
            "log",
            "--full-history",
            "--topo-order",
            "--format=%H",
            "--",
            relative,
        )
        .decode("ascii")
        .split()
    )
    introducing_commit: str | None = None
    for commit in commits:
        blob = _git_checked(root, "show", f"{commit}:{relative}")
        document = _load_json_bytes(blob, label=f"{commit[:12]}:{relative}")
        records = document.get("records")
        _require(
            isinstance(records, list),
            f"historical registry records invalid: {commit}",
        )
        matching_ids = [
            candidate
            for candidate in records
            if isinstance(candidate, dict) and candidate.get("seal_id") == seal_id
        ]
        _require(
            len(matching_ids) <= 1,
            f"historical registry duplicates {subject} ID: {seal_id}",
        )
        if not matching_ids:
            continue
        _require(
            _canonical_record(matching_ids[0]) == expected_record,
            f"{subject} record differs at its introducing history: {seal_id}",
        )
        _require_git_regular_100644(
            root,
            commit,
            relative,
            label=f"{subject} introducing registry",
        )
        introducing_commit = commit
        break

    reference = record["reference_commit"]
    _require_git_regular_100644(
        root,
        reference,
        relative,
        label=f"{subject} reference registry",
    )
    if introducing_commit is None:
        head = _git_checked(root, "rev-parse", "HEAD").decode("ascii").strip()
        _require(
            head == reference,
            f"uncommitted {subject} preflight is not at its reference commit",
        )
        tracked_delta = _git_checked(
            root,
            "diff",
            "--name-status",
            "--no-renames",
            reference,
            "--",
        ).decode("utf-8").splitlines()
        _require(
            tracked_delta == [f"M\t{relative}"],
            f"uncommitted {subject} preflight changes more than "
            f"{relative}",
        )
        untracked = [
            path
            for path in _git_checked(
                root,
                "ls-files",
                "--others",
                "--exclude-standard",
            )
            .decode("utf-8")
            .splitlines()
            if path
        ]
        _require(
            not untracked,
            f"uncommitted {subject} preflight contains untracked paths: "
            + ", ".join(untracked),
        )
        return None

    parents = (
        _git_checked(
            root,
            "rev-list",
            "--parents",
            "-n",
            "1",
            introducing_commit,
        )
        .decode("ascii")
        .split()
    )
    _require(
        parents == [introducing_commit, reference],
        f"{subject} introducing commit is not the single-parent direct child "
        f"of its reference: {seal_id}",
    )
    delta = _git_checked(
        root,
        "diff",
        "--name-status",
        "--no-renames",
        reference,
        introducing_commit,
    ).decode("utf-8").splitlines()
    _require(
        delta == [f"M\t{relative}"],
        f"{subject} introducing commit changes more than "
        f"{relative}: {seal_id}",
    )
    return introducing_commit


def _validate_successor_introduction(
    root: Path,
    registry_path: Path,
    record: dict[str, Any],
) -> str | None:
    return _validate_registry_only_introduction(
        root,
        registry_path,
        record,
        subject="successor seal",
    )


def _validate_prospective_authorization_record(
    root: Path,
    record: dict[str, Any],
    earlier_records: list[dict[str, Any]],
    registry_path: Path,
) -> tuple[str, str | None]:
    """Authorize one absent experiment path after a completed successor seal."""

    _exact_keys(
        record,
        {
            "seal_id",
            "record_type",
            "predecessor_seal_id",
            "reference_commit",
            "authorized_path",
            "must_be_absent_at_reference",
            "policy",
            "closure_requirement",
            "limitations",
        },
        label="prospective successor authorization",
    )
    predecessor_id = record["predecessor_seal_id"]
    _require(
        isinstance(predecessor_id, str) and bool(predecessor_id),
        "prospective authorization predecessor_seal_id must be non-empty",
    )
    previous_transition = _latest_successor_transition(earlier_records)
    _require(
        previous_transition is not None
        and previous_transition.get("record_type") == "successor_path_snapshot"
        and previous_transition.get("seal_id") == predecessor_id,
        "prospective authorization must immediately follow and name the latest "
        "completed successor seal",
    )
    assert previous_transition is not None
    _require(
        isinstance(previous_transition.get("reference_commit"), str)
        and COMMIT_PATTERN.fullmatch(previous_transition["reference_commit"]) is not None,
        "prospective authorization predecessor reference_commit is invalid",
    )

    reference = record["reference_commit"]
    _require(
        isinstance(reference, str) and COMMIT_PATTERN.fullmatch(reference) is not None,
        "prospective authorization reference_commit is invalid",
    )
    _require(
        _git(root, "merge-base", "--is-ancestor", reference, "HEAD").returncode == 0,
        f"prospective authorization reference is not an ancestor of HEAD: {reference}",
    )
    path = _prospective_experiment_path(
        record["authorized_path"],
        field="prospective authorization authorized_path",
    )
    _require(
        record["must_be_absent_at_reference"] is True,
        "prospective authorization must require absence at reference",
    )
    _require(
        record["policy"] == "additions_only_until_successor_seal",
        "prospective authorization policy differs",
    )
    _require(
        record["closure_requirement"] == "exact_tree_successor_path_snapshot",
        "prospective authorization closure requirement differs",
    )
    _require(
        _git(root, "cat-file", "-e", f"{reference}:{path}").returncode != 0,
        f"prospective authorization is retroactive; path exists at reference: {path}",
    )
    earlier_paths = {
        candidate.get("authorized_path")
        for candidate in earlier_records
        if candidate.get("record_type") == "prospective_successor_authorization"
    }
    _require(
        path not in earlier_paths,
        f"prospective authorization reuses a previously authorized path: {path}",
    )

    predecessor_introduction = _validate_successor_introduction(
        root,
        registry_path,
        previous_transition,
    )
    authorization_introduction = _validate_registry_only_introduction(
        root,
        registry_path,
        record,
        subject="prospective authorization",
    )
    predecessor_is_prior = (
        predecessor_introduction is not None
        and _git(
            root,
            "merge-base",
            "--is-ancestor",
            predecessor_introduction,
            reference,
        ).returncode
        == 0
    )
    _require(
        predecessor_introduction == authorization_introduction
        or predecessor_is_prior,
        "prospective authorization predates its completed predecessor seal",
    )

    if authorization_introduction is None:
        target = root / path
        try:
            target.lstat()
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise SealRegistryError(
                f"prospective authorization path cannot be inspected: {path}"
            ) from exc
        else:
            raise SealRegistryError(
                f"prospective authorization is retroactive; worktree path exists: {path}"
            )

    limitations = record["limitations"]
    _require(
        isinstance(limitations, list)
        and len(limitations) >= 2
        and all(isinstance(item, str) and item.strip() for item in limitations),
        "prospective authorization limitations must contain explicit non-empty limitations",
    )
    return path, authorization_introduction


def _validate_historical_seal_record(root: Path, record: dict[str, Any]) -> None:
    _exact_keys(
        record,
        {
            "seal_id",
            "record_type",
            "source_commit",
            "source_parents",
            "seal_commit",
            "seal_parents",
            "seal_delta",
            "receipt_path",
        },
        label="historical source/seal record",
    )
    source = record["source_commit"]
    seal = record["seal_commit"]
    for field, value in (("source_commit", source), ("seal_commit", seal)):
        _require(
            isinstance(value, str) and COMMIT_PATTERN.fullmatch(value) is not None,
            f"historical {field} is invalid",
        )
        _require(
            _git(root, "merge-base", "--is-ancestor", value, "HEAD").returncode == 0,
            f"historical {field} is not an ancestor of HEAD: {value}",
        )

    for field, commit in (("source_parents", source), ("seal_parents", seal)):
        expected = record[field]
        _require(
            isinstance(expected, list)
            and bool(expected)
            and all(
                isinstance(parent, str) and COMMIT_PATTERN.fullmatch(parent) is not None
                for parent in expected
            ),
            f"historical {field} is invalid",
        )
        actual = _git_checked(root, "rev-list", "--parents", "-n", "1", commit).decode().split()
        _require(actual == [commit, *expected], f"historical {field} topology differs: {commit}")

    delta = record["seal_delta"]
    _require(
        isinstance(delta, list)
        and bool(delta)
        and all(
            isinstance(item, dict) and set(item) == {"status", "path"} for item in delta
        ),
        "historical seal_delta is invalid",
    )
    expected_delta = []
    for index, item in enumerate(delta):
        status_code = item["status"]
        _require(status_code in {"A", "M"}, f"seal_delta[{index}] status is invalid")
        path = _canonical_path(item["path"], field=f"seal_delta[{index}].path")
        expected_delta.append(f"{status_code}\t{path}")
    actual_delta = _git_checked(
        root,
        "diff",
        "--name-status",
        "--no-renames",
        source,
        seal,
    ).decode("utf-8").splitlines()
    _require(actual_delta == expected_delta, f"historical seal delta differs: {seal}")

    receipt_path = record["receipt_path"]
    if receipt_path is not None:
        path = _canonical_path(receipt_path, field="historical receipt_path")
        from scripts.receipt_sealing import (  # noqa: PLC0415
            ReceiptSealingError,
            verify_against_source,
        )

        try:
            receipt_source, _ = verify_against_source(root, root / path)
        except ReceiptSealingError as exc:
            raise SealRegistryError(f"historical receipt does not verify: {path}: {exc}") from exc
        _require(
            receipt_source == source,
            f"historical receipt source differs: {path}",
        )


def _validate_append_only_history(
    root: Path,
    registry_path: Path,
    current: dict[str, Any],
) -> None:
    try:
        relative = registry_path.relative_to(root).as_posix()
    except ValueError as exc:
        raise SealRegistryError("seal registry is outside repository root") from exc
    history = _git_checked(
        root,
        "log",
        "--full-history",
        "--topo-order",
        "--format=%H",
        "--",
        relative,
    ).decode("ascii").split()
    current_records = current["records"]
    for commit in history:
        _require_git_regular_100644(
            root,
            commit,
            relative,
            label=f"historical seal registry at {commit[:12]}",
        )
        blob = _git_checked(root, "show", f"{commit}:{relative}")
        historical = _load_json_bytes(blob, label=f"{commit[:12]}:{relative}")
        _require(
            historical.get("schema_version") == current["schema_version"],
            f"registry schema changed after {commit[:12]}",
        )
        _require(
            historical.get("claim_boundary") == current["claim_boundary"],
            f"registry claim boundary changed after {commit[:12]}",
        )
        old_records = historical.get("records")
        _require(isinstance(old_records, list), f"historical registry records invalid: {commit}")
        _require(
            len(old_records) <= len(current_records),
            f"registry records were removed after {commit[:12]}",
        )
        for index, old_record in enumerate(old_records):
            _require(
                isinstance(old_record, dict)
                and _canonical_record(old_record) == _canonical_record(current_records[index]),
                f"registry record {index} was rewritten or reordered after {commit[:12]}",
            )


def _build_additive_windows(
    records: list[dict[str, Any]],
    prospective_introductions: dict[str, str | None],
) -> tuple[AdditiveWindow, ...]:
    baseline = records[0]
    windows: dict[tuple[str, str], AdditiveWindow] = {}
    baseline_id = baseline["seal_id"]
    for successor in baseline["allowed_additive_successors"]:
        path = successor["path"]
        windows[(baseline_id, path)] = AdditiveWindow(
            path=path,
            authorization_id=baseline_id,
            start_commit=baseline["reference_commit"],
            end_commit=None,
        )
    for record in records:
        if record.get("record_type") != "prospective_successor_authorization":
            continue
        path = record["authorized_path"]
        seal_id = record["seal_id"]
        windows[(seal_id, path)] = AdditiveWindow(
            path=path,
            authorization_id=seal_id,
            start_commit=prospective_introductions[seal_id],
            end_commit=None,
        )

    for record in records:
        if record.get("record_type") != "successor_path_snapshot":
            continue
        predecessor_id = record["predecessor_seal_id"]
        selected_paths = {
            protected["selector"]["path"] for protected in record["protected_sets"]
        }
        for path in selected_paths:
            key = (predecessor_id, path)
            _require(
                key in windows,
                f"successor seal has no matching additive history window: "
                f"{predecessor_id} {path}",
            )
            previous = windows[key]
            _require(
                previous.end_commit is None,
                f"additive history window was closed more than once: "
                f"{predecessor_id} {path}",
            )
            windows[key] = AdditiveWindow(
                path=previous.path,
                authorization_id=previous.authorization_id,
                start_commit=previous.start_commit,
                end_commit=record["reference_commit"],
            )
    return tuple(windows.values())


def _validate_transition_history(
    root: Path,
    records: list[dict[str, Any]],
    prospective_introductions: dict[str, str | None],
) -> None:
    windows = _build_additive_windows(records, prospective_introductions)
    baseline = records[0]
    for protected in baseline["protected_sets"]:
        _verify_transition_history(
            root,
            baseline["reference_commit"],
            protected,
            windows,
        )
    for record in records:
        if record.get("record_type") != "successor_path_snapshot":
            continue
        for protected in record["protected_sets"]:
            _verify_transition_history(
                root,
                record["reference_commit"],
                protected,
                (),
            )
    for window in windows:
        _verify_open_window_worktree(root, window)


def validate(
    root: Path = ROOT,
    registry_path: Path | None = None,
    *,
    enforce_project_baseline: bool = True,
    check_history: bool = True,
) -> list[str]:
    """Return seal-registry failures without mutating any repository artifact."""

    path = registry_path or root / "mission/seal_registry.json"
    try:
        raw = _validate_current_registry_mode(root, path)
        document = _load_json_bytes(raw, label=str(path))
        _exact_keys(
            document,
            {"schema_version", "claim_boundary", "records"},
            label="seal registry",
        )
        _require(document["schema_version"] == SCHEMA_VERSION, "seal registry schema differs")
        _require(
            isinstance(document["claim_boundary"], str)
            and "byte" in document["claim_boundary"].lower()
            and "truth" in document["claim_boundary"].lower(),
            "seal registry claim boundary omits digest limitations",
        )
        records = document["records"]
        _require(isinstance(records, list) and bool(records), "seal registry records are empty")
        _require(
            all(isinstance(record, dict) for record in records),
            "seal registry records must be objects",
        )
        seal_ids = [record.get("seal_id") for record in records]
        _require(
            all(isinstance(seal_id, str) and seal_id for seal_id in seal_ids),
            "every seal record requires a non-empty seal_id",
        )
        _require(len(seal_ids) == len(set(seal_ids)), "duplicate seal_id")
        _require(
            records[0].get("record_type") == "retrospective_path_snapshot",
            "first seal record must be the retrospective path snapshot",
        )
        _require(
            records[0].get("seal_id") == "iter237-merged-historical-baseline"
            if enforce_project_baseline
            else True,
            "first seal ID differs from the registered iter237 baseline",
        )

        prospective_results = [
            (
                record,
                _validate_prospective_authorization_record(
                    root,
                    record,
                    records[:index],
                    path,
                ),
            )
            for index, record in enumerate(records)
            if record.get("record_type") == "prospective_successor_authorization"
        ]
        prospective_successors = tuple(result[0] for _, result in prospective_results)
        prospective_introductions = {
            record["seal_id"]: result[1]
            for record, result in prospective_results
        }
        for index, record in enumerate(records):
            record_type = record.get("record_type")
            if record_type == "retrospective_path_snapshot":
                _require(index == 0, "only the first record may be retrospective")
                _validate_snapshot_record(
                    root,
                    record,
                    enforce_project_baseline=enforce_project_baseline,
                    prospective_successors=prospective_successors,
                )
            elif record_type == "successor_path_snapshot":
                _validate_successor_snapshot_record(
                    root,
                    record,
                    records[:index],
                    path,
                )
            elif record_type == "prospective_successor_authorization":
                continue
            elif record_type == "historical_source_seal":
                _validate_historical_seal_record(root, record)
            else:
                raise SealRegistryError(f"unknown seal record type: {record_type}")
        _validate_transition_history(
            root,
            records,
            prospective_introductions,
        )
        if check_history:
            _validate_append_only_history(root, path, document)
    except (OSError, SealRegistryError) as exc:
        return [str(exc)]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    failures = validate()
    if failures:
        print("seal registry guard failed:", file=sys.stderr)
        for failure in failures:
            print(f" - {failure}", file=sys.stderr)
        return 1
    print(
        "seal registry guard: retrospective baseline and historical Git topology pass; "
        "committed transition history and exact registered additive windows pass"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
