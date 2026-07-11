# Iteration 98 - External Verifier/Telos Differential Suite Design After Adjudication

Status: pre-registered, result pending.

## Purpose

Design a sharper zero-spend differential fixture suite after iter97 showed that complete Telos and
the simpler external verifier had identical endpoint vectors on the first completion-verification
suite. The next suite must target cases where receipt structure, artifact hashes, stopping
boundaries, adversarial receipts, and protocol completeness can separate complete Telos from a
generic external verifier.

## Execution Envelope

Hard ceilings:

- prerequisite: iter97 adjudication evidence must validate cleanly,
- provider model invocations: `0`,
- provider spend: `$0.00`,
- strategy execution: `0`,
- row execution: `0`,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include:

1. validation of iter97 adjudication evidence,
2. a differential target matrix naming where external verifier and complete Telos are expected to
   diverge,
3. fixture-design rules that keep labels private and artifacts identical across strategies,
4. endpoint and sample-size rationale for a later materialization gate,
5. no-claim boundary preserving all benchmark/model/SOTA limits.

## Clean-Pass Bar

The gate can pass only if it designs a stricter empirical test without provider calls, row
execution, hidden labels in strategy inputs, or any benchmark/model/SOTA claim.
