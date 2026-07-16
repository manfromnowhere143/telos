#!/usr/bin/env python3
"""Build and verify the iter203 eight-shard execution evidence chain.

This collector is deliberately versioned independently from iter202.  It binds
both runtime generations and the iter203 safety-recovery bridge, accepts only
eight successful artifacts from one GitHub run attempt, and exposes a pure
verified-log snapshot for downstream adjudication.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import stat
import subprocess
import sys
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import collect_iter202_execution as fs  # noqa: E402


EXPERIMENT_ID = "iter203_iter202_safety_recovery"
EXP = ROOT / "experiments" / EXPERIMENT_ID
UPSTREAM = ROOT / "experiments/iter202_natural_rate_scaled"
BRIDGE = EXP / "proof/raw/safety_recovery_bridge"
DEFAULT_SPEC_INDEX = EXP / "proof/raw/specs/index.json"
DEFAULT_RUNTIME_MANIFEST = EXP / "proof/raw/runtime_manifest.json"
DEFAULT_EXECUTION_DIR = EXP / "proof/raw/execution"
AGGREGATE_RECEIPT_NAME = "_telos_iter203_execution_complete.receipt.json"

SHARD_COUNT = 8
VALID_PATCH_COUNT = 50
CANONICAL_REPOSITORY = "manfromnowhere143/telos"
CANONICAL_WORKFLOW_REF = (
    f"{CANONICAL_REPOSITORY}/.github/workflows/iter203-execute.yml@refs/heads/master"
)
PRIMARY_CI_AUTHORIZATION_ENV = "TELOS_ITER203_PRIMARY_CI_AUTHORIZATION"
PRIMARY_CI_AUTHORIZATION_SCHEMA = "telos.iter203.primary_ci_authorization.v1"
PRIMARY_CI_WORKFLOW_PATH = ".github/workflows/ci.yml"
PRIMARY_CI_REQUIRED_CHECKS = ("verify py3.11", "verify py3.12")
UPSTREAM_SOURCE_COMMIT = "8b8809ed6b358d16eb08fe38f0f2edf4a284af0e"
UPSTREAM_RUNTIME_SHA256 = "dd935a6f5873940fca5768891bb74a6cc635ef86bb65cdf493dd2a8ffe043868"
SPEC_INDEX_SCHEMA = "telos.iter200.spec_index.v2"
RUNTIME_MANIFEST_SCHEMA = "telos.iter203.execution_runtime.v1"
SHARD_SCHEMA = "telos.iter203.execution_shard_receipt.v1"
AGGREGATE_SCHEMA = "telos.iter203.execution_aggregate_receipt.v1"
ASSIGNMENT_METHOD = "zero_based_ordered_valid_patch_spec_ordinal_modulo_8"

INSTANCE_RE = re.compile(r"[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
GITHUB_SHA_RE = re.compile(r"[0-9a-f]{40}")
POSITIVE_INTEGER_RE = re.compile(r"[1-9][0-9]*")
REPOSITORY_RE = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
ARTIFACT_RE = re.compile(
    r"iter203-execution-run-([1-9][0-9]*)-attempt-([1-9][0-9]*)-"
    r"shard-([0-7])-of-8"
)

SOURCE_KEYS = {
    "image_lock_sha256",
    "input_bridge_sha256",
    "projected_scenarios_summary_sha256",
    "projected_solve_summary_sha256",
    "runtime_manifest_sha256",
    "safe_scenario_index_sha256",
    "scenario_disposition_sha256",
    "solution_projection_index_sha256",
    "spec_index_sha256",
    "upstream_inventory_sha256",
    "upstream_runtime_manifest_sha256",
    "upstream_solve_summary_sha256",
}
GITHUB_KEYS = {"repository", "run_attempt", "run_id", "sha", "workflow_ref"}
AUTHORIZATION_KEYS = {
    "approved_commit_sha",
    "primary_ci_event",
    "primary_ci_head_branch",
    "primary_ci_run_attempt",
    "primary_ci_run_id",
    "primary_ci_workflow_path",
    "required_checks",
    "schema_version",
}
PRIMARY_CI_CHECK_KEYS = {
    "app_slug",
    "conclusion",
    "details_url",
    "id",
    "name",
    "status",
}
FILE_KEYS = {"bytes", "name", "sha256"}
AGGREGATE_LOG_KEYS = FILE_KEYS | {"shard_index"}
ASSIGNMENT_KEYS = {
    "method",
    "ordered_instance_ids",
    "shard_count",
    "shard_index",
}
AGGREGATE_ASSIGNMENT_KEYS = {"method", "ordered_instance_ids", "shard_count"}
SHARD_TOP_KEYS = {
    "assignment",
    "authorization",
    "experiment_id",
    "github",
    "logs",
    "schema_version",
    "source",
}
AGGREGATE_TOP_KEYS = SHARD_TOP_KEYS | {"shards"}
SHARD_RECORD_KEYS = {
    "artifact_name",
    "ordered_instance_ids",
    "receipt_bytes",
    "receipt_name",
    "receipt_sha256",
    "shard_index",
}


class ExecutionCollectionError(ValueError):
    """Iter203 evidence is incomplete, mixed, mutable, or source-divergent."""


def canonical_json_bytes(value: dict[str, Any]) -> bytes:
    try:
        return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    except (TypeError, ValueError) as exc:
        raise ExecutionCollectionError(f"cannot render canonical strict JSON: {exc}") from exc


def _read(path: Path) -> bytes:
    try:
        return fs._read_regular_file(path)
    except fs.ExecutionCollectionError as exc:
        raise ExecutionCollectionError(str(exc)) from exc


def _load(path: Path, *, canonical: bool = False) -> tuple[dict[str, Any], bytes]:
    raw = _read(path)
    duplicates: list[str] = []

    def object_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                duplicates.append(key)
            value[key] = item
        return value

    def nonfinite(value: str) -> Any:
        raise ExecutionCollectionError(f"non-finite JSON constant is forbidden: {value}")

    try:
        value = json.loads(raw, object_pairs_hook=object_hook, parse_constant=nonfinite)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExecutionCollectionError(f"cannot parse strict JSON {path}: {exc}") from exc
    if duplicates:
        raise ExecutionCollectionError(f"duplicate JSON key in {path}: {duplicates[0]!r}")
    if not isinstance(value, dict):
        raise ExecutionCollectionError(f"JSON evidence must be an object: {path}")
    if canonical and raw != canonical_json_bytes(value):
        raise ExecutionCollectionError(f"JSON evidence is not canonical: {path}")
    return value, raw


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise ExecutionCollectionError(
            f"{label} keys differ: expected {sorted(expected)}, got {sorted(value)}"
        )


def _plain_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _manifest_source(document: dict[str, Any], raw: bytes) -> dict[str, str]:
    if document.get("schema_version") != RUNTIME_MANIFEST_SCHEMA:
        raise ExecutionCollectionError("iter203 runtime manifest schema is invalid")
    if document.get("experiment_id") != EXPERIMENT_ID:
        raise ExecutionCollectionError("iter203 runtime manifest experiment identity is invalid")
    if document.get("upstream_source_commit") != UPSTREAM_SOURCE_COMMIT:
        raise ExecutionCollectionError("upstream iter202 source-commit binding differs")
    if document.get("upstream_runtime_manifest_sha256") != UPSTREAM_RUNTIME_SHA256:
        raise ExecutionCollectionError("upstream iter202 runtime binding differs")
    _validate_runtime_file_closures(document)
    source = document.get("source_bindings")
    if not isinstance(source, dict):
        raise ExecutionCollectionError("runtime manifest source bindings are malformed")
    _exact_keys(source, SOURCE_KEYS - {"runtime_manifest_sha256"}, "runtime source bindings")
    if any(
        not isinstance(value, str) or SHA256_RE.fullmatch(value) is None
        for value in source.values()
    ):
        raise ExecutionCollectionError("runtime source binding contains an invalid SHA-256")
    if source["upstream_runtime_manifest_sha256"] != UPSTREAM_RUNTIME_SHA256:
        raise ExecutionCollectionError("runtime source map does not bind frozen iter202 v1")
    return {**source, "runtime_manifest_sha256": _sha256(raw)}


def _validated_file_records(value: Any, *, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ExecutionCollectionError(f"{label} records are not a list")
    records: list[dict[str, Any]] = []
    paths: list[str] = []
    for ordinal, record in enumerate(value):
        if not isinstance(record, dict):
            raise ExecutionCollectionError(f"{label} record {ordinal} is not an object")
        _exact_keys(record, {"bytes", "path", "role", "sha256"}, f"{label} record {ordinal}")
        path_text = record["path"]
        if not isinstance(path_text, str):
            raise ExecutionCollectionError(f"{label} record {ordinal} path is invalid")
        pure = PurePosixPath(path_text)
        if pure.is_absolute() or ".." in pure.parts or pure.as_posix() != path_text:
            raise ExecutionCollectionError(f"{label} record {ordinal} path is unsafe")
        if (
            not isinstance(record["role"], str)
            or not record["role"]
            or not _plain_int(record["bytes"])
            or record["bytes"] < 0
            or not isinstance(record["sha256"], str)
            or SHA256_RE.fullmatch(record["sha256"]) is None
        ):
            raise ExecutionCollectionError(f"{label} record {ordinal} metadata is invalid")
        payload = _read(ROOT / Path(*pure.parts))
        if len(payload) != record["bytes"] or _sha256(payload) != record["sha256"]:
            raise ExecutionCollectionError(
                f"{label} file differs from runtime manifest: {path_text}"
            )
        paths.append(path_text)
        records.append(record)
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise ExecutionCollectionError(f"{label} paths are not unique and path-sorted")
    return records


def _records_closure(records: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for record in records:
        digest.update(record["path"].encode())
        digest.update(b"\0")
        digest.update(record["role"].encode())
        digest.update(b"\0")
        digest.update(record["sha256"].encode())
        digest.update(b"\0")
        digest.update(str(record["bytes"]).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def _validate_runtime_file_closures(document: dict[str, Any]) -> None:
    records = _validated_file_records(document.get("files"), label="runtime closure")
    if document.get("file_count") != len(records):
        raise ExecutionCollectionError("runtime manifest file count differs")
    closure = document.get("closure")
    if (
        not isinstance(closure, dict)
        or closure.get("algorithm")
        != "SHA-256(path NUL role NUL file_sha256 NUL byte_count LF), path-sorted"
        or closure.get("sha256") != _records_closure(records)
    ):
        raise ExecutionCollectionError("runtime file closure digest differs")
    bridge = document.get("input_bridge")
    if not isinstance(bridge, dict):
        raise ExecutionCollectionError("runtime input bridge is malformed")
    bridge_records = _validated_file_records(bridge.get("files"), label="input-bridge closure")
    if (
        bridge.get("algorithm")
        != "SHA-256(path NUL role NUL file_sha256 NUL byte_count LF), path-sorted"
        or bridge.get("file_count") != len(bridge_records)
        or bridge.get("sha256") != _records_closure(bridge_records)
    ):
        raise ExecutionCollectionError("input-bridge file closure digest differs")
    runtime_by_path = {record["path"]: record for record in records}
    if any(runtime_by_path.get(record["path"]) != record for record in bridge_records):
        raise ExecutionCollectionError(
            "input-bridge record is not identically contained in runtime closure"
        )


def _validate_spec_index(path: Path) -> tuple[list[str], str]:
    document, raw = _load(path, canonical=True)
    if document.get("schema_version") != SPEC_INDEX_SCHEMA:
        raise ExecutionCollectionError("iter203 certification spec index schema is invalid")
    rows = document.get("specs")
    if (
        not isinstance(rows, list)
        or document.get("count") != VALID_PATCH_COUNT
        or len(rows) != VALID_PATCH_COUNT
    ):
        raise ExecutionCollectionError("iter203 spec index must contain exactly 50 valid patches")
    ids: list[str] = []
    for ordinal, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ExecutionCollectionError(f"iter203 spec row {ordinal} is not an object")
        instance_id = row.get("instance_id")
        if not isinstance(instance_id, str) or INSTANCE_RE.fullmatch(instance_id) is None:
            raise ExecutionCollectionError(f"iter203 spec row {ordinal} has an unsafe instance id")
        ids.append(instance_id)
    if len(ids) != len(set(ids)):
        raise ExecutionCollectionError("iter203 spec index contains duplicate instance ids")
    return ids, _sha256(raw)


def _validate_current_sources(
    spec_index: Path, runtime_manifest: Path
) -> tuple[list[str], dict[str, str]]:
    ordered_ids, spec_sha = _validate_spec_index(spec_index)
    manifest, manifest_raw = _load(runtime_manifest, canonical=True)
    source = _manifest_source(manifest, manifest_raw)
    if source["spec_index_sha256"] != spec_sha:
        raise ExecutionCollectionError("runtime manifest/spec-index hash binding differs")
    current_paths = {
        "image_lock_sha256": UPSTREAM / "proof/raw/image_lock.json",
        "projected_scenarios_summary_sha256": EXP / "proof/raw/scenarios/scenarios_summary.json",
        "projected_solve_summary_sha256": EXP / "proof/raw/solutions/solve_summary.json",
        "safe_scenario_index_sha256": BRIDGE / "safe_scenario_index.json",
        "scenario_disposition_sha256": BRIDGE / "scenario_disposition.json",
        "solution_projection_index_sha256": BRIDGE / "solution_projection_index.json",
        "upstream_inventory_sha256": BRIDGE / "upstream_inventory.json",
        "upstream_runtime_manifest_sha256": UPSTREAM / "proof/raw/runtime_manifest.json",
        "upstream_solve_summary_sha256": UPSTREAM / "proof/raw/solutions/solve_summary.json",
    }
    for key, path in current_paths.items():
        if _sha256(_read(path)) != source[key]:
            raise ExecutionCollectionError(f"current source hash differs: {key}")
    bridge = manifest.get("input_bridge")
    if not isinstance(bridge, dict) or bridge.get("sha256") != source["input_bridge_sha256"]:
        raise ExecutionCollectionError("runtime manifest input-bridge closure binding differs")
    solution_summary, _ = _load(current_paths["projected_solve_summary_sha256"], canonical=True)
    solution_rows = solution_summary.get("manifest")
    if not isinstance(solution_rows, list):
        raise ExecutionCollectionError("upstream solution manifest is malformed")
    solution_ids = [
        row.get("instance_id")
        for row in solution_rows
        if isinstance(row, dict) and row.get("status") == "solution"
    ]
    if (
        solution_summary.get("targets") != 53
        or solution_summary.get("solutions") != VALID_PATCH_COUNT
        or solution_ids != ordered_ids
    ):
        raise ExecutionCollectionError(
            "iter203 spec order does not exactly cover all 50 upstream valid patches"
        )
    if (
        max(
            sum(1 for ordinal in range(len(ordered_ids)) if ordinal % SHARD_COUNT == index)
            for index in range(SHARD_COUNT)
        )
        > 7
    ):
        raise ExecutionCollectionError("iter203 shard plan exceeds seven rows per shard")
    return ordered_ids, source


def _github_from_environment(*, required: bool) -> dict[str, str] | None:
    mapping = {
        "repository": "GITHUB_REPOSITORY",
        "run_attempt": "GITHUB_RUN_ATTEMPT",
        "run_id": "GITHUB_RUN_ID",
        "sha": "GITHUB_SHA",
        "workflow_ref": "GITHUB_WORKFLOW_REF",
    }
    values = {key: os.environ.get(name, "") for key, name in mapping.items()}
    if not any(values.values()):
        if required:
            raise ExecutionCollectionError("complete GitHub run provenance is required")
        return None
    if not all(values.values()):
        raise ExecutionCollectionError("partial GitHub run provenance is forbidden")
    return _validate_github(values, "GitHub environment")


def _validate_github(value: Any, label: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ExecutionCollectionError(f"{label} is not an object")
    _exact_keys(value, GITHUB_KEYS, label)
    if not all(isinstance(value[key], str) for key in GITHUB_KEYS):
        raise ExecutionCollectionError(f"{label} values are not strings")
    if (
        POSITIVE_INTEGER_RE.fullmatch(value["run_id"]) is None
        or POSITIVE_INTEGER_RE.fullmatch(value["run_attempt"]) is None
    ):
        raise ExecutionCollectionError(f"{label} run identity is invalid")
    if (
        GITHUB_SHA_RE.fullmatch(value["sha"]) is None
        or REPOSITORY_RE.fullmatch(value["repository"]) is None
    ):
        raise ExecutionCollectionError(f"{label} repository or commit identity is invalid")
    if (
        value["repository"] != CANONICAL_REPOSITORY
        or value["workflow_ref"] != CANONICAL_WORKFLOW_REF
    ):
        raise ExecutionCollectionError(
            f"{label} is not the canonical repository/master workflow identity"
        )
    return value


def _authorization_transport(value: dict[str, Any]) -> str:
    """Encode the sole workflow-safe transport for primary-CI authorization."""

    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return base64.urlsafe_b64encode(payload).decode("ascii")


def _decode_authorization_transport(value: str) -> dict[str, Any]:
    duplicates: list[str] = []

    def object_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in pairs:
            if key in result:
                duplicates.append(key)
            result[key] = item
        return result

    try:
        payload = base64.b64decode(value, altchars=b"-_", validate=True)
        document = json.loads(
            payload,
            object_pairs_hook=object_hook,
            parse_constant=lambda constant: (_ for _ in ()).throw(
                ExecutionCollectionError(
                    f"non-finite primary-CI authorization constant: {constant}"
                )
            ),
        )
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExecutionCollectionError(
            f"primary-CI authorization transport is invalid: {exc}"
        ) from exc
    if duplicates:
        raise ExecutionCollectionError(
            f"primary-CI authorization contains duplicate key: {duplicates[0]!r}"
        )
    if not isinstance(document, dict):
        raise ExecutionCollectionError("primary-CI authorization is not an object")
    if _authorization_transport(document) != value:
        raise ExecutionCollectionError("primary-CI authorization transport is not canonical")
    return document


def _validate_authorization(
    value: Any, github: dict[str, str], label: str
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ExecutionCollectionError(f"{label} is not an object")
    _exact_keys(value, AUTHORIZATION_KEYS, label)
    run_id = value.get("primary_ci_run_id")
    run_attempt = value.get("primary_ci_run_attempt")
    if (
        value.get("schema_version") != PRIMARY_CI_AUTHORIZATION_SCHEMA
        or value.get("approved_commit_sha") != github["sha"]
        or value.get("primary_ci_event") != "push"
        or value.get("primary_ci_head_branch") != "master"
        or value.get("primary_ci_workflow_path") != PRIMARY_CI_WORKFLOW_PATH
        or not _plain_int(run_id)
        or run_id < 1
        or not _plain_int(run_attempt)
        or run_attempt < 1
    ):
        raise ExecutionCollectionError(f"{label} identity is invalid")
    checks = value.get("required_checks")
    if not isinstance(checks, list) or len(checks) != len(PRIMARY_CI_REQUIRED_CHECKS):
        raise ExecutionCollectionError(f"{label} required checks are incomplete")
    for ordinal, (check, expected_name) in enumerate(
        zip(checks, PRIMARY_CI_REQUIRED_CHECKS, strict=True)
    ):
        if not isinstance(check, dict):
            raise ExecutionCollectionError(f"{label} check {ordinal} is not an object")
        _exact_keys(check, PRIMARY_CI_CHECK_KEYS, f"{label} check {ordinal}")
        check_id = check.get("id")
        expected_url = (
            f"https://github.com/{CANONICAL_REPOSITORY}/actions/runs/{run_id}/job/{check_id}"
        )
        if (
            check.get("name") != expected_name
            or check.get("status") != "completed"
            or check.get("conclusion") != "success"
            or check.get("app_slug") != "github-actions"
            or not _plain_int(check_id)
            or check_id < 1
            or check.get("details_url") != expected_url
        ):
            raise ExecutionCollectionError(f"{label} check {ordinal} is not complete/success")
    return value


def _authorization_from_environment(
    *, github: dict[str, str], required: bool
) -> dict[str, Any] | None:
    encoded = os.environ.get(PRIMARY_CI_AUTHORIZATION_ENV, "")
    if not encoded:
        if required:
            raise ExecutionCollectionError("primary-CI authorization is required")
        return None
    return _validate_authorization(
        _decode_authorization_transport(encoded), github, "primary-CI authorization environment"
    )


def _require_current_checkout_sha(github: dict[str, str]) -> None:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ExecutionCollectionError(f"cannot bind receipt to checked-out commit: {exc}") from exc
    if completed.stdout.strip() != github["sha"]:
        raise ExecutionCollectionError("checked-out commit differs from GITHUB_SHA")


def shard_receipt_name(index: int) -> str:
    return f"_telos_iter203_shard_{index}_of_8.receipt.json"


def artifact_name(github: dict[str, str], index: int) -> str:
    return (
        f"iter203-execution-run-{github['run_id']}-attempt-{github['run_attempt']}-"
        f"shard-{index}-of-8"
    )


def _expected_log_names(ids: Iterable[str]) -> list[str]:
    return [f"{instance_id}.{kind}.log" for instance_id in ids for kind in ("gold", "variant")]


def _file_record(path: Path) -> dict[str, Any]:
    payload = _read(path)
    return {"bytes": len(payload), "name": path.name, "sha256": _sha256(payload)}


def _assigned(ordered_ids: list[str], index: int) -> list[str]:
    return [
        instance_id
        for ordinal, instance_id in enumerate(ordered_ids)
        if ordinal % SHARD_COUNT == index
    ]


def _expected_shard_document(
    *,
    execution_dir: Path,
    ordered_ids: list[str],
    source: dict[str, str],
    github: dict[str, str],
    authorization: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    assigned = _assigned(ordered_ids, index)
    return {
        "assignment": {
            "method": ASSIGNMENT_METHOD,
            "ordered_instance_ids": assigned,
            "shard_count": SHARD_COUNT,
            "shard_index": index,
        },
        "authorization": authorization,
        "experiment_id": EXPERIMENT_ID,
        "github": github,
        "logs": [_file_record(execution_dir / name) for name in _expected_log_names(assigned)],
        "schema_version": SHARD_SCHEMA,
        "source": source,
    }


def _regular_entries(path: Path, label: str) -> list[Path]:
    try:
        entries = fs._require_regular_directory(path, label)
        fs._require_regular_file_entries(entries, label)
        return entries
    except fs.ExecutionCollectionError as exc:
        raise ExecutionCollectionError(str(exc)) from exc


def _materialize_once(path: Path, payload: bytes) -> None:
    try:
        fs._materialize_once(path, payload)
    except fs.ExecutionCollectionError as exc:
        raise ExecutionCollectionError(str(exc)) from exc


def publish_log(source: Path, destination: Path) -> None:
    """Atomically publish one log and refuse any pre-existing destination."""

    if destination.exists() or destination.is_symlink():
        raise ExecutionCollectionError(f"refusing to overwrite execution log: {destination}")
    payload = _read(source)
    _materialize_once(destination, payload)
    source.unlink()


def create_shard_receipt(
    *,
    execution_dir: Path,
    spec_index: Path,
    runtime_manifest: Path,
    shard_index: int,
    shard_count: int,
) -> Path:
    if shard_count != SHARD_COUNT or shard_index not in range(SHARD_COUNT):
        raise ExecutionCollectionError("iter203 shard receipt requires index 0..7 and count 8")
    github = _github_from_environment(required=True)
    assert github is not None
    _require_current_checkout_sha(github)
    authorization = _authorization_from_environment(github=github, required=True)
    assert authorization is not None
    ordered_ids, source = _validate_current_sources(spec_index, runtime_manifest)
    receipt = execution_dir / shard_receipt_name(shard_index)
    expected = set(_expected_log_names(_assigned(ordered_ids, shard_index)))
    actual = {entry.name for entry in _regular_entries(execution_dir, "shard execution directory")}
    allowed = expected | ({receipt.name} if receipt.name in actual else set())
    if actual != allowed:
        raise ExecutionCollectionError(
            "shard execution directory contains missing or extra evidence"
        )
    document = _expected_shard_document(
        execution_dir=execution_dir,
        ordered_ids=ordered_ids,
        source=source,
        github=github,
        authorization=authorization,
        index=shard_index,
    )
    _materialize_once(receipt, canonical_json_bytes(document))
    return receipt


def _validate_file_record(record: Any, *, aggregate: bool, label: str) -> None:
    if not isinstance(record, dict):
        raise ExecutionCollectionError(f"{label} is not an object")
    _exact_keys(record, AGGREGATE_LOG_KEYS if aggregate else FILE_KEYS, label)
    if (
        not isinstance(record["name"], str)
        or "/" in record["name"]
        or "\\" in record["name"]
        or not _plain_int(record["bytes"])
        or record["bytes"] < 0
        or not isinstance(record["sha256"], str)
        or SHA256_RE.fullmatch(record["sha256"]) is None
    ):
        raise ExecutionCollectionError(f"{label} file record is invalid")
    if aggregate and (
        not _plain_int(record["shard_index"]) or record["shard_index"] not in range(8)
    ):
        raise ExecutionCollectionError(f"{label} shard index is invalid")


def _validate_shard_receipt(
    *,
    receipt_path: Path,
    log_root: Path,
    ordered_ids: list[str],
    source: dict[str, str],
    expected_github: dict[str, str],
    expected_authorization: dict[str, Any],
    expected_index: int,
) -> dict[str, Any]:
    document, _ = _load(receipt_path, canonical=True)
    _exact_keys(document, SHARD_TOP_KEYS, "shard receipt")
    if document["schema_version"] != SHARD_SCHEMA or document["experiment_id"] != EXPERIMENT_ID:
        raise ExecutionCollectionError(f"shard {expected_index} receipt identity is invalid")
    if document["source"] != source or document["github"] != expected_github:
        raise ExecutionCollectionError(f"shard {expected_index} provenance differs")
    authorization = _validate_authorization(
        document["authorization"], expected_github, f"shard {expected_index} authorization"
    )
    if authorization != expected_authorization:
        raise ExecutionCollectionError(f"shard {expected_index} primary-CI authorization differs")
    assignment = document["assignment"]
    if not isinstance(assignment, dict):
        raise ExecutionCollectionError(f"shard {expected_index} assignment is malformed")
    _exact_keys(assignment, ASSIGNMENT_KEYS, "shard assignment")
    expected_assignment = {
        "method": ASSIGNMENT_METHOD,
        "ordered_instance_ids": _assigned(ordered_ids, expected_index),
        "shard_count": SHARD_COUNT,
        "shard_index": expected_index,
    }
    if assignment != expected_assignment:
        raise ExecutionCollectionError(f"shard {expected_index} assignment differs")
    logs = document["logs"]
    if not isinstance(logs, list):
        raise ExecutionCollectionError(f"shard {expected_index} logs are malformed")
    for ordinal, record in enumerate(logs):
        _validate_file_record(
            record, aggregate=False, label=f"shard {expected_index} log {ordinal}"
        )
    if [record["name"] for record in logs] != _expected_log_names(
        expected_assignment["ordered_instance_ids"]
    ):
        raise ExecutionCollectionError(f"shard {expected_index} log names/order differ")
    expected = _expected_shard_document(
        execution_dir=log_root,
        ordered_ids=ordered_ids,
        source=source,
        github=expected_github,
        authorization=expected_authorization,
        index=expected_index,
    )
    if document != expected:
        raise ExecutionCollectionError(f"shard {expected_index} log hashes or sizes differ")
    return document


def _artifact_directories(artifacts_dir: Path) -> tuple[dict[str, str], dict[int, Path]]:
    try:
        entries = fs._require_regular_directory(artifacts_dir, "artifact download root")
    except fs.ExecutionCollectionError as exc:
        raise ExecutionCollectionError(str(exc)) from exc
    by_index: dict[int, Path] = {}
    run_ids: set[str] = set()
    attempts: set[str] = set()
    for entry in entries:
        try:
            metadata = entry.lstat()
        except OSError as exc:
            raise ExecutionCollectionError(f"cannot inspect artifact entry: {exc}") from exc
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise ExecutionCollectionError("artifact root must contain only regular directories")
        match = ARTIFACT_RE.fullmatch(entry.name)
        if match is None:
            raise ExecutionCollectionError(f"unexpected artifact directory: {entry.name}")
        run_id, attempt, index_text = match.groups()
        index = int(index_text)
        if index in by_index:
            raise ExecutionCollectionError(f"duplicate shard artifact: {index}")
        by_index[index] = entry
        run_ids.add(run_id)
        attempts.add(attempt)
    if set(by_index) != set(range(SHARD_COUNT)):
        raise ExecutionCollectionError("collector requires exact shard indexes 0..7")
    if len(run_ids) != 1 or len(attempts) != 1:
        raise ExecutionCollectionError("artifact directories mix GitHub runs or attempts")
    environment = _github_from_environment(required=True)
    assert environment is not None
    if environment["run_id"] not in run_ids or environment["run_attempt"] not in attempts:
        raise ExecutionCollectionError("artifacts are not from the current GitHub run attempt")
    _require_current_checkout_sha(environment)
    return environment, by_index


def _aggregate_document(
    *,
    execution_dir: Path,
    ordered_ids: list[str],
    source: dict[str, str],
    github: dict[str, str],
    authorization: dict[str, Any],
    receipts: list[dict[str, Any]],
) -> dict[str, Any]:
    shards: list[dict[str, Any]] = []
    owners: dict[str, int] = {}
    for index, receipt in enumerate(receipts):
        receipt_path = execution_dir / shard_receipt_name(index)
        payload = _read(receipt_path)
        assigned = receipt["assignment"]["ordered_instance_ids"]
        shards.append(
            {
                "artifact_name": artifact_name(github, index),
                "ordered_instance_ids": assigned,
                "receipt_bytes": len(payload),
                "receipt_name": receipt_path.name,
                "receipt_sha256": _sha256(payload),
                "shard_index": index,
            }
        )
        for record in receipt["logs"]:
            if record["name"] in owners:
                raise ExecutionCollectionError("duplicate log across shard receipts")
            owners[record["name"]] = index
    expected_names = _expected_log_names(ordered_ids)
    if set(owners) != set(expected_names):
        raise ExecutionCollectionError("shard union does not exactly cover all 50 patches")
    logs = []
    for name in expected_names:
        record = _file_record(execution_dir / name)
        record["shard_index"] = owners[name]
        logs.append(record)
    return {
        "assignment": {
            "method": ASSIGNMENT_METHOD,
            "ordered_instance_ids": ordered_ids,
            "shard_count": SHARD_COUNT,
        },
        "authorization": authorization,
        "experiment_id": EXPERIMENT_ID,
        "github": github,
        "logs": logs,
        "schema_version": AGGREGATE_SCHEMA,
        "shards": shards,
        "source": source,
    }


def collect_shards(
    *,
    artifacts_dir: Path,
    output_dir: Path,
    aggregate_receipt: Path,
    spec_index: Path = DEFAULT_SPEC_INDEX,
    runtime_manifest: Path = DEFAULT_RUNTIME_MANIFEST,
) -> dict[str, Any]:
    output_dir = Path(os.path.abspath(output_dir))
    aggregate_receipt = Path(os.path.abspath(aggregate_receipt))
    artifacts_dir = Path(os.path.abspath(artifacts_dir))
    spec_index = Path(os.path.abspath(spec_index))
    runtime_manifest = Path(os.path.abspath(runtime_manifest))
    try:
        fs._reject_symlink_components(output_dir, "iter203 collector output")
        fs._reject_symlink_components(aggregate_receipt, "iter203 aggregate receipt")
        fs._reject_symlink_components(artifacts_dir, "iter203 artifact root")
        fs._reject_symlink_components(spec_index, "iter203 spec index")
        fs._reject_symlink_components(runtime_manifest, "iter203 runtime manifest")
    except fs.ExecutionCollectionError as exc:
        raise ExecutionCollectionError(str(exc)) from exc
    if aggregate_receipt != output_dir / AGGREGATE_RECEIPT_NAME:
        raise ExecutionCollectionError(
            "aggregate receipt must use the frozen name inside output-dir"
        )
    ordered_ids, source = _validate_current_sources(spec_index, runtime_manifest)
    github, directories = _artifact_directories(artifacts_dir)
    authorization = _authorization_from_environment(github=github, required=True)
    assert authorization is not None
    receipts: list[dict[str, Any]] = []
    files: dict[str, Path] = {}
    for index in range(SHARD_COUNT):
        directory = directories[index]
        receipt_path = directory / shard_receipt_name(index)
        receipt = _validate_shard_receipt(
            receipt_path=receipt_path,
            log_root=directory,
            ordered_ids=ordered_ids,
            source=source,
            expected_github=github,
            expected_authorization=authorization,
            expected_index=index,
        )
        expected = set(_expected_log_names(_assigned(ordered_ids, index))) | {receipt_path.name}
        entries = _regular_entries(directory, f"shard {index} artifact")
        if {entry.name for entry in entries} != expected:
            raise ExecutionCollectionError(
                f"shard {index} artifact contains missing or extra files"
            )
        for entry in entries:
            if entry.name in files:
                raise ExecutionCollectionError(f"collector file collision: {entry.name}")
            files[entry.name] = entry
        receipts.append(receipt)

    try:
        fs._mkdir_parents_no_follow(output_dir.parent, "iter203 collector output parent")
        parent_descriptor = fs._open_directory_fd(
            output_dir.parent, "iter203 collector output parent"
        )
    except fs.ExecutionCollectionError as exc:
        raise ExecutionCollectionError(str(exc)) from exc
    staging = (
        output_dir.parent / f".{output_dir.name}.{os.getpid()}.{secrets.token_hex(8)}.collecting"
    )
    staging_exists = False
    try:
        fs._create_staging_directory_at(parent_descriptor, staging.name, staging)
        staging_exists = True
        for name in sorted(files):
            fs._write_staged_file(staging / name, _read(files[name]))
        aggregate = _aggregate_document(
            execution_dir=staging,
            ordered_ids=ordered_ids,
            source=source,
            github=github,
            authorization=authorization,
            receipts=receipts,
        )
        fs._write_staged_file(staging / AGGREGATE_RECEIPT_NAME, canonical_json_bytes(aggregate))
        fs._fsync_directory(staging)
        checked = check_execution_bundle(
            execution_dir=staging,
            aggregate_receipt=staging / AGGREGATE_RECEIPT_NAME,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
        )
        try:
            output_metadata = os.stat(
                output_dir.name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            output_metadata = None
        if output_metadata is not None:
            if not stat.S_ISDIR(output_metadata.st_mode):
                raise ExecutionCollectionError(
                    "collector output is not a regular non-symlink directory"
                )
            if fs._directory_names_at(parent_descriptor, output_dir.name, output_dir):
                raise ExecutionCollectionError("refusing to overwrite non-empty collector output")
            os.rmdir(output_dir.name, dir_fd=parent_descriptor)
        os.replace(
            staging.name,
            output_dir.name,
            src_dir_fd=parent_descriptor,
            dst_dir_fd=parent_descriptor,
        )
        staging_exists = False
        os.fsync(parent_descriptor)
    except fs.ExecutionCollectionError as exc:
        raise ExecutionCollectionError(str(exc)) from exc
    finally:
        if staging_exists:
            try:
                fs._remove_staging_directory_at(parent_descriptor, staging.name, staging)
            except fs.ExecutionCollectionError as exc:
                raise ExecutionCollectionError(str(exc)) from exc
        os.close(parent_descriptor)
    return checked


def check_execution_bundle(
    *,
    execution_dir: Path,
    aggregate_receipt: Path,
    spec_index: Path = DEFAULT_SPEC_INDEX,
    runtime_manifest: Path = DEFAULT_RUNTIME_MANIFEST,
) -> dict[str, Any]:
    if (
        Path(os.path.abspath(aggregate_receipt))
        != Path(os.path.abspath(execution_dir)) / AGGREGATE_RECEIPT_NAME
    ):
        raise ExecutionCollectionError("aggregate receipt path is not the frozen path")
    ordered_ids, source = _validate_current_sources(spec_index, runtime_manifest)
    aggregate, _ = _load(aggregate_receipt, canonical=True)
    _exact_keys(aggregate, AGGREGATE_TOP_KEYS, "aggregate receipt")
    if (
        aggregate["schema_version"] != AGGREGATE_SCHEMA
        or aggregate["experiment_id"] != EXPERIMENT_ID
    ):
        raise ExecutionCollectionError("aggregate receipt identity is invalid")
    if aggregate["source"] != source:
        raise ExecutionCollectionError("aggregate source hashes differ from current evidence")
    github = _validate_github(aggregate["github"], "aggregate GitHub provenance")
    authorization = _validate_authorization(
        aggregate["authorization"], github, "aggregate primary-CI authorization"
    )
    environment = _github_from_environment(required=False)
    if environment is not None and github != environment:
        raise ExecutionCollectionError("aggregate is not from the current GitHub run attempt")
    environment_authorization = _authorization_from_environment(
        github=github, required=environment is not None
    )
    if environment_authorization is not None and authorization != environment_authorization:
        raise ExecutionCollectionError(
            "aggregate primary-CI authorization differs from current workflow"
        )
    expected_assignment = {
        "method": ASSIGNMENT_METHOD,
        "ordered_instance_ids": ordered_ids,
        "shard_count": SHARD_COUNT,
    }
    if not isinstance(aggregate["assignment"], dict):
        raise ExecutionCollectionError("aggregate assignment is malformed")
    _exact_keys(aggregate["assignment"], AGGREGATE_ASSIGNMENT_KEYS, "aggregate assignment")
    if aggregate["assignment"] != expected_assignment:
        raise ExecutionCollectionError(
            "aggregate assignment differs from current 50-row spec order"
        )
    records = aggregate["shards"]
    if not isinstance(records, list) or len(records) != SHARD_COUNT:
        raise ExecutionCollectionError("aggregate must contain exactly eight shard records")
    receipts: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ExecutionCollectionError(f"aggregate shard record {index} is malformed")
        _exact_keys(record, SHARD_RECORD_KEYS, f"aggregate shard record {index}")
        receipt_path = Path(execution_dir) / shard_receipt_name(index)
        payload = _read(receipt_path)
        if record != {
            "artifact_name": artifact_name(github, index),
            "ordered_instance_ids": _assigned(ordered_ids, index),
            "receipt_bytes": len(payload),
            "receipt_name": receipt_path.name,
            "receipt_sha256": _sha256(payload),
            "shard_index": index,
        }:
            raise ExecutionCollectionError(f"aggregate shard record {index} differs")
        receipts.append(
            _validate_shard_receipt(
                receipt_path=receipt_path,
                log_root=Path(execution_dir),
                ordered_ids=ordered_ids,
                source=source,
                expected_github=github,
                expected_authorization=authorization,
                expected_index=index,
            )
        )
    logs = aggregate["logs"]
    if not isinstance(logs, list):
        raise ExecutionCollectionError("aggregate logs are malformed")
    for ordinal, record in enumerate(logs):
        _validate_file_record(record, aggregate=True, label=f"aggregate log {ordinal}")
    expected_entries = (
        set(_expected_log_names(ordered_ids))
        | {shard_receipt_name(index) for index in range(SHARD_COUNT)}
        | {AGGREGATE_RECEIPT_NAME}
    )
    if {
        entry.name
        for entry in _regular_entries(Path(execution_dir), "aggregate execution directory")
    } != expected_entries:
        raise ExecutionCollectionError(
            "aggregate execution directory has missing or extra evidence"
        )
    expected = _aggregate_document(
        execution_dir=Path(execution_dir),
        ordered_ids=ordered_ids,
        source=source,
        github=github,
        authorization=authorization,
        receipts=receipts,
    )
    if aggregate != expected:
        raise ExecutionCollectionError("aggregate log/receipt binding differs")
    return aggregate


def check_execution_bundle_with_logs(
    *,
    execution_dir: Path,
    aggregate_receipt: Path,
    spec_index: Path = DEFAULT_SPEC_INDEX,
    runtime_manifest: Path = DEFAULT_RUNTIME_MANIFEST,
) -> tuple[dict[str, Any], dict[str, bytes]]:
    """Return the verified receipt and its immutable in-memory log snapshot."""

    aggregate = check_execution_bundle(
        execution_dir=execution_dir,
        aggregate_receipt=aggregate_receipt,
        spec_index=spec_index,
        runtime_manifest=runtime_manifest,
    )
    snapshot: dict[str, bytes] = {}
    for ordinal, record in enumerate(aggregate["logs"]):
        payload = _read(Path(execution_dir) / record["name"])
        if len(payload) != record["bytes"] or _sha256(payload) != record["sha256"]:
            raise ExecutionCollectionError(f"aggregate log {ordinal} changed before snapshot")
        snapshot[record["name"]] = payload
    return aggregate, snapshot


def source_lines(*, spec_index: Path, runtime_manifest: Path) -> list[str]:
    """Emit the preflight-validated 50-row execution plan as tab-separated lines."""

    ids, _ = _validate_current_sources(spec_index, runtime_manifest)
    # The frozen v1 lock has its own byte-level validator/rendering and is not
    # reserialized here; its exact historic bytes are already hash-bound.
    lock, _ = _load(UPSTREAM / "proof/raw/image_lock.json", canonical=False)
    lock_rows = lock.get("images")
    if (
        lock.get("schema_version") != "telos.iter202.image_lock.v1"
        or lock.get("count") != 53
        or not isinstance(lock_rows, list)
        or len(lock_rows) != 53
    ):
        raise ExecutionCollectionError("frozen iter202 image lock is malformed")
    by_id = {row.get("instance_id"): row for row in lock_rows if isinstance(row, dict)}
    if len(by_id) != 53:
        raise ExecutionCollectionError("frozen iter202 image lock contains duplicate rows")
    safe_index, _ = _load(BRIDGE / "safe_scenario_index.json", canonical=True)
    safe_rows = safe_index.get("scenarios")
    if (
        safe_index.get("schema_version") != "telos.iter203.safe_scenario_index.v1"
        or safe_index.get("count") != 29
        or not isinstance(safe_rows, list)
        or len(safe_rows) != 29
    ):
        raise ExecutionCollectionError("safe-scenario index rows are malformed")
    safe_ids = {row.get("instance_id") for row in safe_rows if isinstance(row, dict)}
    if len(safe_ids) != 29 or None in safe_ids:
        raise ExecutionCollectionError("safe-scenario index must identify exactly 29 rows")
    if not safe_ids.issubset(ids):
        raise ExecutionCollectionError(
            "safe-scenario index contains an instance outside the 50 valid patches"
        )
    lines: list[str] = []
    for instance_id in ids:
        row = by_id.get(instance_id)
        if not isinstance(row, dict):
            raise ExecutionCollectionError(f"image lock does not cover {instance_id}")
        values = [
            instance_id,
            row.get("tag"),
            row.get("manifest_digest"),
            row.get("image_id"),
            row.get("reference"),
            "safe_scenario" if instance_id in safe_ids else "no_safe_scenario",
        ]
        if any(not isinstance(value, str) or not value for value in values):
            raise ExecutionCollectionError(f"execution plan row is malformed for {instance_id}")
        lines.append("\t".join(values))
    return lines


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    receipt = commands.add_parser("shard-receipt")
    receipt.add_argument("--execution-dir", type=Path, required=True)
    receipt.add_argument("--spec-index", type=Path, required=True)
    receipt.add_argument("--runtime-manifest", type=Path, required=True)
    receipt.add_argument("--shard-index", type=int, required=True)
    receipt.add_argument("--shard-count", type=int, required=True)
    collect = commands.add_parser("collect")
    collect.add_argument("--artifacts-dir", type=Path, required=True)
    collect.add_argument("--output-dir", type=Path, required=True)
    collect.add_argument("--aggregate-receipt", type=Path, required=True)
    collect.add_argument("--spec-index", type=Path, default=DEFAULT_SPEC_INDEX)
    collect.add_argument("--runtime-manifest", type=Path, default=DEFAULT_RUNTIME_MANIFEST)
    check = commands.add_parser("check")
    check.add_argument("--execution-dir", type=Path, required=True)
    check.add_argument("--aggregate-receipt", type=Path, required=True)
    check.add_argument("--spec-index", type=Path, default=DEFAULT_SPEC_INDEX)
    check.add_argument("--runtime-manifest", type=Path, default=DEFAULT_RUNTIME_MANIFEST)
    lines = commands.add_parser("source-lines")
    lines.add_argument("--spec-index", type=Path, default=DEFAULT_SPEC_INDEX)
    lines.add_argument("--runtime-manifest", type=Path, default=DEFAULT_RUNTIME_MANIFEST)
    publish = commands.add_parser("publish-log")
    publish.add_argument("--source", type=Path, required=True)
    publish.add_argument("--destination", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "shard-receipt":
            path = create_shard_receipt(
                execution_dir=args.execution_dir,
                spec_index=args.spec_index,
                runtime_manifest=args.runtime_manifest,
                shard_index=args.shard_index,
                shard_count=args.shard_count,
            )
            print(f"iter203 shard receipt complete: {path}")
        elif args.command == "collect":
            document = collect_shards(
                artifacts_dir=args.artifacts_dir,
                output_dir=args.output_dir,
                aggregate_receipt=args.aggregate_receipt,
                spec_index=args.spec_index,
                runtime_manifest=args.runtime_manifest,
            )
            print(
                f"iter203 collection complete: {len(document['shards'])} shards, {len(document['logs'])} logs"
            )
        elif args.command == "check":
            document = check_execution_bundle(
                execution_dir=args.execution_dir,
                aggregate_receipt=args.aggregate_receipt,
                spec_index=args.spec_index,
                runtime_manifest=args.runtime_manifest,
            )
            print(
                f"iter203 bundle verifies: {len(document['shards'])} shards, {len(document['logs'])} logs"
            )
        elif args.command == "source-lines":
            print(
                *source_lines(spec_index=args.spec_index, runtime_manifest=args.runtime_manifest),
                sep="\n",
            )
        else:
            publish_log(args.source, args.destination)
    except (ExecutionCollectionError, fs.ExecutionCollectionError) as exc:
        print(f"iter203 execution collection failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
