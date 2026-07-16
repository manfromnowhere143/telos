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


def verify_against_source(root: Path, receipt_path: Path) -> tuple[str, int]:
    """Validate a committed receipt's artifacts against its source commit's blobs.

    Returns ``(source_commit, evidence_count)``.  Raises when any bound artifact's bytes at
    that commit disagree with the digest the receipt recorded.
    """

    relative = receipt_path.relative_to(root).as_posix()
    source = introducing_commit(root, relative)
    if source is None:
        raise ReceiptSealingError(f"receipt is not committed: {relative}")

    blob = _git(root, "show", f"{source}:{relative}")
    if blob.returncode != 0:
        raise ReceiptSealingError(f"cannot read sealed receipt at {source[:12]}: {relative}")
    receipt: dict[str, Any] = json.loads(blob.stdout.decode("utf-8"))

    for item in receipt.get("evidence", []):
        artifact = item["artifact"]
        path = artifact["path"]
        if path == relative:
            # The receipt cannot bind its own final bytes; that is self-referential.
            continue
        payload = _git(root, "show", f"{source}:{path}")
        if payload.returncode != 0:
            raise ReceiptSealingError(f"sealed artifact absent at {source[:12]}: {path}")
        if len(payload.stdout) != artifact["bytes"]:
            raise ReceiptSealingError(f"sealed artifact byte count differs: {path}")
        if hashlib.sha256(payload.stdout).hexdigest() != artifact["sha256"]:
            raise ReceiptSealingError(f"sealed artifact digest differs: {path}")

    return source, len(receipt.get("evidence", []))


def receipt_is_committed(root: Path, receipt_path: Path) -> bool:
    relative = receipt_path.relative_to(root).as_posix()
    return introducing_commit(root, relative) is not None
