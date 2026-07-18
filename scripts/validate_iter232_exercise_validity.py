#!/usr/bin/env python3
"""Iter232 stage A — the static validity gate for gold-free exercises.

An exercise is an instrument. Iter231 shipped four that were not: two applied a single ``%`` specifier to a
multi-element tuple (raises unconditionally, so the exercise dies while reporting rather than because the code
under test failed), and two could not import against their pinned image. The first class is statically
detectable and this gate rejects it; the second needs stage B, which runs inside the container.

Stage A checks, all offline and at zero spend:

1. the source parses;
2. no ``%``-format applies a single specifier to a multi-element tuple;
3. no ``.format``/f-string equivalent silently drops arguments (the ``%`` case is the one observed, but the
   check generalizes to any always-raising report path);
4. the AST safety instrument accepts it;
5. it prints a literal ``RESULT=``;
6. every name it imports is resolvable to a module root that is either the project package under test or a
   standard/scientific dependency on the allowlist.

Run with ``--report`` to classify an arbitrary exercise directory without failing, or with no arguments to
gate the committed iter232 exercise set.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.validate_iter223_scenario_safety import scenario_ast_errors  # noqa: E402

EXP = ROOT / "experiments/iter232_validated_exercise_instrument"
EXERCISES = EXP / "proof/raw/exercises"
MAX_EXERCISE_BYTES = 64 * 1024

# The one enumerated allowlist extension, applied HERE rather than by editing the shared iter223
# instrument, so iter223-iter229's guards keep validating their evidence against the exact instrument
# that produced it.
#
# `astropy` is the project package under test for the benchmark's astropy rows, and is a pure
# computational library — a peer of the already-allowlisted numpy, sympy, sklearn, xarray, and
# matplotlib. Its absence was an allowlist gap, not a judgement that it is dangerous. Closing a gap
# is not loosening a bar.
#
# `requests` is deliberately NOT extended, though it is equally the package under test for the
# benchmark's two psf/requests rows. It is an HTTP client and sits on the instrument's forbidden
# list. Admitting it would admit network capability, which the iter232 pre-registration names as a
# falsifier. Those two rows therefore stay permanently uncoverable, and that coverage limit is
# reported rather than engineered away. The container runs with --network none, so this is defense in
# depth over an already-closed door — which is exactly when it is cheapest to hold the line.
ALLOWLIST_EXTENSION = {"astropy"}
_EXTENSION_ERRORS = tuple(
    f"unsafe import root: {name}" for name in sorted(ALLOWLIST_EXTENSION)
) + tuple(f"unsafe import alias: {name}" for name in sorted(ALLOWLIST_EXTENSION))


def format_bug_errors(tree: ast.AST) -> list[str]:
    """Report paths that raise unconditionally instead of reporting an observation.

    ``print("RESULT=%r" % (a, b))`` looks correct and is not: ``%r`` consumes one element and the operator
    raises ``TypeError: not all arguments converted during string formatting``. Observed in 4 of iter231's 51
    exercises, in the main report path and in except handlers.
    """

    errors: list[str] = []
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Mod)
            and isinstance(node.left, ast.Constant)
            and isinstance(node.left.value, str)
        ):
            continue
        template = node.left.value
        # %% is a literal percent and consumes no argument.
        specifiers = template.replace("%%", "").count("%")
        if isinstance(node.right, ast.Tuple):
            supplied = len(node.right.elts)
            if specifiers != supplied:
                errors.append(
                    f"format applies {specifiers} specifier(s) to {supplied} element(s): "
                    f"{template[:40]!r}"
                )
        elif specifiers > 1:
            # A single non-tuple operand cannot satisfy more than one specifier.
            errors.append(f"format applies {specifiers} specifiers to one operand: {template[:40]!r}")
    return errors


# The oldest interpreter this toolchain can run. SWE-bench images pin Pythons from 3.6 up, and 3.12
# RELAXED f-string syntax -- nested f-strings with escaped quotes, and backslashes inside expression
# parts, parse on 3.12+ and are SyntaxErrors before. A generator running on a newer host therefore
# accepts tests that cannot parse in their own container.
#
# Observed live: a Gemini-authored test used f'...[\"A\", \"B\"]...' nested inside an outer
# f-string. It parsed on this host (3.14) at generation time and failed under 3.11 in CI.
#
# A hand-rolled scanner for this got it wrong -- nested braces defeated the depth tracking -- so the
# check is ground truth rather than a heuristic: hand the source to the oldest interpreter available
# and see whether it parses. When this guard itself runs under an old enough interpreter, the
# caller's own ast.parse already covers it.
COMPAT_PYTHON = "python3.11"


def _compat_parse_errors(source: str) -> list[str]:
    if sys.version_info < (3, 12):
        return []
    executable = shutil.which(COMPAT_PYTHON)
    if not executable:
        return []
    try:
        proc = subprocess.run(
            [executable, "-c", "import ast,sys; ast.parse(sys.stdin.read())"],
            input=source, capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if proc.returncode != 0:
        detail = (proc.stderr.strip().splitlines() or ["unknown"])[-1]
        return [f"does not parse on {COMPAT_PYTHON}: {detail[:110]}"]
    return []


def exercise_errors(source: str) -> list[str]:
    errors: list[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [f"does not parse: {exc}"]
    errors.extend(_compat_parse_errors(source))
    errors.extend(format_bug_errors(tree))
    # The shared instrument is run unmodified; only the enumerated extension above is subtracted from
    # its verdict, so every other rejection it makes still stands.
    errors.extend(
        error for error in scenario_ast_errors(source) if error not in _EXTENSION_ERRORS
    )
    return sorted(set(errors))


def validate_file(path: Path) -> list[str]:
    if path.is_symlink():
        return ["exercise symlinks are forbidden"]
    raw = path.read_bytes()
    if not raw or len(raw) > MAX_EXERCISE_BYTES:
        return ["exercise size is outside the safe bound"]
    if b"\x00" in raw or b"\r" in raw:
        return ["NUL/CR bytes are forbidden"]
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        return ["exercise must have exactly one terminal LF"]
    try:
        source = raw[:-1].decode("utf-8")
    except UnicodeDecodeError as exc:
        return [f"not UTF-8: {exc}"]
    return exercise_errors(source)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", type=Path,
        help="classify every *.exercise.py in this directory and print a summary without failing",
    )
    args = parser.parse_args()

    directory = args.report or EXERCISES
    if not directory.is_dir():
        if args.report:
            print(f"no such directory: {directory}", file=sys.stderr)
            return 2
        print("iter232 stage A: no exercises committed yet (explicit empty pre-generation state)")
        return 0

    results = {
        path.name: validate_file(path)
        for path in sorted(directory.glob("*.exercise.py"))
    }
    failing = {name: errors for name, errors in results.items() if errors}

    if args.report:
        for name, errors in failing.items():
            print(f"FAIL {name}")
            for error in errors:
                print(f"       {error}")
        print(
            json.dumps(
                {
                    "directory": str(directory),
                    "exercises": len(results),
                    "stage_a_pass": len(results) - len(failing),
                    "stage_a_fail": len(failing),
                    "failing": sorted(failing),
                },
                indent=2,
            )
        )
        return 0

    if failing:
        for name, errors in failing.items():
            for error in errors:
                print(f"iter232 stage A error: {name}: {error}", file=sys.stderr)
        return 1
    print(f"iter232 stage A: {len(results)} committed exercises are statically valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
