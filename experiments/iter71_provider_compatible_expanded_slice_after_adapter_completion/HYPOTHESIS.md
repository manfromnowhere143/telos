# Iteration 71 - Provider-Compatible Expanded Slice After Adapter Completion

Status: pre-registered, result pending.

## Purpose

Refreeze the provider-compatible protocol-effect slice after `iter70` adapter completion. This gate
decides whether the newly planned Dummy and deterministic-edit rows are legitimate enough to join
the already executed two-row BattleSnake slice before any larger paid run.

This is a local selection and readiness gate only. It must not execute CodeClash rows, call a
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

1. machine-readable read of the `iter70` adapter-completion result,
2. machine-readable read of the existing two-row BattleSnake provider-compatible result,
3. exact candidate row list with source, adapter, command, artifact, cost, redaction, receipt, and
   teardown plans,
4. explicit inclusion/exclusion decision for every candidate row,
5. exact provider/API and spend ceilings for the next paid gate if one is authorized,
6. statement that this gate is slice selection evidence, not execution evidence,
7. redaction scan over generated selection artifacts,
8. human-readable adversarial review,
9. machine-readable run summary with artifact hashes,
10. valid Telos receipt for this local slice-refreeze gate.

## Clean-Pass Bar

The gate can pass only if:

- `iter70` is present and passed with adapter rows backed by committed source evidence,
- every selected row has exact command/artifact/cost/receipt/redaction/teardown plans,
- every excluded row has a precise exclusion reason,
- provider calls, spend, row execution, GPU, cloud runner startup, Sentinel mutation, and
  live-domain mutation remain zero,
- no benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art result is claimed.

## Falsifiers

Publish blocked/null evidence if:

- `iter70` is missing, blocked, failed, or hash-mismatched,
- a candidate row lacks source or adapter evidence,
- the expanded selection would mix incomparable rows without an explicit analysis boundary,
- cost, redaction, receipt, or teardown plans are incomplete.

Publish a quality failure if:

- any provider call, provider spend, row execution, GPU, cloud runner startup, Sentinel mutation,
  production/live-domain mutation, or hidden task mutation occurs,
- unsupported benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only that a provider-compatible expanded slice has been frozen
or rejected before paid execution. It may not claim benchmark performance, model superiority,
production/live-domain behavior, leaderboard standing, or state-of-the-art status.
