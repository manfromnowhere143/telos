# Iteration 83 - Benchmark-Facing Protocol-Effect Execution Pilot

Status: pre-registered, result pending.

## Purpose

Execute the six-row benchmark-facing protocol-effect pilot designed in iter82. The pilot tests
baseline versus Telos receipt-enforced completion evidence on the frozen CodeClash public
task-condition rows, while keeping SWE-bench Verified as a receipt-field anchor only.

This is a bounded paid execution gate. It may execute only the six selected CodeClash
task-condition rows under the frozen provider-call and spend ceilings. It must not execute
unselected rows, start a cloud runner, use GPU, mutate Sentinel-named resources, mutate
production/live-domain systems, or make benchmark/model/SOTA claims.

## Execution Envelope

Hard ceilings:

- selected task-condition rows to execute: `6`,
- selected pair ids: exactly those in
  `experiments/iter82_benchmark_facing_protocol_effect_slice_design/proof/future_paid_run_plan.json`,
- per-row provider model invocation ceiling: `16`,
- total provider model invocation ceiling: `96`,
- per-row provider spend ceiling: `$2.00`,
- total provider spend ceiling: `$10.00`,
- wall-clock ceiling: `90` minutes,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include:

1. validation of the iter82 design packet,
2. preflight proving the selected pair ids, row count, call ceiling, spend ceiling, and no-cloud/no-GPU boundary,
3. raw command artifacts for every selected row,
4. per-row receipt, raw-artifact, cost/call, redaction, and failure-mode accounting,
5. exact provider-call and spend totals,
6. pass/blocked/null/fail semantics applied exactly as frozen in iter82,
7. explicit confirmation that no benchmark, leaderboard, SWE-bench, production/live-domain,
   model-superiority, or state-of-the-art result is claimed.

## Clean-Pass Bar

The gate can pass only if:

- iter82 validates as a clean slice-design packet,
- exactly the six selected rows execute and no unselected row executes,
- provider calls and spend remain at or below the frozen ceilings,
- every completed row has committed raw artifacts, cost/call stats, redaction scan, and receipt
  accounting,
- Telos receipt-enforced rows require a valid Telos receipt before verified completion is accepted,
- no token, project identifier, service-account, or credential material is committed,
- no GPU, cloud runner startup, Sentinel mutation, production/live-domain mutation, hidden task
  mutation, benchmark/model claim, or state-of-the-art claim occurs.

## Falsifiers

Publish blocked/null evidence if:

- iter82 validation fails,
- provider readiness cannot be checked without printing secrets,
- a selected row cannot execute while preserving the frozen call/spend ceilings,
- cost/call stats or raw artifacts are missing for a completed row,
- the result shows no interpretable Telos-minus-baseline protocol-effect signal.

Publish a quality failure if:

- any unselected row executes,
- provider calls or spend exceed the frozen ceilings,
- token, project identifier, service-account, or credential material is committed,
- GPU, cloud runner startup, Sentinel mutation, production/live-domain mutation, or hidden task
  mutation occurs,
- unsupported benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only a bounded benchmark-facing protocol-effect pilot result on
the six selected CodeClash task-condition rows. It may not claim benchmark performance, model
superiority, production/live-domain behavior, leaderboard standing, SWE-bench standing, or
state-of-the-art status.
