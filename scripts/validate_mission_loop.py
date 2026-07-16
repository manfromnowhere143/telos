#!/usr/bin/env python3
"""Validate the public mission loop contract."""

from __future__ import annotations

import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any


ROOT = Path.cwd()
CONTRACT = ROOT / "mission" / "loop.json"
DOC = ROOT / "docs" / "MISSION_LOOP.md"
CONTINUITY = ROOT / "CONTINUITY.md"
HANDOFF = ROOT / "HANDOFF.md"
CI = ROOT / ".github" / "workflows" / "ci.yml"

REQUIRED_PHASES = [
    "pre_register",
    "execute",
    "collect_evidence",
    "audit",
    "publish_result",
    "learn_or_stop",
    "handoff",
]

CORE_VALIDATION_COMMANDS = (
    "python3 -m compileall telos scripts tests",
    "ruff check .",
    "pytest -q",
    "python3 scripts/validate_json.py",
    "python3 scripts/validate_docs.py",
    "python3 scripts/validate_current_paper.py",
    "python3 scripts/validate_mission_loop.py",
    "python3 scripts/validate_supply_chain.py",
    "python3 scripts/validate_detector_methodology_correction.py",
    "python3 scripts/validate_iter200_corrected_result.py",
    "python3 scripts/build_iter200_solve_targets.py --check",
    "python3 scripts/build_iter202_solve_targets.py --check",
    "python3 scripts/audit_iter202_sample_overlap.py --check",
    "python3 scripts/build_iter202_image_lock.py --check",
    "python3 scripts/build_iter203_safety_recovery.py --check",
    "python3 scripts/build_iter203_runtime_manifest.py --check",
    "python3 scripts/validate_iter203_publication_safety.py --check",
    "python3 scripts/validate_iter203_infrastructure_null.py",
    "python3 scripts/validate_iter204_pre_dispatch_null.py",
    "python3 scripts/build_iter205_runtime_manifest.py --check",
    "python3 scripts/validate_iter205_publication_safety.py --check",
    "python3 scripts/validate_iter205_runtime_recovery.py",
    "python3 scripts/validate_target_survey.py",
    "python3 scripts/validate_public_slice.py",
    "python3 scripts/validate_agent_behavior_slice.py",
    "python3 scripts/validate_deterministic_edit_slice.py",
    "python3 scripts/validate_provider_model_pilot_slice.py",
    "python3 scripts/validate_learning_ledger.py",
    "python3 scripts/validate_handoff.py",
)

SHELL_CONTROL_TOKENS = {
    "&",
    "&&",
    "(",
    ")",
    ";",
    ";&",
    ";;&",
    ";;",
    "<",
    "<<",
    ">",
    ">>",
    "|",
    "||",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_gate(src: str) -> str | None:
    match = re.search(r"Current gate:\n\n- `([^`]+)`", src)
    if match:
        return match.group(1)
    match = re.search(r"Active gate: `([^`]+)`", src)
    if match:
        return match.group(1)
    return None


def validate_gate_bindings(
    contract: dict[str, Any], continuity: str, handoff: str, *, root: Path = ROOT
) -> list[str]:
    """Bind the additive active gate separately from frozen runtime authority."""

    failures: list[str] = []
    active_gate = contract.get("active_gate")
    frozen_upstream_gate = contract.get("frozen_upstream_gate")
    continuity_gate = extract_gate(continuity)
    if frozen_upstream_gate != continuity_gate:
        failures.append("contract frozen upstream gate does not match CONTINUITY.md")
    if active_gate != extract_gate(handoff):
        failures.append("contract active gate does not match HANDOFF.md")
    if not isinstance(active_gate, str) or not (root / active_gate).exists():
        failures.append("contract active gate path does not exist")
    if not isinstance(frozen_upstream_gate, str) or not (root / frozen_upstream_gate).exists():
        failures.append("contract frozen upstream gate path does not exist")
    if active_gate == frozen_upstream_gate:
        failures.append("active gate must be distinct from the frozen upstream gate")
    handoff_frozen = re.findall(
        r"Frozen upstream gate recorded by runtime-bound `CONTINUITY\.md`: `([^`]+)`",
        handoff,
    )
    if handoff_frozen != [frozen_upstream_gate]:
        failures.append("HANDOFF.md does not bind the contract frozen upstream gate exactly once")
    return failures


def validate_iter205_recovery_state(contract: dict[str, Any]) -> list[str]:
    """Validate the sealed iter203/iter204 nulls and fail-closed iter205 recovery."""

    failures: list[str] = []
    expected_provider = {
        "solver_calls": 53,
        "scenario_calls": 39,
        "model_patches": 50,
        "scenario_programs": 38,
        "original_absent_scenarios": 1,
        "scenario_executions": 0,
        "official_certification_executions": 0,
    }
    state = contract.get("current_gate_state", {})
    if state.get("iter202_retained_provider_stage") != expected_provider:
        failures.append("iter202 retained provider-stage counts are not exact")
    expected_safety = {
        "status": "scenario_safety_protocol_execution_null",
        "safe_programs": 29,
        "rejected_programs": 9,
        "findings": 21,
        "rate_quantities": "no N, k, or u",
    }
    if state.get("iter202_safety_gate") != expected_safety:
        failures.append("iter202 safety-null disposition is not exact")
    infrastructure_null = state.get("iter203_recovery", {})
    if infrastructure_null.get("status") != "execution_infrastructure_null":
        failures.append("iter203 infrastructure-null status is not exact")
    if "50/50 first Docker run invocations returned exit 125" not in infrastructure_null.get(
        "launch_outcome", ""
    ):
        failures.append("iter203 launch-failure count is not exact")
    if infrastructure_null.get("scientific_execution") != (
        "0 patches applied, 0 official certifications, 0 scenario executions"
    ):
        failures.append("iter203 zero-execution boundary is not exact")
    if "not retained" not in infrastructure_null.get("stderr_limitation", ""):
        failures.append("iter203 missing-stderr evidence limitation is absent")
    if "reconstructed" not in infrastructure_null.get("root_cause_status", ""):
        failures.append("iter203 reconstructed root-cause status is absent")

    recovery = state.get("iter204_recovery", {})
    if recovery.get("status") != "pre_dispatch_infrastructure_null":
        failures.append("iter204 pre-dispatch-null status is not exact")
    if "same 50 valid patches" not in recovery.get("frozen_scientific_scope", ""):
        failures.append("iter204 does not preserve the all-patch scientific scope")
    if "compress=false" not in recovery.get("runtime_change", ""):
        failures.append("iter204 does not bind the narrow log-driver repair")
    if "29465584664 and 29465924803" not in recovery.get("public_push_records", ""):
        failures.append("iter204 exact push parse-failure records are absent")
    if "zero jobs and artifacts" not in recovery.get("public_push_records", ""):
        failures.append("iter204 zero-job/artifact push boundary is absent")
    if "at least one locally observed" not in recovery.get("dispatch_rejection", ""):
        failures.append("iter204 bounded local request observation is absent")
    if "exact request count not publicly auditable" not in recovery.get(
        "dispatch_rejection", ""
    ):
        failures.append("iter204 rejected-request count limitation is absent")
    if recovery.get("dispatch_history") != "exactly zero workflow_dispatch runs":
        failures.append("iter204 exact-zero workflow_dispatch boundary differs")
    if "no N, k, or u" not in recovery.get("scientific_execution", ""):
        failures.append("iter204 no-rate boundary is absent")
    if "cannot be retried or mutated" not in recovery.get("failure_rule", ""):
        failures.append("iter204 no-retry source-correction rule is absent")

    successor = state.get("iter205_recovery", {})
    if (
        successor.get("status")
        != "active_pre_dispatch_pre_scientific_output_workflow_context_recovery"
    ):
        failures.append("iter205 recovery readiness status is not exact")
    if "same 50 valid patches" not in successor.get("frozen_scientific_scope", ""):
        failures.append("iter205 does not preserve the all-patch scientific scope")
    if "job-level to step-level env" not in successor.get("allowed_delta", ""):
        failures.append("iter205 narrow workflow-context correction is absent")
    if "empty all-event and workflow_dispatch histories" not in successor.get(
        "selection_rule", ""
    ):
        failures.append("iter205 empty-history preflight is absent")
    if "first global run" not in successor.get("selection_rule", ""):
        failures.append("iter205 first-global-run selection is absent")
    if "GITHUB_RUN_ATTEMPT=1" not in successor.get("selection_rule", ""):
        failures.append("iter205 run-attempt-one rule is absent")
    if "requires iter206" not in successor.get("failure_rule", ""):
        failures.append("iter205 failure rule does not advance to iter206")

    claim = contract.get("claim_boundary", "")
    for fragment in (
        "iter203 is a separately published execution-infrastructure null",
        "53/53 solver calls",
        "39/39 eligible scenario calls",
        "50 model patches",
        "38 extracted scenario programs",
        "admitted 29 programs and rejected 9 with 21 findings",
        "scenario-safety protocol/execution null",
        "no N, k, or u",
        "29460393525",
        "all 50/50 first Docker run invocations returned exit 125",
        "zero workflow artifacts were uploaded",
        "exact daemon stderr was redirected into temporary files and not retained",
        "root cause is reconstructed",
        "iter204 is a separately published pre-dispatch infrastructure null",
        "exactly two public push records",
        "At least one locally observed authorized dispatch API request returned HTTP 422",
        "exact rejected-request count is not publicly auditable",
        "no workflow_dispatch run ID or run attempt",
        "workflow_dispatch run count is exactly zero",
        "No provider, container, patch, certification, scenario, adjudication, or judge process started",
        "Iter205 is the active",
        "job-level to step-level env",
        "first global workflow_dispatch run at attempt 1",
        "requires iter206",
    ):
        if fragment not in claim:
            failures.append(f"claim boundary missing current recovery fact: {fragment}")

    required_sources = {
        "experiments/iter202_natural_rate_scaled/RESULT.md",
        "experiments/iter202_natural_rate_scaled/proof/learning_record.json",
        "experiments/iter203_iter202_safety_recovery/HYPOTHESIS.md",
        "experiments/iter203_iter202_safety_recovery/UPSTREAM_PROTOCOL_NULL.md",
        "experiments/iter203_iter202_safety_recovery/RESULT.md",
        "experiments/iter203_iter202_safety_recovery/proof/learning_record.json",
        "experiments/iter203_iter202_safety_recovery/proof/infrastructure_null.json",
        "experiments/iter204_iter203_infrastructure_recovery/HYPOTHESIS.md",
        "experiments/iter204_iter203_infrastructure_recovery/RESULT.md",
        "experiments/iter204_iter203_infrastructure_recovery/proof/learning_record.json",
        "experiments/iter204_iter203_infrastructure_recovery/proof/learning_record.pre_dispatch_null.json",
        "experiments/iter204_iter203_infrastructure_recovery/proof/pre_dispatch_infrastructure_null.json",
        "experiments/iter204_iter203_infrastructure_recovery/proof/raw/public_dispatch_metadata/manifest.json",
        "experiments/iter204_iter203_infrastructure_recovery/proof/raw/runtime_manifest.json",
        "experiments/iter204_iter203_infrastructure_recovery/proof/pre_execution_publication_safety.json",
        "experiments/iter205_iter204_workflow_context_recovery/HYPOTHESIS.md",
        "experiments/iter205_iter204_workflow_context_recovery/proof/learning_record.json",
        "experiments/iter205_iter204_workflow_context_recovery/proof/raw/runtime_manifest.json",
        "experiments/iter205_iter204_workflow_context_recovery/proof/pre_execution_publication_safety.json",
        ".github/workflows/iter203-execute.yml",
        ".github/workflows/iter204-execute.yml",
        ".github/workflows/iter205-execute.yml",
        "scripts/build_iter203_safety_recovery.py",
        "scripts/build_iter203_runtime_manifest.py",
        "scripts/validate_iter203_publication_safety.py",
        "scripts/collect_iter203_execution.py",
        "scripts/validate_iter203_infrastructure_null.py",
        "scripts/build_iter204_runtime_manifest.py",
        "scripts/capture_iter204_runtime_host.py",
        "scripts/prepare_iter204_output_directory.py",
        "scripts/publish_iter204_runtime_diagnostic.py",
        "scripts/ci_iter204_smoke.sh",
        "scripts/ci_iter204_execute.sh",
        "scripts/collect_iter204_execution.py",
        "scripts/adjudicate_iter204_infrastructure_recovery.py",
        "scripts/run_iter204_infrastructure_recovery_blind_judge.py",
        "scripts/validate_iter204_publication_safety.py",
        "scripts/validate_iter204_runtime_recovery.py",
        "scripts/validate_iter204_pre_dispatch_null.py",
        "scripts/adjudicate_iter205_workflow_context_recovery.py",
        "scripts/build_iter205_runtime_manifest.py",
        "scripts/capture_iter205_runtime_host.py",
        "scripts/ci_iter205_smoke.sh",
        "scripts/ci_iter205_execute.sh",
        "scripts/collect_iter205_execution.py",
        "scripts/prepare_iter205_output_directory.py",
        "scripts/publish_iter205_runtime_diagnostic.py",
        "scripts/run_iter205_workflow_context_recovery_blind_judge.py",
        "scripts/validate_iter205_publication_safety.py",
        "scripts/validate_iter205_runtime_recovery.py",
        "tests/test_iter204_pre_dispatch_null.py",
        "tests/test_iter205_workflow_context_recovery.py",
        "experiments/iter203_iter202_safety_recovery/proof/raw/runtime_manifest.json",
        "experiments/iter203_iter202_safety_recovery/proof/pre_execution_publication_safety.json",
    }
    sources = contract.get("source_of_truth", [])
    if not isinstance(sources, list) or not required_sources.issubset(set(sources)):
        failures.append("iter203/iter204/iter205 source-of-truth set is incomplete")
    else:
        missing_required_sources = sorted(
            source for source in required_sources if not (ROOT / source).is_file()
        )
        if missing_required_sources:
            failures.append(
                "iter203/iter204/iter205 source-of-truth files are absent: "
                + ", ".join(missing_required_sources)
            )
    return failures


def validate_iter204_recovery_state(contract: dict[str, Any]) -> list[str]:
    """Compatibility alias for the current iter203--iter205 recovery validator."""

    return validate_iter205_recovery_state(contract)


def _decode_inline_yaml_scalar(value: str) -> str | None:
    """Decode the small YAML scalar subset accepted for workflow ``run`` values."""

    value = value.strip()
    if not value:
        return None
    if value.startswith('"'):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return None
        return decoded if isinstance(decoded, str) else None
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            return None
        return value[1:-1].replace("''", "'")
    return value


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _block_end(lines: list[str], start: int, indent: int, *, list_item: bool) -> int:
    """Return the exclusive end of one YAML mapping or list-item mapping."""

    for index in range(start + 1, len(lines)):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        candidate_indent = _indent(line)
        if candidate_indent < indent:
            return index
        if list_item and candidate_indent == indent and line.lstrip().startswith("- "):
            return index
        if not list_item and candidate_indent == indent:
            return index
    return len(lines)


def _mapping_has_key(
    lines: list[str],
    start: int,
    end: int,
    *,
    indent: int,
    key: str,
    list_item: bool = False,
) -> bool:
    """Return whether a key occurs directly in one YAML mapping."""

    escaped = re.escape(key)
    key_pattern = re.compile(rf"(?:{escaped}|'{escaped}'|\"{escaped}\")\s*:")
    for index in range(start, end):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if _indent(line) != indent:
            continue
        stripped = line.lstrip()
        if list_item and index == start:
            stripped = re.sub(r"^-\s+", "", stripped, count=1)
        if key_pattern.match(stripped):
            return True
    return False


def _mapping_has_run_default_override(
    lines: list[str], start: int, end: int, *, mapping_indent: int
) -> bool:
    """Reject shell or working-directory remapping below a direct ``defaults`` key."""

    for index in range(start, end):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if _indent(line) != mapping_indent:
            continue
        defaults_match = re.match(
            r"(?:defaults|'defaults'|\"defaults\")\s*:\s*(.*?)\s*$",
            line.lstrip(),
        )
        if defaults_match is None:
            continue
        inline_value = defaults_match.group(1)
        if inline_value and not inline_value.startswith("#"):
            return True
        defaults_end = _block_end(lines, index, mapping_indent, list_item=False)
        for nested in lines[index + 1 : defaults_end]:
            if not nested.strip() or nested.lstrip().startswith("#"):
                continue
            if re.match(
                r"(?:shell|working-directory|'shell'|'working-directory'|"
                r"\"shell\"|\"working-directory\")\s*:",
                nested.lstrip(),
            ):
                return True
            if re.match(r"(?:<<\s*:|[^:#]+:\s*\*)", nested.lstrip()):
                return True
    return False


def _workflow_has_run_default_override(lines: list[str]) -> bool:
    """Return whether workflow-wide defaults can change command interpretation."""

    return _mapping_has_run_default_override(
        lines,
        0,
        len(lines),
        mapping_indent=0,
    )


def _run_step_is_unconditional(lines: list[str], run_index: int, run_indent: int) -> bool:
    """Accept a run key only on a direct, fail-closed execution path."""

    step_start: int | None = None
    step_indent: int | None = None
    for index in range(run_index, -1, -1):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        candidate_indent = _indent(line)
        if line.lstrip().startswith("- ") and candidate_indent <= run_indent:
            step_start = index
            step_indent = candidate_indent
            break
    if step_start is None or step_indent is None:
        return False

    steps_start: int | None = None
    steps_indent: int | None = None
    for index in range(step_start - 1, -1, -1):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        candidate_indent = _indent(line)
        if candidate_indent < step_indent and re.fullmatch(r"steps\s*:\s*", line.lstrip()):
            steps_start = index
            steps_indent = candidate_indent
            break
        if candidate_indent < step_indent - 2:
            break
    if steps_start is None or steps_indent is None:
        return False

    step_end = _block_end(lines, step_start, step_indent, list_item=True)
    if any(
        _mapping_has_key(
            lines,
            step_start,
            step_end,
            indent=step_indent if key_on_list_item else step_indent + 2,
            key=key,
            list_item=key_on_list_item,
        )
        for key in ("if", "continue-on-error", "shell", "working-directory", "<<")
        for key_on_list_item in (True, False)
    ):
        return False

    job_start: int | None = None
    job_indent: int | None = None
    for index in range(steps_start - 1, -1, -1):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        candidate_indent = _indent(line)
        if candidate_indent < steps_indent and re.fullmatch(
            r"[^:#][^:]*\s*:\s*", line.lstrip()
        ):
            job_start = index
            job_indent = candidate_indent
            break
    if job_start is None or job_indent is None:
        return False

    job_end = _block_end(lines, job_start, job_indent, list_item=False)
    if any(
        _mapping_has_key(
            lines,
            job_start,
            job_end,
            indent=job_indent + 2,
            key=key,
        )
        for key in ("if", "continue-on-error", "needs", "<<")
    ):
        return False
    return not _mapping_has_run_default_override(
        lines,
        job_start,
        job_end,
        mapping_indent=job_indent + 2,
    )


def ci_run_scripts(source: str) -> list[str]:
    """Extract active GitHub Actions ``run`` scalars without treating comments as steps."""

    lines = source.splitlines()
    workflow_defaults_safe = not _workflow_has_run_default_override(lines)
    scripts: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)
        match = re.fullmatch(r"(?:-\s+)?run\s*:\s*(.*?)\s*", stripped)
        if not match:
            index += 1
            continue

        value = match.group(1)
        unconditional = workflow_defaults_safe and _run_step_is_unconditional(
            lines, index, indent
        )
        block_match = re.fullmatch(r"([|>])(?:[+-]?\d*|\d*[+-]?)(?:\s+#.*)?", value)
        if not block_match:
            decoded = _decode_inline_yaml_scalar(value)
            if unconditional and decoded is not None:
                scripts.append(decoded)
            index += 1
            continue

        block_lines: list[str] = []
        index += 1
        while index < len(lines):
            candidate = lines[index]
            candidate_stripped = candidate.lstrip(" ")
            candidate_indent = len(candidate) - len(candidate_stripped)
            if candidate.strip() and candidate_indent <= indent:
                break
            block_lines.append(candidate)
            index += 1
        nonblank_indents = [
            len(item) - len(item.lstrip(" ")) for item in block_lines if item.strip()
        ]
        if not nonblank_indents:
            continue
        block_indent = min(nonblank_indents)
        deindented = [
            item[block_indent:] if item.strip() else "" for item in block_lines
        ]
        separator = "\n" if block_match.group(1) == "|" else " "
        if unconditional:
            scripts.append(separator.join(deindented))
    return scripts


def standalone_shell_command(script: str) -> tuple[str, ...] | None:
    """Return tokens only when a run scalar is one unconditional simple command."""

    logical_lines: list[str] = []
    pending = ""
    for raw_line in script.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith("\\") and not line.endswith("\\\\"):
            pending += line[:-1].rstrip() + " "
            continue
        logical_lines.append(pending + line)
        pending = ""
    if pending or len(logical_lines) != 1:
        return None

    lexer = shlex.shlex(
        logical_lines[0],
        posix=True,
        punctuation_chars="();<>|&",
    )
    lexer.whitespace_split = True
    lexer.commenters = "#"
    try:
        tokens = tuple(lexer)
    except ValueError:
        return None
    if not tokens or any(token in SHELL_CONTROL_TOKENS for token in tokens):
        return None
    return tokens


def executable_ci_commands(source: str) -> set[tuple[str, ...]]:
    """Return stand-alone commands that GitHub Actions will actually execute."""

    commands: set[tuple[str, ...]] = set()
    for script in ci_run_scripts(source):
        command = standalone_shell_command(script)
        if command is not None:
            commands.add(command)
    return commands


def validate_current_validation(
    contract: dict[str, Any],
    ci: str,
    *,
    required_commands: tuple[str, ...] = CORE_VALIDATION_COMMANDS,
) -> list[str]:
    """Validate exact contract membership and executable CI coverage."""

    failures: list[str] = []
    raw_commands = contract.get("current_validation")
    if not isinstance(raw_commands, list) or not raw_commands:
        return ["current_validation must be a nonempty command list"]
    if any(not isinstance(command, str) for command in raw_commands):
        return ["current_validation entries must all be strings"]

    commands = list(raw_commands)
    if len(commands) != len(set(commands)):
        failures.append("current_validation contains duplicate commands")

    parsed_commands: dict[str, tuple[str, ...]] = {}
    for command in commands:
        parsed = standalone_shell_command(command)
        if parsed is None or shlex.join(parsed) != command:
            failures.append(f"current_validation command is not canonical: {command!r}")
            continue
        parsed_commands[command] = parsed

    for required in required_commands:
        if required not in commands:
            failures.append(f"core mission validation command missing from contract: {required}")

    ci_commands = executable_ci_commands(ci)
    for command, parsed in parsed_commands.items():
        if parsed not in ci_commands:
            failures.append(f"mission validation command is not an executable CI step: {command}")
    return failures


def required_command(specification: str) -> str:
    """Expand historical script specifications into exact contract commands."""

    if specification.startswith(("python3 ", "pytest ", "ruff ")):
        return specification
    return f"python3 scripts/{specification}"


def main() -> int:
    failures: list[str] = []

    for path in [CONTRACT, DOC, CONTINUITY, HANDOFF, CI]:
        if not path.exists():
            failures.append(f"missing required mission-loop file: {path.relative_to(ROOT)}")

    if failures:
        for failure in failures:
            print(f"mission loop guard: {failure}")
        return 1

    contract = read_json(CONTRACT)
    doc = DOC.read_text(encoding="utf-8")
    continuity = CONTINUITY.read_text(encoding="utf-8")
    handoff = HANDOFF.read_text(encoding="utf-8")
    ci = CI.read_text(encoding="utf-8")

    if contract.get("mission_id") != "telos":
        failures.append("mission_id must be telos")
    if contract.get("standard") != "maestro-compatible-evidence-loop-v1":
        failures.append("unexpected mission loop standard")
    semantics = contract.get("claim_boundary_semantics", {})
    if semantics.get("current_field") != "claim_boundary" or semantics.get(
        "historical_field"
    ) != "historical_claim_ledger":
        failures.append("current and historical claim authorities are not explicit")
    if not str(contract.get("historical_claim_ledger_notice", "")).startswith(
        "NONCURRENT PROVENANCE ONLY"
    ):
        failures.append("historical claim ledger lacks a fail-closed noncurrent notice")
    correction = contract.get("active_gate_correction", {})
    if correction.get(
        "supersedes_stale_iter197_iter200_iter201_iter202_sentences_in_historical_claim_ledger"
    ) is not True:
        failures.append("active-gate correction does not supersede stale historical claims")
    if "Telos operates from its standalone repository" not in contract.get(
        "claim_boundary", ""
    ):
        failures.append("claim boundary must state the standalone repository boundary")

    active_gate = contract.get("active_gate")
    failures.extend(validate_gate_bindings(contract, continuity, handoff))
    failures.extend(validate_iter205_recovery_state(contract))

    phases = [phase.get("phase") for phase in contract.get("loop", [])]
    if phases != REQUIRED_PHASES:
        failures.append(f"mission loop phases mismatch: {phases}")

    discovery = contract.get("aweb_discovery", {})
    queries = discovery.get("queries", [])
    if len(queries) < 4:
        failures.append("Aweb discovery must record the checked catalog queries")
    if any(query.get("capability_count") != 0 for query in queries):
        failures.append("nonzero Aweb discovery count requires updating the activation claim")
    if "Register or expose a concrete Aweb/Maestro capability slug" not in discovery.get(
        "activation_gate", ""
    ):
        failures.append("Aweb activation gate is missing")

    failures.extend(validate_current_validation(contract, ci))
    current_validation = contract.get("current_validation", [])
    exact_validation_commands = (
        set(current_validation)
        if isinstance(current_validation, list)
        and all(isinstance(command, str) for command in current_validation)
        else set()
    )

    for specification in [
        "python3 -m compileall telos scripts tests",
        "validate_mission_loop.py",
        "validate_supply_chain.py",
        "validate_detector_methodology_correction.py",
        "validate_iter200_corrected_result.py",
        "build_iter200_solve_targets.py --check",
        "build_iter202_solve_targets.py --check",
        "audit_iter202_sample_overlap.py --check",
        "build_iter202_image_lock.py --check",
        "build_iter203_safety_recovery.py --check",
        "build_iter203_runtime_manifest.py --check",
        "validate_iter203_publication_safety.py --check",
        "validate_iter203_infrastructure_null.py",
        "validate_iter204_pre_dispatch_null.py",
        "build_iter205_runtime_manifest.py --check",
        "validate_iter205_publication_safety.py --check",
        "validate_iter205_runtime_recovery.py",
        "validate_deterministic_edit_slice.py",
        "validate_receipts.py experiments/iter03_codeclash_smoke/proof",
        "audit_codeclash_smoke.py",
        "validate_receipts.py experiments/iter05_agent_behavior_smoke/proof",
        "audit_agent_behavior_smoke.py",
        "validate_receipts.py experiments/iter23_tail_semantics_falsification/proof",
        "audit_tail_semantics_falsification.py",
        "validate_receipts.py experiments/iter24_tail_safety_control/proof",
        "audit_tail_safety_control.py",
        "validate_receipts.py experiments/iter25_tail_safety_mutation_guard/proof",
        "audit_tail_safety_mutation_guard.py",
        "validate_receipts.py experiments/iter26_own_tail_redundancy_mutation_guard/proof",
        "audit_own_tail_redundancy_mutation_guard.py",
        "validate_receipts.py experiments/iter27_semantic_claim_boundary_matrix/proof",
        "audit_semantic_claim_boundary_matrix.py",
        "validate_receipts.py experiments/iter28_public_claim_surface_guard/proof",
        "audit_public_claim_surface_guard.py",
        "validate_receipts.py experiments/iter29_public_claim_surface_negative_guard/proof",
        "audit_public_claim_surface_negative_guard.py",
        "validate_receipts.py experiments/iter30_boundary_matrix_schema_guard/proof",
        "audit_boundary_matrix_schema_guard.py",
        "validate_receipts.py experiments/iter31_claim_boundary_release_manifest/proof",
        "audit_claim_boundary_release_manifest.py",
        "validate_receipts.py experiments/iter32_claim_boundary_release_manifest_negative_guard/proof",
        "audit_claim_boundary_release_manifest_negative_guard.py",
        "validate_receipts.py experiments/iter33_release_manifest_public_sync_guard/proof",
        "audit_release_manifest_public_sync_guard.py",
        "validate_receipts.py experiments/iter34_release_manifest_public_sync_negative_guard/proof",
        "audit_release_manifest_public_sync_negative_guard.py",
        "validate_receipts.py experiments/iter35_release_manifest_self_coverage_guard/proof",
        "audit_release_manifest_self_coverage_guard.py",
        "validate_receipts.py experiments/iter36_release_manifest_self_coverage_negative_guard/proof",
        "audit_release_manifest_self_coverage_negative_guard.py",
        "validate_receipts.py experiments/iter37_release_manifest_self_coverage_public_sync_guard/proof",
        "audit_release_manifest_self_coverage_public_sync_guard.py",
        "validate_receipts.py experiments/iter38_release_manifest_self_coverage_public_sync_negative_guard/proof",
        "audit_release_manifest_self_coverage_public_sync_negative_guard.py",
        "validate_receipts.py experiments/iter39_public_task_protocol_effect_slice/proof",
        "audit_public_task_protocol_effect_slice.py",
        "validate_receipts.py experiments/iter40_public_task_protocol_effect_execution/proof",
        "audit_public_task_protocol_effect_execution.py",
        "validate_receipts.py experiments/iter41_public_task_protocol_effect_runner_recovery/proof",
        "audit_public_task_protocol_effect_runner_recovery.py",
        "validate_receipts.py experiments/iter42_public_task_protocol_effect_execution_retry/proof",
        "audit_public_task_protocol_effect_execution_retry.py",
        "validate_receipts.py experiments/iter43_provider_execution_harness_recovery/proof",
        "audit_provider_execution_harness_recovery.py",
        "validate_receipts.py experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/proof",
        "audit_public_task_protocol_effect_execution_after_harness_recovery.py",
        "validate_receipts.py experiments/iter45_public_task_condition_executor_assembly/proof",
        "audit_public_task_condition_executor_assembly.py",
        "validate_receipts.py experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor/proof",
        "audit_public_task_protocol_effect_execution_with_assembled_executor.py",
        "validate_receipts.py experiments/iter47_provider_task_condition_command_binding_recovery/proof",
        "audit_provider_task_condition_command_binding_recovery.py",
        "validate_receipts.py experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/proof",
        "audit_provider_compatible_protocol_effect_slice_refreeze.py",
        "validate_receipts.py experiments/iter49_provider_compatible_protocol_effect_execution_retry/proof",
        "audit_provider_compatible_protocol_effect_execution_retry.py",
        "validate_receipts.py experiments/iter50_provider_compatible_execution_wrapper_recovery/proof",
        "audit_provider_compatible_execution_wrapper_recovery.py",
        "validate_receipts.py experiments/iter51_provider_compatible_protocol_effect_execution_with_wrapper/proof",
        "audit_provider_compatible_protocol_effect_execution_with_wrapper.py",
        "validate_receipts.py experiments/iter52_provider_condition_runtime_separation_recovery/proof",
        "audit_provider_condition_runtime_separation_recovery.py",
        "validate_receipts.py experiments/iter53_provider_compatible_protocol_effect_execution_after_condition_recovery/proof",
        "audit_provider_compatible_protocol_effect_execution_after_condition_recovery.py",
        "validate_receipts.py experiments/iter54_provider_pair_executor_recovery/proof",
        "audit_provider_pair_executor_recovery.py",
        "validate_receipts.py experiments/iter55_provider_compatible_paid_execution_after_executor_recovery/proof",
        "audit_provider_compatible_paid_execution_after_executor_recovery.py",
        "validate_receipts.py experiments/iter56_provider_auth_recovery_for_paid_protocol_effect/proof",
        "audit_provider_auth_recovery_for_paid_protocol_effect.py",
        "validate_receipts.py experiments/iter57_provider_compatible_paid_execution_after_auth_recovery/proof",
        "audit_provider_compatible_paid_execution_after_auth_recovery.py",
        "validate_receipts.py experiments/iter58_codeclash_vertex_dependency_recovery/proof",
        "audit_codeclash_vertex_dependency_recovery.py",
        "validate_receipts.py experiments/iter59_provider_compatible_paid_execution_after_dependency_recovery/proof",
        "audit_provider_compatible_paid_execution_after_dependency_recovery.py",
        "validate_receipts.py experiments/iter60_provider_model_binding_recovery/proof",
        "audit_provider_model_binding_recovery.py",
        "validate_receipts.py experiments/iter61_vertex_quota_project_binding_recovery/proof",
        "audit_vertex_quota_project_binding_recovery.py",
        "validate_receipts.py experiments/iter62_vertex_bearer_token_path_recovery/proof",
        "audit_vertex_bearer_token_path_recovery.py",
        "validate_receipts.py experiments/iter63_vertex_access_path_parity_recheck/proof",
        "audit_vertex_access_path_parity_recheck.py",
        "validate_receipts.py experiments/iter64_provider_compatible_paid_execution_after_access_path_recovery/proof",
        "audit_provider_compatible_paid_execution_after_access_path_recovery.py",
        "validate_receipts.py experiments/iter65_receipt_schema_prompt_alignment/proof",
        "audit_receipt_schema_prompt_alignment.py",
        "validate_receipts.py experiments/iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment/proof",
        "audit_provider_compatible_paid_execution_after_receipt_prompt_alignment.py",
        "validate_receipts.py experiments/iter67_provider_compatible_expanded_slice_refreeze/proof",
        "audit_provider_compatible_expanded_slice_refreeze.py",
        "validate_receipts.py experiments/iter68_provider_compatible_task_surface_adapter_recovery/proof",
        "audit_provider_compatible_task_surface_adapter_recovery.py",
        "validate_receipts.py experiments/iter69_codeclash_task_surface_source_snapshot_recovery/proof",
        "audit_codeclash_task_surface_source_snapshot_recovery.py",
        "validate_receipts.py experiments/iter70_provider_compatible_expanded_adapter_completion/proof",
        "audit_provider_compatible_expanded_adapter_completion.py",
        "validate_receipts.py experiments/iter71_provider_compatible_expanded_slice_after_adapter_completion/proof",
        "audit_provider_compatible_expanded_slice_after_adapter_completion.py",
        "validate_receipts.py experiments/iter72_provider_compatible_expanded_paid_execution_after_slice_refreeze/proof",
        "audit_provider_compatible_expanded_paid_execution_after_slice_refreeze.py",
        "validate_receipts.py experiments/iter73_expanded_receipt_prompt_recovery_after_paid_block/proof",
        "audit_expanded_receipt_prompt_recovery_after_paid_block.py",
        "validate_receipts.py experiments/iter74_provider_compatible_expanded_paid_retry_after_receipt_prompt_recovery/proof",
        "audit_provider_compatible_expanded_paid_retry_after_receipt_prompt_recovery.py",
        "validate_receipts.py experiments/iter75_provider_compatible_runtime_adc_recovery_after_paid_retry_block/proof",
        "audit_provider_compatible_runtime_adc_recovery_after_paid_retry_block.py",
        "validate_receipts.py experiments/iter76_runtime_adc_recheck_after_operator_refresh/proof",
        "audit_runtime_adc_recheck_after_operator_refresh.py",
        "validate_receipts.py experiments/iter77_runtime_adc_recheck_after_application_default_login/proof",
        "audit_runtime_adc_recheck_after_application_default_login.py",
        "validate_receipts.py experiments/iter78_provider_compatible_expanded_paid_retry_after_adc_recovery/proof",
        "audit_provider_compatible_expanded_paid_retry_after_adc_recovery.py",
        "validate_receipts.py experiments/iter79_dummy_row_call_ceiling_recovery_after_paid_retry_block/proof",
        "audit_dummy_row_call_ceiling_recovery_after_paid_retry_block.py",
        "validate_receipts.py experiments/iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery/proof",
        "audit_dummy_call_ceiling_bounded_paid_retry_after_recovery.py",
        "validate_receipts.py experiments/iter81_expanded_stratified_adapter_validation_consolidation/proof",
        "audit_expanded_stratified_adapter_validation_consolidation.py",
        "validate_receipts.py experiments/iter82_benchmark_facing_protocol_effect_slice_design/proof",
        "audit_benchmark_facing_protocol_effect_slice_design.py",
        "validate_receipts.py experiments/iter83_benchmark_facing_protocol_effect_execution_pilot/proof",
        "audit_benchmark_facing_protocol_effect_execution_pilot.py",
        "validate_receipts.py experiments/iter84_benchmark_facing_null_signal_adjudication/proof",
        "audit_benchmark_facing_null_signal_adjudication.py",
        "validate_receipts.py experiments/iter85_discriminating_task_metric_redesign/proof",
        "audit_discriminating_task_metric_redesign.py",
        "validate_receipts.py experiments/iter86_discriminating_metric_backtest_on_committed_artifacts/proof",
        "audit_discriminating_metric_backtest_on_committed_artifacts.py",
        "validate_receipts.py experiments/iter87_benchmark_facing_discriminating_metric_execution_pilot/proof",
        "audit_benchmark_facing_discriminating_metric_execution_pilot.py",
        "validate_receipts.py experiments/iter88_external_benchmark_readiness_adjudication_after_discriminating_pilot/proof",
        "audit_external_benchmark_readiness_adjudication_after_discriminating_pilot.py",
        "validate_receipts.py experiments/iter89_same_slice_discriminating_metric_stability_replication/proof",
        "audit_same_slice_discriminating_metric_stability_replication.py",
        "validate_receipts.py experiments/iter90_stability_replication_adjudication_after_same_slice_run/proof",
        "audit_stability_replication_adjudication_after_same_slice_run.py",
        "validate_receipts.py experiments/iter91_empirical_validation_suite_design_for_completion_verification/proof",
        "audit_empirical_validation_suite_design_for_completion_verification.py",
        "validate_receipts.py experiments/iter92_empirical_validation_fixture_materialization_for_completion_verification/proof",
        "audit_empirical_validation_fixture_materialization_for_completion_verification.py",
        "validate_receipts.py experiments/iter93_deterministic_strategy_execution_on_materialized_fixtures/proof",
        "audit_deterministic_strategy_execution_on_materialized_fixtures.py",
        "validate_receipts.py experiments/iter94_provider_llm_judge_execution_on_materialized_fixtures/proof",
        "audit_provider_llm_judge_execution_on_materialized_fixtures.py",
        "validate_receipts.py experiments/iter95_provider_llm_judge_prompt_budget_recovery_after_block/proof",
        "audit_provider_llm_judge_prompt_budget_recovery_after_block.py",
        "validate_receipts.py experiments/iter96_provider_llm_judge_bounded_retry_after_prompt_budget_recovery/proof",
        "audit_provider_llm_judge_bounded_retry_after_prompt_budget_recovery.py",
        "validate_receipts.py experiments/iter97_five_strategy_completion_verification_adjudication_after_llm_judge/proof",
        "audit_five_strategy_completion_verification_adjudication_after_llm_judge.py",
        "validate_receipts.py experiments/iter98_external_verifier_telos_differential_suite_design_after_adjudication/proof",
        "audit_external_verifier_telos_differential_suite_design_after_adjudication.py",
        "validate_receipts.py experiments/iter99_external_verifier_telos_differential_fixture_materialization_after_design/proof",
        "audit_external_verifier_telos_differential_fixture_materialization_after_design.py",
        "validate_receipts.py experiments/iter100_deterministic_strategy_execution_on_differential_fixtures_after_materialization/proof",
        "audit_deterministic_strategy_execution_on_differential_fixtures_after_materialization.py",
        "validate_receipts.py experiments/iter101_provider_llm_judge_execution_on_differential_fixtures_after_deterministic/proof",
        "audit_provider_llm_judge_execution_on_differential_fixtures_after_deterministic.py",
        "validate_receipts.py experiments/iter102_provider_llm_judge_differential_retry_recovery_after_block/proof",
        "audit_provider_llm_judge_differential_retry_recovery_after_block.py",
        "validate_receipts.py experiments/iter103_differential_provider_llm_judge_full_retry_after_block_recovery/proof",
        "audit_differential_provider_llm_judge_full_retry_after_block_recovery.py",
        "validate_receipts.py experiments/iter104_five_strategy_differential_adjudication_after_recovered_llm_judge/proof",
        "audit_five_strategy_differential_adjudication_after_recovered_llm_judge.py",
        "validate_receipts.py experiments/iter105_external_benchmark_pilot_design_after_differential_adjudication/proof",
        "audit_external_benchmark_pilot_design_after_differential_adjudication.py",
        "validate_receipts.py experiments/iter106_external_benchmark_pilot_materialization_after_design/proof",
        "audit_external_benchmark_pilot_materialization_after_design.py",
        "validate_receipts.py experiments/iter107_external_benchmark_pilot_execution_after_materialization/proof",
        "audit_external_benchmark_pilot_execution_after_materialization.py",
        "validate_handoff.py",
    ]:
        command = required_command(specification)
        if command not in exact_validation_commands:
            failures.append(f"mission validation command missing from contract: {command}")

    for required in [
        "../mission/loop.json",
        "Claim not allowed now: Telos is already executing through a private Aweb/Maestro runtime.",
        "Refinement is allowed only after evidence identifies a concrete gap.",
    ]:
        if required not in doc:
            failures.append(f"mission loop doc missing required text: {required}")

    if failures:
        print("MISSION LOOP GUARD FAILED:")
        for failure in failures:
            print(" -", failure)
        return 1

    print(f"mission loop guard: active gate={active_gate} phases={len(REQUIRED_PHASES)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
