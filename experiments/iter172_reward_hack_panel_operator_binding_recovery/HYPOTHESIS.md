# Iteration 172 - Reward-Hack Panel Operator Binding Recovery

Status: pre-registered zero-spend operator binding recovery; no provider calls, credential probes, model
evaluations, SWE-bench executions, cloud resources, benchmark scores, leaderboard claims,
model-comparison claims, state-of-the-art claims, natural-frequency claims, or broad robustness claims have
been run for this gate.

## Why this gate exists

`iter171` froze the panel's primary aggregation rule and bounded-pilot call accounting, but it did not
authorize paid execution because exact operator-owned model/API bindings were not complete. This gate is
the recovery step: collect or block the non-secret binding choices needed before any paid provider call.

## Method

Inputs:

- `experiments/iter171_reward_hack_panel_model_binding_freeze/RESULT.md`
- `experiments/iter171_reward_hack_panel_model_binding_freeze/proof/binding_manifest.json`
- `experiments/iter171_reward_hack_panel_model_binding_freeze/proof/primary_aggregation_rule.json`
- `experiments/iter171_reward_hack_panel_model_binding_freeze/proof/paid_pilot_plan.json`
- `experiments/iter171_reward_hack_panel_model_binding_freeze/proof/readiness_decision.json`
- operator-supplied non-secret model/API binding choices, if supplied.

Execution envelope:

- provider calls: `0`,
- credential probes: `0`,
- model evaluations: `0`,
- new SWE-bench executions: `0`,
- new cloud runner/resources: `0`,
- do not read or print secrets,
- do not test live credentials,
- do not choose a model by seeing outputs,
- do not raise the iter171 call or spend ceilings.

## Required Outputs

- operator-binding packet for each panel slot, or an explicit blocked reason if the operator did not supply
  enough non-secret binding information,
- secret-safety audit showing no committed artifact contains tokens, project IDs, service accounts, bearer
  strings, or credential material,
- readiness decision: `ready_for_bounded_paid_pilot` or `blocked_with_reasons`,
- valid receipt, audit report, run summary, and learning record.

## Numeric Bars

Minimum pass bars:

- zero provider calls, credential probes, model evaluations, SWE-bench executions, and cloud resources,
- every slot has `ready`, `blocked`, or `requires_operator_input` status,
- no exact binding artifact contains secrets or private project/account identifiers,
- the iter171 `majority_catch` primary aggregation rule remains frozen,
- future paid pilot remains capped at `160` provider calls and `$50.00`,
- no leaderboard, model-superiority, state-of-the-art, natural-frequency, or broad robustness claim is made.

## Falsifiers

1. The gate performs any provider call, credential probe, or model evaluation.
2. The gate prints or commits secrets, bearer strings, project IDs, service accounts, or private account data.
3. A slot is marked ready without exact model, endpoint/location, credential-source route, and
   structured-output mode.
4. The primary aggregation rule changes after iter171.
5. The result authorizes a paid pilot above `160` calls or `$50.00`.
6. The result presents a model, panel, benchmark, leaderboard, SOTA, or broad robustness score.

## Claim Boundary

At most, if this gate passes: Telos has a zero-spend operator-binding packet or a blocked binding decision
for the iter169-iter171 independent judge-panel path.

Not supported: any model score, panel score, changed iter167/iter168 metric, leaderboard ranking, model
superiority, state-of-the-art claim, natural reward-hacking frequency estimate, broad reward-model
robustness claim, or claim about provider calls not actually run on the paired packets.
