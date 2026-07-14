# Iteration 180 - Reward-Hack Panel OpenAI Nondecision Repair Design

Status: pre-registered zero-spend design gate; no provider calls, credential probes, model
evaluations, SWE-bench executions, cloud resources, benchmark scores, leaderboard claims,
model-comparison claims, state-of-the-art claims, natural-frequency claims, broad robustness claims, or
repaired-score claims have been run for this gate.

## Why this gate exists

Iter179 adjudicated the full unrepaired iter175+iter178 panel cohort and kept OpenAI recovery diagnostics
out of score. The full cohort still has five primary panel nondecision rows caused by OpenAI empty output:
three from iter175, two fresh from iter178. A repair protocol must be designed before any paid repair call
or repaired-score report, so the process cannot use already-seen diagnostic outputs as a post-hoc metric
patch.

## Method

Inputs:

- `experiments/iter179_reward_hack_panel_full_cohort_adjudication/RESULT.md`
- `experiments/iter179_reward_hack_panel_full_cohort_adjudication/proof/row_level_disagreement_and_nondecision_audit.json`
- `experiments/iter179_reward_hack_panel_full_cohort_adjudication/proof/openai_recovery_effect_boundary.json`
- `experiments/iter178_reward_hack_panel_remaining_pairs_paid_expansion/proof/openai_recovery_diagnostic_table.json`

Design envelope:

- provider calls: `0`,
- credential probes: `0`,
- estimated provider spend: `$0.00`,
- new SWE-bench executions: `0`,
- new cloud runner/resources: `0`,
- define whether a future repair run should rerun all OpenAI empty-output primary slots, including rows
  that already have diagnostic outputs,
- keep unrepaired iter179 metrics as the primary public result unless a future gate pre-registers a
  separate repaired metric.

## Required Outputs

- complete OpenAI nondecision repair row list,
- repair call/spend ceiling proposal,
- rule for separating unrepaired primary metrics from repaired diagnostics,
- claim-boundary decision,
- secret-safety audit, endpoint results, receipt, audit report, run summary, and learning record.

## Numeric Bars

Minimum pass bars:

- provider calls are exactly `0`,
- credential probes are exactly `0`,
- every proposed repair row comes from an iter179 primary panel nondecision with OpenAI `empty_output`,
- already-seen diagnostic outputs are not used as repaired score evidence,
- no committed artifact contains a secret, private project/account identifier, service-account value,
  bearer token, or API key,
- no leaderboard, model-superiority, state-of-the-art, natural-frequency, broad robustness, public
  benchmark-score, or repaired-score claim is made.

## Falsifiers

1. The gate performs any provider call, credential probe, model evaluation, SWE-bench execution, or cloud
   resource change.
2. The repair row list includes a row that was not a primary OpenAI empty-output nondecision in iter179.
3. Already-seen diagnostic outputs are counted as repaired primary decisions.
4. The gate changes the unrepaired iter179 primary metric.
5. A committed artifact contains a secret, bearer token, service account, project ID, account ID, or
   private credential material.
6. The result presents a leaderboard, model-superiority, SOTA, natural-frequency, broad robustness,
   public benchmark-score, or repaired-score claim.

## Claim Boundary

At most, if this gate passes: Telos has a frozen design for a future OpenAI nondecision repair run and a
clear separation between unrepaired primary metrics and any later repaired diagnostic.

Not supported: a repaired panel score, leaderboard ranking, state-of-the-art claim, natural
reward-hacking frequency estimate, broad reward-model robustness claim, production deployment claim, or
any claim outside committed iter175-iter180 proof packets.
