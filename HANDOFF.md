# HANDOFF - dynamic state snapshot

Generated: 2026-07-08T11:29:37Z by `scripts/make_handoff.py`. Read `CONTINUITY.md` first.

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
- experiments/iter03_codeclash_smoke: RESULT PUBLISHED
- experiments/iter04_agent_behavior_slice: RESULT PUBLISHED
- experiments/iter05_agent_behavior_smoke: RESULT PUBLISHED
- experiments/iter06_deterministic_edit_slice: RESULT PUBLISHED
- experiments/iter07_deterministic_edit_smoke: RESULT PUBLISHED
- experiments/iter08_provider_model_pilot_slice: RESULT PUBLISHED
- experiments/iter09_provider_model_pilot_smoke: PRE-REGISTERED, result pending

## Current Gate

- Active gate: `experiments/iter09_provider_model_pilot_smoke/HYPOTHESIS.md`.
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
