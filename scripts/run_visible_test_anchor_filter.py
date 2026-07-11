#!/usr/bin/env python3
"""Iter123 - the visible-test anchor rejects unsound proposed properties with no gold reference.

Fully reproducible in CI: pure evaluation of each property on the known-correct (input, output)
anchor pairs taken from the visible FAIL_TO_PASS test. A property is kept only if it holds on every
anchor pair.
"""

from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter123_visible_test_anchor_filter"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
ZERO = Decimal("0.00000000")

# Anchors are known-correct (input, output) pairs read off the visible FAIL_TO_PASS test.
CASES = {
    "django__django-14089": {
        "anchors": [{"inp": [1, 2, 3], "out": [3, 2, 1]}],
        "sound_property": "out == list(reversed(inp))",
        "unsound_property": "out == sorted(inp)",
    },
    "django__django-14373": {
        "anchors": [{"inp": 1, "out": "0001"}, {"inp": 999, "out": "0999"}],
        "sound_property": "len(out) == 4 and out.isdigit() and int(out) == inp",
        "unsound_property": "out == str(inp)",
    },
}


def holds_on_anchors(expr: str, anchors: list[dict]) -> bool:
    for anchor in anchors:
        try:
            ok = bool(eval(expr, {"__builtins__": {"len": len, "sorted": sorted, "int": int, "list": list, "reversed": reversed, "str": str}}, {"inp": anchor["inp"], "out": anchor["out"]}))
        except Exception:
            return False
        if not ok:
            return False
    return True


def _rate(n: int, d: int) -> str:
    return format((Decimal(n) / Decimal(d)).quantize(ZERO), "f") if d else "0.00000000"


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    rows = []
    for iid, case in CASES.items():
        sound_kept = holds_on_anchors(case["sound_property"], case["anchors"])
        unsound_kept = holds_on_anchors(case["unsound_property"], case["anchors"])
        rows.append(
            {
                "instance_id": iid,
                "anchors": case["anchors"],
                "sound_property": case["sound_property"],
                "sound_property_kept": sound_kept,
                "unsound_property": case["unsound_property"],
                "unsound_property_kept": unsound_kept,
                "unsound_property_rejected": not unsound_kept,
            }
        )

    n = len(rows)
    sound_kept = sum(1 for r in rows if r["sound_property_kept"])
    unsound_rejected = sum(1 for r in rows if r["unsound_property_rejected"])
    endpoints = {
        "schema_version": "telos.visible_test_anchor_filter.endpoints.v1",
        "experiment_id": EXPERIMENT.name,
        "instance_count": n,
        "sound_kept_rate": _rate(sound_kept, n),
        "unsound_rejected_rate": _rate(unsound_rejected, n),
        "per_instance": rows,
        "mechanism": "the visible FAIL_TO_PASS test is a known-correct (input, output) pair; a sound metamorphic property must hold on it, so violating it rejects an unsound property with no gold reference",
        "caveat": "a single anchor pair is a necessary, not sufficient, soundness condition; more anchors tighten it",
        "benchmark_or_sota_claim": False,
    }
    bars = {
        "all_sound_kept": sound_kept == n and n > 0,
        "all_unsound_rejected": unsound_rejected == n and n > 0,
    }
    status = "pass" if all(bars.values()) else "null"

    receipt = {
        "receipt_id": f"iter123-visible-test-anchor-filter-{status}",
        "task_id": "telos:iter123_visible_test_anchor_filter",
        "agent_id": "codex-local-visible-test-anchor-filter-analyst",
        "benchmark_id": "swebench_verified_visible_test_anchor_filter_v0",
        "status": status,
        "stated_goal": "Reject unsound proposed metamorphic properties using the visible test as a gold-free anchor.",
        "acceptance_criteria": [
            "Each sound property holds on the visible-test anchor (kept).",
            "Each unsound property violates the visible-test anchor (rejected).",
            "No gold reference is used.",
        ],
        "evidence": [
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json"},
        ],
        "falsifiers": [
            "Record a failure if a sound property violates the anchor.",
            "Record a miss if an unsound property holds on the anchor.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)

    _write(PROOF / "endpoint_results.json", endpoints)
    _write(VALID / "receipt_visible_test_anchor_filter.json", receipt)
    _write(PROOF / "run_summary.json", {"schema_version": "telos.visible_test_anchor_filter.summary.v1", "experiment_id": EXPERIMENT.name, "status": status, "endpoints": endpoints})

    print(f"status={status}")
    print(f"sound_kept_rate={endpoints['sound_kept_rate']} unsound_rejected_rate={endpoints['unsound_rejected_rate']}")
    for r in rows:
        print(f"  {r['instance_id']}: sound_kept={r['sound_property_kept']} unsound_rejected={r['unsound_property_rejected']}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
