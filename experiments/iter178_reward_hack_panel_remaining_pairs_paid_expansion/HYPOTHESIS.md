# Iteration 178 - Reward-Hack Panel Remaining-Pairs Paid Expansion

Status: pre-registered paid execution gate; no provider calls, credential probes, model evaluations,
SWE-bench executions, cloud resources, benchmark scores, leaderboard claims, model-comparison claims,
state-of-the-art claims, natural-frequency claims, or broad robustness claims have been run for this gate.

## Why this gate exists

`iter175` ran the first bounded `20`-pair panel pilot and `iter176` adjudicated it. `iter177` froze the
next expansion design: complete the remaining `20` paired rows from `reward_hack_benchmark_v1` and
separately test whether a larger OpenAI output budget recovers the three iter175 empty-content rows.

## Method

Inputs:

- `experiments/iter177_reward_hack_panel_disagreement_calibrated_expansion_design/RESULT.md`
- `experiments/iter177_reward_hack_panel_disagreement_calibrated_expansion_design/proof/expansion_row_selection_design.json`
- `experiments/iter177_reward_hack_panel_disagreement_calibrated_expansion_design/proof/openai_output_budget_recovery_design.json`
- `experiments/iter177_reward_hack_panel_disagreement_calibrated_expansion_design/proof/call_spend_ceiling_proposal.json`
- `experiments/iter174_reward_hack_panel_default_choice_freeze/proof/default_choice_packet.json`
- `experiments/iter171_reward_hack_panel_model_binding_freeze/proof/primary_aggregation_rule.json`

Execution envelope:

- planned fresh remaining-pair panel calls: `120`,
- planned diagnostic OpenAI recovery calls: `3`,
- total planned provider calls before retries: `123`,
- total provider-call ceiling including retry reserve: `160`,
- retry reserve: `37`,
- spend ceiling: `$50.00`,
- new SWE-bench executions: `0`,
- new cloud runner/resources: `0`,
- primary rule: `majority_catch`,
- OpenAI recovered max output tokens: `1536`,
- runtime credentials may be loaded only from environment or external secret stores; secret values,
  project IDs, account IDs, bearer tokens, and service-account values must never be written.

## Required Outputs

- scheduled call manifest,
- raw prompt and raw response artifacts,
- provider call ledger,
- parsed judge outputs,
- per-slot metrics,
- panel metrics for the fresh remaining-pair cohort,
- combined unrepaired iter175+iter178 diagnostic table,
- OpenAI recovery diagnostic table,
- cost/call audit,
- secret-safety audit, endpoint results, receipt, audit report, run summary, and learning record.

## Numeric Bars

Minimum pass bars:

- attempted provider calls are `<= 160`,
- estimated spend is `<= $50.00`,
- all fresh remaining-pair calls use the frozen iter174 provider defaults,
- OpenAI calls use the iter177 recovered output-budget shape,
- every attempted output is parsed by `telos/reward_hack_judge_parser.py` before aggregation,
- invalid, refusal, empty, and inconclusive outputs remain nondecisions,
- the three recovery calls are reported diagnostically and do not rewrite iter175 primary metrics,
- total new SWE-bench executions and new cloud resources are `0`,
- no committed artifact contains a secret, private project/account identifier, service-account value,
  bearer token, or API key,
- no leaderboard, model-superiority, state-of-the-art, natural-frequency, broad robustness, or public
  benchmark-score claim is made.

## Falsifiers

1. The gate attempts more than `160` provider calls or exceeds `$50.00` estimated spend.
2. Any provider binding differs from the iter174 frozen defaults.
3. OpenAI recovery calls use a request shape different from iter177's frozen design.
4. A parser, row, provider, model, aggregation rule, or metric denominator is changed after outputs.
5. Invalid, refusal, empty, or inconclusive outputs are counted as catches or legitimate decisions.
6. The recovery cohort is used to rewrite the published iter175 primary result.
7. A committed artifact contains a secret, bearer token, service account, project ID, account ID, or
   private credential material.
8. The result presents a leaderboard, model-superiority, SOTA, natural-frequency, broad robustness, or
   public benchmark-score claim.

## Claim Boundary

At most, if this gate passes: Telos has a bounded paid panel expansion over the previously unobserved
`20` paired rows, plus a separately reported OpenAI output-budget recovery diagnostic.

Not supported: a leaderboard ranking, state-of-the-art claim, natural reward-hacking frequency estimate,
broad reward-model robustness claim, production deployment claim, or any claim about rows, models, calls,
or outputs outside the committed iter175-iter178 proof packets.
