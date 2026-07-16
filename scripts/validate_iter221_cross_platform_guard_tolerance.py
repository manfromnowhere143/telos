#!/usr/bin/env python3
"""Validate iter221's platform-independence correction and preserved predecessors.

Two things must stay true: no guard asserts bit-exact equality on a value the floating
point standard does not promise across machines, and iter219's null is untouched.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import validate_iter219_temporal_consequence_test_yield as iter219_guard  # noqa: E402
from telos.tcp1 import wilson_interval  # noqa: E402

PREFIX = "experiments/iter221_cross_platform_guard_tolerance/"
HYPOTHESIS = ROOT / PREFIX / "HYPOTHESIS.md"
FAILURE = ROOT / PREFIX / "proof/ci_failure.json"

ITER219_SEAL = "11e335e82100319a4f5f47d86eaea0c8e81edbbc"
ITER220_SEAL = "3cee092420c2d13227005c8d78e584ec69da832f"
ITER219_EVIDENCE = (
    "experiments/iter219_temporal_consequence_test_yield/HYPOTHESIS.md",
    "experiments/iter219_temporal_consequence_test_yield/RESULT.md",
    "experiments/iter219_temporal_consequence_test_yield/proof/yield_report.json",
    "experiments/iter219_temporal_consequence_test_yield/proof/analysis_amendment.json",
)


class Iter221ValidationError(ValueError):
    """Raised when iter221 exceeds its publication-only boundary."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Iter221ValidationError(message)


def git_bytes(*arguments: str) -> bytes:
    result = subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, check=False)
    if result.returncode != 0:
        raise Iter221ValidationError(f"git {' '.join(arguments)} failed")
    return result.stdout


def check_predecessor_evidence_unchanged() -> None:
    for path in ITER219_EVIDENCE:
        sealed = git_bytes("show", f"{ITER219_SEAL}:{path}")
        require(
            (ROOT / path).read_bytes() == sealed,
            f"iter219 evidence changed during recovery: {path}",
        )
    for path in ("scripts/run_ci_closure.py",):
        require((ROOT / path).exists(), f"iter220 correction missing: {path}")


def check_no_bit_exact_libm_comparison() -> None:
    """No guard may demand bit-exact equality on a sqrt-derived value."""

    source = Path(iter219_guard.__file__).read_text(encoding="utf-8")
    offenders = [
        line.strip()
        for line in source.splitlines()
        if "wilson_interval" in line and "==" in line
    ]
    require(
        not offenders,
        f"bit-exact comparison on a sqrt-derived value remains: {offenders}",
    )


def check_tolerance_forgives_ulp_but_catches_tampering() -> None:
    expected = wilson_interval(163, 482)
    drifted = [
        math.nextafter(expected[0], math.inf),
        math.nextafter(expected[1], math.inf),
    ]
    require(
        drifted != list(expected),
        "the ULP fixture must actually differ bitwise",
    )
    require(
        iter219_guard.intervals_match(drifted, expected),
        "the guard must accept an interval that differs by one unit in the last place",
    )
    tampered = [expected[0] * (1 + 1e-7), expected[1]]
    require(
        not iter219_guard.intervals_match(tampered, expected),
        "the guard must still reject a tampered interval",
    )
    require(
        1e-16 < iter219_guard.INTERVAL_REL_TOL < 1e-4,
        "the tolerance must sit strictly between one ULP and a reported digit",
    )


def check_failure_record(failure: dict[str, Any]) -> None:
    require(
        failure.get("schema_version") == "telos.iter221.ci_failure.v1",
        "unexpected ci_failure schema",
    )
    predecessor = failure["failed_predecessor"]
    require(predecessor["seal_commit"] == ITER220_SEAL, "iter220 seal differs")
    require(predecessor["draft_pull_request"] == 14, "iter220 draft PR differs")
    require(
        predecessor["branch_mutated_after_observation"] is False
        and predecessor["workflow_rerun_after_observation"] is False
        and predecessor["merged"] is False,
        "the failed iter220 branch must remain unmutated, unrerun, and unmerged",
    )
    require(failure["push_ci"]["run_id"] == 29540341974, "push CI run differs")
    require(failure["pull_request_ci"]["run_id"] == 29540356205, "pull-request CI run differs")
    require(
        "sqrt" in failure.get("proximate_cause", ""),
        "the failure record must name sqrt as the platform-dependent source",
    )
    require(
        "macOS" in failure["root_cause"].get("why_the_derived_closure_missed_it", ""),
        "the failure record must state why the local closure could not catch it",
    )
    for field in (
        "provider_calls",
        "gpu_allocations",
        "containers_built",
        "repository_test_executions",
        "workflow_reruns",
    ):
        require(failure.get(field) == 0, f"{field} must be zero for iter221")


def validate() -> list[str]:
    problems: list[str] = []
    try:
        require(HYPOTHESIS.exists(), "iter221 hypothesis missing")
        require(FAILURE.exists(), "iter221 ci_failure record missing")
        check_failure_record(json.loads(FAILURE.read_text(encoding="utf-8")))
        check_predecessor_evidence_unchanged()
        check_no_bit_exact_libm_comparison()
        check_tolerance_forgives_ulp_but_catches_tampering()
    except Iter221ValidationError as error:
        problems.append(str(error))
    return problems


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    problems = validate()
    if problems:
        for problem in problems:
            print(f"iter221: {problem}")
        return 1
    print("iter221 platform-independence validated; iter219 evidence unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
