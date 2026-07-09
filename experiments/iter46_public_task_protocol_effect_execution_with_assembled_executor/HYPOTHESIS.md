# Iteration 46 - Public Task Protocol-Effect Execution With Assembled Executor

Status: pre-registered, result pending.

## Purpose

`iter45` is expected to assemble a dry-run executor manifest for the frozen public task-condition
slice. This gate is the bounded provider-backed retry: execute the six frozen task-condition pairs
through that assembled executor, publish exact counts and costs, and stop at the pilot result
boundary.

The purpose is to measure protocol-effect evidence on a small public slice, not to claim a
leaderboard score or model-superiority result.

## Frozen Input

- Protocol-effect slice:
  `experiments/iter39_public_task_protocol_effect_slice/proof/protocol_effect_slice.json`.
- Provider harness recovery:
  `experiments/iter43_provider_execution_harness_recovery/proof/run_summary.json`.
- Execution-after-harness blocked result:
  `experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/RESULT.md`.
- Executor manifest:
  `experiments/iter45_public_task_condition_executor_assembly/proof/executor_manifest.json`.
- Frozen task identifiers:
  - `codeclash:configs/test/dummy.yaml`,
  - `codeclash:configs/test/battlesnake_pvp_test.yaml`,
  - `codeclash:configs/test/telos_battlesnake_edit_test.yaml`.
- Frozen conditions:
  - `baseline_agent_completion_evidence`,
  - `telos_receipt_enforced_completion_evidence`.

## Provider And Runtime Budget

- Provider: Google Vertex AI, using the model path frozen by `iter39`.
- Maximum provider model invocations: `48`.
- Maximum provider spend: `$25.00`.
- Wall-clock ceiling: `90` minutes.
- GPU use: forbidden.
- Runner: a Telos-named ephemeral non-GPU runner only.
- Sentinel isolation: Sentinel-named resources may be counted for safety visibility but must not be
  modified, stopped, started, deleted, or reused.
- Secret boundary: credential material, project identifiers, account identifiers, and service
  account emails must not be committed or printed.

## Execution Plan

1. Verify the `iter45` executor manifest exists, is audited, and contains exactly six dry-run pairs.
2. Run only those six frozen pairs through the recovered provider harness.
3. Collect raw logs, trajectory artifacts when present, metadata, diffs, cost/call stats,
   redaction scans, pair summaries, condition rows, and command output.
4. Compute primary and secondary metrics separately for baseline and Telos receipt-enforced
   conditions.
5. Publish all blocked, null, failed, and successful pair rows at full weight.
6. Stop immediately if cost capture, redaction, artifact retention, runner lifecycle, or receipt
   validation cannot be proven.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- `iter45` passed and the assembled executor manifest is unchanged,
- exactly six task-condition pairs are attempted or explicitly blocked by a recorded preflight,
- no task or condition identifier changes,
- baseline and Telos receipt-enforced rows remain separate,
- provider model invocations are `<= 48`,
- provider spend is `<= $25.00`,
- no GPU is requested or used,
- any Telos runner started by the gate is deleted before publication,
- raw artifacts and pair summaries are committed or the missing artifact is counted as a result gap,
- cost/call stats are parsed from committed artifacts,
- redaction scan passes before publication,
- receipts validate for Telos-enforced rows where required,
- exact counts are reported before percentages,
- no leaderboard, SWE-bench score, production/live-domain, model-superiority, or state-of-the-art
  result is claimed.

## Falsifiers

Publish blocked/null evidence if:

- the `iter45` manifest or audit is missing,
- provider credentials, runner identity, service readiness, or quota is unavailable,
- runner lifecycle cannot be proven without touching Sentinel-named resources,
- cost/call stats cannot be parsed,
- required raw artifacts or hashes are missing,
- redaction cannot prove the committed packet is secret-safe.

Publish a quality failure, not a clean pass, if:

- any task-condition pair is dropped, renamed, duplicated, or silently skipped,
- provider spend exceeds `$25.00`,
- model invocations exceed `48`,
- GPU is requested or used,
- a Telos runner remains active after the gate,
- Sentinel-named resources are modified,
- metrics are computed from uncommitted artifacts,
- unsupported benchmark/model/production claims appear.

## Claim Boundary

If successful, this gate may claim only a bounded six-pair Telos protocol-effect pilot result on
the frozen CodeClash task surfaces with a SWE-bench Verified receipt-field anchor. It may not claim
a SWE-bench score, leaderboard position, production/live-domain result, general model superiority,
or state-of-the-art benchmark/model result.
