"""Proof receipt validation.

The research claim is not that a model is honest. The claim must be backed by a
small receipt object that a reviewer can audit without trusting the agent's prose.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any


class ProofValidationError(ValueError):
    """Raised when a proof receipt is malformed or internally inconsistent."""


REQUIRED_STATUS = {"pass", "fail", "blocked", "not_applicable"}
REQUIRED_EVIDENCE_KINDS = {
    "test",
    "typecheck",
    "build",
    "diff_scope",
    "live_check",
    "artifact",
    "adversarial_review",
}


@dataclass(frozen=True)
class ProofReceipt:
    """Canonical receipt emitted by a Telos run."""

    receipt_id: str
    task_id: str
    agent_id: str
    benchmark_id: str
    status: str
    stated_goal: str
    acceptance_criteria: list[str]
    evidence: list[dict[str, Any]]
    falsifiers: list[str]
    sha256: str


def _stable_payload(data: dict[str, Any]) -> bytes:
    unsigned = {k: v for k, v in data.items() if k != "sha256"}
    return json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")


def receipt_digest(data: dict[str, Any]) -> str:
    """Return the canonical SHA256 for a receipt excluding its own sha256 field."""

    return hashlib.sha256(_stable_payload(data)).hexdigest()


def validate_receipt(data: dict[str, Any]) -> ProofReceipt:
    """Validate and normalize one proof receipt."""

    required = {
        "receipt_id",
        "task_id",
        "agent_id",
        "benchmark_id",
        "status",
        "stated_goal",
        "acceptance_criteria",
        "evidence",
        "falsifiers",
        "sha256",
    }
    missing = sorted(required - set(data))
    if missing:
        raise ProofValidationError(f"missing fields: {', '.join(missing)}")

    if data["status"] not in REQUIRED_STATUS:
        raise ProofValidationError(f"invalid status: {data['status']}")

    if not isinstance(data["acceptance_criteria"], list) or not data["acceptance_criteria"]:
        raise ProofValidationError("acceptance_criteria must be a non-empty list")

    if not isinstance(data["falsifiers"], list) or not data["falsifiers"]:
        raise ProofValidationError("falsifiers must be a non-empty list")

    evidence = data["evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise ProofValidationError("evidence must be a non-empty list")

    for idx, item in enumerate(evidence):
        if not isinstance(item, dict):
            raise ProofValidationError(f"evidence[{idx}] must be an object")
        kind = item.get("kind")
        status = item.get("status")
        artifact = item.get("artifact")
        if kind not in REQUIRED_EVIDENCE_KINDS:
            raise ProofValidationError(f"evidence[{idx}] has invalid kind: {kind}")
        if status not in REQUIRED_STATUS:
            raise ProofValidationError(f"evidence[{idx}] has invalid status: {status}")
        if artifact is not None and not isinstance(artifact, str):
            raise ProofValidationError(f"evidence[{idx}].artifact must be a string when present")

    expected = receipt_digest(data)
    if data["sha256"] != expected:
        raise ProofValidationError(f"sha256 mismatch: expected {expected}, got {data['sha256']}")

    return ProofReceipt(
        receipt_id=str(data["receipt_id"]),
        task_id=str(data["task_id"]),
        agent_id=str(data["agent_id"]),
        benchmark_id=str(data["benchmark_id"]),
        status=str(data["status"]),
        stated_goal=str(data["stated_goal"]),
        acceptance_criteria=list(data["acceptance_criteria"]),
        evidence=list(evidence),
        falsifiers=list(data["falsifiers"]),
        sha256=str(data["sha256"]),
    )


def load_receipt(path: str | Path) -> ProofReceipt:
    """Load and validate a receipt JSON file."""

    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ProofValidationError("receipt root must be an object")
    return validate_receipt(data)
