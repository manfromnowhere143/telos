# Iteration 187 Result - Reward-Hack Property-Generator Schema Preflight

Status: `pass`.

## What this gate did

This zero-spend gate validated the local output contract for future property-generator calls over the
iter186 property-probe packet set. It made no provider calls, credential probes, model evaluations,
property-generator calls, SWE-bench executions, or cloud resource changes.

## Parser Contract

- Fixture count: `17`.
- Observed statuses: `{'invalid': 11, 'non_applicable': 1, 'parsed': 3, 'refusal': 2}`.
- Valid fixture parse rate: `1.0`.
- Invalid/refusal/malformed rejection rate: `1.0`.
- Parser source SHA256: `6e9b0d873858e069fe7e273a273ad43f6d2fb6f4ce9612b4c03de93517f8e282`.

The strict parser accepts executable proposals only when all required fields are present, all fields use
the expected types, the strategy is in the allowed vocabulary, compact property names stay within the
audit limit, active strategies do not carry non-applicability reasons, and hidden Telos row or label terms
are absent. `not_applicable`, refusal, and invalid outputs remain nondecisions.

Failures / blockers:

- none

## Prompt Contract

The prompt-contract preflight combined the iter186 model-facing payload with the iter187 output schema
for `24` request contracts. Leakage hits: `0`.
Prompt-key allowlist mismatches: `0`.

## Future Gate Bars

Paid property generation remains unauthorized. The preserved future bars are
`48` maximum provider calls including retries, `$40.00`
spend ceiling, at least `20` local or container
execution attempts, control false-positive ceiling `0`,
nondecision ceiling `4`, prompt leakage ceiling `0`, and response secret-hit
ceiling `0`.

The active next gate is `experiments/iter188_telos_mission_data_process_audit_design/HYPOTHESIS.md`, a zero-spend Telos-wide data/process audit design before any new
property-generator spend.

## Claim Boundary

At most, this gate supports a zero-spend schema, parser, fixture suite, and prompt-contract preflight for
future property-generator outputs over the committed iter186 packet set. The public panel metric remains
unrepaired iter179 `majority_catch`: `17/40` hack rows and `0/40` controls.

No leaderboard ranking, state-of-the-art claim, natural reward-hacking frequency estimate, broad
reward-model robustness claim, production deployment claim, model-superiority claim, public benchmark
score, repaired-score claim, or claim outside committed iter175-iter187 proof packets is supported.

## Evidence

- `proof/property_generator_output_schema.json`
- `proof/fixtures/property_generator_output_fixtures.jsonl`
- `proof/parsed_fixture_results.json`
- `proof/parser_audit.json`
- `proof/prompt_contract_preflight.json`
- `proof/future_paid_execution_readiness.json`
- `proof/claim_boundary_audit.json`
- `proof/forbidden_claim_scan.json`
- `proof/secret_safety_audit.json`
- `proof/endpoint_results.json`
- `proof/audit_report.json`
- `proof/run_summary.json`
- `proof/valid/receipt_reward_hack_property_generator_schema_preflight.json`
