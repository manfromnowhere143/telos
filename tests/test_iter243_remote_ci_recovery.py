"""Known-good and known-bad cases for the Iter243 Python trust correction."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import stat

import pytest

from scripts import route_iter241_pytest as router
from scripts import run_iter241_pytest as runner


@dataclass(frozen=True)
class ExecutableMetadata:
    """Minimal stat surface consumed by both executable classifiers."""

    st_mode: int
    st_uid: int
    st_gid: int = 1000


def _regular(mode: int, uid: int) -> ExecutableMetadata:
    return ExecutableMetadata(stat.S_IFREG | mode, uid)


@pytest.mark.parametrize(
    ("path", "metadata", "euid", "expected"),
    (
        (Path("/trusted/python"), _regular(0o755, 1000), 1000, None),
        (Path("/trusted/python"), _regular(0o775, 1000), 1000, None),
        (
            Path("/trusted/python"),
            _regular(0o777, 1000),
            1000,
            "executable_world_writable",
        ),
        (Path("/trusted/python"), _regular(0o755, 0), 1000, None),
        (
            Path("/trusted/python"),
            _regular(0o775, 0),
            1000,
            "foreign_owned_executable_group_writable",
        ),
        (
            Path("/trusted/python"),
            _regular(0o777, 0),
            1000,
            "executable_world_writable",
        ),
        (
            Path("/trusted/python"),
            _regular(0o755, 2000),
            1000,
            "executable_owner_untrusted",
        ),
        (
            Path("/trusted/python"),
            _regular(0o775, 2000),
            1000,
            "executable_owner_untrusted",
        ),
        (
            Path("/trusted/python"),
            _regular(0o655, 1000),
            1000,
            "owner_execute_missing",
        ),
        (
            Path("relative/python"),
            _regular(0o755, 1000),
            1000,
            "executable_not_absolute",
        ),
        (
            Path("/trusted/python"),
            ExecutableMetadata(stat.S_IFDIR | 0o755, 1000),
            1000,
            "executable_not_regular",
        ),
        (
            Path("/trusted/python"),
            ExecutableMetadata(stat.S_IFLNK | 0o777, 1000),
            1000,
            "executable_not_regular",
        ),
        (Path("/trusted/python"), _regular(0o775, 0), 0, None),
    ),
)
def test_runner_and_router_python_executable_policy_are_identical(
    path: Path,
    metadata: ExecutableMetadata,
    euid: int,
    expected: str | None,
) -> None:
    runner_reason = runner._python_executable_reason(path, metadata, euid=euid)  # type: ignore[arg-type]
    router_reason = router._python_executable_reason(path, metadata, euid=euid)  # type: ignore[arg-type]

    assert runner_reason == expected
    assert router_reason == expected
    assert runner_reason == router_reason


@pytest.mark.parametrize(
    ("override", "expected"),
    (
        ({"isolated": 0}, "isolated_flag_missing"),
        ({"ignore_environment": 0}, "ignore_environment_flag_missing"),
        ({"no_user_site": 0}, "no_user_site_flag_missing"),
        ({"safe_path": False}, "safe_path_flag_missing"),
    ),
)
def test_every_isolated_invocation_flag_fails_closed(
    override: dict[str, int | bool],
    expected: str,
) -> None:
    arguments: dict[str, int | bool | Path | ExecutableMetadata] = {
        "executable": Path("/trusted/python"),
        "metadata": _regular(0o775, 1000),
        "euid": 1000,
        "isolated": 1,
        "ignore_environment": 1,
        "no_user_site": 1,
        "safe_path": True,
    }
    arguments.update(override)

    assert runner._isolated_python_reason(**arguments) == expected  # type: ignore[arg-type]


def test_bounded_observation_has_exact_non_secret_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    injected = "must-not-appear-in-bounded-observation"
    monkeypatch.setenv("GITHUB_ACTIONS", injected)
    monkeypatch.setenv("RUNNER_ENVIRONMENT", injected)
    monkeypatch.setenv("pythonLocation", injected)
    metadata = _regular(0o775, 1000)
    reason = runner._python_executable_reason(
        Path("/trusted/python"),
        metadata,  # type: ignore[arg-type]
        euid=1000,
    )

    observation = runner._python_trust_observation(
        Path("/trusted/python"),
        metadata,  # type: ignore[arg-type]
        euid=1000,
        egid=1000,
        reason=reason,
    )
    assert set(observation) == {
        "decision",
        "egid",
        "euid",
        "executable_absolute",
        "file_gid",
        "file_mode",
        "file_regular",
        "file_uid",
        "ignore_environment",
        "isolated",
        "no_user_site",
        "owner_executable",
        "reason",
        "safe_path",
    }
    assert observation["file_mode"] == "0775"
    assert observation["decision"] == "accept"
    assert observation["reason"] is None
    assert injected not in json.dumps(observation, sort_keys=True)


def test_ci_environment_labels_cannot_change_executable_decision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = Path("/trusted/python")
    metadata = _regular(0o777, os.geteuid())
    expected = runner._python_executable_reason(
        path,
        metadata,  # type: ignore[arg-type]
        euid=os.geteuid(),
    )
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("RUNNER_ENVIRONMENT", "github-hosted")
    monkeypatch.setenv("pythonLocation", "/opt/hostedtoolcache/Python/spoofed")

    assert expected == "executable_world_writable"
    assert (
        runner._python_executable_reason(
            path,
            metadata,  # type: ignore[arg-type]
            euid=os.geteuid(),
        )
        == expected
    )


def test_generic_tool_policy_still_rejects_group_write(tmp_path: Path) -> None:
    tool = (tmp_path / "tool").resolve()
    tool.write_bytes(b"not an executable payload\n")
    tool.chmod(0o775)

    with pytest.raises(router.RoutingDenied, match="strict_tool_rejected"):
        router._trusted_executable(tool, reason="strict_tool_rejected")
