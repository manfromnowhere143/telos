# Iteration 43 - Provider Execution Harness Recovery

Status: pre-registered, result pending.

## Purpose

`iter42` blocked the protocol-effect execution retry because the repo did not contain an auditable
provider-capable execution harness for the frozen six task-condition pairs. This gate recovers that
harness before any full provider-backed protocol-effect execution starts.

## Frozen Input

- Protocol-effect slice:
  `experiments/iter39_public_task_protocol_effect_slice/proof/protocol_effect_slice.json`.
- Blocked execution retry:
  `experiments/iter42_public_task_protocol_effect_execution_retry/RESULT.md`.
- Runner-recovery proof:
  `experiments/iter41_public_task_protocol_effect_runner_recovery/proof/runner_recovery_report.json`.
- Prior provider evidence boundary:
  `experiments/iter21_opponent_collision_control/proof/run_summary.json`.
- Provider boundary remains:
  - provider: Google Vertex AI,
  - model: `gemini-3.1-pro-preview-customtools`,
  - region: `global`,
  - no full task-condition execution in this harness-recovery gate,
  - maximum model invocations: `1` minimal access probe if needed,
  - maximum output tokens for any access probe: `4`,
  - dollar ceiling: `$1`,
  - wall-clock ceiling: `45` minutes.

## Verification Plan

1. Recover a committed provider-execution harness path: either a provider-capable GitHub Actions
   workflow with a safe secret boundary or a reusable ephemeral GCE/Vertex CodeClash runner script.
2. Record secret-safe provider readiness without account, project, token, or credential material.
3. Prove runner lifecycle controls: create or identify the isolated runner, run bounded readiness
   checks, collect evidence, and delete or prove no new runner was created.
4. Prove pinned CodeClash availability and the frozen config paths without running the six
   protocol-effect task-condition pairs.
5. Prove cost capture, raw artifact retention, and redaction checks on a dry run or one minimal
   access probe.
6. Publish a harness receipt, command output, machine-readable proof, artifact hashes, and review.

## Clean-Pass Bar

The gate can pass only if all hold:

- provider-capable execution is represented by committed reusable code or workflow,
- provider credentials and project/account identifiers are not committed or printed,
- runner lifecycle is proven and any ephemeral runner is deleted,
- pinned CodeClash commit and frozen config paths are verified,
- provider model invocations are `0` unless one minimal access probe is required,
- any access probe reports exact call count, token ceiling, and cost under `$1`,
- cost capture is proven before a future full execution retry,
- raw artifact retention and redaction checks are proven,
- no baseline/Telos task-condition pair from the frozen iter39 slice is executed,
- no benchmark, leaderboard, SWE-bench, production, live-domain, model-superiority, or
  state-of-the-art result is claimed.

## Falsifiers

Publish blocked/null evidence if:

- provider credentials, service readiness, or isolated runner lifecycle cannot be verified without
  logging identifiers,
- no provider-capable harness can be committed,
- cost capture cannot be measured or guaranteed,
- raw artifacts cannot be retained and scanned safely,
- runner deletion cannot be proven after a created runner,
- the run would exceed `$1` or more than one model invocation.

Publish a quality failure, not a clean pass, if:

- a full protocol-effect task-condition pair is executed in this harness-recovery gate,
- any secret material, project identifier, account identifier, or credential path is committed,
- prior provider evidence is presented as a current reusable harness without new harness proof,
- unsupported benchmark, model-superiority, production, live-domain, leaderboard, SWE-bench, or
  state-of-the-art claims appear.

## Scope Boundary

This is a provider-execution harness recovery gate. It is not the protocol-effect execution result,
not a leaderboard run, not a SWE-bench result, not a production/live-domain verification, and not a
general model-superiority or state-of-the-art claim.
