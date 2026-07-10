# Iteration 86 Result - Discriminating Metric Backtest on Committed Artifacts

Status: `PASS`.

## Summary

This gate backtested the iter85 candidate metric from committed iter83 artifacts only. It made zero
provider calls, spent `$0.00`, and executed zero CodeClash rows.

- iter85 validation clean: `true`,
- metric: `task_native_score_share_delta_with_receipt_gates`,
- source rows parsed: `6`,
- task deltas computed: `3`,
- metric collapsed to completion boolean: `false`,
- mixed-direction diagnostic signal: `true`,
- provider calls in this gate: `0`,
- provider spend in this gate: `$0.00000000`,
- row execution in this gate: `0`,
- next-step decision: `pre_register_bounded_paid_discriminating_metric_execution`,
- next gate: `experiments/iter87_benchmark_facing_discriminating_metric_execution_pilot/HYPOTHESIS.md`,
- benchmark/model/SOTA claim: `false`,
- blockers: `none`,
- failures: `none`.

## Backtest Deltas

| Task surface | Baseline score share | Telos score share | Telos-minus-baseline |
| --- | --- | --- | --- |
| `dummy` | `0.49400000` | `0.49975000` | `0.00575000` |
| `battlesnake` | `1.00000000` | `0.00000000` | `-1.00000000` |
| `deterministic_edit` | `0.00000000` | `0.50000000` | `0.50000000` |

These are diagnostic backtest values from prior committed artifacts. They are not a benchmark
score, not fresh execution evidence, and not a model-superiority claim.

## Claim Boundary

This gate may claim only that the iter85 candidate metric is computable from committed iter83
artifacts and does not collapse to the saturated completion boolean. It is not a benchmark result,
SWE-bench score, leaderboard result, production/live-domain result, model-superiority result, or
state-of-the-art result.

## Evidence

- `proof/prerequisite_validation.json`
- `proof/raw_metric_extraction.json`
- `proof/backtest_report.json`
- `proof/next_step_decision.json`
- `proof/claim_boundary.json`
- `proof/redaction_scan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_discriminating_metric_backtest_on_committed_artifacts.json`
