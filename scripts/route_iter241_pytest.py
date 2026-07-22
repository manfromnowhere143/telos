"""Authenticated, fail-closed qualification for iter241's fixed pytest command.

This module is authority-bearing only when its exact bytes are loaded by
``scripts/run_iter241_pytest.py`` after that runner authenticates this module
and both delegated validators.  It is deliberately not a pytest plugin.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
import tokenize
from typing import Any, Iterable, Iterator


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = "mission/seal_registry.json"
ITER241_PATH = "experiments/iter241_iter240_repository_closure"
CORRECTION_RECEIPT_PATH = f"{ITER241_PATH}/proof/iter240_repository_closure_correction.json"
SEAL_VALIDATOR_PATH = "scripts/validate_seal_registry.py"
RECEIPT_SEALING_PATH = "scripts/receipt_sealing.py"
CORRECTION_ADJUDICATOR_PATH = "scripts/adjudicate_iter241_repository_closure_correction.py"
FROZEN_VALIDATOR_PATH = "scripts/validate_iter240_repository_closure.py"
FROZEN_TEST_PATH = "tests/test_iter240_repository_closure.py"
PYPROJECT_PATH = "pyproject.toml"
TESTS_PATH = "tests"

TRUSTED_GIT = Path("/usr/bin/git")
TRUSTED_PATH = "/usr/bin:/bin"
TRUSTED_TEMP_ROOT = Path("/tmp").resolve(strict=True)
TIMEOUT_CANDIDATES = (
    Path("/usr/bin/timeout"),
    Path("/bin/timeout"),
    Path("/opt/homebrew/bin/timeout"),
    Path("/usr/local/bin/timeout"),
)

FROZEN_EXACT_HEAD_NODEIDS = (
    "tests/test_iter240_repository_closure.py::test_local_authorization_and_sealed_iter240_bytes",
    "tests/test_iter240_repository_closure.py::test_retained_capture_validates_when_present",
)

EXPECTED_STATUS_ITEMS = (
    ("all_checks_green", "contradicted"),
    ("attempt", "failed"),
    ("capture_completeness", "failed"),
    ("frozen_validator_acceptance", "invalid"),
    ("independent_ground_truth", "blocked"),
    ("independent_review", "blocked"),
    ("non_required_security_check", "failed"),
    ("repository_closure", "failed"),
    ("required_ci", "supported"),
    ("raw_header_byte_fidelity", "failed"),
    ("retry_authority", "none"),
    ("scientific_authority", "none"),
)

AUTHORIZATION_LIMITATIONS = (
    "This authorizes additions only within one absent iter241 path for retained, "
    "read-only repository-closure evidence about iter240 PR #88; it authorizes no "
    "GitHub write, repository-setting mutation, workflow dispatch or rerun, provider "
    "or model call, human contact, scientific execution, spending, publication, or "
    "release.",
    "Authorization is not completion: a prospectively frozen GET-only capture "
    "contract, armed-before-first-request attempt marker, retained raw responses and "
    "metadata, independent validator, known-bad fixtures, and a later exact-tree "
    "successor seal remain separate requirements.",
    "Required GitHub Actions success must remain distinct from an all-checks-green "
    "claim: the observed non-required GitGuardian failure is unresolved and may not "
    "be omitted, rewritten as success, or treated as security approval.",
    "Remote GitHub state is mutable and time-bounded; repository-closure evidence "
    "establishes no reviewer independence, semantic truth, scientific correctness, "
    "independent ground truth, detector efficacy, transfer, or population claim.",
)

SUCCESSOR_LIMITATIONS = (
    "This snapshot freezes the exact thirty-nine regular Git blobs in the iter241 "
    "component at the named reference commit; byte identity does not establish "
    "authorship, chronology, semantic truth, scientific correctness, independence, "
    "or external timestamp authority.",
    "This record closes only the iter241 additive authorization; it does not repair "
    "capture completeness, raw-header-byte fidelity, or repository closure, and it "
    "does not authorize an iter241 retry.",
    "The retained attempt remains failed: capture_completeness failed because "
    "merge_commit_sha was omitted, raw_header_byte_fidelity failed because exact "
    "response header-section bytes were not retained, required CI is supported, "
    "all-checks-green is contradicted, and the non-required GitGuardian check failed.",
    "Independent review and independent ground truth remain blocked; scientific "
    "authority and retry authority remain none, and no security approval, "
    "publication, release, provider call, repository mutation, or scientific "
    "execution is authorized.",
)

COMMIT_ID = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
READ_ONLY_GIT_SUBCOMMANDS = {
    "cat-file",
    "diff",
    "ls-files",
    "ls-tree",
    "merge-base",
    "rev-parse",
    "show",
}

ISOLATED_GIT_CONFIG = b"""\
[core]
\trepositoryformatversion = 0
\tbare = false
\tfilemode = true
\tlogallrefupdates = false
\tignorecase = false
\tprecomposeunicode = true
\thooksPath = /dev/null
\tfsmonitor = false
[credential]
\thelper =
\tinteractive = never
"""


@dataclass(frozen=True)
class RoutingContract:
    """Every fixed identity required in addition to a future successor reference."""

    authorization_commit: str
    authorization_tree: str
    authorization_parents: tuple[str, ...]
    sealed_iter240_commit: str
    sealed_iter240_parent: str
    sealed_iter240_tree: str
    sealed_iter240_subtree: str
    governed_merge: str
    governed_merge_tree: str
    governed_merge_parents: tuple[str, ...]
    correction_checkpoint: str
    correction_checkpoint_subtree: str
    iter241_subtree: str
    iter241_blob_count: int
    correction_receipt_sha256: str
    correction_adjudicator_sha256: str
    seal_registry_validator_sha256: str
    receipt_sealing_sha256: str
    frozen_validator_sha256: str
    frozen_test_sha256: str
    pyproject_sha256: str
    authorization_seal_id: str
    authorization_predecessor_id: str
    authorization_record_sha256: str
    authorization_limitations: tuple[str, ...]
    successor_seal_id: str
    successor_set_id: str
    successor_limitations: tuple[str, ...]
    successor_limitations_sha256: str


DEFAULT_CONTRACT = RoutingContract(
    authorization_commit="6a9a4f66ec331011c9dfbe14b3a22259a5b585d5",
    authorization_tree="76c6791ec2a051804a50f65b5297b709dea4f49c",
    authorization_parents=(
        "39e2484cba450fe5346349921572720b0e456fb7",
        "ceb8dfbb2ba451e76c71528a8ca5fcc75f5edc31",
    ),
    sealed_iter240_commit="f954696c935ad0b733dcd613b553e1799a7b3810",
    sealed_iter240_parent="a61a005cc7cdc92d72d79c017a650237c3e57faa",
    sealed_iter240_tree="1a6384324dd3e2a15121d981938a0bcee397c904",
    sealed_iter240_subtree="cb03a4bd15d38f1ffb8ba33682502fa59dac26c2",
    governed_merge="39e2484cba450fe5346349921572720b0e456fb7",
    governed_merge_tree="1a6384324dd3e2a15121d981938a0bcee397c904",
    governed_merge_parents=(
        "b597b763f2eb52b2f4f2d36e7daaa31654be076b",
        "f954696c935ad0b733dcd613b553e1799a7b3810",
    ),
    correction_checkpoint="aef48926738c4843fc61db73562729e50ca516a5",
    correction_checkpoint_subtree="75c90ec47db8b657f9926c33be3b8848d6df1052",
    iter241_subtree="5b963e4824ae2b2b7e8ccc0d5cf9fd37c222db10",
    iter241_blob_count=39,
    correction_receipt_sha256=("854523c490ee0eb9807b4ed3da52677edffd148e754bd233ea2cdc09a12231c4"),
    correction_adjudicator_sha256=(
        "7028522587ea53b306f056321ee579c6938610f8c87cb261bb8d5913471ab0ae"
    ),
    seal_registry_validator_sha256=(
        "c8b393f1adbb1960cead14a9da198baae02d62c7ec65413b58fd0dec8cc5ed4d"
    ),
    receipt_sealing_sha256=("7bd9c7184d37e6d20841e95d96bc352ce2b8198d210b323a0dee974b4df65afe"),
    frozen_validator_sha256=("9f54fdacca4ce334d97c60593c585873f07ec968fcffded7d82c19e649cd36ec"),
    frozen_test_sha256=("1b2804edaa05eb049ca6eeca776f6477766b6f86c61e6ad37946c319ea1341a7"),
    pyproject_sha256=("5f010f66125f117671ba19ad5d3cbecdcfa2ade4ef2daf3b87b49b6bc108654c"),
    authorization_seal_id="iter241-iter240-repository-closure-authorization",
    authorization_predecessor_id="iter240-completed-evidence-seal",
    authorization_record_sha256=(
        "32bae1043d722d81baf2b847aee6f82ad074060b0d2f0d458a3e3172b3a8ce61"
    ),
    authorization_limitations=AUTHORIZATION_LIMITATIONS,
    successor_seal_id="iter241-completed-evidence-seal",
    successor_set_id="iter241-completed-evidence-tree",
    successor_limitations=SUCCESSOR_LIMITATIONS,
    successor_limitations_sha256=(
        "cc62e045f38955b46906cc5f43bd76e54ba626dc02a0d1cef100df5ac0a3f2de"
    ),
)


@dataclass(frozen=True)
class SealQualification:
    """Fail-closed result consumed before pytest starts."""

    qualified: bool
    reason: str
    reference_commit: str | None = None
    source_commit: str | None = None


@dataclass(frozen=True)
class GitContext:
    """Structurally resolved repository paths used without ambient Git discovery."""

    root: Path
    git_dir: Path
    common_dir: Path


@dataclass(frozen=True)
class FrozenGitView:
    """Detached Git control bytes and their source-state reauthentication data."""

    context: GitContext
    source: GitContext
    source_head: str
    source_head_control: bytes
    source_index: bytes


class RoutingDenied(ValueError):
    """A required trust or qualification predicate did not hold."""


def _deny_if(condition: bool, reason: str) -> None:
    if condition:
        raise RoutingDenied(reason)


def _canonical_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _regular_0644(path: Path, *, reason: str) -> bytes:
    try:
        metadata = path.lstat()
        raw = path.read_bytes()
    except OSError as exc:
        raise RoutingDenied(reason) from exc
    _deny_if(
        not stat.S_ISREG(metadata.st_mode)
        or path.is_symlink()
        or stat.S_IMODE(metadata.st_mode) != 0o644,
        reason,
    )
    return raw


def _real_directory(path: Path, *, reason: str) -> Path:
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise RoutingDenied(reason) from exc
    _deny_if(
        not stat.S_ISDIR(metadata.st_mode) or path.is_symlink() or resolved != path,
        reason,
    )
    return resolved


def _trusted_executable(path: Path, *, reason: str) -> None:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise RoutingDenied(reason) from exc
    _deny_if(
        not path.is_absolute()
        or path.is_symlink()
        or not stat.S_ISREG(metadata.st_mode)
        or not metadata.st_mode & stat.S_IXUSR
        or metadata.st_mode & (stat.S_IWGRP | stat.S_IWOTH),
        reason,
    )


def _python_executable_reason(
    executable: Path,
    metadata: os.stat_result,
    *,
    euid: int,
) -> str | None:
    """Classify Python separately; Git and timeout retain stricter mode policy."""

    if not executable.is_absolute():
        return "executable_not_absolute"
    if not stat.S_ISREG(metadata.st_mode):
        return "executable_not_regular"
    if not metadata.st_mode & stat.S_IXUSR:
        return "owner_execute_missing"
    if metadata.st_uid not in {0, euid}:
        return "executable_owner_untrusted"
    if metadata.st_mode & stat.S_IWOTH:
        return "executable_world_writable"
    if metadata.st_mode & stat.S_IWGRP and metadata.st_uid != euid:
        return "foreign_owned_executable_group_writable"
    return None


def _trusted_python_executable(path: Path, *, reason: str) -> None:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise RoutingDenied(reason) from exc
    _deny_if(
        _python_executable_reason(path, metadata, euid=os.geteuid()) is not None,
        reason,
    )


def _control_path(raw: bytes, base: Path, *, prefix: bytes | None, reason: str) -> Path:
    _deny_if(len(raw) > 4096 or not raw.endswith(b"\n"), reason)
    lines = raw.splitlines()
    _deny_if(len(lines) != 1, reason)
    line = lines[0]
    if prefix is not None:
        _deny_if(not line.startswith(prefix), reason)
        line = line[len(prefix) :]
    try:
        value = line.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RoutingDenied(reason) from exc
    _deny_if(not value or "\0" in value, reason)
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = base / candidate
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise RoutingDenied(reason) from exc
    return resolved


def _reject_repository_indirection(git_dir: Path, common_dir: Path) -> None:
    forbidden_files = {
        common_dir / "objects/info/alternates",
        common_dir / "info/grafts",
        common_dir / "shallow",
        git_dir / "shallow",
    }
    _deny_if(
        any(path.exists() or path.is_symlink() for path in forbidden_files),
        "git_object_indirection",
    )
    for replace_root in {common_dir / "refs/replace", git_dir / "refs/replace"}:
        if replace_root.exists() or replace_root.is_symlink():
            _deny_if(
                replace_root.is_symlink()
                or not replace_root.is_dir()
                or any(replace_root.iterdir()),
                "git_replace_ref_present",
            )
    packed_refs = common_dir / "packed-refs"
    if packed_refs.exists() or packed_refs.is_symlink():
        raw = _regular_0644(packed_refs, reason="git_packed_refs_invalid")
        _deny_if(b" refs/replace/" in raw, "git_replace_ref_present")


def _discover_git_context(root: Path) -> GitContext:
    try:
        resolved_root = root.resolve(strict=True)
    except OSError as exc:
        raise RoutingDenied("repository_root_unavailable") from exc
    _deny_if(resolved_root != root, "repository_root_noncanonical")
    dot_git = root / ".git"
    try:
        metadata = dot_git.lstat()
    except OSError as exc:
        raise RoutingDenied("git_control_path_unavailable") from exc
    linked = stat.S_ISREG(metadata.st_mode) and not dot_git.is_symlink()
    if linked:
        git_dir = _control_path(
            dot_git.read_bytes(),
            root,
            prefix=b"gitdir: ",
            reason="git_control_path_invalid",
        )
        _real_directory(git_dir, reason="git_directory_invalid")
    else:
        _deny_if(
            not stat.S_ISDIR(metadata.st_mode) or dot_git.is_symlink(),
            "git_control_path_invalid",
        )
        git_dir = _real_directory(dot_git, reason="git_directory_invalid")

    commondir_path = git_dir / "commondir"
    if commondir_path.exists() or commondir_path.is_symlink():
        raw = _regular_0644(commondir_path, reason="git_commondir_invalid")
        common_dir = _control_path(
            raw,
            git_dir,
            prefix=None,
            reason="git_commondir_invalid",
        )
        _real_directory(common_dir, reason="git_commondir_invalid")
    else:
        common_dir = git_dir

    if linked:
        _deny_if(
            git_dir.parent.name != "worktrees" or git_dir.parent.parent != common_dir,
            "linked_git_directory_outside_common_dir",
        )
        backpointer = _regular_0644(git_dir / "gitdir", reason="git_backpointer_invalid")
        pointed = _control_path(
            backpointer,
            git_dir,
            prefix=None,
            reason="git_backpointer_invalid",
        )
        _deny_if(pointed != dot_git, "git_backpointer_invalid")
    else:
        _deny_if(common_dir != git_dir, "regular_git_commondir_invalid")

    _real_directory(common_dir / "objects", reason="git_objects_invalid")
    _regular_0644(git_dir / "HEAD", reason="git_head_invalid")
    _regular_0644(git_dir / "index", reason="git_index_invalid")
    _reject_repository_indirection(git_dir, common_dir)
    _trusted_executable(TRUSTED_GIT, reason="trusted_git_unavailable")
    context = GitContext(root, git_dir, common_dir)
    _deny_if(
        _git_checked(context, "rev-parse", "--show-object-format") != b"sha1\n",
        "git_object_format_invalid",
    )
    top = _git_checked(context, "rev-parse", "--show-toplevel")
    try:
        observed_root = Path(top.decode("utf-8").strip()).resolve(strict=True)
    except (OSError, UnicodeDecodeError) as exc:
        raise RoutingDenied("git_worktree_identity_invalid") from exc
    _deny_if(observed_root != root, "git_worktree_identity_invalid")
    return context


def _isolated_environment(*, pytest_process: bool = False) -> dict[str, str]:
    environment = {
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
        "PATH": TRUSTED_PATH,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
    }
    if pytest_process:
        environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    return environment


def _pytest_tool_path(python_executable: str) -> str:
    try:
        python = Path(python_executable).resolve(strict=True)
    except OSError as exc:
        raise RoutingDenied("trusted_python_unavailable") from exc
    _trusted_python_executable(python, reason="trusted_python_unavailable")
    directories = [python.parent]
    for candidate in TIMEOUT_CANDIDATES:
        try:
            timeout = candidate.resolve(strict=True)
        except OSError:
            continue
        _trusted_executable(timeout, reason="trusted_timeout_unavailable")
        directories.append(timeout.parent)
        break
    directories.extend((Path("/usr/bin"), Path("/bin")))
    return os.pathsep.join(dict.fromkeys(str(directory) for directory in directories))


def _git(
    context: GitContext,
    *arguments: str,
    input_bytes: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    _deny_if(
        not arguments or arguments[0] not in READ_ONLY_GIT_SUBCOMMANDS,
        "non_read_only_git_subcommand",
    )
    command = [
        str(TRUSTED_GIT),
        "--no-pager",
        f"--git-dir={context.git_dir}",
        f"--work-tree={context.root}",
        "-c",
        "credential.helper=",
        "-c",
        "credential.interactive=never",
        "-c",
        "core.hooksPath=/dev/null",
        "-c",
        "core.fsmonitor=false",
        *arguments,
    ]
    try:
        return subprocess.run(
            command,
            capture_output=True,
            check=False,
            cwd=context.root,
            env=_isolated_environment(),
            input=input_bytes,
            stdin=subprocess.DEVNULL if input_bytes is None else None,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RoutingDenied("local_git_inspection_failed") from exc


def _git_checked(
    context: GitContext,
    *arguments: str,
    input_bytes: bytes | None = None,
) -> bytes:
    result = _git(context, *arguments, input_bytes=input_bytes)
    if result.returncode != 0:
        raise RoutingDenied("local_git_inspection_failed")
    return result.stdout


def _write_isolated_control(path: Path, raw: bytes) -> None:
    try:
        path.write_bytes(raw)
        path.chmod(0o644)
    except OSError as exc:
        raise RoutingDenied("isolated_git_control_unavailable") from exc
    _deny_if(
        _regular_0644(path, reason="isolated_git_control_invalid") != raw,
        "isolated_git_control_invalid",
    )


@contextmanager
def _frozen_git_view(source: GitContext) -> Iterator[FrozenGitView]:
    """Detach Git from mutable refs and all repository-local configuration."""

    try:
        temp_metadata = TRUSTED_TEMP_ROOT.lstat()
    except OSError as exc:
        raise RoutingDenied("trusted_temp_root_unavailable") from exc
    temp_mode = stat.S_IMODE(temp_metadata.st_mode)
    _deny_if(
        not stat.S_ISDIR(temp_metadata.st_mode)
        or TRUSTED_TEMP_ROOT.is_symlink()
        or temp_metadata.st_uid != 0
        or (temp_mode & (stat.S_IWGRP | stat.S_IWOTH) and not temp_mode & stat.S_ISVTX),
        "trusted_temp_root_invalid",
    )

    head_raw = _git_checked(source, "rev-parse", "--verify", "HEAD^{commit}")
    try:
        head = head_raw.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise RoutingDenied("source_head_identity_invalid") from exc
    _deny_if(COMMIT_ID.fullmatch(head) is None, "source_head_identity_invalid")
    source_head_control = _regular_0644(
        source.git_dir / "HEAD",
        reason="source_head_control_invalid",
    )
    source_index = _regular_0644(
        source.git_dir / "index",
        reason="source_index_invalid",
    )

    with tempfile.TemporaryDirectory(
        prefix="telos-iter241-git-",
        dir=TRUSTED_TEMP_ROOT,
    ) as temporary:
        control = Path(temporary).resolve(strict=True)
        try:
            metadata = control.lstat()
        except OSError as exc:
            raise RoutingDenied("isolated_git_control_unavailable") from exc
        _deny_if(
            not stat.S_ISDIR(metadata.st_mode)
            or control.is_symlink()
            or metadata.st_uid != os.geteuid()
            or stat.S_IMODE(metadata.st_mode) & (stat.S_IRWXG | stat.S_IRWXO),
            "isolated_git_control_invalid",
        )
        try:
            (control / "refs/heads").mkdir(parents=True)
            (control / "refs/tags").mkdir(parents=True)
            (control / "objects").symlink_to(
                source.common_dir / "objects",
                target_is_directory=True,
            )
        except OSError as exc:
            raise RoutingDenied("isolated_git_control_unavailable") from exc
        _write_isolated_control(control / "HEAD", f"{head}\n".encode("ascii"))
        _write_isolated_control(control / "index", source_index)
        _write_isolated_control(control / "config", ISOLATED_GIT_CONFIG)

        context = GitContext(source.root, control, control)
        _deny_if(
            _git_checked(context, "rev-parse", "--show-object-format") != b"sha1\n",
            "isolated_git_object_format_invalid",
        )
        observed_top = _git_checked(context, "rev-parse", "--show-toplevel")
        try:
            top = Path(observed_top.decode("utf-8").strip()).resolve(strict=True)
        except (OSError, UnicodeDecodeError) as exc:
            raise RoutingDenied("isolated_git_worktree_invalid") from exc
        _deny_if(top != source.root, "isolated_git_worktree_invalid")
        yield FrozenGitView(
            context=context,
            source=source,
            source_head=head,
            source_head_control=source_head_control,
            source_index=source_index,
        )


def _reauthenticate_source_git(view: FrozenGitView) -> None:
    observed = _discover_git_context(view.source.root)
    _deny_if(observed != view.source, "source_git_context_drift")
    _deny_if(
        _regular_0644(
            observed.git_dir / "HEAD",
            reason="source_head_control_drift",
        )
        != view.source_head_control,
        "source_head_control_drift",
    )
    _deny_if(
        _regular_0644(
            observed.git_dir / "index",
            reason="source_index_drift",
        )
        != view.source_index,
        "source_index_drift",
    )
    current_head = _git_checked(observed, "rev-parse", "--verify", "HEAD^{commit}")
    _deny_if(
        current_head != f"{view.source_head}\n".encode("ascii"),
        "source_head_identity_drift",
    )


def _strict_object(raw: bytes, *, label: str) -> dict[str, Any]:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise RoutingDenied(f"{label}_duplicate_key")
            result[key] = value
        return result

    try:
        value = json.loads(
            raw,
            object_pairs_hook=unique_object,
            parse_constant=lambda _value: (_ for _ in ()).throw(
                RoutingDenied(f"{label}_nonfinite_number")
            ),
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RoutingDenied(f"{label}_invalid_json") from exc
    _deny_if(not isinstance(value, dict), f"{label}_not_object")
    return value


def _commit_identity(context: GitContext, commit: str) -> tuple[str, tuple[str, ...]]:
    _deny_if(COMMIT_ID.fullmatch(commit) is None, "pinned_commit_identity_invalid")
    raw = _git_checked(context, "show", "-s", "--format=%T%x00%P", commit)
    try:
        tree_raw, parents_raw = raw.rstrip(b"\n").split(b"\0", 1)
        tree = tree_raw.decode("ascii")
        parents = tuple(parents_raw.decode("ascii").split())
    except (UnicodeDecodeError, ValueError) as exc:
        raise RoutingDenied("commit_identity_malformed") from exc
    _deny_if(COMMIT_ID.fullmatch(tree) is None, "commit_tree_identity_invalid")
    _deny_if(
        any(COMMIT_ID.fullmatch(parent) is None for parent in parents),
        "commit_parent_identity_invalid",
    )
    return tree, parents


def _tree_oid(context: GitContext, commit: str, path: str) -> str:
    result = _git(context, "rev-parse", "--verify", f"{commit}:{path}")
    if result.returncode != 0:
        raise RoutingDenied("protected_subtree_missing")
    try:
        object_id = result.stdout.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise RoutingDenied("protected_subtree_identity_invalid") from exc
    _deny_if(COMMIT_ID.fullmatch(object_id) is None, "protected_subtree_identity_invalid")
    object_type = _git_checked(context, "cat-file", "-t", object_id).decode("ascii").strip()
    _deny_if(object_type != "tree", "protected_subtree_not_tree")
    return object_id


def _is_ancestor(context: GitContext, ancestor: str, descendant: str) -> bool:
    result = _git(context, "merge-base", "--is-ancestor", ancestor, descendant)
    if result.returncode not in {0, 1}:
        raise RoutingDenied("ancestry_inspection_failed")
    return result.returncode == 0


def _literal_pathspec(path: str) -> str:
    return f":(literal){path}"


def _canonical_relative_path(value: str) -> bool:
    path = PurePosixPath(value)
    return (
        bool(value)
        and "\\" not in value
        and not path.is_absolute()
        and path.as_posix() == value
        and all(part not in {"", ".", ".."} for part in path.parts)
        and not any(ord(character) < 32 or ord(character) == 127 for character in value)
    )


def _manifest(context: GitContext, reference: str, path: str) -> tuple[int, str]:
    listing = _git_checked(
        context,
        "ls-tree",
        "-r",
        "-z",
        "--full-tree",
        reference,
        "--",
        _literal_pathspec(path),
    )
    entries: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for raw_entry in listing.split(b"\0"):
        if not raw_entry:
            continue
        try:
            metadata, path_raw = raw_entry.split(b"\t", 1)
            mode, object_type, object_id = metadata.decode("ascii").split()
            relative = path_raw.decode("utf-8")
        except (UnicodeDecodeError, ValueError) as exc:
            raise RoutingDenied("protected_manifest_malformed") from exc
        _deny_if(
            object_type != "blob"
            or mode not in {"100644", "100755"}
            or COMMIT_ID.fullmatch(object_id) is None
            or not _canonical_relative_path(relative)
            or not relative.startswith(f"{path}/")
            or relative in seen,
            "protected_manifest_malformed",
        )
        seen.add(relative)
        entries.append((relative, mode, object_id))
    entries.sort()
    digest = hashlib.sha256()
    for relative, mode, object_id in entries:
        payload = _git_checked(context, "cat-file", "blob", object_id)
        digest.update(
            relative.encode("utf-8")
            + b"\0"
            + mode.encode("ascii")
            + b"\0"
            + str(len(payload)).encode("ascii")
            + b"\0"
            + hashlib.sha256(payload).hexdigest().encode("ascii")
            + b"\n"
        )
    return len(entries), digest.hexdigest()


def _authenticate_committed_file(
    context: GitContext,
    relative: str,
    expected_digest: str,
    *,
    reference: str | None = None,
    reason: str,
) -> bytes:
    _deny_if(SHA256.fullmatch(expected_digest) is None, reason)
    raw = _regular_0644(context.root / relative, reason=reason)
    head_raw = _git_checked(context, "show", f"HEAD:{relative}")
    index_raw = _git_checked(context, "show", f":{relative}")
    identities = [raw, head_raw, index_raw]
    if reference is not None:
        identities.append(_git_checked(context, "show", f"{reference}:{relative}"))
    _deny_if(any(item != raw for item in identities), reason)
    _deny_if(hashlib.sha256(raw).hexdigest() != expected_digest, reason)
    return raw


def _expected_authorization(contract: RoutingContract) -> dict[str, Any]:
    return {
        "seal_id": contract.authorization_seal_id,
        "record_type": "prospective_successor_authorization",
        "predecessor_seal_id": contract.authorization_predecessor_id,
        "reference_commit": contract.governed_merge,
        "authorized_path": ITER241_PATH,
        "must_be_absent_at_reference": True,
        "policy": "additions_only_until_successor_seal",
        "closure_requirement": "exact_tree_successor_path_snapshot",
        "limitations": list(contract.authorization_limitations),
    }


def _authorization_record(
    registry: dict[str, Any],
    contract: RoutingContract,
) -> None:
    records = registry.get("records")
    _deny_if(not isinstance(records, list), "seal_registry_records_invalid")
    matches = [
        record
        for record in records
        if isinstance(record, dict) and record.get("seal_id") == contract.authorization_seal_id
    ]
    _deny_if(len(matches) != 1, "authorization_record_absent_or_ambiguous")
    expected = _expected_authorization(contract)
    _deny_if(matches[0] != expected, "authorization_record_mismatch")
    _deny_if(
        _canonical_digest(matches[0]) != contract.authorization_record_sha256,
        "authorization_record_digest_mismatch",
    )


def _record_selects_path(record: dict[str, Any]) -> bool:
    protected_sets = record.get("protected_sets")
    if not isinstance(protected_sets, list):
        return False
    return any(
        isinstance(protected, dict)
        and isinstance(protected.get("selector"), dict)
        and protected["selector"].get("path") == ITER241_PATH
        for protected in protected_sets
    )


def _successor_record(
    registry: dict[str, Any],
    contract: RoutingContract,
) -> dict[str, Any]:
    records = registry.get("records")
    _deny_if(not isinstance(records, list), "seal_registry_records_invalid")
    candidates = [
        record
        for record in records
        if isinstance(record, dict)
        and (
            record.get("seal_id") == contract.successor_seal_id
            or record.get("predecessor_seal_id") == contract.authorization_seal_id
            or _record_selects_path(record)
        )
    ]
    _deny_if(len(candidates) != 1, "successor_record_absent_or_ambiguous")
    record = candidates[0]
    _deny_if(
        set(record)
        != {
            "seal_id",
            "record_type",
            "predecessor_seal_id",
            "reference_commit",
            "protected_sets",
            "limitations",
        },
        "successor_record_fields_invalid",
    )
    _deny_if(record.get("seal_id") != contract.successor_seal_id, "successor_seal_id_mismatch")
    _deny_if(
        record.get("record_type") != "successor_path_snapshot", "successor_record_type_invalid"
    )
    _deny_if(
        record.get("predecessor_seal_id") != contract.authorization_seal_id,
        "successor_predecessor_mismatch",
    )
    reference = record.get("reference_commit")
    _deny_if(
        not isinstance(reference, str) or COMMIT_ID.fullmatch(reference) is None,
        "successor_reference_invalid",
    )
    protected_sets = record.get("protected_sets")
    _deny_if(
        not isinstance(protected_sets, list) or len(protected_sets) != 1,
        "successor_protected_set_invalid",
    )
    protected = protected_sets[0]
    _deny_if(
        not isinstance(protected, dict)
        or set(protected) != {"set_id", "selector", "policy", "blob_count", "manifest_sha256"},
        "successor_protected_set_invalid",
    )
    _deny_if(
        protected.get("set_id") != contract.successor_set_id
        or protected.get("selector") != {"kind": "tree", "path": ITER241_PATH}
        or protected.get("policy") != "exact_tree"
        or protected.get("blob_count") != contract.iter241_blob_count
        or not isinstance(protected.get("manifest_sha256"), str)
        or SHA256.fullmatch(protected["manifest_sha256"]) is None,
        "successor_protected_set_invalid",
    )
    limitations = record.get("limitations")
    _deny_if(
        limitations != list(contract.successor_limitations),
        "successor_limitations_mismatch",
    )
    _deny_if(
        _canonical_digest(limitations) != contract.successor_limitations_sha256,
        "successor_limitations_digest_mismatch",
    )
    return record


def _verify_topology(
    context: GitContext,
    reference: str,
    contract: RoutingContract,
) -> None:
    authorization = _commit_identity(context, contract.authorization_commit)
    _deny_if(
        authorization != (contract.authorization_tree, contract.authorization_parents),
        "authorization_identity_mismatch",
    )
    sealed = _commit_identity(context, contract.sealed_iter240_commit)
    _deny_if(
        sealed != (contract.sealed_iter240_tree, (contract.sealed_iter240_parent,)),
        "sealed_iter240_identity_mismatch",
    )
    _deny_if(
        _tree_oid(
            context,
            contract.sealed_iter240_commit,
            "experiments/iter240_ground_truth_admission_design",
        )
        != contract.sealed_iter240_subtree,
        "sealed_iter240_subtree_mismatch",
    )
    merge = _commit_identity(context, contract.governed_merge)
    _deny_if(
        merge != (contract.governed_merge_tree, contract.governed_merge_parents),
        "governed_merge_identity_mismatch",
    )
    try:
        resolved_reference = (
            _git_checked(context, "rev-parse", "--verify", f"{reference}^{{commit}}")
            .decode("ascii")
            .strip()
        )
    except (RoutingDenied, UnicodeDecodeError) as exc:
        raise RoutingDenied("successor_reference_missing") from exc
    _deny_if(resolved_reference != reference, "successor_reference_missing")
    _commit_identity(context, reference)
    _deny_if(
        not _is_ancestor(context, contract.authorization_commit, reference),
        "successor_reference_predates_authorization",
    )
    _deny_if(
        not _is_ancestor(context, contract.correction_checkpoint, reference),
        "successor_reference_predates_correction",
    )
    _deny_if(
        _tree_oid(context, contract.correction_checkpoint, ITER241_PATH)
        != contract.correction_checkpoint_subtree,
        "correction_checkpoint_subtree_mismatch",
    )
    _deny_if(
        not _is_ancestor(context, reference, "HEAD"),
        "successor_reference_not_ancestor",
    )


def _verify_subtree_and_manifest(
    context: GitContext,
    reference: str,
    record: dict[str, Any],
    contract: RoutingContract,
) -> None:
    reference_subtree = _tree_oid(context, reference, ITER241_PATH)
    _deny_if(
        reference_subtree != contract.iter241_subtree,
        "successor_reference_subtree_mismatch",
    )
    _deny_if(
        _tree_oid(context, "HEAD", ITER241_PATH) != reference_subtree,
        "current_iter241_subtree_mismatch",
    )
    protected = record["protected_sets"][0]
    count, digest = _manifest(context, reference, ITER241_PATH)
    _deny_if(
        count != contract.iter241_blob_count
        or count != protected["blob_count"]
        or digest != protected["manifest_sha256"],
        "successor_manifest_mismatch",
    )
    pathspec = _literal_pathspec(ITER241_PATH)
    staged = _git(
        context,
        "diff",
        "--cached",
        "--no-ext-diff",
        "--no-textconv",
        "--quiet",
        reference,
        "--",
        pathspec,
    )
    worktree = _git(
        context,
        "diff",
        "--no-ext-diff",
        "--no-textconv",
        "--quiet",
        reference,
        "--",
        pathspec,
    )
    _deny_if(staged.returncode != 0 or worktree.returncode != 0, "iter241_worktree_drift")
    untracked = _git_checked(
        context,
        "ls-files",
        "--others",
        "-z",
        "--",
        pathspec,
    )
    _deny_if(bool(untracked), "iter241_untracked_drift")


def _verify_correction(
    context: GitContext,
    reference: str,
    contract: RoutingContract,
) -> None:
    raw = _authenticate_committed_file(
        context,
        CORRECTION_RECEIPT_PATH,
        contract.correction_receipt_sha256,
        reference=reference,
        reason="correction_receipt_identity_mismatch",
    )
    receipt = _strict_object(raw, label="correction_receipt")
    _deny_if(
        receipt.get("schema_version") != "telos.iter241.repository_closure_correction.v1",
        "correction_receipt_schema_mismatch",
    )
    _deny_if(
        receipt.get("adjudication") != dict(EXPECTED_STATUS_ITEMS),
        "correction_status_vector_mismatch",
    )
    defect = receipt.get("defect")
    _deny_if(not isinstance(defect, dict), "correction_defect_vector_mismatch")
    _deny_if(
        defect.get("retained_pull_request")
        != {
            "contract_acceptance": False,
            "merge_commit_sha_classification": "omitted",
            "merge_commit_sha_member_present": False,
            "original_projection_value": None,
        },
        "correction_merge_member_falsifier_mismatch",
    )
    _deny_if(
        defect.get("retained_response_headers")
        != {
            "capture_completeness": "failed",
            "contract_acceptance": False,
            "exact_header_section_bytes_reconstructible": False,
            "raw_header_byte_fidelity": "failed",
            "raw_header_section_bytes_retained": False,
            "retained_representation": "canonicalized_returned_header_pair_documents",
            "source_api": "http.client.HTTPResponse.getheaders",
        },
        "correction_header_falsifier_mismatch",
    )
    original_attempt = receipt.get("original_attempt")
    _deny_if(
        not isinstance(original_attempt, dict) or original_attempt.get("retry_authority") != "none",
        "correction_retry_authority_mismatch",
    )


def _verify_guard_bytes(
    context: GitContext,
    reference: str,
    contract: RoutingContract,
) -> None:
    expected = {
        CORRECTION_ADJUDICATOR_PATH: contract.correction_adjudicator_sha256,
        SEAL_VALIDATOR_PATH: contract.seal_registry_validator_sha256,
        RECEIPT_SEALING_PATH: contract.receipt_sealing_sha256,
        FROZEN_VALIDATOR_PATH: contract.frozen_validator_sha256,
        FROZEN_TEST_PATH: contract.frozen_test_sha256,
        PYPROJECT_PATH: contract.pyproject_sha256,
    }
    for relative, expected_digest in expected.items():
        _authenticate_committed_file(
            context,
            relative,
            expected_digest,
            reference=reference,
            reason="guard_file_identity_mismatch",
        )


DELEGATE_BOOTSTRAP = (
    "import sys, types\n"
    "path = sys.argv[1]\n"
    "dependency_path = sys.argv[2]\n"
    "stream = sys.stdin.buffer\n"
    "dependency_size = int(stream.readline())\n"
    "dependency = stream.read(dependency_size)\n"
    "if len(dependency) != dependency_size: raise RuntimeError('truncated dependency')\n"
    "payload = stream.read()\n"
    "if dependency_path != '-':\n"
    "    package = types.ModuleType('scripts')\n"
    "    package.__package__ = 'scripts'\n"
    "    package.__path__ = []\n"
    "    sys.modules['scripts'] = package\n"
    "    module = types.ModuleType('scripts.receipt_sealing')\n"
    "    module.__file__ = dependency_path\n"
    "    module.__package__ = 'scripts'\n"
    "    sys.modules['scripts.receipt_sealing'] = module\n"
    "    package.receipt_sealing = module\n"
    "    exec(compile(dependency, dependency_path, 'exec'), module.__dict__, module.__dict__)\n"
    "elif dependency_size != 0: raise RuntimeError('unexpected dependency')\n"
    "sys.argv = [path]\n"
    "namespace = {'__name__': '__main__', '__file__': path, '__package__': None}\n"
    "exec(compile(payload, path, 'exec'), namespace, namespace)\n"
)


def _authenticate_delegates(
    context: GitContext,
    contract: RoutingContract,
) -> dict[str, bytes]:
    return {
        SEAL_VALIDATOR_PATH: _authenticate_committed_file(
            context,
            SEAL_VALIDATOR_PATH,
            contract.seal_registry_validator_sha256,
            reason="seal_validator_identity_mismatch",
        ),
        RECEIPT_SEALING_PATH: _authenticate_committed_file(
            context,
            RECEIPT_SEALING_PATH,
            contract.receipt_sealing_sha256,
            reason="receipt_sealing_identity_mismatch",
        ),
        CORRECTION_ADJUDICATOR_PATH: _authenticate_committed_file(
            context,
            CORRECTION_ADJUDICATOR_PATH,
            contract.correction_adjudicator_sha256,
            reason="correction_adjudicator_identity_mismatch",
        ),
    }


def _run_delegate(
    context: GitContext,
    relative: str,
    payload: bytes,
    *,
    dependency_relative: str | None = None,
    dependency_payload: bytes = b"",
) -> bool:
    try:
        python = Path(sys.executable).resolve(strict=True)
    except OSError as exc:
        raise RoutingDenied("trusted_python_unavailable") from exc
    _trusted_python_executable(python, reason="trusted_python_unavailable")
    environment = _isolated_environment()
    environment.update(
        {
            "GIT_DIR": str(context.git_dir),
            "GIT_WORK_TREE": str(context.root),
        }
    )
    dependency_path = (
        str(context.root / dependency_relative) if dependency_relative is not None else "-"
    )
    bundle = f"{len(dependency_payload)}\n".encode("ascii") + dependency_payload + payload
    try:
        result = subprocess.run(
            [
                str(python),
                "-I",
                "-c",
                DELEGATE_BOOTSTRAP,
                str(context.root / relative),
                dependency_path,
            ],
            input=bundle,
            capture_output=True,
            check=False,
            cwd=context.root,
            env=environment,
            timeout=180,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RoutingDenied("delegated_validator_execution_failed") from exc
    return result.returncode == 0


def _run_delegated_validators(
    context: GitContext,
    contract: RoutingContract,
) -> None:
    authenticated = _authenticate_delegates(context, contract)
    seal_ok = _run_delegate(
        context,
        SEAL_VALIDATOR_PATH,
        authenticated[SEAL_VALIDATOR_PATH],
        dependency_relative=RECEIPT_SEALING_PATH,
        dependency_payload=authenticated[RECEIPT_SEALING_PATH],
    )
    correction_ok = _run_delegate(
        context,
        CORRECTION_ADJUDICATOR_PATH,
        authenticated[CORRECTION_ADJUDICATOR_PATH],
    )
    _authenticate_delegates(context, contract)
    _deny_if(not seal_ok, "full_seal_registry_invalid")
    _deny_if(not correction_ok, "correction_adjudicator_invalid")


def _qualify(root: Path, contract: RoutingContract) -> SealQualification:
    source_commit: str | None = None
    try:
        source = _discover_git_context(root)
        with _frozen_git_view(source) as view:
            source_commit = view.source_head
            context = view.context
            registry_raw = _authenticate_committed_file(
                context,
                REGISTRY_PATH,
                hashlib.sha256((root / REGISTRY_PATH).read_bytes()).hexdigest(),
                reason="seal_registry_not_committed_clean",
            )
            registry_digest = hashlib.sha256(registry_raw).hexdigest()
            registry = _strict_object(registry_raw, label="seal_registry")
            _authorization_record(registry, contract)
            record = _successor_record(registry, contract)
            _run_delegated_validators(context, contract)
            _authenticate_committed_file(
                context,
                REGISTRY_PATH,
                registry_digest,
                reason="seal_registry_drift_after_delegation",
            )
            reference = record["reference_commit"]
            assert isinstance(reference, str)
            _verify_topology(context, reference, contract)
            _verify_subtree_and_manifest(context, reference, record, contract)
            _verify_correction(context, reference, contract)
            _verify_guard_bytes(context, reference, contract)
            _reauthenticate_source_git(view)
    except RoutingDenied as exc:
        return SealQualification(False, str(exc), source_commit=source_commit)
    except Exception:
        return SealQualification(
            False,
            "unexpected_qualification_failure",
            source_commit=source_commit,
        )
    return SealQualification(True, "seal_qualified", reference, source_commit)


def seal_qualification(root: Path = ROOT) -> SealQualification:
    """Evaluate the fixed production contract without injectable authority inputs."""

    return _qualify(root, DEFAULT_CONTRACT)


def authoritative_pytest_argv(
    qualification: SealQualification,
    *,
    python_executable: str,
    root: Path,
) -> tuple[str, ...]:
    """Build the sole authoritative full-suite command before pytest starts."""

    try:
        resolved_root = root.resolve(strict=True)
        tests = (root / TESTS_PATH).resolve(strict=True)
    except OSError as exc:
        raise RoutingDenied("pytest_target_unavailable") from exc
    _deny_if(
        resolved_root != root or tests != root / TESTS_PATH or not tests.is_dir(),
        "pytest_target_invalid",
    )
    command = [
        python_executable,
        "-I",
        "-m",
        "pytest",
        "-q",
        "-c",
        str(root / PYPROJECT_PATH),
        f"--confcutdir={root}",
        str(tests),
    ]
    if qualification.qualified:
        command.extend(f"--deselect={nodeid}" for nodeid in FROZEN_EXACT_HEAD_NODEIDS)
    return tuple(command)


def pytest_environment(*, python_executable: str) -> dict[str, str]:
    """Return the fixed environment used by the authenticated runner."""

    environment = _isolated_environment(pytest_process=True)
    environment["PATH"] = _pytest_tool_path(python_executable)
    return environment


def no_pytest_plugin_surface(root: Path = ROOT) -> bool:
    """Reject repository plugin surfaces that could mutate qualified collection."""

    if (root / "conftest.py").exists() or (root / "conftest.py").is_symlink():
        return False
    tests = root / "tests"
    try:
        for path in tests.rglob("*.py"):
            metadata = path.lstat()
            if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
                return False
            if path.name == "conftest.py":
                return False
            tokens = tokenize.tokenize(io.BytesIO(path.read_bytes()).readline)
            if any(
                token.type == tokenize.NAME and token.string == "pytest_plugins"
                for token in tokens
            ):
                return False
    except (OSError, SyntaxError, tokenize.TokenError):
        return False
    return True


def protected_deselections(arguments: Iterable[str]) -> tuple[str, ...]:
    """Extract protected deselections for runner-side exact-command verification."""

    allowed = {f"--deselect={nodeid}" for nodeid in FROZEN_EXACT_HEAD_NODEIDS}
    return tuple(argument for argument in arguments if argument in allowed)
