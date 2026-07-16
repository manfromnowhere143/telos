from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_guard():
    path = ROOT / "scripts/validate_supply_chain.py"
    spec = importlib.util.spec_from_file_location("validate_supply_chain", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_repository_supply_chain_contract_is_green() -> None:
    guard = load_guard()
    assert guard.collect_failures() == []


def test_workflow_guard_rejects_mutable_action_runner_and_permissions(tmp_path: Path) -> None:
    guard = load_guard()
    path = tmp_path / "unsafe.yml"
    path.write_text(
        "name: unsafe\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
        "    steps:\n      - uses: actions/checkout@v4\n"
    )

    failures = "\n".join(guard.validate_workflow(path))
    assert "runner must be one of" in failures
    assert "not an immutable SHA" in failures
    assert "top-level permissions must be exactly" in failures


@pytest.mark.parametrize(
    "workflow_name",
    [
        "iter203-execute.yml",
        "iter204-execute.yml",
        "iter205-execute.yml",
        "iter206-execute.yml",
    ],
)
def test_workflow_guard_allows_only_execution_workflows_read_only_actions_and_checks(
    tmp_path: Path,
    workflow_name: str,
) -> None:
    guard = load_guard()
    allowed = tmp_path / workflow_name
    allowed.write_text(
        "name: iter203\non: [workflow_dispatch]\npermissions:\n"
        "  actions: read\n  checks: read\n  contents: read\njobs:\n"
        "  authorize:\n    runs-on: ubuntu-24.04\n    steps:\n      - run: 'true'\n"
    )
    assert guard.validate_workflow(allowed) == []

    ordinary = tmp_path / "ordinary.yml"
    ordinary.write_text(allowed.read_text())
    failures = "\n".join(guard.validate_workflow(ordinary))
    assert "top-level permissions must be exactly" in failures


def test_workflow_guard_structurally_rejects_flow_uses_matrix_runner_and_job_write(
    tmp_path: Path,
) -> None:
    guard = load_guard()
    path = tmp_path / "structural-bypass.yml"
    path.write_text(
        "name: bypass\non: [push]\npermissions:\n  contents: read\njobs:\n"
        "  test:\n    permissions: {contents: write}\n"
        "    strategy:\n      matrix:\n        os: [ubuntu-latest]\n"
        "    runs-on: ${{ matrix.os }}\n    steps:\n"
        "      - {uses: actions/checkout@v4}\n"
    )

    failures = "\n".join(guard.validate_workflow(path))
    assert "may not override permissions" in failures
    assert "runner must be one of" in failures
    assert "not an immutable SHA" in failures


def test_workflow_guard_rejects_invalid_yaml_even_when_regexes_match(tmp_path: Path) -> None:
    guard = load_guard()
    path = tmp_path / "invalid.yml"
    path.write_text(
        "name: invalid\non: [push]\npermissions:\n  contents: read\njobs:\n"
        "  test:\n    runs-on: ubuntu-24.04\n    steps:\n"
        "      - run: command --option=:all:\n"
    )

    failures = "\n".join(guard.validate_workflow(path))
    assert "invalid YAML" in failures


def test_workflow_guard_rejects_duplicate_yaml_keys(tmp_path: Path) -> None:
    guard = load_guard()
    path = tmp_path / "duplicate.yml"
    path.write_text(
        "name: duplicate\non: [push]\npermissions:\n  contents: read\n"
        "permissions:\n  contents: read\njobs:\n  test:\n"
        "    runs-on: ubuntu-24.04\n    steps: []\n"
    )

    failures = "\n".join(guard.validate_workflow(path))
    assert "duplicate key" in failures


@pytest.mark.parametrize(
    "run_block",
    [
        "curl -LsSf https://example.invalid/install.sh | sh",
        "wget -qO- https://example.invalid/install.sh | bash",
        (
            "curl -o /tmp/tool https://example.invalid/tool\n"
            "chmod +x /tmp/tool\n"
            "./tmp/tool"
        ),
    ],
)
def test_workflow_guard_rejects_download_and_execute_run_blocks(
    tmp_path: Path, run_block: str
) -> None:
    guard = load_guard()
    path = tmp_path / "download-execute.yml"
    indented_run = "\n".join(f"          {line}" for line in run_block.splitlines())
    path.write_text(
        "name: unsafe-download\non: [push]\npermissions:\n  contents: read\njobs:\n"
        "  test:\n    runs-on: ubuntu-24.04\n    steps:\n"
        f"      - run: |\n{indented_run}\n"
    )

    failures = "\n".join(guard.validate_workflow(path))
    assert "unsafe download-and-execute pattern" in failures


@pytest.mark.parametrize(
    "with_block",
    [
        "",
        "        with:\n          version: latest\n",
        "        with:\n          version: \"0.11\"\n",
    ],
)
def test_workflow_guard_rejects_setup_uv_without_exact_version(
    tmp_path: Path, with_block: str
) -> None:
    guard = load_guard()
    path = tmp_path / "unpinned-setup-uv.yml"
    path.write_text(
        "name: unpinned-uv\non: [push]\npermissions:\n  contents: read\njobs:\n"
        "  test:\n    runs-on: ubuntu-24.04\n    steps:\n"
        "      - uses: astral-sh/setup-uv@" + "a" * 40 + "\n"
        + with_block
    )

    failures = "\n".join(guard.validate_workflow(path))
    assert "setup-uv version must be an exact X.Y.Z string" in failures


def guarded_workflow(run_block: str) -> str:
    indented_run = "\n".join(f"          {line}" for line in run_block.splitlines())
    return (
        "name: pip-guard\non: [push]\npermissions:\n  contents: read\njobs:\n"
        "  test:\n    runs-on: ubuntu-24.04\n    steps:\n"
        f"      - run: |\n{indented_run}\n"
    )


@pytest.mark.parametrize(
    "upgrade_command",
    [
        "python -m pip install --upgrade pip",
        "python -m pip install -U pip",
    ],
)
def test_workflow_guard_rejects_pip_self_upgrade(
    tmp_path: Path, upgrade_command: str
) -> None:
    guard = load_guard()
    path = tmp_path / "pip-upgrade.yml"
    path.write_text(guarded_workflow(upgrade_command))

    failures = "\n".join(guard.validate_workflow(path))
    assert "pip upgrades are forbidden" in failures


@pytest.mark.parametrize(
    ("run_block", "expected_error"),
    [
        (
            'wheelhouse="$(mktemp -d /tmp/test.XXXXXX)"\n'
            'python -m pip download --no-cache-dir --only-binary=:all: --dest "$wheelhouse" '
            "-r requirements-ci.txt",
            "pip download must use --require-hashes",
        ),
        (
            'wheelhouse="$(mktemp -d /tmp/test.XXXXXX)"\n'
            'python -m pip download --no-cache-dir --require-hashes --dest "$wheelhouse" '
            "-r requirements-ci.txt",
            "pip download must use --only-binary=:all:",
        ),
        (
            'wheelhouse="$(mktemp -d /tmp/test.XXXXXX)"\n'
            "python -m pip download --no-cache-dir --require-hashes --only-binary=:all: "
            '--dest "$wheelhouse" pytest==9.0.2',
            "pip download must use one validated repository lock",
        ),
        (
            "python -m pip download --no-cache-dir --require-hashes --only-binary=:all: "
            '--dest "$wheelhouse" -r requirements-ci.txt',
            "requires a fresh mktemp wheelhouse",
        ),
        (
            'wheelhouse="$(mktemp -d /tmp/test.XXXXXX)"\n'
            "python -m pip download --require-hashes --only-binary=:all: "
            '--dest "$wheelhouse" -r requirements-ci.txt',
            "pip download must use --no-cache-dir",
        ),
        (
            'wheelhouse="$(mktemp -d /tmp/test.XXXXXX)"\n'
            "python -m pip install --no-cache-dir --require-hashes --only-binary=:all: "
            '-r requirements-ci.txt --find-links "$wheelhouse"',
            "pip install must use --no-index",
        ),
        (
            'wheelhouse="$(mktemp -d /tmp/test.XXXXXX)"\n'
            "python -m pip install --no-cache-dir --no-index --require-hashes --only-binary=:all: "
            "-r requirements-ci.txt",
            "pip install must use the fresh wheelhouse",
        ),
        (
            'wheelhouse="$(mktemp -d /tmp/test.XXXXXX)"\n'
            "python -m pip install --no-cache-dir --no-index --require-hashes "
            '--only-binary=:all: --find-links "$wheelhouse" pytest==9.0.2',
            "pip install must use one validated repository lock",
        ),
    ],
)
def test_workflow_guard_rejects_unlocked_or_online_pip_operations(
    tmp_path: Path, run_block: str, expected_error: str
) -> None:
    guard = load_guard()
    path = tmp_path / "pip-operation.yml"
    path.write_text(guarded_workflow(run_block))

    failures = "\n".join(guard.validate_workflow(path))
    assert expected_error in failures


def test_workflow_guard_accepts_locked_download_and_offline_install(
    tmp_path: Path,
) -> None:
    guard = load_guard()
    path = tmp_path / "locked-wheelhouse.yml"
    path.write_text(
        guarded_workflow(
            'wheelhouse="$(mktemp -d /tmp/test.XXXXXX)"\n'
            "export PIP_DISABLE_PIP_VERSION_CHECK=1\n"
            "python -m pip download --no-cache-dir --require-hashes --only-binary=:all: "
            '--dest "$wheelhouse" -r requirements-ci.txt\n'
            "python -m pip install --no-cache-dir --no-index --require-hashes --only-binary=:all: "
            '--find-links "$wheelhouse" -r requirements-ci.txt'
        )
    )

    assert guard.validate_workflow(path) == []


def test_workflow_guard_rejects_enabled_pip_version_check(tmp_path: Path) -> None:
    guard = load_guard()
    path = tmp_path / "version-check.yml"
    path.write_text(
        guarded_workflow(
            'wheelhouse="$(mktemp -d /tmp/test.XXXXXX)"\n'
            "python -m pip download --no-cache-dir --require-hashes --only-binary=:all: "
            '--dest "$wheelhouse" -r requirements-ci.txt'
        )
    )

    failures = "\n".join(guard.validate_workflow(path))
    assert "must disable the pip version check" in failures


def test_lock_guard_rejects_unhashed_dependency(tmp_path: Path) -> None:
    guard = load_guard()
    path = tmp_path / "requirements-ci.txt"
    path.write_text("pytest==9.0.2\n")

    assert guard.validate_lock(path)


def test_lock_guard_accepts_multiple_unique_platform_wheel_hashes(tmp_path: Path) -> None:
    guard = load_guard()
    path = tmp_path / "requirements-ci.txt"
    path.write_text(
        "demo==1.2.3 \\\n"
        "    --hash=sha256:" + "a" * 64 + " \\\n"
        "    --hash=sha256:" + "b" * 64 + "\n"
    )

    assert guard.validate_lock(path) == []


def test_lock_guard_rejects_markers_arbitrary_equality_and_duplicate_names(
    tmp_path: Path,
) -> None:
    guard = load_guard()
    path = tmp_path / "requirements-ci.txt"
    digest = "a" * 64
    path.write_text(
        f"demo==1.0;python_version>'3' \\\n    --hash=sha256:{digest}\n"
        f"demo===1.0 \\\n    --hash=sha256:{digest}\n"
        f"demo==1.0 \\\n    --hash=sha256:{digest}\n"
        f"demo==1.0 \\\n    --hash=sha256:{digest}\n"
    )

    failures = "\n".join(guard.validate_lock(path))
    assert "dependency is not exactly pinned" in failures
    assert "normalized package names must be unique" in failures
