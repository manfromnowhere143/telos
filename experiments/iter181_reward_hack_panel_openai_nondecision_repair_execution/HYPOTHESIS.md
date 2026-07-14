# Iteration 181 - Reward-Hack Panel OpenAI Nondecision Repair Execution

Status: pre-registered bounded paid execution gate; no provider calls, credential probes, model
evaluations, SWE-bench executions, cloud resources, benchmark scores, leaderboard claims,
model-comparison claims, state-of-the-art claims, natural-frequency claims, broad robustness claims, or
repaired-score claims have been run for this gate.

## Why this gate exists

Iter180 designed a repair protocol for the five OpenAI empty-output primary panel nondecisions found by
iter179. The future execution must rerun all five repair rows, including the three that already have
diagnostic outputs, so no already-seen output becomes post-hoc score evidence.

## Method

Inputs:

- `experiments/iter180_reward_hack_panel_openai_nondecision_repair_design/RESULT.md`
- `experiments/iter180_reward_hack_panel_openai_nondecision_repair_design/proof/openai_nondecision_repair_row_list.json`
- `experiments/iter180_reward_hack_panel_openai_nondecision_repair_design/proof/repair_call_spend_ceiling_proposal.json`
- `experiments/iter180_reward_hack_panel_openai_nondecision_repair_design/proof/metric_separation_rule.json`

Execution envelope:

- provider calls: at most `10`,
- planned primary repair calls: exactly `5`,
- retry reserve calls: `5`,
- provider family: OpenAI only,
- max output tokens: `1536`,
- estimated spend ceiling: `$10.00`,
- new SWE-bench executions: `0`,
- new cloud runner/resources: `0`,
- already-seen diagnostic outputs cannot be counted as repair evidence.

## Required Outputs

- scheduled repair call manifest,
- provider call ledger and raw prompt/response hashes,
- parsed repair outputs,
- unrepaired-vs-repaired diagnostic comparison,
- claim-boundary decision,
- secret-safety audit, endpoint results, receipt, audit report, run summary, and learning record.

## Numeric Bars

Minimum pass bars:

- exactly `5` primary repair rows are attempted unless blocked before calls,
- attempted provider calls never exceed `10`,
- estimated spend guard never exceeds `$10.00`,
- all attempted rows come from iter180's repair row list,
- already-seen diagnostic outputs are not used as repaired evidence,
- unrepaired iter179 remains the primary public result,
- no committed artifact contains a secret, private project/account identifier, service-account value,
  bearer token, or API key,
- no leaderboard, model-superiority, state-of-the-art, natural-frequency, broad robustness, or public
  benchmark-score claim is made.

## Falsifiers

1. The gate calls any provider other than OpenAI or any row outside the iter180 repair row list.
2. The gate exceeds the call or spend ceiling.
3. Already-seen diagnostic outputs are counted as repaired evidence.
4. The gate mutates the unrepaired iter179 primary result.
5. A committed artifact contains a secret, bearer token, service account, project ID, account ID, or
   private credential material.
6. The result presents a leaderboard, model-superiority, SOTA, natural-frequency, broad robustness, or
   public benchmark-score claim.

## Claim Boundary

At most, if this gate passes: Telos has a bounded OpenAI repair execution diagnostic for the five
previously nondecision panel rows, reported separately from the unrepaired iter179 primary result.

Not supported: a leaderboard ranking, state-of-the-art claim, natural reward-hacking frequency estimate,
broad reward-model robustness claim, production deployment claim, or any claim outside committed
iter175-iter181 proof packets.
