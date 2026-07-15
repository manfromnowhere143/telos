from __future__ import annotations

import base64
import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_extractor():
    path = ROOT / "scripts/extract_iter200_specs.py"
    spec = importlib.util.spec_from_file_location("extract_iter200_specs_provenance", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def record_hash(payload: bytes) -> str:
    encoded = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=")
    return encoded.decode("ascii")


def write_test_wheel(path: Path, *, corrupt_record: bool = False) -> None:
    members = {
        "swebench/__init__.py": b'__version__ = "4.1.0"\n',
        "swebench/harness/test_spec/test_spec.py": b"def make_test_spec(value):\n    return value\n",
        "swebench-4.1.0.dist-info/METADATA": b"Name: swebench\nVersion: 4.1.0\n",
        "swebench-4.1.0.dist-info/WHEEL": b"Wheel-Version: 1.0\n",
        "swebench-4.1.0.dist-info/top_level.txt": b"swebench\n",
    }
    rows = []
    for index, (name, payload) in enumerate(sorted(members.items())):
        digest = "A" * 43 if corrupt_record and index == 0 else record_hash(payload)
        rows.append(f"{name},sha256={digest},{len(payload)}\n")
    rows.append("swebench-4.1.0.dist-info/RECORD,,\n")
    members["swebench-4.1.0.dist-info/RECORD"] = "".join(rows).encode()
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)


def installed_fixture(tmp_path: Path) -> tuple[Path, Path, dict[str, bytes]]:
    package = tmp_path / "site-packages/swebench"
    dist_info = tmp_path / "site-packages/swebench-4.1.0.dist-info"
    package.mkdir(parents=True)
    dist_info.mkdir()
    wheel_files = {
        "swebench/__init__.py": b"verified package\n",
        "swebench/harness.py": b"verified harness\n",
        "swebench-4.1.0.dist-info/METADATA": b"verified metadata\n",
        "swebench-4.1.0.dist-info/WHEEL": b"verified wheel metadata\n",
        "swebench-4.1.0.dist-info/top_level.txt": b"swebench\n",
        "swebench-4.1.0.dist-info/RECORD": b"wheel record\n",
    }
    for logical, payload in wheel_files.items():
        target = tmp_path / "site-packages" / logical
        if logical.endswith("/RECORD"):
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    (dist_info / "RECORD").write_bytes(b"installed record\n")
    (dist_info / "INSTALLER").write_bytes(b"pip\n")
    (dist_info / "REQUESTED").write_bytes(b"")
    return package, dist_info, wheel_files


def test_repository_dual_platform_lock_is_exact_and_hash_bound() -> None:
    extract = load_extractor()
    locked = extract._locked_environment()

    assert len(locked) == extract.SWEBENCH_LOCK_ENTRY_COUNT == 73
    assert locked["swebench"] == (
        "4.1.0",
        (extract.SWEBENCH_WHEEL_SHA256,),
    )
    assert sum(len(hashes) == 2 for _version, hashes in locked.values()) == 16


def test_wheel_verifier_rehashes_at_use_time_and_rejects_tamper(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    extract = load_extractor()
    wheel = tmp_path / extract.SWEBENCH_WHEEL
    write_test_wheel(wheel)
    original_hash = hashlib.sha256(wheel.read_bytes()).hexdigest()
    monkeypatch.setattr(extract, "SWEBENCH_WHEEL_SHA256", original_hash)
    files, _tree = extract._verified_wheel_files(wheel)
    assert "swebench/__init__.py" in files

    with wheel.open("ab") as stream:
        stream.write(b"tampered after pin")
    with pytest.raises(extract.SwebenchProvenanceError, match="SHA-256 mismatch"):
        extract._verified_wheel_files(wheel)


def test_wheel_verifier_rejects_invalid_embedded_record(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    extract = load_extractor()
    wheel = tmp_path / extract.SWEBENCH_WHEEL
    write_test_wheel(wheel, corrupt_record=True)
    monkeypatch.setattr(
        extract, "SWEBENCH_WHEEL_SHA256", hashlib.sha256(wheel.read_bytes()).hexdigest()
    )

    with pytest.raises(extract.SwebenchProvenanceError, match="RECORD mismatch"):
        extract._verified_wheel_files(wheel)


def test_wheel_verifier_rejects_symlink_input(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    extract = load_extractor()
    real = tmp_path / "real.whl"
    write_test_wheel(real)
    wheel = tmp_path / extract.SWEBENCH_WHEEL
    wheel.symlink_to(real)
    monkeypatch.setattr(
        extract, "SWEBENCH_WHEEL_SHA256", hashlib.sha256(real.read_bytes()).hexdigest()
    )

    with pytest.raises(extract.SwebenchProvenanceError, match="symlink forbidden"):
        extract._verified_wheel_files(wheel)


@pytest.mark.parametrize("mutation", ["missing", "extra", "changed"])
def test_installed_payload_rejects_missing_extra_and_changed_files(
    tmp_path: Path, mutation: str
) -> None:
    extract = load_extractor()
    package, dist_info, wheel_files = installed_fixture(tmp_path)
    if mutation == "missing":
        (package / "harness.py").unlink()
    elif mutation == "extra":
        (package / "unexpected.py").write_text("unexpected\n")
    else:
        (package / "harness.py").write_text("changed\n")

    with pytest.raises(extract.SwebenchProvenanceError):
        extract._verify_installed_payload(wheel_files, package, dist_info)


def test_installed_payload_accepts_only_exact_wheel_bytes_and_pip_metadata(
    tmp_path: Path,
) -> None:
    extract = load_extractor()
    package, dist_info, wheel_files = installed_fixture(tmp_path)

    extract._verify_installed_payload(wheel_files, package, dist_info)


def test_import_spec_root_must_equal_distribution_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    extract = load_extractor()
    expected = tmp_path / "expected/swebench"
    shadow = tmp_path / "shadow/swebench"
    expected.mkdir(parents=True)
    shadow.mkdir(parents=True)
    (expected / "__init__.py").write_text("expected\n")
    (shadow / "__init__.py").write_text("shadow\n")
    fake_spec = SimpleNamespace(
        origin=str(shadow / "__init__.py"),
        submodule_search_locations=[str(shadow)],
    )
    monkeypatch.setattr(extract.util, "find_spec", lambda _name: fake_spec)

    with pytest.raises(extract.SwebenchProvenanceError, match="differs"):
        extract._verify_import_spec_root(expected)


def test_wheelhouse_requires_one_allowed_wheel_per_locked_package(
    tmp_path: Path,
) -> None:
    extract = load_extractor()
    first = tmp_path / "first.whl"
    second = tmp_path / "second.whl"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    locked = {
        "first": ("1.0", (hashlib.sha256(b"first").hexdigest(),)),
        "second": ("1.0", (hashlib.sha256(b"second").hexdigest(),)),
    }

    extract._verify_wheelhouse(first, locked)
    (tmp_path / "extra.whl").write_bytes(b"extra")
    with pytest.raises(extract.SwebenchProvenanceError, match="unlocked wheel hash"):
        extract._verify_wheelhouse(first, locked)


def test_wheelhouse_rejects_missing_locked_package(tmp_path: Path) -> None:
    extract = load_extractor()
    first = tmp_path / "first.whl"
    first.write_bytes(b"first")
    locked = {
        "first": ("1.0", (hashlib.sha256(b"first").hexdigest(),)),
        "second": ("1.0", (hashlib.sha256(b"second").hexdigest(),)),
    }

    with pytest.raises(extract.SwebenchProvenanceError, match=r"missing=\['second'\]"):
        extract._verify_wheelhouse(first, locked)


def test_wheelhouse_rejects_two_allowed_platform_wheels_for_one_package(
    tmp_path: Path,
) -> None:
    extract = load_extractor()
    linux = tmp_path / "demo-linux.whl"
    macos = tmp_path / "demo-macos.whl"
    linux.write_bytes(b"linux")
    macos.write_bytes(b"macos")
    locked = {
        "demo": (
            "1.0",
            tuple(
                sorted(
                    (
                        hashlib.sha256(b"linux").hexdigest(),
                        hashlib.sha256(b"macos").hexdigest(),
                    )
                )
            ),
        )
    }

    with pytest.raises(extract.SwebenchProvenanceError, match="multiple platform wheels"):
        extract._verify_wheelhouse(linux, locked)


def test_wheelhouse_rejects_hash_reused_across_packages(tmp_path: Path) -> None:
    extract = load_extractor()
    wheel = tmp_path / "demo.whl"
    wheel.write_bytes(b"same")
    digest = hashlib.sha256(b"same").hexdigest()
    locked = {
        "first": ("1.0", (digest,)),
        "second": ("1.0", (digest,)),
    }

    with pytest.raises(extract.SwebenchProvenanceError, match="must be unique"):
        extract._verify_wheelhouse(wheel, locked)


def test_locked_environment_rejects_wrong_exact_python(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    extract = load_extractor()
    monkeypatch.setattr(extract.sys, "version_info", (3, 11, 14, "final", 0))

    with pytest.raises(extract.SwebenchProvenanceError, match="exact Python 3.11.15"):
        extract._installed_locked_distributions({})


def test_lock_rehash_rejects_drift_and_symlink(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    extract = load_extractor()
    requirements = tmp_path / "requirements"
    requirements.mkdir()
    lock = requirements / "iter200-swebench.txt"
    original = (ROOT / extract.SWEBENCH_LOCK).read_bytes()
    lock.write_bytes(original)
    monkeypatch.setattr(extract, "ROOT", tmp_path)
    assert len(extract._locked_environment()) == 73

    lock.write_bytes(original + b"# drift\n")
    with pytest.raises(extract.SwebenchProvenanceError, match="lock SHA-256 mismatch"):
        extract._locked_environment()

    lock.unlink()
    target = tmp_path / "real-lock.txt"
    target.write_bytes(original)
    lock.symlink_to(target)
    with pytest.raises(extract.SwebenchProvenanceError, match="symlink forbidden"):
        extract._locked_environment()


def test_extractor_requires_explicit_absolute_wheel_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    extract = load_extractor()
    monkeypatch.setattr(extract, "EXP", tmp_path / "iter200")
    monkeypatch.delenv("TELOS_SWEEBENCH_WHEEL", raising=False)

    assert extract.main() == 2
