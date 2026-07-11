# Iteration 100 - Deterministic Strategy Execution on Differential Fixtures After Materialization

Status: pre-registered, result pending.

## Purpose

Run only the zero-provider deterministic verification strategies on the iter99 materialized
external-verifier/Telos differential fixtures. This gate is for strategy decisions over frozen
public artifacts, not provider LLM judging and not benchmark/model/SOTA claiming.

## Execution Envelope

Hard ceilings:

- prerequisite: iter99 differential fixture materialization evidence must validate cleanly,
- provider model invocations: `0`,
- provider spend: `$0.00`,
- deterministic strategy execution: allowed only for `agent_self_report`,
  `execution_tests_only`, `external_verifier`, and `complete_telos_protocol`,
- provider-backed `llm_judge` execution: forbidden,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include:

1. validation of iter99 materialized fixture evidence,
2. deterministic decisions for every materialized fixture for each allowed deterministic strategy,
3. proof that the same public fixture artifacts were used for every strategy,
4. proof that private labels remained excluded from all strategy inputs during execution,
5. scored endpoint evidence separated from unsupported benchmark/model/SOTA claims,
6. a no-claim boundary preserving provider, model, benchmark, live-domain, and SOTA limits.

## Clean-Pass Bar

The gate can pass only if iter99 validates cleanly, deterministic strategy execution covers every
materialized fixture, no provider calls or provider-backed LLM judge execution occurs, private
labels remain excluded from strategy inputs, and no benchmark/model/SOTA claim is made.
