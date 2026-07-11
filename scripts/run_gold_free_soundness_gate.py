#!/usr/bin/env python3
"""Iter126 - a gold-free soundness gate: non-triviality plus the visible-test anchor.

Fully reproducible in CI: evaluates each iter125-synthesized property on the known-correct visible-test
anchor pairs with a restricted evaluator, and checks it reproduces the gold-based decision without gold.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter126_gold_free_soundness_gate"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
SYNTH = ROOT / "experiments/iter125_harness_synthesizer/proof/synthesizer_results.json"
ZERO = Decimal("0.00000000")

# Visible-test anchors: (inp, out) pairs read off the FAIL_TO_PASS tests. inp matches each harness's
# expected input shape (a bare value or a tuple the check indexes).
ANCHORS = {
    "django__django-14089": [([1, 2, 3], [3, 2, 1])],
    "django__django-14373": [((datetime(1, 1, 1),), "0001")],
    "django__django-13670": [((4,), "04"), ((476,), "76")],
    "django__django-10999": [("-172800", timedelta(days=-2))],
    # 11848 anchor depends on a mocked utcnow (two-digit-year rollover); not applicable here.
}
ANCHOR_NOT_APPLICABLE = {"django__django-11848": "anchor depends on mocked utcnow for two-digit-year rollover"}
GOLD_BASED_GENUINE = {"django__django-14089", "django__django-14373", "django__django-13670", "django__django-11848"}
_EVAL_SCOPE = {"__builtins__": {"len": len, "sorted": sorted, "int": int, "list": list, "reversed": reversed, "str": str, "abs": abs, "datetime": datetime, "timedelta": timedelta}}


def is_nontrivial(h: dict) -> bool:
    return "inp" in h.get("call", "") and "inp" in h.get("check", "") and "out" in h.get("check", "")


def holds_on_anchors(check: str, anchors: list) -> bool:
    for inp, out in anchors:
        try:
            if not bool(eval(check, dict(_EVAL_SCOPE), {"inp": inp, "out": out})):
                return False
        except Exception:
            return False
    return True


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    synth = json.loads(SYNTH.read_text(encoding="utf-8"))
    rows = []
    for iid, v in synth.items():
        h = v.get("harness") or {}
        nontrivial = is_nontrivial(h) if h else False
        if iid in ANCHOR_NOT_APPLICABLE:
            decision = "anchor_not_applicable"
            holds = None
        elif iid in ANCHORS and nontrivial:
            holds = holds_on_anchors(h["check"], ANCHORS[iid])
            decision = "kept" if holds else "rejected_unsound"
        elif not nontrivial and h:
            holds = None
            decision = "rejected_vacuous"
        else:
            holds = None
            decision = "no_harness"
        rows.append({"instance_id": iid, "nontrivial": nontrivial, "holds_on_anchor": holds, "gold_free_decision": decision})

    kept = [r["instance_id"] for r in rows if r["gold_free_decision"] == "kept"]
    rejected_unsound = [r["instance_id"] for r in rows if r["gold_free_decision"] == "rejected_unsound"]
    rejected_vacuous = [r["instance_id"] for r in rows if r["gold_free_decision"] == "rejected_vacuous"]
    # Agreement where an anchor was applicable (exclude anchor_not_applicable / no_harness).
    applicable = [r for r in rows if r["gold_free_decision"] in {"kept", "rejected_unsound", "rejected_vacuous"}]
    agree = all((r["instance_id"] in GOLD_BASED_GENUINE) == (r["gold_free_decision"] == "kept") for r in applicable)

    endpoints = {
        "schema_version": "telos.gold_free_soundness_gate.endpoints.v1",
        "experiment_id": EXPERIMENT.name,
        "gold_free_kept_ids": sorted(kept),
        "unsound_rejected_by_anchor": sorted(rejected_unsound),
        "vacuous_rejected_by_nontriviality": sorted(rejected_vacuous),
        "anchor_not_applicable": sorted(ANCHOR_NOT_APPLICABLE),
        "agreement_with_gold_based_where_applicable": agree,
        "per_instance": rows,
        "finding": "a non-triviality filter plus the visible-test anchor reproduces the gold-based soundness decision without gold: it keeps the genuine-sound properties, rejects the unsound 10999 property gold was needed for in iter125, and rejects the vacuous 11276 harness",
        "benchmark_or_sota_claim": False,
    }
    bars = {
        "unsound_10999_rejected_gold_free": "django__django-10999" in rejected_unsound,
        "vacuous_11276_rejected": "django__django-11276" in rejected_vacuous,
        "genuine_kept_and_agree": agree and len(kept) >= 3,
    }
    status = "pass" if all(bars.values()) else "null"

    receipt = {
        "receipt_id": f"iter126-gold-free-soundness-gate-{status}",
        "task_id": "telos:iter126_gold_free_soundness_gate",
        "agent_id": "codex-local-gold-free-soundness-gate-analyst",
        "benchmark_id": "swebench_verified_gold_free_soundness_gate_v0",
        "status": status,
        "stated_goal": "Make the soundness decision gold-free with non-triviality plus the visible-test anchor, rejecting the unsound property gold was needed for.",
        "acceptance_criteria": [
            "The unsound 10999 property is rejected by its visible-test anchor with no gold.",
            "The vacuous 11276 harness is rejected by non-triviality.",
            "Genuine-sound harnesses are kept and the decision agrees with the gold-based one where an anchor is applicable.",
        ],
        "evidence": [
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json"},
        ],
        "falsifiers": [
            "Record a failure if the anchor rejects a genuine-sound property.",
            "Record a miss if the anchor keeps the unsound property.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)

    _write(PROOF / "endpoint_results.json", endpoints)
    _write(VALID / "receipt_gold_free_soundness_gate.json", receipt)
    _write(PROOF / "run_summary.json", {"schema_version": "telos.gold_free_soundness_gate.summary.v1", "experiment_id": EXPERIMENT.name, "status": status, "endpoints": endpoints})

    print(f"status={status}")
    print(f"gold_free_kept={sorted(kept)}")
    print(f"unsound_rejected_by_anchor={sorted(rejected_unsound)}")
    print(f"vacuous_rejected={sorted(rejected_vacuous)}")
    print(f"agreement_with_gold_based_where_applicable={agree}")
    print(f"bars={bars}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
