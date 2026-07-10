# Iteration 91 - Empirical Validation Suite Design for Completion Verification

Status: pre-registered, result pending.

## Purpose

Design a controlled empirical validation suite that tests whether Telos materially improves
autonomous software-agent completion verification compared with simpler verification strategies.
This gate shifts the milestone from protocol completeness toward defensible empirical validation.

The suite must focus on cases where conventional completion checks can fail:

- proxy completion,
- misleading passing tests,
- partial implementations,
- reward-hacking behavior,
- incorrect stopping boundaries,
- adversarial or malformed receipts,
- semantically incomplete solutions.

The comparison targets are:

- agent self-report,
- execution tests only,
- LLM judge,
- external verifier,
- complete Telos protocol.

This is not a benchmark, leaderboard, SWE-bench, model-superiority, production/live-domain, or
state-of-the-art claim. It is a zero-spend suite-design gate.

## Execution Envelope

Hard ceilings:

- provider model invocations: `0`,
- provider spend: `$0.00`,
- row execution: `0`,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include:

1. validation of iter90 adjudication evidence,
2. a frozen empirical suite design with case families, labels, and expected failure modes,
3. a comparison plan for all five verification strategies under identical artifacts,
4. quantitative endpoints: false-completion acceptance, false rejection, legitimate completion
   preservation, cost/time overhead, and reviewer reproducibility,
5. a no-claim boundary that forbids benchmark/model/SOTA claims until comparative execution data
   exists.

## Clean-Pass Bar

The gate can pass only if:

- iter90 validates cleanly,
- the suite design is falsifiable and compares Telos against simpler baselines,
- every case family has a stated target failure mode and expected evidence artifact,
- quantitative endpoints are defined before execution,
- no provider calls, spend, row execution, cloud runner, GPU, Sentinel mutation, or production
  mutation occurs,
- no benchmark/model/SOTA claim occurs.

## Falsifiers

Publish blocked evidence if:

- iter90 validation fails,
- the suite design does not compare against simpler verification baselines,
- failure modes or quantitative endpoints are ambiguous.

Publish a quality failure if:

- any provider call, spend, row execution, cloud runner, GPU, Sentinel mutation, or
  production/live-domain mutation occurs,
- unsupported benchmark, leaderboard, SWE-bench, model-superiority, production/live-domain, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only a frozen empirical validation suite design. It may not
claim that Telos outperforms any baseline until comparative execution evidence exists.
