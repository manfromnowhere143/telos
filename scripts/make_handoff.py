#!/usr/bin/env python3
"""Generate HANDOFF.md from current repository state."""

from __future__ import annotations

from datetime import UTC, datetime
import subprocess
from pathlib import Path


def run(args: list[str]) -> str:
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    text = result.stdout.strip()
    if not text and result.stderr.strip():
        text = result.stderr.strip()
    return text


def experiment_status() -> list[str]:
    rows = []
    for path in sorted(Path("experiments").glob("*/")):
        if (path / "RESULT.md").exists():
            status = "RESULT PUBLISHED"
        elif (path / "HYPOTHESIS.md").exists():
            status = "PRE-REGISTERED, result pending"
        else:
            status = "artifacts only"
        rows.append(f"- {path.as_posix().rstrip('/')}: {status}")
    return rows


def main() -> None:
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"]) or "git branch unavailable"
    status = run(["git", "status", "--short"]) or "clean"
    rows = "\n".join(experiment_status()) or "- no experiments yet"
    content = f"""# HANDOFF - dynamic state snapshot

Generated: {now} by `scripts/make_handoff.py`. Read `CONTINUITY.md` first.

## Repository State

```text
branch: {branch}
```

Working tree:

```text
{status}
```

## Experiments

{rows}

## Current Gate

- Active gate: `experiments/iter00_target_survey/HYPOTHESIS.md`.
- No benchmark result is claimed yet.
- Next action: run the target survey exactly as frozen, then publish `RESULT.md` with source
  receipts under `experiments/iter00_target_survey/proof/`.

## Verification Before Action

Run:

```bash
ruff check .
pytest -q
python3 scripts/validate_docs.py
python3 scripts/validate_target_survey.py
python3 scripts/make_handoff.py
```
"""
    Path("HANDOFF.md").write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
