# Iteration 171 - Reward-Hack Panel Model Binding Freeze

Status: pre-registered zero-spend exact model/API binding freeze; no provider calls, model evaluations,
SWE-bench executions, cloud resources, benchmark scores, leaderboard claims, model-comparison claims,
state-of-the-art claims, natural-frequency claims, or broad robustness claims have been run for this gate.

## Why this gate exists

`iter170` locally preflighted the iter169 panel's strict parser, schema hashes, request-shape templates,
leakage checks, and nondecision accounting. It passed, but paid panel execution remains blocked because the
exact model IDs, credential sources, endpoints/locations, structured-output modes, and primary aggregation
rule are not yet frozen.

The next step is therefore still zero-spend. This gate must turn the provider-family request templates into
an execution-ready binding manifest without making any provider call. A later paid gate may run only if this
binding manifest passes and preserves the iter169/iter170 claim boundaries.

## Method

Inputs:

- `experiments/iter170_reward_hack_panel_structured_output_preflight/RESULT.md`
- `experiments/iter170_reward_hack_panel_structured_output_preflight/proof/request_shape_plan.json`
- `experiments/iter170_reward_hack_panel_structured_output_preflight/proof/source_alignment.json`
- `experiments/iter170_reward_hack_panel_structured_output_preflight/proof/readiness_recommendation.json`
- `experiments/iter169_reward_hack_independent_judge_panel_design/proof/aggregation_rules.json`
- `experiments/iter169_reward_hack_independent_judge_panel_design/proof/budget_and_gate_recommendation.json`
- current repository-local provider configuration surfaces, if any are committed and secret-safe.

Execution envelope:

- provider calls: `0`,
- model evaluations: `0`,
- new SWE-bench executions: `0`,
- new cloud runner/resources: `0`,
- do not read or print secrets,
- do not test live credentials,
- do not choose a model by seeing outputs,
- do not score any model or panel,
- keep all claim language below completed iter167-iter170 evidence.

## Required Outputs

- binding manifest for each panel slot with exact model-id policy, endpoint/location policy, credential-source
  policy, structured-output mode, and block reason if not executable,
- primary aggregation rule selection before outputs, plus all secondary rules that must still be reported,
- paid pilot command/ledger plan with call ceiling, spend ceiling, retry policy, and stop conditions,
- secret-safety audit showing no committed binding artifact contains tokens, project IDs, service accounts,
  bearer strings, or credential material,
- readiness decision: `ready_for_bounded_paid_pilot` or `blocked_with_reasons`,
- valid receipt, audit report, run summary, and learning record.

## Numeric Bars

Minimum pass bars:

- zero provider calls, model evaluations, SWE-bench executions, and cloud resources,
- every slot has a binding status of `ready`, `blocked`, or `requires_operator_input`,
- no exact binding artifact contains secrets or private project/account identifiers,
- the primary aggregation rule is frozen before any paid outputs,
- future paid pilot remains capped at `160` provider calls and `$50.00`,
- nondecision accounting from iter170 is preserved,
- no leaderboard, model-superiority, state-of-the-art, natural-frequency, or broad robustness claim is made.

## Falsifiers

1. The gate performs any provider call, credential probe, or model evaluation.
2. The gate prints or commits secrets, bearer strings, project IDs, service accounts, or private account data.
3. A slot is marked ready without exact model, endpoint/location, credential-source, and structured-output mode.
4. The primary aggregation rule is left for post-output selection.
5. The result authorizes a paid pilot above `160` calls or `$50.00`.
6. The result presents a model, panel, benchmark, leaderboard, SOTA, or broad robustness score.

## Claim Boundary

At most, if this gate passes: Telos has a zero-spend exact binding manifest or a blocked binding decision
for the iter169/iter170 independent judge-panel path.

Not supported: any model score, panel score, changed iter167/iter168 metric, leaderboard ranking, model
superiority, state-of-the-art claim, natural reward-hacking frequency estimate, broad reward-model
robustness claim, or claim about provider bindings not yet run on the paired packets.
