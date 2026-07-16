"""Learning ledger validation.

Telos should get better by retaining what each experiment teaches. The ledger is
deliberately small: result, evidence paths, insight, and next action.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from pathlib import PurePosixPath
import re
from typing import Any


class LedgerValidationError(ValueError):
    """Raised when a learning record is malformed."""


VALID_STATUSES = {"pass", "fail", "null", "blocked", "pending"}
LEARNING_RECORD_PATTERN = "experiments/*/proof/learning_record*.json"


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


def discover_learning_record_paths(root: str | Path) -> list[Path]:
    """Return canonical records and additive adjudication records in stable order."""

    base = Path(root)
    paths = sorted(base.glob(LEARNING_RECORD_PATTERN))
    invalid = [path for path in paths if path.is_symlink() or not path.is_file()]
    if invalid:
        rendered = ", ".join(path.as_posix() for path in invalid)
        raise LedgerValidationError(f"learning record is not a regular file: {rendered}")
    return paths


def select_active_learning_record(
    records: list[LearningRecord], active_gate: str
) -> LearningRecord:
    """Bind the current action to the mission contract's exact active gate."""

    if not isinstance(active_gate, str) or not active_gate.strip():
        raise LedgerValidationError("mission active_gate must be a non-empty string")
    gate = PurePosixPath(active_gate)
    if gate.is_absolute() or ".." in gate.parts or gate.as_posix() != active_gate:
        raise LedgerValidationError("mission active_gate must be normalized and relative")
    matches = [record for record in records if record.result_path == active_gate]
    if len(matches) != 1:
        raise LedgerValidationError(
            "active_gate must have exactly one learning record; "
            f"found {len(matches)} for {active_gate}"
        )
    record = matches[0]
    expected_experiment_id = gate.parent.name
    if record.experiment_id != expected_experiment_id:
        raise LedgerValidationError(
            "active learning record experiment_id does not match active_gate parent"
        )
    if record.status != "pending":
        raise LedgerValidationError("active learning record status must be pending")
    return record


def _experiment_sort_key(record: LearningRecord) -> tuple[int, int | str, str]:
    match = re.match(r"^iter(\d+)(?:_|$)", record.experiment_id)
    if match:
        return (1, int(match.group(1)), record.experiment_id)
    return (0, record.experiment_id, record.experiment_id)


def latest_next_action(records: list[LearningRecord]) -> str:
    """Return the newest non-pending next action by experiment id."""

    completed = [record for record in records if record.status != "pending"]
    if not completed:
        raise LedgerValidationError("no completed learning records")
    return sorted(completed, key=_experiment_sort_key)[-1].next_action
