# Continuity

Read this file before changing the repository. It carries the stable operating rules; `HANDOFF.md`
carries the dynamic state.

## Standard

1. **Pre-register before data.** Every experiment gets a `HYPOTHESIS.md` with numeric bars and
   named falsifiers before any result.
2. **Nulls publish at full weight.** A failed gate is a result, not a footnote.
3. **Evidence or it did not happen.** Every number in a result must regenerate from committed
   proof artifacts or cited public sources.
4. **No inflated language.** Confidence comes from receipts, not adjectives.
5. **Corrections stay visible.** If a claim is wrong, correct it in place and explain the reason.
6. **Cheap-first.** Offline gates run before API spend, GPU spend, or long harness runs.
7. **One operator at a time.** Keep the repo handoff-ready after every state change.

## Current Research Arc

This repo is separate from Sentinel. It keeps Sentinel's operating standard and changes the domain:
autonomous agent completion proof.

Current gate:

- `experiments/iter00_target_survey/HYPOTHESIS.md`

Current claim:

- No benchmark result is claimed yet.
- The only frozen claim is that target selection must be evidence-scored before the first Telos
  experiment.

## Required Verification

Run before and after material changes:

```bash
ruff check .
pytest -q
python3 scripts/validate_docs.py
python3 scripts/validate_target_survey.py
python3 scripts/make_handoff.py
```

If `make_handoff.py` changes `HANDOFF.md`, commit that change with the state change that caused it.

## Handoff Rule

Before stopping:

1. Commit or clearly leave the work uncommitted with a reason.
2. Regenerate `HANDOFF.md`.
3. State whether any experiment is in flight.
4. Never imply a result exists before `RESULT.md` and proof artifacts exist.
