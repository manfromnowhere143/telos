# Iteration 73 - Expanded Receipt Prompt Recovery After Paid Block

Status: pre-registered, result pending.

## Purpose

Recover the receipt-schema prompt gap exposed by
`iter72_provider_compatible_expanded_paid_execution_after_slice_refreeze` before any paid retry.
Iter72 executed the four adapter-planned rows under the frozen provider-compatible expanded-slice
boundary, but both receipt-enforced rows produced schema-incomplete receipt candidates. This gate
may only diagnose and repair that receipt prompt/schema alignment locally.

## Execution Envelope

Hard ceilings:

- provider model invocations: `0`,
- provider spend: `$0.00`,
- paid row execution: forbidden,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

The only allowed evidence inputs from iter72 are:

1. `proof/protocol_effect_report.json`,
2. `proof/run_summary.json`,
3. the two invalid receipt candidates under `proof/raw/*/telos_completion_receipt_candidate.json`,
4. the invalid receipt artifacts under `proof/raw/*/invalid/telos_completion_receipt.json`,
5. the current receipt validator and proof schema.

## Required Evidence

The proof packet must include:

1. machine-readable classification of the two iter72 receipt candidate failures,
2. exact missing-field lists for each receipt-enforced row,
3. recovered receipt-enforced prompt overlays or a precise blocker explaining why recovery is not
   valid from committed evidence,
4. a local valid fixture for the recovered receipt shape,
5. a local malformed fixture proving the validator still fails closed,
6. artifact hashes for every recovered prompt/schema artifact,
7. redaction scan over committed proof and overlay text,
8. human-readable adversarial review,
9. valid Telos receipt for this recovery gate.

## Clean-Pass Bar

The gate can pass only if:

- iter72 proof validates and its audit publishes a clean blocked artifact packet,
- both iter72 receipt failures are classified without provider calls or row execution,
- recovered prompt overlays explicitly require `acceptance_criteria`, `agent_id`, `benchmark_id`,
  `evidence`, `falsifiers`, `receipt_id`, `sha256`, `stated_goal`, `status`, and `task_id`,
- local positive and malformed receipt fixtures prove the validator behavior,
- no provider model call, spend, row execution, GPU, cloud runner startup, Sentinel mutation,
  production/live-domain mutation, or benchmark/model/SOTA claim occurs.

## Falsifiers

Publish blocked/null evidence if:

- iter72 proof, receipt validation, or audit is missing or inconsistent,
- the missing-field diagnosis cannot be derived from committed iter72 artifacts,
- recovered prompts cannot be mapped back to the two expanded receipt-enforced adapter rows,
- local fixtures cannot prove the validator accepts the recovered shape and rejects malformed
  receipts.

Publish a quality failure if:

- any provider model call, spend, row execution, GPU, cloud runner startup, Sentinel mutation,
  production/live-domain mutation, or hidden task mutation occurs,
- unsupported benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art claims appear,
- the gate accepts a receipt-required row without a valid Telos receipt.

## Claim Boundary

If successful, this gate may claim only that the expanded receipt-enforced prompts were locally
recovered from the iter72 schema-incomplete receipt failures and validated with local fixtures. It
may not claim benchmark performance, model superiority, production/live-domain behavior,
leaderboard standing, state-of-the-art status, or a successful paid retry.
