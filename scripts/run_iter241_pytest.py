#!/usr/bin/env python3
"""Authenticate iter241 routing inputs, qualify once, then run one fixed pytest command."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
import types
from typing import Any, Iterator
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = "scripts/run_iter241_pytest.py"
ROUTER_PATH = "scripts/route_iter241_pytest.py"
PYPROJECT_PATH = "pyproject.toml"
TESTS_PATH = "tests"
TRUSTED_GIT = Path("/usr/bin/git")
COMMIT_ID = re.compile(r"^[0-9a-f]{40}$")
SAFE_COMPONENT = re.compile(r"^[^\x00-\x1f\x7f]+$")
MAX_SNAPSHOT_FILES = 20_000
MAX_SNAPSHOT_BYTES = 1_073_741_824
MAX_GIT_STORAGE_FILES = 50_000
MAX_GIT_STORAGE_BYTES = 2_147_483_648
MAX_PRIVATE_FILES = MAX_SNAPSHOT_FILES + MAX_GIT_STORAGE_FILES
MAX_PRIVATE_BYTES = MAX_SNAPSHOT_BYTES + MAX_GIT_STORAGE_BYTES
TIMEOUT_CANDIDATES = (
    Path("/usr/bin/timeout"),
    Path("/bin/timeout"),
    Path("/opt/homebrew/bin/timeout"),
    Path("/usr/local/bin/timeout"),
)
ROUTER_SHA256 = "231a35a79572db39fd3bcbf00ac7d36373e519f23f853a5f88a411d20f7a1fc5"
AUTHENTICATED_SOURCES = {
    "scripts/validate_seal_registry.py": (
        "c8b393f1adbb1960cead14a9da198baae02d62c7ec65413b58fd0dec8cc5ed4d"
    ),
    "scripts/receipt_sealing.py": (
        "7bd9c7184d37e6d20841e95d96bc352ce2b8198d210b323a0dee974b4df65afe"
    ),
    "scripts/adjudicate_iter241_repository_closure_correction.py": (
        "7028522587ea53b306f056321ee579c6938610f8c87cb261bb8d5913471ab0ae"
    ),
    PYPROJECT_PATH: ("5f010f66125f117671ba19ad5d3cbecdcfa2ade4ef2daf3b87b49b6bc108654c"),
}


class RunnerError(ValueError):
    """The pre-pytest authentication or fixed-command boundary failed."""


@dataclass(frozen=True)
class SnapshotEntry:
    """One exact regular Git blob expected in the private checkout."""

    path: str
    mode: str
    object_id: str
    size: int


@dataclass(frozen=True)
class MaterializedRepository:
    """A private exact-commit checkout and its verified identities."""

    root: Path
    source_commit: str
    source_tree: str
    tests_tree: str
    entries: tuple[SnapshotEntry, ...]
    byte_count: int


@dataclass(frozen=True)
class PytestPlan:
    """Immutable result produced before the pytest process exists."""

    qualified: bool
    reason: str
    reference_commit: str | None
    source_commit: str
    source_tree: str
    snapshot_root: Path
    argv: tuple[str, ...]
    environment: dict[str, str]


def _committed_source_bytes(root: Path, relative: str, raw: bytes) -> None:
    """Require one authority-bearing source to equal both HEAD and the Git index."""

    head_raw = _run_git(
        ("show", f"HEAD:{relative}"),
        cwd=root,
        reason=f"authenticated source is absent from HEAD: {relative}",
    )
    index_raw = _run_git(
        ("show", f":{relative}"),
        cwd=root,
        reason=f"authenticated source is absent from the Git index: {relative}",
    )
    if head_raw != raw or index_raw != raw:
        raise RunnerError(f"authenticated source differs from HEAD or Git index: {relative}")


def _authenticated_bytes(root: Path, relative: str, expected_digest: str) -> bytes:
    path = root / relative
    try:
        metadata = path.lstat()
        raw = path.read_bytes()
    except OSError as exc:
        raise RunnerError(f"authenticated source unavailable: {relative}") from exc
    if (
        not stat.S_ISREG(metadata.st_mode)
        or path.is_symlink()
        or stat.S_IMODE(metadata.st_mode) != 0o644
        or hashlib.sha256(raw).hexdigest() != expected_digest
    ):
        raise RunnerError(f"authenticated source differs: {relative}")
    _committed_source_bytes(root, relative, raw)
    return raw


def authenticate_before_router_execution(root: Path = ROOT) -> dict[str, bytes]:
    """Freeze router and every delegated source before any of them executes."""

    expected = {ROUTER_PATH: ROUTER_SHA256, **AUTHENTICATED_SOURCES}
    return {
        relative: _authenticated_bytes(root, relative, digest)
        for relative, digest in expected.items()
    }


def _load_authenticated_router(raw: bytes, path: Path) -> types.ModuleType:
    name = "_telos_authenticated_iter241_router"
    sys.modules.pop(name, None)
    module = types.ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = None
    sys.modules[name] = module
    try:
        exec(compile(raw, str(path), "exec"), module.__dict__, module.__dict__)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


def _require_isolated_python() -> None:
    try:
        executable = Path(sys.executable).resolve(strict=True)
        metadata = executable.lstat()
    except OSError as exc:
        raise RunnerError("isolated Python executable is unavailable") from exc
    if not (
        sys.flags.isolated
        and sys.flags.ignore_environment
        and sys.flags.no_user_site
        and executable.is_absolute()
        and stat.S_ISREG(metadata.st_mode)
        and metadata.st_mode & stat.S_IXUSR
        and not metadata.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
    ):
        raise RunnerError("runner requires an isolated Python invocation with -I")


def _python_executable() -> str:
    try:
        return str(Path(sys.executable).resolve(strict=True))
    except OSError as exc:
        raise RunnerError("isolated Python executable is unavailable") from exc


def _require_repository_cwd(root: Path) -> None:
    try:
        current = Path.cwd().resolve(strict=True)
        expected = root.resolve(strict=True)
    except OSError as exc:
        raise RunnerError("repository working directory is unavailable") from exc
    if current != expected:
        raise RunnerError("runner requires the repository root as its working directory")


def _pytest_tool_path() -> str:
    python = Path(_python_executable())
    directories = [python.parent]
    for candidate in TIMEOUT_CANDIDATES:
        try:
            timeout = candidate.resolve(strict=True)
            metadata = timeout.lstat()
        except OSError:
            continue
        if (
            not stat.S_ISREG(metadata.st_mode)
            or not metadata.st_mode & stat.S_IXUSR
            or metadata.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
        ):
            raise RunnerError("trusted timeout executable differs")
        directories.append(timeout.parent)
        break
    directories.extend((Path("/usr/bin"), Path("/bin")))
    return os.pathsep.join(dict.fromkeys(str(directory) for directory in directories))


def _runner_surface(root: Path) -> bytes:
    path = root / RUNNER_PATH
    try:
        expected = path.resolve(strict=True)
        executing = Path(__file__).resolve(strict=True)
        metadata = path.lstat()
        raw = path.read_bytes()
    except OSError as exc:
        raise RunnerError("runner surface is unavailable") from exc
    if (
        expected != path
        or executing != expected
        or path.is_symlink()
        or not stat.S_ISREG(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o644
    ):
        raise RunnerError("runner surface is invalid")
    _committed_source_bytes(root, RUNNER_PATH, raw)
    return raw


def _reauthenticate_runner_surface(root: Path, expected: bytes) -> None:
    if _runner_surface(root) != expected:
        raise RunnerError("runner surface drifted")


def _git_environment() -> dict[str, str]:
    return {
        "GIT_ALLOW_PROTOCOL": "file",
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_LOCAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_CONFIG_WORKTREE": os.devnull,
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_PAGER": "cat",
        "GIT_TERMINAL_PROMPT": "0",
        "LC_ALL": "C",
        "PAGER": "cat",
        "PATH": "/usr/bin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
    }


def _trusted_git_executables() -> Path:
    upload_pack: Path | None = None
    for executable in (TRUSTED_GIT, Path("/usr/bin/git-upload-pack")):
        try:
            path_metadata = executable.lstat()
            parent = executable.parent.resolve(strict=True)
            parent_metadata = parent.lstat()
            resolved = executable.resolve(strict=True)
            metadata = resolved.lstat()
        except OSError as exc:
            raise RunnerError("trusted Git executable is unavailable") from exc
        if (
            not executable.is_absolute()
            or path_metadata.st_uid != 0
            or not (stat.S_ISREG(path_metadata.st_mode) or stat.S_ISLNK(path_metadata.st_mode))
            or (
                stat.S_ISREG(path_metadata.st_mode)
                and path_metadata.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
            )
            or not stat.S_ISDIR(parent_metadata.st_mode)
            or parent_metadata.st_uid != 0
            or parent_metadata.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
            or not resolved.is_absolute()
            or resolved.is_symlink()
            or not stat.S_ISREG(metadata.st_mode)
            or not metadata.st_mode & stat.S_IXUSR
            or metadata.st_uid != 0
            or metadata.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
        ):
            raise RunnerError("trusted Git executable is invalid")
        if executable != TRUSTED_GIT:
            upload_pack = executable
    assert upload_pack is not None
    return upload_pack


def _git_command(arguments: tuple[str, ...]) -> tuple[str, ...]:
    _trusted_git_executables()
    return (
        str(TRUSTED_GIT),
        "--no-pager",
        "-c",
        "credential.helper=",
        "-c",
        "credential.interactive=never",
        "-c",
        "core.hooksPath=/dev/null",
        "-c",
        "core.fsmonitor=false",
        *arguments,
    )


def _run_git(
    arguments: tuple[str, ...],
    *,
    cwd: Path,
    reason: str,
    timeout: int = 180,
) -> bytes:
    command = _git_command(arguments)
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=_git_environment(),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RunnerError(reason) from exc
    if completed.returncode != 0:
        raise RunnerError(reason)
    return completed.stdout


def _snapshot_git(root: Path, *arguments: str, reason: str) -> bytes:
    return _run_git(
        (
            f"--git-dir={root / '.git'}",
            f"--work-tree={root}",
            *arguments,
        ),
        cwd=root,
        reason=reason,
    )


def _canonical_snapshot_path(value: str) -> bool:
    path = PurePosixPath(value)
    return (
        bool(value)
        and len(value.encode("utf-8")) <= 4096
        and SAFE_COMPONENT.fullmatch(value) is not None
        and unicodedata.normalize("NFC", value) == value
        and "\\" not in value
        and not path.is_absolute()
        and path.as_posix() == value
        and all(
            part not in {"", ".", ".."}
            and part.casefold() != ".git"
            and not part.endswith((" ", "."))
            and len(part.encode("utf-8")) <= 255
            for part in path.parts
        )
    )


def _parse_tree_listing(raw: bytes) -> tuple[tuple[SnapshotEntry, ...], int]:
    if raw and not raw.endswith(b"\0"):
        raise RunnerError("snapshot tree listing is malformed")
    entries: list[SnapshotEntry] = []
    seen: set[str] = set()
    folded: set[str] = set()
    byte_count = 0
    for item in raw.split(b"\0"):
        if not item:
            continue
        try:
            metadata, path_raw = item.split(b"\t", 1)
            mode, object_type, object_id, size_raw = metadata.decode("ascii").split()
            relative = path_raw.decode("utf-8")
            size = int(size_raw)
        except (UnicodeDecodeError, ValueError) as exc:
            raise RunnerError("snapshot tree listing is malformed") from exc
        folded_path = relative.casefold()
        if (
            mode not in {"100644", "100755"}
            or object_type != "blob"
            or COMMIT_ID.fullmatch(object_id) is None
            or size < 0
            or not _canonical_snapshot_path(relative)
            or relative in seen
            or folded_path in folded
        ):
            raise RunnerError("snapshot tree contains an unsupported entry")
        seen.add(relative)
        folded.add(folded_path)
        byte_count += size
        if len(entries) >= MAX_SNAPSHOT_FILES or byte_count > MAX_SNAPSHOT_BYTES:
            raise RunnerError("snapshot tree exceeds the materialization bound")
        entries.append(SnapshotEntry(relative, mode, object_id, size))
    if not entries:
        raise RunnerError("snapshot tree is empty")
    return tuple(sorted(entries, key=lambda entry: entry.path)), byte_count


def _bounded_directory_usage(
    root: Path,
    *,
    maximum_files: int,
    maximum_bytes: int,
    require_single_link: bool,
    reason: str,
) -> tuple[int, int]:
    files = 0
    byte_count = 0
    stack = [root]
    try:
        root_metadata = root.lstat()
        if root.is_symlink() or not stat.S_ISDIR(root_metadata.st_mode):
            raise RunnerError(reason)
        while stack:
            directory = stack.pop()
            with os.scandir(directory) as children:
                for child in children:
                    metadata = child.stat(follow_symlinks=False)
                    if stat.S_ISDIR(metadata.st_mode):
                        if child.is_symlink():
                            raise RunnerError(reason)
                        stack.append(Path(child.path))
                        continue
                    if (
                        not stat.S_ISREG(metadata.st_mode)
                        or child.is_symlink()
                        or (require_single_link and metadata.st_nlink != 1)
                    ):
                        raise RunnerError(reason)
                    files += 1
                    byte_count += metadata.st_size
                    if files > maximum_files or byte_count > maximum_bytes:
                        raise RunnerError(reason)
    except OSError as exc:
        raise RunnerError(reason) from exc
    return files, byte_count


def _write_exact_regular(path: Path, raw: bytes) -> None:
    try:
        metadata = path.lstat()
        if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
            raise RunnerError("snapshot Git configuration is invalid")
        descriptor = os.open(
            path,
            os.O_WRONLY | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0),
        )
        with os.fdopen(descriptor, "wb") as destination:
            opened = os.fstat(destination.fileno())
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_nlink != 1
                or opened.st_dev != metadata.st_dev
                or opened.st_ino != metadata.st_ino
            ):
                raise RunnerError("snapshot Git configuration is invalid")
            destination.write(raw)
            destination.flush()
            os.fchmod(destination.fileno(), 0o644)
            os.fsync(destination.fileno())
        observed = path.lstat()
        if (
            path.is_symlink()
            or not stat.S_ISREG(observed.st_mode)
            or stat.S_IMODE(observed.st_mode) != 0o644
            or path.read_bytes() != raw
        ):
            raise RunnerError("snapshot Git configuration is invalid")
    except OSError as exc:
        raise RunnerError("snapshot Git configuration is unavailable") from exc


def _materialize_exact_blobs(root: Path, entries: tuple[SnapshotEntry, ...]) -> None:
    try:
        if any(child.name != ".git" for child in root.iterdir()):
            raise RunnerError("no-checkout clone unexpectedly populated its worktree")
    except OSError as exc:
        raise RunnerError("no-checkout clone worktree is unavailable") from exc

    command = _git_command(
        (
            f"--git-dir={root / '.git'}",
            f"--work-tree={root}",
            "cat-file",
            "--batch",
        )
    )
    try:
        process = subprocess.Popen(
            command,
            cwd=root,
            env=_git_environment(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        raise RunnerError("snapshot blob reader is unavailable") from exc
    assert process.stdin is not None
    assert process.stdout is not None
    try:
        for entry in entries:
            process.stdin.write(f"{entry.object_id}\n".encode("ascii"))
            process.stdin.flush()
            header = process.stdout.readline(256)
            expected_header = f"{entry.object_id} blob {entry.size}\n".encode("ascii")
            if header != expected_header:
                raise RunnerError("snapshot blob header differs from the commit tree")

            destination = root / entry.path
            destination.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
            descriptor = os.open(
                destination,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                0o600,
            )
            digest = hashlib.sha1(usedforsecurity=False)
            digest.update(f"blob {entry.size}\0".encode("ascii"))
            remaining = entry.size
            with os.fdopen(descriptor, "wb") as output:
                while remaining:
                    payload = process.stdout.read(min(1024 * 1024, remaining))
                    if not payload:
                        raise RunnerError("snapshot blob payload ended early")
                    output.write(payload)
                    digest.update(payload)
                    remaining -= len(payload)
                os.fchmod(output.fileno(), 0o644 if entry.mode == "100644" else 0o755)
            if process.stdout.read(1) != b"\n" or digest.hexdigest() != entry.object_id:
                raise RunnerError("snapshot blob payload differs from the commit tree")
        process.stdin.close()
        if process.wait(timeout=180) != 0 or process.stdout.read(1):
            raise RunnerError("snapshot blob reader failed")
    except (OSError, subprocess.SubprocessError) as exc:
        raise RunnerError("snapshot blob materialization failed") from exc
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def _git_blob_identity(path: Path, expected_size: int) -> str:
    try:
        before = path.lstat()
        if (
            path.is_symlink()
            or not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before.st_size != expected_size
        ):
            raise RunnerError("snapshot worktree entry is invalid")
        digest = hashlib.sha1(usedforsecurity=False)
        digest.update(f"blob {expected_size}\0".encode("ascii"))
        observed_size = 0
        with path.open("rb") as source:
            while payload := source.read(1024 * 1024):
                observed_size += len(payload)
                digest.update(payload)
        after = path.lstat()
    except OSError as exc:
        raise RunnerError("snapshot worktree entry is unavailable") from exc
    stable_fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    if observed_size != expected_size or any(
        getattr(before, field) != getattr(after, field) for field in stable_fields
    ):
        raise RunnerError("snapshot worktree entry drifted during verification")
    return digest.hexdigest()


def _verify_worktree(
    root: Path,
    entries: tuple[SnapshotEntry, ...],
    expected_pyproject: bytes,
) -> None:
    expected = {entry.path: entry for entry in entries}
    observed: dict[str, os.stat_result] = {}
    observed_directories: set[str] = set()
    stack = [root]
    try:
        root_metadata = root.lstat()
        if (
            root.is_symlink()
            or not stat.S_ISDIR(root_metadata.st_mode)
            or root_metadata.st_uid != os.geteuid()
            or stat.S_IMODE(root_metadata.st_mode) & (stat.S_IWGRP | stat.S_IWOTH)
        ):
            raise RunnerError("snapshot worktree root is invalid")
        while stack:
            directory = stack.pop()
            with os.scandir(directory) as children:
                for child in children:
                    child_path = Path(child.path)
                    relative = child_path.relative_to(root).as_posix()
                    metadata = child.stat(follow_symlinks=False)
                    if relative == ".git":
                        if child.is_symlink() or not stat.S_ISDIR(metadata.st_mode):
                            raise RunnerError("snapshot Git directory is invalid")
                        continue
                    if stat.S_ISDIR(metadata.st_mode):
                        if (
                            child.is_symlink()
                            or metadata.st_uid != os.geteuid()
                            or stat.S_IMODE(metadata.st_mode) & (stat.S_IWGRP | stat.S_IWOTH)
                        ):
                            raise RunnerError("snapshot worktree directory is invalid")
                        observed_directories.add(relative)
                        stack.append(child_path)
                        continue
                    if (
                        child.is_symlink()
                        or not stat.S_ISREG(metadata.st_mode)
                        or metadata.st_uid != os.geteuid()
                    ):
                        raise RunnerError("snapshot worktree contains a special entry")
                    observed[relative] = metadata
    except OSError as exc:
        raise RunnerError("snapshot worktree is unavailable") from exc
    expected_directories = {
        parent.as_posix()
        for entry in entries
        for parent in PurePosixPath(entry.path).parents
        if parent != PurePosixPath(".")
    }
    if set(observed) != set(expected) or observed_directories != expected_directories:
        raise RunnerError("snapshot worktree path set differs from the commit")
    for relative, entry in expected.items():
        metadata = observed[relative]
        expected_mode = 0o644 if entry.mode == "100644" else 0o755
        if stat.S_IMODE(metadata.st_mode) != expected_mode:
            raise RunnerError("snapshot worktree mode differs from the commit")
        if _git_blob_identity(root / relative, entry.size) != entry.object_id:
            raise RunnerError("snapshot worktree bytes differ from the commit")
    try:
        pyproject = (root / PYPROJECT_PATH).read_bytes()
    except OSError as exc:
        raise RunnerError("snapshot pytest configuration is unavailable") from exc
    if pyproject != expected_pyproject:
        raise RunnerError("snapshot pytest configuration differs from authenticated bytes")


def _verify_snapshot(
    materialized: MaterializedRepository,
    module: types.ModuleType,
    expected_pyproject: bytes,
) -> None:
    root = materialized.root
    try:
        config = (root / ".git/config").read_bytes()
        config_mode = stat.S_IMODE((root / ".git/config").lstat().st_mode)
    except OSError as exc:
        raise RunnerError("snapshot Git configuration is unavailable") from exc
    if config != module.ISOLATED_GIT_CONFIG or config_mode != 0o644:
        raise RunnerError("snapshot Git configuration differs")
    hooks = root / ".git/hooks"
    try:
        if hooks.exists() or hooks.is_symlink():
            if hooks.is_symlink() or not hooks.is_dir() or any(hooks.iterdir()):
                raise RunnerError("snapshot Git hook surface is present")
    except OSError as exc:
        raise RunnerError("snapshot Git hook surface is unavailable") from exc

    try:
        context = module._discover_git_context(root)
        head = (
            module._git_checked(
                context,
                "rev-parse",
                "--verify",
                "HEAD^{commit}",
            )
            .decode("ascii")
            .strip()
        )
        source_tree = module._commit_identity(context, materialized.source_commit)[0]
        tests_tree = module._tree_oid(context, materialized.source_commit, TESTS_PATH)
        listing = module._git_checked(
            context,
            "ls-tree",
            "-r",
            "-z",
            "-l",
            "--full-tree",
            materialized.source_commit,
        )
        staged = module._git(
            context,
            "diff",
            "--cached",
            "--quiet",
            materialized.source_commit,
            "--",
        )
    except (UnicodeDecodeError, ValueError) as exc:
        raise RunnerError("snapshot Git identity verification failed") from exc
    parsed, byte_count = _parse_tree_listing(listing)
    if (
        head != materialized.source_commit
        or source_tree != materialized.source_tree
        or tests_tree != materialized.tests_tree
        or parsed != materialized.entries
        or byte_count != materialized.byte_count
        or staged.returncode != 0
    ):
        raise RunnerError("snapshot Git identity differs")
    _verify_worktree(root, materialized.entries, expected_pyproject)
    _bounded_directory_usage(
        root,
        maximum_files=MAX_PRIVATE_FILES,
        maximum_bytes=MAX_PRIVATE_BYTES,
        require_single_link=True,
        reason="private snapshot exceeds its storage bound",
    )


def _trusted_external_temp_root(root: Path, module: types.ModuleType) -> Path:
    try:
        temporary_root = module.TRUSTED_TEMP_ROOT.resolve(strict=True)
        metadata = temporary_root.lstat()
    except (AttributeError, OSError) as exc:
        raise RunnerError("trusted external temp root is unavailable") from exc
    mode = stat.S_IMODE(metadata.st_mode)
    if (
        not temporary_root.is_absolute()
        or temporary_root != module.TRUSTED_TEMP_ROOT
        or temporary_root.is_symlink()
        or not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != 0
        or (mode & (stat.S_IWGRP | stat.S_IWOTH) and not mode & stat.S_ISVTX)
        or temporary_root == root
        or temporary_root.is_relative_to(root)
    ):
        raise RunnerError("trusted external temp root is invalid")
    try:
        if any(
            child.name.startswith((".iter241-pytest-", "telos-iter241-pytest-"))
            for child in os.scandir(root)
        ):
            raise RunnerError("source worktree contains a snapshot remnant")
    except OSError as exc:
        raise RunnerError("source worktree snapshot-remnant check failed") from exc
    return temporary_root


@contextmanager
def _materialized_repository(
    root: Path,
    module: types.ModuleType,
    source_commit: str,
    expected_pyproject: bytes,
) -> Iterator[MaterializedRepository]:
    if COMMIT_ID.fullmatch(source_commit) is None:
        raise RunnerError("qualified source commit is invalid")
    source = module._discover_git_context(root)
    _bounded_directory_usage(
        source.common_dir / "objects",
        maximum_files=MAX_GIT_STORAGE_FILES,
        maximum_bytes=MAX_GIT_STORAGE_BYTES,
        require_single_link=False,
        reason="source Git object storage exceeds the clone bound",
    )
    temporary_root = _trusted_external_temp_root(root, module)
    with tempfile.TemporaryDirectory(
        prefix="telos-iter241-pytest-",
        dir=temporary_root,
    ) as temporary:
        private_root = Path(temporary).resolve(strict=True)
        metadata = private_root.lstat()
        if (
            private_root.parent != temporary_root
            or private_root == root
            or private_root.is_relative_to(root)
            or root.is_relative_to(private_root)
            or private_root.is_symlink()
            or not stat.S_ISDIR(metadata.st_mode)
            or metadata.st_uid != os.geteuid()
            or stat.S_IMODE(metadata.st_mode) & (stat.S_IRWXG | stat.S_IRWXO)
        ):
            raise RunnerError("private snapshot root is invalid")
        template = private_root / "empty-template"
        template.mkdir(mode=0o700)
        snapshot_root = private_root / "repository"
        with module._frozen_git_view(source) as view:
            if view.source_head != source_commit:
                raise RunnerError("qualified source commit drifted before materialization")
            source_tree = module._commit_identity(view.context, source_commit)[0]
            tests_tree = module._tree_oid(view.context, source_commit, TESTS_PATH)
            listing = module._git_checked(
                view.context,
                "ls-tree",
                "-r",
                "-z",
                "-l",
                "--full-tree",
                source_commit,
            )
            entries, byte_count = _parse_tree_listing(listing)
            upload_pack = _trusted_git_executables()
            _run_git(
                (
                    "-c",
                    "protocol.allow=never",
                    "-c",
                    "protocol.file.allow=always",
                    "clone",
                    "--no-local",
                    "--no-hardlinks",
                    "--no-checkout",
                    "--no-tags",
                    f"--template={template}",
                    f"--upload-pack={upload_pack}",
                    "--",
                    str(view.context.git_dir),
                    str(snapshot_root),
                ),
                cwd=private_root,
                reason="private exact-commit clone failed",
            )
            _bounded_directory_usage(
                snapshot_root / ".git",
                maximum_files=MAX_GIT_STORAGE_FILES,
                maximum_bytes=MAX_GIT_STORAGE_BYTES,
                require_single_link=True,
                reason="private clone exceeds its Git storage bound",
            )
            _write_exact_regular(snapshot_root / ".git/config", module.ISOLATED_GIT_CONFIG)
            _snapshot_git(
                snapshot_root,
                "fsck",
                "--strict",
                "--full",
                "--no-dangling",
                reason="private clone object verification failed",
            )
            _materialize_exact_blobs(snapshot_root, entries)
            _snapshot_git(
                snapshot_root,
                "read-tree",
                "--reset",
                source_commit,
                reason="private exact-commit index materialization failed",
            )
            _write_exact_regular(
                snapshot_root / ".git/HEAD",
                f"{source_commit}\n".encode("ascii"),
            )
            module._reauthenticate_source_git(view)
        materialized = MaterializedRepository(
            root=snapshot_root,
            source_commit=source_commit,
            source_tree=source_tree,
            tests_tree=tests_tree,
            entries=entries,
            byte_count=byte_count,
        )
        _verify_snapshot(materialized, module, expected_pyproject)
        yield materialized


def _verify_fixed_command(
    module: types.ModuleType,
    plan: PytestPlan,
    root: Path,
) -> None:
    base = (
        _python_executable(),
        "-I",
        "-m",
        "pytest",
        "-q",
        "-c",
        str(root / PYPROJECT_PATH),
        f"--confcutdir={root}",
        str(root / TESTS_PATH),
    )
    if plan.argv[: len(base)] != base:
        raise RunnerError("pytest command prefix differs")
    expected_deselections = tuple(
        f"--deselect={nodeid}" for nodeid in module.FROZEN_EXACT_HEAD_NODEIDS
    )
    observed = tuple(plan.argv[len(base) :])
    if observed != (expected_deselections if plan.qualified else ()):
        raise RunnerError("pytest deselection set differs")
    forbidden_environment = {
        "GIT_DIR",
        "GIT_EXEC_PATH",
        "GIT_OBJECT_DIRECTORY",
        "GIT_REPLACE_REF_BASE",
        "PYTHONPATH",
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
    }
    if forbidden_environment & set(plan.environment):
        raise RunnerError("pytest environment retains an authority-bearing override")
    if plan.environment.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") != "1":
        raise RunnerError("pytest plugin autoload is not disabled")
    if plan.environment.get("PATH") != _pytest_tool_path():
        raise RunnerError("pytest tool path differs")
    if not module.no_pytest_plugin_surface(root):
        raise RunnerError("repository pytest plugin surface is present")


@dataclass(frozen=True)
class PreparedPytest:
    """Authenticated state retained while the private snapshot exists."""

    source_root: Path
    runner_bytes: bytes
    authenticated: dict[str, bytes]
    module: types.ModuleType
    materialized: MaterializedRepository
    plan: PytestPlan


def _verify_authenticated_sources(root: Path, expected: dict[str, bytes]) -> None:
    if authenticate_before_router_execution(root) != expected:
        raise RunnerError("authenticated source drifted")


def _verify_prepared_run(prepared: PreparedPytest) -> None:
    plan = prepared.plan
    materialized = prepared.materialized
    if (
        plan.source_commit != materialized.source_commit
        or plan.source_tree != materialized.source_tree
        or plan.snapshot_root != materialized.root
    ):
        raise RunnerError("pytest plan differs from the materialized repository")
    _verify_snapshot(
        materialized,
        prepared.module,
        prepared.authenticated[PYPROJECT_PATH],
    )
    _verify_fixed_command(prepared.module, plan, materialized.root)
    _verify_authenticated_sources(prepared.source_root, prepared.authenticated)
    _reauthenticate_runner_surface(prepared.source_root, prepared.runner_bytes)


@contextmanager
def _prepare_run(root: Path = ROOT) -> Iterator[PreparedPytest]:
    """Authenticate once and retain a verified exact-commit snapshot through pytest."""

    _require_isolated_python()
    _require_repository_cwd(root)
    runner_bytes = _runner_surface(root)
    authenticated = authenticate_before_router_execution(root)
    module = _load_authenticated_router(authenticated[ROUTER_PATH], root / ROUTER_PATH)
    qualification = module.seal_qualification(root)
    if qualification.source_commit is None:
        raise RunnerError("qualification did not bind a source commit")
    _verify_authenticated_sources(root, authenticated)
    _reauthenticate_runner_surface(root, runner_bytes)
    with _materialized_repository(
        root,
        module,
        qualification.source_commit,
        authenticated[PYPROJECT_PATH],
    ) as materialized:
        if qualification.qualified:
            snapshot_qualification = module.seal_qualification(materialized.root)
            if snapshot_qualification != qualification:
                raise RunnerError("private snapshot did not reproduce seal qualification")
            _verify_snapshot(materialized, module, authenticated[PYPROJECT_PATH])
        argv = module.authoritative_pytest_argv(
            qualification,
            python_executable=_python_executable(),
            root=materialized.root,
        )
        environment = module.pytest_environment(
            python_executable=_python_executable(),
        )
        plan = PytestPlan(
            qualified=qualification.qualified,
            reason=qualification.reason,
            reference_commit=qualification.reference_commit,
            source_commit=materialized.source_commit,
            source_tree=materialized.source_tree,
            snapshot_root=materialized.root,
            argv=argv,
            environment=environment,
        )
        prepared = PreparedPytest(
            source_root=root,
            runner_bytes=runner_bytes,
            authenticated=authenticated,
            module=module,
            materialized=materialized,
            plan=plan,
        )
        _verify_prepared_run(prepared)
        yield prepared


@contextmanager
def build_plan(root: Path = ROOT) -> Iterator[PytestPlan]:
    """Yield a verified plan only while its private exact-commit snapshot exists."""

    with _prepare_run(root) as prepared:
        yield prepared.plan


def _render_plan(plan: PytestPlan) -> str:
    document: dict[str, Any] = {
        "argv": list(plan.argv),
        "cwd": str(plan.snapshot_root),
        "ephemeral_snapshot": True,
        "executable_after_runner_exit": False,
        "qualified": plan.qualified,
        "reason": plan.reason,
        "reference_commit": plan.reference_commit,
        "schema_version": "telos.iter241.authenticated_pytest_plan.v2",
        "source_commit": plan.source_commit,
        "source_tree": plan.source_tree,
    }
    return json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--plan", action="store_true")
    action.add_argument("--run", action="store_true")
    args = parser.parse_args()
    try:
        with _prepare_run() as prepared:
            _verify_prepared_run(prepared)
            if args.plan:
                print(_render_plan(prepared.plan), end="")
                return 0
            completed = subprocess.run(
                prepared.plan.argv,
                cwd=prepared.plan.snapshot_root,
                env=prepared.plan.environment,
                check=False,
            )
            return completed.returncode
    except (OSError, RunnerError, RuntimeError, subprocess.SubprocessError, ValueError) as exc:
        print(f"iter241 pytest runner denied: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
