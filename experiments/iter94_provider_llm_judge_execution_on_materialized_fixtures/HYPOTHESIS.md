# Iteration 94 - Provider LLM Judge Execution on Materialized Fixtures

Status: pre-registered, result pending.

## Purpose

Execute the deferred LLM-judge strategy over the frozen iter92 materialized fixtures, after iter93
has produced deterministic zero-provider strategy evidence.

This gate exists only to complete the five-strategy comparison under frozen fixture conditions. It
does not authorize benchmark, leaderboard, SWE-bench, model-superiority, or state-of-the-art claims.

## Execution Envelope

Hard ceilings:

- prerequisite: iter93 deterministic strategy execution must validate cleanly,
- materialized fixture count: exactly the iter92 frozen count,
- LLM judge decisions: exactly one per materialized fixture if execution proceeds,
- provider model invocations: at most `14`,
- provider spend: at most `$10.00`,
- deterministic strategies: no rerun except validation of committed iter93 evidence,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include:

1. validation of iter92 and iter93 evidence,
2. the frozen LLM-judge prompt and model binding,
3. one raw LLM-judge decision artifact per materialized fixture if execution proceeds,
4. endpoint calculations that add the LLM judge to the already committed deterministic strategy
   table,
5. exact provider-call and spend accounting,
6. a no-claim boundary forbidding benchmark/model/SOTA conclusions unless a later gate adjudicates
   the full comparison under hostile-review standards.

## Clean-Pass Bar

The gate can pass only if:

- iter93 validates cleanly,
- every materialized fixture receives exactly one LLM-judge decision or the gate publishes a precise
  blocker before partial execution,
- provider calls and spend remain within the ceilings,
- raw judge decisions and endpoint calculations are committed,
- no cloud runner, GPU, Sentinel mutation, or production mutation occurs,
- no benchmark/model/SOTA claim occurs.

## Falsifiers

Publish blocked evidence if:

- iter93 validation fails,
- provider authentication or quota fails before a complete judge run,
- any fixture decision is missing, ambiguous, or unmappable to a blinded fixture id,
- the judge prompt or model binding cannot be frozen before execution.

Publish a quality failure if:

- provider calls or spend exceed the ceiling,
- deterministic strategies are rerun as new evidence instead of validated from iter93,
- labels leak into the LLM-judge prompt,
- unsupported benchmark, leaderboard, SWE-bench, model-superiority, production/live-domain, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only completed five-strategy fixture-comparison evidence. It may
not claim Telos is benchmark-superior, model-superior, production-ready, or state of the art without
a later pre-registered adjudication gate.
