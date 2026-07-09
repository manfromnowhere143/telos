# Iteration 68 - Provider-Compatible Task Surface Adapter Recovery

Status: pre-registered, result pending.

## Purpose

Recover the blocker named by `iter67`: the committed candidate universe has no expanded,
condition-balanced provider-compatible rows beyond the two BattleSnake PvP rows already executed in
`iter66`.

This gate is local-only. It may create or reject provider-compatible adapters for the previously
excluded public task surfaces, but it must not execute provider rows or soften the task semantics to
make expansion look easier.

Target excluded surfaces:

- `configs/test/dummy.yaml`,
- `configs/test/telos_battlesnake_edit_test.yaml`.

## Execution Envelope

Hard ceilings:

- provider model invocations: `0`,
- provider spend: `$0.00`,
- row execution: forbidden,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include:

1. machine-readable read of the `iter67` blocked decision,
2. exact source task-surface inventory from committed artifacts,
3. adapter plan for each target excluded surface or an explicit residual rejection reason,
4. baseline and Telos condition separation for every recovered surface,
5. exact future command materialization for every recovered row,
6. receipt, artifact, cost, redaction, and audit plan for every recovered row,
7. proof that provider calls and spend remain zero,
8. human-readable adversarial review,
9. machine-readable run summary with artifact hashes,
10. valid Telos receipt for this local adapter-recovery gate.

## Clean-Pass Bar

The gate can pass only if:

- `iter67` is present and blocked for `expanded_task_surface_adapter_missing`,
- every recovered row preserves the original task surface rather than rebinding it to BattleSnake
  semantics,
- baseline and Telos rows are condition-separated beyond output directory,
- every recovered row has command, receipt, artifact, cost, redaction, and audit plans,
- every unrecovered row has a precise residual rejection reason,
- provider calls, spend, row execution, GPU, cloud runner startup, Sentinel mutation, and
  live-domain mutation remain zero,
- no benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art result is claimed.

## Falsifiers

Publish blocked/null evidence if:

- the source task surface cannot be read without relying on uncommitted local state,
- an adapter would change the public task semantics or prompt condition,
- condition separation cannot be represented without running provider rows,
- command, receipt, artifact, cost, redaction, or audit plans remain incomplete.

Publish a quality failure if:

- any provider call, provider spend, row execution, GPU, cloud runner startup, Sentinel mutation,
  production/live-domain mutation, or excluded-row execution occurs,
- any recovered adapter hides task-surface changes,
- unsupported benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only that additional task-surface adapters are locally recovered
for a future pre-registered slice refreeze. It may not claim benchmark performance, model
superiority, production/live-domain behavior, leaderboard standing, or state-of-the-art status.
