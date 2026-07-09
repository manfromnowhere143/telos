# Iteration 45 - Public Task-Condition Executor Assembly

Status: pre-registered, result pending.

## Purpose

`iter44` blocked because the recovered provider harness still disables full protocol-effect
execution. This gate assembles the missing executor layer without running provider models: it must
map the three frozen CodeClash task surfaces across the two frozen conditions and prove the run plan,
artifact plan, redaction plan, cost parser, lifecycle plan, and metric computation can dry-run.

## Frozen Input

- Protocol-effect slice:
  `experiments/iter39_public_task_protocol_effect_slice/proof/protocol_effect_slice.json`.
- Harness recovery:
  `experiments/iter43_provider_execution_harness_recovery/RESULT.md`.
- Blocked execution-after-harness result:
  `experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/RESULT.md`.
- Frozen task identifiers:
  - `codeclash:configs/test/dummy.yaml`,
  - `codeclash:configs/test/battlesnake_pvp_test.yaml`,
  - `codeclash:configs/test/telos_battlesnake_edit_test.yaml`.
- Frozen conditions:
  - baseline agent completion evidence,
  - Telos receipt-enforced completion evidence.

## Verification Plan

1. Add or update a committed executor that can enumerate the exact six task-condition pairs.
2. Keep provider model calls at `0`; this is an assembly and dry-run gate only.
3. Prove the executor records for each pair:
   - task identifier,
   - condition identifier,
   - frozen command or provider-backed command template,
   - artifact destination,
   - required raw logs and trajectory paths,
   - cost-stat source,
   - redaction scan source,
   - receipt expectation,
   - metric row destination.
4. Dry-run the executor so it emits the full execution manifest without starting a cloud runner or
   calling a model.
5. Audit that no task-condition pair is dropped, duplicated, or renamed.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- exactly six task-condition pairs are enumerated,
- baseline and Telos-enforced conditions remain separate,
- every pair has artifact, cost, redaction, lifecycle, and metric destinations,
- the executor refuses full execution unless an explicit later gate enables it,
- provider model API calls remain `0`,
- provider spend remains `$0.00`,
- no cloud runner is started,
- no GPU is used,
- no benchmark, leaderboard, SWE-bench, production, live-domain, model-superiority, or
  state-of-the-art result is claimed.

## Falsifiers

Publish blocked/null evidence if:

- the executor cannot represent all six frozen task-condition pairs,
- the provider-backed command template cannot be represented without secrets,
- artifact, cost, redaction, lifecycle, or metric destinations are missing,
- the dry-run cannot be audited from committed artifacts.

Publish a quality failure, not a clean pass, if:

- the executor changes task identifiers or condition identifiers,
- any full task-condition pair is executed in this assembly gate,
- any provider model call occurs,
- any cloud runner starts,
- metrics are computed from uncommitted artifacts,
- unsupported benchmark/model/production claims appear.

## Scope Boundary

This is an executor-assembly dry-run gate. It is not the provider-backed six-pair execution, not a
leaderboard run, not a SWE-bench result, not a production/live-domain verification, and not a
general model-superiority or state-of-the-art claim.
