"""Known-good and known-bad controls for the Iter242 CI successor."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml
from yaml.constructor import ConstructorError


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/ci.yml"
EXPECTED_WORKFLOW_SHA256 = "aaa6fb8de99d4774976fbed923eafc5985ce5e0cbdcbea1fc06fb47ea3084971"
EXPECTED_TEST_COMMAND = "python3 -I scripts/run_iter241_pytest.py --run"
CHECKOUT = "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0"
BOOTSTRAP_RUN = (
    "/usr/bin/printf '%s  %s\\n' "
    "'e4c7320047bf66e75709649ceaa29239e206ca5a7fe85b63456ed46788af1638' "
    "'scripts/bootstrap_iter245_python.sh' | /usr/bin/sha256sum --check --strict -\n"
    "/usr/bin/printf '%s  %s\\n' "
    "'2cf5ffa33ea82367f62d5e96d34a42f6aacac522520f918d51c735409f0be374' "
    "'scripts/extract_iter245_python.py' | /usr/bin/sha256sum --check --strict -\n"
    "/usr/bin/printf '%s  %s\\n' "
    "'4c3bf499a03e0f251ddaa75e46eb0c6eb0ce0673fbbe17cfa66aa600affcf159' "
    "'scripts/validate_iter245_python_bootstrap.py' | "
    "/usr/bin/sha256sum --check --strict -\n"
    '/usr/bin/bash scripts/bootstrap_iter245_python.sh --bootstrap "${{ matrix.python-version }}"\n'
)


class StrictLoader(yaml.BaseLoader):
    """Preserve GitHub's scalar keys and reject duplicate YAML mappings."""

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict:
        if not isinstance(node, yaml.MappingNode):
            raise ConstructorError(None, None, "expected a mapping", node.start_mark)
        result: dict = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in result:
                raise ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"duplicate key {key!r}",
                    key_node.start_mark,
                )
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def validation_errors(raw: bytes) -> list[str]:
    errors: list[str] = []
    if hashlib.sha256(raw).hexdigest() != EXPECTED_WORKFLOW_SHA256:
        errors.append("workflow digest differs")
    try:
        document = yaml.load(raw.decode("utf-8"), Loader=StrictLoader)
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        return [*errors, f"workflow parse failed: {exc}"]
    if not isinstance(document, dict):
        return [*errors, "workflow root differs"]
    if document.get("on") != {"push": "", "pull_request": ""}:
        errors.append("workflow triggers differ")
    if document.get("permissions") != {"contents": "read"}:
        errors.append("workflow permissions differ")
    jobs = document.get("jobs")
    verify = jobs.get("verify") if isinstance(jobs, dict) else None
    if not isinstance(verify, dict):
        return [*errors, "verify job is absent"]
    if verify.get("runs-on") != "ubuntu-24.04":
        errors.append("runner differs")
    if verify.get("timeout-minutes") != "60":
        errors.append("job timeout differs")
    if verify.get("continue-on-error") is not None or verify.get("if") is not None:
        errors.append("job failure semantics differ")
    strategy = verify.get("strategy")
    if strategy != {
        "fail-fast": "false",
        "matrix": {"python-version": ["3.11", "3.12"]},
    }:
        errors.append("matrix differs")
    steps = verify.get("steps")
    if not isinstance(steps, list):
        return [*errors, "steps are absent"]
    checkout = next(
        (step for step in steps if isinstance(step, dict) and step.get("uses") == CHECKOUT),
        None,
    )
    if not isinstance(checkout, dict) or checkout.get("with") != {
        "fetch-depth": "0",
        "persist-credentials": "false",
    }:
        errors.append("checkout boundary differs")
    setup = next(
        (
            step
            for step in steps
            if isinstance(step, dict)
            and isinstance(step.get("uses"), str)
            and step["uses"].startswith("actions/setup-python@")
        ),
        None,
    )
    if setup is not None:
        errors.append("setup-python was reintroduced")
    bootstrap = next(
        (
            step
            for step in steps
            if isinstance(step, dict)
            and step.get("name") == "Bootstrap offline verified Python"
        ),
        None,
    )
    if not isinstance(bootstrap, dict) or bootstrap.get("run") != BOOTSTRAP_RUN:
        errors.append("offline verified Python bootstrap differs")
    tests = next(
        (
            step
            for step in steps
            if isinstance(step, dict) and step.get("name") == "Tests"
        ),
        None,
    )
    if (
        not isinstance(tests, dict)
        or tests.get("run") != EXPECTED_TEST_COMMAND
        or tests.get("continue-on-error") is not None
        or tests.get("if") is not None
    ):
        errors.append("authenticated test command differs")
    return errors


def mutate(old: bytes, new: bytes) -> bytes:
    raw = WORKFLOW.read_bytes()
    assert raw.count(old) == 1
    return raw.replace(old, new, 1)


def test_current_ci_is_the_exact_iter245_successor() -> None:
    assert validation_errors(WORKFLOW.read_bytes()) == []


@pytest.mark.parametrize(
    "candidate",
    (
        lambda: mutate(b"    timeout-minutes: 60\n", b"    timeout-minutes: 600\n"),
        lambda: mutate(b"          persist-credentials: false\n", b"          persist-credentials: true\n"),
        lambda: mutate(
            f"        run: {EXPECTED_TEST_COMMAND}\n".encode(),
            b"        run: pytest -q\n",
        ),
        lambda: mutate(b"permissions:\n  contents: read\n", b"permissions:\n  contents: write\n"),
    ),
)
def test_ci_known_bad_mutations_fail_closed(candidate) -> None:
    assert validation_errors(candidate())


def test_every_current_recovery_entrypoint_uses_authenticated_pytest() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    handoff = (ROOT / "docs/HANDOFF-2026-07-21-iter242.md").read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    for surface in (agents, handoff, workflow):
        assert EXPECTED_TEST_COMMAND in surface
    assert "\npytest -q\n" not in agents
    assert "\npytest -q\n" not in handoff
    assert "        run: pytest -q\n" not in workflow
