#!/usr/bin/env python3
"""Recompute the TCP-1 admission view after iter222's three filled gates.

Starts from the iter211 admission gates and flips exactly the three iter222 fills to pass,
each only if its evidence artifact actually verifies.  It never hard-codes a pass: a gate
flips because the evidence is present and checks, or it stays blocked.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter222_tcp1_agent_solvable_admission_evidence"
PROOF = EXPERIMENT / "proof"
SOURCE = ROOT / "experiments/iter211_tcp1_materialization_preflight/proof/admission_report.json"
OUTPUT = PROOF / "admission_view.json"

FILLED_GATES = {
    "model_license_cutoff_and_weight_binding": "model_binding.json",
    "external_transparency_timestamp": "transparency_timestamp.json",
    "hostile_isolation_rehearsal": "isolation_rehearsal.json",
}


def evidence_holds(gate: str) -> bool:
    record = json.loads((PROOF / FILLED_GATES[gate]).read_text(encoding="utf-8"))
    if gate == "model_license_cutoff_and_weight_binding":
        default = record.get("default_model", {})
        return bool(default.get("weight_sha256") and default.get("resolved_commit_sha"))
    if gate == "external_transparency_timestamp":
        return record.get("verified") is True
    if gate == "hostile_isolation_rehearsal":
        return (
            record.get("all_attacks_denied_by_real_contract") is True
            and record.get("all_positive_controls_pass") is True
        )
    return False


def build() -> dict[str, Any]:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    gates = []
    passed = 0
    blocked = 0
    for gate in source["gates"]:
        name = gate["gate"]
        status = gate["status"]
        if name in FILLED_GATES:
            status = "pass" if evidence_holds(name) else "blocked"
        gates.append({"gate": name, "status": status, "iter222_filled": name in FILLED_GATES})
        if status == "pass":
            passed += 1
        else:
            blocked += 1
    return {
        "schema_version": "telos.iter222.admission_view.v1",
        "gate": "experiments/iter222_tcp1_agent_solvable_admission_evidence/HYPOTHESIS.md",
        "predecessor_admission_report": "experiments/iter211_tcp1_materialization_preflight/proof/admission_report.json",
        "gates": gates,
        "passed_gate_count": passed,
        "blocked_gate_count": blocked,
        "iter222_filled_gates": sorted(FILLED_GATES),
        "execution_authorized": False,
        "scientific_execution_admission": "blocked",
        "remaining_blockers_require": (
            "external humans (reviewers, task authors, hidden-test authors), the real "
            "runtime/container/hardware, a paid throughput preflight, and an approved budget"
        ),
        "scientific_result_claimed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate the committed view")
    args = parser.parse_args()

    if args.check:
        if not OUTPUT.exists():
            print("iter222 admission view missing")
            return 1
        committed = json.loads(OUTPUT.read_text(encoding="utf-8"))
        if committed != build():
            print("iter222 admission view does not reproduce from the evidence")
            return 1
        if committed["passed_gate_count"] != 5 or committed["blocked_gate_count"] != 6:
            print(
                f"iter222 admission view is not 5 pass / 6 blocked: "
                f"{committed['passed_gate_count']} / {committed['blocked_gate_count']}"
            )
            return 1
        if committed["execution_authorized"] is not False:
            print("iter222 admission view must keep execution unauthorized")
            return 1
        print("iter222 admission view verified: 5 pass, 6 blocked, execution unauthorized")
        return 0

    PROOF.mkdir(parents=True, exist_ok=True)
    record = build()
    OUTPUT.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"iter222 admission view written: {record['passed_gate_count']} pass, "
        f"{record['blocked_gate_count']} blocked, execution_authorized="
        f"{record['execution_authorized']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
