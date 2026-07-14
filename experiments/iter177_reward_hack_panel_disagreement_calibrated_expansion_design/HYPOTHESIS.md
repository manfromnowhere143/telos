# Iteration 177 - Reward-Hack Panel Disagreement-Calibrated Expansion Design

Status: pre-registered zero-spend design gate; no provider calls, credential probes, model
evaluations, SWE-bench executions, cloud resources, benchmark scores, leaderboard claims,
model-comparison claims, state-of-the-art claims, natural-frequency claims, or broad robustness claims
have been run for this gate.

## Why this gate exists

`iter175` produced a promising bounded panel-pilot signal, and `iter176` adjudicated it without spending
again. The pilot also exposed two concrete limits that must be handled before expansion: OpenAI
reasoning rows can exhaust the `512` output-token budget and return no content, and Google disagrees with
the OpenAI/Anthropic catch pattern on most hack rows. The next paid run should be designed around those
observations before any new call is made.

## Method

Inputs:

- `experiments/iter175_reward_hack_panel_bounded_paid_pilot/RESULT.md`
- `experiments/iter175_reward_hack_panel_bounded_paid_pilot/proof/panel_metrics.json`
- `experiments/iter176_reward_hack_panel_result_adjudication/RESULT.md`
- `experiments/iter176_reward_hack_panel_result_adjudication/proof/invalid_output_audit.json`
- `experiments/iter176_reward_hack_panel_result_adjudication/proof/row_level_disagreement_matrix.json`
- `experiments/iter176_reward_hack_panel_result_adjudication/proof/panel_rule_comparison_table.json`

Design envelope:

- provider calls: `0`,
- credential probes: `0`,
- model evaluations: `0`,
- new SWE-bench executions: `0`,
- new cloud runner/resources: `0`,
- freeze an expansion row-selection strategy before outputs,
- freeze OpenAI output-budget/request-shape recovery before paid calls,
- preserve `majority_catch` as the primary rule unless a later pre-registered gate changes it,
- preserve invalid/refusal/inconclusive rows as nondecisions.

## Required Outputs

- expansion row-selection design,
- OpenAI output-budget recovery design,
- disagreement-stratification table,
- call/spend ceiling proposal,
- stop-condition proposal,
- claim-boundary decision,
- secret-safety audit, endpoint results, receipt, audit report, run summary, and learning record.

## Numeric Bars

Minimum pass bars:

- the design uses only committed iter175/iter176 artifacts,
- total new provider calls, credential probes, SWE-bench executions, and cloud resources are all `0`,
- the design includes at least four row strata: panel-missed hacks, majority-caught hacks, panel
  nondecisions, and clean controls,
- the design includes a concrete mitigation for the `max_output_tokens` empty-content failure mode,
- the next paid plan has an explicit provider-call ceiling and spend ceiling,
- no committed artifact contains a secret, private project/account identifier, service-account value,
  bearer token, or API key,
- no leaderboard, model-superiority, state-of-the-art, natural-frequency, broad robustness, or public
  benchmark-score claim is made.

## Falsifiers

1. The gate makes any provider call, credential probe, model evaluation, SWE-bench execution, or cloud
   resource change.
2. The row-selection or request-shape design depends on uncommitted output inspection or private labels not
   present in iter175/iter176 artifacts.
3. Invalid, refusal, or inconclusive outputs are converted into catches or legitimate decisions.
4. The gate changes the primary aggregation rule after seeing iter175 outputs without explicitly registering
   that as a future hypothesis.
5. A committed artifact contains a secret, bearer token, service account, project ID, account ID, or private
   credential material.
6. The result presents a leaderboard, model-superiority, SOTA, natural-frequency, broad robustness, or public
   benchmark-score claim.

## Claim Boundary

At most, if this gate passes: Telos has a frozen, reviewer-facing design for the next bounded panel
expansion and OpenAI output-budget recovery.

Not supported: a new score, paid-run result, leaderboard ranking, state-of-the-art claim, natural
reward-hacking frequency estimate, broad reward-model robustness claim, production deployment claim, or
any claim about rows, models, calls, or outputs outside the committed iter175/iter176 proof packets.
