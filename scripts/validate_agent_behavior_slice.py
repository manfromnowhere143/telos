#!/usr/bin/env python3
"""Validate the frozen agent-behavior slice when it exists."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.agent_behavior_slice import (
    AgentBehaviorSliceValidationError,
    load_agent_behavior_slice,
)


DEFAULT_SLICE = Path("experiments/iter04_agent_behavior_slice/proof/slice.json")


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SLICE
    if not path.exists():
        print(f"agent behavior slice: pending ({path} not present)")
        return 0

    try:
        selected = load_agent_behavior_slice(path)
    except AgentBehaviorSliceValidationError as exc:
        print(f"agent behavior slice invalid: {exc}")
        return 1

    print(
        "agent behavior slice valid: "
        f"slice={selected.slice_id} config={selected.config_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
