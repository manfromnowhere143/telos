"""Known-good and known-bad controls for the Iter245 archive boundary."""

from __future__ import annotations

import hashlib
from io import BytesIO
import os
from pathlib import Path
import stat
import subprocess
import sys
import tarfile

import pytest

from scripts import extract_iter245_python as extractor
from scripts import validate_iter245_python_bootstrap as bootstrap_guard


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "scripts/bootstrap_iter245_python.sh"


def tar_member(
    name: str,
    *,
    kind: bytes = tarfile.REGTYPE,
    data: bytes = b"",
    mode: int = 0o777,
    linkname: str = "",
) -> tuple[tarfile.TarInfo, bytes]:
    member = tarfile.TarInfo(name)
    member.type = kind
    member.mode = mode
    member.linkname = linkname
    member.size = len(data) if kind in {tarfile.REGTYPE, tarfile.AREGTYPE} else 0
    return member, data


def write_archive(
    path: Path,
    entries: list[tuple[tarfile.TarInfo, bytes]],
    *,
    root_kind: bytes = tarfile.DIRTYPE,
    root_records: int = 1,
    archive_format: int = tarfile.GNU_FORMAT,
) -> None:
    root = tarfile.TarInfo(".")
    root.type = root_kind
    root.mode = 0o777
    with tarfile.open(path, "w:gz", format=archive_format) as archive:
        for _ in range(root_records):
            archive.addfile(root)
        for member, data in entries:
            archive.addfile(member, BytesIO(data) if member.isreg() else None)


def inspect(path: Path) -> dict[tuple[str, ...], extractor.Entry]:
    with tarfile.open(path, "r:gz") as archive:
        return extractor.inspect_archive(archive)


def safe_entries() -> list[tuple[tarfile.TarInfo, bytes]]:
    return [
        tar_member("./bin", kind=tarfile.DIRTYPE),
        tar_member("./lib", kind=tarfile.DIRTYPE),
        tar_member("./lib/python3.11", kind=tarfile.DIRTYPE),
        tar_member(
            "./bin/python3.11",
            data=b"ELF fixture\n",
        ),
        tar_member(
            "./bin/python3",
            kind=tarfile.SYMTYPE,
            linkname="python3.11",
        ),
        tar_member("./lib/python3.11/Lorem ipsum.txt", data=b"fixture\n"),
        tar_member("./setup.sh", data=b"#!/usr/bin/env bash\nexit 99\n"),
    ]


def destination(tmp_path: Path) -> Path:
    root = tmp_path / "destination"
    root.mkdir(mode=0o700)
    root.chmod(0o700)
    return root


def validate_fixture(
    archive: Path,
    root: Path,
    *,
    python_version: str = "3.11.15",
) -> dict[str, object]:
    return extractor.validate_and_extract(
        archive,
        root,
        python_version=python_version,
        expected_size=archive.stat().st_size,
        expected_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
    )


def test_frozen_wire_namespace_and_printable_space_are_admitted(
    tmp_path: Path,
) -> None:
    archive = tmp_path / "safe.tar.gz"
    write_archive(archive, safe_entries())
    inventory = inspect(archive)

    assert ("lib", "python3.11", "Lorem ipsum.txt") in inventory
    assert inventory[("bin", "python3")].link_target == ("bin", "python3.11")


def test_safe_archive_is_manually_extracted_with_normalized_modes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "safe.tar.gz"
    write_archive(archive, safe_entries())
    root = destination(tmp_path)
    monkeypatch.setattr(
        extractor,
        "validate_elf_boundary",
        lambda *_args, **_kwargs: {"elf_fixture": True},
    )

    observation = validate_fixture(archive, root)

    assert observation["elf_fixture"] is True
    assert stat.S_IMODE(root.stat().st_mode) == 0o700
    assert stat.S_IMODE((root / "bin/python3.11").stat().st_mode) == 0o700
    assert stat.S_IMODE((root / "setup.sh").stat().st_mode) == 0o600
    assert stat.S_IMODE((root / "lib/python3.11/Lorem ipsum.txt").stat().st_mode) == 0o600
    assert (root / "bin/python3").is_symlink()
    assert (root / "bin/python3").resolve() == (root / "bin/python3.11").resolve()


@pytest.mark.parametrize(
    "name",
    (
        "/absolute",
        "plain",
        "././repeated-dot",
        "./../escape",
        "./parent/../escape",
        "./empty//component",
        "./back\\slash",
        "./control\nname",
        "./non-ascii-é",
    ),
)
def test_unsafe_member_names_deny(tmp_path: Path, name: str) -> None:
    archive = tmp_path / "unsafe.tar.gz"
    write_archive(archive, [tar_member(name, data=b"x")])
    with pytest.raises(extractor.ArchiveViolation):
        inspect(archive)


def test_duplicate_normalized_member_denies(tmp_path: Path) -> None:
    archive = tmp_path / "duplicate.tar.gz"
    write_archive(
        archive,
        [
            tar_member("./duplicate", data=b"first"),
            tar_member("./duplicate", data=b"second"),
        ],
    )
    with pytest.raises(extractor.ArchiveViolation, match="duplicate_member_path"):
        inspect(archive)


@pytest.mark.parametrize(
    "target", ("./target", "dir//target", "dir/./target", "target/", "../target")
)
def test_noncanonical_symlink_target_denies(target: str) -> None:
    with pytest.raises(extractor.ArchiveViolation, match="symlink_target_non_canonical"):
        extractor.canonical_link_target(("bin",), target)


def test_gnu_longname_and_longlink_transport_are_normalized(tmp_path: Path) -> None:
    long_name = "x" * 160
    archive = tmp_path / "gnu-long.tar.gz"
    write_archive(
        archive,
        [
            tar_member(f"./{long_name}", data=b"retained\n"),
            tar_member("./link", kind=tarfile.SYMTYPE, linkname=long_name),
        ],
    )

    inventory = inspect(archive)
    assert (long_name,) in inventory
    assert inventory[("link",)].link_target == (long_name,)


def test_pax_metadata_denies(tmp_path: Path) -> None:
    archive = tmp_path / "pax.tar.gz"
    member, data = tar_member("./pax", data=b"fixture")
    member.pax_headers = {"comment": "unregistered"}
    write_archive(
        archive,
        [(member, data)],
        archive_format=tarfile.PAX_FORMAT,
    )
    with pytest.raises(extractor.ArchiveViolation, match="pax_"):
        inspect(archive)


def test_gnu_sparse_member_denies() -> None:
    member = tarfile.TarInfo("./sparse")
    member.type = tarfile.GNUTYPE_SPARSE
    with pytest.raises(extractor.ArchiveViolation, match="sparse_member"):
        extractor._entry_kind(member)


@pytest.mark.parametrize(
    "kind",
    (
        tarfile.LNKTYPE,
        tarfile.CHRTYPE,
        tarfile.BLKTYPE,
        tarfile.FIFOTYPE,
        tarfile.CONTTYPE,
        b"Z",
    ),
)
def test_hardlink_special_and_unknown_members_deny(tmp_path: Path, kind: bytes) -> None:
    archive = tmp_path / "special.tar.gz"
    write_archive(
        archive,
        [tar_member("./special", kind=kind, linkname="target")],
    )
    with pytest.raises(extractor.ArchiveViolation):
        inspect(archive)


@pytest.mark.parametrize("target", ("/outside", "../../outside", ""))
def test_absolute_escaping_and_empty_symlink_targets_deny(tmp_path: Path, target: str) -> None:
    archive = tmp_path / "link.tar.gz"
    write_archive(
        archive,
        [
            tar_member("./bin", kind=tarfile.DIRTYPE),
            tar_member(
                "./bin/python3",
                kind=tarfile.SYMTYPE,
                linkname=target,
            ),
        ],
    )
    with pytest.raises(extractor.ArchiveViolation):
        inspect(archive)


def test_absent_symlink_terminal_denies(tmp_path: Path) -> None:
    archive = tmp_path / "absent.tar.gz"
    write_archive(
        archive,
        [
            tar_member("./bin", kind=tarfile.DIRTYPE),
            tar_member(
                "./bin/python3",
                kind=tarfile.SYMTYPE,
                linkname="missing",
            ),
        ],
    )
    with pytest.raises(extractor.ArchiveViolation, match="symlink_target_absent"):
        inspect(archive)


def test_symlink_cycle_denies(tmp_path: Path) -> None:
    archive = tmp_path / "cycle.tar.gz"
    write_archive(
        archive,
        [
            tar_member("./a", kind=tarfile.SYMTYPE, linkname="b"),
            tar_member("./b", kind=tarfile.SYMTYPE, linkname="a"),
        ],
    )
    with pytest.raises(extractor.ArchiveViolation, match="symlink_cycle"):
        inspect(archive)


def test_member_cannot_descend_through_archive_symlink(tmp_path: Path) -> None:
    archive = tmp_path / "prefix.tar.gz"
    write_archive(
        archive,
        [
            tar_member("./real", kind=tarfile.DIRTYPE),
            tar_member("./alias", kind=tarfile.SYMTYPE, linkname="real"),
            tar_member("./alias/file", data=b"escape attempt"),
        ],
    )
    with pytest.raises(extractor.ArchiveViolation, match="member_parent_not_directory"):
        inspect(archive)


def test_declared_size_and_inventory_limits_deny(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "limits.tar.gz"
    write_archive(archive, [tar_member("./large", data=b"xx")])
    monkeypatch.setattr(extractor, "MAX_MEMBER_SIZE", 1)
    with pytest.raises(extractor.ArchiveViolation, match="archive_member_size"):
        inspect(archive)


def test_member_count_limit_denies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    archive = tmp_path / "count.tar.gz"
    write_archive(archive, [tar_member("./one", data=b"1")])
    monkeypatch.setattr(extractor, "MAX_MEMBERS", 1)
    with pytest.raises(extractor.ArchiveViolation, match="archive_member_count"):
        inspect(archive)


def test_total_size_limit_denies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    archive = tmp_path / "total.tar.gz"
    write_archive(archive, [tar_member("./two", data=b"12")])
    monkeypatch.setattr(extractor, "MAX_TOTAL_SIZE", 1)
    with pytest.raises(extractor.ArchiveViolation, match="archive_total_size"):
        inspect(archive)


def test_root_record_must_be_directory(tmp_path: Path) -> None:
    archive = tmp_path / "root.tar.gz"
    write_archive(archive, [], root_kind=tarfile.REGTYPE)
    with pytest.raises(extractor.ArchiveViolation, match="archive_root_not_directory"):
        inspect(archive)


def test_root_record_with_payload_denies_before_inventory_acceptance() -> None:
    root = tarfile.TarInfo(".")
    root.type = tarfile.DIRTYPE
    root.size = 1

    class ArchiveFixture:
        pax_headers: dict[str, str] = {}

        @staticmethod
        def getmembers() -> list[tarfile.TarInfo]:
            return [root]

    with pytest.raises(extractor.ArchiveViolation, match="non_regular_member_has_data"):
        extractor.inspect_archive(ArchiveFixture())


@pytest.mark.parametrize("root_records", (0, 2))
def test_root_record_count_denies_before_destination_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    root_records: int,
) -> None:
    archive = tmp_path / "root-count.tar.gz"
    write_archive(
        archive,
        [tar_member("./retained", data=b"fixture")],
        root_records=root_records,
    )
    root = destination(tmp_path)
    monkeypatch.setattr(extractor, "validate_elf_boundary", lambda *_a, **_k: {})
    with pytest.raises(extractor.ArchiveViolation, match="archive_root_record_count"):
        validate_fixture(archive, root)
    assert list(root.iterdir()) == []


def test_wrong_same_descriptor_digest_denies_before_write(tmp_path: Path) -> None:
    archive = tmp_path / "digest.tar.gz"
    write_archive(archive, [tar_member("./retained", data=b"fixture")])
    root = destination(tmp_path)
    with pytest.raises(extractor.ArchiveViolation, match="archive_descriptor_digest"):
        extractor.validate_and_extract(
            archive,
            root,
            python_version="3.11.15",
            expected_size=archive.stat().st_size,
            expected_sha256="0" * 64,
        )
    assert list(root.iterdir()) == []


def test_parser_uses_authenticated_descriptor_after_path_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive = tmp_path / "authenticated.tar.gz"
    replacement = tmp_path / "replacement.tar.gz"
    write_archive(archive, safe_entries())
    write_archive(replacement, [], root_records=0)
    expected_size = archive.stat().st_size
    expected_sha256 = hashlib.sha256(archive.read_bytes()).hexdigest()
    root = destination(tmp_path)
    real_open = extractor.os.open
    swapped = False

    def replace_after_open(path, flags, *args, **kwargs):
        nonlocal swapped
        descriptor = real_open(path, flags, *args, **kwargs)
        if not swapped and os.fspath(path) == os.fspath(archive):
            replacement.replace(archive)
            swapped = True
        return descriptor

    monkeypatch.setattr(extractor.os, "open", replace_after_open)
    monkeypatch.setattr(
        extractor,
        "validate_elf_boundary",
        lambda *_a, **_k: {"elf_fixture": True},
    )
    observation = extractor.validate_and_extract(
        archive,
        root,
        python_version="3.11.15",
        expected_size=expected_size,
        expected_sha256=expected_sha256,
    )

    assert swapped is True
    assert observation["archive_sha256"] == expected_sha256
    assert (root / "setup.sh").read_bytes().startswith(b"#!/usr/bin/env bash")


def test_archive_symlink_is_denied_without_writing(tmp_path: Path) -> None:
    archive = tmp_path / "archive.tar.gz"
    alias = tmp_path / "alias.tar.gz"
    write_archive(archive, safe_entries())
    alias.symlink_to(archive.name)
    root = destination(tmp_path)
    with pytest.raises(extractor.ArchiveViolation, match="archive_open_failed"):
        extractor.validate_and_extract(
            alias,
            root,
            python_version="3.11.15",
            expected_size=archive.stat().st_size,
            expected_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        )
    assert list(root.iterdir()) == []


def test_nonfresh_destination_is_denied_without_deleting_it(tmp_path: Path) -> None:
    archive = tmp_path / "safe.tar.gz"
    write_archive(archive, safe_entries())
    root = destination(tmp_path)
    retained = root / "preexisting"
    retained.write_bytes(b"must remain")
    retained.chmod(0o600)
    with pytest.raises(
        extractor.ArchiveViolation,
        match="extraction_root_not_fresh_owner_0700",
    ):
        validate_fixture(archive, root)
    assert retained.read_bytes() == b"must remain"


def test_truncated_archive_denies_and_cleans_destination(tmp_path: Path) -> None:
    archive = tmp_path / "truncated.tar.gz"
    archive.write_bytes(b"\x1f\x8b\x08\x00truncated")
    archive.chmod(0o600)
    root = destination(tmp_path)
    with pytest.raises(extractor.ArchiveViolation, match="archive_parse_failed"):
        validate_fixture(archive, root)
    assert list(root.iterdir()) == []


def test_extracted_tree_rejects_writable_file(tmp_path: Path) -> None:
    root = destination(tmp_path)
    writable = root / "writable"
    writable.write_bytes(b"fixture")
    writable.chmod(0o666)
    with pytest.raises(
        extractor.ArchiveViolation,
        match="extracted_path_group_or_world_writable",
    ):
        extractor.validate_extracted_tree(root)


GOOD_ELF_HEADER = (
    "  Class:                             ELF64\n"
    "  Machine:                           Advanced Micro Devices X86-64\n"
)
GOOD_ELF_DYNAMIC = (
    " 0x1 (NEEDED) Shared library: [libpython3.11.so.1.0]\n"
    " 0x1 (NEEDED) Shared library: [libc.so.6]\n"
    " 0x1 (RUNPATH) Library runpath: "
    "[/opt/hostedtoolcache/Python/3.11.15/x64/lib]\n"
)
GOOD_ELF_PROGRAM = "[Requesting program interpreter: /lib64/ld-linux-x86-64.so.2]\n"


def elf_root(tmp_path: Path) -> Path:
    root = destination(tmp_path)
    (root / "bin").mkdir(mode=0o700)
    (root / "lib").mkdir(mode=0o700)
    target = root / "bin/python3.11"
    target.write_bytes(b"ELF")
    target.chmod(0o700)
    library = root / "lib/libpython3.11.so.1.0"
    library.write_bytes(b"ELF library")
    library.chmod(0o600)
    return root


def install_fake_readelf(
    monkeypatch: pytest.MonkeyPatch,
    *,
    header: str = GOOD_ELF_HEADER,
    dynamic: str = GOOD_ELF_DYNAMIC,
    program: str = GOOD_ELF_PROGRAM,
) -> None:
    monkeypatch.setattr(
        extractor,
        "_validate_root_owned_executable",
        lambda path, *, label: path,
    )

    def fake_readelf(_tool: Path, *arguments: str) -> str:
        if "-hW" in arguments:
            return header
        if "-dW" in arguments:
            return dynamic
        return program

    monkeypatch.setattr(extractor, "_readelf", fake_readelf)


def test_elf_boundary_accepts_exact_static_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = elf_root(tmp_path)
    install_fake_readelf(monkeypatch)
    observation = extractor.validate_elf_boundary(root, python_version="3.11.15")

    assert observation["rpath_present"] is False
    assert observation["direct_needed_count"] == 2


@pytest.mark.parametrize(
    ("dynamic", "expected"),
    (
        (
            " 0x1 (RPATH) Library rpath: [/opt/hostedtoolcache/Python/3.11.15/x64/lib]\n"
            " 0x1 (NEEDED) Shared library: [libpython3.11.so.1.0]\n",
            "rpath_present",
        ),
        (
            " 0x1 (RUNPATH) Library runpath: [/wrong/lib]\n"
            " 0x1 (NEEDED) Shared library: [libpython3.11.so.1.0]\n",
            "runpath_differs",
        ),
        (
            " 0x1 (RUNPATH) Library runpath: "
            "[/opt/hostedtoolcache/Python/3.11.15/x64/lib]\n"
            " 0x1 (NEEDED) Shared library: [/outside/libpython3.11.so.1.0]\n",
            "needed_differs",
        ),
        (
            " 0x1 (NEEDED) Shared library: [libpython3.11.so.1.0]\n",
            "runpath_differs",
        ),
        (
            " 0x1 (RUNPATH) Library runpath: "
            "[/opt/hostedtoolcache/Python/3.11.15/x64/lib]\n"
            " 0x1 (RUNPATH) Library runpath: "
            "[/opt/hostedtoolcache/Python/3.11.15/x64/lib]\n"
            " 0x1 (NEEDED) Shared library: [libpython3.11.so.1.0]\n",
            "runpath_differs",
        ),
        (
            " 0x1 (RUNPATH) Library runpath: "
            "[/opt/hostedtoolcache/Python/3.11.15/x64/lib]\n"
            " 0x1 (NEEDED) Shared library: [libpython3.11.so.1.0]\n"
            " 0x1 (NEEDED) Shared library: [libpython3.11.so.1.0]\n",
            "needed_differs",
        ),
        (
            GOOD_ELF_DYNAMIC + " 0x6ffffefc (AUDIT) Audit library: [libunregistered.so]\n",
            "loader_authority_present",
        ),
    ),
)
def test_elf_boundary_known_bad_dynamic_tags_deny(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dynamic: str,
    expected: str,
) -> None:
    root = elf_root(tmp_path)
    install_fake_readelf(monkeypatch, dynamic=dynamic)
    with pytest.raises(extractor.ArchiveViolation, match=expected):
        extractor.validate_elf_boundary(root, python_version="3.11.15")


@pytest.mark.parametrize(
    "header",
    (
        "Class: ELF32\nMachine: Advanced Micro Devices X86-64\n",
        "Class: ELF64\nMachine: AArch64\n",
        "",
    ),
)
def test_elf_boundary_wrong_identity_denies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    header: str,
) -> None:
    root = elf_root(tmp_path)
    install_fake_readelf(monkeypatch, header=header)
    with pytest.raises(extractor.ArchiveViolation, match="python_elf_identity"):
        extractor.validate_elf_boundary(root, python_version="3.11.15")


@pytest.mark.parametrize(
    "program",
    (
        "",
        "[Requesting program interpreter: /wrong/loader]\n",
        GOOD_ELF_PROGRAM + GOOD_ELF_PROGRAM,
    ),
)
def test_elf_boundary_wrong_interpreter_denies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    program: str,
) -> None:
    root = elf_root(tmp_path)
    install_fake_readelf(monkeypatch, program=program)
    with pytest.raises(extractor.ArchiveViolation, match="python_elf_interpreter_differs"):
        extractor.validate_elf_boundary(root, python_version="3.11.15")


@pytest.mark.parametrize("mode", (None, 0o666))
def test_elf_boundary_missing_or_writable_libpython_denies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: int | None,
) -> None:
    root = elf_root(tmp_path)
    library = root / "lib/libpython3.11.so.1.0"
    if mode is None:
        library.unlink()
        expected = "contained_libpython_unreadable"
    else:
        library.chmod(mode)
        expected = "contained_libpython_mode_or_owner"
    install_fake_readelf(monkeypatch)
    with pytest.raises(extractor.ArchiveViolation, match=expected):
        extractor.validate_elf_boundary(root, python_version="3.11.15")


def test_elf_boundary_untrusted_readelf_denies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = elf_root(tmp_path)

    def deny_readelf(path: Path, *, label: str) -> Path:
        raise extractor.ArchiveViolation(f"{label}_untrusted")

    monkeypatch.setattr(extractor, "_validate_root_owned_executable", deny_readelf)
    with pytest.raises(extractor.ArchiveViolation, match="readelf_untrusted"):
        extractor.validate_elf_boundary(root, python_version="3.11.15")


def test_elf_boundary_untrusted_registered_interpreter_denies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = elf_root(tmp_path)

    def validate_platform_path(path: Path, *, label: str) -> Path:
        if label == "program_interpreter":
            raise extractor.ArchiveViolation("program_interpreter_untrusted")
        return path

    monkeypatch.setattr(
        extractor,
        "_validate_root_owned_executable",
        validate_platform_path,
    )

    def fake_readelf(_tool: Path, *arguments: str) -> str:
        if "-hW" in arguments:
            return GOOD_ELF_HEADER
        if "-dW" in arguments:
            return GOOD_ELF_DYNAMIC
        return GOOD_ELF_PROGRAM

    monkeypatch.setattr(extractor, "_readelf", fake_readelf)
    with pytest.raises(extractor.ArchiveViolation, match="program_interpreter_untrusted"):
        extractor.validate_elf_boundary(root, python_version="3.11.15")


def guard_inputs() -> tuple[bytes, bytes, bytes, bytes]:
    return (
        bootstrap_guard.BOOTSTRAP.read_bytes(),
        bootstrap_guard.EXTRACTOR.read_bytes(),
        bootstrap_guard.WORKFLOW.read_bytes(),
        bootstrap_guard.VALIDATOR.read_bytes(),
    )


def replace_once(raw: bytes, old: bytes, new: bytes) -> bytes:
    assert raw.count(old) == 1, old
    return raw.replace(old, new, 1)


def replace_first(raw: bytes, old: bytes, new: bytes) -> bytes:
    assert old in raw, old
    return raw.replace(old, new, 1)


def test_static_source_contract_guard_accepts_exact_current_inputs() -> None:
    bootstrap_raw, extractor_raw, workflow_raw, validator_raw = guard_inputs()
    assert (
        bootstrap_guard.validation_errors(
            bootstrap_raw,
            extractor_raw,
            workflow_raw,
            validator_raw=validator_raw,
            bootstrap_mode=bootstrap_guard.BOOTSTRAP.stat().st_mode,
            extractor_mode=bootstrap_guard.EXTRACTOR.stat().st_mode,
            validator_mode=bootstrap_guard.VALIDATOR.stat().st_mode,
        )
        == []
    )


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    (
        (
            b"/usr/bin/env -i HOME=/nonexistent",
            b"/usr/bin/env    HOME=/nonexistent",
            "environment isolation count differs",
        ),
        (
            b'LD_LIBRARY_PATH="$python_root/lib"',
            b'LD_LIBRARY_PATH="/unregistered/lib"',
            "loader binding count differs",
        ),
        (
            b"    printf 'ANTHROPIC_API_KEY=\\n'\n",
            b"",
            "bootstrap control absent",
        ),
    ),
)
def test_static_guard_rejects_bootstrap_boundary_mutations(
    old: bytes,
    new: bytes,
    expected: str,
) -> None:
    bootstrap_raw, _, _, _ = guard_inputs()
    errors = bootstrap_guard.bootstrap_errors(replace_first(bootstrap_raw, old, new))
    assert any(expected in error for error in errors), errors


def test_static_guard_rejects_manual_extraction_mutation() -> None:
    _, extractor_raw, _, _ = guard_inputs()
    mutated = replace_once(
        extractor_raw,
        b"os.O_WRONLY | os.O_CREAT | os.O_EXCL | nofollow",
        b"os.O_WRONLY | os.O_CREAT | os.O_TRUNC | nofollow",
    )
    errors = bootstrap_guard.extractor_errors(mutated)
    assert any("extractor control absent: os.O_EXCL" in error for error in errors)


def test_workflow_binding_rejects_mutated_validator_source() -> None:
    _, _, workflow_raw, validator_raw = guard_inputs()
    errors = bootstrap_guard.workflow_errors(
        workflow_raw,
        validator_raw=validator_raw + b"# weakened\n",
    )
    assert "workflow bootstrap command differs" in errors


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    (
        (
            b"      - name: Iter245 offline verified Python bootstrap guard\n",
            b"      - name: Iter245 offline verified Python bootstrap guard\n"
            b"        continue-on-error: true\n",
            "workflow step failure or environment semantics differ",
        ),
        (
            b"    steps:\n",
            b"    steps:\n"
            b"      - uses: actions/setup-python@1111111111111111111111111111111111111111\n",
            "workflow action set or order differs",
        ),
        (
            b"  verify:\n",
            b"  verify:\n    env:\n      GH_TOKEN: ${{ github.token }}\n",
            "workflow job failure or environment authority differs",
        ),
        (
            b"      - name: Bootstrap offline verified Python\n",
            b"      - name: Bootstrap offline verified Python\n        shell: bash\n",
            "workflow step failure or environment semantics differ",
        ),
    ),
)
def test_static_guard_rejects_workflow_authority_mutations(
    old: bytes,
    new: bytes,
    expected: str,
) -> None:
    _, _, workflow_raw, validator_raw = guard_inputs()
    errors = bootstrap_guard.workflow_errors(
        replace_once(workflow_raw, old, new),
        validator_raw=validator_raw,
    )
    assert any(expected in error for error in errors), errors


@pytest.mark.parametrize("matrix", ("3.11", "3.12"))
def test_bootstrap_contract_is_available_without_platform_execution(matrix: str) -> None:
    result = subprocess.run(
        [str(BOOTSTRAP), "--contract", matrix],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith(matrix + ".")


def test_bootstrap_unknown_matrix_denies() -> None:
    result = subprocess.run(
        [str(BOOTSTRAP), "--contract", "3.13"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "unsupported_matrix_version" in result.stderr


def test_shell_denial_cannot_fall_through_command_substitution() -> None:
    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"\n'
            'probe() { deny forced_predicate; printf "bypass\\n"; }\n'
            'value=""\n'
            "if value=$(probe); then exit 99; fi\n"
            "[[ $value != *bypass* ]]\n",
            "bash",
            str(BOOTSTRAP),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "forced_predicate" in result.stderr
    assert "bypass" not in result.stdout


def run_shell_extractor(source: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"\nrun_authenticated_extractor "$2" "$3" --help\n',
            "bash",
            str(BOOTSTRAP),
            sys.executable,
            str(source),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_shell_executes_same_descriptor_authenticated_extractor_source() -> None:
    result = run_shell_extractor(ROOT / "scripts/extract_iter245_python.py")
    assert result.returncode == 0, result.stderr
    assert "--validate-tree" in result.stdout


def test_shell_rejects_mutated_extractor_source(tmp_path: Path) -> None:
    source = tmp_path / "mutated-extractor.py"
    source.write_bytes((ROOT / "scripts/extract_iter245_python.py").read_bytes() + b"# mutation\n")
    source.chmod(0o700)
    result = run_shell_extractor(source)
    assert result.returncode != 0
    assert "source digest" in result.stderr


def test_bootstrap_sources_are_owner_executable_regular_files() -> None:
    for path in (BOOTSTRAP, ROOT / "scripts/extract_iter245_python.py"):
        metadata = path.stat()
        assert stat.S_ISREG(metadata.st_mode)
        assert metadata.st_mode & stat.S_IXUSR
        assert metadata.st_uid == os.geteuid()
