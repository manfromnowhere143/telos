# Iteration 101 - Provider LLM Judge Execution on Differential Fixtures After Deterministic

Status: pre-registered, result pending.

## Purpose

Run the deferred provider-backed `llm_judge` strategy on the iter99 differential fixtures after
iter100 has produced zero-provider deterministic strategy evidence. This gate is for completing the
five-strategy fixture table, not for benchmark/model/SOTA claiming.

## Execution Envelope

Hard ceilings:

- prerequisite: iter100 deterministic differential-fixture evidence must validate cleanly,
- provider-backed strategy: `llm_judge` only,
- maximum provider model invocations: `16`,
- maximum provider spend: `$5.00`,
- deterministic strategies: must not be rerun,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include:

1. validation of iter100 deterministic evidence,
2. one provider-backed LLM-judge decision attempt per iter99 fixture or an exact blocker,
3. provider call count and cost accounting,
4. proof that private labels remain excluded from LLM-judge prompts,
5. parsed LLM-judge decisions or raw blocked artifacts with redaction,
6. a no-claim boundary preserving benchmark/model/SOTA limits.

## Clean-Pass Bar

The gate can pass only if iter100 validates cleanly, every LLM-judge decision attempt is accounted
for under the provider-call and spend ceilings, private labels remain excluded from prompts, raw
artifacts are redacted, and no benchmark/model/SOTA claim is made.
