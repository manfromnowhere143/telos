#!/usr/bin/env python3
"""Validate iter220's publication-only recovery and iter219's preserved evidence.

Two things must stay true: iter219's science is untouched, and the mechanism that let a
known bug reach CI is closed rather than papered over.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import run_ci_closure  # noqa: E402
from scripts.validate_detector_methodology_correction import normalize_prose  # noqa: E402

PREFIX = "experiments/iter220_iter219_publication_ci_recovery/"
HYPOTHESIS = ROOT / PREFIX / "HYPOTHESIS.md"
FAILURE = ROOT / PREFIX / "proof/ci_failure.json"

ITER219_SEAL = "11e335e82100319a4f5f47d86eaea0c8e81edbbc"
ITER219_SOURCE = "78348446598bb4bb87ee5cda115f29d64db5237e"
ITER219_EVIDENCE = (
    "experiments/iter219_temporal_consequence_test_yield/HYPOTHESIS.md",
    "experiments/iter219_temporal_consequence_test_yield/RESULT.md",
    "experiments/iter219_temporal_consequence_test_yield/proof/yield_report.json",
    "experiments/iter219_temporal_consequence_test_yield/proof/analysis_amendment.json",
)

# The exact wrap that failed CI twice, in two consecutive sessions, on the same phrase.
WRAPPED_SENTENCE = "the property instrument is a locator-assisted,\ngold-validated property pipeline"


class Iter220ValidationError(ValueError):
    """Raised when iter220 exceeds its publication-only boundary."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Iter220ValidationError(message)


def git_bytes(*arguments: str) -> bytes:
    result = subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, check=False)
    if result.returncode != 0:
        raise Iter220ValidationError(f"git {' '.join(arguments)} failed")
    return result.stdout


def check_iter219_evidence_unchanged() -> None:
    """Iter219's null must survive its own recovery byte for byte."""

    for path in ITER219_EVIDENCE:
        sealed = git_bytes("show", f"{ITER219_SEAL}:{path}")
        require(
            (ROOT / path).read_bytes() == sealed,
            f"iter219 evidence changed during recovery: {path}",
        )


def check_failure_record(failure: dict[str, Any]) -> None:
    require(
        failure.get("schema_version") == "telos.iter220.ci_failure.v1",
        "unexpected ci_failure schema",
    )
    predecessor = failure["failed_predecessor"]
    require(predecessor["seal_commit"] == ITER219_SEAL, "iter219 seal differs")
    require(predecessor["source_commit"] == ITER219_SOURCE, "iter219 source differs")
    require(predecessor["draft_pull_request"] == 13, "iter219 draft PR differs")
    require(
        predecessor["branch_mutated_after_observation"] is False
        and predecessor["workflow_rerun_after_observation"] is False
        and predecessor["merged"] is False,
        "the failed iter219 branch must remain unmutated, unrerun, and unmerged",
    )
    require(failure["push_ci"]["run_id"] == 29539630378, "push CI run differs")
    require(failure["pull_request_ci"]["run_id"] == 29539645041, "pull-request CI run differs")

    # The root cause must stay recorded as the closure gap, not the sentence.  If a future
    # edit reduces this to "a line wrapped", the mechanism returns.
    root = failure["root_cause"]
    require(
        root.get("guard_commands_declared_by_ci", 0) > 200,
        "the failure record must state how many guards CI actually declares",
    )
    require(
        root.get("local_guards_run_by_iter219", 0) < 20,
        "the failure record must state how few guards the local closure ran",
    )
    require(
        "run_ci_closure.py" in root.get("correction", ""),
        "the recorded correction must be the derived closure runner",
    )
    require(
        failure["recurrence"]["occurrence"] >= 4,
        "the failure record must state that this bug class has recurred",
    )
    for field in (
        "provider_calls",
        "gpu_allocations",
        "containers_built",
        "repository_test_executions",
        "workflow_reruns",
    ):
        require(failure.get(field) == 0, f"{field} must be zero for iter220")


def check_normalizer_forgives_format_but_not_absence() -> None:
    require(
        "locator-assisted, gold-validated" in normalize_prose(WRAPPED_SENTENCE),
        "the normalizer must read the wrapped phrase that failed CI twice",
    )
    require(
        "locator-assisted, gold-validated"
        not in normalize_prose("the property instrument is an independent detector"),
        "the normalizer must not invent a phrase that is genuinely absent",
    )


def check_closure_is_derived_from_ci() -> None:
    commands = run_ci_closure.declared_commands()
    require(len(commands) > 200, "the closure runner must derive the full CI guard set")
    require(
        any("validate_detector_methodology_correction.py" in command for _, command in commands),
        "the closure runner must include the guard iter219 never ran",
    )
    reuse = [command for _, command in commands if "run_iter200_blind_judge.py" in command]
    require(
        bool(reuse) and all("TELOS_NAT_REUSE_JUDGES=1" in command for command in reuse),
        "the closure runner must preserve the workflow's environment overrides",
    )


def validate() -> list[str]:
    problems: list[str] = []
    try:
        require(HYPOTHESIS.exists(), "iter220 hypothesis missing")
        require(FAILURE.exists(), "iter220 ci_failure record missing")
        check_failure_record(json.loads(FAILURE.read_text(encoding="utf-8")))
        check_iter219_evidence_unchanged()
        check_normalizer_forgives_format_but_not_absence()
        check_closure_is_derived_from_ci()
    except Iter220ValidationError as error:
        problems.append(str(error))
    return problems


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    problems = validate()
    if problems:
        for problem in problems:
            print(f"iter220: {problem}")
        return 1
    print("iter220 publication-only recovery validated; iter219 evidence unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
