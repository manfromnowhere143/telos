# Iteration 49 - Provider-Compatible Protocol-Effect Execution Retry

Status: pre-registered, result pending.

## Purpose

`iter48` refroze the provider-compatible protocol-effect slice to the two BattleSnake PvP
condition pairs with concrete Vertex provider commands. This gate is the bounded execution retry
for that narrowed slice only.

The purpose is to measure a small protocol-effect pilot row, not to claim a leaderboard score,
SWE-bench score, production/live-domain result, model superiority, or state-of-the-art result.

## Frozen Input

- Refrozen provider-compatible slice:
  `experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/proof/provider_compatible_slice.json`.
- Command-binding report:
  `experiments/iter47_provider_task_condition_command_binding_recovery/proof/command_binding_report.json`.
- Provider overlay root:
  `experiments/iter09_provider_model_pilot_smoke/proof/overlay`.
- Selected task surface:
  `configs/test/battlesnake_pvp_test.yaml`.
- Selected conditions:
  - `baseline_agent_completion_evidence`,
  - `telos_receipt_enforced_completion_evidence`.

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
- Secret boundary: credential material, project identifiers, account identifiers, and service
  account emails must not be committed or printed.

## Verification Plan

1. Verify the iter48 slice exists, passed, and selects exactly the two BattleSnake condition pairs.
2. Run a secret-safe provider, cost, runner, overlay, and artifact preflight.
3. Block before provider calls if credentials, quota, runner isolation, cost capture, artifact
   retention, redaction, or overlay placement cannot be proven.
4. If preflight passes, execute each selected pair exactly once with its frozen provider command.
5. Preserve raw logs, trajectories when present, diffs, metadata, cost/call stats, redaction scans,
   pair summaries, condition rows, command output, receipts, and adversarial review.
6. Compute metrics only from committed artifacts and report exact counts before percentages.
7. Publish blocked, null, failed, and pass rows at full weight.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- iter48 passed and the refrozen slice is unchanged,
- exactly two selected task-condition pairs are attempted or explicitly blocked by preflight,
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

- the iter48 refrozen slice or audit is missing,
- provider credentials, runner identity, service readiness, quota, or overlay placement is
  unavailable,
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
