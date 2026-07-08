# HANDOFF - dynamic state snapshot

Generated: 2026-07-08T10:12:28Z by `scripts/make_handoff.py`. Read `CONTINUITY.md` first.

## Repository State

```text
branch: master
```

Working tree:

```text
clean
```

## Experiments

- experiments/iter00_target_survey: RESULT PUBLISHED
- experiments/iter01_receipt_dry_run: RESULT PUBLISHED
- experiments/iter02_public_task_slice: RESULT PUBLISHED
- experiments/iter03_codeclash_smoke: PRE-REGISTERED, result pending

## Current Gate

- Active gate: `experiments/iter03_codeclash_smoke/HYPOTHESIS.md`.
- No benchmark result is claimed yet.
- Next action: run the no-LLM CodeClash smoke exactly as pre-registered, then publish
  `RESULT.md` with logs and a receipt under `experiments/iter03_codeclash_smoke/proof/`.

## Verification Before Action

Run:

```bash
ruff check .
pytest -q
python3 scripts/validate_docs.py
python3 scripts/validate_target_survey.py
python3 scripts/validate_public_slice.py
python3 scripts/validate_receipts.py experiments/iter01_receipt_dry_run/proof
python3 scripts/validate_learning_ledger.py
python3 scripts/validate_json.py
python3 scripts/validate_handoff.py
python3 scripts/make_handoff.py
```
