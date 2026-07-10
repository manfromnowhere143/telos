# Iteration 88 - External Benchmark Readiness Adjudication After Discriminating Pilot

Status: pre-registered, result pending.

## Purpose

Adjudicate whether the fresh iter87 provider-backed discriminating-metric pilot justifies a larger
external benchmark design. Iter87 passed its bounded six-row protocol-effect pilot under
`task_native_score_share_delta_with_receipt_gates`, but the signal was mixed direction: Dummy and
deterministic-edit were negative while BattleSnake was positive. This gate turns that evidence into
an honest scale/no-scale decision before any broader spend.

This is not a paid execution gate, leaderboard run, SWE-bench run, production/live-domain check,
model-superiority claim, benchmark claim, or state-of-the-art claim.

## Execution Envelope

Hard ceilings:

- provider model invocations: `0`,
- total provider spend: `$0.00`,
- row execution: `0`,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include:

1. validation of iter87 receipt and audit evidence,
2. a locked summary of iter87 calls, spend, row count, receipts, and fresh task deltas,
3. adjudication of mixed-direction signal strength and failure modes,
4. explicit decision among `scale_to_external_benchmark_design`, `replicate_same_slice`,
   `recover_metric_or_task_surface`, or `stop_for_null_or_negative_signal`,
5. if scaling is accepted, a pre-registered benchmark-design sketch with frozen ceilings and
   no execution,
6. if scaling is rejected, a precise blocker or recovery target,
7. redaction scan and no-claim boundary.

## Clean-Pass Bar

The gate can pass only if:

- iter87 validates cleanly,
- no new provider calls, spend, or row execution occur,
- iter87 mixed-direction deltas are carried forward without alteration,
- the next decision is explicit and falsifiable,
- no benchmark/model/SOTA claim occurs.

## Falsifiers

Publish blocked evidence if:

- iter87 receipt or audit validation fails,
- iter87 evidence cannot support any precise next decision,
- the next decision would require provider execution to justify.

Publish a quality failure if:

- any provider call, spend, row execution, GPU use, cloud runner, Sentinel mutation, or
  production/live-domain mutation occurs,
- any committed artifact contains credential, token, project, or service-account residue,
- mixed-direction pilot evidence is described as an aggregate benchmark win,
- unsupported benchmark, leaderboard, SWE-bench, model-superiority, production/live-domain, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only a zero-spend adjudication of the iter87 discriminating
pilot and a frozen next-step decision. It may not claim benchmark performance, model superiority,
production/live-domain behavior, leaderboard standing, SWE-bench standing, or state-of-the-art
status.
