#!/usr/bin/env python3
"""Validate experiment learning records."""

from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.ledger import (
    LedgerValidationError,
    discover_learning_record_paths,
    latest_next_action,
    load_learning_record,
    select_active_learning_record,
)


def main() -> int:
    root = Path.cwd()
    paths = discover_learning_record_paths(root)
    if not paths:
        print("learning ledger: no records yet")
        return 0

    try:
        records = [load_learning_record(path, root=root) for path in paths]
        latest_next_action(records)
        contract = json.loads(
            (root / "mission/loop.json").read_text(encoding="utf-8")
        )
        if not isinstance(contract, dict):
            raise LedgerValidationError("mission loop root must be an object")
        active = select_active_learning_record(records, contract.get("active_gate"))
    except (OSError, json.JSONDecodeError, LedgerValidationError) as exc:
        print(f"learning ledger invalid: {exc}")
        return 1

    print(
        f"learning ledger: {len(records)} records valid; "
        f"active={active.experiment_id}; status={active.status}; "
        f"active_next={active.next_action}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
