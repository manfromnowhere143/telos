# Iteration 175 Result - Reward-Hack Panel Bounded Paid Pilot

Status: `pass`.

## What this gate did

This gate attempted the frozen iter174 three-slot panel under the iter171 bounded pilot plan. Runtime
credentials were loaded from the process environment or GCP Secret Manager without writing secret values.
The first frozen scheduled packet for each slot was used as an access sentinel and counted as a primary
provider call.

## Execution Summary

- Planned primary calls: `120`.
- Provider-call ceiling including retry reserve: `160`.
- Attempted provider calls: `120`.
- Successful provider calls: `120`.
- Retry calls used: `0`.
- Estimated spend guard: `$6.312690` of `$50.00`.
- Secret/project/account hits in committed artifacts: `0`.
- New SWE-bench executions: `0`.
- New cloud runners/resources: `0`.

Provider summary:

- `anthropic`: attempted `40`, successful `40`, errors `0`
- `google_vertex_or_gemini`: attempted `40`, successful `40`, errors `0`
- `openai`: attempted `40`, successful `40`, errors `0`

Failures / blockers:

- none

Recommended next gate: adjudicate the panel error/miss pattern and decide whether a larger blinded panel run is justified.

## Claim Boundary

Supported if status is pass: Telos has a bounded paired panel-pilot result under the iter174 frozen
defaults and iter171 call/spend ceilings.

If status is blocked: Telos has only a secret-safe partial/access result for the frozen panel. No panel
score, leaderboard ranking, model superiority, state-of-the-art claim, natural reward-hacking frequency
estimate, broad robustness claim, or production-readiness claim is supported.

## Evidence

- `proof/scheduled_call_manifest.json`
- `proof/client_surface_audit.json`
- `proof/credential_source_audit.json`
- `proof/provider_call_ledger.jsonl`
- `proof/prompt_response_hash_manifest.json`
- `proof/parsed_judge_outputs.jsonl`
- `proof/per_slot_metrics.json`
- `proof/panel_metrics.json`
- `proof/cost_call_audit.json`
- `proof/secret_safety_audit.json`
- `proof/endpoint_results.json`
- `proof/audit_report.json`
- `proof/run_summary.json`
- `proof/valid/receipt_reward_hack_panel_bounded_paid_pilot.json`
