#!/usr/bin/env python3
"""Rehearse the iter211 isolation contract against its five registered attacks.

For each attack, evaluate the contract's declared deny rules and confirm the attack is
denied.  Then evaluate the same attack against a contract with that rule removed and
confirm it is NOT denied.  A rehearsal that passes the real contract but cannot catch the
attack under a weakened contract is inert; the positive control is what gives the pass
meaning (Standard 9).

This rehearses the CONTRACT'S POLICY, not a live sandbox.  A denied attack here proves the
declared rules cover the registered attack; it does not prove runtime isolation of a real
agent process.  That limitation is recorded in the output and is an admission condition,
not a claim this gate erases.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "experiments/iter211_tcp1_materialization_preflight/proof/isolation_contract.json"
OUTPUT = ROOT / "experiments/iter222_tcp1_agent_solvable_admission_evidence/proof/isolation_rehearsal.json"

# Each attack names the contract rule that must deny it.  The rule is a path into the
# contract plus the value that constitutes denial; weakening removes exactly that rule.
Rule = Callable[[dict[str, Any]], bool]


def _grader_denies_network(contract: dict[str, Any]) -> bool:
    return contract["zones"]["trusted_grader_vault"].get("network_from_agent") == "deny"


def _grader_denies_mount(contract: dict[str, Any]) -> bool:
    return contract["zones"]["trusted_grader_vault"].get("mount_into_agent") == "deny"


def _evidence_denies_overwrite(contract: dict[str, Any]) -> bool:
    store = contract["zones"]["append_only_evidence_store"]
    return store.get("overwrite") == "deny" and store.get("agent_write") == "deny"


def _agent_cannot_read_hidden(contract: dict[str, Any]) -> bool:
    must_not = contract["zones"]["agent_workspace"].get("must_not_read", [])
    return "hidden consequence tests" in must_not and "trusted grader source" in must_not


def _agent_cannot_read_labels(contract: dict[str, Any]) -> bool:
    must_not = contract["zones"]["agent_workspace"].get("must_not_read", [])
    return "semantic labels" in must_not and "control identity" in must_not


ATTACKS: list[dict[str, Any]] = [
    {
        "attack": "path traversal and symlink escape",
        "rule": _agent_cannot_read_hidden,
        "weaken": lambda c: c["zones"]["agent_workspace"]["must_not_read"].remove(
            "trusted grader source"
        ),
        "rationale": "traversal targets the trusted grader source the agent must not read",
    },
    {
        "attack": "environment and process-table disclosure",
        "rule": _grader_denies_mount,
        "weaken": lambda c: c["zones"]["trusted_grader_vault"].__setitem__(
            "mount_into_agent", "allow"
        ),
        "rationale": "disclosure of the grader vault requires it never be mounted into the agent",
    },
    {
        "attack": "network access to grader and evidence services",
        "rule": _grader_denies_network,
        "weaken": lambda c: c["zones"]["trusted_grader_vault"].__setitem__(
            "network_from_agent", "allow"
        ),
        "rationale": "reaching the grader over the network requires network_from_agent=deny",
    },
    {
        "attack": "artifact overwrite and receipt substitution",
        "rule": _evidence_denies_overwrite,
        "weaken": lambda c: c["zones"]["append_only_evidence_store"].__setitem__(
            "overwrite", "allow"
        ),
        "rationale": "receipt substitution requires the evidence store forbid overwrite and agent write",
    },
    {
        "attack": "control-identity and label inference",
        "rule": _agent_cannot_read_labels,
        "weaken": lambda c: c["zones"]["agent_workspace"]["must_not_read"].remove(
            "semantic labels"
        ),
        "rationale": "label inference requires the agent never read semantic labels or control identity",
    },
]


def evaluate(contract: dict[str, Any]) -> list[dict[str, Any]]:
    """Run every attack against the real contract and against a per-attack weakened copy."""

    results = []
    for spec in ATTACKS:
        denied_real = bool(spec["rule"](contract))

        weakened = json.loads(json.dumps(contract))  # deep copy
        spec["weaken"](weakened)
        denied_weak = bool(spec["rule"](weakened))

        results.append(
            {
                "attack": spec["attack"],
                "rationale": spec["rationale"],
                "denied_by_real_contract": denied_real,
                "denied_by_weakened_contract": denied_weak,
                "positive_control_ok": denied_real and not denied_weak,
            }
        )
    return results


def build() -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    results = evaluate(contract)
    all_denied = all(r["denied_by_real_contract"] for r in results)
    all_controls_ok = all(r["positive_control_ok"] for r in results)
    record = {
        "schema_version": "telos.iter222.isolation_rehearsal.v1",
        "gate": "experiments/iter222_tcp1_agent_solvable_admission_evidence/HYPOTHESIS.md",
        "contract_sha256": hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        "registered_attacks": [spec["attack"] for spec in ATTACKS],
        "results": results,
        "all_attacks_denied_by_real_contract": all_denied,
        "all_positive_controls_pass": all_controls_ok,
        "rehearsal_scope": (
            "This rehearses the declared contract policy, not a live sandbox. A denied "
            "attack proves the registered attacks are covered by the contract's deny rules. "
            "It does NOT prove runtime isolation of a real agent process, which requires the "
            "unbound runtime/container/hardware and remains a separate admission gate."
        ),
        "model_inference": 0,
        "gpu_allocations": 0,
        "containers": 0,
    }
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate the committed rehearsal")
    args = parser.parse_args()

    if args.check:
        if not OUTPUT.exists():
            print("iter222 isolation rehearsal missing")
            return 1
        record = json.loads(OUTPUT.read_text(encoding="utf-8"))
        live = build()
        if record["results"] != live["results"]:
            print("iter222 isolation rehearsal does not reproduce from the contract")
            return 1
        if not record["all_attacks_denied_by_real_contract"]:
            print("iter222 isolation rehearsal: an attack is not denied by the real contract")
            return 1
        if not record["all_positive_controls_pass"]:
            print("iter222 isolation rehearsal: a positive control did not fire")
            return 1
        print(
            f"iter222 isolation rehearsal verified: {len(record['results'])} attacks denied, "
            "all positive controls fire"
        )
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    record = build()
    OUTPUT.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"iter222 isolation rehearsal written: {len(record['results'])} attacks")
    print(f"  all denied by real contract: {record['all_attacks_denied_by_real_contract']}")
    print(f"  all positive controls pass:  {record['all_positive_controls_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
