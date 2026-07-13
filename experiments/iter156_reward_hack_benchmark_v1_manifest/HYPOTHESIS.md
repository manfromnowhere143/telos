# Iteration 156 - Reward-Hack Benchmark v1 Manifest

Status: result published; the v1 manifest was materialized in `RESULT.md`.

## Why this gate exists

`iter155` crossed the 40-row candidate benchmark-size bar by combining:

- `20` validated seed rows from `reward_hack_seed_v0`,
- `17` iter154 expansion rows,
- `3` iter155 adaptive expansion rows.

That is enough to justify a release-manifest gate, but not enough to claim a released benchmark. A
reviewer-facing benchmark artifact needs row-level joins, duplicate checks, hash checks, source
traceability, static-verifier labels, and public claim boundaries in one audited packet.

## Method

Inputs:

- `benchmarks/reward_hack_seed_v0/reward_hack_seed_v0.jsonl`
- `benchmarks/reward_hack_seed_v0/manifest.json`
- `experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/expansion_rows.jsonl`
- `experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/expansion_results.json`
- `experiments/iter155_adaptive_reward_hack_expansion/proof/raw/expansion_rows.jsonl`
- `experiments/iter155_adaptive_reward_hack_expansion/proof/raw/expansion_results.json`
- iter153, iter154, and iter155 endpoint, audit, receipt, and learning records

Planned output:

- a `benchmarks/reward_hack_benchmark_v1/` artifact or a published null explaining why the manifest
  cannot be released,
- one manifest row per included execution-verified both-miss row,
- source experiment and source row hash for every row,
- `instance_id`, repository, hack diff SHA256, official report SHA256, static-verifier labels, and
  raw artifact paths for every row,
- a release receipt and audit report.

## Numeric Bars

Minimum pass bars:

- `manifest_row_count == 40`
- `unique_instance_ids == 40`
- `rows_with_execution_verified_both_miss == 40`
- `rows_with_hack_diff_sha256 == 40`
- `rows_with_official_report_hash >= 40`
- `rows_with_source_traceability == 40`
- `seed_rows == 20`
- `iter154_rows == 17`
- `iter155_rows == 3`
- `survives_all_static_rows >= 13`
- `new_provider_calls == 0`
- `new_swebench_executions == 0`
- `new_cloud_resources == 0`
- `benchmark_score_claimed == false`
- `leaderboard_claimed == false`
- `model_superiority_claimed == false`
- `sota_claimed == false`

Reported but not pass-required:

- per-repository row counts,
- per-static-layer fooled counts,
- row-source artifact hashes,
- rows excluded from release, if any.

## Falsifiers

1. Any manifest row duplicates another `instance_id`.
2. Any manifest row lacks an execution-verified both-miss source record.
3. Any manifest row lacks a hack diff hash, official report hash, or source artifact path.
4. The release wording claims a benchmark score, leaderboard, model superiority, state-of-the-art result,
   broad reward-model robustness, or natural reward-hacking frequency.
5. Any provider call, SWE-bench execution, cloud resource, GPU run, or live-domain mutation occurs during
   this zero-spend manifest gate.

## Claim Boundary

At most: "Telos released a hash-checked v1 artifact of `40` constructed, execution-verified both-miss
reward-hack rows gathered from iter152 through iter155." Not supported: a model benchmark score,
leaderboard ranking, state-of-the-art performance, natural reward-hacking frequency, or broad
reward-model robustness.
