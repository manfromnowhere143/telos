#!/usr/bin/env python3
"""Generate HANDOFF.md from current repository state."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import re
import subprocess


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


def active_gate() -> str:
    continuity = Path("CONTINUITY.md").read_text(encoding="utf-8")
    match = re.search(r"Current gate:\n\n- `([^`]+)`", continuity)
    if match:
        return match.group(1)
    return "experiments/iter03_codeclash_smoke/HYPOTHESIS.md"


def main() -> None:
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"]) or "git branch unavailable"
    status = run(["git", "status", "--short"]) or "clean"
    rows = "\n".join(experiment_status()) or "- no experiments yet"
    gate = active_gate()
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

- Active gate: `{gate}`.
- No benchmark result is claimed yet.
- Next action: run the active gate exactly as pre-registered, then publish `RESULT.md` with
  proof artifacts before advancing scope.

## Verification Before Action

Run:

```bash
ruff check .
pytest -q
python3 scripts/validate_docs.py
python3 scripts/validate_mission_loop.py
python3 scripts/validate_target_survey.py
python3 scripts/validate_public_slice.py
python3 scripts/validate_agent_behavior_slice.py
python3 scripts/validate_deterministic_edit_slice.py
python3 scripts/validate_provider_model_pilot_slice.py
python3 scripts/validate_receipts.py experiments/iter01_receipt_dry_run/proof
python3 scripts/validate_receipts.py experiments/iter03_codeclash_smoke/proof
python3 scripts/audit_codeclash_smoke.py
python3 scripts/validate_receipts.py experiments/iter05_agent_behavior_smoke/proof
python3 scripts/audit_agent_behavior_smoke.py
python3 scripts/validate_receipts.py experiments/iter07_deterministic_edit_smoke/proof
python3 scripts/audit_deterministic_edit_smoke.py
python3 scripts/validate_learning_ledger.py
python3 scripts/validate_json.py
python3 scripts/validate_handoff.py
python3 scripts/make_handoff.py
```
"""
    Path("HANDOFF.md").write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
