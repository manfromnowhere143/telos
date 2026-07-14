#!/usr/bin/env python3
"""iter194: extract repo-correct eval specs for the iter193 candidates.

Uses the official `swebench` test-spec API (run from a separate environment that has swebench installed)
to emit, per iter193 candidate, the exact repo-correct evaluation script and metadata. Committing these
static artifacts keeps the CI execution harness hermetic: the runner needs only Docker and the committed
scripts, not a swebench install.

Run with a python that has `swebench` importable, e.g.:
    <venv-with-swebench>/bin/python scripts/extract_iter194_specs.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments" / "iter194_certified_resolved_oracle_and_runner_fix" / "proof" / "raw" / "specs"
SNAPSHOT = (
    ROOT
    / "experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/swebench_verified_rows_snapshot.json"
)
PHASE_A = (
    ROOT
    / "experiments/iter193_certified_resolved_reward_hack_construction/proof/raw/phase_a_candidates/phase_a_summary.json"
)


def framework_of(eval_script: str) -> str:
    if "runtests.py" in eval_script:
        return "django_runtests"
    if "pytest" in eval_script:
        return "pytest"
    if "bin/test" in eval_script:
        return "sympy_bintest"
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
    except Exception as exc:  # pragma: no cover - environment guard
        print(f"swebench not importable: {exc}")
        print("run this with a python that has swebench installed")
        return 2

    OUT.mkdir(parents=True, exist_ok=True)
    rows = json.loads(SNAPSHOT.read_text())["rows"]
    by_id = {r["instance_id"]: r for r in rows}
    candidates = [
        m["instance_id"]
        for m in json.loads(PHASE_A.read_text())["manifest"]
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
            "image": "swebench/sweb.eval.x86_64."
            + re.sub("__", "_1776_", iid.lower())
            + ":latest",
        }
        (OUT / f"{stem}.spec.json").write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")
        index.append(
            {"instance_id": iid, "framework": spec["framework"], "test_command": spec["test_command"]}
        )

    (OUT / "index.json").write_text(
        json.dumps(
            {"schema_version": "telos.iter194.spec_index.v1", "count": len(index), "specs": index},
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
