# Iteration 40 - Public Task Protocol-Effect Execution

Status: pre-registered, result pending.

## Purpose

`iter39` froze a public task protocol-effect slice. This gate will execute that slice only under the
recorded provider, cost, artifact, and claim-boundary controls so Telos can start measuring whether
receipt enforcement changes completion evidence on public tasks.

## Frozen Input

- Protocol-effect slice:
  `experiments/iter39_public_task_protocol_effect_slice/proof/protocol_effect_slice.json`.
- Executable task identifiers:
  - `codeclash:configs/test/dummy.yaml`,
  - `codeclash:configs/test/battlesnake_pvp_test.yaml`,
  - `codeclash:configs/test/telos_battlesnake_edit_test.yaml`.
- Receipt anchor: SWE-bench Verified instance `astropy__astropy-12907`.
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

1. Run secret-safe preflight for credentials, runner availability, cost logging, Docker/CodeClash
   readiness, and artifact destinations.
2. If preflight fails, publish a blocked/null result with no provider call.
3. If preflight passes, execute the frozen task-condition pairs.
4. Preserve raw logs, trajectories, diffs, test/arena results, cost stats, and receipt artifacts.
5. Compute metrics from committed artifacts only:
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
- no leaderboard, SWE-bench, production, live-domain, model-superiority, or state-of-the-art result
  is claimed.

## Falsifiers

Publish blocked/null evidence if:

- credentials, Docker, CodeClash, runner state, or cost tracking are unavailable,
- provider cost is missing,
- raw artifacts cannot be committed safely,
- the run would exceed the `$25` ceiling or `48` model invocations.

Publish a quality failure, not a clean pass, if:

- any task-condition pair is omitted after preflight passes,
- receipt failures are hidden as cleanup,
- metrics are chosen or changed after execution,
- unsupported claims appear in the result,
- secret material appears in proof artifacts.

## Scope Boundary

This is a protocol-effect pilot execution. It is not a leaderboard run, not a SWE-bench result, not
a production/live-domain verification, and not a general model-superiority claim.
