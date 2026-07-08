#!/usr/bin/env python3
"""Validate every repository JSON file parses cleanly."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path.cwd()


def main() -> int:
    failures: list[str] = []
    paths = [
        path
        for path in ROOT.glob("**/*.json")
        if ".git" not in path.parts
        and ".pytest_cache" not in path.parts
        and ".ruff_cache" not in path.parts
    ]
    for path in sorted(paths):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"{path}: {exc}")

    if failures:
        print("json guard failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print(f"json guard: {len(paths)} files clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
