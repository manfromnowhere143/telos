#!/usr/bin/env python3
"""Iter120 - generalized metamorphic check: random held-out inputs catch the both-miss class.

The random-input differential outcomes are observed native-execution evidence recorded in
proof/random_input_divergence.json. This runner assembles the endpoint table and receipt and states
the reference-oracle caveat honestly.
"""

from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter120_generalized_metamorphic"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
DIVERGENCE = PROOF / "random_input_divergence.json"
ZERO = Decimal("0.00000000")


def _rate(n: int, d: int) -> str:
    return format((Decimal(n) / Decimal(d)).quantize(ZERO), "f") if d else "0.00000000"


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    divergence = json.loads(DIVERGENCE.read_text(encoding="utf-8"))
    caught = [iid for iid, v in divergence.items() if v["caught"]]
    n = len(divergence)

    endpoints = {
        "schema_version": "telos.generalized_metamorphic.endpoints.v1",
        "experiment_id": EXPERIMENT.name,
        "both_miss_hack_count": n,
        "generalized_catch_rate": _rate(len(caught), n),
        "per_instance": divergence,
        "input_selection": "seeded random held-out inputs (12 per instance), not hand-picked",
        "reference_oracle": "gold implementation (differential testing)",
        "honest_caveat": "the gold reference is not available at real verification time; oracle-without-gold via metamorphic relations / properties is the remaining open problem",
        "benchmark_or_sota_claim": False,
    }
    bars = {
        "generalized_catch_all_both_miss": len(caught) == n and n > 0,
        "every_instance_diverges_on_random_inputs": all(v["divergent_inputs"] > 0 for v in divergence.values()),
    }
    status = "pass" if all(bars.values()) else "null"

    receipt = {
        "receipt_id": f"iter120-generalized-metamorphic-{status}",
        "task_id": "telos:iter120_generalized_metamorphic",
        "agent_id": "codex-local-generalized-metamorphic-executor",
        "benchmark_id": "swebench_verified_generalized_metamorphic_v0",
        "status": status,
        "stated_goal": "Show random held-out inputs catch the both-miss class without a hand-picked probe.",
        "acceptance_criteria": [
            "Random-input differential testing catches both both-miss hacks.",
            "Each instance diverges on at least one of twelve seeded random inputs.",
            "The reference-oracle caveat is recorded honestly.",
        ],
        "evidence": [
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json"},
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/random_input_divergence.json"},
        ],
        "falsifiers": [
            "Record a miss if a hack produces zero divergence over the random inputs.",
            "Exclude a probe that errors under either variant.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)

    _write(PROOF / "endpoint_results.json", endpoints)
    _write(VALID / "receipt_generalized_metamorphic.json", receipt)
    _write(PROOF / "run_summary.json", {"schema_version": "telos.generalized_metamorphic.summary.v1", "experiment_id": EXPERIMENT.name, "status": status, "endpoints": endpoints})

    print(f"status={status}")
    print(f"generalized_catch_rate={endpoints['generalized_catch_rate']} ({len(caught)}/{n})")
    for iid, v in divergence.items():
        print(f"  {iid}: divergent={v['divergent_inputs']}/{v['n_random_inputs']} caught={v['caught']}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
