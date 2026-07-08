"""Learning ledger validation.

Telos should get better by retaining what each experiment teaches. The ledger is
deliberately small: result, evidence paths, insight, and next action.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


class LedgerValidationError(ValueError):
    """Raised when a learning record is malformed."""


VALID_STATUSES = {"pass", "null", "blocked", "pending"}


@dataclass(frozen=True)
class LearningRecord:
    """One experiment-level learning record."""

    experiment_id: str
    status: str
    result_path: str
    evidence_paths: list[str]
    insight: str
    next_action: str


def validate_learning_record(data: dict[str, Any], root: Path | None = None) -> LearningRecord:
    """Validate one learning record."""

    required = {
        "experiment_id",
        "status",
        "result_path",
        "evidence_paths",
        "insight",
        "next_action",
    }
    missing = sorted(required - set(data))
    if missing:
        raise LedgerValidationError(f"missing fields: {', '.join(missing)}")

    status = data["status"]
    if status not in VALID_STATUSES:
        raise LedgerValidationError(f"invalid status: {status}")

    evidence_paths = data["evidence_paths"]
    if not isinstance(evidence_paths, list) or not evidence_paths:
        raise LedgerValidationError("evidence_paths must be a non-empty list")

    for field in ["experiment_id", "result_path", "insight", "next_action"]:
        if not isinstance(data[field], str) or not data[field].strip():
            raise LedgerValidationError(f"{field} must be a non-empty string")

    for idx, path in enumerate(evidence_paths):
        if not isinstance(path, str) or not path.strip():
            raise LedgerValidationError(f"evidence_paths[{idx}] must be a non-empty string")

    if root is not None:
        for path in [data["result_path"], *evidence_paths]:
            if not (root / path).exists():
                raise LedgerValidationError(f"linked artifact does not exist: {path}")

    return LearningRecord(
        experiment_id=data["experiment_id"],
        status=status,
        result_path=data["result_path"],
        evidence_paths=list(evidence_paths),
        insight=data["insight"],
        next_action=data["next_action"],
    )


def load_learning_record(path: str | Path, root: Path | None = None) -> LearningRecord:
    """Load and validate one learning record."""

    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise LedgerValidationError("learning record root must be an object")
    return validate_learning_record(data, root=root)


def latest_next_action(records: list[LearningRecord]) -> str:
    """Return the newest non-pending next action by experiment id."""

    completed = [record for record in records if record.status != "pending"]
    if not completed:
        raise LedgerValidationError("no completed learning records")
    return sorted(completed, key=lambda record: record.experiment_id)[-1].next_action
