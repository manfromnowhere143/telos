#!/usr/bin/env python3
"""Capture or validate the observed Docker/GitHub host for iter204 receipts.

The document is descriptive provenance only.  It never asserts that a hosted
runner is immutable, and it never reads or serializes provider credentials.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Mapping


SCHEMA = "telos.iter204.observed_runtime_host.v1"
CANONICAL_REPOSITORY = "manfromnowhere143/telos"
CANONICAL_WORKFLOW_REF = (
    f"{CANONICAL_REPOSITORY}/.github/workflows/iter204-execute.yml@refs/heads/master"
)
GITHUB_SHA_RE = re.compile(r"[0-9a-f]{40}")
POSITIVE_INTEGER_RE = re.compile(r"[1-9][0-9]*")
HOST_KEYS = {
    "docker_client",
    "docker_server",
    "github",
    "runner_image",
    "schema_version",
    "statement",
}
DOCKER_KEYS = {"api_version", "architecture", "git_commit", "os", "version"}
GITHUB_KEYS = {"repository", "run_attempt", "run_id", "sha", "workflow_ref"}
RUNNER_KEYS = {"image_os", "image_version", "os", "architecture"}


class RuntimeHostError(ValueError):
    """Observed runtime provenance is absent, malformed, or ambiguous."""


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value) and "\n" not in value and "\r" not in value


def validate_document(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != HOST_KEYS:
        raise RuntimeHostError("runtime-host top-level keys differ")
    if value.get("schema_version") != SCHEMA:
        raise RuntimeHostError("runtime-host schema differs")
    if value.get("statement") != "observed_host_metadata_not_an_immutability_claim":
        raise RuntimeHostError("runtime-host mutability statement differs")
    for side in ("docker_client", "docker_server"):
        record = value.get(side)
        if not isinstance(record, dict) or set(record) != DOCKER_KEYS:
            raise RuntimeHostError(f"{side} keys differ")
        if not all(_nonempty(record[key]) for key in DOCKER_KEYS):
            raise RuntimeHostError(f"{side} contains an empty or multiline value")
    github = value.get("github")
    if not isinstance(github, dict) or set(github) != GITHUB_KEYS:
        raise RuntimeHostError("runtime-host GitHub keys differ")
    if (
        not all(_nonempty(github[key]) for key in GITHUB_KEYS)
        or GITHUB_SHA_RE.fullmatch(github["sha"]) is None
        or POSITIVE_INTEGER_RE.fullmatch(github["run_id"]) is None
        or github["run_attempt"] != "1"
        or github["repository"] != CANONICAL_REPOSITORY
        or github["workflow_ref"] != CANONICAL_WORKFLOW_REF
    ):
        raise RuntimeHostError("runtime-host GitHub identity is invalid or not attempt 1")
    runner = value.get("runner_image")
    if not isinstance(runner, dict) or set(runner) != RUNNER_KEYS:
        raise RuntimeHostError("runtime-host runner-image keys differ")
    if not all(
        _nonempty(runner[key]) and runner[key] != "unavailable" for key in RUNNER_KEYS
    ):
        raise RuntimeHostError("runtime-host runner-image values are empty or multiline")
    return value


def _docker_version() -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["docker", "version", "--format", "{{json .}}"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        value = json.loads(completed.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        raise RuntimeHostError(f"cannot capture Docker version: {type(exc).__name__}") from exc
    if not isinstance(value, dict):
        raise RuntimeHostError("Docker version output is not an object")
    return value


def _docker_side(value: Any, label: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise RuntimeHostError(f"Docker {label} version block is absent")
    record = {
        "api_version": value.get("ApiVersion"),
        "architecture": value.get("Arch"),
        "git_commit": value.get("GitCommit"),
        "os": value.get("Os"),
        "version": value.get("Version"),
    }
    if not all(_nonempty(item) for item in record.values()):
        raise RuntimeHostError(f"Docker {label} version fields are incomplete")
    return record  # type: ignore[return-value]


def capture_document(
    docker: Mapping[str, Any], environment: Mapping[str, str]
) -> dict[str, Any]:
    document = {
        "docker_client": _docker_side(docker.get("Client"), "client"),
        "docker_server": _docker_side(docker.get("Server"), "server"),
        "github": {
            "repository": environment.get("GITHUB_REPOSITORY", ""),
            "run_attempt": environment.get("GITHUB_RUN_ATTEMPT", ""),
            "run_id": environment.get("GITHUB_RUN_ID", ""),
            "sha": environment.get("GITHUB_SHA", ""),
            "workflow_ref": environment.get("GITHUB_WORKFLOW_REF", ""),
        },
        "runner_image": {
            "architecture": environment.get("RUNNER_ARCH", ""),
            "image_os": environment.get("ImageOS", ""),
            "image_version": environment.get("ImageVersion", ""),
            "os": environment.get("RUNNER_OS", ""),
        },
        "schema_version": SCHEMA,
        "statement": "observed_host_metadata_not_an_immutability_claim",
    }
    return validate_document(document)


def load_document(path: Path) -> dict[str, Any]:
    duplicates: list[str] = []

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                duplicates.append(key)
            value[key] = item
        return value

    try:
        raw = path.read_bytes()
        value = json.loads(
            raw,
            object_pairs_hook=unique_object,
            parse_constant=lambda item: (_ for _ in ()).throw(ValueError(item)),
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise RuntimeHostError(f"cannot parse runtime-host receipt: {type(exc).__name__}") from exc
    if duplicates:
        raise RuntimeHostError(f"duplicate runtime-host JSON key: {duplicates[0]!r}")
    document = validate_document(value)
    if raw != canonical_json_bytes(document):
        raise RuntimeHostError("runtime-host receipt is not canonical JSON")
    return document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--write", type=Path)
    modes.add_argument("--check", type=Path)
    args = parser.parse_args()
    try:
        if args.write is not None:
            if args.write.exists() or args.write.is_symlink():
                raise RuntimeHostError("refusing to overwrite runtime-host receipt")
            document = capture_document(_docker_version(), os.environ)
            args.write.parent.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(
                args.write,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0),
                0o600,
            )
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(canonical_json_bytes(document))
                stream.flush()
                os.fsync(stream.fileno())
            print(f"iter204 observed runtime host captured: {args.write}")
        else:
            load_document(args.check)
            print(f"iter204 observed runtime host verifies: {args.check}")
    except RuntimeHostError as exc:
        print(f"iter204 runtime-host error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
