#!/usr/bin/env python3
"""Documentation integrity guard.

This is a presentation guard, not a style preference. The repository should read
like an engineering record: links resolve, diagrams render, experiments surface,
and self-praise does not substitute for evidence.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.experiment_index import (
    ExperimentIndexError,
    INDEX,
    build_index,
    read_index,
)


FAILS: list[str] = []
ROOT = Path.cwd()
BANNED_SELF_PRAISE = [
    "brilliant",
    "world-class",
    "top-tier",
    "revolutionary",
    "game-changing",
    "mind-blowing",
]


def tracked_markdown() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "*.md"],
        capture_output=True,
        text=True,
        check=False,
    )
    tracked = set(result.stdout.split())
    discovered = {
        str(path.relative_to(ROOT))
        for path in ROOT.glob("**/*.md")
        if ".git" not in path.parts
        and ".pytest_cache" not in path.parts
        and ".ruff_cache" not in path.parts
    }
    return sorted(tracked | discovered)


def check_mermaid(path: str, src: str) -> None:
    for idx, block in enumerate(re.findall(r"```mermaid\n(.*?)```", src, re.S)):
        if len(block) >= 1100:
            FAILS.append(f"{path}: mermaid block {idx} is {len(block)} chars (budget 1100)")
        if "classDef" in block and "color:" not in block:
            FAILS.append(f"{path}: mermaid block {idx} has classDef without explicit color:")


def check_links(path: str, src: str) -> None:
    base = os.path.dirname(path)
    for _, target in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", src):
        if target.startswith(("http", "#", "mailto:")):
            continue
        clean_target = target.split("#")[0]
        if not clean_target:
            continue
        resolved = os.path.normpath(os.path.join(base, clean_target))
        if not os.path.exists(resolved):
            FAILS.append(f"{path}: broken link -> {target}")


def check_banned_language(path: str, src: str) -> None:
    lowered = src.lower()
    for phrase in BANNED_SELF_PRAISE:
        if phrase in lowered:
            FAILS.append(f"{path}: banned self-praise phrase -> {phrase}")


def check_experiment_surface() -> None:
    index = INDEX.relative_to(INDEX.parents[1])
    try:
        actual = read_index(INDEX.parents[1])
        expected = build_index(INDEX.parents[1])
    except ExperimentIndexError as error:
        FAILS.append(f"{index}: deterministic experiment inventory is unsafe: {error}")
        return
    if actual != expected:
        FAILS.append(f"{index}: deterministic experiment index differs")
    readme = Path("README.md").read_text(encoding="utf-8")
    if "docs/EXPERIMENT_INDEX.md" not in readme:
        FAILS.append("README.md: deterministic experiment index is not linked")


def main() -> int:
    for path in tracked_markdown():
        src = Path(path).read_text(encoding="utf-8", errors="replace")
        check_mermaid(path, src)
        check_links(path, src)
        check_banned_language(path, src)
    check_experiment_surface()

    if FAILS:
        print("DOCS GUARD FAILED:")
        for failure in FAILS:
            print(" -", failure)
        return 1

    print(f"docs guard: {len(tracked_markdown())} markdown files clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
