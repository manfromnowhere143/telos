#!/usr/bin/env python3
"""Validate the exact iter203 attempt-1 infrastructure-null evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/iter203_iter202_safety_recovery"
NULL = EXP / "proof/infrastructure_null.json"
LOG_ROOT = EXP / "proof/raw/public_workflow_logs"
LOG_MANIFEST = LOG_ROOT / "manifest.json"
METADATA_ROOT = EXP / "proof/raw/public_workflow_metadata"
METADATA_MANIFEST = METADATA_ROOT / "manifest.json"
ITER203_RUNTIME = EXP / "proof/raw/runtime_manifest.json"
PRE_EXECUTION_SCAN = EXP / "proof/pre_execution_publication_safety.json"

ITER203_RUNTIME_SHA256 = "8beb0e845dbc9e3a4ce56832f28a62d4fd58ceac20adbc6bc06d6aef41be47e1"
PRE_EXECUTION_SCAN_SHA256 = "78a90912e2d2ced4d861737668b1e98ec5653e5c2ca8b12342bbf52d1f847d81"
RUN_ID = 29460393525
RUN_ATTEMPT = 1
HEAD_SHA = "5c409f79c9333206cff9ed80d59c08aa347110f6"
ASSIGNED = [7, 7, 6, 6, 6, 6, 6, 6]


class InfrastructureNullError(ValueError):
    """The normalized null or one of its exact public logs differs."""


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_strict(path: Path, *, canonical: bool = True) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    duplicates: list[str] = []

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                duplicates.append(key)
            result[key] = value
        return result

    try:
        value = json.loads(
            raw,
            object_pairs_hook=unique,
            parse_constant=lambda item: (_ for _ in ()).throw(ValueError(item)),
        )
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise InfrastructureNullError(f"cannot parse strict JSON {path}: {exc}") from exc
    if duplicates or not isinstance(value, dict):
        raise InfrastructureNullError(f"ambiguous JSON object: {path}")
    rendered = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    if canonical and raw != rendered:
        raise InfrastructureNullError(f"noncanonical JSON: {path}")
    return value, raw


def validate() -> dict[str, Any]:
    if sha256(ITER203_RUNTIME.read_bytes()) != ITER203_RUNTIME_SHA256:
        raise InfrastructureNullError("frozen iter203 runtime manifest changed")
    if sha256(PRE_EXECUTION_SCAN.read_bytes()) != PRE_EXECUTION_SCAN_SHA256:
        raise InfrastructureNullError("frozen iter203 pre-execution scan changed")
    null, _ = load_strict(NULL, canonical=False)
    manifest, _ = load_strict(LOG_MANIFEST)
    metadata_manifest, _ = load_strict(METADATA_MANIFEST)
    if (
        null.get("schema_version") != "telos.iter203.infrastructure_null.v1"
        or null.get("status") != "infrastructure_null"
        or null.get("run")
        != {
            "attempt": RUN_ATTEMPT,
            "conclusion": "failure",
            "event": "workflow_dispatch",
            "head_sha": HEAD_SHA,
            "id": RUN_ID,
            "url": f"https://github.com/manfromnowhere143/telos/actions/runs/{RUN_ID}",
        }
    ):
        raise InfrastructureNullError("iter203 normalized run identity differs")
    if (
        null.get("public_log_manifest_path") != str(LOG_MANIFEST.relative_to(ROOT))
        or null.get("public_workflow_metadata_manifest_path")
        != str(METADATA_MANIFEST.relative_to(ROOT))
        or null.get("artifact_api_total_count") != 0
    ):
        raise InfrastructureNullError("iter203 normalized raw-evidence paths differ")
    scientific = null.get("scientific_evidence")
    if not isinstance(scientific, dict) or scientific != {
        "aggregate_receipts": 0,
        "certification_command_starts": 0,
        "certification_executions": 0,
        "k": None,
        "n": None,
        "receipt_eligible_logs": 0,
        "scenario_attempts": 0,
        "scenario_executions": 0,
        "shard_receipts": 0,
        "u": None,
    }:
        raise InfrastructureNullError("iter203 scientific-null boundary differs")
    docker = null.get("docker_failure")
    if (
        not isinstance(docker, dict)
        or docker.get("failed_docker_run_invocations") != 50
        or docker.get("container_starts") != 0
        or docker.get("container_commands_started") != 0
        or docker.get("exit_code") != 125
        or docker.get("raw_daemon_stderr_retained") is not False
        or docker.get("corrective_option") != "compress=false"
        or docker.get("engine_version") != "28.0.4"
        or docker.get("moby_peeled_commit")
        != "6430e49a55babd9b8f4d08e70ecb2b68900770fe"
        or docker.get("moby_source_path") != "daemon/logger/local/config.go"
    ):
        raise InfrastructureNullError("iter203 Docker-null diagnosis differs")
    files = manifest.get("files")
    if (
        manifest.get("schema_version") != "telos.iter203.public_workflow_logs.v1"
        or manifest.get("run_id") != RUN_ID
        or manifest.get("run_attempt") != RUN_ATTEMPT
        or not isinstance(files, list)
        or len(files) != 8
    ):
        raise InfrastructureNullError("iter203 public-log manifest identity differs")
    null_shards = null.get("shards")
    if not isinstance(null_shards, list) or len(null_shards) != 8:
        raise InfrastructureNullError("iter203 normalized shard inventory differs")
    total_bytes = 0
    expected_names = {"manifest.json"}
    for index, (row, null_row) in enumerate(zip(files, null_shards, strict=True)):
        if not isinstance(row, dict) or not isinstance(null_row, dict):
            raise InfrastructureNullError(f"iter203 shard {index} record is malformed")
        path_text = row.get("path")
        if (
            row.get("shard_index") != index
            or null_row.get("shard_index") != index
            or row.get("job_id") != null_row.get("job_id")
            or row.get("sha256") != null_row.get("public_job_log_sha256_including_bom")
            or null_row.get("assigned_rows") != ASSIGNED[index]
            or null_row.get("docker_exit_125_rows") != ASSIGNED[index]
            or not isinstance(path_text, str)
            or re.fullmatch(rf"shard-{index}-job-[1-9][0-9]*\.log", path_text) is None
        ):
            raise InfrastructureNullError(f"iter203 shard {index} binding differs")
        path = LOG_ROOT / path_text
        if path.is_symlink() or not path.is_file():
            raise InfrastructureNullError(f"iter203 shard {index} log is absent or symlinked")
        payload = path.read_bytes()
        if len(payload) != row.get("bytes") or sha256(payload) != row.get("sha256"):
            raise InfrastructureNullError(f"iter203 shard {index} log hash/size differs")
        text = payload.decode("utf-8-sig")
        if (
            text.count("CERTIFICATION_INFRA_FAIL exit=125") != ASSIGNED[index]
            or text.count("execution failed closed") != 1
            or ">>>>> Cert Start" in text
            or "CERT_EXIT=" in text
            or ">>>>> Scenario Start" in text
        ):
            raise InfrastructureNullError(f"iter203 shard {index} null markers differ")
        total_bytes += len(payload)
        expected_names.add(path_text)
    if manifest.get("total_bytes") != total_bytes or total_bytes != 210202:
        raise InfrastructureNullError("iter203 public-log total bytes differ")
    if {path.name for path in LOG_ROOT.iterdir()} != expected_names:
        raise InfrastructureNullError("iter203 public-log directory has missing or extra entries")
    metadata_files = metadata_manifest.get("files")
    if (
        metadata_manifest.get("schema_version")
        != "telos.iter203.public_workflow_metadata.v1"
        or metadata_manifest.get("run_id") != RUN_ID
        or metadata_manifest.get("run_attempt") != RUN_ATTEMPT
        or not isinstance(metadata_files, list)
        or [row.get("path") for row in metadata_files if isinstance(row, dict)]
        != ["jobs.json", "artifacts.json"]
    ):
        raise InfrastructureNullError("iter203 public workflow metadata manifest differs")
    for row in metadata_files:
        path = METADATA_ROOT / row["path"]
        payload = path.read_bytes()
        if len(payload) != row.get("bytes") or sha256(payload) != row.get("sha256"):
            raise InfrastructureNullError(f"iter203 metadata hash/size differs: {path.name}")
    jobs, _ = load_strict(METADATA_ROOT / "jobs.json")
    artifacts, _ = load_strict(METADATA_ROOT / "artifacts.json")
    job_rows = jobs.get("jobs")
    if jobs.get("total_count") != 10 or not isinstance(job_rows, list) or len(job_rows) != 10:
        raise InfrastructureNullError("iter203 raw job count differs")
    by_id = {row.get("id"): row for row in job_rows if isinstance(row, dict)}
    failed_ids = {row["job_id"] for row in null_shards}
    if (
        by_id.get(87502469240, {}).get("conclusion") != "success"
        or by_id.get(87503534378, {}).get("conclusion") != "skipped"
        or {job_id for job_id in failed_ids if by_id.get(job_id, {}).get("conclusion") == "failure"}
        != failed_ids
        or set(by_id) != failed_ids | {87502469240, 87503534378}
    ):
        raise InfrastructureNullError("iter203 raw job conclusions differ")
    if artifacts != {"artifacts": [], "total_count": 0}:
        raise InfrastructureNullError("iter203 raw artifact response is not exact zero")
    if {path.name for path in METADATA_ROOT.iterdir()} != {
        "manifest.json",
        "jobs.json",
        "artifacts.json",
    }:
        raise InfrastructureNullError("iter203 metadata directory has missing or extra entries")
    return {
        "failed_docker_run_invocations": 50,
        "log_count": 8,
        "run_attempt": RUN_ATTEMPT,
        "run_id": RUN_ID,
        "scientific_outcomes": 0,
    }


def main() -> int:
    try:
        summary = validate()
    except (OSError, InfrastructureNullError) as exc:
        print(f"iter203 infrastructure-null guard failed: {exc}", file=sys.stderr)
        return 1
    print(
        "iter203 infrastructure-null guard: "
        f"{summary['failed_docker_run_invocations']} pre-command Docker run failures, "
        f"{summary['scientific_outcomes']} scientific outcomes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
