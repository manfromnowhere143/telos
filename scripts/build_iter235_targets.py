#!/usr/bin/env python3
"""Derive the iter235 recovery cohort mechanically from committed per-candidate evidence.

A row qualifies when it is certified by the official harness, is NOT normalized-identical to gold, and has
no complete outcome — meaning no usable gold-differential witness was ever obtained. Those rows are the ``u``
term in every published natural-rate result.

Selection reads three booleans that were committed long before iter235 existed. It never reads a label, a
divergence, or a judge verdict, because for these rows none exists. That is what makes regeneration
instrument repair rather than outcome fishing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/iter235_witness_recovery/proof/raw/targets.json"

RUNS = (
    "iter200_natural_certified_yet_wrong_rate",
    "iter223_natural_rate_safety_aware",
    "iter225_cross_model_generalization",
    "iter226_cross_model_generalization_gpt54",
    "iter227_cross_provider_generalization",
    "iter229_cross_provider_gemini",
)
SCHEMA = "telos.iter235.targets.v1"


def build() -> dict:
    targets, per_run = [], {}
    for run in RUNS:
        path = ROOT / f"experiments/{run}/proof/iter200_per_candidate.json"
        rows = json.loads(path.read_text())["candidates"]
        certified = [r for r in rows if r.get("certified_resolved")]
        qualifying = [
            r for r in certified
            if not r.get("gold_equivalent_after_terminal_lf_normalization")
            and not r.get("outcome_complete")
        ]
        for row in sorted(qualifying, key=lambda r: r["instance_id"]):
            targets.append({
                "run": run,
                "instance_id": row["instance_id"],
                "repo": row.get("repo"),
                # Why it is unadjudicable, which determines what regeneration must fix.
                "prior_state": (
                    "no_scenario" if not row.get("scenario_available")
                    else "scenario_without_usable_result"
                ),
            })
        per_run[run] = {"certified": len(certified), "unadjudicated": len(qualifying)}

    return {
        "schema_version": SCHEMA,
        "selection_rule": (
            "certified_resolved AND NOT gold_equivalent_after_terminal_lf_normalization "
            "AND NOT outcome_complete"
        ),
        "selection_never_reads": ["label", "divergence", "judge verdict"],
        "runs": per_run,
        "certified_total": sum(v["certified"] for v in per_run.values()),
        "count": len(targets),
        "prior_state_counts": {
            state: sum(1 for t in targets if t["prior_state"] == state)
            for state in ("no_scenario", "scenario_without_usable_result")
        },
        "targets": targets,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    built = build()
    payload = json.dumps(built, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUT.is_file() or OUT.read_text() != payload:
            print("iter235 targets do not regenerate from committed evidence", file=sys.stderr)
            return 1
        print(
            f"iter235 targets regenerate: {built['count']} unadjudicated of "
            f"{built['certified_total']} certified"
        )
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(payload)
    digest = hashlib.sha256(payload.encode()).hexdigest()[:12]
    print(
        f"iter235 targets: {built['count']} unadjudicated of {built['certified_total']} certified "
        f"({built['prior_state_counts']['no_scenario']} never had a scenario, "
        f"{built['prior_state_counts']['scenario_without_usable_result']} had one without a usable "
        f"result); sha {digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
