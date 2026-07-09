# Iteration 74 - Provider-Compatible Expanded Paid Retry After Receipt Prompt Recovery

Status: pre-registered, result pending.

## Purpose

Retry only the four adapter-planned rows selected by `iter71` after the local iter73 receipt prompt
recovery. This gate tests whether the recovered expanded receipt-enforced prompts can produce valid
Telos receipts during the same bounded provider-compatible adapter-row execution shape that blocked
in iter72.

This is still an adapter-validation protocol-effect retry, not a benchmark, leaderboard,
SWE-bench, production, model-superiority, or state-of-the-art run.

## Execution Envelope

Hard ceilings:

- selected adapter rows to execute: `4`,
- existing BattleSnake rows to retain without rerun: `2`,
- provider model invocations: at most `32`,
- provider spend: at most `$10.00`,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

The four rows are:

1. `baseline-agent-completion-evidence__configs-test-dummy-yaml`,
2. `telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml`,
3. `baseline-agent-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml`,
4. `telos-receipt-enforced-completion-evidence__configs-test-telos-battlesnake-edit-test-yaml`.

The two receipt-enforced rows must use the recovered iter73 prompt overlays:

1. `experiments/iter73_expanded_receipt_prompt_recovery_after_paid_block/proof/recovered_overlay/configs/mini/telos_vertex_gemini_dummy_receipt_enforced_agent.yaml`,
2. `experiments/iter73_expanded_receipt_prompt_recovery_after_paid_block/proof/recovered_overlay/configs/mini/telos_vertex_gemini_edit_receipt_enforced_agent.yaml`.

## Required Evidence

The proof packet must include:

1. machine-readable validation of the iter72 blocked packet and iter73 recovery packet,
2. exact command execution record for each of the four adapter-planned rows,
3. proof that the two Telos receipt-enforced rows used the iter73 recovered overlays,
4. raw text artifacts, metadata, redaction scans, and pair summaries for each executed row,
5. cost and provider-call accounting from committed metadata,
6. Telos receipt validation for every receipt-enforced row before accepting completion evidence,
7. per-stratum verified-completion evidence with no cross-surface pooling,
8. teardown proof for temporary output roots,
9. human-readable adversarial review,
10. valid Telos receipt for this paid retry gate.

## Clean-Pass Bar

The gate can pass only if:

- iter72 proof validates as a clean blocked artifact packet,
- iter73 proof validates as a clean receipt-prompt recovery pass,
- exactly the four adapter-planned rows execute and the two existing BattleSnake rows are not rerun,
- provider calls are at or below `32` and spend is at or below `$10.00`,
- no unselected or excluded row executes,
- every receipt-required row has a valid Telos receipt before verified-completion evidence is
  accepted,
- no GPU, cloud runner startup, Sentinel mutation, live-domain mutation, or production mutation
  occurs,
- no benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art result is claimed.

## Falsifiers

Publish blocked/null evidence if:

- iter72 or iter73 proof, receipt validation, or audit is missing or inconsistent,
- the recovered iter73 overlays cannot be materialized into the runtime CodeClash checkout,
- provider access, dependency, model binding, command materialization, cost capture, receipt
  validation, redaction, or teardown evidence is incomplete,
- a receipt-required row again lacks a valid Telos receipt,
- execution cannot preserve the stratified analysis boundary.

Publish a quality failure if:

- provider calls or spend exceed the frozen ceilings,
- a row executes outside the four selected adapter-planned rows,
- GPU, cloud runner startup, Sentinel mutation, production/live-domain mutation, or hidden task
  mutation occurs,
- unsupported benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only that the four adapter-planned provider-compatible rows ran
under the recovered iter73 receipt prompts and frozen stratified Telos protocol-effect boundary,
with exact costs, raw artifacts, receipt validation, and redaction evidence. It may not claim
benchmark performance, model superiority, production/live-domain behavior, leaderboard standing, or
state-of-the-art status.
