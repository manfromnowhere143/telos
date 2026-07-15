"""Descriptor-anchored filesystem operations for retained provider evidence.

The paid iter202 stages must not follow a repository-local symlink or let a
renamed parent redirect checkpoint I/O.  ``SecureCheckpointStage`` opens a
fixed stage beneath a trusted repository root, retains directory descriptors,
and performs every subsequent operation relative to those descriptors.

The class protects evidence location and fail-closed behavior.  It does not
attempt to provide availability against an actor that can rename repository
directories while a provider request is in flight; path-to-descriptor binding
checks turn such interference into an explicit failure.
"""

from __future__ import annotations

import fcntl
import os
from pathlib import Path
import secrets
import stat
from types import TracebackType
from typing import Iterator


class SecureCheckpointError(ValueError):
    """A checkpoint path cannot be proved anchored below its trusted root."""


_DIRECTORY_FLAGS = (
    os.O_RDONLY
    | getattr(os, "O_CLOEXEC", 0)
    | getattr(os, "O_DIRECTORY", 0)
    | getattr(os, "O_NOFOLLOW", 0)
)
_READ_FLAGS = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
_WRITE_FLAGS = (
    os.O_WRONLY
    | os.O_CREAT
    | os.O_EXCL
    | getattr(os, "O_CLOEXEC", 0)
    | getattr(os, "O_NOFOLLOW", 0)
)


def _identity(descriptor: int) -> tuple[int, int]:
    info = os.fstat(descriptor)
    return info.st_dev, info.st_ino


def _normalized_absolute(path: Path) -> Path:
    """Normalize dots without resolving or following any filesystem entry."""

    return Path(os.path.abspath(os.fspath(path)))


def _safe_name(name: str) -> str:
    if (
        not isinstance(name, str)
        or not name
        or name in {".", ".."}
        or "/" in name
        or (os.altsep is not None and os.altsep in name)
        or "\x00" in name
    ):
        raise SecureCheckpointError(f"unsafe checkpoint entry name: {name!r}")
    return name


class SecureCheckpointStage:
    """An opened and continuously verifiable checkpoint directory.

    Instances are context managers.  The repository root and stage directory
    descriptors remain open for the full context.  Direct child directories
    (notably ``provider_attempts``) are opened once and retained as well.
    """

    def __init__(
        self,
        *,
        root: Path,
        path: Path,
        relative_parts: tuple[str, ...],
        root_descriptor: int,
        stage_descriptor: int,
        error_type: type[Exception],
    ) -> None:
        self.root = root
        self.path = path
        self.relative_parts = relative_parts
        self._root_descriptor = root_descriptor
        self._stage_descriptor = stage_descriptor
        self._root_identity = _identity(root_descriptor)
        self._stage_identity = _identity(stage_descriptor)
        self._children: dict[str, tuple[int, tuple[int, int]]] = {}
        self._error_type = error_type
        self._closed = False
        self._locked = False

    @classmethod
    def open(
        cls,
        root: Path,
        path: Path,
        *,
        create: bool,
        error_type: type[Exception] = SecureCheckpointError,
    ) -> SecureCheckpointStage:
        root = _normalized_absolute(root)
        path = _normalized_absolute(path)
        try:
            relative = path.relative_to(root)
        except ValueError as exc:
            raise error_type(f"checkpoint stage escapes trusted root: {path}") from exc
        parts = tuple(relative.parts)
        if not parts:
            raise error_type("checkpoint stage must be below, not equal to, trusted root")
        if any(part in {"", ".", ".."} for part in parts):
            raise error_type(f"checkpoint stage has an unsafe component: {path}")

        try:
            root_descriptor = os.open(root, _DIRECTORY_FLAGS)
        except OSError as exc:
            raise error_type(f"cannot open trusted checkpoint root without symlinks: {root}") from exc

        current = os.dup(root_descriptor)
        stage_descriptor = -1
        try:
            for part in parts:
                _safe_name(part)
                try:
                    following = os.open(part, _DIRECTORY_FLAGS, dir_fd=current)
                except FileNotFoundError:
                    if not create:
                        raise
                    try:
                        os.mkdir(part, mode=0o700, dir_fd=current)
                        os.fsync(current)
                    except FileExistsError:
                        # Another process created the entry.  The no-follow open
                        # below proves it is the directory we require.
                        pass
                    following = os.open(part, _DIRECTORY_FLAGS, dir_fd=current)
                os.close(current)
                current = following
            stage_descriptor = current
            current = -1
            opened = cls(
                root=root,
                path=path,
                relative_parts=parts,
                root_descriptor=root_descriptor,
                stage_descriptor=stage_descriptor,
                error_type=error_type,
            )
            opened.verify_binding()
            return opened
        except BaseException as exc:
            if current >= 0:
                os.close(current)
            if stage_descriptor >= 0:
                os.close(stage_descriptor)
            os.close(root_descriptor)
            if isinstance(exc, error_type):
                raise
            if isinstance(exc, SecureCheckpointError):
                raise error_type(str(exc)) from exc
            if isinstance(exc, OSError):
                raise error_type(
                    f"cannot traverse checkpoint stage without symlinks: {path}: {exc}"
                ) from exc
            raise

    @property
    def descriptor(self) -> int:
        self._require_open()
        return self._stage_descriptor

    @property
    def name(self) -> str:
        """Path-compatible stage label used by lock-order instrumentation."""

        return self.path.name

    def _require_open(self) -> None:
        if self._closed:
            raise self._error_type(f"checkpoint stage is closed: {self.path}")

    def _raise(self, message: str, exc: BaseException | None = None) -> None:
        if exc is None:
            raise self._error_type(message)
        raise self._error_type(message) from exc

    def __enter__(self) -> SecureCheckpointStage:
        self._require_open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            self.close()
        except OSError:
            if exc_type is None:
                raise

    def close(self) -> None:
        if self._closed:
            return
        if self._locked:
            try:
                fcntl.flock(self._stage_descriptor, fcntl.LOCK_UN)
            finally:
                self._locked = False
        for descriptor, _ in self._children.values():
            os.close(descriptor)
        self._children.clear()
        os.close(self._stage_descriptor)
        os.close(self._root_descriptor)
        self._closed = True

    def _reopen_stage_from_root(self) -> int:
        current = os.dup(self._root_descriptor)
        try:
            for part in self.relative_parts:
                following = os.open(part, _DIRECTORY_FLAGS, dir_fd=current)
                os.close(current)
                current = following
            return current
        except BaseException:
            os.close(current)
            raise

    def verify_binding(self) -> None:
        """Prove retained descriptors still match entries below the trusted root."""

        self._require_open()
        try:
            # The already-open root descriptor is the trust anchor.  Reopening
            # its pathname would reintroduce dependence on components above the
            # trusted boundary; all stage-path checks instead re-traverse from
            # this retained descriptor.
            if _identity(self._root_descriptor) != self._root_identity:
                self._raise(f"trusted checkpoint root descriptor changed: {self.root}")
            reopened = self._reopen_stage_from_root()
            try:
                if _identity(reopened) != self._stage_identity:
                    self._raise(f"checkpoint stage path binding changed: {self.path}")
            finally:
                os.close(reopened)
            if _identity(self._stage_descriptor) != self._stage_identity:
                self._raise(f"checkpoint stage descriptor identity changed: {self.path}")
            for name, (descriptor, identity) in self._children.items():
                reopened_child = os.open(name, _DIRECTORY_FLAGS, dir_fd=self._stage_descriptor)
                try:
                    if _identity(reopened_child) != identity or _identity(descriptor) != identity:
                        self._raise(
                            f"checkpoint child-directory binding changed: {self.path / name}"
                        )
                finally:
                    os.close(reopened_child)
        except self._error_type:
            raise
        except OSError as exc:
            self._raise(f"checkpoint path binding cannot be verified: {self.path}: {exc}", exc)

    def hold_directory(self, name: str, *, create: bool) -> None:
        """Open and retain one direct child directory without following symlinks."""

        name = _safe_name(name)
        self.verify_binding()
        if name in self._children:
            return
        try:
            try:
                descriptor = os.open(name, _DIRECTORY_FLAGS, dir_fd=self._stage_descriptor)
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(name, mode=0o700, dir_fd=self._stage_descriptor)
                    os.fsync(self._stage_descriptor)
                except FileExistsError:
                    pass
                descriptor = os.open(name, _DIRECTORY_FLAGS, dir_fd=self._stage_descriptor)
            self._children[name] = (descriptor, _identity(descriptor))
            self.verify_binding()
        except self._error_type:
            raise
        except OSError as exc:
            self._raise(
                f"cannot open checkpoint child directory without symlinks: {self.path / name}: {exc}",
                exc,
            )

    def child_exists(self, name: str) -> bool:
        name = _safe_name(name)
        self.verify_binding()
        try:
            info = os.stat(name, dir_fd=self._stage_descriptor, follow_symlinks=False)
        except FileNotFoundError:
            return False
        if not stat.S_ISDIR(info.st_mode):
            self._raise(f"checkpoint child is not a regular directory: {self.path / name}")
        return True

    def _directory_descriptor(self, directory: str | None) -> int:
        if directory is None:
            return self._stage_descriptor
        directory = _safe_name(directory)
        retained = self._children.get(directory)
        if retained is None:
            self._raise(f"checkpoint child directory is not held: {self.path / directory}")
        return retained[0]

    def display_path(self, name: str, *, directory: str | None = None) -> Path:
        name = _safe_name(name)
        return self.path / name if directory is None else self.path / _safe_name(directory) / name

    def list_regular_names(self, *, directory: str | None = None) -> list[str]:
        """List a directory while rejecting every non-regular entry."""

        self.verify_binding()
        descriptor = self._directory_descriptor(directory)
        try:
            names = sorted(os.listdir(descriptor))
            for name in names:
                _safe_name(name)
                info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
                if not stat.S_ISREG(info.st_mode):
                    self._raise(
                        f"unexpected non-regular checkpoint entry: "
                        f"{self.display_path(name, directory=directory)}"
                    )
            return names
        except self._error_type:
            raise
        except OSError as exc:
            self._raise(f"cannot list checkpoint directory: {self.path}: {exc}", exc)

    def matching_regular_names(
        self, suffixes: tuple[str, ...], *, directory: str | None = None
    ) -> set[str]:
        self.verify_binding()
        descriptor = self._directory_descriptor(directory)
        matches: set[str] = set()
        try:
            for name in os.listdir(descriptor):
                _safe_name(name)
                if not any(name.endswith(suffix) for suffix in suffixes):
                    continue
                info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
                if not stat.S_ISREG(info.st_mode):
                    self._raise(
                        f"checkpoint artifact is not a regular file: "
                        f"{self.display_path(name, directory=directory)}"
                    )
                matches.add(name)
            return matches
        except self._error_type:
            raise
        except OSError as exc:
            self._raise(f"cannot inspect checkpoint artifacts: {self.path}: {exc}", exc)

    def regular_file_exists(self, name: str, *, directory: str | None = None) -> bool:
        name = _safe_name(name)
        self.verify_binding()
        descriptor = self._directory_descriptor(directory)
        try:
            info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
        except FileNotFoundError:
            return False
        except OSError as exc:
            self._raise(f"cannot stat checkpoint file: {self.display_path(name, directory=directory)}", exc)
        if not stat.S_ISREG(info.st_mode):
            self._raise(
                f"checkpoint entry is not a regular file: {self.display_path(name, directory=directory)}"
            )
        return True

    def read_bytes(self, name: str, *, directory: str | None = None) -> bytes:
        name = _safe_name(name)
        self.verify_binding()
        descriptor = self._directory_descriptor(directory)
        try:
            file_descriptor = os.open(name, _READ_FLAGS, dir_fd=descriptor)
            try:
                before = os.fstat(file_descriptor)
                if not stat.S_ISREG(before.st_mode):
                    self._raise(
                        f"checkpoint entry is not a regular file: "
                        f"{self.display_path(name, directory=directory)}"
                    )
                chunks: list[bytes] = []
                while True:
                    chunk = os.read(file_descriptor, 1024 * 1024)
                    if not chunk:
                        break
                    chunks.append(chunk)
                after = os.fstat(file_descriptor)
                if (
                    (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
                    or before.st_mode != after.st_mode
                    or before.st_nlink != after.st_nlink
                    or before.st_size != after.st_size
                    or before.st_mtime_ns != after.st_mtime_ns
                    or before.st_ctime_ns != after.st_ctime_ns
                    or sum(map(len, chunks)) != after.st_size
                ):
                    self._raise(
                        f"checkpoint file changed while being read: "
                        f"{self.display_path(name, directory=directory)}"
                    )
                return b"".join(chunks)
            finally:
                os.close(file_descriptor)
        except self._error_type:
            raise
        except OSError as exc:
            self._raise(f"cannot read checkpoint file: {self.display_path(name, directory=directory)}", exc)

    def _write_temporary(
        self, name: str, payload: bytes, *, directory: str | None
    ) -> tuple[int, str]:
        descriptor = self._directory_descriptor(directory)
        temporary = f".{name}.{os.getpid()}.{secrets.token_hex(8)}.tmp"
        temporary = _safe_name(temporary)
        file_descriptor = os.open(temporary, _WRITE_FLAGS, 0o600, dir_fd=descriptor)
        try:
            view = memoryview(payload)
            written = 0
            while written < len(view):
                count = os.write(file_descriptor, view[written:])
                if count <= 0:
                    raise OSError("checkpoint temporary write made no forward progress")
                written += count
            os.fsync(file_descriptor)
        except BaseException:
            os.close(file_descriptor)
            try:
                os.unlink(temporary, dir_fd=descriptor)
            except FileNotFoundError:
                pass
            raise
        return file_descriptor, temporary

    def atomic_create(self, name: str, payload: bytes, *, directory: str | None = None) -> None:
        """Create immutable evidence atomically; an existing name is never replaced."""

        name = _safe_name(name)
        self.verify_binding()
        descriptor = self._directory_descriptor(directory)
        temporary_descriptor = -1
        temporary = ""
        try:
            temporary_descriptor, temporary = self._write_temporary(
                name, payload, directory=directory
            )
            os.close(temporary_descriptor)
            temporary_descriptor = -1
            try:
                os.link(
                    temporary,
                    name,
                    src_dir_fd=descriptor,
                    dst_dir_fd=descriptor,
                    follow_symlinks=False,
                )
            except FileExistsError as exc:
                self._raise(
                    f"refusing to overwrite retained evidence: "
                    f"{self.display_path(name, directory=directory)}",
                    exc,
                )
            os.fsync(descriptor)
        except self._error_type:
            raise
        except OSError as exc:
            self._raise(
                f"cannot create retained checkpoint evidence: "
                f"{self.display_path(name, directory=directory)}",
                exc,
            )
        finally:
            if temporary_descriptor >= 0:
                os.close(temporary_descriptor)
            if temporary:
                try:
                    os.unlink(temporary, dir_fd=descriptor)
                except FileNotFoundError:
                    pass
                os.fsync(descriptor)
        self.verify_binding()

    def atomic_replace(self, name: str, payload: bytes, *, directory: str | None = None) -> None:
        """Replace derived state atomically without following an existing symlink."""

        name = _safe_name(name)
        self.verify_binding()
        descriptor = self._directory_descriptor(directory)
        try:
            info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
        except FileNotFoundError:
            info = None
        except OSError as exc:
            self._raise(f"cannot stat derived checkpoint output: {self.display_path(name)}", exc)
        if info is not None and not stat.S_ISREG(info.st_mode):
            self._raise(
                f"refusing to replace non-regular derived output: "
                f"{self.display_path(name, directory=directory)}"
            )
        temporary_descriptor = -1
        temporary = ""
        try:
            temporary_descriptor, temporary = self._write_temporary(
                name, payload, directory=directory
            )
            os.close(temporary_descriptor)
            temporary_descriptor = -1
            os.replace(
                temporary,
                name,
                src_dir_fd=descriptor,
                dst_dir_fd=descriptor,
            )
            temporary = ""
            os.fsync(descriptor)
        except self._error_type:
            raise
        except OSError as exc:
            self._raise(
                f"cannot replace derived checkpoint output: "
                f"{self.display_path(name, directory=directory)}",
                exc,
            )
        finally:
            if temporary_descriptor >= 0:
                os.close(temporary_descriptor)
            if temporary:
                try:
                    os.unlink(temporary, dir_fd=descriptor)
                except FileNotFoundError:
                    pass
            os.fsync(descriptor)
        self.verify_binding()

    def retain_exact(self, name: str, payload: bytes, *, directory: str | None = None) -> None:
        if self.regular_file_exists(name, directory=directory):
            if self.read_bytes(name, directory=directory) != payload:
                self._raise(
                    f"retained output differs from checkpoint evidence: "
                    f"{self.display_path(name, directory=directory)}"
                )
            return
        self.atomic_create(name, payload, directory=directory)

    def exclusive_lock(self) -> Iterator[None]:
        """Lock this exact stage inode for the duration of one active run."""

        stage = self

        class _LockContext:
            def __enter__(self) -> None:
                stage.verify_binding()
                if stage._locked:
                    stage._raise(f"checkpoint stage is already locked in this process: {stage.path}")
                try:
                    fcntl.flock(stage._stage_descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as exc:
                    stage._raise(f"another iter202 process owns {stage.path}", exc)
                stage._locked = True
                stage.verify_binding()

            def __exit__(
                self,
                exc_type: type[BaseException] | None,
                exc: BaseException | None,
                traceback: TracebackType | None,
            ) -> None:
                try:
                    # Do not mask an already-active exception, but make a clean
                    # exit prove that the named stage never changed underneath us.
                    if exc_type is None:
                        stage.verify_binding()
                finally:
                    try:
                        fcntl.flock(stage._stage_descriptor, fcntl.LOCK_UN)
                    except OSError:
                        if exc_type is None:
                            raise
                    finally:
                        stage._locked = False

        return _LockContext()
