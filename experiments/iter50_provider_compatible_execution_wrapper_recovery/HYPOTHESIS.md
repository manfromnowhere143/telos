# Iteration 50 - Provider-Compatible Execution Wrapper Recovery

Status: pre-registered, result pending.

## Purpose

`iter49` blocked before provider calls because the repository still lacks a committed wrapper that
can execute exactly the two refrozen provider-compatible BattleSnake pairs. This gate recovers that
wrapper at zero provider spend before any paid execution retry.

The purpose is harness recovery, not a benchmark score, SWE-bench score, production/live-domain
result, model-superiority result, or state-of-the-art result.

## Frozen Input

- Iter49 blocked preflight:
  `experiments/iter49_provider_compatible_protocol_effect_execution_retry/proof/preflight.json`.
- Refrozen provider-compatible slice:
  `experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/proof/provider_compatible_slice.json`.
- Existing secret-safe provider harness:
  `scripts/run_ephemeral_vertex_codeclash_provider.py`.
- Required wrapper path:
  `scripts/run_provider_compatible_protocol_effect_pairs.py`.
- Selected task-condition pairs:
  - `baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml`,
  - `telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml`.

## Budget And Runtime Boundary

- Provider model calls: `0`.
- Provider spend: `$0.00`.
- GPU use: forbidden.
- Cloud runner startup: forbidden unless this gate first publishes a separate lifecycle-only
  preflight that proves no Sentinel-named resource can be touched. The default bar is no runner
  startup.
- Sentinel isolation: Sentinel-named resources must not be modified, stopped, started, deleted, or
  reused.
- Secret boundary: credential material, project identifiers, account identifiers, service-account
  emails, VM names, and zone/project values must not be committed or printed.

## Required Wrapper Behavior

The wrapper must be able to dry-run the exact future execution plan without provider calls:

1. Load the iter48 selected-pair slice.
2. Reject any pair outside the two selected BattleSnake IDs.
3. Reject duplicate, renamed, or missing selected pairs.
4. Resolve the provider overlay, agent config, model config, and cost registry for each selected
   pair.
5. Build the exact per-pair command and raw artifact root.
6. Represent runner setup, overlay copy, `uv sync`, CodeClash execution, artifact copy-back,
   cost/call parsing, redaction scan, receipt validation, and runner teardown steps as an auditable
   dry-run plan.
7. Keep provider calls, spend, cloud runner startup, GPU use, and Sentinel modifications at zero in
   this recovery gate.

## Clean-Pass Bar

The gate can pass only if all hold:

- iter49 is a committed blocked result with zero provider calls and zero spend,
- the wrapper exists at `scripts/run_provider_compatible_protocol_effect_pairs.py`,
- the wrapper dry-run emits exactly two selected pair plans,
- all four excluded historical pairs are rejected by the wrapper,
- every selected pair plan has artifact, cost, redaction, receipt, lifecycle, and metric capture
  destinations,
- future spend and call ceilings remain `16` and `$10.00`,
- no provider model call occurs,
- no provider spend occurs,
- no cloud runner starts,
- no GPU is requested or used,
- no Sentinel-named resource is modified,
- no secret, project, account, service-account, VM, or zone identifier is committed,
- exact counts are reported before percentages,
- no benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art result is claimed.

## Falsifiers

Publish blocked/null evidence if:

- the iter49 blocked proof is missing or not validated,
- the wrapper cannot be represented as committed code,
- the wrapper cannot dry-run exactly the two selected pair plans,
- artifact, cost, redaction, receipt, lifecycle, or metric destinations are missing,
- provider credentials, runner identity, overlay placement, or future execution command capture is
  not representable without leaking identifiers.

Publish a quality failure, not a clean pass, if:

- the wrapper attempts or permits an excluded Dummy or deterministic-edit pair,
- a selected BattleSnake pair is dropped, renamed, duplicated, or silently skipped,
- provider model calls or spend occur in this wrapper-recovery gate,
- a cloud runner starts without a pre-published lifecycle-only authorization,
- GPU is requested or used,
- Sentinel-named resources are modified,
- committed artifacts contain secret material or private identifiers,
- unsupported benchmark/model/production claims appear.

## Claim Boundary

If successful, this gate may claim only that Telos has recovered a dry-run provider-compatible
execution wrapper for the two selected BattleSnake pairs. It may not claim that either pair has
executed, may not report a model/benchmark result, and may not claim leaderboard, SWE-bench,
production/live-domain, model-superiority, or state-of-the-art status.
