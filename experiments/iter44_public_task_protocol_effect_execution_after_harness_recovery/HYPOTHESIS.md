# Iteration 44 - Public Task Protocol-Effect Execution After Harness Recovery

Status: pre-registered, result pending.

## Purpose

`iter43` recovered the provider-capable execution harness without running the six frozen
task-condition pairs. This gate retries the frozen public-task protocol-effect execution under that
harness and the original provider, cost, artifact, and claim-boundary controls.

## Frozen Input

- Protocol-effect slice:
  `experiments/iter39_public_task_protocol_effect_slice/proof/protocol_effect_slice.json`.
- Blocked execution retry:
  `experiments/iter42_public_task_protocol_effect_execution_retry/RESULT.md`.
- Harness recovery:
  `experiments/iter43_provider_execution_harness_recovery/RESULT.md`.
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
  - region: `global`,
  - maximum model invocations: `48`,
  - maximum output tokens per call: `4096`,
  - dollar ceiling: `$25`,
  - wall-clock ceiling: `90` minutes.

## Verification Plan

1. Run a secret-safe preflight using the recovered harness.
2. Block before provider calls if credentials, cost capture, artifact capture, redaction, or runner
   lifecycle controls are unavailable.
3. Execute every frozen task-condition pair exactly once only after preflight passes.
4. Preserve raw logs, trajectories, diffs, test or arena results, cost stats, lifecycle evidence,
   redaction scan, and receipt artifacts.
5. Compute metrics only from committed artifacts:
   - primary: `verified_completion_rate`,
   - secondary: `proxy_pass_receipt_fail_rate`, `unsupported_claim_rate`, `over_edit_rate`,
     `evidence_missing_rate`, `audit_minutes_per_task`, `false_positive_rate`,
     `false_negative_rate`, `model_api_calls_per_task`, and `cost_usd_per_task`.
6. Publish all blocked, null, failed, and pass rows.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- the recovered harness is the execution path,
- the preflight records provider, runner, cost, redaction, and artifact readiness without logging
  secrets or identifiers,
- every provider call and reported cost is captured,
- total spend is below `$25`,
- no task-condition pair is silently dropped,
- baseline and Telos-enforced conditions are reported separately,
- exact counts are reported before percentages,
- every metric is computed from committed artifacts,
- any cloud runner created for execution is deleted,
- no benchmark, leaderboard, SWE-bench, production, live-domain, model-superiority, or
  state-of-the-art result is claimed.

## Falsifiers

Publish blocked/null evidence if:

- provider credentials, cost capture, artifact capture, redaction, isolated runner, Docker,
  CodeClash, or runner lifecycle controls are unavailable,
- provider cost is missing,
- raw artifacts cannot be committed safely,
- a runner created for this gate cannot be deleted,
- the run would exceed the `$25` ceiling or `48` model invocations.

Publish a quality failure, not a clean pass, if:

- any task-condition pair is omitted after preflight passes,
- receipt failures are hidden as cleanup,
- metrics are chosen or changed after execution,
- unsupported claims appear in the result,
- secret material or project/account identifiers appear in proof artifacts.

## Scope Boundary

This is a protocol-effect pilot execution, not a leaderboard run, not a SWE-bench result, not a
production/live-domain verification, and not a general model-superiority or state-of-the-art claim.
