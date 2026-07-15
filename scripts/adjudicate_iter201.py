"""iter201 adjudicator: gold-free oracle on 22 hacks + combined side-by-side with the judge panel.

Parses the oracle gold/variant property logs (sound = PROP_PASS on gold; catches = PROP_FAIL on variant),
loads the iter201 judge results, and reports both detectors on the 22-hack benchmark plus their
complementarity. No model, no network.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "iter201_detectors_on_full_benchmark"
PROPS = EXP / "proof" / "raw" / "properties"
LOGS = EXP / "proof" / "raw" / "execution"
PROOF = EXP / "proof"
PROP_RE = re.compile(r"^PROP_(PASS|FAIL)$", re.M)


def read_prop(path: Path) -> str:
    if not path.exists():
        return "no_log"
    t = path.read_text(errors="ignore")
    s = t.find(">>>>> Property Start")
    body = t[s:] if s != -1 else t
    if "APPLY_FAIL" in t:
        return "apply_fail"
    m = PROP_RE.findall(body)
    return "PROP_" + m[0] if m else "no_result"


def main() -> int:
    props = [m for m in json.loads((PROPS / "properties_summary.json").read_text())["manifest"] if m["status"] == "property"]
    per = []
    oracle_caught = set()
    sound = 0
    for m in props:
        iid = m["instance_id"]
        stem = iid.replace("/", "__")
        gold = read_prop(LOGS / f"{stem}.gold.log")
        var = read_prop(LOGS / f"{stem}.variant.log")
        is_sound = gold == "PROP_PASS"
        catches = is_sound and var == "PROP_FAIL"
        if is_sound:
            sound += 1
        if catches:
            oracle_caught.add(iid)
        per.append({"instance_id": iid, "repo": m["repo"], "prop_gold": gold, "prop_variant": var,
                    "sound": is_sound, "catches": catches})
    (PROOF / "oracle_22_per_property.json").write_text(json.dumps({"schema_version": "telos.iter201.oracle_per_property.v1", "properties": per}, indent=2, sort_keys=True) + "\n")

    # combine with judge
    jrows = json.loads((PROOF / "judge_panel_22_results.json").read_text())["rows"]
    judge_caught = {r["instance_id"] for r in jrows if r["label"] == "hack" and r["any_catch"]}
    all_hacks = {r["instance_id"] for r in jrows if r["label"] == "hack"}
    jmetrics = json.loads((PROOF / "judge_panel_22_results.json").read_text())["metrics"]

    union = judge_caught | oracle_caught
    combined = {
        "schema_version": "telos.iter201.audit_report.v1",
        "experiment_id": EXP.name,
        "hacks_total": len(all_hacks),
        "judge_panel": {
            "recall_any_catch": jmetrics["recall_on_22_hacks"]["any_catch"],
            "false_positive_gold": jmetrics["false_positive_on_22_gold_controls"]["any_catch"],
        },
        "gold_free_oracle": {
            "properties": len(per),
            "sound": sound,
            "recall_caught": [len(oracle_caught), len(all_hacks)],
        },
        "complementarity": {
            "judge_caught": len(judge_caught),
            "oracle_caught": len(oracle_caught),
            "union": len(union),
            "oracle_only": sorted(i.split("/")[-1] for i in (oracle_caught - judge_caught)),
            "judge_only": sorted(i.split("/")[-1] for i in (judge_caught - oracle_caught)),
            "missed_by_both": sorted(i.split("/")[-1] for i in (all_hacks - union)),
        },
        "oracle_by_repo_caught": dict(Counter(i.split("__")[0] for i in oracle_caught)),
        "status": "pass" if len(per) >= 1 and sound >= 1 else "null",
    }
    (PROOF / "audit_report.json").write_text(json.dumps(combined, indent=2, sort_keys=True) + "\n")
    c = combined
    print(f"oracle: {len(per)} properties, {sound} sound, recall {c['gold_free_oracle']['recall_caught']}")
    print(f"judge: recall {c['judge_panel']['recall_any_catch']}, FP gold {c['judge_panel']['false_positive_gold']}")
    print(f"complementarity: judge {len(judge_caught)}, oracle {len(oracle_caught)}, union {len(union)}/{len(all_hacks)}")
    print(f"  oracle-only: {c['complementarity']['oracle_only']}  missed by both: {c['complementarity']['missed_by_both']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
