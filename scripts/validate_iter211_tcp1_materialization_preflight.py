#!/usr/bin/env python3
"""Validate iter211 TCP-1 materialization, blockers, receipt, and Git topology."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_iter211_receipt import (  # noqa: E402
    BINDINGS,
    RECEIPT_PATH,
    sealed_source_commit,
    verify_sealed_receipt,
)
from scripts.build_iter211_tcp1_packet import (  # noqa: E402
    BASELINE_MERGE,
    BLOCKERS,
    ITER210_SEAL,
    NEXT_GATE,
    OLD_MASTER,
    PROOF,
    documents,
    fixed_seeds,
    rendered,
)
from telos.proof import ProofValidationError, validate_receipt_v2  # noqa: E402
from telos.tcp1 import exact_one_sided_mcnemar, wilson_interval  # noqa: E402


PREFIX = "experiments/iter211_tcp1_materialization_preflight/"
NEXT_PREFIX = "experiments/iter212_tcp1_independent_cohort_and_custody_freeze/"
HYPOTHESIS = ROOT / PREFIX / "HYPOTHESIS.md"
RESULT = ROOT / PREFIX / "RESULT.md"
REVIEW = ROOT / PREFIX / "proof/review.md"
MISSION = ROOT / "mission/loop.json"
ROADMAP = ROOT / "docs/TELOS-ROADMAP-2026.md"
MISSION_DOC = ROOT / "docs/MISSION_LOOP.md"
README = ROOT / "README.md"
CI = ROOT / ".github/workflows/ci.yml"
HANDOFF_SCHEMA = "telos.iter211.handoff.v1"
BRANCH = "agent/iter211-tcp1-materialization"


class Iter211ValidationError(ValueError):
    """Raised when the materialization packet overstates readiness or loses custody."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Iter211ValidationError(message)


def git(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        diagnostic = result.stderr.strip() or result.stdout.strip()
        raise Iter211ValidationError(f"git command failed: {' '.join(arguments)}: {diagnostic}")
    return result.stdout.rstrip()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Iter211ValidationError(f"cannot read canonical JSON: {path}") from exc
    require(isinstance(value, dict), f"JSON root is not an object: {path}")
    return value


def validate_generated_artifacts() -> None:
    expected = documents()
    require(len(expected) == 17, "iter211 generated artifact count differs")
    for relative, value in expected.items():
        path = PROOF / relative
        require(path.is_file() and not path.is_symlink(), f"missing or unsafe artifact: {path}")
        require(path.read_text(encoding="utf-8") == rendered(value), f"artifact drift: {path}")

    schemas = [value for relative, value in expected.items() if relative.startswith("schemas/")]
    require(len(schemas) == 6, "iter211 schema count differs")
    for schema in schemas:
        require(
            schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema",
            "iter211 schema dialect differs",
        )
        require(schema.get("type") == "object", "iter211 schema root is not an object")
        require(schema.get("additionalProperties") is False, "iter211 schema is open-ended")
        require(isinstance(schema.get("required"), list), "iter211 schema lacks required fields")


def validate_protocol_and_analysis() -> None:
    protocol = load_json(PROOF / "protocol.json")
    require(protocol.get("status") == "execution_blocked", "TCP-1 protocol is not blocked")
    require(protocol.get("execution_authorized") is False, "TCP-1 protocol authorizes execution")
    cohort = protocol.get("cohort", {})
    require(
        cohort.get("fresh_task_count") == 12
        and cohort.get("seeds_per_task") == 5
        and cohort.get("planned_natural_trajectory_count") == 60
        and cohort.get("seeds") == fixed_seeds(),
        "TCP-1 cohort shape or deterministic seeds differ",
    )
    require(
        cohort.get("controls_are_separate_from_natural_cohort") is True,
        "TCP-1 controls are not structurally separate",
    )
    independence = protocol.get("independence", {})
    require(
        independence.get("minimum_distinct_humans") == 5
        and independence.get("llm_judge_can_define_ground_truth") is False,
        "TCP-1 human-independence contract differs",
    )
    require(len(protocol.get("hard_falsifiers", [])) == 10, "TCP-1 falsifier set differs")
    claim = protocol.get("claim_boundary", "")
    for forbidden in ("model ranking", "population prevalence", "state-of-the-art"):
        require(forbidden in claim, f"TCP-1 claim boundary omits {forbidden}")

    low, high = wilson_interval(0, 10)
    require(low == 0 and 0.277 < high < 0.278, "Wilson implementation drifted")
    paired = exact_one_sided_mcnemar([(True, False)] * 10)
    require(
        paired.get("one_sided_exact_p_value") == 0.0009765625,
        "exact paired implementation drifted",
    )
    plan = load_json(PROOF / "analysis_plan.json")
    require(plan.get("status") == "frozen_code_no_data", "analysis plan status differs")
    require(plan.get("data_observed") is False, "analysis plan claims observed data")
    require(plan.get("implementation") == "telos/tcp1.py", "analysis implementation differs")
    require(
        plan.get("primary_test", {}).get("minimum_eligible_failures") == 10,
        "primary minimum-failure bar differs",
    )
    require(
        "controls and non-cohort preflight excluded" in plan.get("population", ""),
        "analysis population does not exclude controls/preflight",
    )


def validate_blocked_ledgers() -> None:
    tasks = load_json(PROOF / "task_candidate_ledger.json")
    require(
        tasks.get("status") == "blocked"
        and tasks.get("required_admitted_tasks") == 12
        and tasks.get("admitted_tasks") == 0
        and tasks.get("candidates") == []
        and tasks.get("chosen_model_id") is None
        and tasks.get("documented_training_cutoff") is None,
        "task ledger invents or admits a cohort",
    )
    reviewers = load_json(PROOF / "reviewer_ledger.json")
    slots = reviewers.get("slots", [])
    require(
        reviewers.get("status") == "blocked"
        and reviewers.get("minimum_distinct_humans") == 5
        and reviewers.get("role_overlap_permitted") is False
        and len(slots) == 5
        and all(slot.get("reviewer_id") is None and slot.get("status") == "unfilled" for slot in slots),
        "reviewer ledger is not exactly five unfilled independent roles",
    )
    bindings = load_json(PROOF / "execution_binding_ledger.json")
    require(bindings.get("status") == "blocked", "execution binding ledger is not blocked")
    require(
        bindings.get("all_execution_identity_fields_bound") is False
        and bindings.get("execution_authorized") is False,
        "execution binding ledger overstates readiness",
    )
    for section in ("model", "runtime", "environment", "hardware"):
        values = bindings.get(section, {})
        require(
            isinstance(values, dict) and values and all(value is None for value in values.values()),
            f"execution {section} contains an invented binding",
        )
    budget = load_json(PROOF / "resource_budget.json")
    require(
        budget.get("status") == "blocked"
        and budget.get("total_accelerator_hours_ceiling") == 64
        and budget.get("non_cohort_preflight_accelerator_hours_ceiling") == 2
        and budget.get("maximum_remaining_cohort_accelerator_hours_after_preflight") == 62,
        "resource ceilings differ",
    )
    money = budget.get("monetary_budget", {})
    require(
        money == {
            "amount": None,
            "approval_receipt_sha256": None,
            "approved": False,
            "currency": None,
        },
        "monetary budget is invented or implicitly approved",
    )
    require(
        budget.get("accelerator_allocations_in_this_iteration") == 0
        and budget.get("accelerator_hours_in_this_iteration") == 0
        and budget.get("execution_authorized") is False,
        "resource ledger records or authorizes accelerator use",
    )
    isolation = load_json(PROOF / "isolation_contract.json")
    require(
        isolation.get("status") == "blocked_pending_hostile_rehearsal"
        and isolation.get("hostile_rehearsal", {}).get("status") == "not_run"
        and isolation.get("execution_authorized") is False,
        "isolation rehearsal status overstates readiness",
    )
    controls = load_json(PROOF / "control_plan.json")
    require(controls.get("status") == "blocked_not_materialized", "control status differs")
    for key in ("legitimate_implementation_controls", "deterministic_integrity_attack_controls"):
        control = controls.get(key, {})
        require(
            control.get("count") is None
            and control.get("pooled_into_natural_behavior_estimate") is False,
            f"{key} is invented or pooled",
        )


def validate_admission_and_actions() -> None:
    admission = load_json(PROOF / "admission_report.json")
    require(
        admission.get("materialization_preflight_status") == "pass"
        and admission.get("scientific_execution_admission") == "blocked"
        and admission.get("execution_authorized") is False,
        "iter211 split admission decision differs",
    )
    gates = admission.get("gates", [])
    require(
        len(gates) == 11
        and admission.get("passed_gate_count") == 2
        and admission.get("blocked_gate_count") == 9
        and sum(gate.get("status") == "pass" for gate in gates) == 2
        and sum(gate.get("status") == "blocked" for gate in gates) == 9,
        "iter211 admission gate accounting differs",
    )
    require(admission.get("blockers") == BLOCKERS, "iter211 blocker set differs")
    require(admission.get("next_gate") == NEXT_GATE, "iter211 next gate differs")
    for field in ("provider_calls", "gpu_allocations", "scientific_trajectories"):
        require(admission.get(field) == 0, f"iter211 admission records nonzero {field}")
    require(admission.get("scientific_result_claimed") is False, "iter211 claims a result")

    actions = load_json(PROOF / "action_ledger.json")
    require(actions.get("read_only_github_cli_queries") == 3, "read-only query ledger differs")
    require(actions.get("underlying_http_request_count") is None, "unaudited HTTP count is invented")
    zero_fields = {
        "provider_model_calls",
        "gpu_allocations",
        "accelerator_hours",
        "scientific_container_runs",
        "scientific_trajectory_runs",
        "workflow_dispatches",
        "workflow_reruns",
        "deployments",
        "payments",
        "releases",
        "remote_mutations_before_source_seal",
    }
    require(all(actions.get(field) == 0 for field in zero_fields), "iter211 zero-action ledger differs")


def validate_merged_baseline() -> None:
    require(
        git("rev-list", "--parents", "-n", "1", BASELINE_MERGE).split()
        == [BASELINE_MERGE, OLD_MASTER, ITER210_SEAL],
        "merged iter210 baseline parent order differs",
    )
    baseline = load_json(PROOF / "merged_baseline.json")
    pull = baseline.get("pull_request", {})
    require(
        pull.get("number") == 10
        and pull.get("state") == "MERGED"
        and pull.get("head_sha") == ITER210_SEAL
        and pull.get("merge_commit") == BASELINE_MERGE,
        "iter211 merged PR baseline differs",
    )
    require(
        baseline.get("merge_parents_in_order") == [OLD_MASTER, ITER210_SEAL],
        "iter211 baseline parent ledger differs",
    )
    ci = baseline.get("ci", {})
    require(
        ci.get("branch_push") == {"conclusion": "success", "event": "push", "run_id": 29496323167}
        and ci.get("pull_request")
        == {"conclusion": "success", "event": "pull_request", "run_id": 29496355871}
        and ci.get("merged_master")
        == {"conclusion": "success", "event": "push", "run_id": 29496560409},
        "iter211 CI baseline differs",
    )


def validate_narrative_surfaces() -> None:
    hypothesis = HYPOTHESIS.read_text(encoding="utf-8")
    result = RESULT.read_text(encoding="utf-8")
    review = REVIEW.read_text(encoding="utf-8")
    for fragment in (
        "expected honest outcome is split",
        "scientific execution admission must remain blocked",
        "at least five distinct humans and no role overlap",
        "No historical experiment or raw evidence byte changes",
    ):
        require(fragment in hypothesis, f"iter211 hypothesis omits: {fragment}")
    for fragment in (
        "PASS for deterministic materialization preflight; SCIENTIFIC EXECUTION BLOCKED",
        "`2` of `11` gates pass and `9` remain blocked",
        "`0/12` admitted tasks",
        "contributes no scientific `N`, `k`, `u`",
        "Its receipt remains `blocked`",
    ):
        require(fragment in result, f"iter211 result omits: {fragment}")
    for fragment in (
        "A late-authored test can also be hashed",
        "selected twelve-task cohort is not a population sample",
        "Scientific execution admission: `BLOCKED`",
    ):
        require(fragment in review, f"iter211 adversarial review omits: {fragment}")
    require((ROOT / NEXT_GATE).is_file(), "iter212 next-gate hypothesis is absent")

    roadmap = ROADMAP.read_text(encoding="utf-8")
    for heading in (
        "### Iter211 — TCP-1 materialization preflight",
        "### Iter212 — independent cohort and custody freeze",
        "### Iter213 — isolated throughput preflight",
        "### Iter214 — bounded GPU execution",
        "### Iter215 — blinded adjudication",
        "### Iter216 — multi-model replication",
    ):
        require(heading in roadmap, f"roadmap sequence omits {heading}")
    require("Iter209 — TCP-1 materialization" not in roadmap, "roadmap retains displaced numbering")

    readme = README.read_text(encoding="utf-8")
    for fragment in (
        "TCP-1 materialization preflight PASS — scientific execution BLOCKED",
        "2 local-design gates pass; 9 external admission gates remain blocked",
        "iter211 TCP-1 materialization preflight",
        "iter00-iter211",
    ):
        require(fragment in readme, f"README omits iter211 fact: {fragment}")
    require("I211[\"211 TCP-1 preflight" in readme, "README recovery diagram omits iter211")


def validate_mission_and_ci() -> None:
    mission = load_json(MISSION)
    expected_gate = PREFIX + "HYPOTHESIS.md"
    require(mission.get("active_publication_gate") == expected_gate, "mission active gate differs")
    state = mission.get("current_gate_state", {})
    iter210 = state.get("iter210_recovery", {})
    require(
        iter210.get("status") == "merged_publication_recovery_green"
        and iter210.get("merge_commit") == BASELINE_MERGE
        and iter210.get("pull_request") == 10,
        "mission does not close iter210 as merged and green",
    )
    iter211 = state.get("iter211_tcp1_materialization", {})
    require(
        iter211.get("status") == "materialization_preflight_pass_execution_blocked"
        and iter211.get("predecessor_merge") == BASELINE_MERGE
        and iter211.get("passed_gate_count") == 2
        and iter211.get("blocked_gate_count") == 9
        and iter211.get("execution_authorized") is False,
        "mission iter211 state differs",
    )
    claim = mission.get("publication_claim_boundary", "")
    for fragment in (
        "Iter210 merged through PR #10",
        "Iter211 is the active zero-execution TCP-1 materialization preflight",
        "scientific execution remains blocked",
        "TELOS, Sentinel, Inbar, and Odeya are related to one another and separate from Aweb",
    ):
        require(fragment in claim, f"mission claim boundary omits: {fragment}")
    sources = mission.get("source_of_truth", [])
    required_sources = set(BINDINGS) | {RECEIPT_PATH.relative_to(ROOT).as_posix()}
    require(
        isinstance(sources, list) and required_sources.issubset(set(sources)),
        "mission source-of-truth set omits iter211 artifacts",
    )
    current_validation = mission.get("current_validation", [])
    commands = (
        "python3 scripts/build_iter211_tcp1_packet.py --check",
        "python3 scripts/build_iter211_receipt.py --check",
        "python3 scripts/validate_iter211_tcp1_materialization_preflight.py",
    )
    require(all(command in current_validation for command in commands), "mission omits iter211 checks")
    ci = CI.read_text(encoding="utf-8")
    require(all(f"run: {command}" in ci for command in commands), "CI omits iter211 checks")
    mission_doc = MISSION_DOC.read_text(encoding="utf-8")
    require(
        "Iter211 is the active zero-execution TCP-1 materialization preflight" in mission_doc
        and "scientific execution remains blocked" in mission_doc,
        "mission documentation does not describe iter211",
    )


def changed_paths_from_baseline() -> set[str]:
    changed = set(git("diff", "--name-only", BASELINE_MERGE).splitlines())
    untracked = set(git("ls-files", "--others", "--exclude-standard").splitlines())
    return {path for path in changed | untracked if path}


def validate_experiment_scope() -> None:
    unauthorized = sorted(
        path
        for path in changed_paths_from_baseline()
        if path.startswith("experiments/")
        and not path.startswith(PREFIX)
        and not path.startswith(NEXT_PREFIX)
    )
    require(not unauthorized, "iter211 changes frozen experiment paths: " + ", ".join(unauthorized))
    require(not (ROOT / PREFIX / "proof/raw").exists(), "iter211 unexpectedly contains raw execution data")


def source_and_seal() -> tuple[str, str] | None:
    source = sealed_source_commit()
    if source is None:
        return None
    rows = git("rev-list", "--ancestry-path", "--parents", f"{source}..HEAD").splitlines()
    candidates = []
    for line in rows:
        row = line.split()
        if len(row) == 2 and row[1] == source:
            diff = git("diff", "--name-status", "--no-renames", source, row[0]).splitlines()
            if diff == ["M\tHANDOFF.md"]:
                candidates.append(row[0])
    require(len(candidates) == 1, "cannot resolve exactly one iter211 handoff seal")
    return source, candidates[0]


def validate_receipt_and_topology() -> None:
    resolved = source_and_seal()
    require(resolved is not None, "iter211 sealed handoff identity is absent")
    source, seal = resolved
    require(
        git("rev-list", "--parents", "-n", "1", source).split() == [source, BASELINE_MERGE],
        "iter211 source is not the direct child of merged iter210 master",
    )
    require(
        git("rev-list", "--parents", "-n", "1", seal).split() == [seal, source],
        "iter211 seal is not the direct child of source",
    )
    receipt_count = verify_sealed_receipt(source)
    require(receipt_count == len(BINDINGS), "iter211 receipt artifact count differs")
    source_receipt = json.loads(git("show", f"{source}:{RECEIPT_PATH.relative_to(ROOT)}"))
    receipt = validate_receipt_v2(source_receipt)
    require(receipt.status == "blocked", "iter211 sealed receipt is not blocked")
    bound = {item["artifact"]["path"] for item in receipt.evidence}
    require(bound == set(BINDINGS), "iter211 receipt binding set differs")
    source_delta = set(git("diff", "--name-only", "--no-renames", BASELINE_MERGE, source).splitlines())
    require(
        source_delta == set(BINDINGS) | {RECEIPT_PATH.relative_to(ROOT).as_posix()},
        "iter211 receipt does not cover the exact source delta",
    )
    handoff = (ROOT / "HANDOFF.md").read_text(encoding="utf-8")
    require(f"handoff_schema: {HANDOFF_SCHEMA}" in handoff, "iter211 handoff schema differs")
    require(f"source_branch: {BRANCH}" in handoff, "iter211 handoff branch differs")
    require(f"source_commit: {source}" in handoff, "iter211 handoff source differs")
    require(
        f"Receipt evidence count: `{len(BINDINGS)}`" in handoff
        and f"Receipt closure SHA-256: `{receipt.evidence_closure_sha256}`" in handoff
        and f"Receipt SHA-256: `{receipt.receipt_sha256}`" in handoff,
        "iter211 handoff does not bind receipt identity",
    )


def validate(*, preflight: bool = False) -> list[str]:
    failures: list[str] = []
    checks = (
        validate_generated_artifacts,
        validate_protocol_and_analysis,
        validate_blocked_ledgers,
        validate_admission_and_actions,
        validate_merged_baseline,
        validate_narrative_surfaces,
        validate_mission_and_ci,
        validate_experiment_scope,
    )
    try:
        for check in checks:
            check()
        if not preflight:
            validate_receipt_and_topology()
    except (OSError, ProofValidationError, RuntimeError, Iter211ValidationError) as exc:
        failures.append(str(exc))
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    failures = validate(preflight=args.preflight)
    if failures:
        print("iter211 TCP-1 materialization guard failed:", file=sys.stderr)
        for failure in failures:
            print(f" - {failure}", file=sys.stderr)
        return 1
    mode = "preflight" if args.preflight else "sealed"
    print(f"iter211 TCP-1 materialization guard: {mode} pass; scientific execution blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
