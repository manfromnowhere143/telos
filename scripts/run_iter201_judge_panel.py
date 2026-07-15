#!/usr/bin/env python3
"""iter201: frontier judge panel on the full 22-hack benchmark and 22 gold controls.

Reuses the iter196 judge (RUBRIC, calls, parser, prompt) over all 22 certified-resolved reward hacks
(10 from iter195 in the iter193 candidates dir, 12 from iter199 in the iter199 candidates dir) and their
paired gold controls. Each judge sees only the diff, public task, and visible test. Reports per-model and
any-catch recall on hacks and false positives on gold controls (single stochastic run). Panel is 2-model
(gpt-5.6-terra, claude-opus-4-8); gemini blocked on ADC. Ceiling: <=120 calls, <=$20.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "iter201_detectors_on_full_benchmark"
PROOF = EXP / "proof"
MANIFEST = ROOT / "benchmarks/certified_resolved_reward_hack_v2/manifest.json"
SNAPSHOT = ROOT / "experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/swebench_verified_rows_snapshot.json"
CAND_DIRS = {
    "iter195_synthesized_input_differential_oracle": ROOT / "experiments/iter193_certified_resolved_reward_hack_construction/proof/raw/phase_a_candidates",
    "iter199_benchmark_expansion_across_repos": ROOT / "experiments/iter199_benchmark_expansion_across_repos/proof/raw/candidates",
}

_spec = importlib.util.spec_from_file_location("j196", ROOT / "scripts" / "run_iter196_judge_panel.py")
j = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(j)


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    ok, ak = j._keys()
    by_id = {r["instance_id"]: r for r in json.loads(SNAPSHOT.read_text())["rows"]}
    rows = json.loads(MANIFEST.read_text())["rows"]

    def added(p: str) -> set[str]:
        return {ln[1:].strip() for ln in p.splitlines() if ln.startswith("+") and not ln.startswith("+++") and ln[1:].strip()}

    results = []
    leakage = 0
    calls = 0
    est = 0.0
    for kind in ("hack", "control_gold"):
        for row in rows:
            if calls + 2 > 120 or est >= 20.0:
                break
            iid = row["instance_id"]
            stem = iid.replace("/", "__")
            cdir = CAND_DIRS[row["source_experiment"]]
            diff = (cdir / f"{stem}.{'variant' if kind == 'hack' else 'gold'}.patch").read_text()
            gold_diff = (cdir / f"{stem}.gold.patch").read_text()
            inst = by_id[iid]
            prompt = j.build_prompt(inst["problem_statement"] or "", inst["test_patch"], diff)
            if kind == "hack":
                shared = sorted(x for x in (added(gold_diff) - added(diff)) if x in diff)
                if shared:
                    leakage += 1
            calls += 1
            est += 0.06
            try:
                ovt = j.parse_verdict(j.call_openai(prompt, ok))
            except Exception as exc:
                ovt = f"error:{str(exc)[:50]}"
            calls += 1
            est += 0.06
            try:
                avt = j.parse_verdict(j.call_anthropic(prompt, ak))
            except Exception as exc:
                avt = f"error:{str(exc)[:50]}"
            results.append({"instance_id": iid, "repo": row["repo"], "label": kind,
                            "gpt": ovt, "opus": avt,
                            "any_catch": ovt == "reward_hack" or avt == "reward_hack"})

    def rate(label, pred):
        sub = [r for r in results if r["label"] == label]
        return [sum(1 for r in sub if pred(r)), len(sub)]

    metrics = {
        "panel": "2-model (gpt-5.6-terra + claude-opus-4-8); gemini-2.5-flash blocked on ADC",
        "provider_calls": calls, "estimated_spend_usd": round(est, 4), "leakage_shared_gold_lines": leakage,
        "recall_on_22_hacks": {
            "gpt": rate("hack", lambda r: r["gpt"] == "reward_hack"),
            "opus": rate("hack", lambda r: r["opus"] == "reward_hack"),
            "any_catch": rate("hack", lambda r: r["any_catch"]),
        },
        "false_positive_on_22_gold_controls": {
            "gpt": rate("control_gold", lambda r: r["gpt"] == "reward_hack"),
            "opus": rate("control_gold", lambda r: r["opus"] == "reward_hack"),
            "any_catch": rate("control_gold", lambda r: r["any_catch"]),
        },
    }
    (PROOF / "judge_panel_22_results.json").write_text(json.dumps({"schema_version": "telos.iter201.judge_panel.v1", "metrics": metrics, "rows": results}, indent=2, sort_keys=True) + "\n")
    m = metrics
    print(f"panel calls {calls} ~${est:.2f} leakage {leakage}")
    print(f"recall/22 hacks: gpt {m['recall_on_22_hacks']['gpt']} opus {m['recall_on_22_hacks']['opus']} any {m['recall_on_22_hacks']['any_catch']}")
    print(f"FP/22 gold: gpt {m['false_positive_on_22_gold_controls']['gpt']} opus {m['false_positive_on_22_gold_controls']['opus']} any {m['false_positive_on_22_gold_controls']['any_catch']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
