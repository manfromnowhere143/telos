#!/usr/bin/env python3
"""Iter232 stage B - execute only an exercise's import statements inside its pinned container.

An exercise that cannot import in the environment it will run in is not an instrument. Iter231 shipped two
such exercises, and both surfaced only as a flag in the final result, where an import failure is
indistinguishable from the patched code crashing.

This probe extracts every import/from-import statement from the committed exercise, in source order, and
executes just those. Nothing else in the exercise runs, so the probe cannot produce an observation and cannot
influence the oracle's measurement. It prints exactly one PREFLIGHT= line.

COMPATIBILITY IS A HARD REQUIREMENT, NOT A STYLE CHOICE. This file runs inside SWE-bench images whose pinned
interpreters span many Python versions; the oldest in this benchmark is 3.6. The first version of this probe
used `from __future__ import annotations` (3.7+) and died with SyntaxError on three rows, which the executor
correctly reported as missing stage B evidence. So, deliberately:

  * no `from __future__ import annotations`;
  * no f-strings;
  * no variable or parameter annotations;
  * no `ast.Module(type_ignores=...)`, which is 3.8+ - an empty parsed module is mutated instead;
  * no %-formatting anywhere, since mis-specified %-formats are the exact defect class iter232 exists to
    remove and this file must not model the bug it guards against.

This is harness code, not a generated exercise: it is committed, reviewed, and mounted read-only, so it is
not subject to the exercise safety instrument.
"""

import ast
import sys


def emit(payload):
    """One PREFLIGHT= line, built by repr() rather than any format string."""

    sys.stdout.write("PREFLIGHT=" + repr(payload) + "\n")
    sys.stdout.flush()


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/telos/exercise.py"
    try:
        handle = open(path)
        try:
            source = handle.read()
        finally:
            handle.close()
    except Exception as exc:
        emit(("ERROR", "unreadable", str(exc)[:80]))
        return 1

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        emit(("ERROR", "SyntaxError", str(exc)[:80]))
        return 1

    statements = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    # Source order, not walk order: an alias bound by an earlier import may be used by a later one.
    statements.sort(key=lambda node: (node.lineno, node.col_offset))
    if not statements:
        emit(("OK", 0))
        return 0

    # Build a module without naming ast.Module's version-dependent fields.
    module = ast.parse("")
    module.body = statements
    try:
        code = compile(ast.fix_missing_locations(module), "<iter232-imports>", "exec")
    except Exception as exc:
        emit(("ERROR", type(exc).__name__, str(exc)[:80]))
        return 1

    try:
        exec(code, {"__name__": "__iter232_probe__"})
    except BaseException as exc:
        emit(("ERROR", type(exc).__name__, str(exc)[:120]))
        return 1
    emit(("OK", len(statements)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
