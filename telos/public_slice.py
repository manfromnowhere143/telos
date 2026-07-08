"""Public task-slice validation."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Any


class PublicSliceValidationError(ValueError):
    """Raised when a public task slice is malformed or incomplete."""


REQUIRED_EVIDENCE_KINDS = {"artifact", "diff_scope", "test"}
HEX40 = re.compile(r"^[a-f0-9]{40}$")
HEX64 = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class PublicSlice:
    """Frozen first-run slice for a Telos experiment."""

    slice_id: str
    target_family: str
    selected_candidate: str
    primary_source: str
    task_id: str
    first_run_command: str


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise PublicSliceValidationError(f"{key} must be an object")
    return value


def _require_nonempty_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PublicSliceValidationError(f"{key} must be a non-empty string")
    return value


def _require_url(data: dict[str, Any], key: str) -> str:
    value = _require_nonempty_string(data, key)
    if not value.startswith(("https://", "http://")):
        raise PublicSliceValidationError(f"{key} must be an HTTP(S) URL")
    return value


def _validate_source(source: dict[str, Any], idx: int) -> None:
    _require_nonempty_string(source, "name")
    _require_url(source, "url")
    _require_nonempty_string(source, "license_note")
    commit_sha = source.get("commit_sha")
    if commit_sha is not None and (
        not isinstance(commit_sha, str) or not HEX40.match(commit_sha)
    ):
        raise PublicSliceValidationError(
            f"sources[{idx}].commit_sha must be a 40-character git SHA when present"
        )
    content_sha = source.get("content_sha256")
    if content_sha is not None and (
        not isinstance(content_sha, str) or not HEX64.match(content_sha)
    ):
        raise PublicSliceValidationError(
            f"sources[{idx}].content_sha256 must be a 64-character sha256 when present"
        )


def validate_public_slice(data: dict[str, Any]) -> PublicSlice:
    """Validate a public task-slice decision artifact."""

    for key in [
        "schema_version",
        "slice_id",
        "status",
        "target_family",
        "selected_candidate",
        "sources",
        "task",
        "expected_artifacts",
        "first_run_command",
        "first_run_falsifier",
        "spend",
    ]:
        if key not in data:
            raise PublicSliceValidationError(f"missing field: {key}")

    if data["schema_version"] != "telos.public_slice.v1":
        raise PublicSliceValidationError("schema_version must be telos.public_slice.v1")
    if data["status"] != "selected":
        raise PublicSliceValidationError("status must be selected")

    slice_id = _require_nonempty_string(data, "slice_id")
    target_family = _require_nonempty_string(data, "target_family")
    selected_candidate = _require_nonempty_string(data, "selected_candidate")
    first_run_command = _require_nonempty_string(data, "first_run_command")
    _require_nonempty_string(data, "first_run_falsifier")

    sources = data["sources"]
    if not isinstance(sources, list) or not sources:
        raise PublicSliceValidationError("sources must be a non-empty list")
    for idx, source in enumerate(sources):
        if not isinstance(source, dict):
            raise PublicSliceValidationError(f"sources[{idx}] must be an object")
        _validate_source(source, idx)
    primary_source = str(sources[0]["name"])

    task = _require_mapping(data, "task")
    task_id = _require_nonempty_string(task, "task_id")
    _require_nonempty_string(task, "kind")
    _require_nonempty_string(task, "public_config")
    _require_nonempty_string(task, "receipt_substrate")
    if not HEX40.match(_require_nonempty_string(task, "primary_commit_sha")):
        raise PublicSliceValidationError("task.primary_commit_sha must be a 40-character git SHA")
    supporting_task = task.get("supporting_task")
    if supporting_task is not None:
        if not isinstance(supporting_task, dict):
            raise PublicSliceValidationError("task.supporting_task must be an object when present")
        _require_nonempty_string(supporting_task, "instance_id")
        _require_nonempty_string(supporting_task, "repo")
        for key in ["base_commit", "environment_setup_commit"]:
            if not HEX40.match(_require_nonempty_string(supporting_task, key)):
                raise PublicSliceValidationError(
                    f"task.supporting_task.{key} must be a 40-character git SHA"
                )
        for key in ["patch_sha256", "test_patch_sha256", "problem_statement_sha256"]:
            if not HEX64.match(_require_nonempty_string(supporting_task, key)):
                raise PublicSliceValidationError(
                    f"task.supporting_task.{key} must be a 64-character sha256"
                )
        fail_to_pass = supporting_task.get("fail_to_pass")
        if not isinstance(fail_to_pass, list) or not fail_to_pass:
            raise PublicSliceValidationError(
                "task.supporting_task.fail_to_pass must be a non-empty list"
            )

    expected_artifacts = data["expected_artifacts"]
    if not isinstance(expected_artifacts, list) or not expected_artifacts:
        raise PublicSliceValidationError("expected_artifacts must be a non-empty list")
    kinds = set()
    for idx, artifact in enumerate(expected_artifacts):
        if not isinstance(artifact, dict):
            raise PublicSliceValidationError(f"expected_artifacts[{idx}] must be an object")
        kind = _require_nonempty_string(artifact, "kind")
        _require_nonempty_string(artifact, "name")
        _require_nonempty_string(artifact, "purpose")
        kinds.add(kind)
    missing_kinds = REQUIRED_EVIDENCE_KINDS - kinds
    if missing_kinds:
        raise PublicSliceValidationError(
            "expected_artifacts missing evidence kinds: " + ", ".join(sorted(missing_kinds))
        )

    spend = _require_mapping(data, "spend")
    if spend.get("api_calls") is not False:
        raise PublicSliceValidationError("spend.api_calls must be false")
    if spend.get("cloud") is not False:
        raise PublicSliceValidationError("spend.cloud must be false")
    if spend.get("gpu") is not False:
        raise PublicSliceValidationError("spend.gpu must be false")
    if spend.get("local_only") is not True:
        raise PublicSliceValidationError("spend.local_only must be true")

    return PublicSlice(
        slice_id=slice_id,
        target_family=target_family,
        selected_candidate=selected_candidate,
        primary_source=primary_source,
        task_id=task_id,
        first_run_command=first_run_command,
    )


def load_public_slice(path: str | Path) -> PublicSlice:
    """Load and validate a public task-slice decision artifact."""

    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise PublicSliceValidationError("public slice root must be an object")
    return validate_public_slice(data)
