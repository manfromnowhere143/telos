"""Proof receipt validation.

The research claim is not that a model is honest. The claim must be backed by a
small receipt object that a reviewer can audit without trusting the agent's prose.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
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
RECEIPT_V2_SCHEMA = "telos.proof-receipt.v2"
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


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


@dataclass(frozen=True)
class ProofReceiptV2:
    """Artifact-bound receipt; v1 remains readable as immutable legacy evidence."""

    schema_version: str
    receipt_id: str
    task_id: str
    agent_id: str
    benchmark_id: str
    status: str
    stated_goal: str
    acceptance_criteria: list[str]
    evidence: list[dict[str, Any]]
    falsifiers: list[str]
    evidence_closure_sha256: str
    receipt_sha256: str


def _stable_payload(data: dict[str, Any]) -> bytes:
    unsigned = {k: v for k, v in data.items() if k != "sha256"}
    return json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _stable_payload_without(data: dict[str, Any], excluded: set[str]) -> bytes:
    payload = {key: value for key, value in data.items() if key not in excluded}
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def receipt_digest(data: dict[str, Any]) -> str:
    """Return the canonical SHA256 for a receipt excluding its own sha256 field."""

    return hashlib.sha256(_stable_payload(data)).hexdigest()


def receipt_v2_digest(data: dict[str, Any]) -> str:
    """Return the canonical digest for a v2 receipt excluding its own digest field."""

    return hashlib.sha256(_stable_payload_without(data, {"receipt_sha256"})).hexdigest()


def _canonical_relative_path(value: object) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise ProofValidationError("artifact.path must be a non-empty string")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ProofValidationError("artifact.path must not contain control characters")
    if "\\" in value:
        raise ProofValidationError("artifact.path must use POSIX separators")
    path = PurePosixPath(value)
    if path.is_absolute() or value != path.as_posix() or any(part in {"", ".", ".."} for part in path.parts):
        raise ProofValidationError(f"artifact.path is not canonical and relative: {value}")
    return path


def _artifact_identity_anchored(root: str | Path, relative_path: object) -> tuple[int, str]:
    """Stream a regular file beneath ``root`` without following symlinks."""

    path = _canonical_relative_path(relative_path)
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise ProofValidationError("artifact verification requires O_NOFOLLOW and O_DIRECTORY")

    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    file_flags = os.O_RDONLY | os.O_NOFOLLOW
    descriptors: list[int] = []
    try:
        descriptors.append(os.open(Path(root), directory_flags))
        parent_fd = descriptors[-1]
        for index, part in enumerate(path.parts):
            is_last = index == len(path.parts) - 1
            flags = file_flags if is_last else directory_flags
            descriptors.append(os.open(part, flags, dir_fd=parent_fd))
            parent_fd = descriptors[-1]

        file_fd = descriptors[-1]
        metadata = os.fstat(file_fd)
        if not stat.S_ISREG(metadata.st_mode):
            raise ProofValidationError(f"artifact is not a regular file: {path.as_posix()}")

        byte_count = 0
        digest = hashlib.sha256()
        while True:
            chunk = os.read(file_fd, 1024 * 1024)
            if not chunk:
                break
            byte_count += len(chunk)
            digest.update(chunk)
        return byte_count, digest.hexdigest()
    except OSError as exc:
        raise ProofValidationError(f"cannot read artifact safely: {path.as_posix()}: {exc}") from exc
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def build_artifact_binding(
    root: str | Path,
    relative_path: str,
    *,
    media_type: str,
    producer: str,
) -> dict[str, Any]:
    """Build a byte-level evidence descriptor for a file below ``root``."""

    if not isinstance(media_type, str) or not media_type.strip():
        raise ProofValidationError("artifact.media_type must be non-empty")
    if not isinstance(producer, str) or not producer.strip():
        raise ProofValidationError("artifact.producer must be non-empty")
    byte_count, digest = _artifact_identity_anchored(root, relative_path)
    return {
        "path": _canonical_relative_path(relative_path).as_posix(),
        "bytes": byte_count,
        "sha256": digest,
        "media_type": media_type,
        "producer": producer,
    }


def evidence_closure_digest(evidence: list[dict[str, Any]]) -> str:
    """Digest the complete, order-independent set of v2 evidence bindings."""

    closure = [
        {
            "kind": item.get("kind"),
            "status": item.get("status"),
            "artifact": item.get("artifact"),
        }
        for item in evidence
    ]
    closure.sort(key=lambda item: (str(item["artifact"].get("path", "")), str(item["kind"])))
    return hashlib.sha256(
        json.dumps(closure, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _require_non_empty_string(data: dict[str, Any], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ProofValidationError(f"{field} must be a non-empty string")
    return value


def validate_receipt_v2(data: dict[str, Any]) -> ProofReceiptV2:
    """Validate an artifact-bound receipt without reading its referenced files."""

    required = {
        "schema_version",
        "receipt_id",
        "task_id",
        "agent_id",
        "benchmark_id",
        "status",
        "stated_goal",
        "acceptance_criteria",
        "evidence",
        "falsifiers",
        "evidence_closure_sha256",
        "receipt_sha256",
    }
    missing = sorted(required - set(data))
    unexpected = sorted(set(data) - required)
    if missing:
        raise ProofValidationError(f"missing v2 fields: {', '.join(missing)}")
    if unexpected:
        raise ProofValidationError(f"unexpected v2 fields: {', '.join(unexpected)}")
    if data["schema_version"] != RECEIPT_V2_SCHEMA:
        raise ProofValidationError(f"invalid schema_version: {data['schema_version']}")
    if data["status"] not in REQUIRED_STATUS:
        raise ProofValidationError(f"invalid status: {data['status']}")

    for field in ("receipt_id", "task_id", "agent_id", "benchmark_id", "stated_goal"):
        _require_non_empty_string(data, field)
    for field in ("acceptance_criteria", "falsifiers"):
        values = data[field]
        if not isinstance(values, list) or not values:
            raise ProofValidationError(f"{field} must be a non-empty list")
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ProofValidationError(f"{field} entries must be non-empty strings")

    evidence = data["evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise ProofValidationError("evidence must be a non-empty list")
    seen_paths: set[str] = set()
    for index, item in enumerate(evidence):
        if not isinstance(item, dict) or set(item) != {"kind", "status", "artifact"}:
            raise ProofValidationError(f"evidence[{index}] must contain kind, status, and artifact only")
        if item["kind"] not in REQUIRED_EVIDENCE_KINDS:
            raise ProofValidationError(f"evidence[{index}] has invalid kind: {item['kind']}")
        if item["status"] not in REQUIRED_STATUS:
            raise ProofValidationError(f"evidence[{index}] has invalid status: {item['status']}")
        artifact = item["artifact"]
        artifact_fields = {"path", "bytes", "sha256", "media_type", "producer"}
        if not isinstance(artifact, dict) or set(artifact) != artifact_fields:
            raise ProofValidationError(f"evidence[{index}].artifact has invalid fields")
        canonical_path = _canonical_relative_path(artifact["path"]).as_posix()
        if canonical_path in seen_paths:
            raise ProofValidationError(f"duplicate artifact path: {canonical_path}")
        seen_paths.add(canonical_path)
        byte_count = artifact["bytes"]
        if isinstance(byte_count, bool) or not isinstance(byte_count, int) or byte_count < 0:
            raise ProofValidationError(f"evidence[{index}].artifact.bytes must be a non-negative integer")
        digest = artifact["sha256"]
        if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
            raise ProofValidationError(f"evidence[{index}].artifact.sha256 is invalid")
        for field in ("media_type", "producer"):
            value = artifact[field]
            if not isinstance(value, str) or not value.strip():
                raise ProofValidationError(f"evidence[{index}].artifact.{field} must be non-empty")

    closure_digest = data["evidence_closure_sha256"]
    expected_closure = evidence_closure_digest(evidence)
    if closure_digest != expected_closure:
        raise ProofValidationError(
            f"evidence closure mismatch: expected {expected_closure}, got {closure_digest}"
        )
    expected_receipt = receipt_v2_digest(data)
    if data["receipt_sha256"] != expected_receipt:
        raise ProofValidationError(
            f"receipt_sha256 mismatch: expected {expected_receipt}, got {data['receipt_sha256']}"
        )

    return ProofReceiptV2(
        schema_version=str(data["schema_version"]),
        receipt_id=str(data["receipt_id"]),
        task_id=str(data["task_id"]),
        agent_id=str(data["agent_id"]),
        benchmark_id=str(data["benchmark_id"]),
        status=str(data["status"]),
        stated_goal=str(data["stated_goal"]),
        acceptance_criteria=list(data["acceptance_criteria"]),
        evidence=list(evidence),
        falsifiers=list(data["falsifiers"]),
        evidence_closure_sha256=str(closure_digest),
        receipt_sha256=str(data["receipt_sha256"]),
    )


def verify_receipt_v2_artifacts(data: dict[str, Any], root: str | Path) -> ProofReceiptV2:
    """Validate a v2 receipt and verify every bound artifact against local bytes."""

    receipt = validate_receipt_v2(data)
    for index, item in enumerate(receipt.evidence):
        artifact = item["artifact"]
        byte_count, digest = _artifact_identity_anchored(root, artifact["path"])
        if byte_count != artifact["bytes"]:
            raise ProofValidationError(f"evidence[{index}] artifact byte count mismatch")
        if digest != artifact["sha256"]:
            raise ProofValidationError(f"evidence[{index}] artifact sha256 mismatch")
    return receipt


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


def load_receipt_v2(path: str | Path, *, artifact_root: str | Path | None = None) -> ProofReceiptV2:
    """Load a v2 receipt, optionally verifying all artifact bytes beneath a root."""

    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ProofValidationError("receipt root must be an object")
    if artifact_root is None:
        return validate_receipt_v2(data)
    return verify_receipt_v2_artifacts(data, artifact_root)
