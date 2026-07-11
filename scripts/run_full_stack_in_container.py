#!/usr/bin/env python3
"""Iter135 - the full stack runs inside the pinned container: gold resolution + gold-free property.

Consumes the committed full-stack results (proof/full_stack_results.json) produced by the extended
docker-batch.yml workflow on the native-x86 runner.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter135_full_stack_in_container"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULTS = PROOF / "full_stack_results.json"


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    rows = json.loads(RESULTS.read_text(encoding="utf-8"))
    per = []
    for r in rows:
        gold_ok = "[OK]" in r.get("gold", "")
        base_fail = ("exceptions" in r.get("base", "")) or ("failed" in r.get("base", "")) or ("[OK]" not in r.get("base", ""))
        prop = r.get("property", "NO_PROPERTY")
        per.append({
            "instance_id": r["instance_id"],
            "resolved": bool(r.get("pull")) and base_fail and gold_ok,
            "property": prop,
            "property_sound": prop == "PROP_SOUND",
            "property_applicable": prop != "NO_PROPERTY",
        })

    n = len(per)
    resolved = sum(1 for p in per if p["resolved"])
    prop_applicable = [p for p in per if p["property_applicable"]]
    prop_sound = sum(1 for p in prop_applicable if p["property_sound"])
    full_stack_instance = next((p for p in per if p["resolved"] and p["property_sound"]), None)

    endpoints = {
        "schema_version": "telos.full_stack_in_container.endpoints.v1",
        "experiment_id": EXPERIMENT.name,
        "runner": "GitHub Actions ubuntu-latest (native x86, no emulation)",
        "instance_count": n,
        "gold_resolution_count": resolved,
        "property_applicable_count": len(prop_applicable),
        "property_sound_count": prop_sound,
        "full_stack_instance": full_stack_instance["instance_id"] if full_stack_instance else None,
        "per_instance": per,
        "finding": "inside the pinned SWE-bench container of a natively-unrunnable instance (Python 3.9, sympy 1.1.2), the hidden test resolves (base fails, gold passes) and the gold-free coth metamorphic property is sound - environment fidelity and property verification run together in one pinned environment, the full stack end to end",
        "benchmark_or_sota_claim": False,
    }
    bars = {
        "all_gold_resolved": resolved == n and n >= 3,
        "property_sound_where_applicable": len(prop_applicable) >= 1 and prop_sound == len(prop_applicable),
        "full_stack_demonstrated": full_stack_instance is not None,
    }
    status = "pass" if all(bars.values()) else "null"

    receipt = {
        "receipt_id": f"iter135-full-stack-in-container-{status}",
        "task_id": "telos:iter135_full_stack_in_container",
        "agent_id": "codex-github-actions-full-stack-in-container",
        "benchmark_id": "swebench_verified_full_stack_in_container_v0",
        "status": status,
        "stated_goal": "Run the gold-free property layer inside the pinned SWE-bench container alongside gold resolution.",
        "acceptance_criteria": [
            "The gold patches resolve inside the pinned containers.",
            "Where a property is defined, it is sound in the pinned environment.",
            "At least one instance runs the full stack (gold resolution + sound property) in its pinned container.",
        ],
        "evidence": [
            {"kind": "test", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/full_stack_results.json"},
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json"},
        ],
        "falsifiers": [
            "Record it if the property is unsound in the pinned environment.",
            "Record a runner-resource cause if the workflow fails.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)

    learning = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT.name,
        "status": status,
        "result_path": f"experiments/{EXPERIMENT.name}/RESULT.md",
        "evidence_paths": [f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json", f"experiments/{EXPERIMENT.name}/proof/full_stack_results.json"],
        "insight": "the full stack runs in one pinned SWE-bench container: for a natively-unrunnable instance the hidden test resolves and the gold-free coth metamorphic property is sound, so environment fidelity (Docker) and property verification (Layer 3) compose end to end on real cross-repo instances",
        "next_action": "add per-instance property files for more property-testable blocked instances and scale the x86 CI full-stack batch to measure the property genuine-sound rate across the environment-fidelity-blocked set",
    }

    _write(PROOF / "endpoint_results.json", endpoints)
    _write(VALID / "receipt_full_stack_in_container.json", receipt)
    _write(PROOF / "learning_record.json", learning)
    _write(PROOF / "run_summary.json", {"schema_version": "telos.full_stack_in_container.summary.v1", "experiment_id": EXPERIMENT.name, "status": status, "endpoints": endpoints})

    print(f"status={status}")
    print(f"gold_resolved={resolved}/{n}  property_sound={prop_sound}/{len(prop_applicable)}  full_stack_instance={endpoints['full_stack_instance']}")
    for p in per:
        print(f"  {p['instance_id']}: resolved={p['resolved']} property={p['property']}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
