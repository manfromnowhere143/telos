"""Required-CI integration checks for iter238 offline controls."""

from pathlib import Path

from scripts import run_ci_closure


ROOT = Path(__file__).resolve().parents[1]

REQUIRED = {
    "Iter238 public-claim coverage guard": (
        "env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY -u GOOGLE_API_KEY "
        "python3 scripts/validate_claim_registry.py"
    ),
    "Iter238 retrospective protected-byte coverage guard": (
        "python3 scripts/validate_seal_registry.py"
    ),
    "Iter238 workflow-file lifecycle coverage guard": (
        "python3 scripts/validate_workflow_registry.py"
    ),
}


def test_iter238_offline_guards_are_executable_ci_steps() -> None:
    commands = dict(run_ci_closure.declared_commands())
    for name, command in REQUIRED.items():
        assert commands.get(name) == command


def test_mutable_live_audit_is_not_in_deterministic_ci() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "audit_workflow_server_state.py" not in workflow


def test_derived_closure_includes_all_iter238_offline_guards() -> None:
    commands = {command for _, command in run_ci_closure.declared_commands()}
    assert set(REQUIRED.values()) <= commands
