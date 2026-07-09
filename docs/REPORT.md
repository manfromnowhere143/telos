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
- `experiments/iter40_public_task_protocol_effect_execution/RESULT.md` blocks before provider
  execution because Docker and pinned CodeClash runner readiness were not established.
- `experiments/iter41_public_task_protocol_effect_runner_recovery/RESULT.md` passes runner
  recovery through three isolated GitHub Actions CodeClash runs with zero provider spend.
- `experiments/iter42_public_task_protocol_effect_execution_retry/RESULT.md` blocks before provider
  execution because the provider-capable harness, cost capture, and raw-artifact redaction controls
  were not recovered.
- `experiments/iter43_provider_execution_harness_recovery/RESULT.md` passes a bounded
  provider-execution harness recovery gate with a non-GPU runner lifecycle probe, zero provider
  model calls, zero spend, and zero full task-condition pairs.
- `experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/RESULT.md`
  blocks before provider execution because the recovered harness still disables full task-condition
  execution.
- `experiments/iter45_public_task_condition_executor_assembly/RESULT.md` passes a zero-spend
  executor-assembly dry-run gate with six frozen task-condition pairs and full execution still
  disabled.
- `experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor/RESULT.md`
  blocks before provider execution because provider overlays were not bound into each pair command
  and the recovered harness still disabled full task-condition execution.
- `experiments/iter47_provider_task_condition_command_binding_recovery/RESULT.md` blocks and
  narrows the provider command surface to two BattleSnake PvP pairs while keeping four incompatible
  pairs visible.
- `experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/RESULT.md` passes the
  zero-spend provider-compatible slice refreeze: two BattleSnake pairs selected, four historical
  pairs excluded with reasons, zero provider calls, zero spend.
- `experiments/iter49_provider_compatible_protocol_effect_execution_retry/RESULT.md` blocks before
  provider execution because the two-pair execution wrapper is not committed and the recovered
  provider harness still disables full task-condition execution. Zero provider calls, zero spend,
  no cloud runner, no GPU, and no Sentinel modification occurred.
- `experiments/iter50_provider_compatible_execution_wrapper_recovery/RESULT.md` passes the
  zero-spend wrapper-recovery gate: two selected BattleSnake pair plans, four rejected exclusions,
  zero provider calls, zero spend, no cloud runner, no GPU, and no Sentinel modification.
- `experiments/iter51_provider_compatible_protocol_effect_execution_with_wrapper/RESULT.md`
  blocks before provider execution because the wrapper remains dry-run-only and the baseline/Telos
  runtime conditions are not distinct beyond output directory. Zero provider calls, zero spend, no
  cloud runner, no GPU, and no Sentinel modification occurred.
- `experiments/iter52_provider_condition_runtime_separation_recovery/RESULT.md` passes the
  zero-spend condition-runtime separation recovery: the future baseline and Telos rows now have
  distinct commands, overlays, prompts, and a Telos receipt-validation path before acceptance.
- `experiments/iter53_provider_compatible_protocol_effect_execution_after_condition_recovery/RESULT.md`
  blocks before provider execution because the pair executor is still intentionally unimplemented,
  the base harness still disables full protocol-effect execution, the pinned CodeClash checkout is
  not ready, and Docker readiness timed out. Zero provider calls, zero spend, no cloud runner, no
  GPU, and no Sentinel modification occurred.
- `experiments/iter54_provider_pair_executor_recovery/RESULT.md` passes the zero-spend executor
  recovery gate: pinned CodeClash checkout ready, six recovered overlays copied with matching
  hashes, exact two-row command manifest materialized, Docker daemon readiness proven through the
  current Docker Desktop binary, zero provider calls, zero spend, no GPU, and no Sentinel
  modification.
- `experiments/iter55_provider_compatible_paid_execution_after_executor_recovery/HYPOTHESIS.md`
  pre-registered the smallest paid two-row provider-compatible protocol-effect pilot.
- `experiments/iter55_provider_compatible_paid_execution_after_executor_recovery/RESULT.md` blocks
  before provider execution because non-interactive ADC refresh requires reauthentication and
  dedicated-runner impersonation lacks token-creator access. Zero provider calls, zero spend, no
  cloud runner, no GPU, and no Sentinel modification occurred.
- `experiments/iter56_provider_auth_recovery_for_paid_protocol_effect/HYPOTHESIS.md` pre-registers
  the narrow credential-recovery gate needed before retrying the exact two-row paid pilot. It keeps
  the recovery ceiling at `2` provider access probes and `$1.00` spend, forbids either BattleSnake
  row from running, and forbids benchmark, leaderboard, SWE-bench, production/live-domain,
  model-superiority, or state-of-the-art claims.
- `experiments/iter56_provider_auth_recovery_for_paid_protocol_effect/RESULT.md` passes auth
  recovery: local ADC was repaired non-interactively, one minimal Vertex access probe returned
  HTTP `200` with usage metadata under a `$0.01` spend bound, and no BattleSnake row, excluded
  pair, cloud runner, GPU, Sentinel resource, or benchmark/model claim occurred.
- `experiments/iter57_provider_compatible_paid_execution_after_auth_recovery/HYPOTHESIS.md`
  pre-registers the exact two-row paid retry after auth recovery, preserving the `16` provider-call
  and `$10.00` spend ceilings and the same no-overclaim boundary.
- `experiments/iter57_provider_compatible_paid_execution_after_auth_recovery/RESULT.md` blocks
  before provider model calls because the pinned CodeClash virtualenv cannot import `google.auth`.
  One selected baseline-row attempt reached round-0 raw evidence, the Telos row and all excluded
  rows remained unattempted, and committed metadata records zero provider calls and zero cost.
- `experiments/iter58_codeclash_vertex_dependency_recovery/HYPOTHESIS.md` pre-registers the
  zero-spend recovery gate for that missing CodeClash Vertex dependency. It forbids paid rows,
  provider calls, provider spend, GPU use, Sentinel mutation, and benchmark/model claims.
- `experiments/iter58_codeclash_vertex_dependency_recovery/RESULT.md` passes dependency recovery:
  the local CodeClash virtualenv now imports `google.auth`, the pinned CodeClash commit and frozen
  provider configs remained unchanged, and no paid row, provider model call, provider spend, GPU,
  cloud runner, Sentinel mutation, or benchmark/model claim occurred.
- `experiments/iter59_provider_compatible_paid_execution_after_dependency_recovery/HYPOTHESIS.md`
  pre-registers the exact two-row paid retry after dependency recovery, preserving the `16`
  provider-call and `$10.00` spend ceilings and the same no-overclaim boundary.
- `experiments/iter59_provider_compatible_paid_execution_after_dependency_recovery/RESULT.md`
  blocks after executing both selected BattleSnake rows: each row made one provider call, recorded
  zero cost in CodeClash metadata, returned a redacted Vertex model-not-found-or-access-denied
  provider response, produced no verified-completion evidence, executed no excluded pairs, used no
  GPU, touched no Sentinel resource, and makes no benchmark/model claim.
- `experiments/iter60_provider_model_binding_recovery/HYPOTHESIS.md` pre-registers the next
  blocker-only recovery gate: recover an accessible provider model binding under a `2` call and
  `$0.05` ceiling without executing any BattleSnake row.
- `experiments/iter60_provider_model_binding_recovery/RESULT.md` blocks after adding
  `vertex_location: global` to the recovered provider model overlay. The minimal LiteLLM probe
  moved past the prior location/model-not-found failure but returned a redacted `CONSUMER_INVALID`
  quota-project response. One provider call occurred, no BattleSnake row or excluded pair ran, no
  GPU or cloud runner was used, no Sentinel resource was modified, and no benchmark/model claim is
  made.
- `experiments/iter61_vertex_quota_project_binding_recovery/HYPOTHESIS.md` pre-registers the next
  blocker-only gate: recover the LiteLLM Vertex quota-project/header binding under a `2` call and
  `$0.05` ceiling without executing any BattleSnake row.
- `experiments/iter61_vertex_quota_project_binding_recovery/RESULT.md` blocks after proving the
  Mini-SWE-Agent/LiteLLM `extra_headers` path exists. The bounded LiteLLM probe with
  `X-Goog-User-Project` still returned a redacted `CONSUMER_INVALID` response. One provider call
  occurred, no BattleSnake row or excluded pair ran, no GPU or cloud runner was used, no Sentinel
  resource was modified, and no benchmark/model claim is made.
- `experiments/iter62_vertex_bearer_token_path_recovery/HYPOTHESIS.md` pre-registers the next
  blocker-only gate: recover the LiteLLM Vertex bearer-token/header path under a `2` call and
  `$0.05` ceiling without executing any BattleSnake row.
- `experiments/iter62_vertex_bearer_token_path_recovery/RESULT.md` blocks after proving LiteLLM
  custom headers can override the default Authorization header. The bounded runtime bearer-token
  plus quota-project probe still returned a redacted `CONSUMER_INVALID` response. One provider
  call occurred, no BattleSnake row or excluded pair ran, no GPU or cloud runner was used, no
  Sentinel resource was modified, and no benchmark/model claim is made.
- `experiments/iter63_vertex_access_path_parity_recheck/RESULT.md` passes after current direct
  REST and LiteLLM probes both reach the selected Vertex global model using secret-safe runtime
  credentials. Two provider calls occurred, observed LiteLLM cost was `$0.000014`, no BattleSnake
  row or excluded pair ran, no GPU or cloud runner was used, no Sentinel resource was modified,
  and no benchmark/model claim is made.
- `experiments/iter64_provider_compatible_paid_execution_after_access_path_recovery/HYPOTHESIS.md`
  pre-registers the next execution gate: retry exactly the two frozen provider-compatible
  BattleSnake rows under the recovered access path, the `16` call and `$10.00` ceilings, full raw
  artifact/cost/receipt/redaction evidence, and no benchmark/model claim.
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
