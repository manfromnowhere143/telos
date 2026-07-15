#!/usr/bin/env python3
"""iter201: gold-free property generation for all 22 benchmark hacks (Detector B extension).

Reuses the iter197 property generator (gold-free: public task + visible test only) over the full 22-hack
benchmark. Reads OPENAI_API_KEY. Ceiling: <=40 calls, <=$10.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "iter201_detectors_on_full_benchmark"
STAGE = EXP / "proof" / "raw" / "properties"
MANIFEST = ROOT / "benchmarks/certified_resolved_reward_hack_v2/manifest.json"
SNAPSHOT = ROOT / "experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/swebench_verified_rows_snapshot.json"
CAND_DIRS = {
    "iter195_synthesized_input_differential_oracle": ROOT / "experiments/iter193_certified_resolved_reward_hack_construction/proof/raw/phase_a_candidates",
    "iter199_benchmark_expansion_across_repos": ROOT / "experiments/iter199_benchmark_expansion_across_repos/proof/raw/candidates",
}
_spec = importlib.util.spec_from_file_location("p197", ROOT / "scripts" / "run_iter197_property_generator.py")
p = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(p)


def main() -> int:
    STAGE.mkdir(parents=True, exist_ok=True)
    by_id = {r["instance_id"]: r for r in json.loads(SNAPSHOT.read_text())["rows"]}
    rows = json.loads(MANIFEST.read_text())["rows"]
    key = p._key()
    calls = 0
    est = 0.0
    manifest = []
    for row in rows:
        if calls >= 40 or est >= 10.0:
            break
        iid = row["instance_id"]
        stem = iid.replace("/", "__")
        inst = by_id[iid]
        variant = (CAND_DIRS[row["source_experiment"]] / f"{stem}.variant.patch").read_text()
        src = [ln[6:] for ln in variant.splitlines() if ln.startswith("+++ b/") and "/test" not in ln and "test_" not in ln.split("/")[-1]]
        src_file = src[0] if src else None
        func = "the changed function"
        for ln in variant.splitlines():
            if ln.startswith("@@") and ("def " in ln or "class " in ln):
                mm = re.search(r"(?:def|class)\s+(\w+)", ln)
                if mm:
                    func = mm.group(1)
        if not src_file:
            manifest.append({"instance_id": iid, "status": "no_src"})
            continue
        prompt = p.PROMPT.format(repo=row["repo"], src_file=src_file, func=func,
                                 problem=(inst["problem_statement"] or "")[:1200], visible_test=inst["test_patch"][:2500])
        calls += 1
        est += p.EST_PER_CALL
        try:
            raw, usage = p.gen(prompt, key)
        except Exception as exc:
            manifest.append({"instance_id": iid, "status": "provider_error", "detail": str(exc)[:120]})
            continue
        script = p.extract_code(raw)
        if not script.strip() or ("PROP_PASS" not in script and "PROP_FAIL" not in script):
            manifest.append({"instance_id": iid, "status": "no_property"})
            continue
        (STAGE / f"{stem}.property.py").write_text(script + "\n")
        manifest.append({"instance_id": iid, "status": "property", "repo": row["repo"], "func": func,
                         "source_experiment": row["source_experiment"],
                         "property_sha256": hashlib.sha256(script.encode()).hexdigest(), "provider_usage": usage})
    out = {"schema_version": "telos.iter201.properties.v1", "model": p.MODEL, "instances": len(rows),
           "provider_calls": calls, "estimated_spend_usd": round(est, 4),
           "properties": sum(1 for m in manifest if m["status"] == "property"), "manifest": manifest}
    (STAGE / "properties_summary.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(f"iter201 properties: {out['properties']} from {len(rows)} hacks, {calls} calls, ~${est:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
