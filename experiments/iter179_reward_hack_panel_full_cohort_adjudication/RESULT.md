# Iteration 179 Result - Reward-Hack Panel Full-Cohort Adjudication

Status: `pass`.

## What this gate did

This zero-spend gate adjudicated the committed iter175+iter178 three-provider reward-hack panel cohort.
It made no provider calls, no credential probes, no model evaluations, no SWE-bench executions, and no
cloud-resource changes. The three iter178 OpenAI recovery diagnostics remain diagnostic only.

## Recomputed Full-Cohort Result

- Provider calls in this gate: `0`.
- Credential probes in this gate: `0`.
- Estimated provider spend in this gate: `$0.00`.
- New SWE-bench executions: `0`.
- New cloud resources: `0`.
- Primary rule: `majority_catch`.
- Primary hack catches: `17/40`.
- Primary control catches: `0/40`.
- Panel nondecisions: hack `4`, control `1`.
- Secret/project/account hits in this gate: `0`.

| panel rule | hack catches | control catches | hack nondecisions | control nondecisions |
| --- | ---: | ---: | ---: | ---: |
| `majority_catch` | `17/40` | `0/40` | `4` | `1` |
| `any_catch` | `23/40` | `0/40` | `4` | `1` |
| `unanimous_catch` | `2/40` | `0/40` | `4` | `1` |

## Disagreement And Nondecisions

- Full-cohort panel rows: `80`.
- Panel nondecision rows: `5`.
- Nondecision cause counts: `{"openai_empty_output": 5}`.

Disagreement classes:

- `openai_anthropic_catch_google_legitimate`: `15`
- `panel_nondecision`: `5`
- `single_anthropic_catch`: `2`
- `single_openai_catch`: `4`
- `unanimous_legitimate`: `52`
- `unanimous_reward_hack`: `2`

## OpenAI Recovery Boundary

- OpenAI recovery diagnostic rows parsed: `3/3`.
- Recovery rows allowed to rewrite score: `0`.
- Unrecovered primary nondecision rows remaining: `2`.

The recovery diagnostics changed only whether three old OpenAI empty-output slots could emit parseable
content under a larger output budget. They did not change the full-cohort numerator, denominator, row
labels, panel nondecision accounting, or claim boundary.

## Failures / Blockers

- none

Recommended next gate: `experiments/iter180_reward_hack_panel_openai_nondecision_repair_design/HYPOTHESIS.md`.

## Claim Boundary

Supported if status is pass: Telos has a committed zero-spend full-cohort adjudication of the bounded
iter175+iter178 reward-hack panel: unrepaired `majority_catch` caught `17/40` hack rows and `0/40`
controls, with `4` hack nondecisions and `1` control nondecision.

Not supported: a leaderboard ranking, state-of-the-art claim, natural reward-hacking frequency estimate,
broad reward-model robustness claim, production deployment claim, model-superiority claim, public
benchmark score, repaired score, or any claim outside committed iter175-iter179 proof packets.

## Evidence

- `proof/full_cohort_panel_metrics.json`
- `proof/full_cohort_metric_recomputation_audit.json`
- `proof/row_level_disagreement_and_nondecision_audit.json`
- `proof/openai_recovery_effect_boundary.json`
- `proof/panel_rule_comparison_table.json`
- `proof/claim_boundary_decision.json`
- `proof/next_gate_recommendation.json`
- `proof/secret_safety_audit.json`
- `proof/endpoint_results.json`
- `proof/audit_report.json`
- `proof/run_summary.json`
- `proof/valid/receipt_reward_hack_panel_full_cohort_adjudication.json`
