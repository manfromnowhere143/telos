# Iteration 87 - Benchmark-Facing Discriminating Metric Execution Pilot

Status: pre-registered, result pending.

## Purpose

Run the smallest paid execution pilot that can test the iter85/iter86 discriminating metric under
fresh provider execution. Iter86 must first show that the metric is computable from committed
CodeClash artifacts. This gate may then rerun only the six frozen CodeClash public task-condition
rows and evaluate `task_native_score_share_delta_with_receipt_gates`.

This is not a leaderboard, SWE-bench, model-superiority, production/live-domain, benchmark, or
state-of-the-art claim. It is a bounded protocol-effect execution pilot.

## Execution Envelope

Hard ceilings:

- selected rows: exactly the six iter83 task-condition rows,
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

1. validation of iter86 backtest evidence,
2. preflight proving the frozen row set, provider/API readiness, and spend/call ceilings,
3. raw artifacts for each executed row before interpretation,
4. per-row cost/call accounting and redaction scans,
5. Telos receipt validation for every receipt-required row,
6. deterministic score-share extraction from fresh raw metadata,
7. per-task baseline/Telos score-share deltas,
8. pass/null/blocked/fail semantics and no-claim boundaries.

## Clean-Pass Bar

The gate can pass only if:

- iter86 validates cleanly,
- exactly the six frozen rows execute and no extra rows execute,
- provider calls and spend stay under every ceiling,
- all raw artifacts, metadata, cost/call stats, and redaction scans are present,
- Telos receipt-required rows validate,
- the discriminating metric is computed from fresh committed raw artifacts,
- no benchmark/model/SOTA claim occurs.

## Falsifiers

Publish blocked evidence if:

- iter86 validation fails,
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

If successful, this gate may claim only a bounded six-row provider-backed protocol-effect pilot
under the discriminating metric. It may not claim benchmark performance, model superiority,
production/live-domain behavior, leaderboard standing, SWE-bench standing, or state-of-the-art
status.
