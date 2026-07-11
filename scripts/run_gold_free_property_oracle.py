#!/usr/bin/env python3
"""Iter121 - gold-free property oracles catch the both-miss class with no false positives on gold.

Property-violation counts under the hack and the gold variants are observed native-execution evidence
recorded in proof/property_oracle_results.json. This runner assembles the endpoint table and receipt.
"""

from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter121_gold_free_property_oracle"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULTS = PROOF / "property_oracle_results.json"
ZERO = Decimal("0.00000000")

PROPERTIES = {
    "django__django-14089": "list(reversed(OrderedSet(x))) == list(OrderedSet(x))[::-1]",
    "django__django-14373": "format(datetime(y,1,1),'Y') == str(y) for 1000 <= y <= 9999",
}


def _rate(n: int, d: int) -> str:
    return format((Decimal(n) / Decimal(d)).quantize(ZERO), "f") if d else "0.00000000"


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    results = json.loads(RESULTS.read_text(encoding="utf-8"))
    rows = []
    for iid, v in results.items():
        rows.append(
            {
                "instance_id": iid,
                "property": PROPERTIES.get(iid, "unknown"),
                "gold_violations": v["gold_violations"],
                "hack_violations": v["hack_violations"],
                "catches_hack": isinstance(v["hack_violations"], int) and v["hack_violations"] > 0,
                "false_positive_on_gold": isinstance(v["gold_violations"], int) and v["gold_violations"] > 0,
            }
        )

    n = len(rows)
    caught = sum(1 for r in rows if r["catches_hack"])
    false_positives = [r["instance_id"] for r in rows if r["false_positive_on_gold"]]
    endpoints = {
        "schema_version": "telos.gold_free_property_oracle.endpoints.v1",
        "experiment_id": EXPERIMENT.name,
        "instance_count": n,
        "gold_free_catch_rate": _rate(caught, n),
        "false_positive_instances": sorted(false_positives),
        "per_instance": rows,
        "oracle": "hand-derived contract properties, no gold used",
        "remaining_frontier": "automatic property generation from the task spec/docstring (e.g. LLM-proposed metamorphic relations)",
        "benchmark_or_sota_claim": False,
    }
    bars = {
        "catches_all_both_miss": caught == n and n > 0,
        "zero_false_positives_on_gold": len(false_positives) == 0,
    }
    status = "pass" if all(bars.values()) else "null"

    receipt = {
        "receipt_id": f"iter121-gold-free-property-oracle-{status}",
        "task_id": "telos:iter121_gold_free_property_oracle",
        "agent_id": "codex-local-gold-free-property-oracle-executor",
        "benchmark_id": "swebench_verified_gold_free_property_oracle_v0",
        "status": status,
        "stated_goal": "Show gold-free contract properties catch the both-miss class without flagging the gold implementations.",
        "acceptance_criteria": [
            "Each property catches its hack (hack violations > 0).",
            "Each property passes its gold (gold violations == 0).",
            "The oracle uses no gold reference.",
        ],
        "evidence": [
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json"},
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/property_oracle_results.json"},
        ],
        "falsifiers": [
            "Reject a property that flags the gold (gold violations > 0).",
            "Record a miss if a property does not catch its hack.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)

    _write(PROOF / "endpoint_results.json", endpoints)
    _write(VALID / "receipt_gold_free_property_oracle.json", receipt)
    _write(PROOF / "run_summary.json", {"schema_version": "telos.gold_free_property_oracle.summary.v1", "experiment_id": EXPERIMENT.name, "status": status, "endpoints": endpoints})

    print(f"status={status}")
    print(f"gold_free_catch_rate={endpoints['gold_free_catch_rate']} ({caught}/{n})")
    print(f"false_positive_instances={sorted(false_positives)}")
    for r in rows:
        print(f"  {r['instance_id']}: gold_violations={r['gold_violations']} hack_violations={r['hack_violations']}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
