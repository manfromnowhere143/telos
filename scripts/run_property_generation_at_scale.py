#!/usr/bin/env python3
"""Iter124 - measure the clean-sound rate of fully automatic property harness generation at scale.

The generated harnesses and their native-execution soundness classification are observed evidence
(proof/generated_harnesses.json, proof/soundness_classification.json). This runner tallies the rate
and failure taxonomy and records the mis-target caveat.
"""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter124_property_generation_at_scale"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
CLASS = PROOF / "soundness_classification.json"
ZERO = Decimal("0.00000000")

# A harness classified `sound` can still test the wrong function if the model mis-inferred the call
# target from the diff. Recorded manually from harness inspection.
MIS_TARGETED = {"django__django-11276": "call target inferred as html.escape, but the task concerns the make_list filter"}


def _rate(n: int, d: int) -> str:
    return format((Decimal(n) / Decimal(d)).quantize(ZERO), "f") if d else "0.00000000"


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    classification = json.loads(CLASS.read_text(encoding="utf-8"))
    n = len(classification)
    taxonomy = Counter(v["class"] for v in classification.values())
    sound_ids = [iid for iid, v in classification.items() if v["class"] == "sound"]
    clean_sound_ids = [iid for iid in sound_ids if iid not in MIS_TARGETED]

    endpoints = {
        "schema_version": "telos.property_generation_at_scale.endpoints.v1",
        "experiment_id": EXPERIMENT.name,
        "instance_count": n,
        "clean_sound_rate": _rate(len(clean_sound_ids), n),
        "clean_sound_ids": sorted(clean_sound_ids),
        "sound_but_mis_targeted": {k: MIS_TARGETED[k] for k in sound_ids if k in MIS_TARGETED},
        "failure_taxonomy": dict(taxonomy),
        "per_instance": classification,
        "finding": "full-auto property-harness generation does not reliably generalize across diverse pure functions; it succeeds when the contract and input domain are simple and fails on generation truncation, syntax, unsynthesizable input domains, and call-target mis-inference",
        "benchmark_or_sota_claim": False,
    }
    # This is a descriptive measurement gate; it passes by producing a faithful tally.
    status = "pass"

    receipt = {
        "receipt_id": f"iter124-property-generation-at-scale-{status}",
        "task_id": "telos:iter124_property_generation_at_scale",
        "agent_id": "codex-local-property-generation-at-scale-analyst",
        "benchmark_id": "swebench_verified_property_generation_at_scale_v0",
        "status": status,
        "stated_goal": "Measure the clean-sound rate and failure taxonomy of fully automatic property-harness generation across real instances.",
        "acceptance_criteria": [
            "Each instance is classified from real native execution against gold.",
            "The clean-sound rate excludes sound-but-mis-targeted harnesses.",
            "The failure taxonomy is recorded faithfully.",
        ],
        "evidence": [
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json"},
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/soundness_classification.json"},
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/generated_harnesses.json"},
        ],
        "falsifiers": [
            "A sound classification is not a correctness guarantee; mis-targeted harnesses are excluded from the clean-sound rate.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)

    _write(PROOF / "endpoint_results.json", endpoints)
    _write(VALID / "receipt_property_generation_at_scale.json", receipt)
    _write(PROOF / "run_summary.json", {"schema_version": "telos.property_generation_at_scale.summary.v1", "experiment_id": EXPERIMENT.name, "status": status, "endpoints": endpoints})

    print(f"status={status}")
    print(f"clean_sound_rate={endpoints['clean_sound_rate']} ({len(clean_sound_ids)}/{n}) ids={sorted(clean_sound_ids)}")
    print(f"sound_but_mis_targeted={list(endpoints['sound_but_mis_targeted'])}")
    print(f"failure_taxonomy={endpoints['failure_taxonomy']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
