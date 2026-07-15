from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shlex


ROOT = Path(__file__).resolve().parents[1]


def load_guard_module():
    path = ROOT / "scripts" / "validate_mission_loop.py"
    spec = importlib.util.spec_from_file_location("validate_mission_loop", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rendered_commands(module, source: str) -> set[str]:
    return {shlex.join(command) for command in module.executable_ci_commands(source)}


def test_ci_command_parser_accepts_only_standalone_active_run_steps() -> None:
    guard = load_guard_module()
    source = """
jobs:
  verify:
    steps:
      - name: real inline command
        run: python3 scripts/real.py
      - name: real block command
        run: |
          python3 scripts/block.py
      - name: commented out
        # run: python3 scripts/commented.py
      - name: echoed text
        run: echo python3 scripts/echoed.py
      - name: shell-comment bypass
        run: "true # python3 scripts/disabled.py"
      - name: unreachable compound command
        run: false && python3 scripts/conditional.py
      - name: statically disabled step
        if: false
        run: python3 scripts/step-disabled.py
      - if: false
        run: python3 scripts/inline-step-disabled.py
  disabled-job:
    if: false
    runs-on: ubuntu-latest
    steps:
      - run: python3 scripts/job-disabled.py
"""

    assert rendered_commands(guard, source) == {
        "echo python3 scripts/echoed.py",
        "python3 scripts/block.py",
        "python3 scripts/real.py",
        "true",
    }


def test_current_validation_requires_exact_structured_membership() -> None:
    guard = load_guard_module()
    required = "python3 scripts/required.py"
    contract = {"current_validation": [required + " --different-command"]}
    ci = f"""jobs:
  verify:
    steps:
      - run: {required} --different-command
"""

    failures = guard.validate_current_validation(
        contract,
        ci,
        required_commands=(required,),
    )

    assert failures == [
        f"core mission validation command missing from contract: {required}"
    ]


def test_disabled_or_commented_ci_text_cannot_satisfy_contract() -> None:
    guard = load_guard_module()
    required = "python3 scripts/required.py"
    contract = {"current_validation": [required]}
    ci = f'''jobs:
  verify:
    steps:
      - name: disabled
        run: "true # {required}"
      - name: comment only
        # run: {required}
'''

    failures = guard.validate_current_validation(
        contract,
        ci,
        required_commands=(required,),
    )

    assert failures == [
        f"mission validation command is not an executable CI step: {required}"
    ]


def test_ci_parser_rejects_error_suppression_dependencies_and_run_overrides() -> None:
    guard = load_guard_module()
    source = """
jobs:
  safe:
    steps:
      - run: python3 scripts/safe.py
  step-error-suppressed:
    steps:
      - continue-on-error: true
        run: python3 scripts/step-error.py
      - "continue-on-error": true
        run: python3 scripts/quoted-step-error.py
  job-error-suppressed:
    continue-on-error: true
    steps:
      - run: python3 scripts/job-error.py
  dependency-gated:
    needs: safe
    steps:
      - run: python3 scripts/dependency.py
  alternate-shell:
    steps:
      - shell: python
        run: python3 scripts/shell.py
  relocated-step:
    steps:
      - working-directory: nested
        run: python3 scripts/step-directory.py
  remapped-job-defaults:
    defaults:
      run:
        working-directory: nested
    steps:
      - run: python3 scripts/job-directory.py
  merged-job-policy:
    <<: *job_policy
    steps:
      - run: python3 scripts/merged-job.py
  merged-step-policy:
    steps:
      - <<: *step_policy
        run: python3 scripts/merged-step.py
  aliased-job-defaults:
    defaults: *run_defaults
    steps:
      - run: python3 scripts/aliased-defaults.py
"""

    assert rendered_commands(guard, source) == {"python3 scripts/safe.py"}


def test_ci_parser_rejects_workflow_wide_shell_or_directory_defaults() -> None:
    guard = load_guard_module()
    for override in (
        "shell: bash",
        "working-directory: nested",
        "'shell': bash",
        '"working-directory": nested',
        "<<: *run_defaults",
    ):
        source = f"""
defaults:
  run:
    {override}
jobs:
  verify:
    steps:
      - run: python3 scripts/required.py
"""
        assert rendered_commands(guard, source) == set()


def test_committed_contract_has_executable_ci_coverage() -> None:
    guard = load_guard_module()
    contract = json.loads((ROOT / "mission" / "loop.json").read_text(encoding="utf-8"))
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert guard.validate_current_validation(contract, ci) == []
