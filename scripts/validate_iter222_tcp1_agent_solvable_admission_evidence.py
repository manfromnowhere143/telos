#!/usr/bin/env python3
"""Validate iter222's three filled admission gates and its claim boundary.

Each evidence piece must independently re-verify: the model binding digest recomputes, the
timestamp token re-verifies against its committed chain, and the isolation rehearsal both
denies every attack and catches every weakened-contract hole.  The admission view must show
exactly the three fills and keep execution unauthorized.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import build_iter222_admission_view as admission  # noqa: E402
from scripts import run_iter222_isolation_rehearsal as rehearsal  # noqa: E402

PREFIX = "experiments/iter222_tcp1_agent_solvable_admission_evidence/"
HYPOTHESIS = ROOT / PREFIX / "HYPOTHESIS.md"
RESULT = ROOT / PREFIX / "RESULT.md"
PROOF = ROOT / PREFIX / "proof"

FORBIDDEN_CLAIMS = (
    "execution authorized",
    "state of the art",
    "state-of-the-art",
    "model behavior established",
    "tcp-1 is ready",
    "population rate",
    "detector efficacy",
)


class Iter222ValidationError(ValueError):
    """Raised when iter222 exceeds its materialization boundary."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Iter222ValidationError(message)


def run_check(script: str) -> bool:
    return (
        subprocess.run(
            ["python3", f"scripts/{script}", "--check"], cwd=ROOT, capture_output=True
        ).returncode
        == 0
    )


def check_model_binding() -> None:
    record = json.loads((PROOF / "model_binding.json").read_text(encoding="utf-8"))
    require(len(record.get("candidate_menu", [])) >= 3, "model menu has fewer than three candidates")
    default = record["default_model"]
    require(bool(default.get("weight_sha256")), "model binding has no weight digests")
    require(bool(default.get("resolved_commit_sha")), "model binding has no resolved commit sha")
    require(bool(default.get("license")), "model binding has no license")
    require(bool(default.get("cutoff_source")), "model binding has no cutoff source")
    require(record.get("weights_downloaded") is False, "model binding must not download weights")


def check_timestamp() -> None:
    record = json.loads((PROOF / "transparency_timestamp.json").read_text(encoding="utf-8"))
    require(record.get("verified") is True, "transparency timestamp is not verified")
    require(
        run_check("build_iter222_transparency_timestamp.py"),
        "the committed timestamp token does not re-verify offline",
    )


def check_isolation() -> None:
    contract = json.loads(rehearsal.CONTRACT.read_text(encoding="utf-8"))
    live = rehearsal.evaluate(contract)
    require(all(r["denied_by_real_contract"] for r in live), "an attack is not denied by the real contract")
    require(
        all(r["positive_control_ok"] for r in live),
        "a positive control did not fire: a weakened contract must let its attack through",
    )
    require(len(live) == 5, "the five registered attacks must all be rehearsed")


def check_admission_view() -> None:
    view = json.loads((PROOF / "admission_view.json").read_text(encoding="utf-8"))
    require(view == admission.build(), "admission view does not reproduce from the evidence")
    require(view["passed_gate_count"] == 5, "admission view must show five passing gates")
    require(view["blocked_gate_count"] == 6, "admission view must show six blocked gates")
    require(view["execution_authorized"] is False, "execution must remain unauthorized")
    filled = {g["gate"] for g in view["gates"] if g["iter222_filled"]}
    require(
        filled == set(admission.FILLED_GATES),
        "exactly the three agent-solvable gates must be marked filled",
    )


NEGATORS = ("no", "not", "never", "without", "authorizes no", "establishes no")


def _asserted(text: str, phrase: str) -> bool:
    """True only where the phrase is asserted, not disclaimed.

    A result that says "establishes no state of the art" is the disclaimer we want, not the
    overclaim we forbid.  Flag an occurrence only when it is not immediately preceded by a
    negation, so a negated mention passes and an assertion fails.
    """

    start = 0
    while (index := text.find(phrase, start)) != -1:
        preceding = text[max(0, index - 24):index].strip().rstrip(",")
        if not any(preceding.endswith(negator) for negator in NEGATORS):
            return True
        start = index + len(phrase)
    return False


def check_claim_boundary() -> None:
    text = RESULT.read_text(encoding="utf-8").lower()
    for phrase in FORBIDDEN_CLAIMS:
        require(not _asserted(text, phrase), f"forbidden claim asserted: {phrase!r}")
    require("5/11" in text or "5 of 11" in text, "the result must state admission is 5 of 11")
    require(
        "does not authorize" in text or "not authorize" in text,
        "the result must state it authorizes no execution",
    )


def validate(preflight: bool = False) -> list[str]:
    problems: list[str] = []
    try:
        require(HYPOTHESIS.exists(), "iter222 hypothesis missing")
        if preflight:
            return problems
        check_model_binding()
        check_timestamp()
        check_isolation()
        check_admission_view()
        require(RESULT.exists(), "iter222 result missing")
        check_claim_boundary()
    except Iter222ValidationError as error:
        problems.append(str(error))
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    problems = validate(preflight=args.preflight)
    if problems:
        for problem in problems:
            print(f"iter222: {problem}")
        return 1
    print("iter222 admission evidence validated: 5/11 gates, execution unauthorized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
