#!/usr/bin/env python3
"""Validate and manually extract one verified Iter245 Python archive."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tarfile
from typing import BinaryIO


MAX_MEMBERS = 100_000
MAX_MEMBER_SIZE = 512 * 1024 * 1024
MAX_TOTAL_SIZE = 2 * 1024 * 1024 * 1024
MAX_PATH_BYTES = 4096
COPY_CHUNK_SIZE = 1024 * 1024


class ArchiveViolation(ValueError):
    """The verified archive violates the registered extraction contract."""


@dataclass(frozen=True)
class Entry:
    """One canonical archive member admitted by the structural preflight."""

    member: tarfile.TarInfo
    parts: tuple[str, ...]
    kind: str
    link_target: tuple[str, ...] | None = None


def _deny(message: str) -> None:
    raise ArchiveViolation(message)


def _printable_component(component: str, *, field: str) -> None:
    if not component:
        _deny(f"{field}_empty_component")
    try:
        encoded = component.encode("ascii")
    except UnicodeEncodeError:
        _deny(f"{field}_non_ascii")
    if any(byte < 0x20 or byte > 0x7E for byte in encoded):
        _deny(f"{field}_non_printable")
    if "/" in component or "\\" in component:
        _deny(f"{field}_separator")


def canonical_member_parts(name: str) -> tuple[str, ...]:
    """Return the normalized path from the frozen archive's exact ``./`` namespace."""

    if not isinstance(name, str) or not name:
        _deny("member_name_empty")
    if len(name.encode("utf-8", errors="surrogatepass")) > MAX_PATH_BYTES:
        _deny("member_name_too_long")
    if name.startswith("/") or "\\" in name:
        _deny("member_name_absolute_or_backslash")
    if name == ".":
        return ()
    if not name.startswith("./") or name.startswith("././"):
        _deny("member_name_wire_prefix")
    raw_parts = name[2:].split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        _deny("member_name_non_canonical")
    for part in raw_parts:
        _printable_component(part, field="member_name")
    return tuple(raw_parts)


def canonical_link_target(parent: tuple[str, ...], linkname: str) -> tuple[str, ...]:
    """Resolve one canonical relative link name inside the archive root."""

    if not isinstance(linkname, str) or not linkname:
        _deny("symlink_target_empty")
    if len(linkname.encode("utf-8", errors="surrogatepass")) > MAX_PATH_BYTES:
        _deny("symlink_target_too_long")
    if linkname.startswith("/") or "\\" in linkname:
        _deny("symlink_target_absolute_or_backslash")
    resolved = list(parent)
    for part in linkname.split("/"):
        if part in {"", ".", ".."}:
            _deny("symlink_target_non_canonical")
        _printable_component(part, field="symlink_target")
        resolved.append(part)
    if not resolved:
        _deny("symlink_target_root")
    return tuple(resolved)


def _entry_kind(member: tarfile.TarInfo) -> str:
    if member.pax_headers:
        _deny("pax_metadata_member")
    if member.type == tarfile.GNUTYPE_SPARSE or member.sparse is not None:
        _deny("sparse_member")
    if member.isdir():
        return "directory"
    if member.type in {tarfile.REGTYPE, tarfile.AREGTYPE}:
        return "regular"
    if member.issym():
        return "symlink"
    if member.islnk():
        _deny("hardlink_member")
    if member.ischr() or member.isblk() or member.isfifo():
        _deny("special_member")
    _deny("unknown_member_type")
    raise AssertionError("unreachable")


def inspect_archive(archive: tarfile.TarFile) -> dict[tuple[str, ...], Entry]:
    """Build the complete admitted inventory before writing any archive member."""

    inventory: dict[tuple[str, ...], Entry] = {}
    total_size = 0
    root_records = 0
    if archive.pax_headers:
        _deny("pax_global_metadata")
    members = archive.getmembers()
    if not members or len(members) > MAX_MEMBERS:
        _deny("archive_member_count")
    for member in members:
        parts = canonical_member_parts(member.name)
        kind = _entry_kind(member)
        if member.size < 0 or member.size > MAX_MEMBER_SIZE:
            _deny("archive_member_size")
        if kind != "regular" and member.size != 0:
            _deny("non_regular_member_has_data")
        total_size += member.size
        if total_size > MAX_TOTAL_SIZE:
            _deny("archive_total_size")
        if not parts:
            if kind != "directory":
                _deny("archive_root_not_directory")
            root_records += 1
            continue
        if parts in inventory:
            _deny("duplicate_member_path")
        link_target = None
        if kind == "symlink":
            link_target = canonical_link_target(parts[:-1], member.linkname)
        inventory[parts] = Entry(member, parts, kind, link_target)

    if root_records != 1:
        _deny("archive_root_record_count")

    for entry in inventory.values():
        for depth in range(1, len(entry.parts)):
            parent = inventory.get(entry.parts[:depth])
            if parent is not None and parent.kind != "directory":
                _deny("member_parent_not_directory")
        if entry.kind == "symlink":
            resolve_inventory_link(entry.parts, inventory)
    return inventory


def resolve_inventory_link(
    path: tuple[str, ...], inventory: dict[tuple[str, ...], Entry]
) -> tuple[str, ...]:
    """Resolve a link chain to a retained regular file or directory."""

    visited: set[tuple[str, ...]] = set()
    current = path
    while True:
        if current in visited:
            _deny("symlink_cycle")
        visited.add(current)
        entry = inventory.get(current)
        if entry is None:
            _deny("symlink_target_absent")
        if entry.kind != "symlink":
            return current
        assert entry.link_target is not None
        current = entry.link_target


def _destination(root: Path, parts: tuple[str, ...]) -> Path:
    candidate = root.joinpath(*parts)
    if PurePosixPath(candidate.relative_to(root).as_posix()).parts != parts:
        _deny("destination_path_differs")
    return candidate


def _ensure_real_directory(path: Path, *, uid: int) -> None:
    metadata = path.lstat()
    if not stat.S_ISDIR(metadata.st_mode) or path.is_symlink():
        _deny("extraction_parent_not_directory")
    if metadata.st_uid != uid:
        _deny("extraction_parent_foreign_owned")


def _ensure_parents(root: Path, parts: tuple[str, ...], *, uid: int) -> None:
    current = root
    for part in parts:
        current = current / part
        if not current.exists():
            current.mkdir(mode=0o700)
        _ensure_real_directory(current, uid=uid)


def _regular_mode(entry: Entry, *, python_version: str) -> int:
    major_minor = ".".join(python_version.split(".")[:2])
    if entry.parts == ("bin", f"python{major_minor}"):
        return 0o700
    return 0o600


def _copy_exact(source: BinaryIO, descriptor: int, expected: int) -> None:
    copied = 0
    with os.fdopen(descriptor, "wb", closefd=True) as destination:
        while True:
            chunk = source.read(COPY_CHUNK_SIZE)
            if not chunk:
                break
            copied += len(chunk)
            if copied > expected:
                _deny("regular_member_exceeds_declared_size")
            destination.write(chunk)
        destination.flush()
        if copied != expected:
            _deny("regular_member_size_differs")


def extract_archive(
    archive: tarfile.TarFile,
    inventory: dict[tuple[str, ...], Entry],
    root: Path,
    *,
    python_version: str,
) -> dict[str, int]:
    """Extract without tarfile.extract and without following archive links."""

    uid = os.geteuid()
    _validate_fresh_root(root)

    directories = [entry for entry in inventory.values() if entry.kind == "directory"]
    regulars = [entry for entry in inventory.values() if entry.kind == "regular"]
    symlinks: list[Entry] = []
    seen: set[tuple[str, ...]] = set()
    root_records = 0
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    if nofollow == 0:
        _deny("platform_lacks_no_follow")

    for streamed_member in archive:
        parts = canonical_member_parts(streamed_member.name)
        kind = _entry_kind(streamed_member)
        if not parts:
            if kind != "directory":
                _deny("streamed_archive_root_not_directory")
            root_records += 1
            continue
        expected = inventory.get(parts)
        if expected is None or parts in seen:
            _deny("streamed_inventory_differs")
        if (
            expected.kind != kind
            or expected.member.type != streamed_member.type
            or expected.member.size != streamed_member.size
            or stat.S_IMODE(expected.member.mode) != stat.S_IMODE(streamed_member.mode)
            or expected.member.linkname != streamed_member.linkname
        ):
            _deny("streamed_member_metadata_differs")
        seen.add(parts)
        entry = Entry(
            streamed_member,
            parts,
            kind,
            expected.link_target,
        )
        if kind == "directory":
            _ensure_parents(root, parts, uid=uid)
            continue
        if kind == "symlink":
            symlinks.append(entry)
            continue

        _ensure_parents(root, parts[:-1], uid=uid)
        destination = _destination(root, parts)
        source = archive.extractfile(streamed_member)
        if source is None:
            _deny("regular_member_unreadable")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | nofollow
        descriptor = os.open(destination, flags, 0o600)
        try:
            _copy_exact(source, descriptor, entry.member.size)
        finally:
            source.close()
        os.chmod(
            destination,
            _regular_mode(entry, python_version=python_version),
            follow_symlinks=False,
        )

    if root_records != 1 or seen != set(inventory):
        _deny("streamed_archive_inventory_incomplete")

    for entry in sorted(symlinks, key=lambda item: item.parts):
        _ensure_parents(root, entry.parts[:-1], uid=uid)
        destination = _destination(root, entry.parts)
        os.symlink(entry.member.linkname, destination)

    for entry in sorted(
        directories,
        key=lambda item: (len(item.parts), item.parts),
        reverse=True,
    ):
        destination = _destination(root, entry.parts)
        os.chmod(
            destination,
            0o700,
            follow_symlinks=False,
        )
    os.chmod(root, 0o700, follow_symlinks=False)

    validate_extracted_tree(root, python_version=python_version)
    return {
        "archive_member_count": len(inventory),
        "directory_count": len(directories),
        "regular_file_count": len(regulars),
        "symlink_count": len(symlinks),
        "uncompressed_regular_bytes": sum(entry.member.size for entry in regulars),
    }


def validate_extracted_tree(root: Path, *, python_version: str | None = None) -> None:
    """Recheck ownership, modes, entry types, and every realized link target."""

    uid = os.geteuid()
    root_resolved = root.resolve(strict=True)
    for current, directory_names, file_names in os.walk(root, followlinks=False):
        current_path = Path(current)
        for name in [".", *directory_names, *file_names]:
            path = current_path if name == "." else current_path / name
            metadata = path.lstat()
            if metadata.st_uid != uid:
                _deny("extracted_path_foreign_owned")
            if stat.S_ISLNK(metadata.st_mode):
                try:
                    resolved = path.resolve(strict=True)
                except (OSError, RuntimeError):
                    _deny("extracted_symlink_unresolvable")
                try:
                    resolved.relative_to(root_resolved)
                except ValueError:
                    _deny("extracted_symlink_escapes_root")
                terminal = resolved.stat()
                if not (stat.S_ISREG(terminal.st_mode) or stat.S_ISDIR(terminal.st_mode)):
                    _deny("extracted_symlink_terminal_type")
                continue
            if not (stat.S_ISREG(metadata.st_mode) or stat.S_ISDIR(metadata.st_mode)):
                _deny("extracted_path_special_type")
            mode = stat.S_IMODE(metadata.st_mode)
            if mode & 0o022:
                _deny("extracted_path_group_or_world_writable")
            if python_version is not None:
                relative = path.relative_to(root_resolved).parts
                major_minor = ".".join(python_version.split(".")[:2])
                expected_mode = (
                    0o700
                    if stat.S_ISDIR(metadata.st_mode) or relative == ("bin", f"python{major_minor}")
                    else 0o600
                )
                if mode != expected_mode:
                    _deny("extracted_path_mode_differs")


def _validate_root_owned_executable(path: Path, *, label: str) -> Path:
    try:
        resolved = path.resolve(strict=True)
        metadata = resolved.lstat()
    except OSError as exc:
        raise ArchiveViolation(f"{label}_unreadable") from exc
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != 0
        or stat.S_IMODE(metadata.st_mode) & 0o6022
        or stat.S_IMODE(metadata.st_mode) & stat.S_IXUSR == 0
    ):
        _deny(f"{label}_untrusted")
    current = resolved.parent
    while True:
        parent_metadata = current.lstat()
        if (
            not stat.S_ISDIR(parent_metadata.st_mode)
            or parent_metadata.st_uid != 0
            or stat.S_IMODE(parent_metadata.st_mode) & 0o022
        ):
            _deny(f"{label}_parent_untrusted")
        if current == current.parent:
            break
        current = current.parent
    return resolved


def _readelf(readelf: Path, *arguments: str) -> str:
    try:
        completed = subprocess.run(
            [str(readelf), *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
            env={
                "HOME": "/nonexistent",
                "LANG": "C",
                "LC_ALL": "C",
                "PATH": "/usr/bin:/bin",
            },
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ArchiveViolation("readelf_execution_failed") from exc
    if completed.returncode != 0:
        _deny("readelf_rejected_target")
    return completed.stdout


def validate_elf_boundary(root: Path, *, python_version: str) -> dict[str, object]:
    """Prove the direct libpython loader boundary without executing the target."""

    major_minor = ".".join(python_version.split(".")[:2])
    target = root / "bin" / f"python{major_minor}"
    try:
        target_metadata = target.lstat()
    except OSError as exc:
        raise ArchiveViolation("python_elf_unreadable") from exc
    if (
        not stat.S_ISREG(target_metadata.st_mode)
        or target_metadata.st_uid != os.geteuid()
        or stat.S_IMODE(target_metadata.st_mode) != 0o700
    ):
        _deny("python_elf_mode_or_owner")

    readelf = _validate_root_owned_executable(
        Path("/usr/bin/readelf"),
        label="readelf",
    )
    header = _readelf(readelf, "-hW", str(target))
    if (
        re.search(r"^\s*Class:\s+ELF64\s*$", header, re.MULTILINE) is None
        or re.search(
            r"^\s*Machine:\s+Advanced Micro Devices X86-64\s*$",
            header,
            re.MULTILINE,
        )
        is None
    ):
        _deny("python_elf_identity")

    dynamic = _readelf(readelf, "-dW", str(target))
    tags: dict[str, list[str]] = {}
    for match in re.finditer(
        r"\((?P<tag>[A-Z0-9_]+)\)\s+[^\n]*?\[(?P<value>[^\]\n]*)\]",
        dynamic,
    ):
        tags.setdefault(match.group("tag"), []).append(match.group("value"))
    if tags.get("RPATH"):
        _deny("python_elf_rpath_present")
    if any(tags.get(tag) for tag in ("AUDIT", "DEPAUDIT", "FILTER", "AUXILIARY")):
        _deny("python_elf_loader_authority_present")
    expected_prefix = f"/opt/hostedtoolcache/Python/{python_version}/x64"
    if tags.get("RUNPATH") != [f"{expected_prefix}/lib"]:
        _deny("python_elf_runpath_differs")
    needed = tags.get("NEEDED", [])
    expected_soname = f"libpython{major_minor}.so.1.0"
    if (
        needed.count(expected_soname) != 1
        or len(needed) != len(set(needed))
        or any(not name or "/" in name or "\\" in name for name in needed)
    ):
        _deny("python_elf_needed_differs")

    program = _readelf(readelf, "-lW", str(target))
    interpreters = re.findall(
        r"\[Requesting program interpreter:\s*([^\]\n]+)\]",
        program,
    )
    if interpreters != ["/lib64/ld-linux-x86-64.so.2"]:
        _deny("python_elf_interpreter_differs")
    _validate_root_owned_executable(
        Path(interpreters[0]),
        label="program_interpreter",
    )

    libpython = root / "lib" / expected_soname
    try:
        libpython_metadata = libpython.lstat()
    except OSError as exc:
        raise ArchiveViolation("contained_libpython_unreadable") from exc
    if (
        not stat.S_ISREG(libpython_metadata.st_mode)
        or libpython_metadata.st_uid != os.geteuid()
        or stat.S_IMODE(libpython_metadata.st_mode) != 0o600
    ):
        _deny("contained_libpython_mode_or_owner")
    return {
        "direct_needed_count": len(needed),
        "program_interpreter": interpreters[0],
        "rpath_present": False,
        "runpath": tags["RUNPATH"][0],
    }


def _hash_open_file(raw_archive: BinaryIO) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    while True:
        chunk = raw_archive.read(COPY_CHUNK_SIZE)
        if not chunk:
            break
        size += len(chunk)
        digest.update(chunk)
    return size, digest.hexdigest()


def _validate_fresh_root(root: Path) -> None:
    metadata = root.lstat()
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or root.is_symlink()
        or metadata.st_uid != os.geteuid()
        or stat.S_IMODE(metadata.st_mode) != 0o700
        or any(root.iterdir())
    ):
        _deny("extraction_root_not_fresh_owner_0700")


def _clear_destination(root: Path) -> None:
    """Remove only entries below the already validated private extraction root."""

    for current, directory_names, file_names in os.walk(
        root,
        topdown=False,
        followlinks=False,
    ):
        current_path = Path(current)
        for name in file_names:
            (current_path / name).unlink(missing_ok=False)
        for name in directory_names:
            path = current_path / name
            if path.is_symlink():
                path.unlink(missing_ok=False)
            else:
                path.rmdir()


def validate_and_extract(
    archive_path: Path,
    root: Path,
    *,
    python_version: str,
    expected_size: int,
    expected_sha256: str,
) -> dict[str, object]:
    if expected_size <= 0 or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None:
        _deny("archive_expected_identity_invalid")
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    if nofollow == 0:
        _deny("platform_lacks_no_follow")
    _validate_fresh_root(root)
    try:
        descriptor = os.open(archive_path, os.O_RDONLY | nofollow)
    except OSError as exc:
        raise ArchiveViolation("archive_open_failed") from exc
    try:
        with os.fdopen(descriptor, "rb", buffering=0) as raw_archive:
            before = os.fstat(raw_archive.fileno())
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_uid != os.geteuid()
                or stat.S_IMODE(before.st_mode) & 0o022
                or before.st_size != expected_size
            ):
                _deny("archive_descriptor_identity")
            observed_size, observed_sha256 = _hash_open_file(raw_archive)
            if observed_size != expected_size or observed_sha256 != expected_sha256:
                _deny("archive_descriptor_digest")
            raw_archive.seek(0)
            with tarfile.open(fileobj=raw_archive, mode="r:gz") as archive:
                inventory = inspect_archive(archive)
            raw_archive.seek(0)
            with tarfile.open(fileobj=raw_archive, mode="r|gz") as archive:
                observation = extract_archive(
                    archive,
                    inventory,
                    root,
                    python_version=python_version,
                )
            after = os.fstat(raw_archive.fileno())
            if (
                before.st_dev != after.st_dev
                or before.st_ino != after.st_ino
                or before.st_size != after.st_size
                or before.st_mtime_ns != after.st_mtime_ns
                or before.st_ctime_ns != after.st_ctime_ns
            ):
                _deny("archive_changed_during_extraction")
            raw_archive.seek(0)
            final_size, final_sha256 = _hash_open_file(raw_archive)
            if final_size != expected_size or final_sha256 != expected_sha256:
                _deny("archive_changed_during_extraction")
            observation.update(validate_elf_boundary(root, python_version=python_version))
            observation.update(
                {
                    "archive_sha256": observed_sha256,
                    "archive_size": observed_size,
                }
            )
            return observation
    except Exception as exc:
        try:
            _clear_destination(root)
        except OSError as cleanup_error:
            raise ArchiveViolation("failed_extraction_cleanup") from cleanup_error
        if isinstance(exc, (tarfile.TarError, EOFError)):
            raise ArchiveViolation("archive_parse_failed") from exc
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("--archive", type=Path)
    operation.add_argument("--validate-tree", type=Path)
    parser.add_argument("--archive-size", type=int)
    parser.add_argument("--archive-sha256")
    parser.add_argument("--destination", type=Path)
    parser.add_argument(
        "--python-version",
        choices=("3.11.15", "3.12.13"),
        required=True,
    )
    args = parser.parse_args()
    try:
        if args.archive is not None:
            if args.archive_size is None or args.archive_sha256 is None or args.destination is None:
                _deny("archive_operation_arguments")
            observation = validate_and_extract(
                args.archive,
                args.destination,
                python_version=args.python_version,
                expected_size=args.archive_size,
                expected_sha256=args.archive_sha256,
            )
        else:
            assert args.validate_tree is not None
            if (
                args.archive_size is not None
                or args.archive_sha256 is not None
                or args.destination is not None
            ):
                _deny("tree_operation_arguments")
            validate_extracted_tree(args.validate_tree, python_version=args.python_version)
            observation = validate_elf_boundary(
                args.validate_tree,
                python_version=args.python_version,
            )
    except (ArchiveViolation, OSError) as exc:
        print(f"iter245 archive extraction denied: {exc}", file=sys.stderr)
        return 2
    label = "archive extraction" if args.archive is not None else "retained tree validation"
    print(
        f"iter245 {label} observation="
        + json.dumps(observation, sort_keys=True, separators=(",", ":"))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
