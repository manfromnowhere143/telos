# Iteration 54 - Provider Pair Executor Recovery

Status: pre-registered, result pending.

## Purpose

Recover the missing execution machinery exposed by `iter53` without starting a provider model call.

The question is narrow:

> Can Telos commit a pair executor that proves the pinned CodeClash checkout, recovered iter52
> overlays, Docker/runner readiness, exact command materialization, artifact-copy plan, cost parser,
> Telos receipt-validation path, redaction scan, and teardown plan before the next paid retry?

This is not a benchmark run, not a SWE-bench score, not a production/live-domain result, not a
model-superiority result, and not a state-of-the-art claim.

## Frozen Input

- Iter53 blocked result:
  `experiments/iter53_provider_compatible_protocol_effect_execution_after_condition_recovery/proof/run_summary.json`.
- Iter52 condition plan:
  `experiments/iter52_provider_condition_runtime_separation_recovery/proof/condition_runtime_separation_plan.json`.
- Iter52 recovered overlay:
  `experiments/iter52_provider_condition_runtime_separation_recovery/proof/recovered_overlay/`.
- Refrozen provider-compatible slice:
  `experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/proof/provider_compatible_slice.json`.
- Pinned CodeClash commit: `381cdfa05a35e8acd35853b9fc7e13005121b127`.

## Execution Envelope

This gate is zero-spend and may not run a provider-backed task-condition row.

Allowed actions:

- verify or create a local pinned CodeClash checkout under `/tmp/telos-codeclash`,
- install/sync CodeClash dependencies only if the command can be bounded and logged without secrets,
- copy recovered iter52 overlay files into the pinned checkout or prove the copy plan exactly,
- materialize the two exact provider-backed commands without executing them,
- validate Docker/runner readiness with a timeout,
- run no-provider structural checks only,
- write a machine-readable executor readiness report.

Forbidden actions:

- provider model calls,
- provider spend,
- cloud runner startup unless explicitly limited to a no-model lifecycle probe with teardown proof,
- GPU use,
- Sentinel-named resource mutation,
- production/live-domain mutation,
- execution of excluded Dummy or deterministic-edit pairs,
- benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or state-of-the-art
  claims.

## Required Evidence

The proof packet must include:

1. preflight proving iter53 blocked for executor/runner readiness and did not make provider calls,
2. exact selected and excluded pair IDs,
3. pinned CodeClash checkout status and commit check,
4. overlay-copy manifest with hashes,
5. exact command manifest for both selected BattleSnake rows,
6. executor implementation or dry-run report showing `execute_pair` no longer ends in the iter52
   intentional `RuntimeError`,
7. Docker/runner readiness result with timeout behavior,
8. cost/call parser fixture or dry-run parse plan,
9. Telos receipt validation path for the Telos row,
10. redaction scan over committed proof artifacts,
11. human-readable adversarial review,
12. machine-readable run summary with artifact hashes.

## Clean-Pass Bar

The gate can pass only if:

- iter53 is a committed blocked result with zero provider calls and zero spend,
- exactly two selected BattleSnake rows remain bound,
- all four excluded historical pairs remain unattempted,
- the pair executor can materialize both exact commands,
- the executor has an implementation path rather than the iter52 intentional `RuntimeError`,
- pinned CodeClash checkout readiness is proven or a precise blocker is published,
- Docker/runner readiness is proven or a precise blocker is published,
- provider calls remain `0`,
- provider spend remains `$0.00`,
- no cloud runner starts unless the gate explicitly records a no-model lifecycle probe and teardown,
- no GPU is used,
- no Sentinel-named resource is modified,
- no unsupported benchmark/model/production claim appears.

## Falsifiers

Publish blocked evidence if:

- the pinned CodeClash checkout cannot be created or verified,
- Docker/runner readiness cannot be proven within the timeout,
- the executor cannot be implemented without risking provider calls,
- artifact-copy, cost, receipt, redaction, or teardown controls are incomplete.

Publish a quality failure if:

- any provider model call occurs,
- any provider spend occurs,
- any excluded pair executes,
- any GPU is used,
- any Sentinel-named resource is modified,
- committed artifacts contain credential, account, project, service-account, VM, or zone residue,
- unsupported benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only zero-spend executor readiness for the next two-row
provider-compatible paid retry. It may not claim a benchmark result, SWE-bench score, leaderboard
position, production/live-domain result, general model superiority, or state-of-the-art
benchmark/model result.
