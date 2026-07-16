#!/usr/bin/env python3
"""Publish one bounded, visible iter205 Docker diagnostic without overwrite."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import capture_iter205_runtime_host as host_capture  # noqa: E402


TRUNCATION_MARKER = b"\nTELOS_ITER205_DIAGNOSTIC_TRUNCATED\n"
SCHEMA = "telos.iter205.runtime_diagnostic.v1"
CANONICAL_REPOSITORY = "manfromnowhere143/telos"
CANONICAL_WORKFLOW_REF = (
    f"{CANONICAL_REPOSITORY}/.github/workflows/iter205-execute.yml@refs/heads/master"
)
SHA_RE = re.compile(r"[0-9a-f]{40}")
POSITIVE_INTEGER_RE = re.compile(r"[1-9][0-9]*")


class DiagnosticError(ValueError):
    """A diagnostic source or destination violates the recovery contract."""


def _read_regular_bounded(path: Path, limit: int) -> tuple[bytes, int]:
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode):
        raise DiagnosticError("diagnostic source is not a regular non-symlink file")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        chunks: list[bytes] = []
        remaining = limit + 1
        while remaining:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if not os.path.samestat(before, after):
        raise DiagnosticError("diagnostic source changed during read")
    return b"".join(chunks), after.st_size


def bounded_payload(payload: bytes, limit: int) -> tuple[bytes, bool]:
    if limit < len(TRUNCATION_MARKER):
        raise DiagnosticError("diagnostic limit is smaller than the truncation marker")
    if len(payload) <= limit:
        return payload, False
    return payload[: limit - len(TRUNCATION_MARKER)] + TRUNCATION_MARKER, True


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: dict[str, object]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def publish(
    source: Path,
    destination: Path,
    metadata_destination: Path,
    limit: int,
    *,
    phase: str,
    row_id: str,
    image_ref: str,
    image_id: str,
    shard_index: int,
    exit_code: int,
    argv_sha256: str,
    runtime_manifest: Path,
    runtime_host_receipt: Path,
) -> bool:
    if (
        destination.exists()
        or destination.is_symlink()
        or metadata_destination.exists()
        or metadata_destination.is_symlink()
    ):
        raise DiagnosticError("refusing to overwrite a runtime diagnostic")
    prefix, source_bytes = _read_regular_bounded(source, limit)
    payload, truncated = bounded_payload(prefix if source_bytes <= limit else prefix[: limit + 1], limit)
    try:
        runtime_prefix, runtime_size = _read_regular_bounded(runtime_manifest, 16 * 1024 * 1024)
    except (OSError, DiagnosticError) as exc:
        raise DiagnosticError("cannot read iter205 runtime manifest") from exc
    if runtime_size != len(runtime_prefix):
        raise DiagnosticError("iter205 runtime manifest exceeds the 16 MiB read ceiling")
    try:
        host_prefix, host_size = _read_regular_bounded(runtime_host_receipt, 1024 * 1024)
        duplicates: list[str] = []

        def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
            value: dict[str, object] = {}
            for key, item in pairs:
                if key in value:
                    duplicates.append(key)
                value[key] = item
            return value

        runtime_host = json.loads(
            host_prefix,
            object_pairs_hook=unique_object,
            parse_constant=lambda item: (_ for _ in ()).throw(ValueError(item)),
        )
    except (OSError, DiagnosticError, ValueError, json.JSONDecodeError) as exc:
        raise DiagnosticError("cannot read strict iter205 runtime-host receipt") from exc
    if (
        host_size != len(host_prefix)
        or duplicates
        or not isinstance(runtime_host, dict)
        or host_prefix != _canonical_json(runtime_host)
    ):
        raise DiagnosticError("iter205 runtime-host receipt is unbounded or noncanonical")
    github = {
        "repository": os.environ.get("GITHUB_REPOSITORY", ""),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", ""),
        "run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "sha": os.environ.get("GITHUB_SHA", ""),
        "workflow_ref": os.environ.get("GITHUB_WORKFLOW_REF", ""),
    }
    try:
        runtime_host = host_capture.validate_document(runtime_host)
    except host_capture.RuntimeHostError as exc:
        raise DiagnosticError("iter205 runtime-host receipt fails its schema") from exc
    if (
        github["repository"] != CANONICAL_REPOSITORY
        or github["workflow_ref"] != CANONICAL_WORKFLOW_REF
        or github["run_attempt"] != "1"
        or POSITIVE_INTEGER_RE.fullmatch(github["run_id"]) is None
        or SHA_RE.fullmatch(github["sha"]) is None
        or len(argv_sha256) != 64
        or any(character not in "0123456789abcdef" for character in argv_sha256)
        or not phase
        or not row_id
        or not image_ref
        or not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id)
        or shard_index not in range(-1, 8)
        or exit_code < 0
        or runtime_host["github"] != github
    ):
        raise DiagnosticError("diagnostic provenance is incomplete or not attempt 1")
    metadata = {
        "argv_sha256": argv_sha256,
        "diagnostic": {
            "bytes": len(payload),
            "path": destination.name,
            "sha256": _sha256(payload),
            "source_bytes": source_bytes,
            "truncated": truncated,
        },
        "exit_code": exit_code,
        "github": github,
        "image_ref": image_ref,
        "image_id": image_id,
        "phase": phase,
        "row_id": row_id,
        "runtime_manifest_sha256": _sha256(runtime_prefix),
        "runtime_host": runtime_host,
        "schema_version": SCHEMA,
        "shard_index": shard_index,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        destination,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0),
        0o600,
    )
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    metadata_destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        metadata_descriptor = os.open(
            metadata_destination,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0),
            0o600,
        )
        with os.fdopen(metadata_descriptor, "wb") as stream:
            stream.write(_canonical_json(metadata))
            stream.flush()
            os.fsync(stream.fileno())
    except OSError:
        metadata_destination.unlink(missing_ok=True)
        raise
    source.unlink()
    return truncated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--metadata-destination", type=Path, required=True)
    parser.add_argument("--limit", type=int, required=True)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--row-id", required=True)
    parser.add_argument("--image-ref", required=True)
    parser.add_argument("--image-id", required=True)
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--exit-code", type=int, required=True)
    parser.add_argument("--argv-sha256", required=True)
    parser.add_argument("--runtime-manifest", type=Path, required=True)
    parser.add_argument("--runtime-host-receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        truncated = publish(
            args.source,
            args.destination,
            args.metadata_destination,
            args.limit,
            phase=args.phase,
            row_id=args.row_id,
            image_ref=args.image_ref,
            image_id=args.image_id,
            shard_index=args.shard_index,
            exit_code=args.exit_code,
            argv_sha256=args.argv_sha256,
            runtime_manifest=args.runtime_manifest,
            runtime_host_receipt=args.runtime_host_receipt,
        )
    except (OSError, DiagnosticError) as exc:
        print(f"iter205 diagnostic error: {exc}", file=sys.stderr)
        return 2
    print(
        f"iter205 diagnostic published: {args.destination} truncated={str(truncated).lower()}"
    )
    return 3 if truncated else 0


if __name__ == "__main__":
    raise SystemExit(main())
