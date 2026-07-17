#!/usr/bin/env python3
"""Deterministically build the iter228 fresh diverse-cohort target manifest.

Selects SWE-bench Verified rows that (a) pass the same eligibility shape used by the
neutral solver — a single non-test source file with exactly one added run — and (b) are
disjoint from the natural-rate measurement cohorts iter200, iter223 (the frozen 53), and
iter224. To force repository diversity (the fixed 53-target cohort and iter224 were
django/sympy-dominated), django is capped; every other eligible repository contributes all
its eligible targets. Selection is fully deterministic: targets are sorted by instance id
and taken in order, so the manifest regenerates byte-for-byte.

Run: python3 scripts/build_iter228_cohort.py   (writes the frozen solve_targets.json)
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / (
    "experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/"
    "swebench_verified_rows_snapshot.json"
)
OUT = ROOT / "experiments/iter228_fresh_diverse_cohort/proof/raw/solve_targets.json"
DJANGO_CAP = 8
PRIOR_COHORTS = (
    "experiments/iter200_natural_certified_yet_wrong_rate/proof/raw/solve_targets.json",
    "experiments/iter225_cross_model_generalization/proof/raw/solve_targets.json",  # the frozen 53
    "experiments/iter224_natural_rate_scale_n/proof/raw/solve_targets.json",
)


def _ids(path: Path) -> set[str]:
    try:
        return {t["instance_id"] for t in json.loads(path.read_text())["targets"]}
    except Exception:  # noqa: BLE001 — a missing prior cohort simply contributes no exclusions
        return set()


def _one_src(patch: str) -> str | None:
    fs = [
        line[6:] for line in patch.splitlines()
        if line.startswith("+++ b/")
        and "/test" not in line and "test_" not in line.split("/")[-1]
    ]
    return fs[0] if len(fs) == 1 else None


def _one_added_run(patch: str, srcf: str) -> bool:
    runs = 0
    in_srcf = False
    prev_add = False
    for line in patch.splitlines():
        if line.startswith("+++ b/"):
            in_srcf = srcf in line
        if in_srcf and line.startswith("+") and not line.startswith("+++"):
            if not prev_add:
                runs += 1
            prev_add = True
        else:
            prev_add = False
    return runs == 1


def main() -> int:
    rows = json.loads(SNAPSHOT.read_text())["rows"]
    excluded: set[str] = set()
    for rel in PRIOR_COHORTS:
        excluded |= _ids(ROOT / rel)

    eligible: list[tuple[str, str]] = []
    for row in sorted(rows, key=lambda r: r["instance_id"]):
        iid = row["instance_id"]
        if iid in excluded:
            continue
        srcf = _one_src(row["patch"])
        if not srcf or not _one_added_run(row["patch"], srcf):
            continue
        eligible.append((iid, row["repo"]))

    selected: list[dict] = []
    django = 0
    for iid, repo in eligible:
        if repo == "django/django":
            if django >= DJANGO_CAP:
                continue
            django += 1
        selected.append({"instance_id": iid, "repo": repo})

    repos = sorted({t["repo"] for t in selected})
    manifest = {
        "schema_version": "telos.iter228.solve_targets.v1",
        "django_cap": DJANGO_CAP,
        "count": len(selected),
        "repositories": len(repos),
        "constraint": (
            "single-non-test-source-file single-added-run; disjoint from iter200, "
            "iter223 (frozen 53), and iter224; django capped for repository diversity; "
            "standalone (not pooled) — prior detector-construction exposure not audited"
        ),
        "targets": selected,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"iter228 cohort: {len(selected)} targets across {len(repos)} repos: {repos}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
