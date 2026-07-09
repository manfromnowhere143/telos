# Iteration 70 - Provider-Compatible Expanded Adapter Completion

Status: pre-registered, result pending.

## Purpose

Complete the provider-compatible adapter set that `iter68` could not honestly finish before the
Dummy task source was committed. This gate may use the `iter69` source snapshot for
`configs/test/dummy.yaml` and the existing committed deterministic-edit source artifacts to plan
expanded provider-compatible rows.

This is a local planning and artifact gate only. It must not execute CodeClash rows, call a
provider, start a cloud runner, use GPU, or widen the result claim.

## Execution Envelope

Hard ceilings:

- provider model invocations: `0`,
- provider spend: `$0.00`,
- row execution: forbidden,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include:

1. machine-readable read of the `iter69` pass and the committed Dummy source snapshot hash,
2. machine-readable read of the `iter68` residual adapter rejection,
3. provider-compatible adapter plan for the Dummy baseline and Telos receipt-enforced rows,
4. provider-compatible adapter plan for the deterministic-edit baseline and Telos
   receipt-enforced rows, either reused from `iter68` or regenerated from committed source,
5. exact future command materialization for every planned row,
6. exact future artifact, cost, receipt-validation, redaction, and teardown plan for every row,
7. explicit statement that the generated adapters are planning evidence, not execution results,
8. redaction scan over generated adapter files,
9. human-readable adversarial review,
10. machine-readable run summary with artifact hashes,
11. valid Telos receipt for this local adapter-completion gate.

## Clean-Pass Bar

The gate can pass only if:

- `iter69` is present and passed with a matching Dummy source snapshot hash,
- `iter68` is present and contains the expected Dummy residual rejection,
- every planned adapter row is backed by committed source evidence,
- every planned row has command, artifact, cost, receipt, redaction, and teardown plans,
- provider calls, spend, row execution, GPU, cloud runner startup, Sentinel mutation, and
  live-domain mutation remain zero,
- no benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art result is claimed.

## Falsifiers

Publish blocked/null evidence if:

- the `iter69` source snapshot is missing, failed, or hash-mismatched,
- adapter planning cannot distinguish Dummy task-source semantics from generated provider
  adapter output,
- any target row lacks committed source evidence or exact future command/artifact/cost plans.

Publish a quality failure if:

- any provider call, provider spend, row execution, GPU, cloud runner startup, Sentinel mutation,
  production/live-domain mutation, or hidden task mutation occurs,
- unsupported benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only that a provider-compatible expanded adapter plan exists for
the committed Dummy and deterministic-edit task surfaces. It may not claim benchmark performance,
model superiority, production/live-domain behavior, leaderboard standing, or state-of-the-art
status.
