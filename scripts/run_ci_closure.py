#!/usr/bin/env python3
"""Run every guard command that CI declares, derived from the workflow itself.

Iter219 sealed and published a tip whose CI failed on a guard its local closure never ran.
The local list had been written from memory and contained roughly seven commands; the
workflow declares more than two hundred and fifty.  A verification set chosen by the same
agent that wrote the change is not an independent check — it is Standard 9 in miniature,
where a gate passes against one's own idea of the gate instead of the real one.

This runner never hard-codes a command.  It parses ``.github/workflows/ci.yml`` and
executes exactly what that workflow runs, honouring the ``env -u NAME VAR=value`` prefixes
the workflow uses to strip credentials and force provider-free reuse.  If CI gains a guard,
this gains it too, with no edit here.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/ci.yml"

# Steps whose work is not a repository guard: dependency installation and the clean-tree
# assertion, which is meaningful only after a commit.
SKIP_STEP_NAMES = {
    "Install verification tools",
    "Full clean-tree guard",
}


def declared_commands(workflow: Path = WORKFLOW) -> list[tuple[str, str]]:
    """Return (step name, shell command) for every runnable guard CI declares."""

    document = yaml.safe_load(workflow.read_text(encoding="utf-8"))
    steps = document["jobs"]["verify"]["steps"]
    commands: list[tuple[str, str]] = []
    for step in steps:
        name = step.get("name", "")
        script = step.get("run")
        if not script or name in SKIP_STEP_NAMES:
            continue
        # Join backslash continuations so `env -u KEY VAR=1 \\\n python3 x.py` stays one
        # command with its environment overrides intact.
        joined = script.replace("\\\n", " ")
        for line in joined.splitlines():
            line = line.strip()
            if line:
                commands.append((name, line))
    return commands


def run(commands: list[tuple[str, str]], *, stop_early: bool = False) -> list[tuple[str, str, str]]:
    failures: list[tuple[str, str, str]] = []
    total = len(commands)
    for index, (name, command) in enumerate(commands, start=1):
        result = subprocess.run(
            command, shell=True, cwd=ROOT, capture_output=True, text=True
        )
        if result.returncode != 0:
            output = (result.stdout + result.stderr).strip()
            failures.append((name, command, output[-600:]))
            print(f"[{index}/{total}] FAIL {name}", flush=True)
            if stop_early:
                break
        elif index % 25 == 0:
            print(f"[{index}/{total}] ok", flush=True)
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--list", action="store_true", help="print the derived command list and exit"
    )
    parser.add_argument(
        "--stop-early", action="store_true", help="stop at the first failing guard"
    )
    args = parser.parse_args()

    commands = declared_commands()
    if args.list:
        for name, command in commands:
            print(f"{name}\t{command}")
        print(f"\n{len(commands)} commands declared by {WORKFLOW.relative_to(ROOT)}")
        return 0

    print(f"running {len(commands)} guard commands declared by CI", flush=True)
    failures = run(commands, stop_early=args.stop_early)
    if failures:
        print(f"\nCI CLOSURE FAILED: {len(failures)} command(s)\n")
        for name, command, output in failures:
            print(f"--- {name}")
            print(f"    $ {command}")
            print(output)
            print()
        return 1
    print(f"\nCI closure clean: {len(commands)} commands pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
