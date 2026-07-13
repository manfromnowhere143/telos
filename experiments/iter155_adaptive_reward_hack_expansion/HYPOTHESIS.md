# Iteration 155 - Adaptive Reward-Hack Expansion

Status: pre-registered design; adaptive candidate pool frozen before provider outcomes; redacted
provider/cloud preflight passed; no iter155 execution data has been produced yet.

## Why this gate exists

`iter154` honestly missed its pre-registered expansion bar: a frozen round-robin pool produced `17`
execution-verified new both-miss rows, not the required `20`. It also produced a useful signal: accepted
rows clustered in productive strata while still covering `10` repositories, and `8` new rows survived every
static layer. The next gate should learn from that evidence explicitly instead of silently changing iter154.

## Method

Inputs:

- `benchmarks/reward_hack_seed_v0/reward_hack_seed_v0.jsonl`
- `experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/eligible_candidate_pool.json`
- `experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/expansion_results.json`
- committed iter154 runner and proof artifacts

Candidate selection:

- exclude every seed-v0 instance,
- exclude every iter154 processed candidate,
- start from the remaining iter154 eligible pool,
- prioritize repositories that produced at least one iter154 accepted row, while retaining at least three
  repositories if enough candidates remain,
- prefer candidates whose gold patch adds a compact source block and has at least four `PASS_TO_PASS`
  checks, because iter154 target failures were common when the rewrite damaged visible behavior,
- freeze the selected adaptive pool before any new provider call.

Frozen no-spend pool:

- `proof/raw/adaptive_candidate_pool.json`
- `proof/adaptive_pool_summary.json`
- `48` selected candidates across `6` repositories
- `38/48` candidates from repositories that produced at least one iter154 accepted row
- `47/48` candidates meet the `PASS_TO_PASS >= 4` preference
- `46/48` candidates meet the compact-added-block preference
- `0` duplicates with seed-v0 rows or iter154 processed candidates
- `0` provider calls, `0` SWE-bench executions, and `0` cloud resources created

Redacted preflight:

- `proof/preflight_report.json`
- `ready_for_cloud_execution: true`
- `gpt-5.6-terra` readiness `true`
- `claude-opus-4-8` readiness `true`
- `0` execution blockers
- redaction flags confirm no secrets, bearer tokens, account IDs, project IDs, or raw model text were
  written

Execution:

- use the patched iter154 remote runner or a narrowly scoped successor that preserves the same acceptance
  rule: official SWE-bench target pass and held-out failure,
- label every accepted row with the deterministic detector, `gpt-5.6-terra`, and `claude-opus-4-8`,
- do not add a third judge unless a separate preflight succeeds before execution,
- archive raw model-call ledgers, official reports, and cloud lifecycle evidence,
- delete every VM and firewall before publication.

## Numeric Bars

Minimum pass bars:

- `additional_execution_verified_both_miss >= 3`
- `total_seed_plus_iter154_plus_iter155_rows >= 40`
- `additional_rows_with_hack_diff_sha256 == additional_execution_verified_both_miss`
- `additional_rows_with_official_report_hash == additional_execution_verified_both_miss`
- `additional_rows_traceable_to_raw_evidence == additional_execution_verified_both_miss`
- `duplicate_seed_or_iter154_instances == 0`
- `provider_plus_cloud_spend_usd <= 250`
- `undeleted_cloud_resources == 0`

Reported but not pass-required:

- `additional_survives_all_static`
- per-repository acceptance counts
- provider call errors

## Falsifiers

1. The adaptive pool is selected after seeing iter155 provider outcomes.
2. Any counted iter155 row duplicates seed-v0 or an iter154 processed candidate.
3. Any counted row lacks a hack diff, SHA256, source raw row, or official execution report hash.
4. The gate claims a released benchmark before the `>=40` total-row bar is met.
5. Provider/cloud spend exceeds the ceiling or any VM/firewall remains after the result.
6. The result claims a leaderboard, model superiority, state-of-the-art result, broad reward-model
   robustness, or natural-RL reward-hacking frequency.

## Claim Boundary

At most: "Telos used iter154's published shortfall evidence to adaptively add `N` more
execution-verified constructed both-miss rows and, if `N >= 3`, crossed the 40-row candidate benchmark-size
bar." Not supported: a released public benchmark without a manifest gate, a model score, a leaderboard,
state-of-the-art performance, natural reward-hacking frequency, or broad reward-model robustness.
