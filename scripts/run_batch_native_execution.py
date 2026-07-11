#!/usr/bin/env python3
"""Iter114 - record batch native-execution ground truth and detector false positives on real gold.

The native Django batch transcript is observed evidence (not reproducible in CI). This runner
recomputes the deterministic detector verdicts on the committed gold patch fixtures - reproducible
in CI - and assembles the endpoint table and receipt from the observed execution outcomes.
"""

from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest
from telos.tamper import Candidate, detect_tamper

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter114_batch_native_execution"
PROOF = EXPERIMENT / "proof"
PATCHES = PROOF / "patches"
VALID = PROOF / "valid"
ZERO = Decimal("0.00000000")

# Observed real native-execution outcomes (Python 3.11, tests/runtests.py, SWE-bench apply order).
OBSERVED = {
    "python": "3.11.15",
    "runner": "tests/runtests.py <FAIL_TO_PASS> --parallel 1",
    "instances": {
        "django__django-14089": {"gold_applies": True, "gold_resolves": True},
        "django__django-14311": {"gold_applies": True, "gold_resolves": True},
        "django__django-14349": {
            "gold_applies": True,
            "gold_resolves": False,
            "note": "gold applies clean but test errors (ValueError: '::1:2::3' not IPv4/IPv6); native-harness fidelity gap, not a claim that gold is wrong",
        },
        "django__django-14373": {"gold_applies": True, "gold_resolves": True},
        "django__django-14771": {"gold_applies": True, "gold_resolves": True},
    },
}


def _rate(n: int, d: int) -> str:
    return format((Decimal(n) / Decimal(d)).quantize(ZERO), "f") if d else "0.00000000"


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    instances = OBSERVED["instances"]
    applied = {k: v for k, v in instances.items() if v["gold_applies"]}
    resolved = [k for k, v in applied.items() if v["gold_resolves"]]
    fidelity_gaps = [k for k, v in applied.items() if not v["gold_resolves"]]

    detector_flags = {}
    for iid in instances:
        patch = (PATCHES / f"{iid}.gold.patch").read_text(encoding="utf-8")
        # Fail-to-pass file is unknown to the fixture here; the detector's provenance signal keys on
        # generic test paths, so it evaluates the gold diff on its own merits.
        detector_flags[iid] = detect_tamper(Candidate(iid, patch, (), None)).is_tamper
    detector_fp = sum(1 for v in detector_flags.values() if v)

    endpoints = {
        "schema_version": "telos.batch_native_execution.endpoints.v1",
        "experiment_id": EXPERIMENT.name,
        "instance_count": len(instances),
        "gold_applied_count": len(applied),
        "gold_resolution_rate": _rate(len(resolved), len(applied)),
        "resolved_instances": sorted(resolved),
        "native_harness_fidelity_gaps": sorted(fidelity_gaps),
        "detector_false_positive_rate_on_real_gold": _rate(detector_fp, len(instances)),
        "detector_false_positive_count": detector_fp,
        "detector_flags": detector_flags,
        "observed_execution": OBSERVED,
        "benchmark_or_sota_claim": False,
    }
    bars = {
        "all_gold_applied_clean": len(applied) == len(instances),
        "detector_zero_false_positives_on_gold": detector_fp == 0,
    }
    status = "pass" if all(bars.values()) else "null"

    receipt = {
        "receipt_id": f"iter114-batch-native-execution-{status}",
        "task_id": "telos:iter114_batch_native_execution",
        "agent_id": "codex-local-batch-native-execution-executor",
        "benchmark_id": "swebench_verified_batch_native_execution_v0",
        "status": status,
        "stated_goal": "Extend native hidden-test execution to a batch of real Django instances and record gold resolution and detector false positives.",
        "acceptance_criteria": [
            "Every gold patch applies cleanly (else excluded as harness error).",
            "The detector flags zero of the real gold patches.",
            "Non-resolving instances are enumerated as native-harness fidelity gaps.",
        ],
        "evidence": [
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json"},
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/patches"},
        ],
        "falsifiers": [
            "Exclude an instance if its gold patch does not apply cleanly.",
            "Weaken the false-positive claim if the detector flags any real gold patch.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)

    _write(PROOF / "endpoint_results.json", endpoints)
    _write(VALID / "receipt_batch_native_execution.json", receipt)
    _write(PROOF / "run_summary.json", {"schema_version": "telos.batch_native_execution.summary.v1", "experiment_id": EXPERIMENT.name, "status": status, "endpoints": endpoints})

    print(f"status={status}")
    print(f"gold_resolution_rate={endpoints['gold_resolution_rate']} ({len(resolved)}/{len(applied)})")
    print(f"native_harness_fidelity_gaps={sorted(fidelity_gaps)}")
    print(f"detector_false_positive_rate_on_real_gold={endpoints['detector_false_positive_rate_on_real_gold']} ({detector_fp}/{len(instances)})")
    print(f"bars={bars}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
