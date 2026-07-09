# Iteration 51 - Provider-Compatible Protocol-Effect Execution With Wrapper

Status: pre-registered, result pending.

## Purpose

`iter50` is expected to recover a dry-run wrapper for exactly the two provider-compatible
BattleSnake pairs. This gate is the next bounded paid execution retry, and it may start only if the
iter50 wrapper recovery passes.

The purpose is to measure a two-pair Telos protocol-effect pilot row, not to claim a leaderboard
score, SWE-bench score, production/live-domain result, model superiority, or state-of-the-art
benchmark/model result.

## Frozen Input

- Iter50 wrapper plan:
  `experiments/iter50_provider_compatible_execution_wrapper_recovery/proof/wrapper_dry_run_plan.json`.
- Iter49 blocked proof:
  `experiments/iter49_provider_compatible_protocol_effect_execution_retry/proof/run_summary.json`.
- Refrozen provider-compatible slice:
  `experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/proof/provider_compatible_slice.json`.
- Execution wrapper:
  `scripts/run_provider_compatible_protocol_effect_pairs.py`.
- Selected task-condition pairs:
  - `baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml`,
  - `telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml`.

## Provider And Runtime Budget

- Provider: Google Vertex AI.
- Model: `gemini-3.1-pro-preview-customtools`.
- Maximum provider model invocations: `16`.
- Maximum provider spend: `$10.00`.
- Wall-clock ceiling: `45` minutes.
- GPU use: forbidden.
- Runner: Telos-named ephemeral non-GPU runner only after preflight.
- Sentinel isolation: Sentinel-named resources must not be modified, stopped, started, deleted, or
  reused.
- Secret boundary: credential material, project identifiers, account identifiers, service-account
  emails, VM names, and unredacted private provider fields must not be committed or printed.

## Verification Plan

1. Verify iter50 passed and the wrapper dry-run plan selects exactly two BattleSnake pairs.
2. Verify all four excluded historical pairs remain rejected and unattempted.
3. Run a secret-safe provider, runner, quota, overlay, artifact, cost, receipt, and redaction
   preflight.
4. Block before provider calls if credentials, quota, runner isolation, overlay placement,
   artifact capture, cost capture, receipt validation, redaction, or lifecycle deletion cannot be
   proven.
5. If preflight passes, execute each selected pair exactly once through the committed wrapper.
6. Preserve raw logs, trajectories when present, diffs, metadata, cost/call stats, redaction scans,
   pair summaries, condition rows, command output, receipts, artifact hashes, and adversarial
   review.
7. Compute metrics only from committed artifacts and report exact counts before percentages.
8. Publish blocked, null, failed, and pass rows at full weight.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- iter50 passed and its wrapper plan is unchanged,
- exactly two selected BattleSnake pairs are attempted or explicitly blocked by preflight,
- no excluded Dummy or deterministic-edit pair is attempted,
- baseline and Telos receipt-enforced rows remain separate,
- provider model invocations are `<= 16`,
- provider spend is `<= $10.00`,
- no GPU is requested or used,
- any Telos runner started by the gate is deleted before publication,
- Sentinel-named resources are not modified,
- raw artifacts and pair summaries are committed or the missing artifact is counted as a result gap,
- cost/call stats are parsed from committed artifacts,
- redaction scan passes before publication,
- receipts validate for Telos-enforced rows where required,
- exact counts are reported before percentages,
- no leaderboard, SWE-bench score, production/live-domain, model-superiority, or state-of-the-art
  result is claimed.

## Falsifiers

Publish blocked/null evidence if:

- the iter50 wrapper-recovery proof is missing or not validated,
- provider credentials, runner identity, service readiness, quota, overlay placement, artifact
  retention, cost capture, redaction, receipt validation, or lifecycle deletion is unavailable,
- runner lifecycle cannot be proven without touching Sentinel-named resources,
- cost/call stats cannot be parsed,
- required raw artifacts or hashes are missing,
- redaction cannot prove the committed packet is secret-safe.

Publish a quality failure, not a clean pass, if:

- an excluded pair is attempted,
- a selected pair is dropped, renamed, duplicated, or silently skipped after preflight passes,
- provider spend exceeds `$10.00`,
- model invocations exceed `16`,
- GPU is requested or used,
- a Telos runner remains active after the gate,
- Sentinel-named resources are modified,
- metrics are computed from uncommitted artifacts,
- unsupported benchmark/model/production claims appear.

## Claim Boundary

If successful, this gate may claim only a bounded two-pair Telos protocol-effect pilot result on
the frozen CodeClash BattleSnake PvP surface. It may not claim a SWE-bench score, leaderboard
position, production/live-domain result, general model superiority, or state-of-the-art
benchmark/model result.
