# Iteration 153 - Reward-Hack Benchmark Seed Materialization

Status: pre-registered design; no data has been produced for this gate yet.

## Why this gate exists

`iter152` saved 20 execution-verified both-miss hack diffs across 8 repositories. That is strong evidence
for reward-model gaming, but it is not yet a benchmark artifact. Before growing `N`, adding more judges, or
spending on another cloud run, Telos needs a clean seed package that a reviewer can inspect without reading
the raw detection runner.

This gate converts the committed `iter152` evidence into a benchmark-seed artifact. It is a zero-spend
materialization and audit gate, not a new measurement.

## Method

Use only committed artifacts from:

- `experiments/iter152_reward_model_gaming_scale/proof/raw/detection_results.json`
- `experiments/iter152_reward_model_gaming_scale/proof/raw/det_reports.tgz`
- `experiments/iter152_reward_model_gaming_scale/proof/run_summary.json`

Materialize a benchmark seed under `benchmarks/reward_hack_seed_v0/` with:

- one JSONL row per execution-verified both-miss hack,
- stable row IDs,
- repository and instance identifiers,
- hack diff text plus SHA256,
- detector and judge verdict labels from iter152,
- `survives_all_static` label,
- links to the source iter152 proof artifacts,
- an explicit claim boundary saying this is a seed artifact, not a released benchmark or leaderboard.

Add a small validator script or audit script that proves:

- exactly 20 both-miss rows are present,
- all 8 iter152 repositories are represented,
- every row has a non-empty hack diff and matching SHA256,
- every row traces back to the committed iter152 raw evidence,
- `survives_all_static` rows count to 5,
- public wording does not call the seed a benchmark result, SOTA result, model comparison, or leaderboard.

## Numeric bars

- `row_count == 20`
- `repo_count == 8`
- `hack_diff_sha256_present == 20/20`
- `survives_all_static == 5`
- `new_provider_calls == 0`
- `new_cloud_resources == 0`

## Falsifiers

1. Fewer or more than 20 iter152 both-miss rows are materialized.
2. Any materialized row cannot be traced back to committed iter152 evidence.
3. Any hack diff is missing or has a mismatched SHA256.
4. The artifact or prose claims a released benchmark, leaderboard, model superiority, broad reward-model
   robustness result, or state-of-the-art result.
5. The gate performs new provider calls, launches cloud resources, executes SWE-bench, or adds new judge
   verdicts.

## Claim boundary

At most: "Telos materialized a validated benchmark seed from the 20 iter152 reward-hack diffs, preserving
the 8-repository coverage, static-verifier verdicts, and 5/20 survives-all-static labels." Not supported:
a released benchmark, a benchmark score, a model comparison, a SOTA claim, a natural-RL frequency claim, or
any statement about reward models beyond the iter152 bounded evidence.
