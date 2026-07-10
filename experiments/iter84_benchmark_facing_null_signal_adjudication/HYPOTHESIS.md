# Iteration 84 - Benchmark-Facing Null-Signal Adjudication

Status: pre-registered, result pending.

## Purpose

Adjudicate the iter83 six-row benchmark-facing execution pilot before any broader paid run or
benchmark/model/SOTA claim. Iter83 executed the frozen six selected CodeClash public
task-condition rows under budget, but the observed Telos-minus-baseline verified-completion deltas
were all zero. This gate must decide whether the next step is a replication design, a task/metric
redesign, or a stop, using only committed iter83 evidence.

This is a zero-spend analysis gate. It must not execute provider rows, start a cloud runner, use
GPU, mutate Sentinel-named resources, mutate production/live-domain systems, or make benchmark,
model-superiority, leaderboard, SWE-bench, or state-of-the-art claims.

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

1. validation of the iter83 receipt and audit packet,
2. exact iter83 row accounting: selected ids, executed ids, calls, cost, receipts, and raw-artifact
   presence,
3. per-task delta table for Dummy, BattleSnake, and deterministic-edit rows,
4. classification of the null/no-signal result as evidence, not as a hidden pass,
5. a frozen next-step decision: replicate, redesign task/metric, or stop,
6. explicit no-claim boundary for benchmark, leaderboard, SWE-bench, model-superiority, production,
   live-domain, and state-of-the-art language.

## Clean-Pass Bar

The gate can pass only if:

- iter83 validates as a clean blocked/null artifact packet,
- the no-signal blocker is preserved without deletion or reinterpretation,
- all provider usage remains exactly the committed iter83 accounting,
- no new provider rows execute and no spend occurs,
- the next gate is pre-registered as either a replication design, a task/metric redesign, or a
  stop/review gate,
- no benchmark/model/SOTA claim occurs.

## Falsifiers

Publish blocked evidence if:

- iter83 receipt or audit validation fails,
- row accounting cannot be reproduced from committed artifacts,
- the next-step decision cannot be justified from committed evidence.

Publish a quality failure if:

- any provider row executes in this gate,
- provider spend occurs,
- the iter83 null/no-signal blocker is hidden, deleted, or rebranded as a benchmark win,
- unsupported benchmark, leaderboard, SWE-bench, model-superiority, production/live-domain, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only that iter83 produced a bounded six-row null/no-signal
protocol-effect pilot under the frozen budget. It may not claim benchmark performance, model
superiority, production/live-domain behavior, leaderboard standing, SWE-bench standing, or
state-of-the-art status.
