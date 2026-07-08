#!/usr/bin/env python3
"""Validate the frozen public task slice when it exists."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.public_slice import PublicSliceValidationError, load_public_slice


DEFAULT_SLICE = Path("experiments/iter02_public_task_slice/proof/slice.json")


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SLICE
    if not path.exists():
        print(f"public slice: pending ({path} not present)")
        return 0

    try:
        public_slice = load_public_slice(path)
    except PublicSliceValidationError as exc:
        print(f"public slice invalid: {exc}")
        return 1

    print(
        "public slice valid: "
        f"slice={public_slice.slice_id} task={public_slice.task_id}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
