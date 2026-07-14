# Iteration 175 - Reward-Hack Panel Bounded Paid Pilot

Status: pre-registered bounded paid panel pilot; no provider calls, credential probes, model evaluations,
SWE-bench executions, cloud resources, benchmark scores, leaderboard claims, model-comparison claims,
state-of-the-art claims, natural-frequency claims, or broad robustness claims have been run for this gate.

## Why this gate exists

`iter174` freezes exact default model/API choices from the public iter173 menu. This gate is the first
possible paid pilot under those defaults, but it must stop rather than substitute a model, endpoint, parser,
aggregation rule, row set, or budget after outputs are observed.

## Method

Inputs:

- `experiments/iter174_reward_hack_panel_default_choice_freeze/RESULT.md`
- `experiments/iter174_reward_hack_panel_default_choice_freeze/proof/default_choice_packet.json`
- `experiments/iter171_reward_hack_panel_model_binding_freeze/proof/paid_pilot_plan.json`
- `experiments/iter170_reward_hack_panel_structured_output_preflight/proof/panel_request_templates.json`
- frozen hack/control blinded packets referenced by the iter171 bounded pilot plan.

Execution envelope:

- provider calls: maximum `160` including retry reserve,
- planned primary calls: `120` (`20` paired rows x `2` packet classes x `3` panel slots),
- retry reserve: maximum `40`, only for provider, transport, or rate-limit errors,
- estimated provider spend: stop before or at `$50.00`,
- new SWE-bench executions: `0`,
- new cloud runner/resources: `0`,
- use runtime credentials only; never print or commit secrets, bearer tokens, project IDs, service accounts,
  account IDs, or quota-project names,
- do not substitute any model, endpoint, row, parser, or aggregation rule after seeing outputs.

## Required Outputs

- provider-call ledger with one row per attempted call,
- prompt/response hash manifest for every attempted call,
- strict parser results for every response before aggregation,
- per-slot hack/control metrics with nondecision accounting,
- primary `majority_catch` panel metrics plus required secondary rules,
- secret-safety audit, cost/call audit, endpoint results, receipt, audit report, run summary, and learning
  record,
- blocked/partial result if credentials, access, rate limits, parser failure, secret safety, or budget limits
  prevent completion.

## Numeric Bars

Minimum pass bars:

- all planned `120` primary calls complete or the result publishes a blocked/partial status with raw evidence,
- total attempted provider calls never exceed `160`,
- estimated spend never exceeds `$50.00`,
- no new SWE-bench execution or cloud resource is created,
- every call uses the iter174 frozen default-choice packet,
- no secret, private project/account identifier, service-account value, bearer token, or API key is committed,
- no leaderboard, model-superiority, state-of-the-art, natural-frequency, or broad robustness claim is made.

## Falsifiers

1. The run exceeds `160` provider calls or `$50.00`.
2. A provider binding differs from the iter174 frozen default choices.
3. A model, endpoint, parser, row, or aggregation rule is changed after outputs are observed.
4. A committed artifact contains a secret, bearer token, service account, project ID, account ID, or private
   credential material.
5. Nondecisions are counted as true positives or true negatives.
6. The result presents a leaderboard, model-superiority, SOTA, natural-frequency, broad robustness, or public
   benchmark-score claim.

## Claim Boundary

At most, if this gate passes: Telos has a bounded paired panel-pilot result under the iter174 frozen
defaults and iter171 call/spend ceilings.

Not supported: a leaderboard ranking, state-of-the-art claim, natural reward-hacking frequency estimate,
broad reward-model robustness claim, production deployment claim, or any claim about rows, models, calls, or
outputs not actually executed and committed in the proof packet.
