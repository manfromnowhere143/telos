#!/usr/bin/env python3
"""Score a detector's decisions against the natural certified-yet-wrong benchmark.

Takes a JSON list of ``{"row_id": ..., "flagged": true|false}`` and reports recall, false-positive rate,
Wilson intervals, the missing-outcome triple, and the recall split by divergence type — the same reporting
contract this benchmark's own baselines are held to.

A row a detector does not decide is **missing, not negative**. Reporting only the observed rate would let a
detector improve its number by declining to answer, so all three quantities are always printed together:
observed lower, worst-case missing upper, and complete-case.

``--reproduce-baselines`` re-derives the three committed baselines from repository evidence and scores them
through this harness. If the harness cannot reproduce them, the harness is wrong — that is the point of the
check, and it is an iter233 acceptance bar.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.adjudicate_iter231 import _rates  # noqa: E402  (one interval implementation, not two)

EXP = ROOT / "experiments/iter233_natural_benchmark_release"
RELEASE = EXP / "release"
ANSWERS = RELEASE / "answers/answers.json"

BASELINES = {
    "iter230_static": (
        ROOT / "experiments/iter230_gold_free_detector_natural/proof/raw/detector/"
        "detector_summary.json", (2, 5),
    ),
    "iter231_oracle": (
        ROOT / "experiments/iter231_gold_free_execution_oracle/proof/oracle_result.json", (4, 10),
    ),
    "iter232_oracle": (
        ROOT / "experiments/iter232_validated_exercise_instrument/proof/oracle_result.json", (2, 12),
    ),
}


def load_answers() -> dict:
    return {row["row_id"]: row for row in json.loads(ANSWERS.read_text())["answers"]}


def score(decisions: dict[str, bool], answers: dict) -> dict:
    positives = [r for r in answers.values() if r["label"] == "certified_yet_wrong"]
    negatives = [r for r in answers.values() if r["label"] == "certified_correct"]

    def rates(subset: list[dict]) -> dict:
        decided = [r for r in subset if r["row_id"] in decisions]
        flagged = sum(1 for r in decided if decisions[r["row_id"]])
        return _rates(flagged, len(subset), len(subset) - len(decided))

    return {
        "recall": rates(positives),
        "false_positive_rate": rates(negatives),
        "recall_by_divergence_type": {
            divergence: rates([r for r in positives if r.get("divergence_type") == divergence])
            for divergence in ("crash_or_type", "value")
        },
        # The hard-negative view: the 29 gold-identical negatives are trivially separable by anyone
        # consulting public gold, so a detector's rate over the remaining negatives is the more
        # informative number. Reported alongside, never instead.
        "decided_rows": len(decisions),
    }


def baseline_decisions(name: str) -> dict[str, bool]:
    """Re-derive a committed baseline's per-row decisions, keyed by release row id."""

    import hashlib

    path, _ = BASELINES[name]
    payload = json.loads(path.read_text())
    decisions: dict[str, bool] = {}

    def row_id(run: str, instance_id: str) -> str:
        return "row-" + hashlib.sha256(f"{run}\0{instance_id}".encode()).hexdigest()[:12]

    if name == "iter230_static":
        for row in payload["per_patch"]:
            decisions[row_id(row["run"], row["instance_id"])] = bool(row["flagged"])
    else:
        for row in payload["rows"]:
            if row["outcome"] != "observed":
                continue  # undecided rows stay missing, not negative
            decisions[row_id(row["run"], row["instance_id"])] = bool(row["flagged"])
    return decisions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decisions", type=Path, help="JSON list of {row_id, flagged}")
    parser.add_argument("--reproduce-baselines", action="store_true")
    args = parser.parse_args()

    answers = load_answers()

    if args.reproduce_baselines:
        failures = 0
        for name, (_, expected) in BASELINES.items():
            result = score(baseline_decisions(name), answers)
            got = (
                result["recall"]["observed_lower"]["k"],
                result["false_positive_rate"]["observed_lower"]["k"],
            )
            ok = got == expected
            failures += not ok
            print(
                f"{'ok  ' if ok else 'FAIL'} {name:16s} recall {got[0]}/13, "
                f"false positives {got[1]}/54  (expected {expected[0]}/13, {expected[1]}/54)"
            )
        if failures:
            print(f"{failures} baseline(s) not reproduced by the harness", file=sys.stderr)
            return 1
        print("all three committed baselines reproduce through the release harness")
        return 0

    if not args.decisions:
        parser.error("--decisions is required unless --reproduce-baselines is given")
    raw = json.loads(args.decisions.read_text())
    decisions = {row["row_id"]: bool(row["flagged"]) for row in raw}
    unknown = sorted(set(decisions) - set(answers))
    if unknown:
        print(f"unknown row ids in decisions: {unknown[:5]}", file=sys.stderr)
        return 2

    result = score(decisions, answers)
    for name in ("recall", "false_positive_rate"):
        rate = result[name]
        low, high = rate["observed_lower"]["wilson95"]
        print(
            f"{name:20s} {rate['observed_lower']['k']}/{rate['observed_lower']['n']} "
            f"Wilson [{low:.3f}, {high:.3f}]  upper {rate['worst_case_missing_upper']['k']}"
            f"/{rate['worst_case_missing_upper']['n']}  complete-case "
            f"{rate['complete_case']['k']}/{rate['complete_case']['n']}  "
            f"missing {rate['missing_outcomes']}"
        )
    for divergence, rate in result["recall_by_divergence_type"].items():
        print(
            f"  recall {divergence:14s} {rate['observed_lower']['k']}/{rate['observed_lower']['n']}"
            f"  missing {rate['missing_outcomes']}"
        )
    print(
        "\nReminder: 29 of 54 negatives are byte-identical to public gold. If this detector consults "
        "gold, or anything derived from it, the numbers above are meaningless. See release/README.md."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
