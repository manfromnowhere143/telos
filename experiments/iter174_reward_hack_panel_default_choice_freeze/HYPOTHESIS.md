# Iteration 174 - Reward-Hack Panel Default Choice Freeze

Status: pre-registered zero-spend default model/API choice freeze; no provider calls, credential probes,
model evaluations, SWE-bench executions, cloud resources, benchmark scores, leaderboard claims,
model-comparison claims, state-of-the-art claims, natural-frequency claims, or broad robustness claims have
been run for this gate.

## Why this gate exists

`iter173` builds a public binding menu. This gate must freeze exact non-secret default choices from that
menu before any paid provider call, or publish a blocked reason if the menu is not ready.

## Method

Inputs:

- `experiments/iter173_reward_hack_panel_public_binding_menu/RESULT.md`
- `experiments/iter173_reward_hack_panel_public_binding_menu/proof/public_binding_menu.json`
- `experiments/iter173_reward_hack_panel_public_binding_menu/proof/operator_choice_template.json`
- `experiments/iter173_reward_hack_panel_public_binding_menu/proof/readiness_decision.json`

Execution envelope:

- provider calls: `0`,
- credential probes: `0`,
- model evaluations: `0`,
- new SWE-bench executions: `0`,
- new cloud runner/resources: `0`,
- do not read or print secrets,
- do not test live credentials,
- do not choose by observing model outputs,
- do not raise the iter171/iter173 call or spend ceilings.

## Required Outputs

- frozen default-choice packet or explicit blocked reason per slot,
- secret-safety audit showing no committed artifact contains tokens, project IDs, service accounts, bearer
  strings, or credential material,
- readiness decision: `ready_for_bounded_paid_pilot_hypothesis` or `blocked_with_reasons`,
- valid receipt, audit report, run summary, and learning record.

## Numeric Bars

Minimum pass bars:

- zero provider calls, credential probes, model evaluations, SWE-bench executions, and cloud resources,
- every frozen choice must come from the iter173 public menu,
- no committed artifact contains secrets or private project/account identifiers,
- the iter171 `majority_catch` primary aggregation rule remains frozen,
- future paid pilot remains capped at `160` provider calls and `$50.00`,
- no leaderboard, model-superiority, state-of-the-art, natural-frequency, or broad robustness claim is made.

## Falsifiers

1. The gate performs any provider call, credential probe, or model evaluation.
2. The gate prints or commits secrets, bearer strings, project IDs, service accounts, or private account data.
3. A frozen choice is not present in the iter173 public menu.
4. The primary aggregation rule changes after iter171.
5. The result authorizes a paid pilot above `160` calls or `$50.00`.
6. The result presents a model, panel, benchmark, leaderboard, SOTA, or broad robustness score.

## Claim Boundary

At most, if this gate passes: Telos has a zero-spend default model/API choice freeze for the
iter169-iter173 independent judge-panel path.

Not supported: any model score, panel score, changed iter167/iter168 metric, leaderboard ranking, model
superiority, state-of-the-art claim, natural reward-hacking frequency estimate, broad reward-model
robustness claim, or claim about provider calls not actually run on the paired packets.
