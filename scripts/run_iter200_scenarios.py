#!/usr/bin/env python3
"""iter200 Phase A (part 2): gold-vs-model witnessing scenarios for the neutral-solve patches.

Reuses the iter195 scenario generator, comparing the gold patch against the MODEL patch. Only patches that
differ from gold need a scenario (identical ones cannot diverge). Gold is used at ground-truth time only.
Reads OPENAI_API_KEY. Ceiling: <=50 calls, <=$15.00.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "iter200_natural_certified_yet_wrong_rate"
SOLS = EXP / "proof" / "raw" / "solutions"
STAGE = EXP / "proof" / "raw" / "scenarios"
SNAPSHOT = (
    ROOT
    / "experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/swebench_verified_rows_snapshot.json"
)
_spec = importlib.util.spec_from_file_location("scen195", ROOT / "scripts" / "run_iter195_scenario_generator.py")
scen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scen)

CALL_CEILING = 50
SPEND_CEILING = 15.00


def main() -> int:
    STAGE.mkdir(parents=True, exist_ok=True)
    by_id = {r["instance_id"]: r for r in json.loads(SNAPSHOT.read_text())["rows"]}
    summary = json.loads((SOLS / "solve_summary.json").read_text())
    # only patches that differ from gold can diverge behaviorally
    diffs = [m["instance_id"] for m in summary["manifest"] if m["status"] == "solution" and not m["identical_to_gold"]]

    key = scen._key()
    calls = 0
    est = 0.0
    manifest: list[dict] = []
    for iid in diffs:
        if calls >= CALL_CEILING or est >= SPEND_CEILING:
            break
        stem = iid.replace("/", "__")
        row = by_id[iid]
        gold_patch = (SOLS / f"{stem}.gold.patch").read_text()
        model_patch = (SOLS / f"{stem}.model.patch").read_text()
        src_files = [
            line[6:] for line in model_patch.splitlines()
            if line.startswith("+++ b/") and "/test" not in line and "test_" not in line.split("/")[-1]
        ]
        src_file = src_files[0] if src_files else None
        func = "the changed function"
        for line in model_patch.splitlines():
            if line.startswith("@@") and ("def " in line or "class " in line):
                mm = re.search(r"(?:def|class)\s+(\w+)", line)
                if mm:
                    func = mm.group(1)
        if not src_file:
            manifest.append({"instance_id": iid, "status": "no_src"})
            continue
        prompt = scen.PROMPT.format(
            repo=row["repo"], src_file=src_file, func=func,
            problem=(row["problem_statement"] or "")[:1000],
            gold_hunk=scen.hunk(gold_patch, src_file)[:2500],
            variant_hunk=scen.hunk(model_patch, src_file)[:2500],
        )
        calls += 1
        est += scen.EST_USD_PER_CALL
        try:
            raw, usage = scen.gen(prompt, key)
        except Exception as exc:
            manifest.append({"instance_id": iid, "status": "provider_error", "detail": str(exc)[:160]})
            continue
        script = scen.extract_code(raw)
        if not script.strip() or "RESULT=" not in script:
            manifest.append({"instance_id": iid, "status": "no_scenario"})
            continue
        (STAGE / f"{stem}.scenario.py").write_text(script + "\n")
        manifest.append({"instance_id": iid, "status": "scenario", "repo": row["repo"], "func": func,
                         "scenario_sha256": hashlib.sha256(script.encode()).hexdigest(), "provider_usage": usage})

    out = {"schema_version": "telos.iter200.scenarios_summary.v1", "model": scen.MODEL,
           "differing_solutions": len(diffs), "provider_calls": calls, "estimated_spend_usd": round(est, 4),
           "scenarios": sum(1 for m in manifest if m["status"] == "scenario"), "manifest": manifest}
    (STAGE / "scenarios_summary.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(f"iter200 scenarios: {out['scenarios']} from {len(diffs)} differing solutions, {calls} calls, ~${est:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
