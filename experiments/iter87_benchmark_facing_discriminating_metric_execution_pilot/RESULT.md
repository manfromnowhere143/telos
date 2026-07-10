# Iteration 87 Result - Benchmark-Facing Discriminating Metric Execution Pilot

Status: `PASS`.

## Summary

This gate ran the bounded six-row provider-backed pilot envelope and evaluated the fresh raw
artifacts under `task_native_score_share_delta_with_receipt_gates`. It does not make a benchmark, model-superiority, leaderboard,
SWE-bench, production/live-domain, or state-of-the-art claim.

- iter86 validation clean: `true`,
- selected row count: `6`,
- executed row count: `6`,
- per-row provider call ceiling: `16`,
- provider API calls: `21`,
- provider call ceiling: `96`,
- provider cost from CodeClash metadata: `$0.12498400`,
- provider spend ceiling: `$10.00`,
- metric: `task_native_score_share_delta_with_receipt_gates`,
- fresh metric rows parsed: `6`,
- fresh task deltas computed: `3`,
- metric collapsed to completion boolean: `false`,
- mixed-direction signal: `true`,
- GPU used: `false`,
- cloud runner started: `false`,
- Sentinel-named resources modified: `false`,
- benchmark/model/SOTA claim: `false`,
- blockers: `none`,
- failures: `none`.

## Fresh Metric Deltas

| Task surface | Baseline score share | Telos score share | Telos-minus-baseline |
| --- | --- | --- | --- |
| `dummy` | `0.51325000` | `0.49750000` | `-0.01575000` |
| `battlesnake` | `0.50000000` | `1.00000000` | `0.50000000` |
| `deterministic_edit` | `0.50000000` | `0.00000000` | `-0.50000000` |

These are bounded protocol-effect pilot values from six frozen rows. They are not an aggregate
benchmark score and do not establish model superiority or state-of-the-art status.

## Claim Boundary

This gate may claim only bounded provider-backed protocol-effect pilot evidence under a
task-native score-share metric. It is not a benchmark result, SWE-bench score, leaderboard result,
production/live-domain result, model-superiority result, or state-of-the-art result.

## Evidence

- `proof/iter86_prerequisite_validation.json`
- `proof/execution_accounting_report.json`
- `proof/fresh_metric_extraction.json`
- `proof/discriminating_metric_report.json`
- `proof/claim_boundary.json`
- `proof/protocol_effect_report.json`
- `proof/raw/`
- `proof/redaction_scan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_benchmark_facing_discriminating_metric_execution_pilot.json`
