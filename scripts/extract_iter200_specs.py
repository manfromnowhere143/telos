#!/usr/bin/env python3
"""Extract official eval specs for every neutral-solve model patch.

Certification must precede the optional gold-differential witness. Exact-gold patches and patches for
which scenario generation failed still enter the official-harness denominator. Run with a
swebench-equipped Python. Commit eval scripts and spec JSON so CI stays hermetic.
"""

from __future__ import annotations

from collections import Counter
import hashlib
from importlib import metadata
import json
import os
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / os.environ.get("TELOS_NAT_EXP", "iter200_natural_certified_yet_wrong_rate")
OUT = EXP / "proof" / "raw" / "specs"
SCEN = EXP / "proof" / "raw" / "scenarios"
SNAPSHOT = ROOT / "experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/swebench_verified_rows_snapshot.json"
EXPECTED_SWEBENCH_VERSION = "4.1.0"
SWEBENCH_WHEEL = "swebench-4.1.0-py3-none-any.whl"
SWEBENCH_WHEEL_SHA256 = "1243776f720047cc9e20a427f7a52b75c13a07abda6154fb60fe77f82ec8af57"


def framework_of(s: str) -> str:
    if "runtests.py" in s:
        return "django_runtests"
    if "pytest" in s:
        return "pytest"
    if "bin/test" in s:
        return "sympy_bintest"
    if "tox" in s:
        return "tox"
    return "unknown"


def solution_rows_for_specs(solve_summary: dict, scenarios_summary: dict) -> list[dict]:
    """Return every valid solution, annotated with independent witness availability."""

    scenario_ids = {
        row["instance_id"]
        for row in scenarios_summary["manifest"]
        if row["status"] == "scenario"
    }
    return [
        {
            "instance_id": row["instance_id"],
            "identical_to_gold": bool(row["identical_to_gold"]),
            "scenario_available": row["instance_id"] in scenario_ids,
        }
        for row in solve_summary["manifest"]
        if row["status"] == "solution"
    ]


def main() -> int:
    try:
        installed_version = metadata.version("swebench")
    except metadata.PackageNotFoundError:
        print("swebench not importable: distribution is not installed")
        return 2
    if installed_version != EXPECTED_SWEBENCH_VERSION:
        print(
            "unsupported swebench version: "
            f"expected {EXPECTED_SWEBENCH_VERSION}, got {installed_version}"
        )
        return 2
    try:
        from swebench.harness.test_spec.test_spec import make_test_spec
    except Exception as exc:
        print(f"swebench not importable: {exc}")
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    by = {r["instance_id"]: r for r in json.loads(SNAPSHOT.read_text())["rows"]}
    solve_summary = json.loads((EXP / "proof/raw/solutions/solve_summary.json").read_text())
    scenarios_summary = json.loads((SCEN / "scenarios_summary.json").read_text())
    solution_rows = solution_rows_for_specs(solve_summary, scenarios_summary)
    index = []
    for solution in solution_rows:
        iid = solution["instance_id"]
        inst = by[iid]
        ts = make_test_spec(inst)
        stem = iid.replace("/", "__")
        eval_script = ts.eval_script
        eval_script_sha256 = hashlib.sha256(eval_script.encode()).hexdigest()
        (OUT / f"{stem}.eval_script.sh").write_text(eval_script)
        spec = {
            "instance_id": iid,
            "repo": inst["repo"],
            "base_commit": inst["base_commit"],
            "framework": framework_of(ts.eval_script),
            "eval_script_sha256": eval_script_sha256,
            "fail_to_pass": json.loads(inst["FAIL_TO_PASS"]),
            "pass_to_pass": json.loads(inst["PASS_TO_PASS"]),
            "image": (
                "swebench/sweb.eval.x86_64."
                + re.sub("__", "_1776_", iid.lower())
                + ":latest"
            ),
            "identical_to_gold": solution["identical_to_gold"],
            "scenario_available": solution["scenario_available"],
        }
        (OUT / f"{stem}.spec.json").write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")
        index.append(
            {
                "instance_id": iid,
                "repo": inst["repo"],
                "framework": spec["framework"],
                "eval_script_sha256": eval_script_sha256,
                "identical_to_gold": solution["identical_to_gold"],
                "scenario_available": solution["scenario_available"],
            }
        )
    (OUT / "index.json").write_text(
        json.dumps(
            {
                "schema_version": "telos.iter200.spec_index.v2",
                "count": len(index),
                "generator": {
                    "package": "swebench",
                    "version": EXPECTED_SWEBENCH_VERSION,
                    "distribution_filename": SWEBENCH_WHEEL,
                    "distribution_sha256": SWEBENCH_WHEEL_SHA256,
                    "source_snapshot": str(SNAPSHOT.relative_to(ROOT)),
                    "source_snapshot_sha256": hashlib.sha256(
                        SNAPSHOT.read_bytes()
                    ).hexdigest(),
                },
                "specs": index,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(f"extracted {len(index)} specs; frameworks:", dict(Counter(s["framework"] for s in index)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
