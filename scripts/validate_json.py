#!/usr/bin/env python3
"""Validate every repository JSON file parses cleanly."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path.cwd()


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject ambiguous JSON objects instead of silently accepting the last duplicate key."""

    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate object key: {key!r}")
        result[key] = value
    return result


def reject_nonfinite_constant(value: str) -> object:
    """Reject Python's non-standard NaN and infinity JSON extensions."""

    raise ValueError(f"non-finite JSON constant: {value}")


def load_strict_json(path: Path) -> object:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=reject_nonfinite_constant,
    )


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
            load_strict_json(path)
        except (json.JSONDecodeError, ValueError) as exc:
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
