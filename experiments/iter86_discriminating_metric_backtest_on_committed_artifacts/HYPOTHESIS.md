# Iteration 86 - Discriminating Metric Backtest on Committed Artifacts

Status: pre-registered, result pending.

## Purpose

Backtest the iter85 discriminating task/metric contract against committed iter83 raw artifacts
without executing any new CodeClash rows. Iter85 may define a more discriminating metric, but the
metric must prove it can be computed deterministically from committed artifacts before any further
provider-backed execution is justified.

This is a zero-spend backtest gate. It must not execute CodeClash rows, call providers, start a
cloud runner, use GPU, mutate Sentinel-named resources, mutate production/live-domain systems, or
make benchmark/model/SOTA claims.

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

1. validation of iter85 metric-redesign evidence,
2. deterministic extraction of task-native score fields from committed iter83 raw metadata,
3. per-task baseline/Telos score-share deltas under the iter85 metric contract,
4. explicit treatment of missing, ambiguous, or non-computable fields as blockers,
5. a next-step decision: paid execution pre-registration, metric redesign, or stop/review,
6. explicit no-claim boundaries for benchmark, leaderboard, SWE-bench, model-superiority,
   production/live-domain, and state-of-the-art language.

## Clean-Pass Bar

The gate can pass only if:

- iter85 validates as a clean zero-spend metric-redesign packet,
- all six iter83 rows are parsed from committed raw metadata,
- the metric is computable without provider calls, row execution, or live-domain mutation,
- no aggregate benchmark, leaderboard, SWE-bench, model-superiority, production/live-domain, or
  state-of-the-art claim occurs,
- any future paid execution remains separately pre-registered.

## Falsifiers

Publish blocked evidence if:

- iter85 validation fails,
- any required iter83 raw metadata is missing,
- controlled-player score mapping is ambiguous,
- task-native score fields are absent or cannot be interpreted without rerunning rows,
- the metric collapses back to the saturated verified-completion boolean.

Publish a quality failure if:

- any provider row executes in this gate,
- provider spend occurs,
- raw artifacts are mutated to improve the metric result,
- the iter83 null result is hidden or rebranded as a win,
- unsupported benchmark, leaderboard, SWE-bench, model-superiority, production/live-domain, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only a zero-spend backtest of the iter85 candidate metric on
committed iter83 artifacts. It may not claim benchmark performance, model superiority,
production/live-domain behavior, leaderboard standing, SWE-bench standing, or state-of-the-art
status.
