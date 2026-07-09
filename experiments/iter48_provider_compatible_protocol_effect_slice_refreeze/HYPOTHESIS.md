# Iteration 48 - Provider-Compatible Protocol-Effect Slice Refreeze

Status: pre-registered, result pending.

## Purpose

`iter47` showed that the existing Vertex provider overlay binds only the BattleSnake PvP task
surface. This gate must refreeze the next provider-compatible protocol-effect slice before any paid
execution.

The goal is not to make the original six-pair plan sound executable. The goal is to choose the
smallest honest next slice whose provider-backed command surface is concrete.

## Frozen Input

- Original protocol-effect slice:
  `experiments/iter39_public_task_protocol_effect_slice/proof/protocol_effect_slice.json`.
- Executor manifest:
  `experiments/iter45_public_task_condition_executor_assembly/proof/executor_manifest.json`.
- Blocked execution proof:
  `experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor/proof/run_summary.json`.
- Command-binding report:
  `experiments/iter47_provider_task_condition_command_binding_recovery/proof/command_binding_report.json`.

## Verification Plan

1. Read the iter47 command-binding report.
2. Preserve all six original pairs as historical context.
3. Select only pairs with concrete provider-backed command bindings unless a new provider overlay is
   generated and audited at zero spend.
4. Emit a machine-readable provider-compatible slice with:
   - selected pair ids,
   - excluded pair ids and reasons,
   - exact future commands,
   - provider overlay files,
   - budget ceiling,
   - artifact plan,
   - cost/call stats plan,
   - redaction plan,
   - receipt plan,
   - metric plan,
   - claim boundary.
5. Keep provider model calls at `0`.
6. Keep provider spend at `$0.00`.
7. Do not start a cloud runner.
8. Do not request or use GPU.
9. Do not modify Sentinel-named resources.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- the slice includes only concrete provider-backed command bindings,
- every excluded original pair has a reason,
- baseline and Telos receipt-enforced conditions remain separated for selected tasks,
- exact commands name the provider overlay and output roots,
- provider model API calls remain `0`,
- provider spend remains `$0.00`,
- no cloud runner starts,
- no GPU is used,
- no Sentinel-named resource is modified,
- no benchmark, leaderboard, SWE-bench, production, live-domain, model-superiority, or
  state-of-the-art result is claimed.

## Falsifiers

Publish blocked/null evidence if:

- no provider-compatible condition pair remains,
- selected pairs are not condition-balanced,
- exact provider commands are missing,
- excluded pairs lack reasons,
- artifact, cost, redaction, lifecycle, receipt, or metric plans are missing.

Publish a quality failure, not a clean pass, if:

- an incompatible pair is silently included,
- a deterministic/no-provider command is labeled provider-backed,
- provider calls or spend occur in this refreeze gate,
- a cloud runner starts,
- GPU is requested or used,
- Sentinel-named resources are modified,
- unsupported benchmark/model/production claims appear.

## Scope Boundary

This is a provider-compatible slice-refreeze gate. It is not a provider-backed execution, not a
leaderboard run, not a SWE-bench result, not a production/live-domain verification, and not a
general model-superiority or state-of-the-art claim.
