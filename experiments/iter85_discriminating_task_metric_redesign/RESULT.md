# Iteration 85 Result - Discriminating Task/Metric Redesign

Status: `PASS`.

## Summary

This gate redesigned the benchmark-facing protocol-effect metric from committed evidence only. It
made zero provider calls, spent `$0.00`, and executed zero CodeClash rows.

- iter84 validation clean: `true`,
- prior classification: `verified_completion_metric_saturated`,
- redesigned metric: `task_native_score_share_delta_with_receipt_gates`,
- metric status: `candidate_contract_frozen_for_zero_spend_backtest`,
- source rows inventoried: `6`,
- task-native score fields available for all rows: `true`,
- provider calls in this gate: `0`,
- provider spend in this gate: `$0.00000000`,
- row execution in this gate: `0`,
- future paid execution authorized by this gate: `false`,
- next gate: `experiments/iter86_discriminating_metric_backtest_on_committed_artifacts/HYPOTHESIS.md`,
- benchmark/model/SOTA claim: `false`,
- blockers: `none`,
- failures: `none`.

## Candidate Metric

The prior verified-completion boolean remains an admissibility gate only. The candidate primary
metric is task-native controlled-player score share:

`sum(controlled_player_score) / sum(all_player_scores)`, compared as
`Telos score share - baseline score share` within the same `public_config`.

## Design-Time Field Inventory

| Task surface | Baseline score share | Telos score share | Candidate delta |
| --- | --- | --- | --- |
| `dummy` | `0.49400000` | `0.49975000` | `0.00575000` |
| `battlesnake` | `1.00000000` | `0.00000000` | `-1.00000000` |
| `deterministic_edit` | `0.00000000` | `0.50000000` | `0.50000000` |

These field values prove the candidate metric is not identical to the saturated completion
boolean, but they are design evidence only. Iter86 must backtest the extractor and publish the
metric result from committed artifacts before any paid execution is proposed.

## Claim Boundary

This gate may claim only that a zero-spend task-native metric contract has been designed and
pre-registered for backtest. It is not a benchmark result, SWE-bench score, leaderboard result,
production/live-domain result, model-superiority result, or state-of-the-art result.

## Evidence

- `proof/prerequisite_validation.json`
- `proof/saturation_critique.json`
- `proof/source_field_inventory.json`
- `proof/metric_contract.json`
- `proof/task_eligibility_rules.json`
- `proof/future_gate_plan.json`
- `proof/claim_boundary.json`
- `proof/redaction_scan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_discriminating_task_metric_redesign.json`
