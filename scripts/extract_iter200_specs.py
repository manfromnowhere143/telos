#!/usr/bin/env python3
"""Extract official eval specs for every neutral-solve model patch.

Certification must precede the optional gold-differential witness. Exact-gold patches and patches for
which scenario generation failed still enter the official-harness denominator. Run with a
swebench-equipped Python. Commit eval scripts and spec JSON so CI stays hermetic.
"""

from __future__ import annotations

import base64
from collections import Counter
import csv
import hashlib
from importlib import metadata, util
import io
import json
import os
import re
from pathlib import Path, PurePosixPath
import stat
import sys
from types import ModuleType
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / os.environ.get("TELOS_NAT_EXP", "iter200_natural_certified_yet_wrong_rate")
OUT = EXP / "proof" / "raw" / "specs"
SCEN = EXP / "proof" / "raw" / "scenarios"
SNAPSHOT = ROOT / "experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/swebench_verified_rows_snapshot.json"
EXPECTED_SWEBENCH_VERSION = "4.1.0"
SWEBENCH_WHEEL = "swebench-4.1.0-py3-none-any.whl"
SWEBENCH_WHEEL_SHA256 = "1243776f720047cc9e20a427f7a52b75c13a07abda6154fb60fe77f82ec8af57"
SWEBENCH_LOCK = "requirements/iter200-swebench.txt"
SWEBENCH_LOCK_SHA256 = "70d0525fa3a238b9ce51b256883473cac92dd486299f47f003ac2388bb241f19"
SWEBENCH_LOCK_ENTRY_COUNT = 73
SWEBENCH_PYTHON_VERSION = "3.11.15"
SWEBENCH_DIST_INFO = "swebench-4.1.0.dist-info"
SWEBENCH_RECORD = f"{SWEBENCH_DIST_INFO}/RECORD"
SWEBENCH_WHEEL_MAX_BYTES = 16 * 1024 * 1024
SWEBENCH_WHEEL_MAX_UNCOMPRESSED_BYTES = 64 * 1024 * 1024
WHEELHOUSE_MEMBER_MAX_BYTES = 256 * 1024 * 1024
LOCK_PACKAGE_RE = re.compile(
    r"^([a-z0-9]+(?:-[a-z0-9]+)*)==([^\s\\]+)\s*\\$"
)
LOCK_HASH_RE = re.compile(r"^\s*--hash=sha256:([0-9a-f]{64})(\s*\\)?\s*$")
INSTALLER_DIST_INFO_EXTRAS = {
    f"{SWEBENCH_DIST_INFO}/INSTALLER": b"pip\n",
    f"{SWEBENCH_DIST_INFO}/REQUESTED": b"",
}
INSTALLER_DISTRIBUTION_ALLOWLIST = {"pip", "setuptools"}
ITER202_EXP = "iter202_natural_rate_scaled"

sys.path.insert(0, str(ROOT))
from scripts import run_iter200_scenarios as iter202_stages  # noqa: E402
from scripts.validate_iter202_runtime_freeze import (  # noqa: E402
    RuntimeFreezeError,
    require_valid_runtime_freeze,
)


class SwebenchProvenanceError(ValueError):
    """The installed spec generator is not the frozen wheel payload."""


def _normalize_distribution_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _assert_no_symlink_components(path: Path) -> None:
    if not path.is_absolute() or ".." in path.parts:
        raise SwebenchProvenanceError(f"path must be absolute and canonical: {path}")
    cursor = Path(path.anchor)
    for part in path.parts[1:]:
        cursor /= part
        try:
            mode = os.lstat(cursor).st_mode
        except OSError as exc:
            raise SwebenchProvenanceError(f"cannot lstat provenance path {cursor}: {exc}") from exc
        if stat.S_ISLNK(mode):
            raise SwebenchProvenanceError(f"symlink forbidden in provenance path: {cursor}")


def _read_regular_nofollow(path: Path, *, max_bytes: int | None = None) -> bytes:
    """Read one stable regular file while refusing symlinks and path swaps."""

    _assert_no_symlink_components(path)
    try:
        before = os.lstat(path)
    except OSError as exc:
        raise SwebenchProvenanceError(f"cannot lstat provenance file {path}: {exc}") from exc
    if not stat.S_ISREG(before.st_mode):
        raise SwebenchProvenanceError(f"provenance input is not a regular file: {path}")
    if max_bytes is not None and before.st_size > max_bytes:
        raise SwebenchProvenanceError(f"provenance input exceeds byte limit: {path}")
    if not hasattr(os, "O_NOFOLLOW"):
        raise SwebenchProvenanceError("O_NOFOLLOW is required for provenance verification")
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise SwebenchProvenanceError(f"cannot securely open provenance file {path}: {exc}") from exc
    try:
        opened_before = os.fstat(descriptor)
        if not stat.S_ISREG(opened_before.st_mode) or not os.path.samestat(
            before, opened_before
        ):
            raise SwebenchProvenanceError(f"provenance file changed before open: {path}")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if max_bytes is not None and total > max_bytes:
                raise SwebenchProvenanceError(f"provenance input exceeds byte limit: {path}")
            chunks.append(chunk)
        opened_after = os.fstat(descriptor)
        stable_fields_before = (
            opened_before.st_dev,
            opened_before.st_ino,
            opened_before.st_size,
            opened_before.st_mtime_ns,
            opened_before.st_ctime_ns,
        )
        stable_fields_after = (
            opened_after.st_dev,
            opened_after.st_ino,
            opened_after.st_size,
            opened_after.st_mtime_ns,
            opened_after.st_ctime_ns,
        )
        if stable_fields_before != stable_fields_after or total != opened_after.st_size:
            raise SwebenchProvenanceError(f"provenance file changed while read: {path}")
    finally:
        os.close(descriptor)
    try:
        after = os.lstat(path)
    except OSError as exc:
        raise SwebenchProvenanceError(f"cannot re-lstat provenance file {path}: {exc}") from exc
    if not os.path.samestat(opened_after, after):
        raise SwebenchProvenanceError(f"provenance path changed after read: {path}")
    return b"".join(chunks)


def _require_directory_nofollow(path: Path) -> None:
    _assert_no_symlink_components(path)
    try:
        mode = os.lstat(path).st_mode
    except OSError as exc:
        raise SwebenchProvenanceError(f"cannot lstat provenance directory {path}: {exc}") from exc
    if not stat.S_ISDIR(mode):
        raise SwebenchProvenanceError(f"provenance path is not a directory: {path}")


def _parse_locked_environment(raw: bytes) -> dict[str, tuple[str, tuple[str, ...]]]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SwebenchProvenanceError(f"swebench lock is not UTF-8: {exc}") from exc
    lines = [line for line in text.splitlines() if line and not line.startswith("#")]
    locked: dict[str, tuple[str, tuple[str, ...]]] = {}
    index = 0
    while index < len(lines):
        package_match = LOCK_PACKAGE_RE.fullmatch(lines[index])
        if package_match is None:
            raise SwebenchProvenanceError(
                f"invalid swebench lock block at logical line {index + 1}"
            )
        name, version = package_match.groups()
        if name in locked:
            raise SwebenchProvenanceError(f"duplicate swebench lock package: {name}")
        index += 1
        hashes: list[str] = []
        terminated = False
        while index < len(lines):
            hash_match = LOCK_HASH_RE.fullmatch(lines[index])
            if hash_match is None:
                break
            hashes.append(hash_match.group(1))
            index += 1
            if hash_match.group(2) is None:
                terminated = True
                break
        if not hashes or not terminated or hashes != sorted(set(hashes)):
            raise SwebenchProvenanceError(
                f"invalid swebench wheel hash set for locked package {name}"
            )
        locked[name] = (version, tuple(hashes))
    if list(locked) != sorted(locked):
        raise SwebenchProvenanceError("swebench lock packages are not sorted")
    if len(locked) != SWEBENCH_LOCK_ENTRY_COUNT:
        raise SwebenchProvenanceError(
            "swebench lock package count changed: "
            f"expected {SWEBENCH_LOCK_ENTRY_COUNT}, got {len(locked)}"
        )
    expected_swebench = (
        EXPECTED_SWEBENCH_VERSION,
        (SWEBENCH_WHEEL_SHA256,),
    )
    if locked.get("swebench") != expected_swebench:
        raise SwebenchProvenanceError("swebench wheel pin changed inside dependency lock")
    return locked


def _locked_environment() -> dict[str, tuple[str, tuple[str, ...]]]:
    raw = _read_regular_nofollow(ROOT / SWEBENCH_LOCK, max_bytes=1024 * 1024)
    actual = hashlib.sha256(raw).hexdigest()
    if actual != SWEBENCH_LOCK_SHA256:
        raise SwebenchProvenanceError(
            f"swebench lock SHA-256 mismatch: expected {SWEBENCH_LOCK_SHA256}, got {actual}"
        )
    return _parse_locked_environment(raw)


def _installed_locked_distributions(
    locked: dict[str, tuple[str, tuple[str, ...]]],
) -> metadata.Distribution:
    actual_python = ".".join(str(part) for part in sys.version_info[:3])
    if actual_python != SWEBENCH_PYTHON_VERSION:
        raise SwebenchProvenanceError(
            "spec extraction requires exact Python "
            f"{SWEBENCH_PYTHON_VERSION}, got {actual_python}"
        )
    matches: dict[str, list[metadata.Distribution]] = {name: [] for name in locked}
    unexpected: set[str] = set()
    for distribution in metadata.distributions():
        distribution_name = distribution.metadata.get("Name")
        if not isinstance(distribution_name, str):
            continue
        normalized = _normalize_distribution_name(distribution_name)
        if normalized in matches:
            matches[normalized].append(distribution)
        elif normalized not in INSTALLER_DISTRIBUTION_ALLOWLIST:
            unexpected.add(normalized)
    if unexpected:
        raise SwebenchProvenanceError(
            f"fresh extraction environment has unexpected distributions: {sorted(unexpected)}"
        )
    for name, (expected_version, _wheel_hashes) in locked.items():
        distributions = matches[name]
        if len(distributions) != 1:
            raise SwebenchProvenanceError(
                f"locked distribution {name} has {len(distributions)} installed matches"
            )
        actual_version = distributions[0].version
        if actual_version != expected_version:
            raise SwebenchProvenanceError(
                f"locked distribution {name} version mismatch: "
                f"expected {expected_version}, got {actual_version}"
            )
    return matches["swebench"][0]


def _verify_wheelhouse(
    wheel_path: Path, locked: dict[str, tuple[str, tuple[str, ...]]]
) -> None:
    wheelhouse = wheel_path.parent
    _require_directory_nofollow(wheelhouse)
    package_by_hash: dict[str, str] = {}
    for package, (_version, hashes) in locked.items():
        for digest in hashes:
            if digest in package_by_hash:
                raise SwebenchProvenanceError("swebench lock wheel hashes must be unique")
            package_by_hash[digest] = package
    selected_packages: set[str] = set()
    seen_wheel = False
    try:
        entries = sorted(os.scandir(wheelhouse), key=lambda entry: entry.name)
    except OSError as exc:
        raise SwebenchProvenanceError(f"cannot enumerate frozen wheelhouse: {exc}") from exc
    for entry in entries:
        entry_path = Path(entry.path)
        if entry.is_symlink() or not entry.is_file(follow_symlinks=False):
            raise SwebenchProvenanceError(
                f"wheelhouse contains a non-regular entry: {entry_path}"
            )
        if not entry.name.endswith(".whl"):
            raise SwebenchProvenanceError(f"wheelhouse contains a non-wheel file: {entry_path}")
        payload = _read_regular_nofollow(
            entry_path, max_bytes=WHEELHOUSE_MEMBER_MAX_BYTES
        )
        digest = hashlib.sha256(payload).hexdigest()
        package = package_by_hash.get(digest)
        if package is None:
            raise SwebenchProvenanceError(f"wheelhouse contains an unlocked wheel hash: {digest}")
        if package in selected_packages:
            raise SwebenchProvenanceError(
                f"wheelhouse contains multiple platform wheels for {package}"
            )
        selected_packages.add(package)
        if os.path.samefile(entry_path, wheel_path):
            seen_wheel = True
    if not seen_wheel:
        raise SwebenchProvenanceError("explicit swebench wheel is not in the verified wheelhouse")
    if selected_packages != set(locked):
        missing = sorted(set(locked) - selected_packages)
        raise SwebenchProvenanceError(
            f"wheelhouse package closure mismatch: missing={missing}"
        )


def _canonical_wheel_member(name: str, *, directory: bool) -> str:
    if not name or "\\" in name or "\x00" in name:
        raise SwebenchProvenanceError(f"unsafe wheel member path: {name!r}")
    candidate = name[:-1] if directory and name.endswith("/") else name
    pure = PurePosixPath(candidate)
    if (
        pure.is_absolute()
        or ".." in pure.parts
        or "." in pure.parts
        or pure.as_posix() != candidate
    ):
        raise SwebenchProvenanceError(f"unsafe wheel member path: {name!r}")
    return candidate


def _record_digest(raw: bytes) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).rstrip(b"=").decode("ascii")


def _verified_wheel_files(path: Path) -> tuple[dict[str, bytes], str]:
    if path.name != SWEBENCH_WHEEL:
        raise SwebenchProvenanceError(
            f"unexpected swebench wheel filename: expected {SWEBENCH_WHEEL}, got {path.name}"
        )
    raw = _read_regular_nofollow(path, max_bytes=SWEBENCH_WHEEL_MAX_BYTES)
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if actual_sha256 != SWEBENCH_WHEEL_SHA256:
        raise SwebenchProvenanceError(
            "swebench wheel SHA-256 mismatch: "
            f"expected {SWEBENCH_WHEEL_SHA256}, got {actual_sha256}"
        )
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw))
    except (zipfile.BadZipFile, OSError) as exc:
        raise SwebenchProvenanceError(f"swebench wheel is not a valid ZIP archive: {exc}") from exc
    files: dict[str, bytes] = {}
    total_uncompressed = 0
    try:
        for info in archive.infolist():
            name = _canonical_wheel_member(info.filename, directory=info.is_dir())
            if name in files:
                raise SwebenchProvenanceError(f"duplicate wheel member: {name}")
            if info.flag_bits & 0x1:
                raise SwebenchProvenanceError(f"encrypted wheel member forbidden: {name}")
            unix_mode = info.external_attr >> 16
            file_type = stat.S_IFMT(unix_mode)
            allowed_type = stat.S_IFDIR if info.is_dir() else stat.S_IFREG
            if file_type not in (0, allowed_type):
                raise SwebenchProvenanceError(f"non-regular wheel member forbidden: {name}")
            if info.is_dir():
                continue
            total_uncompressed += info.file_size
            if total_uncompressed > SWEBENCH_WHEEL_MAX_UNCOMPRESSED_BYTES:
                raise SwebenchProvenanceError("swebench wheel exceeds uncompressed byte limit")
            files[name] = archive.read(info)
    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
        raise SwebenchProvenanceError(f"cannot read swebench wheel payload: {exc}") from exc
    finally:
        archive.close()
    record_raw = files.get(SWEBENCH_RECORD)
    if record_raw is None:
        raise SwebenchProvenanceError("swebench wheel lacks its embedded RECORD")
    try:
        record_text = record_raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SwebenchProvenanceError(f"swebench wheel RECORD is not UTF-8: {exc}") from exc
    record_rows: dict[str, tuple[str, str]] = {}
    try:
        rows = csv.reader(io.StringIO(record_text, newline=""))
        for row in rows:
            if len(row) != 3:
                raise SwebenchProvenanceError("swebench wheel RECORD row must have three fields")
            name = _canonical_wheel_member(row[0], directory=False)
            if name in record_rows:
                raise SwebenchProvenanceError(f"duplicate swebench wheel RECORD row: {name}")
            record_rows[name] = (row[1], row[2])
    except csv.Error as exc:
        raise SwebenchProvenanceError(f"cannot parse swebench wheel RECORD: {exc}") from exc
    if set(record_rows) != set(files):
        missing = sorted(set(files) - set(record_rows))
        extra = sorted(set(record_rows) - set(files))
        raise SwebenchProvenanceError(
            f"swebench wheel RECORD coverage mismatch: missing={missing}, extra={extra}"
        )
    for name, payload in files.items():
        digest_field, size_field = record_rows[name]
        if name == SWEBENCH_RECORD:
            if digest_field or size_field:
                raise SwebenchProvenanceError("swebench wheel RECORD must not hash itself")
            continue
        expected_digest = f"sha256={_record_digest(payload)}"
        if digest_field != expected_digest or size_field != str(len(payload)):
            raise SwebenchProvenanceError(f"swebench wheel RECORD mismatch for {name}")
    package_members = [name for name in files if name.startswith("swebench/")]
    if not package_members or "swebench/__init__.py" not in package_members:
        raise SwebenchProvenanceError("swebench wheel package payload is incomplete")
    tree = hashlib.sha256()
    for name in sorted(files):
        if name == SWEBENCH_RECORD:
            continue
        tree.update(name.encode("utf-8"))
        tree.update(b"\0")
        tree.update(hashlib.sha256(files[name]).digest())
    return files, tree.hexdigest()


def _collect_regular_tree(root: Path, prefix: str) -> dict[str, bytes]:
    _require_directory_nofollow(root)
    collected: dict[str, bytes] = {}

    def visit(directory: Path, relative: PurePosixPath) -> None:
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as exc:
            raise SwebenchProvenanceError(f"cannot enumerate installed payload {directory}: {exc}") from exc
        for entry in entries:
            if entry.name in {".", ".."}:
                raise SwebenchProvenanceError("invalid installed payload entry")
            entry_path = Path(entry.path)
            if entry.is_symlink():
                raise SwebenchProvenanceError(f"symlink forbidden in installed payload: {entry_path}")
            try:
                mode = entry.stat(follow_symlinks=False).st_mode
            except OSError as exc:
                raise SwebenchProvenanceError(f"cannot stat installed payload {entry_path}: {exc}") from exc
            child = relative / entry.name
            if stat.S_ISDIR(mode):
                if entry.name != "__pycache__":
                    visit(entry_path, child)
                continue
            if not stat.S_ISREG(mode):
                raise SwebenchProvenanceError(
                    f"non-regular entry forbidden in installed payload: {entry_path}"
                )
            logical = PurePosixPath(prefix, child).as_posix()
            collected[logical] = _read_regular_nofollow(entry_path)

    visit(root, PurePosixPath())
    return collected


def _distribution_roots(distribution: metadata.Distribution) -> tuple[Path, Path, Path]:
    distribution_root = Path(distribution.locate_file(""))
    package_root = Path(distribution.locate_file("swebench"))
    dist_info_root = Path(distribution.locate_file(SWEBENCH_DIST_INFO))
    for path in (distribution_root, package_root, dist_info_root):
        _require_directory_nofollow(path)
    if package_root.parent != distribution_root or dist_info_root.parent != distribution_root:
        raise SwebenchProvenanceError("swebench distribution roots are not direct site-package children")
    return distribution_root, package_root, dist_info_root


def _verify_import_spec_root(package_root: Path) -> None:
    specification = util.find_spec("swebench")
    if specification is None or specification.origin is None:
        raise SwebenchProvenanceError("cannot resolve the unimported swebench package")
    origin = Path(specification.origin)
    _read_regular_nofollow(origin)
    if not os.path.samefile(origin.parent, package_root):
        raise SwebenchProvenanceError("resolved swebench import root differs from distribution root")
    locations = specification.submodule_search_locations
    if locations is None or len(locations) != 1:
        raise SwebenchProvenanceError("swebench import must resolve to one package root")
    location = Path(next(iter(locations)))
    _require_directory_nofollow(location)
    if not os.path.samefile(location, package_root):
        raise SwebenchProvenanceError("swebench search path differs from distribution root")


def _verify_installed_payload(
    wheel_files: dict[str, bytes], package_root: Path, dist_info_root: Path
) -> None:
    actual = _collect_regular_tree(package_root, "swebench")
    actual.update(_collect_regular_tree(dist_info_root, SWEBENCH_DIST_INFO))
    expected = {name: payload for name, payload in wheel_files.items() if name != SWEBENCH_RECORD}
    required_installer_files = {SWEBENCH_RECORD, *INSTALLER_DIST_INFO_EXTRAS}
    missing = sorted(set(expected) - set(actual))
    extras = sorted(set(actual) - set(expected) - required_installer_files)
    missing_installer = sorted(required_installer_files - set(actual))
    if missing or extras or missing_installer:
        raise SwebenchProvenanceError(
            "installed swebench file-set mismatch: "
            f"missing={missing}, extra={extras}, missing_installer={missing_installer}"
        )
    for name, payload in expected.items():
        if actual[name] != payload:
            raise SwebenchProvenanceError(f"installed swebench payload differs from wheel: {name}")
    for name, payload in INSTALLER_DIST_INFO_EXTRAS.items():
        if actual[name] != payload:
            raise SwebenchProvenanceError(f"unexpected installer-owned swebench metadata: {name}")


def _verify_imported_swebench_root(module: ModuleType, package_root: Path) -> None:
    module_file = getattr(module, "__file__", None)
    module_path = getattr(module, "__path__", None)
    if not isinstance(module_file, str) or module_path is None:
        raise SwebenchProvenanceError("imported swebench is not a regular package")
    imported_file = Path(module_file)
    _read_regular_nofollow(imported_file)
    locations = [Path(value) for value in module_path]
    if len(locations) != 1:
        raise SwebenchProvenanceError("imported swebench has multiple package roots")
    _require_directory_nofollow(locations[0])
    if not os.path.samefile(imported_file.parent, package_root) or not os.path.samefile(
        locations[0], package_root
    ):
        raise SwebenchProvenanceError("imported swebench root differs from verified distribution root")


def verify_swebench_provenance(
    wheel_path: Path,
) -> tuple[dict[str, bytes], Path, Path, str]:
    """Bind the importable spec generator to the complete frozen wheel environment."""

    locked = _locked_environment()
    _verify_wheelhouse(wheel_path, locked)
    distribution = _installed_locked_distributions(locked)
    if distribution.version != EXPECTED_SWEBENCH_VERSION:
        raise SwebenchProvenanceError(
            "unsupported swebench version: "
            f"expected {EXPECTED_SWEBENCH_VERSION}, got {distribution.version}"
        )
    wheel_files, tree_sha256 = _verified_wheel_files(wheel_path)
    _distribution_root, package_root, dist_info_root = _distribution_roots(distribution)
    _verify_import_spec_root(package_root)
    _verify_installed_payload(wheel_files, package_root, dist_info_root)
    return wheel_files, package_root, dist_info_root, tree_sha256


def framework_of(s: str) -> str:
    if "runtests.py" in s:
        return "django_runtests"
    if "pytest" in s:
        return "pytest"
    if "bin/test" in s:
        return "sympy_bintest"
    if "tox" in s:
        return "tox"
    return "unknown"


def solution_rows_for_specs(solve_summary: dict, scenarios_summary: dict) -> list[dict]:
    """Return every valid solution, annotated with independent witness availability."""

    scenario_ids = {
        row["instance_id"]
        for row in scenarios_summary["manifest"]
        if row["status"] == "scenario"
    }
    return [
        {
            "instance_id": row["instance_id"],
            "identical_to_gold": bool(row["identical_to_gold"]),
            "scenario_available": row["instance_id"] in scenario_ids,
        }
        for row in solve_summary["manifest"]
        if row["status"] == "solution"
    ]


def stage_summaries_for_specs(
    runtime_manifest_sha256: str | None = None,
) -> tuple[dict, dict]:
    """Load legacy summaries, or prove iter202 summaries from immutable checkpoints."""

    if EXP.name != ITER202_EXP:
        return (
            json.loads((EXP / "proof/raw/solutions/solve_summary.json").read_text()),
            json.loads((SCEN / "scenarios_summary.json").read_text()),
        )
    if (
        iter202_stages.EXP.resolve() != EXP.resolve()
        or iter202_stages.STAGE.resolve() != SCEN.resolve()
    ):
        raise ValueError("iter202 spec extractor is not bound to the checkpointed stage paths")
    if runtime_manifest_sha256 is None:
        runtime_manifest_sha256 = require_valid_runtime_freeze()
    return iter202_stages.reconstruct_stage_inputs_for_specs(
        runtime_manifest_sha256
    )


def main() -> int:
    runtime_manifest_sha256: str | None = None
    if EXP.name == ITER202_EXP:
        try:
            runtime_manifest_sha256 = require_valid_runtime_freeze()
        except RuntimeFreezeError as exc:
            print(f"iter202 runtime freeze preflight failed: {exc}")
            return 2
    wheel_value = os.environ.get("TELOS_SWEEBENCH_WHEEL")
    if not wheel_value:
        print("swebench provenance failed: TELOS_SWEEBENCH_WHEEL is required")
        return 2
    wheel_path = Path(wheel_value)
    if not wheel_path.is_absolute():
        print("swebench provenance failed: TELOS_SWEEBENCH_WHEEL must be absolute")
        return 2
    try:
        wheel_files, package_root, dist_info_root, tree_sha256 = (
            verify_swebench_provenance(wheel_path)
        )
    except (SwebenchProvenanceError, metadata.PackageNotFoundError) as exc:
        print(f"swebench provenance failed: {exc}")
        return 2
    try:
        import swebench

        _verify_imported_swebench_root(swebench, package_root)
        from swebench.harness.test_spec.test_spec import make_test_spec
        generator_module = sys.modules.get(make_test_spec.__module__)
        generator_file = getattr(generator_module, "__file__", None)
        if not isinstance(generator_file, str):
            raise SwebenchProvenanceError("make_test_spec has no regular module file")
        generator_path = Path(generator_file)
        _read_regular_nofollow(generator_path)
        try:
            generator_path.relative_to(package_root)
        except ValueError as exc:
            raise SwebenchProvenanceError(
                "make_test_spec module is outside the verified swebench package"
            ) from exc
        _verify_installed_payload(wheel_files, package_root, dist_info_root)
    except Exception as exc:
        print(f"swebench provenance failed during verified import: {exc}")
        return 2
    print(
        "verified swebench extraction environment: "
        f"python={SWEBENCH_PYTHON_VERSION}, "
        f"locked_distributions={SWEBENCH_LOCK_ENTRY_COUNT}, "
        f"wheel_sha256={SWEBENCH_WHEEL_SHA256}, payload_tree_sha256={tree_sha256}"
    )
    by = {r["instance_id"]: r for r in json.loads(SNAPSHOT.read_text())["rows"]}
    solve_summary, scenarios_summary = stage_summaries_for_specs(
        runtime_manifest_sha256
    )
    solution_rows = solution_rows_for_specs(solve_summary, scenarios_summary)
    OUT.mkdir(parents=True, exist_ok=True)
    index = []
    for solution in solution_rows:
        iid = solution["instance_id"]
        inst = by[iid]
        ts = make_test_spec(inst)
        stem = iid.replace("/", "__")
        eval_script = ts.eval_script
        eval_script_sha256 = hashlib.sha256(eval_script.encode()).hexdigest()
        (OUT / f"{stem}.eval_script.sh").write_text(eval_script)
        spec = {
            "instance_id": iid,
            "repo": inst["repo"],
            "base_commit": inst["base_commit"],
            "framework": framework_of(ts.eval_script),
            "eval_script_sha256": eval_script_sha256,
            "fail_to_pass": json.loads(inst["FAIL_TO_PASS"]),
            "pass_to_pass": json.loads(inst["PASS_TO_PASS"]),
            "image": (
                "swebench/sweb.eval.x86_64."
                + re.sub("__", "_1776_", iid.lower())
                + ":latest"
            ),
            "identical_to_gold": solution["identical_to_gold"],
            "scenario_available": solution["scenario_available"],
        }
        (OUT / f"{stem}.spec.json").write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")
        index.append(
            {
                "instance_id": iid,
                "repo": inst["repo"],
                "framework": spec["framework"],
                "eval_script_sha256": eval_script_sha256,
                "identical_to_gold": solution["identical_to_gold"],
                "scenario_available": solution["scenario_available"],
            }
        )
    (OUT / "index.json").write_text(
        json.dumps(
            {
                "schema_version": "telos.iter200.spec_index.v2",
                "count": len(index),
                "generator": {
                    "package": "swebench",
                    "version": EXPECTED_SWEBENCH_VERSION,
                    "distribution_filename": SWEBENCH_WHEEL,
                    "distribution_sha256": SWEBENCH_WHEEL_SHA256,
                    "source_snapshot": str(SNAPSHOT.relative_to(ROOT)),
                    "source_snapshot_sha256": hashlib.sha256(
                        SNAPSHOT.read_bytes()
                    ).hexdigest(),
                },
                "specs": index,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(f"extracted {len(index)} specs; frameworks:", dict(Counter(s["framework"] for s in index)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
