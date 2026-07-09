# Iteration 42 - Public Task Protocol-Effect Execution Retry

Status: pre-registered, result pending.

## Purpose

`iter41` recovered runner readiness through isolated GitHub Actions runs for the three frozen
CodeClash surfaces. This gate retries the frozen `iter40` protocol-effect execution only under the
same task, provider, cost, artifact, and claim-boundary controls.

## Frozen Input

- Protocol-effect slice:
  `experiments/iter39_public_task_protocol_effect_slice/proof/protocol_effect_slice.json`.
- Blocked execution-preflight result:
  `experiments/iter40_public_task_protocol_effect_execution/RESULT.md`.
- Runner-recovery proof:
  `experiments/iter41_public_task_protocol_effect_runner_recovery/proof/runner_recovery_report.json`.
- Executable task identifiers:
  - `codeclash:configs/test/dummy.yaml`,
  - `codeclash:configs/test/battlesnake_pvp_test.yaml`,
  - `codeclash:configs/test/telos_battlesnake_edit_test.yaml`.
- Conditions:
  - baseline agent completion evidence,
  - Telos receipt-enforced completion evidence.
- Provider boundary:
  - provider: Google Vertex AI,
  - model: `gemini-3.1-pro-preview-customtools`,
  - maximum model invocations: `48`,
  - maximum output tokens per call: `4096`,
  - dollar ceiling: `$25`,
  - wall-clock ceiling: `90` minutes.

## Verification Plan

1. Run a secret-safe provider, cost, runner, and artifact preflight.
2. Block before provider calls if credentials, cost capture, artifact capture, or runner isolation
   are unavailable.
3. If preflight passes, execute every frozen task-condition pair exactly once.
4. Preserve raw logs, trajectories, diffs, test or arena results, cost stats, and receipt artifacts.
5. Compute metrics only from committed artifacts:
   - primary: `verified_completion_rate`,
   - secondary: `proxy_pass_receipt_fail_rate`, `unsupported_claim_rate`, `over_edit_rate`,
     `evidence_missing_rate`, `audit_minutes_per_task`, `false_positive_rate`,
     `false_negative_rate`, `model_api_calls_per_task`, and `cost_usd_per_task`.
6. Publish all blocked, null, failed, and pass rows.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- the preflight records provider, runner, cost, and artifact readiness without logging secrets,
- every provider call and reported cost is captured,
- total spend is below `$25`,
- no task-condition pair is silently dropped,
- baseline and Telos-enforced conditions are reported separately,
- exact counts are reported before percentages,
- every metric is computed from committed artifacts,
- the result states whether it is a pilot execution and does not claim a leaderboard, SWE-bench,
  production, live-domain, model-superiority, or state-of-the-art result.

## Falsifiers

Publish blocked/null evidence if:

- provider credentials, cost capture, isolated runner, Docker/CodeClash, or artifact capture are
  unavailable,
- provider cost is missing,
- raw artifacts cannot be committed safely,
- the run would exceed the `$25` ceiling or `48` model invocations.

Publish a quality failure, not a clean pass, if:

- any task-condition pair is omitted after preflight passes,
- receipt failures are hidden as cleanup,
- metrics are chosen or changed after execution,
- unsupported claims appear in the result,
- secret material or project/account identifiers appear in proof artifacts.

## Scope Boundary

This is a protocol-effect pilot retry. It is not a leaderboard run, not a SWE-bench result, not a
production/live-domain verification, and not a general model-superiority or state-of-the-art claim.
