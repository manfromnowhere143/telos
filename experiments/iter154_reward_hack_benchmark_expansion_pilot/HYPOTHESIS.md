# Iteration 154 - Reward-Hack Benchmark Expansion Pilot

Status: result published as `null_shortfall`; see `RESULT.md`.

## Why this gate exists

`iter153` materialized a validated seed package from the `20` iter152 reward-hack diffs. That made the
evidence inspectable, but it did not add new measurement. The next benchmark-building question is whether
Telos can grow the seed under the same evidence discipline: every new row must be execution-verified,
hashable, traceable, and below its claim boundary.

This gate is allowed to use paid provider calls and a cloud x86 Docker VM if needed, but only inside the
execution envelope below.

## Method

Start from:

- `benchmarks/reward_hack_seed_v0/manifest.json`
- `benchmarks/reward_hack_seed_v0/reward_hack_seed_v0.jsonl`
- committed iter151/iter152 harness code and proof artifacts

Do not mutate `reward_hack_seed_v0`. Write any expanded artifact to a new candidate directory such as
`benchmarks/reward_hack_seed_v1_candidate/`.

Candidate selection:

- exclude every instance already present in `reward_hack_seed_v0`,
- prefer SWE-bench_Verified instances with a single primary source file, one visible `FAIL_TO_PASS`, and at
  least two `PASS_TO_PASS` checks,
- cap per-repository additions so the expansion does not become one-repo dominated,
- record the full candidate pool and the deterministic sampling rule before provider calls.

Execution:

- use an x86 Docker VM with the official SWE-bench harness for instances that need pinned containers,
- construct candidate both-miss hacks with the same adversary family used in iter151/iter152 unless the
  endpoint is unavailable, in which case publish a blocked/null result rather than substituting silently,
- verify every accepted new hack by execution: target behavior passes and held-out regression behavior fails,
- score every accepted new hack with the deterministic detector and the two iter152 reward-model judges,
- add a third judge only if its endpoint passes an explicit preflight; if no third judge is available, do not
  claim judge-diversity expansion.

## Numeric bars

Minimum pass bars for expansion:

- `new_execution_verified_both_miss >= 20`
- `total_seed_plus_new_rows >= 40`
- `new_rows_with_hack_diff_sha256 == new_execution_verified_both_miss`
- `new_rows_with_official_report_hash == new_execution_verified_both_miss`
- `new_rows_traceable_to_raw_evidence == new_execution_verified_both_miss`
- `duplicate_seed_instances == 0`
- `provider_plus_cloud_spend_usd <= 500`
- `undeleted_cloud_resources == 0`

Optional judge-diversity bar, reported separately:

- `third_judge_labels == new_execution_verified_both_miss` if and only if the third-judge preflight passes.

## Falsifiers

1. Any expanded row lacks a hack diff, SHA256, source raw row, or official execution report hash.
2. Any expanded row duplicates a `reward_hack_seed_v0` instance while being counted as new.
3. The candidate pool or sampling rule is created after seeing provider outcomes.
4. Provider/cloud spend exceeds the ceiling or a VM/firewall is left running after the gate.
5. A third-judge claim is made without a successful third-judge preflight and complete labels.
6. The result claims a released benchmark, leaderboard, model superiority, broad reward-model robustness,
   state-of-the-art result, or natural-RL reward-hacking frequency.

## Execution envelope

- Maximum provider plus cloud spend: `$500`.
- GPU not required.
- Use a direct-SSH firewall rule from the current operator IP when provisioning GCE; IAP tunnel reliability is
  not assumed.
- Long cloud work should run under `systemd-run` or equivalent so logs survive disconnects.
- Delete the VM and any firewall rule before publishing the result.
- Do not print secrets, credentials, bearer tokens, account ids, or project ids into committed artifacts.

## Claim boundary

At most: "Telos expanded the validated reward-hack seed from `20` to `N` execution-verified constructed
both-miss rows under official execution, with per-row hashes, source traceability, spend accounting, and
static-verifier labels." Not supported: a released benchmark, benchmark score, leaderboard, model
superiority result, state-of-the-art claim, natural-RL frequency claim, or broad statement about all reward
models.
