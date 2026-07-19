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
        historical_contract = json.loads(
            (root / "mission/loop.json").read_text(encoding="utf-8")
        )
        if not isinstance(historical_contract, dict):
            raise LedgerValidationError(
                "historical mission loop root must be an object"
            )
        historical_pending = select_active_learning_record(
            records,
            historical_contract.get("active_gate"),
        )
        current = json.loads(
            (root / "mission/current.json").read_text(encoding="utf-8")
        )
        if not isinstance(current, dict) or not isinstance(
            current.get("active_gate"),
            str,
        ):
            raise LedgerValidationError(
                "mission/current.json must identify a string active_gate"
            )
    except (OSError, json.JSONDecodeError, LedgerValidationError) as exc:
        print(f"learning ledger invalid: {exc}")
        return 1

    print(
        f"learning ledger: {len(records)} records valid; "
        f"historical_pending_at_freeze={historical_pending.experiment_id}; "
        f"historical_status={historical_pending.status}; "
        "operational_authority=mission/current.json; "
        f"current_gate={current['active_gate']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
