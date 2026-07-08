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
8. **Mission loop is explicit.** The public loop contract lives at `mission/loop.json`. Do not claim
   private Aweb/Maestro execution unless Aweb discovery returns a concrete Telos capability slug.

## Current Research Arc

This repo is separate from Sentinel. It keeps Sentinel's operating standard and changes the domain:
autonomous agent completion proof.

Current gate:

- `experiments/iter13_provider_model_pilot_retry_after_access_recovery/HYPOTHESIS.md`

Current claim:

- `iter00_target_survey` selected a hybrid Telos overlay on CodeClash + SWE-bench Verified.
- `iter01_receipt_dry_run` passed: valid receipt accepted, invalid receipt rejected, learning
  record validated.
- `iter02_public_task_slice` passed: selected a CodeClash-first no-LLM smoke slice with SWE-bench
  Verified receipt fields.
- `iter03_codeclash_smoke` passed: GitHub Actions ran the no-LLM CodeClash dummy tournament and
  produced a valid Telos receipt.
- `iter04_agent_behavior_slice` passed: selected the deterministic Mini-SWE-Agent BattleSnake PvP
  smoke as the first real agent-behavior run.
- `iter05_agent_behavior_smoke` passed: GitHub Actions ran the deterministic Mini-SWE-Agent
  BattleSnake PvP smoke and produced a valid, audited Telos receipt.
- `iter06_deterministic_edit_slice` passed: selected a CodeClash overlay that should produce a
  non-empty `telos_marker.py` diff through the Mini-SWE-Agent path at zero provider cost.
- `iter07_deterministic_edit_smoke` passed: GitHub Actions ran the deterministic Mini-SWE-Agent
  edit smoke, captured a non-empty `p1` diff creating `telos_marker.py`, and produced a valid,
  audited Telos receipt.
- `iter08_provider_model_pilot_slice` passed: selected a local-first Google Vertex AI
  `gemini-3.1-pro-preview-customtools` CodeClash pilot with a $25 ceiling and no model-result
  claim.
- `iter09_provider_model_pilot_smoke` blocked before spend: ADC token refresh required
  interactive reauthentication, so no paid model call or CodeClash provider run occurred.
- `iter10_provider_auth_recovery` passed: local ADC refresh now succeeds with token output
  suppressed, required Google services are visible by service name, and no credential material or
  project/account identifier is committed.
- `iter11_provider_model_pilot_retry` blocked: an ephemeral GCE runner executed the frozen
  CodeClash path and reached Vertex, but the selected `gemini-3.1-pro-preview-customtools` model
  path returned `aiplatform.endpoints.predict` permission denial until the run hit the 45-minute
  ceiling. No provider trajectory, cost, or API-call stats are claimed.
- `iter12_vertex_model_access_recovery` passed: a dedicated Telos runner identity reached the
  original Vertex custom-tools endpoint from an ephemeral GCE VM through metadata credentials,
  returned HTTP `200` with one candidate and usage metadata, deleted the probe VM, and kept the
  original model selection.
- No model or benchmark result is claimed yet.
- The next gate must run the provider smoke on the dedicated Telos runner identity or publish
  blocked/null evidence.

## Required Verification

Run before and after material changes:

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
python3 scripts/validate_receipts.py experiments/iter09_provider_model_pilot_smoke/proof
python3 scripts/audit_provider_model_pilot_smoke.py
python3 scripts/validate_receipts.py experiments/iter10_provider_auth_recovery/proof
python3 scripts/audit_provider_auth_recovery.py
python3 scripts/validate_receipts.py experiments/iter11_provider_model_pilot_retry/proof
python3 scripts/audit_provider_model_pilot_retry.py
python3 scripts/validate_receipts.py experiments/iter12_vertex_model_access_recovery/proof
python3 scripts/audit_vertex_model_access_recovery.py
python3 scripts/validate_learning_ledger.py
python3 scripts/validate_json.py
python3 scripts/validate_handoff.py
python3 scripts/make_handoff.py
```

If `make_handoff.py` changes `HANDOFF.md`, commit that change with the state change that caused it.

## Handoff Rule

Before stopping:

1. Commit or clearly leave the work uncommitted with a reason.
2. Regenerate `HANDOFF.md`.
3. State whether any experiment is in flight.
4. Never imply a result exists before `RESULT.md` and proof artifacts exist.
