#!/usr/bin/env python3
"""Validate iter213's additive post-seal compatibility recovery and topology."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import validate_iter200_corrected_result as standing_guard  # noqa: E402
from scripts import validate_iter210_pr_synthetic_merge_recovery as iter210_guard  # noqa: E402
from scripts import validate_iter211_tcp1_materialization_preflight as iter211_guard  # noqa: E402
from scripts.build_iter210_receipt import (  # noqa: E402
    ITER210_SEAL_COMMIT,
    ITER210_SOURCE_COMMIT,
    sealed_source_commit as iter210_source,
)
from scripts.build_iter211_receipt import (  # noqa: E402
    ITER211_SEAL_COMMIT,
    ITER211_SOURCE_COMMIT,
    sealed_source_commit as iter211_source,
)
from scripts.build_iter213_receipt import (  # noqa: E402
    BINDINGS,
    PREDECESSOR_SEAL,
    RECEIPT_PATH,
    sealed_source_commit,
    verify_sealed_receipt,
)
from telos.proof import ProofValidationError, validate_receipt_v2  # noqa: E402


PREFIX = "experiments/iter213_iter211_post_seal_validation_recovery/"
HYPOTHESIS = ROOT / PREFIX / "HYPOTHESIS.md"
RESULT = ROOT / PREFIX / "RESULT.md"
FAILURE = ROOT / PREFIX / "proof/post_seal_failure.json"
MISSION = ROOT / "mission/loop.json"
README = ROOT / "README.md"
ROADMAP = ROOT / "docs/TELOS-ROADMAP-2026.md"
MISSION_DOC = ROOT / "docs/MISSION_LOOP.md"
CI = ROOT / ".github/workflows/ci.yml"
HANDOFF_SCHEMA = "telos.iter213.handoff.v1"
BRANCH = "agent/iter213-iter211-post-seal-validation-recovery"


class Iter213ValidationError(ValueError):
    """Raised when iter213 loses its additive, publication-only boundary."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Iter213ValidationError(message)


def git(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        diagnostic = result.stderr.strip() or result.stdout.strip()
        raise Iter213ValidationError(f"git command failed: {' '.join(arguments)}: {diagnostic}")
    return result.stdout.rstrip()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Iter213ValidationError(f"cannot read canonical JSON: {path}") from exc
    require(isinstance(value, dict), f"JSON root is not an object: {path}")
    return value


def validate_failure_record() -> None:
    failure = load_json(FAILURE)
    require(
        failure.get("schema_version") == "telos.iter213.iter211_post_seal_failure.v1",
        "iter213 failure schema differs",
    )
    require(
        failure.get("predecessor_source") == ITER211_SOURCE_COMMIT
        and failure.get("predecessor_seal") == ITER211_SEAL_COMMIT,
        "iter213 predecessor identity differs",
    )
    require(
        failure.get("command") == "pytest -q"
        and failure.get("passed") == 648
        and failure.get("failed") == 3,
        "iter213 observed test counts differ",
    )
    tests = [item.get("test") for item in failure.get("failures", [])]
    require(
        tests
        == [
            "tests/test_iter203_publication_safety.py::test_build_audit_rejects_a_hit_without_printing_its_value",
            "tests/test_iter210_pr_synthetic_merge_recovery.py::test_iter210_preflight_is_clean",
            "tests/test_natural_rate_pipeline.py::test_iter200_claim_guard_covers_every_standing_public_surface",
        ],
        "iter213 failed-test identities differ",
    )
    actions = failure.get("pre_recovery_actions", {})
    require(
        isinstance(actions, dict) and actions and all(value == 0 for value in actions.values()),
        "iter213 pre-recovery zero-action ledger differs",
    )
    require(
        failure.get("iter211_mutated") is False
        and failure.get("iter212_mutated") is False
        and failure.get("scientific_result_changed") is False,
        "iter213 failure record overstates mutation or science",
    )


def validate_descendant_recovery() -> None:
    require(iter210_source() == ITER210_SOURCE_COMMIT, "iter210 sealed source does not resolve")
    require(iter211_source() == ITER211_SOURCE_COMMIT, "iter211 sealed source does not resolve")
    require(
        iter210_guard.source_and_seal() == (ITER210_SOURCE_COMMIT, ITER210_SEAL_COMMIT),
        "iter210 exact descendant topology differs",
    )
    require(
        iter211_guard.source_and_seal() == (ITER211_SOURCE_COMMIT, ITER211_SEAL_COMMIT),
        "iter211 exact descendant topology differs",
    )
    require(iter210_guard.validate(preflight=True) == [], "iter210 descendant preflight fails")
    require(iter210_guard.validate() == [], "iter210 descendant final validation fails")
    require(iter211_guard.validate(preflight=True) == [], "iter211 descendant preflight fails")
    require(iter211_guard.validate() == [], "iter211 descendant final validation fails")

    path = standing_guard.ROOT / "HANDOFF.md"
    body = "bounded current claim\n"
    action = "## Current Gate\n" + body + "## Verification Before Action\n"
    publication = "## Current Gates\n" + body + "## Verification Before Publication\n"
    require(
        standing_guard.standing_surface_text(path, action) == body
        and standing_guard.standing_surface_text(path, publication) == body,
        "standing handoff title compatibility differs",
    )
    require(standing_guard.standing_public_claim_scan() == [], "standing public claim scan fails")


def validate_narrative_surfaces() -> None:
    hypothesis = HYPOTHESIS.read_text(encoding="utf-8")
    result = RESULT.read_text(encoding="utf-8")
    normalized_hypothesis = " ".join(hypothesis.split())
    normalized_result = " ".join(result.split())
    for fragment in (
        "first complete iter211 post-seal test suite exposed three non-scientific compatibility defects",
        "Iter211 source",
        "Iter212's prospective independent-cohort hypothesis also remains unchanged and inactive",
        "local two-parent synthetic-merge simulation",
    ):
        require(fragment in normalized_hypothesis, f"iter213 hypothesis omits: {fragment}")
    for fragment in (
        "PASS locally; remote publication gates pending",
        "repairs three descendant-compatibility defects",
        "`execution_authorized=false` remain unchanged",
        "contributes no scientific `N`, `k`, `u`",
    ):
        require(fragment in normalized_result, f"iter213 result omits: {fragment}")

    readme = README.read_text(encoding="utf-8")
    for fragment in (
        "Post-seal validation recovery active — TCP-1 scientific execution BLOCKED",
        "passed `648` tests and failed `3` publication-only compatibility checks",
        "iter213 iter211 post-seal validation recovery",
        "iter00-iter213",
        "I213[\"213 validation recovery",
    ):
        require(fragment in readme, f"README omits iter213 fact: {fragment}")
    roadmap = ROADMAP.read_text(encoding="utf-8")
    for heading in (
        "### Iter213 — iter211 post-seal validation recovery",
        "### Iter214 — isolated throughput preflight",
        "### Iter215 — bounded GPU execution",
        "### Iter216 — blinded adjudication",
        "### Iter217 — multi-model replication",
    ):
        require(heading in roadmap, f"roadmap omits {heading}")
    mission_doc = MISSION_DOC.read_text(encoding="utf-8")
    require(
        "Iter213 is the active additive post-seal validation recovery" in mission_doc
        and "scientific execution remains blocked" in mission_doc,
        "mission documentation omits iter213 boundary",
    )


def validate_mission_and_ci() -> None:
    mission = load_json(MISSION)
    require(
        mission.get("active_publication_gate") == PREFIX + "HYPOTHESIS.md",
        "mission active publication gate differs",
    )
    state = mission.get("current_gate_state", {})
    iter211 = state.get("iter211_tcp1_materialization", {})
    require(
        iter211.get("status") == "sealed_materialization_post_seal_validation_failed"
        and iter211.get("source_commit") == ITER211_SOURCE_COMMIT
        and iter211.get("seal_commit") == ITER211_SEAL_COMMIT
        and iter211.get("post_seal_tests_passed") == 648
        and iter211.get("post_seal_tests_failed") == 3
        and iter211.get("execution_authorized") is False,
        "mission iter211 post-seal state differs",
    )
    iter213 = state.get("iter213_recovery", {})
    require(
        iter213.get("status") == "active_local_post_seal_validation_recovery"
        and iter213.get("predecessor_seal") == PREDECESSOR_SEAL
        and iter213.get("scientific_change") is False
        and iter213.get("execution_authorized") is False,
        "mission iter213 state differs",
    )
    claim = mission.get("publication_claim_boundary", "")
    for fragment in (
        "Iter211 is sealed and its first complete post-seal suite passed 648 tests and failed 3",
        "Iter213 is the active additive publication-validation recovery",
        "Iter212 remains unchanged and inactive",
        "scientific execution remains blocked",
        "TELOS, Sentinel, Inbar, and Odeya are related to one another and separate from Aweb",
    ):
        require(fragment in claim, f"mission claim boundary omits: {fragment}")
    sources = mission.get("source_of_truth", [])
    required_sources = set(BINDINGS) | {RECEIPT_PATH.relative_to(ROOT).as_posix()}
    require(
        isinstance(sources, list) and required_sources.issubset(set(sources)),
        "mission source-of-truth set omits iter213 artifacts",
    )
    commands = (
        "python3 scripts/build_iter213_receipt.py --check",
        "python3 scripts/validate_iter213_post_seal_validation_recovery.py",
    )
    current_validation = mission.get("current_validation", [])
    require(all(command in current_validation for command in commands), "mission omits iter213 checks")
    ci = CI.read_text(encoding="utf-8")
    require(all(f"run: {command}" in ci for command in commands), "CI omits iter213 checks")


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
    require(not unauthorized, "iter213 changes frozen experiment paths: " + ", ".join(unauthorized))
    require(not (ROOT / PREFIX / "proof/raw").exists(), "iter213 unexpectedly contains raw execution data")


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
    require(len(candidates) == 1, "cannot resolve exactly one iter213 handoff seal")
    return source, candidates[0]


def validate_receipt_and_topology() -> None:
    resolved = source_and_seal()
    require(resolved is not None, "iter213 sealed handoff identity is absent")
    source, seal = resolved
    require(
        git("rev-list", "--parents", "-n", "1", source).split()
        == [source, PREDECESSOR_SEAL],
        "iter213 source is not the direct child of iter211 seal",
    )
    require(
        git("rev-list", "--parents", "-n", "1", seal).split() == [seal, source],
        "iter213 seal is not the direct child of source",
    )
    require(verify_sealed_receipt(source) == len(BINDINGS), "iter213 receipt count differs")
    receipt = validate_receipt_v2(
        json.loads(git("show", f"{source}:{RECEIPT_PATH.relative_to(ROOT)}"))
    )
    require(receipt.status == "pass", "iter213 sealed receipt is not pass")
    bound = {item["artifact"]["path"] for item in receipt.evidence}
    require(bound == set(BINDINGS), "iter213 receipt binding set differs")
    source_delta = set(
        git("diff", "--name-only", "--no-renames", PREDECESSOR_SEAL, source).splitlines()
    )
    require(
        source_delta == set(BINDINGS) | {RECEIPT_PATH.relative_to(ROOT).as_posix()},
        "iter213 receipt does not cover the exact source delta",
    )
    handoff = git("show", f"{seal}:HANDOFF.md")
    require(f"handoff_schema: {HANDOFF_SCHEMA}" in handoff, "iter213 handoff schema differs")
    require(f"source_branch: {BRANCH}" in handoff, "iter213 handoff branch differs")
    require(f"source_commit: {source}" in handoff, "iter213 handoff source differs")
    require(
        f"Receipt evidence count: `{len(BINDINGS)}`" in handoff
        and f"Receipt closure SHA-256: `{receipt.evidence_closure_sha256}`" in handoff
        and f"Receipt SHA-256: `{receipt.receipt_sha256}`" in handoff,
        "iter213 handoff does not bind receipt identity",
    )


def validate(*, preflight: bool = False) -> list[str]:
    failures: list[str] = []
    checks = (
        validate_failure_record,
        validate_descendant_recovery,
        validate_narrative_surfaces,
        validate_mission_and_ci,
        validate_experiment_scope,
    )
    try:
        # Once iter213 is sealed, validate its immutable source/receipt/topology
        # rather than reinterpreting additive descendant files as iter213 work.
        # This is the same fail-closed descendant mode used by the iter211 guard.
        if source_and_seal() is not None:
            validate_receipt_and_topology()
            return failures
        for check in checks:
            check()
        if not preflight:
            validate_receipt_and_topology()
    except (OSError, ProofValidationError, RuntimeError, Iter213ValidationError) as exc:
        failures.append(str(exc))
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    failures = validate(preflight=args.preflight)
    if failures:
        print("iter213 post-seal validation recovery guard failed:", file=sys.stderr)
        for failure in failures:
            print(f" - {failure}", file=sys.stderr)
        return 1
    mode = "preflight" if args.preflight else "sealed"
    print(f"iter213 post-seal validation recovery guard: {mode} pass; no science")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
