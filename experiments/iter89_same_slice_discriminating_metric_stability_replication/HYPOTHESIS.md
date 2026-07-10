# Iteration 89 - Same-Slice Discriminating Metric Stability Replication

Status: pre-registered, result pending.

## Purpose

Run one bounded same-slice replication of the iter87 discriminating-metric pilot before any larger
external benchmark design. Iter86 and iter87 both showed that
`task_native_score_share_delta_with_receipt_gates` is computable and non-saturated, but their
task-level directions were unstable. This gate tests whether a second fresh execution of the exact
six frozen CodeClash task-condition rows gives stable enough directionality to justify benchmark
design work.

This is not a leaderboard, SWE-bench, model-superiority, production/live-domain, benchmark, or
state-of-the-art claim. It is a bounded stability replication.

## Execution Envelope

Hard ceilings:

- selected rows: exactly the six iter83/iter87 task-condition rows,
- provider model invocations: at most `96`,
- total provider spend: at most `$10.00`,
- per-row provider model invocations: at most `16`,
- per-row provider spend: at most `$2.00`,
- CodeClash task surfaces: Dummy, BattleSnake, deterministic-edit only,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include:

1. validation of iter88 adjudication evidence,
2. preflight proving the frozen row set, provider/API readiness, and spend/call ceilings,
3. raw artifacts for each executed row before interpretation,
4. per-row cost/call accounting and redaction scans,
5. Telos receipt validation for every receipt-required row,
6. deterministic score-share extraction from fresh raw metadata,
7. per-task baseline/Telos score-share deltas,
8. comparison against iter86 backtest and iter87 fresh execution directions,
9. explicit stability classification: stable, unstable, blocked, or quality failure,
10. no-claim boundaries.

## Clean-Pass Bar

The gate can pass only if:

- iter88 validates cleanly,
- exactly the six frozen rows execute and no extra rows execute,
- provider calls and spend stay under every ceiling,
- all raw artifacts, metadata, cost/call stats, and redaction scans are present,
- Telos receipt-required rows validate,
- the discriminating metric is computed from fresh committed raw artifacts,
- stability is classified without claiming benchmark/model/SOTA performance,
- no benchmark/model/SOTA claim occurs.

## Falsifiers

Publish blocked evidence if:

- iter88 validation fails,
- ADC/provider readiness fails before row execution,
- any selected row cannot run while preserving frozen scope and ceilings,
- required raw artifacts or cost/call stats are missing,
- score-share extraction is ambiguous or non-computable from fresh artifacts.

Publish a quality failure if:

- any unselected row executes,
- provider calls or spend exceed a ceiling,
- raw artifacts are changed after interpretation,
- credential, token, project, or service-account residue is committed,
- GPU, cloud runner, Sentinel mutation, production/live-domain mutation, or hidden task mutation
  occurs,
- unsupported benchmark, leaderboard, SWE-bench, model-superiority, production/live-domain, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only a bounded six-row stability replication under the
discriminating metric. It may not claim benchmark performance, model superiority,
production/live-domain behavior, leaderboard standing, SWE-bench standing, or state-of-the-art
status.
