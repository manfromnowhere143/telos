# Iteration 179 - Reward-Hack Panel Full-Cohort Adjudication

Status: pre-registered zero-spend adjudication gate; no provider calls, credential probes, model
evaluations, SWE-bench executions, cloud resources, benchmark scores, leaderboard claims,
model-comparison claims, state-of-the-art claims, natural-frequency claims, or broad robustness claims
have been run for this gate.

## Why this gate exists

Iter178 completes the bounded paid panel expansion over the remaining pairs and separately reports OpenAI
output-budget recovery diagnostics. Before any public-facing claim is upgraded, the full iter175+iter178
cohort must be adjudicated from committed proof artifacts with recovery rows kept diagnostic unless a new
pre-registered repair gate says otherwise.

## Method

Inputs:

- `experiments/iter175_reward_hack_panel_bounded_paid_pilot/RESULT.md`
- `experiments/iter175_reward_hack_panel_bounded_paid_pilot/proof/panel_metrics.json`
- `experiments/iter176_reward_hack_panel_result_adjudication/RESULT.md`
- `experiments/iter178_reward_hack_panel_remaining_pairs_paid_expansion/RESULT.md`
- `experiments/iter178_reward_hack_panel_remaining_pairs_paid_expansion/proof/panel_metrics.json`
- `experiments/iter178_reward_hack_panel_remaining_pairs_paid_expansion/proof/combined_unrepaired_diagnostic_table.json`
- `experiments/iter178_reward_hack_panel_remaining_pairs_paid_expansion/proof/openai_recovery_diagnostic_table.json`

Adjudication envelope:

- provider calls: `0`,
- credential probes: `0`,
- estimated provider spend: `$0.00`,
- new SWE-bench executions: `0`,
- new cloud runner/resources: `0`,
- primary rule remains `majority_catch`,
- recovery rows remain diagnostic unless explicitly marked out of score,
- no row, provider, parser, aggregation rule, or denominator substitution after outputs.

## Required Outputs

- recomputed full-cohort majority/any/unanimous panel metrics,
- row-level disagreement and nondecision audit across iter175 and iter178,
- OpenAI recovery effect boundary showing exactly what changed and what did not,
- claim-boundary decision for README/paper language,
- secret-safety audit, endpoint results, receipt, audit report, run summary, and learning record.

## Numeric Bars

Minimum pass bars:

- provider calls are exactly `0`,
- credential probes are exactly `0`,
- all recomputed full-cohort denominators match committed iter175+iter178 primary panel rows,
- OpenAI recovery diagnostics do not rewrite iter175 primary rows,
- no committed artifact contains a secret, private project/account identifier, service-account value,
  bearer token, or API key,
- no leaderboard, model-superiority, state-of-the-art, natural-frequency, broad robustness, or public
  benchmark-score claim is made.

## Falsifiers

1. The gate performs any provider call, credential probe, model evaluation, SWE-bench execution, or cloud
   resource change.
2. A parser, row, provider, aggregation rule, or denominator is changed after outputs.
3. Recovery diagnostics are used to rewrite iter175 primary metrics.
4. A committed artifact contains a secret, bearer token, service account, project ID, account ID, or private
   credential material.
5. The result presents a leaderboard, model-superiority, SOTA, natural-frequency, broad robustness, or
   public benchmark-score claim.

## Claim Boundary

At most, if this gate passes: Telos has a committed full-cohort adjudication of the bounded
reward-hack panel expansion and a precise claim boundary for paper/README language.

Not supported: a leaderboard ranking, state-of-the-art claim, natural reward-hacking frequency estimate,
broad reward-model robustness claim, production deployment claim, or any claim outside committed
iter175-iter179 proof packets.
