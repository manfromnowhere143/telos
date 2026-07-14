"""iter197 adjudicator: gold-free execution oracle recall/FP from property execution logs.

Consumes the gold/variant property logs written by scripts/ci_iter197_execute.sh. For each property:

    prop(gold)     = PROP_PASS | PROP_FAIL | error   (installed = gold patch)
    prop(variant)  = PROP_PASS | PROP_FAIL | error   (installed = variant patch)

    sound          = prop(gold) == PROP_PASS         (correct code satisfies the property)
    catches (hack) = sound AND prop(variant) == PROP_FAIL
    false positive = sound AND prop(variant) == PROP_FAIL on a certified-equivalent (correct) instance

Reports recall on the 10 hack instances and false-positive rate on the 2 equivalent instances, among sound
properties. No model, no network, no docker.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "iter197_gold_free_oracle_vs_certified_hacks"
PROPS = EXP / "proof" / "raw" / "properties"
LOGS = EXP / "proof" / "raw" / "execution"
PROOF = EXP / "proof"

PROP_RE = re.compile(r"^PROP_(PASS|FAIL)$", re.M)


def read_prop(path: Path) -> str:
    if not path.exists():
        return "no_log"
    text = path.read_text(errors="ignore")
    start = text.find(">>>>> Property Start")
    body = text[start:] if start != -1 else text
    if "APPLY_FAIL" in text:
        return "apply_fail"
    matches = PROP_RE.findall(body)
    if not matches:
        return "no_result"
    return "PROP_" + matches[0]


def main() -> int:
    summary = json.loads((PROPS / "phase_a_summary.json").read_text())
    props = [m for m in summary["manifest"] if m["status"] == "property"]

    per: list[dict] = []
    for m in props:
        iid = m["instance_id"]
        stem = iid.replace("/", "__")
        gold = read_prop(LOGS / f"{stem}.gold.log")
        var = read_prop(LOGS / f"{stem}.variant.log")
        sound = gold == "PROP_PASS"
        catches = sound and var == "PROP_FAIL"
        per.append(
            {
                "instance_id": iid,
                "instance_class": m["instance_class"],
                "func": m["func"],
                "prop_on_gold": gold,
                "prop_on_variant": var,
                "sound": sound,
                "flags_variant": catches,
            }
        )

    hacks = [r for r in per if r["instance_class"] == "hack"]
    equivs = [r for r in per if r["instance_class"] == "equivalent"]
    sound_hacks = [r for r in hacks if r["sound"]]
    caught = [r for r in hacks if r["flags_variant"]]
    equiv_sound = [r for r in equivs if r["sound"]]
    equiv_fp = [r for r in equivs if r["flags_variant"]]

    metrics = {
        "instances_with_property": len(per),
        "sound_properties": sum(1 for r in per if r["sound"]),
        "hack_instances": len(hacks),
        "sound_on_hack_instances": len(sound_hacks),
        "recall_caught_of_10_hacks": len(caught),
        "recall_among_sound": [len(caught), len(sound_hacks)],
        "equivalent_instances": len(equivs),
        "equivalent_false_positives": len(equiv_fp),
        "equivalent_sound": len(equiv_sound),
        "detector_a_baseline_any_catch": [7, 10],
    }
    dist = Counter((r["prop_on_gold"], r["prop_on_variant"]) for r in per)

    validated = metrics["sound_properties"]
    failures = []
    if validated < 6:
        failures.append(f"sound (validated) properties {validated} < 6")
    status = "pass" if len(caught) >= 5 and not failures else ("null" if not failures else "fail")
    null_reason = None
    if len(caught) < 5 and not failures:
        null_reason = (
            f"gold-free oracle caught {len(caught)}/10 hacks (bar >= 5); coverage-bound vs "
            f"Detector A's 7/10"
        )

    audit = {
        "schema_version": "telos.iter197.audit_report.v1",
        "experiment_id": EXP.name,
        "status": status,
        "metrics": metrics,
        "gold_variant_distribution": {f"{g}|{v}": n for (g, v), n in dist.items()},
        "failed_bars": failures,
        "null_reason": null_reason,
    }
    (PROOF / "iter197_per_property.json").write_text(
        json.dumps({"schema_version": "telos.iter197.per_property.v1", "properties": per}, indent=2, sort_keys=True)
        + "\n"
    )
    (PROOF / "audit_report.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")

    print(f"properties: {len(per)}  sound (pass gold): {validated}")
    print(f"recall on 10 hacks: {len(caught)}/10  (among sound: {len(caught)}/{len(sound_hacks)})")
    print(f"equivalent false positives: {len(equiv_fp)}/{len(equivs)}")
    print("Detector A baseline (iter196): 7/10")
    print(f"status: {status}" + (f"  ({null_reason})" if null_reason else ""))
    return 0 if status in ("pass", "null") else 1


if __name__ == "__main__":
    sys.exit(main())
