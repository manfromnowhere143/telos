# Iteration 93 - Deterministic Strategy Execution on Materialized Fixtures

Status: pre-registered, result pending.

## Purpose

Execute the deterministic, zero-provider verification strategies over the iter92 materialized
fixtures:

- agent self-report,
- execution tests only,
- external verifier,
- complete Telos protocol.

The LLM judge remains unexecuted in this gate because it requires provider calls. This gate may
produce partial deterministic comparison evidence, but it may not claim all-strategy empirical
superiority, benchmark standing, model superiority, or state-of-the-art status.

## Execution Envelope

Hard ceilings:

- provider model invocations: `0`,
- provider spend: `$0.00`,
- LLM judge execution: `0`,
- materialized fixture count: exactly the iter92 frozen count,
- deterministic strategy execution: allowed only for the four named zero-provider strategies,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include:

1. validation of iter92 fixture-materialization evidence,
2. deterministic decision records for every materialized fixture and every allowed strategy,
3. endpoint calculations limited to the deterministic strategies,
4. explicit LLM-judge deferral evidence,
5. a no-claim boundary forbidding all-strategy empirical-superiority claims until the LLM-judge
   strategy is executed under a later pre-registered gate.

## Clean-Pass Bar

The gate can pass only if:

- iter92 validates cleanly,
- every materialized fixture receives one decision from each allowed deterministic strategy,
- the LLM judge receives zero decisions,
- false-completion acceptance and legitimate-completion preservation are computed only for the
  deterministic strategies,
- no provider calls, spend, LLM-judge execution, cloud runner, GPU, Sentinel mutation, or
  production mutation occurs,
- no benchmark/model/SOTA or all-strategy superiority claim occurs.

## Falsifiers

Publish blocked evidence if:

- iter92 validation fails,
- any materialized fixture is missing from a deterministic strategy,
- fixture labels are unavailable for endpoint scoring,
- deterministic strategy outputs cannot be mapped back to blinded fixture ids.

Publish a quality failure if:

- any provider call, spend, LLM-judge execution, cloud runner, GPU, Sentinel mutation, or
  production/live-domain mutation occurs,
- unsupported benchmark, leaderboard, SWE-bench, model-superiority, production/live-domain,
  all-strategy empirical-superiority, or state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only partial deterministic strategy execution evidence over the
materialized fixtures. It may not claim Telos outperforms all baselines until all comparison
strategies, including the LLM judge, have been executed under frozen conditions.
