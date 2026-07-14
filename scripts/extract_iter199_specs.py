#!/usr/bin/env python3
"""iter199: extract repo-correct official eval specs for the iter199 adversary candidates.

Same as extract_iter194_specs.py but driven by the iter199 candidate set. Run with a python that has
`swebench` importable; commits the eval_scripts and spec.json so the CI harness stays hermetic.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "iter199_benchmark_expansion_across_repos"
OUT = EXP / "proof" / "raw" / "specs"
CANDS = EXP / "proof" / "raw" / "candidates"
SNAPSHOT = (
    ROOT
    / "experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/swebench_verified_rows_snapshot.json"
)


def framework_of(eval_script: str) -> str:
    if "runtests.py" in eval_script:
        return "django_runtests"
    if "pytest" in eval_script:
        return "pytest"
    if "bin/test" in eval_script:
        return "sympy_bintest"
    if "tox" in eval_script:
        return "tox"
    return "unknown"


def test_command(eval_script: str) -> str:
    lines = eval_script.splitlines()
    for i, ln in enumerate(lines):
        if "Start Test Output" in ln:
            for cmd in lines[i + 1 :]:
                if "End Test Output" in cmd:
                    break
                if cmd.strip() and not cmd.strip().startswith(":"):
                    return cmd.strip()
    return ""


def main() -> int:
    try:
        from swebench.harness.test_spec.test_spec import make_test_spec
    except Exception as exc:  # pragma: no cover
        print(f"swebench not importable: {exc}; run with a swebench-equipped python")
        return 2

    OUT.mkdir(parents=True, exist_ok=True)
    by_id = {r["instance_id"]: r for r in json.loads(SNAPSHOT.read_text())["rows"]}
    candidates = [
        m["instance_id"]
        for m in json.loads((CANDS / "adversary_summary.json").read_text())["manifest"]
        if m["status"] == "candidate"
    ]

    index = []
    for iid in candidates:
        inst = by_id[iid]
        ts = make_test_spec(inst)
        stem = iid.replace("/", "__")
        (OUT / f"{stem}.eval_script.sh").write_text(ts.eval_script)
        spec = {
            "instance_id": iid,
            "repo": inst["repo"],
            "base_commit": inst["base_commit"],
            "framework": framework_of(ts.eval_script),
            "test_command": test_command(ts.eval_script),
            "fail_to_pass": json.loads(inst["FAIL_TO_PASS"]),
            "pass_to_pass": json.loads(inst["PASS_TO_PASS"]),
            "image": "swebench/sweb.eval.x86_64." + re.sub("__", "_1776_", iid.lower()) + ":latest",
        }
        (OUT / f"{stem}.spec.json").write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")
        index.append(
            {"instance_id": iid, "repo": inst["repo"], "framework": spec["framework"]}
        )

    (OUT / "index.json").write_text(
        json.dumps(
            {"schema_version": "telos.iter199.spec_index.v1", "count": len(index), "specs": index},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    from collections import Counter

    print(f"extracted {len(index)} specs to {OUT.relative_to(ROOT)}")
    print("frameworks:", dict(Counter(s["framework"] for s in index)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
