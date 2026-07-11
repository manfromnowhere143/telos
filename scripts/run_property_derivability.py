#!/usr/bin/env python3
"""Iter139 - property-derivability estimate within sympy, sharpening the iter138 upper bound.

Reproducible in CI: reads the committed derivability analysis (proof/derivability.json) and reports the
domain-heuristic derivability estimate, cross-checked against the verified instances.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter139_property_derivability"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
DATA = PROOF / "derivability.json"


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    d = json.loads(DATA.read_text(encoding="utf-8"))
    verified = d["verified_instances_in_rich_domain"]
    all_verified_rich = all(verified.values())

    endpoints = {
        "schema_version": "telos.property_derivability.endpoints.v1",
        "experiment_id": EXPERIMENT.name,
        "repo": d["repo"],
        "applicable_single_function": d["applicable_single_function"],
        "property_rich_domain_count": d["property_rich_domain_count"],
        "property_derivability_estimate": d["property_derivability_estimate"],
        "method": d["method"],
        "verified_instances_in_rich_domain": verified,
        "all_verified_in_rich_domain": all_verified_rich,
        "structural_applicability_iter138": 0.81,
        "finding": "structural applicability is broad (0.81 of the dataset) but property-derivability is narrow: even in sympy, the most math-heavy repo, only ~0.10 of applicable instances live in a property-rich domain (elementary/special functions, geometry, arithmetic). Layer 3's natural domain is math-identity functions; the structural/algorithmic majority stays with Layers 1-2, which apply universally",
        "benchmark_or_sota_claim": False,
    }
    bars = {
        "verified_instances_in_rich_domain": all_verified_rich,
        "estimate_is_heuristic_not_verified_rate": "heuristic" in d["method"],
        "sharpens_upper_bound": d["property_derivability_estimate"] < 0.81,
    }
    status = "pass" if all(bars.values()) else "null"

    receipt = {
        "receipt_id": f"iter139-property-derivability-{status}",
        "task_id": "telos:iter139_property_derivability",
        "agent_id": "codex-local-property-derivability-analyst",
        "benchmark_id": "swebench_verified_property_derivability_v0",
        "status": status,
        "stated_goal": "Estimate property-derivability within sympy to sharpen the iter138 applicability upper bound.",
        "acceptance_criteria": [
            "Every verified property-sound instance falls in the property-rich domain.",
            "The estimate is presented as a domain heuristic, not a verified rate.",
            "The estimate sharpens the 0.81 structural upper bound downward.",
        ],
        "evidence": [
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json"},
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/derivability.json"},
        ],
        "falsifiers": [
            "Record it if a verified property-sound instance is not in the property-rich domain.",
            "Do not present the estimate as a verified property genuine-sound rate.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)

    learning = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT.name,
        "status": status,
        "result_path": f"experiments/{EXPERIMENT.name}/RESULT.md",
        "evidence_paths": [f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json", f"experiments/{EXPERIMENT.name}/proof/derivability.json"],
        "insight": f"structural applicability is broad (0.81) but property-derivability is narrow: even in sympy only {d['property_rich_domain_count']}/{d['applicable_single_function']} = {d['property_derivability_estimate']} of applicable instances are in a property-rich domain, and all three verified instances fall there; Layer 3's natural domain is math-identity functions while Layers 1-2 (detector, judge) apply universally - the honest three-layer division of labour",
        "next_action": "record the narrow-derivability finding in docs/PAPER.md limitations, and treat Layers 1-2 as the universal coverage with Layer 3 as the math-domain specialist",
    }

    _write(PROOF / "endpoint_results.json", endpoints)
    _write(VALID / "receipt_property_derivability.json", receipt)
    _write(PROOF / "learning_record.json", learning)
    _write(PROOF / "run_summary.json", {"schema_version": "telos.property_derivability.summary.v1", "experiment_id": EXPERIMENT.name, "status": status, "endpoints": endpoints})

    print(f"status={status}")
    print(f"sympy property-derivability estimate={d['property_derivability_estimate']} ({d['property_rich_domain_count']}/{d['applicable_single_function']})")
    print(f"all_verified_in_rich_domain={all_verified_rich}")
    print(f"structural_applicability(iter138)=0.81 -> derivability(sympy)={d['property_derivability_estimate']}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
