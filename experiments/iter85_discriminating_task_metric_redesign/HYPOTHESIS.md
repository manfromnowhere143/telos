# Iteration 85 - Discriminating Task/Metric Redesign

Status: pre-registered, result pending.

## Purpose

Redesign the next benchmark-facing protocol-effect slice after iter83 produced a bounded
null/no-signal result. The verified-completion metric saturated: baseline and Telos rows all
verified on Dummy, BattleSnake, and deterministic-edit task surfaces. This gate must design a more
discriminating task/metric contract before any additional provider-backed execution.

This is a zero-spend design gate. It must not execute CodeClash rows, call providers, start a cloud
runner, use GPU, mutate Sentinel-named resources, mutate production/live-domain systems, or make
benchmark/model/SOTA claims.

## Execution Envelope

Hard ceilings:

- provider model invocations: `0`,
- provider spend: `$0.00`,
- CodeClash row execution: `0`,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include:

1. validation of iter84 adjudication evidence,
2. a precise critique of why verified-completion evidence saturated in iter83,
3. a candidate discriminating metric contract that preserves receipt/raw-artifact accounting,
4. task eligibility rules for any proposed future slice,
5. future paid-run ceilings if and only if a later execution gate is pre-registered,
6. explicit no-claim boundaries for benchmark, leaderboard, SWE-bench, model-superiority,
   production/live-domain, and state-of-the-art language.

## Clean-Pass Bar

The gate can pass only if:

- iter84 validates as a clean adjudication packet,
- no provider/model calls or row execution occur,
- the proposed metric is not merely the saturated verified-completion boolean,
- future execution remains separately pre-registered,
- no benchmark/model/SOTA claim occurs.

## Falsifiers

Publish blocked evidence if:

- iter84 validation fails,
- the metric redesign cannot be justified from committed iter83/iter84 evidence,
- no candidate metric can be specified without changing production/live-domain behavior.

Publish a quality failure if:

- any provider row executes in this gate,
- provider spend occurs,
- the saturated iter83 null result is hidden or rebranded as a win,
- unsupported benchmark, leaderboard, SWE-bench, model-superiority, production/live-domain, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only a zero-spend discriminating task/metric design. It may not
claim benchmark performance, model superiority, production/live-domain behavior, leaderboard
standing, SWE-bench standing, or state-of-the-art status.
