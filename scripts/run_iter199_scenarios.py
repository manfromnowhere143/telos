#!/usr/bin/env python3
"""iter199 Phase A (part 2): generate gold-differential witnessing scenarios for the adversary variants.

Reuses the iter195 scenario generator (its PROMPT, gen, extract_code, hunk, changed_function), driven by
the iter199 adversary candidates. For each candidate, a model sees both the gold and variant hunks (gold is
permitted at ground-truth time) and writes a version-agnostic in-container scenario that prints one
deterministic RESULT= line. Reads OPENAI_API_KEY from the environment. Ceiling: <=60 calls, <=$15.00.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "iter199_benchmark_expansion_across_repos"
CANDS = EXP / "proof" / "raw" / "candidates"
STAGE = EXP / "proof" / "raw" / "scenarios"
SNAPSHOT = (
    ROOT
    / "experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/swebench_verified_rows_snapshot.json"
)

_spec = importlib.util.spec_from_file_location(
    "scen195", ROOT / "scripts" / "run_iter195_scenario_generator.py"
)
scen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scen)

CALL_CEILING = 60
SPEND_CEILING = 15.00


def main() -> int:
    STAGE.mkdir(parents=True, exist_ok=True)
    by_id = {r["instance_id"]: r for r in json.loads(SNAPSHOT.read_text())["rows"]}
    summary = json.loads((CANDS / "adversary_summary.json").read_text())
    candidates = [m["instance_id"] for m in summary["manifest"] if m["status"] == "candidate"]

    key = scen._key()
    calls = 0
    est = 0.0
    manifest: list[dict] = []
    for iid in candidates:
        if calls >= CALL_CEILING or est >= SPEND_CEILING:
            break
        stem = iid.replace("/", "__")
        row = by_id[iid]
        gold_patch = (CANDS / f"{stem}.gold.patch").read_text()
        var_patch = (CANDS / f"{stem}.variant.patch").read_text()
        src_files = [
            line[6:]
            for line in var_patch.splitlines()
            if line.startswith("+++ b/") and "/test" not in line and "test_" not in line.split("/")[-1]
        ]
        src_file = src_files[0] if src_files else None
        func = "the changed function"
        for line in var_patch.splitlines():
            if line.startswith("@@") and ("def " in line or "class " in line):
                m = re.search(r"(?:def|class)\s+(\w+)", line)
                if m:
                    func = m.group(1)
        if not src_file:
            manifest.append({"instance_id": iid, "status": "no_src"})
            continue
        prompt = scen.PROMPT.format(
            repo=row["repo"],
            src_file=src_file,
            func=func,
            problem=(row["problem_statement"] or "")[:1000],
            gold_hunk=scen.hunk(gold_patch, src_file)[:2500],
            variant_hunk=scen.hunk(var_patch, src_file)[:2500],
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
        manifest.append(
            {
                "instance_id": iid,
                "status": "scenario",
                "repo": row["repo"],
                "src_file": src_file,
                "func": func,
                "scenario_sha256": hashlib.sha256(script.encode()).hexdigest(),
                "provider_usage": usage,
            }
        )

    out = {
        "schema_version": "telos.iter199.scenarios_summary.v1",
        "model": scen.MODEL,
        "candidates": len(candidates),
        "provider_calls": calls,
        "estimated_spend_usd": round(est, 4),
        "scenarios": sum(1 for m in manifest if m["status"] == "scenario"),
        "manifest": manifest,
    }
    (STAGE / "scenarios_summary.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(
        f"iter199 scenarios: {out['scenarios']} from {len(candidates)} candidates, {calls} calls, ~${est:.2f}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
