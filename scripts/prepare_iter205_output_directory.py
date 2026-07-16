#!/usr/bin/env python3
"""Create one empty iter205 output directory without following symlinks."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


class OutputDirectoryError(ValueError):
    """The requested output directory is unsafe or not empty."""


def prepare(path: Path, *, require_new: bool) -> None:
    if path.is_absolute() or not path.parts or any(
        part in {"", ".", ".."} for part in path.parts
    ):
        raise OutputDirectoryError("output path must be a normalized relative path")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor = os.open(".", flags)
    try:
        for index, part in enumerate(path.parts):
            leaf = index == len(path.parts) - 1
            existed = True
            try:
                child = os.open(part, flags, dir_fd=descriptor)
            except FileNotFoundError:
                existed = False
                try:
                    os.mkdir(part, 0o755, dir_fd=descriptor)
                    child = os.open(part, flags, dir_fd=descriptor)
                except OSError as exc:
                    raise OutputDirectoryError(
                        f"cannot create safe output component: {part!r}"
                    ) from exc
            except OSError as exc:
                raise OutputDirectoryError(
                    f"output component is not a real directory: {part!r}"
                ) from exc
            os.close(descriptor)
            descriptor = child
            if leaf and require_new and existed:
                raise OutputDirectoryError("output directory already exists")
        try:
            entries = os.listdir(descriptor)
        except OSError as exc:
            raise OutputDirectoryError("cannot inspect output directory") from exc
        if entries:
            raise OutputDirectoryError("output directory is not empty")
    finally:
        os.close(descriptor)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--new", action="store_true")
    mode.add_argument("--empty", action="store_true")
    args = parser.parse_args()
    try:
        prepare(args.path, require_new=args.new)
    except (OSError, OutputDirectoryError) as exc:
        print(f"iter205 output-directory error: {exc}", file=sys.stderr)
        return 2
    print(f"iter205 safe empty output directory: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
