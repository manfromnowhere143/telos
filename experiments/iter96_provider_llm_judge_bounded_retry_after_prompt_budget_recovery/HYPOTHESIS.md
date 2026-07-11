# Iteration 96 - Provider LLM Judge Bounded Retry After Prompt Budget Recovery

Status: pre-registered, result pending.

## Purpose

Retry the provider LLM-judge strategy after iter95 prompt/token-budget recovery. The retry may only
use the recovered iter95 prompt renderer and generation budget. It must preserve the iter94 blocker
as prior evidence and must not claim benchmark/model/SOTA status.

## Execution Envelope

Hard ceilings:

- prerequisite: iter95 recovery evidence must validate cleanly,
- provider model invocations: at most `14`,
- provider spend: at most `$5.00`,
- LLM-judge decisions: at most one per frozen iter92 fixture,
- deterministic strategy reruns: `0`,
- row execution: `0`,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include:

1. validation of iter95 recovery evidence,
2. exact recovered prompt renderer and prompt hashes for every fixture,
3. raw redacted provider responses and usage metadata for every attempted call,
4. one parseable LLM-judge decision per fixture if the gate passes,
5. label-leakage proof that private labels were excluded from prompts,
6. endpoint metrics only after all `14` LLM-judge decisions exist,
7. provider call and spend accounting,
8. no-claim boundary preserving benchmark/model/SOTA limits.

## Clean-Pass Bar

The gate can pass only if:

- iter95 validates as a clean recovery result,
- provider calls and spend remain within ceilings,
- every frozen fixture receives exactly one parseable LLM-judge decision,
- private labels remain excluded from prompts,
- all raw responses and usage metadata are retained and redacted,
- no deterministic strategy rerun, row execution, GPU, cloud runner, Sentinel mutation,
  production/live-domain mutation, or benchmark/model/SOTA claim occurs.

## Falsifiers

Publish blocked evidence if:

- provider auth/access fails before all fixture decisions are collected,
- any provider response is unparseable or missing usage metadata,
- the call or spend ceiling would be exceeded by continuing,
- endpoint evidence remains incomplete.

Publish a quality failure if:

- private labels leak into prompts,
- provider call or spend ceilings are exceeded,
- any unregistered retry occurs after a parse failure,
- deterministic strategies are rerun in this gate,
- unsupported benchmark, leaderboard, SWE-bench, model-superiority, production/live-domain, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only completed provider LLM-judge fixture decisions under the
recovered prompt budget. It may not claim benchmark superiority, model superiority, production
readiness, or state-of-the-art status.
