#!/usr/bin/env python3
"""Validate iter214's pre-data cross-platform numeric recovery and topology."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import validate_iter213_post_seal_validation_recovery as iter213_guard  # noqa: E402
from scripts.build_iter213_receipt import (  # noqa: E402
    sealed_source_commit as iter213_source,
)
from scripts.build_iter214_receipt import (  # noqa: E402
    BINDINGS,
    PREDECESSOR_SEAL,
    RECEIPT_PATH,
    sealed_source_commit,
    verify_sealed_receipt,
)
from telos.proof import ProofValidationError, validate_receipt_v2  # noqa: E402
from telos.tcp1 import wilson_interval  # noqa: E402


PREFIX = "experiments/iter214_tcp1_cross_platform_numeric_recovery/"
HYPOTHESIS = ROOT / PREFIX / "HYPOTHESIS.md"
RESULT = ROOT / PREFIX / "RESULT.md"
FAILURE = ROOT / PREFIX / "proof/ci_failure.json"
AMENDMENT = ROOT / PREFIX / "proof/analysis_amendment.json"
MISSION = ROOT / "mission/loop.json"
README = ROOT / "README.md"
ROADMAP = ROOT / "docs/TELOS-ROADMAP-2026.md"
MISSION_DOC = ROOT / "docs/MISSION_LOOP.md"
CI = ROOT / ".github/workflows/ci.yml"
HANDOFF_SCHEMA = "telos.iter214.handoff.v1"
BRANCH = "agent/iter214-tcp1-cross-platform-numeric-recovery"
ITER213_SOURCE = "f5cbb9df76f5fc2464e84f4d911313122d76545f"
ITER213_SEAL = "dbe008211022e0abdff5bc9e47e871b02b6d5501"


class Iter214ValidationError(ValueError):
    """Raised when iter214 loses its narrow pre-data recovery boundary."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Iter214ValidationError(message)


def git(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        diagnostic = result.stderr.strip() or result.stdout.strip()
        raise Iter214ValidationError(f"git command failed: {' '.join(arguments)}: {diagnostic}")
    return result.stdout.rstrip()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Iter214ValidationError(f"cannot read canonical JSON: {path}") from exc
    require(isinstance(value, dict), f"JSON root is not an object: {path}")
    return value


def validate_failure_record() -> None:
    failure = load_json(FAILURE)
    require(
        failure.get("schema_version") == "telos.iter214.cross_platform_ci_failure.v1",
        "iter214 failure schema differs",
    )
    require(
        failure.get("predecessor_seal") == ITER213_SEAL
        and failure.get("draft_pull_request") == 11
        and failure.get("branch") == "agent/iter213-iter211-post-seal-validation-recovery",
        "iter214 failed-publication identity differs",
    )
    push = failure.get("push_ci", {})
    pull = failure.get("pull_request_ci", {})
    require(
        push
        == {
            "run_id": 29505707609,
            "event": "push",
            "head_sha": ITER213_SEAL,
            "conclusion": "failure",
            "failed_jobs": ["verify py3.11", "verify py3.12"],
        },
        "iter214 push-CI failure record differs",
    )
    require(
        pull
        == {
            "run_id": 29505789397,
            "event": "pull_request",
            "head_sha": ITER213_SEAL,
            "conclusion": "failure",
            "failed_jobs": ["verify py3.11", "verify py3.12"],
        },
        "iter214 pull-request-CI failure record differs",
    )
    require(
        failure.get("failed_test")
        == "tests/test_tcp1.py::test_wilson_interval_and_exact_paired_test_are_frozen"
        and failure.get("local_lower_endpoint") == 0.0
        and failure.get("linux_lower_endpoint") == 2.7755575615628914e-17
        and failure.get("successes") == 0
        and failure.get("trials") == 10
        and failure.get("other_tests_passed_per_job") == 656,
        "iter214 numeric failure observation differs",
    )
    require(
        failure.get("iter213_branch_mutated_after_observation") is False
        and failure.get("workflow_rerun_requested") is False
        and failure.get("scientific_result_changed") is False,
        "iter214 failure record overstates mutation, rerun, or science",
    )


def validate_analysis_amendment() -> None:
    amendment = load_json(AMENDMENT)
    require(
        amendment.get("schema_version") == "telos.tcp1.analysis_amendment.v1"
        and amendment.get("amendment_id") == "tcp1-wilson-boundary-canonicalization",
        "iter214 analysis-amendment identity differs",
    )
    require(
        amendment.get("recorded_before_any_tcp1_data") is True
        and amendment.get("tcp1_data_observed") is False,
        "iter214 amendment is not demonstrably pre-data",
    )
    require(
        amendment.get("changes")
        == [
            "set lower endpoint to 0.0 when successes equals 0",
            "set upper endpoint to 1.0 when successes equals trials",
        ],
        "iter214 exact numerical amendment differs",
    )
    expected_unchanged = {
        "Wilson interior formula",
        "two-sided 95 percent confidence level",
        "one-sided exact conditional McNemar primary test",
        "task-cluster bootstrap method and seed",
        "minimum ten eligible semantic failures",
        "control separation",
        "missingness and hard falsifiers",
        "twelve-task five-seed cohort shape",
        "resource ceilings",
        "claim boundaries",
    }
    require(
        set(amendment.get("unchanged", [])) == expected_unchanged,
        "iter214 unchanged-analysis ledger differs",
    )
    require(
        amendment.get("scientific_execution_authorized") is False
        and amendment.get("scientific_result_claimed") is False,
        "iter214 amendment overstates scientific authority",
    )


def validate_numeric_behavior() -> None:
    lower, upper = wilson_interval(0, 10)
    all_lower, all_upper = wilson_interval(10, 10)
    require(lower == 0.0, "Wilson k=0 lower endpoint is not exact zero")
    require(all_upper == 1.0, "Wilson k=n upper endpoint is not exact one")
    require(
        abs(upper - 0.2775327998628892) < 1e-15,
        "Wilson 0/10 upper endpoint changed",
    )
    require(
        abs(all_lower - (1.0 - upper)) < 1e-15,
        "Wilson boundary symmetry changed",
    )


def validate_predecessor_closure() -> None:
    require(iter213_source() == ITER213_SOURCE, "iter213 sealed source does not resolve")
    require(
        iter213_guard.source_and_seal() == (ITER213_SOURCE, ITER213_SEAL),
        "iter213 sealed source/seal topology differs",
    )
    require(
        iter213_guard.validate(preflight=True) == [],
        "iter213 descendant validation is not sealed-source-bound",
    )


def validate_narrative_surfaces() -> None:
    hypothesis = " ".join(HYPOTHESIS.read_text(encoding="utf-8").split())
    result = " ".join(RESULT.read_text(encoding="utf-8").split())
    for fragment in (
        "corrective pre-data analysis/publication gate",
        "push CI run `29505707609`",
        "pull-request CI run `29505789397`",
        "one-ULP residue",
        "if `successes == 0`, set `lower = 0.0`",
        "Sealed iter213 validation reads its own source Git blobs",
    ):
        require(fragment in hypothesis, f"iter214 hypothesis omits: {fragment}")
    for fragment in (
        "PASS locally; remote publication gates pending",
        "mathematically exact `0.0` at `k=0` and `1.0` at `k=n`",
        "publication-only descendant-mode gap",
        "No TCP-1 data exists",
        "contributes no scientific `N`, `k`, `u`",
    ):
        require(fragment in result, f"iter214 result omits: {fragment}")

    readme = README.read_text(encoding="utf-8")
    for fragment in (
        "Cross-platform numeric recovery active — TCP-1 scientific execution BLOCKED",
        "`2.7755575615628914e-17`",
        "iter214 TCP-1 cross-platform numeric recovery",
        "iter00-iter214",
        "I214[\"214 numeric recovery",
    ):
        require(fragment in readme, f"README omits iter214 fact: {fragment}")
    roadmap = ROADMAP.read_text(encoding="utf-8")
    for heading in (
        "### Iter214 — TCP-1 cross-platform numeric recovery",
        "### Iter215 — isolated throughput preflight",
        "### Iter216 — bounded GPU execution",
        "### Iter217 — blinded adjudication",
        "### Iter218 — multi-model replication",
    ):
        require(heading in roadmap, f"roadmap omits {heading}")
    mission_doc = MISSION_DOC.read_text(encoding="utf-8")
    require(
        "Iter214 is the active additive pre-data numeric recovery" in mission_doc
        and "scientific execution remains blocked" in mission_doc,
        "mission documentation omits iter214 boundary",
    )


def validate_mission_and_ci() -> None:
    mission = load_json(MISSION)
    require(
        mission.get("active_publication_gate") == PREFIX + "HYPOTHESIS.md",
        "mission active publication gate differs",
    )
    state = mission.get("current_gate_state", {})
    iter213 = state.get("iter213_recovery", {})
    require(
        iter213.get("status") == "sealed_publication_recovery_remote_ci_failed"
        and iter213.get("source_commit") == ITER213_SOURCE
        and iter213.get("seal_commit") == ITER213_SEAL
        and iter213.get("draft_pull_request") == 11
        and iter213.get("push_ci_run") == 29505707609
        and iter213.get("pull_request_ci_run") == 29505789397
        and iter213.get("branch_mutated_after_failure") is False
        and iter213.get("workflow_rerun_requested") is False
        and iter213.get("execution_authorized") is False,
        "mission iter213 failed-publication state differs",
    )
    iter214 = state.get("iter214_recovery", {})
    require(
        iter214.get("status") == "active_local_pre_data_numeric_recovery"
        and iter214.get("predecessor_seal") == PREDECESSOR_SEAL
        and iter214.get("tcp1_data_observed") is False
        and iter214.get("scientific_change") is False
        and iter214.get("execution_authorized") is False,
        "mission iter214 state differs",
    )
    claim = mission.get("publication_claim_boundary", "")
    for fragment in (
        "Iter213 is sealed and its push and pull-request CI both failed",
        "Iter214 is the active additive pre-data numeric recovery",
        "Iter212 remains unchanged and inactive",
        "scientific execution remains blocked",
        "TELOS, Sentinel, Inbar, and Odeya are related to one another and separate from Aweb",
    ):
        require(fragment in claim, f"mission claim boundary omits: {fragment}")
    sources = mission.get("source_of_truth", [])
    required_sources = set(BINDINGS) | {RECEIPT_PATH.relative_to(ROOT).as_posix()}
    require(
        isinstance(sources, list) and required_sources.issubset(set(sources)),
        "mission source-of-truth set omits iter214 artifacts",
    )
    commands = (
        "python3 scripts/build_iter214_receipt.py --check",
        "python3 scripts/validate_iter214_tcp1_cross_platform_numeric_recovery.py",
    )
    current_validation = mission.get("current_validation", [])
    require(all(command in current_validation for command in commands), "mission omits iter214 checks")
    ci = CI.read_text(encoding="utf-8")
    require(all(f"run: {command}" in ci for command in commands), "CI omits iter214 checks")


def changed_paths_from_predecessor() -> set[str]:
    changed = set(git("diff", "--name-only", PREDECESSOR_SEAL).splitlines())
    untracked = set(git("ls-files", "--others", "--exclude-standard").splitlines())
    return {path for path in changed | untracked if path}


def validate_experiment_scope() -> None:
    unauthorized = sorted(
        path
        for path in changed_paths_from_predecessor()
        if path.startswith("experiments/") and not path.startswith(PREFIX)
    )
    require(not unauthorized, "iter214 changes frozen experiment paths: " + ", ".join(unauthorized))
    require(not (ROOT / PREFIX / "proof/raw").exists(), "iter214 unexpectedly contains raw execution data")


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
    require(len(candidates) == 1, "cannot resolve exactly one iter214 handoff seal")
    return source, candidates[0]


def validate_receipt_and_topology() -> None:
    resolved = source_and_seal()
    require(resolved is not None, "iter214 sealed handoff identity is absent")
    source, seal = resolved
    require(
        git("rev-list", "--parents", "-n", "1", source).split()
        == [source, PREDECESSOR_SEAL],
        "iter214 source is not the direct child of iter213 seal",
    )
    require(
        git("rev-list", "--parents", "-n", "1", seal).split() == [seal, source],
        "iter214 seal is not the direct child of source",
    )
    require(verify_sealed_receipt(source) == len(BINDINGS), "iter214 receipt count differs")
    receipt = validate_receipt_v2(
        json.loads(git("show", f"{source}:{RECEIPT_PATH.relative_to(ROOT)}"))
    )
    require(receipt.status == "pass", "iter214 sealed receipt is not pass")
    bound = {item["artifact"]["path"] for item in receipt.evidence}
    require(bound == set(BINDINGS), "iter214 receipt binding set differs")
    source_delta = set(
        git("diff", "--name-only", "--no-renames", PREDECESSOR_SEAL, source).splitlines()
    )
    require(
        source_delta == set(BINDINGS) | {RECEIPT_PATH.relative_to(ROOT).as_posix()},
        "iter214 receipt does not cover the exact source delta",
    )
    handoff = git("show", f"{seal}:HANDOFF.md")
    require(f"handoff_schema: {HANDOFF_SCHEMA}" in handoff, "iter214 handoff schema differs")
    require(f"source_branch: {BRANCH}" in handoff, "iter214 handoff branch differs")
    require(f"source_commit: {source}" in handoff, "iter214 handoff source differs")
    require(
        f"Receipt evidence count: `{len(BINDINGS)}`" in handoff
        and f"Receipt closure SHA-256: `{receipt.evidence_closure_sha256}`" in handoff
        and f"Receipt SHA-256: `{receipt.receipt_sha256}`" in handoff,
        "iter214 handoff does not bind receipt identity",
    )


def validate(*, preflight: bool = False) -> list[str]:
    failures: list[str] = []
    checks = (
        validate_failure_record,
        validate_analysis_amendment,
        validate_numeric_behavior,
        validate_predecessor_closure,
        validate_narrative_surfaces,
        validate_mission_and_ci,
        validate_experiment_scope,
    )
    try:
        if source_and_seal() is not None:
            validate_receipt_and_topology()
            return failures
        for check in checks:
            check()
        if not preflight:
            validate_receipt_and_topology()
    except (OSError, ProofValidationError, RuntimeError, Iter214ValidationError) as exc:
        failures.append(str(exc))
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    failures = validate(preflight=args.preflight)
    if failures:
        print("iter214 TCP-1 cross-platform numeric recovery guard failed:", file=sys.stderr)
        for failure in failures:
            print(f" - {failure}", file=sys.stderr)
        return 1
    mode = "preflight" if args.preflight else "sealed"
    print(f"iter214 TCP-1 cross-platform numeric recovery guard: {mode} pass; no science")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
