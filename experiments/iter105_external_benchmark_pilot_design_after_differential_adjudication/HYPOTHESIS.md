# Iteration 105 - External Benchmark Pilot Design After Differential Adjudication

Status: pre-registered, result pending.

## Purpose

Design the smallest defensible external benchmark pilot after iter104 produced fixture-level
differential evidence that complete Telos caught false-completion traps missed by the simpler
external verifier while preserving legitimate controls.

This gate is design-only. It must decide whether a paid external pilot is scientifically justified,
what task source and sample size are admissible, how baselines and Telos will be compared under
identical artifacts, and which stopping/null-result rules prevent overclaiming.

## Execution Envelope

Hard ceilings:

- prerequisite: iter104 adjudication evidence must validate cleanly,
- provider model invocations: `0`,
- provider spend: `$0.00`,
- benchmark/task execution: `0`,
- strategy execution: `0`,
- row execution: `0`,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include validated iter104 evidence, pilot task-source selection criteria,
baseline/Telos comparison design, sample-size and budget rationale, stopping and null-result rules,
artifact/receipt requirements, claim boundaries, and no benchmark/model/SOTA claim.
