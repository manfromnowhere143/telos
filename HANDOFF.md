# HANDOFF - dynamic state snapshot

Generated: 2026-07-08T09:28:20Z by `scripts/make_handoff.py`. Read `CONTINUITY.md` first.

## Repository State

```text
branch: master
```

Working tree:

```text
clean
```

## Experiments

- experiments/iter00_target_survey: PRE-REGISTERED, result pending

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
