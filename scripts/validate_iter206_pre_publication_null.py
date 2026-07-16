#!/usr/bin/env python3
"""Validate the exact unpublished iter206 claim-integrity null."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/iter206_iter205_admission_history_recovery"
NULL = EXP / "proof/pre_publication_claim_integrity_null.json"
RESULT = EXP / "RESULT.md"
TERMINAL_LEARNING = EXP / "proof/learning_record.pre_publication_claim_integrity_null.json"

SOURCE_COMMIT = "e7c2ec28daa746dbcfb5812d3771ab981ff984c0"
SEAL_COMMIT = "a2a05ef2ed05a0c457076f2bd5f1475507190685"
BASE_COMMIT = "4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f"

FROZEN_HASHES = {
    EXP / "HYPOTHESIS.md": "3e1185f5a79bf0cbd85ee046065ff9caf17fe7c1ccaa2c519be053510b1c4f26",
    ROOT / ".github/workflows/iter206-execute.yml": (
        "2a81a356709db97884b535f82367794541b4bd4d8d77ec4c83760d3deea3f215"
    ),
    EXP / "proof/learning_record.json": (
        "21469ccfab77fec563c234027ce671021e58245481bc78b1d4222cad4370ed6e"
    ),
    EXP / "proof/pre_execution_publication_safety.json": (
        "a6dbc9f8372311e8fc9594fde4b12f090940b105419b6733d8a665ed7291d8d9"
    ),
    EXP / "proof/raw/runtime_manifest.json": (
        "749bad5d40f7117ddcfffce314c1d9fd390ec8663ec2226d8cbd158dc41a942b"
    ),
}


class PrePublicationNullError(ValueError):
    """The iter206 stopped-boundary evidence differs."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _load_json(path: Path) -> dict:
    raw = path.read_bytes()
    document = json.loads(raw)
    canonical = json.dumps(
        document,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    ).encode() + b"\n"
    if raw != canonical:
        raise PrePublicationNullError(f"non-canonical JSON: {path.relative_to(ROOT)}")
    if not isinstance(document, dict):
        raise PrePublicationNullError(f"JSON root is not an object: {path.relative_to(ROOT)}")
    return document


def validate() -> None:
    for path, expected in FROZEN_HASHES.items():
        if not path.is_file() or sha256(path) != expected:
            raise PrePublicationNullError(
                f"frozen iter206 byte drift: {path.relative_to(ROOT)}"
            )

    document = _load_json(NULL)
    if document.get("schema_version") != "telos.iter206.pre_publication_claim_integrity_null.v1":
        raise PrePublicationNullError("iter206 null schema differs")
    if document.get("status") != "pre_publication_claim_integrity_null_superseded_unpublished":
        raise PrePublicationNullError("iter206 null status differs")

    publication = document.get("publication")
    if not isinstance(publication, dict) or set(publication.values()) != {0}:
        raise PrePublicationNullError("iter206 publication boundary is not exact zero")
    provider = document.get("provider_accounting")
    if not isinstance(provider, dict) or set(provider.values()) != {0}:
        raise PrePublicationNullError("iter206 provider boundary is not exact zero")
    science = document.get("scientific_evidence")
    if not isinstance(science, dict):
        raise PrePublicationNullError("iter206 scientific boundary is missing")
    for key in ("n", "k", "u"):
        if science.get(key) is not None:
            raise PrePublicationNullError(f"iter206 {key} must be absent/null")
    for key, value in science.items():
        if key not in {"n", "k", "u"} and value != 0:
            raise PrePublicationNullError(f"iter206 scientific count is nonzero: {key}")

    frozen = document.get("frozen_local_source")
    if not isinstance(frozen, dict):
        raise PrePublicationNullError("iter206 frozen source block is missing")
    if frozen.get("source_commit") != SOURCE_COMMIT or frozen.get("seal_commit") != SEAL_COMMIT:
        raise PrePublicationNullError("iter206 local commit identities differ")
    for key, path in (
        ("hypothesis_sha256", EXP / "HYPOTHESIS.md"),
        ("workflow_sha256", ROOT / ".github/workflows/iter206-execute.yml"),
        ("learning_record_sha256", EXP / "proof/learning_record.json"),
        (
            "pre_execution_publication_safety_sha256",
            EXP / "proof/pre_execution_publication_safety.json",
        ),
        ("runtime_manifest_sha256", EXP / "proof/raw/runtime_manifest.json"),
    ):
        if frozen.get(key) != sha256(path):
            raise PrePublicationNullError(f"iter206 null hash binding differs: {key}")

    if _git("cat-file", "-t", SOURCE_COMMIT) != "commit":
        raise PrePublicationNullError("iter206 source commit is unavailable")
    if _git("cat-file", "-t", SEAL_COMMIT) != "commit":
        raise PrePublicationNullError("iter206 seal commit is unavailable")
    if _git("rev-parse", f"{SOURCE_COMMIT}^") != BASE_COMMIT:
        raise PrePublicationNullError("iter206 source commit parent differs")
    if _git("rev-parse", f"{SEAL_COMMIT}^") != SOURCE_COMMIT:
        raise PrePublicationNullError("iter206 seal commit parent differs")

    result = RESULT.read_text(encoding="utf-8")
    for required in (
        "PRE-PUBLICATION CLAIM-INTEGRITY NULL",
        "SUPERSEDED WITHOUT PUBLICATION OR DISPATCH",
        "remote branch publications, pull requests, and merges: `0`",
        "contributes no `N`, `k`, or `u`",
        "iter207_claim_integrity_and_admission_recovery",
    ):
        if required not in result:
            raise PrePublicationNullError(f"iter206 result missing boundary text: {required}")

    learning = _load_json(TERMINAL_LEARNING)
    if learning.get("schema_version") != "telos.learning_record.v1":
        raise PrePublicationNullError("iter206 terminal learning schema differs")
    if learning.get("status") != "null":
        raise PrePublicationNullError("iter206 terminal learning status differs")
    if learning.get("supersedes") != (
        "experiments/iter206_iter205_admission_history_recovery/proof/learning_record.json"
    ):
        raise PrePublicationNullError("iter206 terminal learning supersession differs")


def main() -> int:
    try:
        validate()
    except (OSError, json.JSONDecodeError, subprocess.CalledProcessError, PrePublicationNullError) as exc:
        print(f"iter206 pre-publication null guard failed: {exc}")
        return 1
    print("iter206 pre-publication claim-integrity null: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
