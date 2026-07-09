# Iteration 39 - Public Task Protocol-Effect Slice Result

Status: `PASS`

## Result

The public task protocol-effect slice was selected.

The slice freezes three executable CodeClash task surfaces, one SWE-bench Verified receipt anchor,
a baseline condition, a Telos-enforced condition, one primary metric, nine secondary metrics, and a
bounded provider execution gate for the next iteration.

## Frozen Slice

Slice ID:

```text
telos_codeclash_swebench_protocol_effect_pilot_v1
```

Executable task identifiers:

- `codeclash:configs/test/dummy.yaml`
- `codeclash:configs/test/battlesnake_pvp_test.yaml`
- `codeclash:configs/test/telos_battlesnake_edit_test.yaml`

Receipt anchor:

- `SWE-bench Verified` instance `astropy__astropy-12907`

Conditions:

- baseline condition: collect completion evidence without requiring a Telos receipt before
  interpretation,
- Telos-enforced condition: fail the task when required receipt evidence, hashes, falsifiers, or
  claim boundaries are missing.

Primary metric:

- `verified_completion_rate`

Secondary metrics:

- `proxy_pass_receipt_fail_rate`
- `unsupported_claim_rate`
- `over_edit_rate`
- `evidence_missing_rate`
- `audit_minutes_per_task`
- `false_positive_rate`
- `false_negative_rate`
- `model_api_calls_per_task`
- `cost_usd_per_task`

## Next Execution Boundary

The next gate may use the frozen provider boundary only if credentials, runner state, cost tracking,
and artifact capture are available:

- provider: Google Vertex AI,
- model: `gemini-3.1-pro-preview-customtools`,
- maximum model invocations: `48`,
- maximum output tokens per call: `4096`,
- dollar ceiling: `$25`,
- wall-clock ceiling: `90` minutes,
- stop if cost is missing,
- stop if credentials or runner state are unavailable.

## What Passed

- No provider, API, GPU, or cloud spend occurred in this slice-selection gate.
- Exact public task identifiers were frozen.
- Baseline and Telos-enforced conditions were specified before execution.
- Primary and secondary metrics were specified before execution.
- Negative controls and claim boundaries were specified.
- No leaderboard, SWE-bench, production, live-domain, model-superiority, or state-of-the-art result
  is claimed.

## Claim Boundary

This is a slice-selection result. It does not run CodeClash, call a provider model, produce a
leaderboard score, produce a SWE-bench score, or prove model superiority.

No provider model was called. This is not a leaderboard result.

## Evidence

- Protocol-effect slice: [`proof/protocol_effect_slice.json`](proof/protocol_effect_slice.json)
- Summary: [`proof/run_summary.json`](proof/run_summary.json)
- Command output: [`proof/command_output.txt`](proof/command_output.txt)
- Review: [`proof/review.md`](proof/review.md)
- Sources: [`proof/sources.md`](proof/sources.md)
- Learning record: [`proof/learning_record.json`](proof/learning_record.json)
- Receipt: [`proof/valid/receipt_public_task_protocol_effect_slice.json`](proof/valid/receipt_public_task_protocol_effect_slice.json)

## Next Gate

Run `iter40_public_task_protocol_effect_execution`: execute the frozen slice only under the recorded
provider, cost, artifact, and claim-boundary controls. If any preflight fails, publish the
blocked/null result instead of widening the claim.
