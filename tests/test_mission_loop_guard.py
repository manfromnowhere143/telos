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


def test_recovery_gate_binding_preserves_distinct_frozen_upstream(tmp_path: Path) -> None:
    guard = load_guard_module()
    active = "experiments/iter205/HYPOTHESIS.md"
    frozen = "experiments/iter202/HYPOTHESIS.md"
    for gate in (active, frozen):
        path = tmp_path / gate
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Gate\n", encoding="utf-8")
    contract = {"active_gate": active, "frozen_upstream_gate": frozen}
    continuity = f"Current gate:\n\n- `{frozen}`\n"
    handoff = (
        f"Active gate: `{active}`\n"
        "Frozen upstream gate recorded by runtime-bound `CONTINUITY.md`: "
        f"`{frozen}`\n"
    )

    assert guard.validate_gate_bindings(
        contract, continuity, handoff, root=tmp_path
    ) == []
    same_gate = {"active_gate": frozen, "frozen_upstream_gate": frozen}
    assert "active gate must be distinct from the frozen upstream gate" in (
        guard.validate_gate_bindings(same_gate, continuity, handoff, root=tmp_path)
    )


def test_committed_iter205_recovery_state_is_evidence_bounded() -> None:
    guard = load_guard_module()
    contract = json.loads((ROOT / "mission" / "loop.json").read_text(encoding="utf-8"))

    assert guard.validate_iter205_recovery_state(contract) == []
    contract["current_gate_state"]["iter202_retained_provider_stage"][
        "scenario_executions"
    ] = 1
    assert "iter202 retained provider-stage counts are not exact" in (
        guard.validate_iter205_recovery_state(contract)
    )


def test_iter205_source_of_truth_requires_the_full_recovery_chain() -> None:
    guard = load_guard_module()
    required = (
        ".github/workflows/iter204-execute.yml",
        "scripts/ci_iter204_smoke.sh",
        "scripts/ci_iter204_execute.sh",
        "scripts/collect_iter204_execution.py",
        "scripts/adjudicate_iter204_infrastructure_recovery.py",
        "scripts/run_iter204_infrastructure_recovery_blind_judge.py",
        "experiments/iter204_iter203_infrastructure_recovery/proof/raw/runtime_manifest.json",
        "experiments/iter204_iter203_infrastructure_recovery/proof/pre_execution_publication_safety.json",
        "experiments/iter204_iter203_infrastructure_recovery/RESULT.md",
        "experiments/iter204_iter203_infrastructure_recovery/proof/pre_dispatch_infrastructure_null.json",
        "experiments/iter204_iter203_infrastructure_recovery/proof/raw/public_dispatch_metadata/manifest.json",
        ".github/workflows/iter205-execute.yml",
        "experiments/iter205_iter204_workflow_context_recovery/HYPOTHESIS.md",
        "scripts/build_iter205_runtime_manifest.py",
        "scripts/validate_iter205_runtime_recovery.py",
    )

    for missing in required:
        contract = json.loads((ROOT / "mission" / "loop.json").read_text(encoding="utf-8"))
        contract["source_of_truth"].remove(missing)
        assert "iter203/iter204/iter205 source-of-truth set is incomplete" in (
            guard.validate_iter205_recovery_state(contract)
        )


def test_current_recovery_guard_distinguishes_push_records_from_dispatch_runs() -> None:
    guard = load_guard_module()
    contract = json.loads((ROOT / "mission" / "loop.json").read_text(encoding="utf-8"))

    contract["current_gate_state"]["iter204_recovery"]["dispatch_history"] = (
        "two workflow_dispatch runs"
    )
    failures = guard.validate_iter205_recovery_state(contract)

    assert "iter204 exact-zero workflow_dispatch boundary differs" in failures


def test_current_recovery_guard_requires_the_narrow_iter205_context_delta() -> None:
    guard = load_guard_module()
    contract = json.loads((ROOT / "mission" / "loop.json").read_text(encoding="utf-8"))

    contract["current_gate_state"]["iter205_recovery"]["allowed_delta"] = (
        "change the workflow"
    )
    failures = guard.validate_iter205_recovery_state(contract)

    assert "iter205 narrow workflow-context correction is absent" in failures


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
