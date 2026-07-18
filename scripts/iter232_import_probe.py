#!/usr/bin/env python3
"""Iter232 stage B — execute only an exercise's import statements inside its pinned container.

An exercise that cannot import in the environment it will run in is not an instrument. Iter231 shipped two
such exercises, and both surfaced only as a flag in the final result, where an import failure is
indistinguishable from the patched code crashing.

This probe extracts every ``import``/``from ... import`` statement from the committed exercise, in source
order, and executes just those. Nothing else in the exercise runs, so the probe cannot produce an
observation and cannot influence the oracle's measurement. It prints exactly one ``PREFLIGHT=`` line.

This is harness code, not a generated exercise: it is committed, reviewed, and mounted read-only, so it is
not subject to the exercise safety instrument.
"""

from __future__ import annotations

import ast
import sys


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "/telos/exercise.py"
    try:
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
    except OSError as exc:
        print(f"PREFLIGHT={('ERROR', 'unreadable', str(exc)[:80])!r}")
        return 1
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        print(f"PREFLIGHT={('ERROR', 'SyntaxError', str(exc)[:80])!r}")
        return 1

    # Source order, not walk order: an alias bound by an earlier import may be referenced by a later one.
    statements = sorted(
        (node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))),
        key=lambda node: (node.lineno, node.col_offset),
    )
    if not statements:
        print(f"PREFLIGHT={('OK', 0)!r}")
        return 0

    module = ast.Module(body=list(statements), type_ignores=[])
    try:
        code = compile(ast.fix_missing_locations(module), "<iter232-imports>", "exec")
    except (SyntaxError, ValueError) as exc:
        print(f"PREFLIGHT={('ERROR', type(exc).__name__, str(exc)[:80])!r}")
        return 1
    try:
        exec(code, {"__name__": "__iter232_probe__"})  # noqa: S102 — the point of the probe
    except BaseException as exc:  # noqa: BLE001 — any failure to import is the finding
        print(f"PREFLIGHT={('ERROR', type(exc).__name__, str(exc)[:120])!r}")
        return 1
    print(f"PREFLIGHT={('OK', len(statements))!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
