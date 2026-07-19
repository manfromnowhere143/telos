"""Exercise iter240's check-only command surface through the existing CI matrix."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROVIDER_CREDENTIAL_NAMES = frozenset(
    {
        "ANTHROPIC_API_KEY",
        "AZURE_OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "GH_TOKEN",
        "GITHUB_TOKEN",
        "GOOGLE_API_KEY",
        "OPENAI_API_KEY",
    }
)
ENVIRONMENT_ALLOWLIST = frozenset(
    {
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "PATH",
        "SYSTEMROOT",
        "TMPDIR",
    }
)


@dataclass(frozen=True)
class CheckCommand:
    name: str
    argv: tuple[str, ...]
    expected_stdout: bytes
    timeout_seconds: int


CHECK_COMMANDS = (
    CheckCommand(
        name="iter239-remote-acceptance",
        argv=("scripts/validate_iter239_remote_acceptance.py",),
        expected_stdout=b"iter239 remote acceptance: supported engineering closure",
        timeout_seconds=180,
    ),
    CheckCommand(
        name="iter240-frozen-selection",
        argv=(
            "scripts/build_iter240_ground_truth_admission.py",
            "--check-selection",
        ),
        expected_stdout=b"iter240 selection freeze: exact 13-row census rebuilds",
        timeout_seconds=180,
    ),
    CheckCommand(
        name="iter240-diagnostic-rebuild",
        argv=("scripts/build_iter240_ground_truth_diagnostics.py", "--check"),
        expected_stdout=b"iter240 post-freeze diagnostics: exact v2 rebuild passes",
        timeout_seconds=300,
    ),
    CheckCommand(
        name="iter240-independent-diagnostic-validation",
        argv=("scripts/validate_iter240_ground_truth_diagnostics.py",),
        expected_stdout=b"iter240 independent post-freeze diagnostics: PASS",
        timeout_seconds=300,
    ),
    CheckCommand(
        name="iter240-role-view-policy",
        argv=("scripts/validate_iter240_role_view_policy.py",),
        expected_stdout=b"PASS iter240 role-view policy",
        timeout_seconds=180,
    ),
)


def _dirty_state_bytes() -> bytes:
    result = subprocess.run(
        [
            "git",
            "status",
            "--porcelain=v2",
            "-z",
            "--untracked-files=all",
        ],
        cwd=ROOT,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        check=True,
        capture_output=True,
    )
    return result.stdout


def _credential_stripped_environment(home: Path) -> dict[str, str]:
    home.mkdir(mode=0o700)
    xdg = home / "xdg"
    xdg.mkdir(mode=0o700)
    environment = {
        name: value
        for name, value in os.environ.items()
        if name in ENVIRONMENT_ALLOWLIST
    }
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "HOME": str(home),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONNOUSERSITE": "1",
            "PYTHONUTF8": "1",
            "TZ": "UTC",
            "XDG_CONFIG_HOME": str(xdg),
        }
    )
    assert PROVIDER_CREDENTIAL_NAMES.isdisjoint(environment)
    return environment


@pytest.mark.parametrize(
    "command",
    CHECK_COMMANDS,
    ids=lambda command: command.name,
)
def test_check_only_ci_entrypoint(
    command: CheckCommand,
    tmp_path: Path,
) -> None:
    before = _dirty_state_bytes()
    result: subprocess.CompletedProcess[bytes] | None = None
    try:
        result = subprocess.run(
            [sys.executable, *command.argv],
            cwd=ROOT,
            env=_credential_stripped_environment(tmp_path / "home"),
            check=False,
            capture_output=True,
            timeout=command.timeout_seconds,
        )
    finally:
        after = _dirty_state_bytes()
        assert after == before, (
            f"{command.name} changed repository dirty state\n"
            f"before={before!r}\n"
            f"after={after!r}"
        )

    assert result is not None
    assert result.returncode == 0, (
        f"{command.name} failed with {result.returncode}\n"
        f"stdout={result.stdout.decode('utf-8', errors='replace')}\n"
        f"stderr={result.stderr.decode('utf-8', errors='replace')}"
    )
    assert command.expected_stdout in result.stdout
    assert result.stderr == b""
