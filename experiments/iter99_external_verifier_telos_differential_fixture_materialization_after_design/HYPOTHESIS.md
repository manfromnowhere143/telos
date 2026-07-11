# Iteration 99 - External Verifier/Telos Differential Fixture Materialization After Design

Status: pre-registered, result pending.

## Purpose

Materialize the iter98 external-verifier/Telos differential suite design as static public fixture
artifacts, private labels, and strategy-input manifests. This is a zero-spend materialization gate,
not strategy execution.

## Execution Envelope

Hard ceilings:

- prerequisite: iter98 differential-suite design evidence must validate cleanly,
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

1. validation of iter98 design evidence,
2. `16` materialized fixtures: one false-completion trap and one legitimate control for each of
   the `8` differential target families,
3. public artifact packets and private ground-truth labels kept separate,
4. strategy-input manifests proving identical public artifacts and label exclusion,
5. artifact hashes for every public fixture file,
6. no-claim boundary preserving benchmark/model/SOTA limits.

## Clean-Pass Bar

The gate can pass only if all planned fixtures are materialized, labels remain excluded from every
strategy input, no provider calls or strategy execution occur, and no benchmark/model/SOTA claim is
made.
