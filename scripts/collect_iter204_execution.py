#!/usr/bin/env python3
"""Collect iter204 evidence without relabeling or mutating iter203 evidence.

The proven iter203 collector implementation is loaded into an isolated module
instance, then narrowed to the additive iter204 workflow identity, schemas,
runtime manifest, output path, attempt-1 rule, and observed-host receipts.
Scientific inputs remain the exact byte-bound iter203 projections.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import capture_iter204_runtime_host as host_capture  # noqa: E402


EXPERIMENT_ID = "iter204_iter203_infrastructure_recovery"
EXP = ROOT / "experiments" / EXPERIMENT_ID
UPSTREAM_ITER203 = ROOT / "experiments/iter203_iter202_safety_recovery"
DEFAULT_SPEC_INDEX = UPSTREAM_ITER203 / "proof/raw/specs/index.json"
DEFAULT_RUNTIME_MANIFEST = EXP / "proof/raw/runtime_manifest.json"
DEFAULT_EXECUTION_DIR = EXP / "proof/raw/execution"
AGGREGATE_RECEIPT_NAME = "_telos_iter204_execution_complete.receipt.json"
RUNTIME_HOST_RECEIPT_ENV = "TELOS_ITER204_RUNTIME_HOST_RECEIPT"
SMOKE_RECEIPT_ENV = "TELOS_ITER204_SMOKE_RECEIPT"

CANONICAL_REPOSITORY = "manfromnowhere143/telos"
CANONICAL_WORKFLOW_REF = (
    f"{CANONICAL_REPOSITORY}/.github/workflows/iter204-execute.yml@refs/heads/master"
)
PRIMARY_CI_AUTHORIZATION_ENV = "TELOS_ITER204_PRIMARY_CI_AUTHORIZATION"
PRIMARY_CI_AUTHORIZATION_SCHEMA = "telos.iter204.primary_ci_authorization.v1"
RUNTIME_MANIFEST_SCHEMA = "telos.iter204.execution_runtime_recovery.v1"
SHARD_SCHEMA = "telos.iter204.execution_shard_receipt.v1"
AGGREGATE_SCHEMA = "telos.iter204.execution_aggregate_receipt.v1"
ARTIFACT_RE = re.compile(
    r"iter204-execution-run-([1-9][0-9]*)-attempt-(1)-shard-([0-7])-of-8"
)


def _load_isolated_core() -> Any:
    path = ROOT / "scripts/collect_iter203_execution.py"
    spec = importlib.util.spec_from_file_location("_telos_iter204_collector_core", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load isolated iter203 collector implementation")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_core = _load_isolated_core()
ExecutionCollectionError = _core.ExecutionCollectionError

# Configure only the isolated instance.  Importing this module cannot mutate the
# historical scripts.collect_iter203_execution module used by iter203 tests.
_core.EXPERIMENT_ID = EXPERIMENT_ID
_core.EXP = UPSTREAM_ITER203
_core.BRIDGE = UPSTREAM_ITER203 / "proof/raw/safety_recovery_bridge"
_core.DEFAULT_SPEC_INDEX = DEFAULT_SPEC_INDEX
_core.DEFAULT_RUNTIME_MANIFEST = DEFAULT_RUNTIME_MANIFEST
_core.DEFAULT_EXECUTION_DIR = DEFAULT_EXECUTION_DIR
_core.AGGREGATE_RECEIPT_NAME = AGGREGATE_RECEIPT_NAME
_core.CANONICAL_REPOSITORY = CANONICAL_REPOSITORY
_core.CANONICAL_WORKFLOW_REF = CANONICAL_WORKFLOW_REF
_core.PRIMARY_CI_AUTHORIZATION_ENV = PRIMARY_CI_AUTHORIZATION_ENV
_core.PRIMARY_CI_AUTHORIZATION_SCHEMA = PRIMARY_CI_AUTHORIZATION_SCHEMA
_core.RUNTIME_MANIFEST_SCHEMA = RUNTIME_MANIFEST_SCHEMA
_core.SHARD_SCHEMA = SHARD_SCHEMA
_core.AGGREGATE_SCHEMA = AGGREGATE_SCHEMA
_core.ARTIFACT_RE = ARTIFACT_RE
_core.SHARD_TOP_KEYS = set(_core.SHARD_TOP_KEYS) | {"runtime_host", "smoke_gate"}
_core.AGGREGATE_TOP_KEYS = set(_core.AGGREGATE_TOP_KEYS) | {
    "runtime_hosts",
    "smoke_gate",
}


def shard_receipt_name(index: int) -> str:
    return f"_telos_iter204_shard_{index}_of_8.receipt.json"


def artifact_name(github: dict[str, str], index: int) -> str:
    return (
        f"iter204-execution-run-{github['run_id']}-attempt-{github['run_attempt']}-"
        f"shard-{index}-of-8"
    )


_core.shard_receipt_name = shard_receipt_name
_core.artifact_name = artifact_name


_original_validate_github = _core._validate_github


def _validate_github(value: Any, label: str) -> dict[str, str]:
    github = _original_validate_github(value, label)
    if github["run_attempt"] != "1":
        raise ExecutionCollectionError(
            f"{label} is not canonical iter204 workflow attempt 1"
        )
    return github


_core._validate_github = _validate_github


def _validate_runtime_host(value: Any, github: dict[str, str]) -> dict[str, Any]:
    try:
        document = host_capture.validate_document(value)
    except host_capture.RuntimeHostError as exc:
        raise ExecutionCollectionError(f"runtime-host receipt is invalid: {exc}") from exc
    if document["github"] != github:
        raise ExecutionCollectionError("runtime-host GitHub provenance differs from shard")
    if document["github"]["workflow_ref"] != CANONICAL_WORKFLOW_REF:
        raise ExecutionCollectionError("runtime-host workflow identity differs")
    return document


def _runtime_host_from_environment(github: dict[str, str]) -> dict[str, Any]:
    value = os.environ.get(RUNTIME_HOST_RECEIPT_ENV, "")
    if not value:
        raise ExecutionCollectionError("iter204 runtime-host receipt path is required")
    path = Path(value)
    try:
        document = host_capture.load_document(path)
    except (OSError, host_capture.RuntimeHostError) as exc:
        raise ExecutionCollectionError(f"cannot load iter204 runtime-host receipt: {exc}") from exc
    return _validate_runtime_host(document, github)


def _argv_sha256(values: list[str]) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(value.encode())
        digest.update(b"\0")
    return digest.hexdigest()


def _validate_smoke_gate(
    value: Any,
    github: dict[str, str],
    *,
    runtime_manifest: Path,
    verify_siblings: bool = False,
    receipt_path: Path | None = None,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ExecutionCollectionError("iter204 smoke receipt is not an object")
    expected_keys = {
        "argument_vector_sha256",
        "command",
        "diagnostic",
        "docker_safety_args",
        "exit_code",
        "github",
        "image_id",
        "image_ref",
        "ordinal",
        "output_exact",
        "row_id",
        "runtime_host",
        "runtime_manifest_sha256",
        "schema_version",
        "status",
        "streams",
    }
    if set(value) != expected_keys:
        raise ExecutionCollectionError("iter204 smoke receipt keys differ")
    expected_args = [
        "--network", "none", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges=true", "--pids-limit", "1024",
        "--memory", "10g", "--cpus", "4", "--log-driver", "local",
        "--log-opt", "max-size=3m", "--log-opt", "max-file=1",
        "--log-opt", "compress=false",
    ]
    expected_command = [
        "bash", "--noprofile", "--norc", "-c",
        'printf "%s\\n" TELOS_ITER204_LOG_DRIVER_SMOKE_OK',
    ]
    runtime_payload = _core._read(runtime_manifest)
    if (
        value.get("schema_version") != "telos.iter204.no_science_smoke_receipt.v1"
        or value.get("status") != "pass"
        or value.get("exit_code") != 0
        or value.get("output_exact") is not True
        or value.get("ordinal") != 0
        or value.get("github") != github
        or value.get("docker_safety_args") != expected_args
        or value.get("command") != expected_command
        or value.get("runtime_manifest_sha256")
        != hashlib.sha256(runtime_payload).hexdigest()
    ):
        raise ExecutionCollectionError("iter204 no-science smoke did not pass exact contract")
    runtime_host = _validate_runtime_host(value.get("runtime_host"), github)
    lines = _core.source_lines(
        spec_index=DEFAULT_SPEC_INDEX,
        runtime_manifest=runtime_manifest,
    )
    first = lines[0].split("\t")
    if (
        len(first) != 6
        or value.get("row_id") != first[0]
        or value.get("image_id") != first[3]
        or value.get("image_ref") != first[4]
    ):
        raise ExecutionCollectionError("iter204 smoke is not bound to frozen ordinal 0")
    expected_argv_digest = _argv_sha256(
        [
            "docker",
            "run",
            "--rm",
            *expected_args,
            "--entrypoint",
            "bash",
            first[4],
            *expected_command[1:],
        ]
    )
    digest = value.get("argument_vector_sha256")
    diagnostic = value.get("diagnostic")
    streams = value.get("streams")
    expected_stdout = b"TELOS_ITER204_LOG_DRIVER_SMOKE_OK\n"
    expected_diagnostic = (
        b"TELOS_ITER204_SEPARATE_STREAMS_V1\n"
        + b"STDOUT_BYTES="
        + str(len(expected_stdout)).encode()
        + b"\nSTDERR_BYTES=0\n>>>>> STDOUT\n"
        + expected_stdout
        + b">>>>> STDERR\n"
    )
    if (
        digest != expected_argv_digest
        or not isinstance(diagnostic, dict)
        or set(diagnostic) != {"bytes", "path", "receipt_sha256", "sha256"}
        or diagnostic.get("path") != "smoke.diagnostic.log"
        or diagnostic.get("bytes") != len(expected_diagnostic)
        or diagnostic.get("sha256") != hashlib.sha256(expected_diagnostic).hexdigest()
        or any(
            not isinstance(diagnostic.get(key), str)
            or re.fullmatch(r"[0-9a-f]{64}", diagnostic[key]) is None
            for key in ("receipt_sha256",)
        )
        or streams
        != {
            "stderr": {
                "bytes": 0,
                "sha256": hashlib.sha256(b"").hexdigest(),
            },
            "stdout": {
                "bytes": len(expected_stdout),
                "sha256": hashlib.sha256(expected_stdout).hexdigest(),
            },
        }
    ):
        raise ExecutionCollectionError("iter204 smoke diagnostic binding is malformed")
    if verify_siblings:
        if receipt_path is None:
            raise ExecutionCollectionError("smoke sibling verification lacks receipt path")
        diagnostic_path = receipt_path.parent / diagnostic["path"]
        metadata_path = receipt_path.parent / "smoke.diagnostic.receipt.json"
        diagnostic_payload = _core._read(diagnostic_path)
        metadata, metadata_payload = _core._load(metadata_path, canonical=True)
        expected_metadata = {
            "argv_sha256": expected_argv_digest,
            "diagnostic": {
                "bytes": len(expected_diagnostic),
                "path": "smoke.diagnostic.log",
                "sha256": hashlib.sha256(expected_diagnostic).hexdigest(),
                "source_bytes": len(expected_diagnostic),
                "truncated": False,
            },
            "exit_code": 0,
            "github": github,
            "image_id": first[3],
            "image_ref": first[4],
            "phase": "global_no_science_log_driver_smoke",
            "row_id": first[0],
            "runtime_host": runtime_host,
            "runtime_manifest_sha256": hashlib.sha256(runtime_payload).hexdigest(),
            "schema_version": "telos.iter204.runtime_diagnostic.v1",
            "shard_index": -1,
        }
        if (
            diagnostic_payload != expected_diagnostic
            or metadata != expected_metadata
            or hashlib.sha256(metadata_payload).hexdigest() != diagnostic["receipt_sha256"]
        ):
            raise ExecutionCollectionError("iter204 smoke sibling evidence differs")
    return value


def _smoke_gate_from_environment(
    github: dict[str, str], runtime_manifest: Path
) -> dict[str, Any]:
    path_text = os.environ.get(SMOKE_RECEIPT_ENV, "")
    if not path_text:
        raise ExecutionCollectionError("iter204 no-science smoke receipt is required")
    path = Path(path_text)
    document, _ = _core._load(path, canonical=True)
    return _validate_smoke_gate(
        document,
        github,
        runtime_manifest=runtime_manifest,
        verify_siblings=True,
        receipt_path=path,
    )


def check_smoke_receipt(*, receipt: Path, runtime_manifest: Path) -> dict[str, Any]:
    github = _core._github_from_environment(required=True)
    assert github is not None
    document, _ = _core._load(receipt, canonical=True)
    return _validate_smoke_gate(
        document,
        github,
        runtime_manifest=runtime_manifest,
        verify_siblings=True,
        receipt_path=receipt,
    )


_expected_runtime_host: dict[str, Any] | None = None
_expected_smoke_gate: dict[str, Any] | None = None
_original_expected_shard_document = _core._expected_shard_document


def _expected_shard_document(**kwargs: Any) -> dict[str, Any]:
    document = _original_expected_shard_document(**kwargs)
    if _expected_runtime_host is None:
        raise ExecutionCollectionError("runtime-host expectation is absent")
    if _expected_smoke_gate is None:
        raise ExecutionCollectionError("no-science smoke expectation is absent")
    document["runtime_host"] = _expected_runtime_host
    document["smoke_gate"] = _expected_smoke_gate
    return document


_core._expected_shard_document = _expected_shard_document
_original_create_shard_receipt = _core.create_shard_receipt


def create_shard_receipt(
    *,
    execution_dir: Path,
    spec_index: Path,
    runtime_manifest: Path,
    shard_index: int,
    shard_count: int,
) -> Path:
    global _expected_runtime_host, _expected_smoke_gate
    github = _core._github_from_environment(required=True)
    assert github is not None
    runtime_host = _runtime_host_from_environment(github)
    smoke_gate = _smoke_gate_from_environment(github, runtime_manifest)
    if _expected_runtime_host is not None or _expected_smoke_gate is not None:
        raise ExecutionCollectionError("nested iter204 shard receipt creation is forbidden")
    _expected_runtime_host = runtime_host
    _expected_smoke_gate = smoke_gate
    try:
        return _original_create_shard_receipt(
            execution_dir=execution_dir,
            spec_index=spec_index,
            runtime_manifest=runtime_manifest,
            shard_index=shard_index,
            shard_count=shard_count,
        )
    finally:
        _expected_runtime_host = None
        _expected_smoke_gate = None


_core.create_shard_receipt = create_shard_receipt
_original_validate_shard_receipt = _core._validate_shard_receipt


def _validate_shard_receipt(**kwargs: Any) -> dict[str, Any]:
    global _expected_runtime_host, _expected_smoke_gate
    receipt_path = kwargs["receipt_path"]
    expected_github = kwargs["expected_github"]
    document, _ = _core._load(receipt_path, canonical=True)
    runtime_host = _validate_runtime_host(document.get("runtime_host"), expected_github)
    smoke_gate = _validate_smoke_gate(
        document.get("smoke_gate"),
        expected_github,
        runtime_manifest=kwargs.get("runtime_manifest", DEFAULT_RUNTIME_MANIFEST),
    )
    if _expected_runtime_host is not None or _expected_smoke_gate is not None:
        raise ExecutionCollectionError("nested iter204 shard receipt validation is forbidden")
    _expected_runtime_host = runtime_host
    _expected_smoke_gate = smoke_gate
    try:
        return _original_validate_shard_receipt(**kwargs)
    finally:
        _expected_runtime_host = None
        _expected_smoke_gate = None


_core._validate_shard_receipt = _validate_shard_receipt
_original_aggregate_document = _core._aggregate_document


def _aggregate_document(**kwargs: Any) -> dict[str, Any]:
    document = _original_aggregate_document(**kwargs)
    receipts = kwargs["receipts"]
    smoke_gates = [receipt["smoke_gate"] for receipt in receipts]
    if any(smoke_gate != smoke_gates[0] for smoke_gate in smoke_gates[1:]):
        raise ExecutionCollectionError("shards bind different iter204 smoke receipts")
    document["smoke_gate"] = smoke_gates[0]
    document["runtime_hosts"] = [receipt["runtime_host"] for receipt in receipts]
    return document


_core._aggregate_document = _aggregate_document

# Public evidence APIs.  These call the isolated, configured implementation.
canonical_json_bytes = _core.canonical_json_bytes
source_lines = _core.source_lines
publish_log = _core.publish_log
collect_shards = _core.collect_shards
check_execution_bundle = _core.check_execution_bundle
check_execution_bundle_with_logs = _core.check_execution_bundle_with_logs
_authorization_transport = _core._authorization_transport
_decode_authorization_transport = _core._decode_authorization_transport
_validate_authorization = _core._validate_authorization
_validate_current_sources = _core._validate_current_sources
_github_from_environment = _core._github_from_environment
_sha256 = _core._sha256


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
    smoke = commands.add_parser("smoke-check")
    smoke.add_argument("--receipt", type=Path, required=True)
    smoke.add_argument("--runtime-manifest", type=Path, default=DEFAULT_RUNTIME_MANIFEST)
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
            print(f"iter204 shard receipt complete: {path}")
        elif args.command == "collect":
            document = collect_shards(
                artifacts_dir=args.artifacts_dir,
                output_dir=args.output_dir,
                aggregate_receipt=args.aggregate_receipt,
                spec_index=args.spec_index,
                runtime_manifest=args.runtime_manifest,
            )
            print(
                f"iter204 collection complete: {len(document['shards'])} shards, "
                f"{len(document['logs'])} logs"
            )
        elif args.command == "check":
            document = check_execution_bundle(
                execution_dir=args.execution_dir,
                aggregate_receipt=args.aggregate_receipt,
                spec_index=args.spec_index,
                runtime_manifest=args.runtime_manifest,
            )
            print(
                f"iter204 bundle verifies: {len(document['shards'])} shards, "
                f"{len(document['logs'])} logs"
            )
        elif args.command == "source-lines":
            print(
                *source_lines(spec_index=args.spec_index, runtime_manifest=args.runtime_manifest),
                sep="\n",
            )
        elif args.command == "publish-log":
            publish_log(args.source, args.destination)
        else:
            check_smoke_receipt(
                receipt=args.receipt,
                runtime_manifest=args.runtime_manifest,
            )
            print(f"iter204 no-science smoke receipt verifies: {args.receipt}")
    except (ExecutionCollectionError, _core.fs.ExecutionCollectionError) as exc:
        print(f"iter204 execution collection failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
