# Iteration 72 - Provider-Compatible Expanded Paid Execution After Slice Refreeze

Status: pre-registered, result pending.

## Purpose

Execute only the four adapter-planned rows selected by
`iter71_provider_compatible_expanded_slice_after_adapter_completion`, while retaining the two
already executed BattleSnake rows from `iter66` as prior evidence. This gate is a bounded
provider-backed protocol-effect extension, not a benchmark, leaderboard, SWE-bench, production,
model-superiority, or state-of-the-art run.

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

## Required Evidence

The proof packet must include:

1. machine-readable read of the `iter71` expanded-slice decision,
2. exact command execution record for each of the four adapter-planned rows,
3. raw text artifacts, metadata, redaction scans, and pair summaries for each executed row,
4. cost and provider-call accounting from committed metadata,
5. Telos receipt validation for every receipt-enforced row before accepting completion evidence,
6. per-stratum verified-completion evidence with no cross-surface pooling,
7. teardown proof for temporary output roots,
8. redaction scan over committed artifacts,
9. human-readable adversarial review,
10. valid Telos receipt for this paid execution gate.

## Clean-Pass Bar

The gate can pass only if:

- `iter71` passed and selected the four adapter-planned rows under a stratified boundary,
- every attempted row stays inside the exact command and output-root plan,
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

- `iter71` is missing, blocked, failed, or hash-mismatched,
- provider access, dependency, model binding, command materialization, cost capture, receipt
  validation, redaction, or teardown evidence is incomplete,
- a row executes outside the four selected adapter-planned rows,
- execution cannot preserve the stratified analysis boundary.

Publish a quality failure if:

- provider calls or spend exceed the frozen ceilings,
- GPU, cloud runner startup, Sentinel mutation, production/live-domain mutation, or hidden task
  mutation occurs,
- unsupported benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only that the four adapter-planned provider-compatible rows ran
under the frozen stratified Telos protocol-effect boundary, with exact costs, raw artifacts,
receipt validation, and redaction evidence. It may not claim benchmark performance, model
superiority, production/live-domain behavior, leaderboard standing, or state-of-the-art status.
