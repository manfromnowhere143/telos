#!/usr/bin/env python3
"""Validate handoff consistency."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys


ROOT = Path.cwd()
HANDOFF = ROOT / "HANDOFF.md"
CONTINUITY = ROOT / "CONTINUITY.md"


def main() -> int:
    failures: list[str] = []
    handoff = HANDOFF.read_text(encoding="utf-8")
    continuity = CONTINUITY.read_text(encoding="utf-8")

    handoff_match = re.search(r"Active gate: `([^`]+)`", handoff)
    continuity_match = re.search(r"Current gate:\n\n- `([^`]+)`", continuity)
    if not handoff_match:
        failures.append("HANDOFF.md does not name an active gate")
    if not continuity_match:
        failures.append("CONTINUITY.md does not name a current gate")

    if handoff_match and continuity_match:
        handoff_gate = handoff_match.group(1)
        continuity_gate = continuity_match.group(1)
        if handoff_gate != continuity_gate:
            failures.append(
                f"active gate mismatch: HANDOFF={handoff_gate} CONTINUITY={continuity_gate}"
            )
        if not (ROOT / handoff_gate).exists():
            failures.append(f"active gate file does not exist: {handoff_gate}")

    status = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    if "Working tree:\n\n```text\nclean\n```" not in handoff and not status:
        failures.append("HANDOFF.md does not record a clean working tree")

    if failures:
        print("handoff guard failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("handoff guard: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
