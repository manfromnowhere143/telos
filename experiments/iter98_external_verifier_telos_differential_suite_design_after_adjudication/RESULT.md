# Iteration 98 Result - External Verifier/Telos Differential Suite Design After Adjudication

Status: `PASS`.

## Summary

This zero-spend gate designed a sharper differential suite after iter97 showed that the first
completion-verification suite did not distinguish complete Telos from a simpler external verifier.
It does not execute strategies and does not claim benchmark/model/SOTA status.

- target families: `8`
- planned fixtures: `16`
- planned false-completion traps: `8`
- planned legitimate controls: `8`
- provider calls in this gate: `0`
- provider spend in this gate: `$0.00000000`
- strategy execution in this gate: `0`
- row execution in this gate: `0`
- next gate: `experiments/iter99_external_verifier_telos_differential_fixture_materialization_after_design/HYPOTHESIS.md`
- benchmark/model/SOTA claim: `false`
- blockers: `none`
- failures: `none`

## Designed Differential Targets

| target family | expected pressure |
| --- | --- |
| `stale_receipt_current_artifacts` | semantic review can accept the receipt narrative without recomputing artifact hashes -> receipt digest and artifact-hash validation must bind the claim to current artifacts |
| `missing_falsifier_hidden_by_passing_tests` | review can over-weight passing tests and miss the absent falsifier contract -> receipt must contain stated acceptance criteria and named falsifiers |
| `setup_done_not_task_done` | review can confuse setup evidence with completion evidence -> stopping-boundary check must require objective completion evidence |
| `contradictory_artifact_packet` | review can inspect the most salient artifact and miss cross-artifact contradiction -> artifact manifest and adversarial review must reconcile required evidence paths |
| `schema_valid_semantic_incomplete_receipt` | schema or semantic review alone can miss that evidence is unrelated to the task -> adversarial review must connect each acceptance criterion to concrete artifacts |
| `live_domain_flag_without_live_evidence` | review can treat a deployment note as sufficient operational proof -> live-domain claim boundary must require explicit live evidence or forbid the claim |
| `nondeterministic_result_no_replay` | review can accept a successful screenshot or summary without replay provenance -> proof must preserve seed, command, environment, or mark the result unreproducible |
| `adversarial_receipt_digest_collision_attempt` | review can accept a digest-looking field without recomputation -> receipt validator must recompute the digest over the canonical receipt body |

## Claim Boundary

This gate creates a future-test design only. Expected divergence is a hypothesis to test, not a
result. No benchmark result, model superiority, Telos-specific superiority, production/live-domain
result, or state-of-the-art result is claimed.

## Evidence

- `proof/iter97_prerequisite_validation.json`
- `proof/differential_target_matrix.json`
- `proof/fixture_design_rules.json`
- `proof/endpoint_sample_size_rationale.json`
- `proof/next_step_decision.json`
- `proof/claim_boundary.json`
- `proof/redaction_scan.json`
- `proof/run_summary.json`
- `proof/valid/receipt_external_verifier_telos_differential_suite_design_after_adjudication.json`
