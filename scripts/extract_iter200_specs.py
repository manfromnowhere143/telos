#!/usr/bin/env python3
"""iter200: extract official eval specs for the neutral-solve instances with a witnessing scenario.

Run with a swebench-equipped python. Commits eval_scripts and spec.json so CI stays hermetic.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "iter200_natural_certified_yet_wrong_rate"
OUT = EXP / "proof" / "raw" / "specs"
SCEN = EXP / "proof" / "raw" / "scenarios"
SNAPSHOT = ROOT / "experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/swebench_verified_rows_snapshot.json"


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


def main() -> int:
    try:
        from swebench.harness.test_spec.test_spec import make_test_spec
    except Exception as exc:
        print(f"swebench not importable: {exc}")
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    by = {r["instance_id"]: r for r in json.loads(SNAPSHOT.read_text())["rows"]}
    ids = [
        m["instance_id"]
        for m in json.loads((SCEN / "scenarios_summary.json").read_text())["manifest"]
        if m["status"] == "scenario"
    ]
    index = []
    for iid in ids:
        inst = by[iid]
        ts = make_test_spec(inst)
        stem = iid.replace("/", "__")
        (OUT / f"{stem}.eval_script.sh").write_text(ts.eval_script)
        spec = {"instance_id": iid, "repo": inst["repo"], "base_commit": inst["base_commit"],
                "framework": framework_of(ts.eval_script),
                "fail_to_pass": json.loads(inst["FAIL_TO_PASS"]), "pass_to_pass": json.loads(inst["PASS_TO_PASS"]),
                "image": "swebench/sweb.eval.x86_64." + re.sub("__", "_1776_", iid.lower()) + ":latest"}
        (OUT / f"{stem}.spec.json").write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")
        index.append({"instance_id": iid, "repo": inst["repo"], "framework": spec["framework"]})
    (OUT / "index.json").write_text(json.dumps({"schema_version": "telos.iter200.spec_index.v1", "count": len(index), "specs": index}, indent=2, sort_keys=True) + "\n")
    from collections import Counter
    print(f"extracted {len(index)} specs; frameworks:", dict(Counter(s["framework"] for s in index)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
