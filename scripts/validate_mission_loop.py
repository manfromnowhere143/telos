#!/usr/bin/env python3
"""Validate the public mission loop contract."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path.cwd()
CONTRACT = ROOT / "mission" / "loop.json"
DOC = ROOT / "docs" / "MISSION_LOOP.md"
CONTINUITY = ROOT / "CONTINUITY.md"
HANDOFF = ROOT / "HANDOFF.md"
CI = ROOT / ".github" / "workflows" / "ci.yml"

REQUIRED_PHASES = [
    "pre_register",
    "execute",
    "collect_evidence",
    "audit",
    "publish_result",
    "learn_or_stop",
    "handoff",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_gate(src: str) -> str | None:
    match = re.search(r"Current gate:\n\n- `([^`]+)`", src)
    if match:
        return match.group(1)
    match = re.search(r"Active gate: `([^`]+)`", src)
    if match:
        return match.group(1)
    return None


def main() -> int:
    failures: list[str] = []

    for path in [CONTRACT, DOC, CONTINUITY, HANDOFF, CI]:
        if not path.exists():
            failures.append(f"missing required mission-loop file: {path.relative_to(ROOT)}")

    if failures:
        for failure in failures:
            print(f"mission loop guard: {failure}")
        return 1

    contract = read_json(CONTRACT)
    doc = DOC.read_text(encoding="utf-8")
    continuity = CONTINUITY.read_text(encoding="utf-8")
    handoff = HANDOFF.read_text(encoding="utf-8")
    ci = CI.read_text(encoding="utf-8")

    if contract.get("mission_id") != "telos":
        failures.append("mission_id must be telos")
    if contract.get("standard") != "maestro-compatible-evidence-loop-v1":
        failures.append("unexpected mission loop standard")
    if "No callable Aweb/Maestro Telos capability is claimed" not in contract.get(
        "claim_boundary", ""
    ):
        failures.append("claim boundary must forbid unverified Aweb/Maestro runtime claims")

    active_gate = contract.get("active_gate")
    if active_gate != extract_gate(continuity):
        failures.append("contract active gate does not match CONTINUITY.md")
    if active_gate != extract_gate(handoff):
        failures.append("contract active gate does not match HANDOFF.md")
    if not isinstance(active_gate, str) or not (ROOT / active_gate).exists():
        failures.append("contract active gate path does not exist")

    phases = [phase.get("phase") for phase in contract.get("loop", [])]
    if phases != REQUIRED_PHASES:
        failures.append(f"mission loop phases mismatch: {phases}")

    discovery = contract.get("aweb_discovery", {})
    queries = discovery.get("queries", [])
    if len(queries) < 4:
        failures.append("Aweb discovery must record the checked catalog queries")
    if any(query.get("capability_count") != 0 for query in queries):
        failures.append("nonzero Aweb discovery count requires updating the activation claim")
    if "Register or expose a concrete Aweb/Maestro capability slug" not in discovery.get(
        "activation_gate", ""
    ):
        failures.append("Aweb activation gate is missing")

    for required in [
        "validate_mission_loop.py",
        "validate_receipts.py experiments/iter03_codeclash_smoke/proof",
        "audit_codeclash_smoke.py",
        "validate_handoff.py",
    ]:
        if required not in "\n".join(contract.get("current_validation", [])):
            failures.append(f"mission validation command missing from contract: {required}")
        if required not in ci:
            failures.append(f"mission validation command missing from CI: {required}")

    for required in [
        "../mission/loop.json",
        "Claim not allowed now: Telos is already executing through a private Aweb/Maestro runtime.",
        "Refinement is allowed only after evidence identifies a concrete gap.",
    ]:
        if required not in doc:
            failures.append(f"mission loop doc missing required text: {required}")

    if failures:
        print("MISSION LOOP GUARD FAILED:")
        for failure in failures:
            print(" -", failure)
        return 1

    print(f"mission loop guard: active gate={active_gate} phases={len(REQUIRED_PHASES)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
