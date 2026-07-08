# Iteration 01 - Receipt Dry Run

Status: pre-registered, result pending.

## Purpose

Validate the Telos receipt protocol before any public benchmark or model-capability claim.

This is an infrastructure experiment. It asks whether the proof receipt can be produced,
validated, rejected when malformed, and recorded in the learning ledger.

## Hypothesis

The receipt validator and learning ledger can support the first Telos proof loop:

1. one valid receipt passes,
2. one deliberately invalid receipt fails,
3. the experiment record links to its proof artifacts,
4. the learning ledger extracts a next action from the result,
5. all checks stay green.

## Bars

The gate passes only if all hold:

- `python3 scripts/validate_receipts.py experiments/iter01_receipt_dry_run/proof` exits 0,
- the invalid receipt is tested and rejected by unit test or proof script,
- `pytest -q` passes,
- `python3 scripts/validate_docs.py` passes,
- `python3 scripts/validate_target_survey.py` passes,
- `HANDOFF.md` is regenerated.

## Falsifiers

Publish a null and stop if:

- receipt validation depends on trusting final-answer text,
- a missing evidence field passes,
- a bad `sha256` passes,
- the result cannot name a concrete next action,
- the repository cannot stay handoff-clean after the run.

## Scope Boundary

No model is evaluated. No CodeClash, SWE-bench, RE-Bench, tau-bench, or AgentDojo score is claimed.
This gate exists so the first public-task experiment does not discover basic protocol failures late.
