#!/usr/bin/env python3
"""Validate experiment learning records."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.ledger import LedgerValidationError, latest_next_action, load_learning_record


def main() -> int:
    root = Path.cwd()
    paths = sorted(root.glob("experiments/*/proof/learning_record.json"))
    if not paths:
        print("learning ledger: no records yet")
        return 0

    try:
        records = [load_learning_record(path, root=root) for path in paths]
        next_action = latest_next_action(records)
    except LedgerValidationError as exc:
        print(f"learning ledger invalid: {exc}")
        return 1

    print(f"learning ledger: {len(records)} records valid; next={next_action}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
