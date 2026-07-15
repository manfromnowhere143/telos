#!/usr/bin/env python3
"""Reproduce the frozen iter202 neutral-solve target manifest from committed inputs."""

from __future__ import annotations

import argparse
from collections import defaultdict
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = (
    ROOT
    / "experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/"
    "swebench_verified_rows_snapshot.json"
)
ITER193 = (
    ROOT
    / "experiments/iter193_certified_resolved_reward_hack_construction/proof/raw/"
    "phase_a_candidates/phase_a_summary.json"
)
ITER199 = ROOT / "experiments/iter199_benchmark_expansion_across_repos/proof/raw/targets.json"
ITER200 = (
    ROOT
    / "experiments/iter200_natural_certified_yet_wrong_rate/proof/raw/solve_targets.json"
)
OUT = ROOT / "experiments/iter202_natural_rate_scaled/proof/raw/solve_targets.json"
CAP_PER_REPO = 16

_spec = importlib.util.spec_from_file_location(
    "iter200_solver", ROOT / "scripts/run_iter200_solver.py"
)
if _spec is None or _spec.loader is None:
    raise RuntimeError("cannot load iter200 solver")
solver = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(solver)
adv = solver.adv


def added_run_count(patch: str, source_file: str) -> int:
    """Count contiguous added-line runs in the selected source file."""

    in_source = False
    in_run = False
    count = 0
    for line in patch.splitlines():
        if line.startswith("+++ b/"):
            in_source = line[6:] == source_file
            in_run = False
            continue
        if line.startswith("diff --git") or line.startswith("--- a/"):
            in_source = False
            in_run = False
            continue
        is_added = in_source and line.startswith("+") and not line.startswith("+++")
        if is_added and not in_run:
            count += 1
        in_run = is_added
    return count


def excluded_ids() -> set[str]:
    iter193 = json.loads(ITER193.read_text())
    iter199 = json.loads(ITER199.read_text())
    iter200 = json.loads(ITER200.read_text())
    return {
        *(row["instance_id"] for row in iter193["manifest"]),
        *(row["instance_id"] for row in iter199["targets"]),
        *(row["instance_id"] for row in iter200["targets"]),
    }


def eligible(row: dict, excluded: set[str]) -> bool:
    if row["instance_id"] in excluded:
        return False
    source_file = adv.one_src(row["patch"])
    if source_file is None or added_run_count(row["patch"], source_file) != 1:
        return False
    gold_lines = adv.added_block(row["patch"], source_file).split("\n")
    rebuilt = solver.build_solve_patch(row["patch"], source_file, gold_lines)
    return rebuilt is not None and rebuilt.strip() == row["patch"].strip()


def build_manifest() -> dict:
    rows = json.loads(SNAPSHOT.read_text())["rows"]
    grouped: dict[str, list[dict]] = defaultdict(list)
    excluded = excluded_ids()
    for row in rows:
        if eligible(row, excluded):
            grouped[row["repo"]].append(
                {"instance_id": row["instance_id"], "repo": row["repo"]}
            )

    targets = []
    for repo in sorted(grouped):
        targets.extend(
            sorted(grouped[repo], key=lambda row: row["instance_id"])[:CAP_PER_REPO]
        )
    return {
        "schema_version": "telos.iter202.solve_targets.v1",
        "cap_per_repo": CAP_PER_REPO,
        "count": len(targets),
        "constraint": (
            "single-source-file single-added-run build_solve_patch round-trips; "
            "excludes iter193/199/200"
        ),
        "pooled_with": (
            "iter200 (39 attempted patches; official-harness backfill complete: "
            "37 valid patches, corrected certified N=24, k=1 strict confirmed case, "
            "u=6 declared missing outcomes)"
        ),
        "targets": targets,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    manifest = build_manifest()
    rendered = json.dumps(manifest, indent=2, sort_keys=False) + "\n"
    if args.check:
        current = json.loads(OUT.read_text())
        if current != manifest:
            print("iter202 target manifest does not reproduce")
            return 1
        print(f"iter202 target manifest reproduces: {manifest['count']} targets")
    elif args.write:
        OUT.write_text(rendered)
        print(f"wrote {manifest['count']} targets to {OUT.relative_to(ROOT)}")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
