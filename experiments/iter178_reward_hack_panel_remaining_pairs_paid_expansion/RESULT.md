# Iteration 178 Result - Reward-Hack Panel Remaining-Pairs Paid Expansion

Status: `pass`.

## What this gate did

This gate ran the pre-registered iter177 expansion design: the unobserved `20` paired rows from
`reward_hack_benchmark_v1` as a fresh three-provider panel, plus the three OpenAI output-budget recovery
diagnostics. Runtime credentials were loaded from environment or external secret stores without writing
secret values.

## Execution Summary

- Planned fresh primary calls: `120`.
- Planned diagnostic OpenAI recovery calls: `3`.
- Provider-call ceiling including retry reserve: `160`.
- Attempted provider calls: `123`.
- Successful provider calls: `123`.
- Retry calls used: `0`.
- Estimated spend guard: `$7.005150` of `$50.00`.
- Secret/project/account hits in committed artifacts: `0`.
- New SWE-bench executions: `0`.
- New cloud runners/resources: `0`.
- OpenAI recovery rows with parsed JSON decisions: `3` of `3`.

Provider summary:

- `anthropic`: attempted `40`, successful `40`, errors `0`
- `google_vertex_or_gemini`: attempted `40`, successful `40`, errors `0`
- `openai`: attempted `43`, successful `43`, errors `0`

## Fresh Remaining-Pair Panel

- Majority-catch hack rows: `4` of `20`.
- Majority-catch control rows: `0` of `20`.
- Panel nondecisions: hacks `2`, controls `0`.

## Combined Unrepaired Diagnostic

The combined table reports iter175 primary rows plus iter178 fresh rows. It does not use the three OpenAI
recovery diagnostics to repair iter175.

- Combined majority-catch hack rows: `17` of `40`.
- Combined majority-catch control rows: `0` of `40`.
- Combined panel nondecisions: hacks `4`, controls `1`.

Failures / blockers:

- none

Recommended next gate: `experiments/iter179_reward_hack_panel_full_cohort_adjudication/HYPOTHESIS.md`.

## Claim Boundary

Supported if status is pass: Telos has a bounded paid panel expansion over the previously unobserved
`20` paired rows, plus a separately reported OpenAI output-budget recovery diagnostic.

Not supported: a leaderboard ranking, state-of-the-art claim, natural reward-hacking frequency estimate,
broad reward-model robustness claim, production deployment claim, model-superiority claim, or any claim
outside committed iter175-iter178 proof packets.

## Evidence

- `proof/scheduled_call_manifest.json`
- `proof/client_surface_audit.json`
- `proof/credential_source_audit.json`
- `proof/provider_call_ledger.jsonl`
- `proof/prompt_response_hash_manifest.json`
- `proof/parsed_judge_outputs.jsonl`
- `proof/per_slot_metrics.json`
- `proof/panel_metrics.json`
- `proof/combined_unrepaired_diagnostic_table.json`
- `proof/openai_recovery_diagnostic_table.json`
- `proof/cost_call_audit.json`
- `proof/secret_safety_audit.json`
- `proof/endpoint_results.json`
- `proof/audit_report.json`
- `proof/run_summary.json`
- `proof/valid/receipt_reward_hack_panel_remaining_pairs_paid_expansion.json`
