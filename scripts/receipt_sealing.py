#!/usr/bin/env python3
"""Verify a sealed receipt against its immutable source Git blobs.

A receipt binds shared files such as ``README.md`` and ``.github/workflows/ci.yml``.  Once
its iteration is sealed, a later iteration legitimately edits those files, and a receipt
check that reads the working tree then fails for a receipt that never changed.  Iter213 and
iter214 already fixed this class once: a sealed receipt must validate the bytes that
existed at its own source commit, never a descendant's working tree.

The rule is simple.  If the receipt is committed, verify it against the commit that
introduced it.  If it is not yet committed, verify it against the working tree, because
that is the iteration currently being built.
"""

from __future__ import annotations

import hashlib
import json
import stat
import subprocess
from pathlib import Path
from typing import Any


class ReceiptSealingError(ValueError):
    """Raised when a sealed receipt no longer matches its own source blobs."""


def _git(root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *arguments], cwd=root, capture_output=True, check=False)


def introducing_commit(root: Path, relative_path: str) -> str | None:
    """The commit that added ``relative_path``, or None when it is uncommitted."""

    result = _git(
        root,
        "log",
        "--follow",
        "--diff-filter=A",
        "--format=%H",
        "--",
        relative_path,
    )
    if result.returncode != 0:
        return None
    commits = result.stdout.decode().split()
    return commits[-1] if commits else None


def _source_blob(root: Path, source: str, relative_path: str) -> tuple[str, str, bytes]:
    """Return a regular source entry's Git mode and exact blob bytes."""

    listing = _git(root, "ls-tree", "-z", source, "--", relative_path)
    if listing.returncode != 0:
        raise ReceiptSealingError(
            f"cannot inspect sealed Git entry at {source[:12]}: {relative_path}"
        )
    records = [record for record in listing.stdout.split(b"\0") if record]
    if len(records) != 1:
        raise ReceiptSealingError(
            f"sealed Git entry is absent or ambiguous at {source[:12]}: {relative_path}"
        )
    try:
        metadata, encoded_path = records[0].split(b"\t", 1)
        mode, object_type, object_id = metadata.decode("ascii").split()
        listed_path = encoded_path.decode("utf-8")
    except (UnicodeDecodeError, ValueError) as exc:
        raise ReceiptSealingError(
            f"sealed Git entry is malformed at {source[:12]}: {relative_path}"
        ) from exc
    if listed_path != relative_path:
        raise ReceiptSealingError(
            f"sealed Git entry resolves a different path at {source[:12]}: {relative_path}"
        )
    if object_type != "blob" or mode not in {"100644", "100755"}:
        raise ReceiptSealingError(
            f"sealed Git entry is not a regular file at {source[:12]}: {relative_path}"
        )
    payload = _git(root, "cat-file", "blob", object_id)
    if payload.returncode != 0:
        raise ReceiptSealingError(
            f"cannot read sealed Git blob at {source[:12]}: {relative_path}"
        )
    return mode, object_id, payload.stdout


def _verify_current_receipt(
    root: Path,
    relative_path: str,
    source_mode: str,
    source_object: str,
    source_payload: bytes,
) -> None:
    """Require the current path and index entry to equal the introducing blob."""

    path = root / relative_path
    try:
        metadata = path.lstat()
        current_payload = path.read_bytes()
    except OSError as exc:
        raise ReceiptSealingError(f"cannot read current sealed receipt: {relative_path}") from exc
    if not stat.S_ISREG(metadata.st_mode) or path.is_symlink():
        raise ReceiptSealingError(f"current sealed receipt is not a regular file: {relative_path}")
    current_mode = "100755" if metadata.st_mode & 0o111 else "100644"
    if current_mode != source_mode:
        raise ReceiptSealingError(f"current sealed receipt mode differs: {relative_path}")
    if current_payload != source_payload:
        raise ReceiptSealingError(
            f"current sealed receipt differs from its introducing Git blob: {relative_path}"
        )

    index = _git(root, "ls-files", "--stage", "-z", "--", relative_path)
    if index.returncode != 0:
        raise ReceiptSealingError(f"cannot inspect current receipt index entry: {relative_path}")
    records = [record for record in index.stdout.split(b"\0") if record]
    if len(records) != 1:
        raise ReceiptSealingError(
            f"current receipt index entry is absent or conflicted: {relative_path}"
        )
    try:
        metadata_raw, encoded_path = records[0].split(b"\t", 1)
        index_mode, index_object, stage = metadata_raw.decode("ascii").split()
        listed_path = encoded_path.decode("utf-8")
    except (UnicodeDecodeError, ValueError) as exc:
        raise ReceiptSealingError(
            f"current receipt index entry is malformed: {relative_path}"
        ) from exc
    if (
        listed_path != relative_path
        or stage != "0"
        or index_mode != source_mode
        or index_object != source_object
    ):
        raise ReceiptSealingError(
            f"current receipt index entry differs from its introducing Git blob: {relative_path}"
        )


def verify_against_source(root: Path, receipt_path: Path) -> tuple[str, int]:
    """Validate a committed receipt's artifacts against its source commit's blobs.

    Returns ``(source_commit, evidence_count)``.  Raises when any bound artifact's bytes at
    that commit disagree with the digest the receipt recorded.
    """

    relative = receipt_path.relative_to(root).as_posix()
    source = introducing_commit(root, relative)
    if source is None:
        raise ReceiptSealingError(f"receipt is not committed: {relative}")

    source_mode, source_object, source_payload = _source_blob(root, source, relative)
    _verify_current_receipt(root, relative, source_mode, source_object, source_payload)
    receipt: dict[str, Any] = json.loads(source_payload.decode("utf-8"))

    for item in receipt.get("evidence", []):
        artifact = item["artifact"]
        path = artifact["path"]
        if path == relative:
            # The receipt cannot bind its own final bytes; that is self-referential.
            continue
        _, _, payload = _source_blob(root, source, path)
        if len(payload) != artifact["bytes"]:
            raise ReceiptSealingError(f"sealed artifact byte count differs: {path}")
        if hashlib.sha256(payload).hexdigest() != artifact["sha256"]:
            raise ReceiptSealingError(f"sealed artifact digest differs: {path}")

    return source, len(receipt.get("evidence", []))


def receipt_is_committed(root: Path, receipt_path: Path) -> bool:
    relative = receipt_path.relative_to(root).as_posix()
    return introducing_commit(root, relative) is not None
