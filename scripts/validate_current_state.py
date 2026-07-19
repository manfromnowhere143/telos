#!/usr/bin/env python3
"""Validate Telos's mutable current-state pointer against its public surfaces.

The large ``mission/loop.json`` and root ``HANDOFF.md`` are sealed historical
evidence. This guard deliberately does not reinterpret or rewrite them. It
checks the small mutable pointer that a new session reads first and fails when
that pointer, AGENTS bootstrap, README, dated handoff, audit, active gate, or
paper revision disagree.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CURRENT = Path("mission/current.json")
AGENTS = Path("AGENTS.md")
README = Path("README.md")
PAPER = Path("paper/telos.tex")

ALLOWED_STATUSES = {
    "proposed",
    "exploratory",
    "preregistered",
    "running",
    "blocked",
    "invalid",
    "null",
    "inconclusive",
    "failed",
    "supported",
    "contradicted",
    "replicated",
    "corrected",
    "retracted",
}
HISTORICAL_SURFACES = ["HANDOFF.md", "mission/loop.json"]


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("current pointer must be a JSON object")
    return value


def _relative_file(root: Path, value: object, field: str) -> tuple[Path | None, str | None]:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        return None, f"{field} must be a non-empty repository-relative path"
    path = root / value
    if not path.is_file():
        return None, f"{field} does not name a file: {value}"
    return path, None


def validate(*, root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    try:
        current = _read_json(root / CURRENT)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        return [f"current pointer is unreadable: {error}"]

    if current.get("schema_version") != "telos.current.v1":
        failures.append("current pointer schema differs")
    updated = current.get("updated")
    if not isinstance(updated, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", updated) is None:
        failures.append("updated must be an ISO calendar date")
    if current.get("status") not in ALLOWED_STATUSES:
        failures.append("status is not an allowed research status")
    if current.get("historical_surfaces") != HISTORICAL_SURFACES:
        failures.append("sealed historical surfaces are not identified exactly")

    bound_paths: dict[str, tuple[Path | None, str | None]] = {}
    for field in ("active_gate", "current_handoff", "current_audit"):
        bound_paths[field] = _relative_file(root, current.get(field), field)
        if bound_paths[field][1]:
            failures.append(bound_paths[field][1] or "")

    active_gate = current.get("active_gate")
    if isinstance(active_gate, str) and not re.fullmatch(
        r"experiments/iter\d+_[^/]+/HYPOTHESIS\.md", active_gate
    ):
        failures.append("active_gate is not an iteration hypothesis")

    for field in ("scientific_status", "next_authorized_action", "claim_boundary"):
        value = current.get(field)
        if not isinstance(value, str) or not value.strip():
            failures.append(f"{field} must be a non-empty string")

    paper_revision = current.get("paper_revision")
    if not isinstance(paper_revision, str) or not paper_revision:
        failures.append("paper_revision must be a non-empty date label")

    try:
        agents = (root / AGENTS).read_text(encoding="utf-8")
        readme = (root / README).read_text(encoding="utf-8")
        paper = (root / PAPER).read_text(encoding="utf-8")
    except OSError as error:
        failures.append(f"current public surface is unreadable: {error}")
        return failures

    if "mission/current.json" not in agents:
        failures.append("AGENTS bootstrap does not read mission/current.json")
    if "`current_handoff`" not in agents:
        failures.append("AGENTS bootstrap does not follow the pointer's current_handoff")
    for sealed in HISTORICAL_SURFACES:
        if sealed not in agents or "historical" not in agents:
            failures.append(f"AGENTS does not identify {sealed} as historical")

    for field in ("active_gate", "current_handoff", "current_audit"):
        value = current.get(field)
        if isinstance(value, str) and value not in readme:
            failures.append(f"README does not bind {field}: {value}")

    if isinstance(paper_revision, str) and f"\\date{{{paper_revision}}}" not in paper:
        failures.append("paper revision does not match mission/current.json")

    handoff_path = bound_paths.get("current_handoff", (None, None))[0]
    if handoff_path is not None:
        handoff = handoff_path.read_text(encoding="utf-8")
        for field in (
            "active_gate",
            "current_audit",
            "scientific_status",
            "next_authorized_action",
        ):
            value = current.get(field)
            if isinstance(value, str) and value not in handoff:
                failures.append(f"current handoff does not bind {field}")

    return failures


def main() -> int:
    failures = validate()
    if failures:
        for failure in failures:
            print(f"current-state: {failure}")
        return 1
    print("current-state pointer, bootstrap, handoff, audit, README, and paper agree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
