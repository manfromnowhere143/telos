#!/usr/bin/env python3
"""Deterministically render or write the iter202 runtime-freeze manifest."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.validate_iter202_runtime_freeze import (  # noqa: E402
    MANIFEST,
    RuntimeFreezeError,
    build_manifest,
    rendered_manifest_bytes,
    sha256,
    validate_committed_manifest,
)


def atomic_write(path: Path, payload: bytes) -> None:
    """Replace ``path`` only after its complete bytes are flushed to disk."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            errors = validate_committed_manifest()
            if errors:
                for error in errors:
                    print(f"iter202 runtime freeze error: {error}", file=sys.stderr)
                return 1
            print(
                "iter202 runtime manifest reproduces: "
                f"sha256={sha256(MANIFEST.read_bytes())}"
            )
            return 0
        payload = rendered_manifest_bytes(build_manifest())
        if args.write:
            atomic_write(MANIFEST, payload)
            print(
                f"wrote {MANIFEST.relative_to(ROOT)}; sha256={sha256(payload)}"
            )
        else:
            sys.stdout.buffer.write(payload)
        return 0
    except RuntimeFreezeError as exc:
        print(f"iter202 runtime freeze error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
