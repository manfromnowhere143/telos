# Iteration 95 - Provider LLM Judge Prompt Budget Recovery After Block

Status: pre-registered, result pending.

## Purpose

Recover from the iter94 LLM-judge blocker without hiding the paid failure. Iter94 made one provider
call, spent `$0.00470000`, and blocked because the model response ended with `MAX_TOKENS` before a
parseable JSON decision was produced.

This is a zero-spend recovery-design gate. It may redesign the frozen LLM-judge prompt and token
budget for a later paid retry, but it must not make provider calls or claim benchmark/model/SOTA
status.

## Execution Envelope

Hard ceilings:

- prerequisite: iter94 blocked evidence must validate cleanly,
- provider model invocations: `0`,
- provider spend: `$0.00`,
- LLM-judge execution: `0`,
- deterministic strategy execution: `0`,
- row execution: `0`,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include:

1. validation of iter94 blocked evidence,
2. analysis of the `MAX_TOKENS`/parse blocker,
3. a recovered prompt/token-budget design that reduces hidden-reasoning truncation risk,
4. a label-leakage check proving private labels remain excluded from judge prompts,
5. a proposed later paid retry envelope, if justified,
6. a no-claim boundary preserving the blocked result.

## Clean-Pass Bar

The gate can pass only if:

- iter94 validates as a clean blocked result,
- no provider calls or spend occur,
- the recovery design directly addresses the `MAX_TOKENS` parse failure,
- label exclusion remains explicit,
- any later paid retry is pre-registered separately with call and spend ceilings,
- no benchmark/model/SOTA claim occurs.

## Falsifiers

Publish blocked evidence if:

- iter94 validation fails,
- the root cause cannot be tied to prompt/token-budget handling,
- the recovered prompt would require labels, hidden ground truth, or non-public artifacts,
- a safe later paid retry envelope cannot be specified.

Publish a quality failure if:

- any provider call, spend, LLM-judge execution, deterministic rerun, row execution, cloud runner,
  GPU, Sentinel mutation, or production/live-domain mutation occurs,
- unsupported benchmark, leaderboard, SWE-bench, model-superiority, production/live-domain, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only prompt/token-budget recovery design after a blocked LLM
judge attempt. It may not claim completed LLM-judge evidence, five-strategy comparison completion,
benchmark superiority, model superiority, production readiness, or state-of-the-art status.
