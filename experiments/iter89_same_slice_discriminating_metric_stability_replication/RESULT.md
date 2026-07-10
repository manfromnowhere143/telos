# Iteration 89 Result - Same-Slice Discriminating Metric Stability Replication

Status: `PASS`.

## Summary

This gate ran the same six frozen rows as iter87 and evaluated fresh raw artifacts under
`task_native_score_share_delta_with_receipt_gates`. It is a bounded stability replication only, not a benchmark, model-superiority,
leaderboard, SWE-bench, production/live-domain, or state-of-the-art claim.

- iter88 validation clean: `true`,
- selected row count: `6`,
- executed row count: `6`,
- per-row provider call ceiling: `16`,
- provider API calls: `19`,
- provider call ceiling: `96`,
- provider cost from CodeClash metadata: `$0.11636200`,
- provider spend ceiling: `$10.00`,
- metric: `task_native_score_share_delta_with_receipt_gates`,
- fresh metric rows parsed: `6`,
- fresh task deltas computed: `3`,
- stability classification: `unstable`,
- stability subclassification: `iter89_mixed_against_prior_directions`,
- iter89 directions matching iter87: `2`,
- iter89 directions matching iter86: `0`,
- next gate: `experiments/iter90_stability_replication_adjudication_after_same_slice_run/HYPOTHESIS.md`,
- benchmark/model/SOTA claim: `false`,
- blockers: `none`,
- failures: `none`.

## Fresh Metric Deltas

| Task surface | Baseline score share | Telos score share | Telos-minus-baseline | Direction |
| --- | --- | --- | --- | --- |
| `dummy` | `0.51175000` | `0.49100000` | `-0.02075000` | `negative` |
| `battlesnake` | `0.50000000` | `0.50000000` | `0.00000000` | `zero` |
| `deterministic_edit` | `0.50000000` | `0.00000000` | `-0.50000000` | `negative` |

## Stability Comparison

| Task surface | Iter86 direction | Iter87 direction | Iter89 direction | Matches iter87 |
| --- | --- | --- | --- | --- |
| `dummy` | `positive` | `negative` | `negative` | `true` |
| `battlesnake` | `negative` | `positive` | `zero` | `false` |
| `deterministic_edit` | `positive` | `negative` | `negative` | `true` |

## Claim Boundary

This gate may claim only a bounded six-row same-slice stability replication and its stability
classification. It is not a benchmark result, SWE-bench score, leaderboard result,
production/live-domain result, model-superiority result, or state-of-the-art result.

## Evidence

- `proof/iter88_prerequisite_validation.json`
- `proof/execution_accounting_report.json`
- `proof/fresh_metric_extraction.json`
- `proof/stability_report.json`
- `proof/claim_boundary.json`
- `proof/protocol_effect_report.json`
- `proof/raw/`
- `proof/redaction_scan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_same_slice_discriminating_metric_stability_replication.json`
