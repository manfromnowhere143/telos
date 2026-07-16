#!/usr/bin/env python3
"""Validate iter219's sealed rules, report arithmetic, and claim boundary.

The load-bearing check is drift: the instrument's frozen constants must still equal the
rules written in the sealed hypothesis, and every reported number must recompute from the
report's own rows.  A gate that only asserts "a report exists" would pass while the thing
it guards is broken.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.measure_iter219_temporal_yield import (  # noqa: E402
    DELTAS_DAYS,
    PERMUTATION_SALT,
    PRIMARY_DELTA,
)
from telos.tcp1 import exact_one_sided_mcnemar, wilson_interval  # noqa: E402

PREFIX = "experiments/iter219_temporal_consequence_test_yield/"
HYPOTHESIS = ROOT / PREFIX / "HYPOTHESIS.md"
RESULT = ROOT / PREFIX / "RESULT.md"
REPORT = ROOT / PREFIX / "proof/yield_report.json"
AMENDMENT = ROOT / PREFIX / "proof/analysis_amendment.json"

# Bars exactly as sealed in HYPOTHESIS.md.
BAR_PRIMARY_YIELD = 0.20
BAR_PRIMARY_WILSON_LOWER = 0.10
BAR_MCNEMAR_P = 0.01
BAR_YIELD_DIFFERENCE = 0.10
BAR_MAX_SINGLE_REPO_SHARE = 0.50
BAR_SYMBOL_EXTRACTION_RATE = 0.90

FORBIDDEN_CLAIMS = (
    "state of the art",
    "state-of-the-art",
    "population rate",
    "prevalence estimate",
    "proves coverage",
    "proves that the test executes",
    "tcp-1 is feasible",
    "detector efficacy",
    "product efficacy",
)


class Iter219ValidationError(ValueError):
    """Raised when iter219 loses its sealed measurement boundary."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Iter219ValidationError(message)


def normalize(text: str) -> str:
    """Collapse whitespace runs so a Markdown line wrap cannot break a required phrase.

    A wrapped sentence silently failed a required-phrase scan once before in this
    repository.  Matching against normalized text removes that failure mode instead of
    depending on prose staying reflowed by hand.
    """

    return " ".join(text.split())


def check_sealed_rules_match_instrument(raw: str) -> None:
    """The sealed prose and the executable constants must not drift apart."""

    text = normalize(raw)
    require(
        f"`Δ ∈ {{{', '.join(str(d) for d in DELTAS_DAYS)}}}`" in text,
        f"hypothesis must seal the exact window set {DELTAS_DAYS}",
    )
    require(
        f"primary window is `Δ = {PRIMARY_DELTA}`" in text,
        f"hypothesis must seal primary window {PRIMARY_DELTA}",
    )
    require(
        f'"{PERMUTATION_SALT}"' in text,
        "hypothesis must seal the exact permutation salt used by the instrument",
    )
    require(
        f"`Y({PRIMARY_DELTA}) ≥ {BAR_PRIMARY_YIELD:.2f}`" in text,
        "hypothesis must seal the primary yield bar",
    )
    require(
        f"`≥ {BAR_PRIMARY_WILSON_LOWER:.2f}`" in text,
        "hypothesis must seal the Wilson lower bar",
    )
    require(
        f"`p < {BAR_MCNEMAR_P:.2f}`" in text,
        "hypothesis must seal the McNemar bar",
    )
    # Amendment A1 is the difference between a real measurement and a tautology.  If the
    # hypothesis ever loses it, the forward window silently readmits the task's own
    # fixing-PR tests and the primary yield becomes meaningless.
    require(
        "test_patch" in text and "visible grader, not a hidden consequence test" in text,
        "hypothesis must retain amendment A1 excluding the task's own fixing-PR tests",
    )
    require(
        "Y_backward" in text,
        "hypothesis must retain amendment A2's backward within-repository control",
    )


def check_amendment(amendment: dict[str, Any]) -> None:
    require(
        amendment.get("schema_version") == "telos.iter219.analysis_amendment.v1",
        "unexpected amendment schema",
    )
    require(
        amendment.get("recorded_before_any_observation") is True,
        "the amendment must be recorded before any observation",
    )
    state = amendment.get("observation_state_at_amendment", {})
    require(
        state.get("yield_report_exists") is False
        and state.get("instances_measured") == 0
        and state.get("overlap_counts_observed") == 0
        and state.get("control_counts_observed") == 0,
        "the amendment must record that no outcome existed when it was written",
    )
    ids = {item["id"] for item in amendment.get("amendments", [])}
    require({"A1", "A2", "A3"} <= ids, "amendments A1, A2, and A3 must all be recorded")
    for item in amendment["amendments"]:
        require(
            item.get("changes_thresholds") is False,
            f"amendment {item['id']} must not move a sealed threshold",
        )
    # A limitation that is silently dropped becomes an overclaim by omission.
    limitation_ids = {
        item["id"] for item in amendment.get("known_limitations_disclosed_not_fixed", [])
    }
    require(
        {"L1", "L2", "L3", "L4"} <= limitation_ids,
        "known limitations L1, L2, L3, and L4 must remain disclosed",
    )
    for item in amendment["known_limitations_disclosed_not_fixed"]:
        require(
            bool(item.get("direction_of_bias")),
            f"limitation {item['id']} must state its direction of bias",
        )
    # L4 fixes what a null means BEFORE the null is known.  Without it, a low yield can be
    # retold after the fact as "maintainer consequence tests do not exist", which this
    # instrument cannot show: it cannot see public-API tests that never name the symbol.
    l4 = next(
        item
        for item in amendment["known_limitations_disclosed_not_fixed"]
        if item["id"] == "L4"
    )
    rule = l4.get("inference_rule_fixed_before_observation", {})
    require(
        bool(rule.get("if_pass")) and bool(rule.get("if_null")),
        "L4 must fix the inference for both a pass and a null before observation",
    )
    require(
        "does NOT falsify the harvest hypothesis" in rule["if_null"],
        "L4's null branch must preserve that a null does not falsify the harvest hypothesis",
    )


def check_report_recomputes(report: dict[str, Any]) -> None:
    """Every headline number must regenerate from the report's own rows."""

    require(
        report.get("schema_version") == "telos.iter219.yield_report.v1",
        "unexpected report schema",
    )
    require(
        report.get("deltas_days") == list(DELTAS_DAYS),
        "report windows drifted from the instrument",
    )
    require(
        report.get("permutation_salt") == PERMUTATION_SALT,
        "report permutation salt drifted from the instrument",
    )

    seen = report["instances_seen"]
    included = report["instances_included"]
    excluded = report["instances_excluded"]
    require(
        seen == included + excluded,
        f"instance accounting does not close: {seen} != {included} + {excluded}",
    )
    require(
        excluded == sum(report["exclusion_counts"].values()),
        "exclusion counts do not sum to the excluded total",
    )

    for delta in DELTAS_DAYS:
        block = report["results_by_delta"][str(delta)]
        rows = block["rows"]
        require(len(rows) == included, f"delta={delta}: row count != included instances")

        real_hits = sum(1 for row in rows if row["real"])
        control_hits = sum(1 for row in rows if row["control"])
        require(
            block["real_hits"] == real_hits,
            f"delta={delta}: real_hits does not match rows",
        )
        require(
            block["control_hits"] == control_hits,
            f"delta={delta}: control_hits does not match rows",
        )

        n = block["n"]
        require(n == included, f"delta={delta}: n != included instances")
        require(
            abs(block["real_yield"] - real_hits / n) < 1e-12,
            f"delta={delta}: real_yield does not recompute",
        )
        require(
            abs(block["control_yield"] - control_hits / n) < 1e-12,
            f"delta={delta}: control_yield does not recompute",
        )

        expected_real_ci = list(wilson_interval(real_hits, n))
        require(
            block["real_wilson_95"] == expected_real_ci,
            f"delta={delta}: real Wilson interval does not recompute",
        )
        expected_control_ci = list(wilson_interval(control_hits, n))
        require(
            block["control_wilson_95"] == expected_control_ci,
            f"delta={delta}: control Wilson interval does not recompute",
        )

        backward_hits = sum(1 for row in rows if row["backward_control"])
        require(
            block["backward_control_hits"] == backward_hits,
            f"delta={delta}: backward_control_hits does not match rows",
        )
        require(
            abs(block["backward_control_yield"] - backward_hits / n) < 1e-12,
            f"delta={delta}: backward_control_yield does not recompute",
        )
        require(
            block["backward_control_wilson_95"] == list(wilson_interval(backward_hits, n)),
            f"delta={delta}: backward Wilson interval does not recompute",
        )

        pairs = [(row["real"], row["control"]) for row in rows]
        require(
            block["mcnemar_real_gt_control"] == exact_one_sided_mcnemar(pairs),
            f"delta={delta}: McNemar result does not recompute",
        )
        backward_pairs = [(row["real"], row["backward_control"]) for row in rows]
        require(
            block["mcnemar_real_gt_backward"] == exact_one_sided_mcnemar(backward_pairs),
            f"delta={delta}: backward McNemar result does not recompute",
        )

        # L1: without exposure counts, a reader cannot separate a temporal effect from
        # repository growth.  The diagnostic must be present and must recompute.
        exposure = block.get("exposure")
        require(exposure is not None, f"delta={delta}: exposure diagnostic missing")
        require(
            exposure["forward_added_tests_total"]
            == sum(row["forward_added_tests"] for row in rows),
            f"delta={delta}: forward exposure total does not recompute",
        )
        require(
            exposure["backward_added_tests_total"]
            == sum(row["backward_added_tests"] for row in rows),
            f"delta={delta}: backward exposure total does not recompute",
        )

        # No instance may be its own control, and no control may share its repository.
        repo_of = {row["instance_id"]: row["repo"] for row in rows}
        for row in rows:
            partner = row["control_partner"]
            require(
                partner != row["instance_id"],
                f"delta={delta}: {row['instance_id']} is its own control",
            )
            require(
                repo_of.get(partner) != row["repo"],
                f"delta={delta}: {row['instance_id']} paired within its own repository",
            )


def check_zero_action(report: dict[str, Any]) -> None:
    for field in (
        "provider_calls",
        "gpu_allocations",
        "containers_built",
        "repository_test_executions",
    ):
        require(report.get(field) == 0, f"{field} must be zero for iter219")
    require(
        report.get("scientific_result_claimed") is False,
        "iter219 claims no scientific result",
    )


def check_result_digests_are_not_invented(result_text: str, report: dict[str, Any]) -> None:
    """Every 64-hex digest in the result must exist verbatim in the evidence.

    A digest is the one claim a reader will never verify by hand, which makes it the
    easiest thing in a scientific record to fabricate.  One was fabricated while drafting
    this very result: the first 16 characters were copied from a log line and the
    remaining 48 were invented.  Bind prose digests to the artifact so prose cannot drift
    from evidence again.
    """

    known = {report["dataset"]["rows_sha256"]}
    for entry in report.get("repositories", {}).values():
        known.add(entry["head_sha"])

    for digest in set(re.findall(r"\b[0-9a-f]{64}\b", result_text)):
        require(
            digest in known,
            f"result states a 64-hex digest absent from the evidence: {digest}",
        )


def check_claim_boundary(text: str) -> None:
    lowered = text.lower()
    for phrase in FORBIDDEN_CLAIMS:
        require(phrase not in lowered, f"forbidden claim present: {phrase!r}")
    require(
        "screen" in lowered,
        "the result must describe static token overlap as a screen",
    )


def validate(preflight: bool = False) -> list[str]:
    problems: list[str] = []
    try:
        require(HYPOTHESIS.exists(), "iter219 hypothesis missing")
        hypothesis_text = HYPOTHESIS.read_text(encoding="utf-8")
        check_sealed_rules_match_instrument(hypothesis_text)

        require(AMENDMENT.exists(), "iter219 pre-data amendment missing")
        check_amendment(json.loads(AMENDMENT.read_text(encoding="utf-8")))

        if preflight:
            return problems

        require(REPORT.exists(), "iter219 yield report missing")
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        check_report_recomputes(report)
        check_zero_action(report)

        require(RESULT.exists(), "iter219 result missing")
        result_text = RESULT.read_text(encoding="utf-8")
        check_claim_boundary(result_text)
        check_result_digests_are_not_invented(result_text, report)
    except Iter219ValidationError as error:
        problems.append(str(error))
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="check only the sealed rules, before the report exists",
    )
    args = parser.parse_args()

    problems = validate(preflight=args.preflight)
    if problems:
        for problem in problems:
            print(f"iter219: {problem}")
        return 1
    print("iter219 sealed rules, report arithmetic, and claim boundary validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
