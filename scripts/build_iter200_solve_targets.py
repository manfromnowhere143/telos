#!/usr/bin/env python3
"""Reproduce the frozen iter200 neutral-solve targets from committed inputs."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

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
ITER199 = (
    ROOT
    / "experiments/iter199_benchmark_expansion_across_repos/proof/raw/targets.json"
)
OUT = (
    ROOT
    / "experiments/iter200_natural_certified_yet_wrong_rate/proof/raw/solve_targets.json"
)
IMPLEMENTATION_SOURCES = (
    ROOT / "scripts/build_iter200_solve_targets.py",
    ROOT / "scripts/run_iter200_solver.py",
    ROOT / "scripts/run_certified_resolved_adversary.py",
)
CAP_PER_REPO = 5


def _load_iter200_solver():
    """Load the exact patch builder used by iter200 without requiring a package import."""

    path = ROOT / "scripts/run_iter200_solver.py"
    module_name = "_telos_iter200_solver_for_target_builder"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load iter200 solver from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


solver = _load_iter200_solver()
adv = solver.adv


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def added_run_count(patch: str, source_file: str) -> int:
    """Count contiguous added-line runs in the selected source-file diff."""

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


def load_inputs() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    snapshot = json.loads(SNAPSHOT.read_text())
    iter193 = json.loads(ITER193.read_text())
    iter199 = json.loads(ITER199.read_text())
    return snapshot["rows"], iter193["manifest"], iter199["targets"]


def eligible(row: dict[str, Any], excluded: set[str]) -> bool:
    """Apply the complete historical iter200 compatibility and exclusion rule."""

    if row["instance_id"] in excluded:
        return False
    source_file = adv.one_src(row["patch"])
    if source_file is None or added_run_count(row["patch"], source_file) != 1:
        return False
    gold_lines = adv.added_block(row["patch"], source_file).split("\n")
    rebuilt = solver.build_solve_patch(row["patch"], source_file, gold_lines)
    return rebuilt is not None and rebuilt.strip() == row["patch"].strip()


def build_manifest() -> dict[str, Any]:
    rows, iter193_rows, iter199_rows = load_inputs()
    iter193_ids = {row["instance_id"] for row in iter193_rows}
    iter199_ids = {row["instance_id"] for row in iter199_rows}
    excluded = iter193_ids | iter199_ids

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    eligible_count = 0
    for row in rows:
        if eligible(row, excluded):
            eligible_count += 1
            grouped[row["repo"]].append(
                {"instance_id": row["instance_id"], "repo": row["repo"]}
            )

    targets: list[dict[str, str]] = []
    for repo in sorted(grouped):
        targets.extend(
            sorted(grouped[repo], key=lambda row: row["instance_id"])[
                :CAP_PER_REPO
            ]
        )

    return {
        "schema_version": "telos.iter200.solve_targets.v1",
        "cap_per_repo": CAP_PER_REPO,
        "count": len(targets),
        "eligible_count": eligible_count,
        "eligible_repo_count": len(grouped),
        "constraint": (
            "exclude iter193 Phase-A manifest and iter199 targets; single source file; "
            "exactly one added run; build_solve_patch with the gold added block "
            "strip-round-trips to gold; repositories and instance IDs lexicographic; "
            "cap first 5 per repository"
        ),
        "source_snapshot": {
            "path": relative(SNAPSHOT),
            "sha256": sha256(SNAPSHOT),
            "row_count": len(rows),
        },
        "excluded_target_sources": [
            {
                "iteration": "iter193",
                "path": relative(ITER193),
                "field": "manifest",
                "count": len(iter193_ids),
                "sha256": sha256(ITER193),
            },
            {
                "iteration": "iter199",
                "path": relative(ITER199),
                "field": "targets",
                "count": len(iter199_ids),
                "sha256": sha256(ITER199),
            },
        ],
        "excluded_target_union_count": len(excluded),
        "implementation_sources": [
            {"path": relative(path), "sha256": sha256(path)}
            for path in IMPLEMENTATION_SOURCES
        ],
        "targets": targets,
    }


def check_manifest(path: Path | None = None) -> bool:
    if path is None:
        path = OUT
    try:
        committed = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read iter200 target manifest: {exc}", file=sys.stderr)
        return False
    if committed != build_manifest():
        print("iter200 target manifest does not reproduce", file=sys.stderr)
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)

    manifest = build_manifest()
    rendered = json.dumps(manifest, indent=2, sort_keys=False) + "\n"
    if args.check:
        if not check_manifest():
            return 1
        print(
            "iter200 target manifest reproduces: "
            f"{manifest['eligible_count']} eligible / {manifest['count']} selected targets"
        )
    elif args.write:
        OUT.write_text(rendered)
        print(f"wrote {manifest['count']} targets to {OUT.relative_to(ROOT)}")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
