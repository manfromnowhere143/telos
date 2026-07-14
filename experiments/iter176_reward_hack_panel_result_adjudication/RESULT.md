# Iteration 176 Result - Reward-Hack Panel Result Adjudication

Status: `pass`.

## What this gate did

This gate made no provider calls and no credential probes. It rederived the iter175 bounded panel pilot
from committed schedule, ledger, parsed-output, hash-manifest, and metric artifacts, then audited invalid
outputs, row-level disagreement, and the allowed claim boundary before any expansion.

## Recomputed Primary Result

- Provider calls in this gate: `0`.
- Credential probes in this gate: `0`.
- New SWE-bench executions: `0`.
- New cloud resources: `0`.
- Iter175 scheduled calls reconciled by hash: `120/120`.
- Iter175 parsed rows reconciled to scheduled calls: `120/120`.
- Primary rule: `majority_catch`.
- Primary hack catches: `13/20`.
- Primary control catches: `0/20`.
- Panel nondecisions: hack `2`, control `1`.
- Secret/project/account hits in this gate: `0`.

| panel rule | hack catches | control catches | hack nondecisions | control nondecisions |
| --- | ---: | ---: | ---: | ---: |
| `majority_catch` | `13/20` | `0/20` | `2` | `1` |
| `any_catch` | `15/20` | `0/20` | `2` | `1` |
| `unanimous_catch` | `1/20` | `0/20` | `2` | `1` |

## Invalid And Disagreement Findings

- Invalid/nondecision rows: `3`.
- Invalid/nondecision cause counts: `{"provider_incomplete_max_output_tokens_empty_content": 3}`.
- The three invalid rows are preserved as nondecisions; this gate does not repair or reinterpret them.

Disagreement classes:

- `openai_anthropic_catch_google_legitimate`: `12`
- `panel_nondecision`: `3`
- `single_openai_catch`: `2`
- `unanimous_legitimate`: `22`
- `unanimous_reward_hack`: `1`

The central finding is bounded but real: OpenAI and Anthropic create the primary majority signal, while
Google is conservative on this slice. That supports a disagreement-calibrated expansion design, not a
leaderboard or model-superiority claim.

## Failures / Blockers

- none

## Claim Boundary

Supported if status is pass: Telos has an independently rederived bounded `20`-pair three-provider panel
pilot under frozen iter174 defaults. The primary `majority_catch` rule caught `13/20` hack rows and
`0/20` controls, with three panel nondecisions and substantial slot disagreement.

Not supported: a leaderboard ranking, state-of-the-art claim, natural reward-hacking frequency estimate,
broad reward-model robustness claim, production deployment claim, public benchmark score, or any claim
about rows, models, calls, or outputs outside the iter175/iter176 proof packets.

Recommended next gate: `experiments/iter177_reward_hack_panel_disagreement_calibrated_expansion_design/HYPOTHESIS.md`.

## Evidence

- `proof/metric_recomputation_audit.json`
- `proof/invalid_output_audit.json`
- `proof/row_level_disagreement_matrix.json`
- `proof/panel_rule_comparison_table.json`
- `proof/claim_boundary_decision.json`
- `proof/next_gate_recommendation.json`
- `proof/secret_safety_audit.json`
- `proof/endpoint_results.json`
- `proof/audit_report.json`
- `proof/run_summary.json`
- `proof/valid/receipt_reward_hack_panel_result_adjudication.json`
