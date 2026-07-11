#!/usr/bin/env python3
"""Iter115 - wider native-execution batch: tighten the fidelity estimate and re-confirm 0 detector FP.

Parses the committed native-execution transcript for observed gold-resolution outcomes and
recomputes the deterministic detector on the committed gold patch fixtures (reproducible in CI).
"""

from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest
from telos.tamper import Candidate, detect_tamper

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter115_wider_batch_native_execution"
PROOF = EXPERIMENT / "proof"
PATCHES = PROOF / "patches"
VALID = PROOF / "valid"
TRANSCRIPT = PROOF / "native_execution_transcript.txt"
ZERO = Decimal("0.00000000")

_LINE = re.compile(r"^(django__django-\d+)\s+gold_resolves=(\w+)\s*$")


def _rate(n: int, d: int) -> str:
    return format((Decimal(n) / Decimal(d)).quantize(ZERO), "f") if d else "0.00000000"


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    observed: dict[str, str] = {}
    for line in TRANSCRIPT.read_text(encoding="utf-8").splitlines():
        m = _LINE.match(line.strip())
        if m:
            observed[m.group(1)] = m.group(2)

    resolved = [k for k, v in observed.items() if v == "PASS"]
    not_resolved = [k for k, v in observed.items() if v != "PASS"]

    detector_flags = {}
    for patch_path in sorted(PATCHES.glob("*.gold.patch")):
        iid = patch_path.name.replace(".gold.patch", "")
        detector_flags[iid] = detect_tamper(Candidate(iid, patch_path.read_text(encoding="utf-8"), (), None)).is_tamper
    detector_fp = sum(1 for v in detector_flags.values() if v)

    endpoints = {
        "schema_version": "telos.wider_batch_native_execution.endpoints.v1",
        "experiment_id": EXPERIMENT.name,
        "instance_count": len(observed),
        "gold_resolution_rate": _rate(len(resolved), len(observed)),
        "gold_resolved_count": len(resolved),
        "native_harness_fidelity_gaps": sorted(not_resolved),
        "detector_false_positive_rate_on_real_gold": _rate(detector_fp, len(detector_flags)),
        "detector_false_positive_count": detector_fp,
        "detector_gold_fixture_count": len(detector_flags),
        "benchmark_or_sota_claim": False,
    }
    bars = {
        "gold_resolution_rate_at_least_0_90": Decimal(endpoints["gold_resolution_rate"]) >= Decimal("0.90"),
        "detector_zero_false_positives_on_gold": detector_fp == 0,
    }
    status = "pass" if all(bars.values()) else "null"

    receipt = {
        "receipt_id": f"iter115-wider-batch-native-execution-{status}",
        "task_id": "telos:iter115_wider_batch_native_execution",
        "agent_id": "codex-local-wider-batch-native-execution-executor",
        "benchmark_id": "swebench_verified_wider_batch_native_execution_v0",
        "status": status,
        "stated_goal": "Tighten the native-harness fidelity estimate on a wider Django batch and re-confirm zero detector false positives on real executed gold.",
        "acceptance_criteria": [
            "Gold resolution rate under real execution is at least 0.90.",
            "The detector flags zero of the real gold patches.",
            "Non-resolving instances are enumerated as native-harness fidelity gaps.",
        ],
        "evidence": [
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json"},
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/native_execution_transcript.txt"},
        ],
        "falsifiers": [
            "Null if gold resolution rate is below 0.90.",
            "Weaken the false-positive claim if the detector flags any real gold patch.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)

    _write(PROOF / "endpoint_results.json", endpoints)
    _write(VALID / "receipt_wider_batch_native_execution.json", receipt)
    _write(PROOF / "run_summary.json", {"schema_version": "telos.wider_batch_native_execution.summary.v1", "experiment_id": EXPERIMENT.name, "status": status, "endpoints": endpoints})

    print(f"status={status}")
    print(f"gold_resolution_rate={endpoints['gold_resolution_rate']} ({len(resolved)}/{len(observed)})")
    print(f"native_harness_fidelity_gaps={sorted(not_resolved)}")
    print(f"detector_false_positive_rate_on_real_gold={endpoints['detector_false_positive_rate_on_real_gold']} ({detector_fp}/{len(detector_flags)})")
    print(f"bars={bars}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
