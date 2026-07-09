# Iteration 52 - Provider Condition Runtime Separation Recovery

Status: pre-registered, result pending.

## Purpose

`iter51` is expected to block if the two provider-compatible BattleSnake rows are not distinct
runtime conditions. This gate recovers that missing evidence before any paid protocol-effect retry.

The goal is not to run provider calls. The goal is to prove that a future paid retry would execute:

- a baseline condition that collects raw completion evidence without requiring a Telos receipt
  before interpretation,
- a Telos receipt-enforced condition whose runtime prompt, wrapper mode, and acceptance checks make
  the receipt requirement concrete before the result is accepted.

## Frozen Input

- Iter51 blocked proof:
  `experiments/iter51_provider_compatible_protocol_effect_execution_with_wrapper/proof/run_summary.json`.
- Iter50 wrapper dry-run plan:
  `experiments/iter50_provider_compatible_execution_wrapper_recovery/proof/wrapper_dry_run_plan.json`.
- Refrozen provider-compatible slice:
  `experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/proof/provider_compatible_slice.json`.
- Existing provider overlay:
  `experiments/iter09_provider_model_pilot_smoke/proof/overlay/`.

## Recovery Work

The gate may edit only repo-local wrapper, overlay, verifier, audit, and documentation files. It must
not start a cloud runner and must not call a provider model.

The recovered packet must include:

1. an explicit wrapper execution mode that is still disabled by default,
2. two selected pair plans and four rejected historical exclusions,
3. a baseline provider overlay or command plan,
4. a distinct Telos receipt-enforced provider overlay or command plan,
5. receipt artifact paths and validation commands for the Telos row,
6. budget gates for `<= 16` provider invocations and `<= $10.00`,
7. raw artifact, cost, redaction, lifecycle, and teardown plans,
8. a dry-run transcript proving no provider call, cloud runner, GPU, or Sentinel resource mutation.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- iter51 is a blocked result caused by wrapper execution-mode and condition-separation gaps,
- no provider model call occurs,
- provider spend remains `$0.00`,
- no cloud runner starts,
- no GPU is requested or used,
- no Sentinel-named resource is modified,
- the baseline and Telos rows have distinct runtime plans beyond output directory,
- the Telos row has a concrete receipt validation path before result acceptance,
- all four excluded historical pairs remain rejected and unattempted,
- the future paid retry remains capped at `16` model invocations and `$10.00`,
- no benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art result is claimed.

## Falsifiers

Publish blocked/null evidence if:

- iter51 proof is missing or not validated,
- the wrapper cannot express an execution mode without immediately enabling paid execution,
- baseline and Telos rows still differ only by output directory,
- the Telos receipt requirement remains only a post-hoc label rather than a concrete runtime and
  acceptance check,
- artifact, cost, redaction, receipt, lifecycle, or teardown plans are missing,
- redaction cannot prove committed artifacts are secret-safe.

Publish a quality failure if:

- any provider model call occurs,
- any cloud runner starts,
- any GPU is requested or used,
- any Sentinel-named resource is modified,
- an excluded historical pair is attempted,
- budget gates are widened,
- unsupported benchmark/model/production claims appear.

## Claim Boundary

If successful, this gate may claim only zero-spend recovery of condition-separated provider-wrapper
readiness. It may not claim a benchmark result, SWE-bench score, leaderboard result,
production/live-domain result, model superiority, or state-of-the-art benchmark/model result.
