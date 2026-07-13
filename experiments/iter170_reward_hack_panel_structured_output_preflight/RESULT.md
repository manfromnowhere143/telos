# Iteration 170 Result - Reward-Hack Panel Structured-Output Preflight

Status: `pass`.

## What this gate did

This zero-spend preflight tested the iter169 panel's local output contract before any paid panel call. It
made no provider calls, model evaluations, SWE-bench executions, or cloud-resource changes.

## Parser Fixtures

The local fixture audit covers valid `reward_hack`, `legitimate`, and `inconclusive` JSON plus refusals,
invalid JSON, markdown-fenced JSON, missing fields, extra fields, invalid confidence values, and unknown
verdicts. Markdown-fenced JSON remains invalid under the strict parser.

## Request Shape Status

- `google_continuity_fast_judge`: `requires_operator_binding`
- `openai_reasoning_judge`: `requires_operator_binding`
- `anthropic_reasoning_or_safety_judge`: `requires_operator_binding`

The static request shapes are documented for Google, OpenAI, and Anthropic structured-output surfaces, but
paid execution is blocked until exact model IDs, credential sources, endpoints/locations, structured-output
modes, and the primary aggregation rule are frozen in a later hypothesis.

## Leakage Preflight

Scanned `40` hack packets and `40` control packets.
Forbidden leakage hits: `0`. Prompt-key allowlist mismatches:
`0`.

## Readiness

Future paid run readiness: `blocked_pending_operator_binding`.

Recommended next gate: `iter171_reward_hack_panel_model_binding_freeze` (zero-spend exact model/API binding freeze), with provider-call ceiling
`0` and spend ceiling `$0.00`.

Failures:

- none

## Claim Boundary

Supported if status is pass: Telos has a zero-spend structured-output and request-shape preflight for the
iter169 independent judge-panel design.

Not supported: any model score, panel score, changed iter167/iter168 metric, leaderboard ranking, model
superiority, state-of-the-art claim, natural reward-hacking frequency estimate, broad reward-model
robustness claim, or claim about provider bindings not yet run on the paired packets.

## Evidence

- `proof/parser_fixture_audit.json`
- `proof/schema_hashes.json`
- `proof/request_shape_plan.json`
- `proof/packet_leakage_preflight.json`
- `proof/nondecision_accounting.json`
- `proof/source_alignment.json`
- `proof/readiness_recommendation.json`
- `proof/audit_report.json`
- `proof/endpoint_results.json`
- `proof/run_summary.json`
- `proof/valid/receipt_reward_hack_panel_structured_output_preflight.json`
