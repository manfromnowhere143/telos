# Report

No model or benchmark result is claimed yet.

This file is an interim technical-report ledger. It records the current evidence line without
turning provider smoke completions, local semantic controls, or failed gates into a benchmark
result.

Current evidence:

- `PREREGISTRATION.md` freezes the target-selection gate.
- `experiments/iter00_target_survey/RESULT.md` selects the first target family.
- `experiments/iter01_receipt_dry_run/RESULT.md` validates the receipt dry run.
- `experiments/iter02_public_task_slice/RESULT.md` selects the public task slice.
- `experiments/iter03_codeclash_smoke/RESULT.md` validates the CodeClash no-LLM smoke receipt.
- `experiments/iter04_agent_behavior_slice/RESULT.md` selects the deterministic agent-behavior
  slice.
- `experiments/iter05_agent_behavior_smoke/RESULT.md` validates deterministic Mini-SWE-Agent
  trajectory and stats capture.
- `experiments/iter06_deterministic_edit_slice/RESULT.md` selects the deterministic edit slice.
- `experiments/iter07_deterministic_edit_smoke/RESULT.md` validates deterministic non-empty diff
  capture through the CodeClash Mini-SWE-Agent path.
- `experiments/iter08_provider_model_pilot_slice/RESULT.md` selects the first paid-provider pilot
  without making a model-result claim.
- `experiments/iter09_provider_model_pilot_smoke/RESULT.md` blocks before spend because ADC
  reauthentication is interactive.
- `experiments/iter10_provider_auth_recovery/RESULT.md` restores non-interactive local ADC
  readiness without making a model call.
- `experiments/iter11_provider_model_pilot_retry/RESULT.md` blocks on Vertex
  `aiplatform.endpoints.predict` permission for the selected model path after cloud-runner setup,
  Docker, and CodeClash reach the provider call path.
- `experiments/iter12_vertex_model_access_recovery/RESULT.md` restores the selected Vertex model
  access path with a minimal probe.
- `experiments/iter13_provider_model_pilot_retry_after_access_recovery/RESULT.md` completes the
  provider smoke but records helper-residue quality evidence.
- `experiments/iter14_provider_diff_quality_review/RESULT.md` reviews the provider diff quality
  without additional provider spend.
- `experiments/iter15_provider_strict_diff_rerun/RESULT.md` fails the strict diff-quality bar due
  to committed helper files.
- `experiments/iter16_provider_workspace_hygiene_control/RESULT.md` passes the helper-residue bar
  with a style caveat.
- `experiments/iter17_provider_lint_hygiene_control/RESULT.md` passes the clean workspace-and-lint
  bar.
- `experiments/iter18_provider_behavior_depth_control/RESULT.md` passes with a process caveat.
- `experiments/iter19_provider_final_inspection_control/RESULT.md` passes the final-inspection bar.
- `experiments/iter20_behavior_semantic_verification/RESULT.md` validates boundary and
  self-collision safety cases locally.
- `experiments/iter21_opponent_collision_control/RESULT.md` validates opponent-body collision cases
  and records the tail-exclusion caveat.
- `experiments/iter22_semantic_mutation_guard/RESULT.md` proves the semantic verifier detects
  targeted boundary, self-collision, and opponent-collision mutants.
- `experiments/iter23_tail_semantics_falsification/RESULT.md` fails under the explicit
  `tail_remains_occupied` assumption because occupied tail moves remain in the safe-move list.
- `experiments/iter24_tail_safety_control/RESULT.md` passes for a clearly labeled changed candidate
  while preserving the original `iter21` tail failure.
- `experiments/iter25_tail_safety_mutation_guard/RESULT.md` fails the full mutation-guard bar
  because a direct own-tail mutant leaves a redundant self-snake fallback path intact.
- `experiments/iter26_own_tail_redundancy_mutation_guard/RESULT.md` passes the compound own-tail
  mutation guard that removes both protection paths.
- `experiments/iter27_semantic_claim_boundary_matrix/RESULT.md` passes a machine-readable
  claim-boundary matrix that keeps original logic, changed candidates, nulls, and verifier-strength
  evidence separate.
- `experiments/iter28_public_claim_surface_guard/RESULT.md` passes a public documentation guard
  against that matrix.
- `experiments/iter29_public_claim_surface_negative_guard/RESULT.md` passes negative fixtures that
  fail the public-claim guard for expected reasons.
- `experiments/iter30_boundary_matrix_schema_guard/RESULT.md` passes a schema/validator guard for
  the claim-boundary matrix and malformed matrix fixtures.
- `experiments/iter31_claim_boundary_release_manifest/RESULT.md` passes a reviewer-facing
  release-manifest gate for the claim-boundary proof packet.
- `experiments/iter32_claim_boundary_release_manifest_negative_guard/RESULT.md` passes a
  negative-fixture guard for the release-manifest audit.
- `experiments/iter33_release_manifest_public_sync_guard/RESULT.md` passes a public-sync guard for
  release-manifest references and claim boundaries.
- `experiments/iter34_release_manifest_public_sync_negative_guard/RESULT.md` passes a
  negative-fixture guard for the release-manifest public-sync checks.
- `experiments/iter35_release_manifest_self_coverage_guard/RESULT.md` passes a self-coverage guard
  for the release-manifest reviewer packet's own `iter31` through `iter34` proof gates.
- `experiments/iter36_release_manifest_self_coverage_negative_guard/RESULT.md` passes a
  negative-fixture guard for the self-coverage report.
- `experiments/iter37_release_manifest_self_coverage_public_sync_guard/RESULT.md` passes a
  public-sync guard for self-coverage prose.
- `experiments/iter38_release_manifest_self_coverage_public_sync_negative_guard/RESULT.md` passes
  a negative-fixture guard for self-coverage public prose.
- `experiments/iter39_public_task_protocol_effect_slice/RESULT.md` passes a public-task
  protocol-effect slice-selection gate for comparing baseline and Telos-enforced completion
  evidence.
- `experiments/iter40_public_task_protocol_effect_execution/HYPOTHESIS.md` freezes the execution
  gate with provider, cost, artifact, and claim-boundary controls.
- `protocol/proof.schema.json` defines the initial receipt contract.
- `tests/` verifies the receipt validator and repository contract.

Current claim-boundary reviewer entry point:
[`../experiments/iter31_claim_boundary_release_manifest/proof/claim_boundary_release_manifest.json`](../experiments/iter31_claim_boundary_release_manifest/proof/claim_boundary_release_manifest.json).
The manifest keeps failed/null gates, the changed candidate, original-provider rows, and no-claim
exclusions in one hash-checked packet.

Current self-coverage reviewer entry points:
[`../experiments/iter35_release_manifest_self_coverage_guard/proof/self_coverage_report.json`](../experiments/iter35_release_manifest_self_coverage_guard/proof/self_coverage_report.json)
and
[`../experiments/iter36_release_manifest_self_coverage_negative_guard/proof/negative_guard_report.json`](../experiments/iter36_release_manifest_self_coverage_negative_guard/proof/negative_guard_report.json).
They account for the release manifest's own proof gates and malformed self-coverage fixtures
without changing the claim boundary.

## Reporting Rule

When results exist, this report must lead with:

1. the exact benchmark target,
2. the baseline,
3. the primary metric,
4. the outcome with confidence intervals or exact counts,
5. the nulls and failed gates,
6. the limitations.

No result paragraph may outrun committed proof artifacts.
