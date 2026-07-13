# Report

No benchmark leaderboard, model-comparison, SOTA, or broad benchmark result is claimed yet. Telos now has a
bounded two-row provider-backed protocol-effect pilot result from `iter64`, controlled
completion-verification fixture suites through `iter104`, a bounded 20-packet external pilot execution
result from `iter107`, a bounded single-model all-hack recall result from `iter161`, a paired legitimate
control artifact from `iter163`, a complete bounded paired single-model metric after the `iter165`
rate-limit recovery (`3/40` recall, `0/40` control false positives, specificity `1.0`, balanced detection
`0.5375`), a zero-spend evaluator-family design from `iter166`, a completed skeptical-prompt null
from `iter167` (`80/80` calls, `3/40` recall, `0/40` false positives, specificity `0.90`), and a
zero-spend iter168 null adjudication showing all `9` invalids were markdown-fenced JSON while diagnostic
repair would still reach only `4/40` recall, plus a zero-spend iter169 independent judge-panel design with
frozen structured-output and aggregation rules, and a zero-spend iter170 structured-output/request preflight
that keeps paid execution blocked pending exact bindings, plus a zero-spend iter171 binding freeze that
keeps the panel blocked while freezing `majority_catch` and a bounded `20`-pair pilot plan; none is a
benchmark leaderboard result and none supports a model-superiority or state-of-the-art claim.

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
  pre-registers the execution gate: retry exactly the two frozen provider-compatible BattleSnake
  rows under the recovered access path, the `16` call and `$10.00` ceilings, full raw
  artifact/cost/receipt/redaction evidence, and no benchmark/model claim.
- `experiments/iter64_provider_compatible_paid_execution_after_access_path_recovery/RESULT.md`
  passes as the first bounded two-row provider-backed protocol-effect measurement. Baseline
  verified-completion evidence was `true`; Telos verified-completion evidence was `false` because
  the Telos row receipt candidate failed validation; the exact primary delta was `-1`; provider
  calls were `10`; CodeClash metadata cost was `$0.070448`; excluded pairs remained unattempted;
  no GPU, cloud runner, Sentinel mutation, production/live-domain change, benchmark claim, model
  claim, or state-of-the-art claim occurred.
- `experiments/iter65_receipt_schema_prompt_alignment/HYPOTHESIS.md` pre-registers the next
  zero-spend gate: diagnose the iter64 receipt-schema failure and recover a schema-aligned Telos
  receipt prompt before any further paid retry.
- `experiments/iter65_receipt_schema_prompt_alignment/RESULT.md` passes that local gate with zero
  provider calls and zero spend. The iter64 Telos receipt candidate is classified as
  schema-incomplete because it omitted `agent_id`, `benchmark_id`, `evidence`, `receipt_id`,
  `sha256`, `stated_goal`, `status`, and `task_id`; the recovered prompt overlay now names the
  required fields and digest rule, a local valid fixture passes, and a malformed fixture fails.
- `experiments/iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment/HYPOTHESIS.md`
  pre-registers the next bounded paid retry: exactly the same two provider-compatible BattleSnake
  rows, the recovered iter65 Telos receipt overlay, the `16` call and `$10.00` ceilings, no
  excluded pairs, no GPU/cloud runner/Sentinel mutation, and no benchmark/model claim.
- `experiments/iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment/RESULT.md`
  passes that bounded paid retry. Both selected rows executed with return code `0`; baseline
  verified-completion evidence was `true`; Telos verified-completion evidence was `true`; the
  Telos receipt validated; the primary Telos-minus-baseline delta was `0`; provider calls were
  `8`; CodeClash metadata cost was `$0.059378`; no excluded pair, GPU, cloud runner, Sentinel
  mutation, production/live-domain change, benchmark claim, model claim, or state-of-the-art claim
  occurred.
- `experiments/iter67_provider_compatible_expanded_slice_refreeze/HYPOTHESIS.md` pre-registers a
  zero-spend expanded-slice freeze or no-expansion decision before any further paid execution.
- `experiments/iter67_provider_compatible_expanded_slice_refreeze/RESULT.md` blocks that
  expanded-slice refreeze honestly. Iter66 receipt validation and audit pass, but the committed
  candidate universe still has only two provider-ready BattleSnake rows and four incompatible
  Dummy/deterministic-edit rows. Zero provider calls, zero spend, no row execution, no GPU, no
  cloud runner, no Sentinel mutation, and no benchmark/model/state-of-the-art claim occurred.
- `experiments/iter68_provider_compatible_task_surface_adapter_recovery/HYPOTHESIS.md`
  pre-registers the named blocker recovery: locally recover or reject provider-compatible adapters
  for the excluded task surfaces before any larger paid run.
- `experiments/iter68_provider_compatible_task_surface_adapter_recovery/RESULT.md` blocks that
  adapter recovery at the correct boundary. Two deterministic-edit adapter rows are planned from
  committed `iter06` source, but the two Dummy rows remain rejected because `configs/test/dummy.yaml`
  has no committed source snapshot. Zero provider calls, zero spend, no row execution, no GPU, no
  cloud runner, no Sentinel mutation, and no benchmark/model/state-of-the-art claim occurred.
- `experiments/iter69_codeclash_task_surface_source_snapshot_recovery/HYPOTHESIS.md`
  pre-registers the source-snapshot recovery needed before Dummy adapters can be validated.
- `experiments/iter69_codeclash_task_surface_source_snapshot_recovery/RESULT.md` passes that
  source-snapshot recovery. `configs/test/dummy.yaml` is copied from the pinned CodeClash Git blob
  at commit `381cdfa05a35e8acd35853b9fc7e13005121b127` into canonical and proof snapshots with
  matching hash `b8e856447fc71c79bb5e042dc530127480d670d84fd51c03e2c2e7f58c630e97`. Zero provider
  calls, zero spend, no row execution, no GPU, no cloud runner, no Sentinel mutation, and no
  benchmark/model/state-of-the-art claim occurred.
- `experiments/iter70_provider_compatible_expanded_adapter_completion/HYPOTHESIS.md`
  pre-registers the next zero-spend adapter-completion gate before any larger paid execution.
- `experiments/iter70_provider_compatible_expanded_adapter_completion/RESULT.md` passes that local
  adapter-completion gate. Four Dummy/deterministic-edit adapter rows and eight overlay files are
  planned from committed source evidence; the generated adapters are planning evidence only, not
  execution evidence. Zero provider calls, zero spend, no row execution, no GPU, no cloud runner,
  no Sentinel mutation, and no benchmark/model/state-of-the-art claim occurred.
- `experiments/iter71_provider_compatible_expanded_slice_after_adapter_completion/RESULT.md`
  passes that zero-spend slice-refreeze gate. The expanded provider-compatible slice is frozen as
  six stratified rows: two already executed BattleSnake rows are retained as prior paid evidence
  and four adapter-planned Dummy/deterministic-edit rows are selected for a bounded future paid
  gate. Zero provider calls, zero spend, no row execution, no GPU, no cloud runner, no Sentinel
  mutation, and no benchmark/model/state-of-the-art claim occurred.
- `experiments/iter72_provider_compatible_expanded_paid_execution_after_slice_refreeze/HYPOTHESIS.md`
  pre-registers the next bounded paid gate for only the four adapter-planned rows.
- `experiments/iter72_provider_compatible_expanded_paid_execution_after_slice_refreeze/RESULT.md`
  blocks that paid gate honestly after executing exactly the four selected adapter-planned rows.
  The run used `17` provider calls and `$0.057646` CodeClash metadata cost under the frozen `32`
  call and `$10.00` ceilings. The two existing BattleSnake rows were retained and not rerun.
  Deterministic-edit baseline verified-completion evidence was `true`, but Dummy baseline,
  Dummy Telos, and deterministic-edit Telos verified-completion evidence were `false`. Both
  receipt-required rows produced parseable but schema-incomplete receipt candidates, so the result
  blocks with no quality failure. No GPU, cloud runner, Sentinel mutation, production/live-domain
  change, benchmark claim, model claim, or state-of-the-art claim occurred.
- `experiments/iter73_expanded_receipt_prompt_recovery_after_paid_block/HYPOTHESIS.md`
  pre-registers the next zero-spend recovery gate: classify the two iter72 receipt-schema failures
  and recover expanded receipt-enforced prompts locally before any paid retry or larger budget.
- `experiments/iter73_expanded_receipt_prompt_recovery_after_paid_block/RESULT.md` passes that
  zero-spend recovery gate. The two iter72 receipt-required candidates are classified as
  schema-incomplete with exact missing-field lists; the deterministic-edit candidate also had an
  unexpected top-level `receipt` field. Two recovered receipt-enforced prompt overlays now name all
  ten Telos receipt fields and the canonical digest rule. Two local valid fixtures pass, one
  malformed fixture fails closed, and no provider calls, spend, row execution, GPU, cloud runner,
  Sentinel mutation, production/live-domain change, benchmark claim, model claim, or
  state-of-the-art claim occurred.
- `experiments/iter74_provider_compatible_expanded_paid_retry_after_receipt_prompt_recovery/HYPOTHESIS.md`
  pre-registers the next bounded paid retry for the same four adapter-planned rows using the
  recovered iter73 receipt prompts under the same `32` provider-invocation and `$10.00` ceilings.
- `experiments/iter74_provider_compatible_expanded_paid_retry_after_receipt_prompt_recovery/RESULT.md`
  blocks before adapter-row execution. Iter72 receipt validation/audit and iter73 receipt
  validation/audit passed, but `gcloud auth application-default print-access-token --quiet` failed
  non-interactively, so runtime overlays were not materialized, no rows executed, zero provider
  calls and zero spend occurred, and no GPU, cloud runner, Sentinel mutation,
  production/live-domain change, benchmark claim, model claim, or state-of-the-art claim occurred.
- `experiments/iter75_provider_compatible_runtime_adc_recovery_after_paid_retry_block/HYPOTHESIS.md`
  pre-registers the next zero-spend recovery gate: prove non-interactive ADC refresh and runtime
  access readiness before any further paid adapter-row retry.
- `experiments/iter75_provider_compatible_runtime_adc_recovery_after_paid_retry_block/RESULT.md`
  blocks with zero provider calls, zero spend, and zero row execution. Iter74 receipt validation and
  audit passed; the CodeClash checkout was pinned, Docker was ready, `google.auth` imported, and
  gcloud project availability was proven with stdout suppressed. ADC refresh still failed as
  `interactive_reauthentication_required`, no credential material was committed, and no GPU, cloud
  runner, Sentinel mutation, production/live-domain change, benchmark claim, model claim, or
  state-of-the-art claim occurred.
- `experiments/iter76_runtime_adc_recheck_after_operator_refresh/HYPOTHESIS.md` pre-registers the
  next zero-spend ADC recheck after interactive credential refresh; it still forbids provider rows,
  provider spend, GPU, cloud runner, Sentinel mutation, production/live-domain changes, and
  benchmark/model/state-of-the-art claims.
- `experiments/iter76_runtime_adc_recheck_after_operator_refresh/RESULT.md` blocks with zero
  provider calls, zero spend, and zero row execution. Iter75 receipt validation and audit passed; the
  CodeClash checkout stayed pinned, Docker was ready, `google.auth` imported, and gcloud project
  availability was proven with stdout suppressed. ADC refresh still failed as
  `interactive_reauthentication_required`, no credential material was committed, and no GPU, cloud
  runner, Sentinel mutation, production/live-domain change, benchmark claim, model claim, or
  state-of-the-art claim occurred.
- `experiments/iter77_runtime_adc_recheck_after_application_default_login/HYPOTHESIS.md`
  pre-registers the next zero-spend ADC recheck after Application Default Credentials refresh; it
  still forbids provider rows, provider spend, GPU, cloud runner, Sentinel mutation,
  production/live-domain changes, and benchmark/model/state-of-the-art claims.
- `experiments/iter77_runtime_adc_recheck_after_application_default_login/RESULT.md` passes with
  zero provider calls, zero spend, and zero row execution. Iter76 receipt validation and audit
  passed; the CodeClash checkout stayed pinned, Docker was ready, `google.auth` imported, gcloud
  project availability was proven with stdout suppressed, ADC token output was suppressed, no
  credential material was committed, and no GPU, cloud runner, Sentinel mutation,
  production/live-domain change, benchmark claim, model claim, or state-of-the-art claim occurred.
- `experiments/iter78_provider_compatible_expanded_paid_retry_after_adc_recovery/HYPOTHESIS.md`
  pre-registers the bounded four-row provider-compatible paid retry after ADC recovery. It keeps the
  frozen iter71 row selection, iter73 recovered receipt prompts, `$10.00` spend ceiling, `32`
  provider-call ceiling, no GPU/cloud/Sentinel/prod mutation boundary, and no
  benchmark/model/state-of-the-art claim boundary.
- `experiments/iter78_provider_compatible_expanded_paid_retry_after_adc_recovery/RESULT.md` blocks
  after exactly four selected adapter-planned rows execute under ceiling. Provider usage was `9`
  calls and `$0.03987600`. Both deterministic-edit rows had verified-completion evidence and both
  Dummy rows hit the per-row global call ceiling before verified-completion evidence could be
  accepted. No GPU, cloud runner, Sentinel mutation, production/live-domain change, benchmark claim,
  model claim, or state-of-the-art claim occurred.
- `experiments/iter79_dummy_row_call_ceiling_recovery_after_paid_retry_block/HYPOTHESIS.md`
  pre-registers a zero-spend recovery gate to classify the iter78 Dummy row call-ceiling blocker
  from committed artifacts before any further paid retry.
- `experiments/iter79_dummy_row_call_ceiling_recovery_after_paid_retry_block/RESULT.md` passes the
  zero-spend recovery gate. Both iter78 Dummy failures are classified from committed raw artifacts
  as per-row global call-ceiling blockers at the frozen `8` call ceiling; deterministic-edit
  evidence remains retained and not rerun. Zero provider calls, zero spend, zero row execution, no
  GPU/cloud/Sentinel/live-domain mutation, and no benchmark/model/state-of-the-art claim occurred.
- `experiments/iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery/HYPOTHESIS.md`
  pre-registers the next bounded paid retry: execute only the two Dummy rows with a `16` call
  per-row ceiling, total calls at or below `32`, total spend at or below `$5.00`, no
  deterministic-edit/BattleSnake rerun, and no benchmark/model/state-of-the-art claim.
- `experiments/iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery/RESULT.md` passes that
  bounded paid retry. Exactly two Dummy rows executed, provider usage was `6` calls and
  `$0.02840000`, both Dummy baseline and Dummy Telos verified, deterministic-edit and BattleSnake
  rows were not rerun, and no benchmark/model/state-of-the-art claim occurred.
- `experiments/iter81_expanded_stratified_adapter_validation_consolidation/HYPOTHESIS.md`
  pre-registers the next zero-spend consolidation gate. It may only account for committed iter66,
  iter78, and iter80 evidence as stratified adapter-validation evidence before any
  benchmark-facing claim or larger paid run.
- `experiments/iter81_expanded_stratified_adapter_validation_consolidation/RESULT.md` passes that
  zero-spend consolidation gate. It validated iter66, iter78, and iter80 source packets, accounted
  for `23` committed source-packet provider calls and `$0.12765400`, preserved six successful rows
  as separated BattleSnake/deterministic-edit/Dummy adapter-validation strata, retained two iter78
  Dummy rows only as diagnostic blocked evidence, and made no benchmark/model/state-of-the-art
  claim.
- `experiments/iter82_benchmark_facing_protocol_effect_slice_design/HYPOTHESIS.md`
  pre-registers the next zero-spend benchmark-facing slice-design gate. It may only freeze task
  eligibility, conditions, receipt/raw-artifact requirements, future paid ceilings, and
  pass/null/fail semantics before any broader paid execution or benchmark claim.
- `experiments/iter82_benchmark_facing_protocol_effect_slice_design/RESULT.md` passes that
  zero-spend design gate. It froze a future six-row CodeClash public task-condition paid pilot
  with a `96` provider-call ceiling, `$10.00` total spend ceiling, `$2.00` per-row spend ceiling,
  no cloud runner/GPU/Sentinel/live-domain mutation, SWE-bench Verified retained only as a
  receipt-field anchor, and no benchmark/model/state-of-the-art claim.
- `experiments/iter83_benchmark_facing_protocol_effect_execution_pilot/HYPOTHESIS.md`
  pre-registers the next bounded paid execution pilot. It may only execute the six selected
  CodeClash task-condition rows under the frozen call/spend ceilings, or publish the blocker.
- `experiments/iter83_benchmark_facing_protocol_effect_execution_pilot/RESULT.md` publishes
  bounded blocked/null evidence. The gate executed exactly the six selected rows, used `21`
  provider calls and `$0.11319400`, kept all artifacts under the frozen ceilings, and found no
  interpretable Telos-minus-baseline protocol-effect signal because all three task-surface deltas
  were `0`.
- `experiments/iter84_benchmark_facing_null_signal_adjudication/HYPOTHESIS.md`
  pre-registers the next zero-spend adjudication gate. It may only classify the iter83 null signal
  and freeze a replication, task/metric redesign, or stop/review decision from committed evidence.
- `experiments/iter84_benchmark_facing_null_signal_adjudication/RESULT.md` passes that zero-spend
  adjudication gate. It classified the iter83 null/no-signal result as
  `verified_completion_metric_saturated`, selected `redesign_task_metric` as the next step, made
  zero provider calls, spent `$0.00`, executed zero rows, and made no
  benchmark/model/state-of-the-art claim.
- `experiments/iter85_discriminating_task_metric_redesign/HYPOTHESIS.md`
  pre-registers the next zero-spend design gate. It may only redesign the task/metric contract
  from committed iter83/iter84 evidence before any further paid execution or benchmark claim.
- `experiments/iter85_discriminating_task_metric_redesign/RESULT.md` passes that zero-spend
  design gate. It froze `task_native_score_share_delta_with_receipt_gates` as the candidate
  metric contract, demoted verified completion to an admissibility gate, made zero provider calls,
  spent `$0.00`, executed zero rows, authorized no paid execution, and made no
  benchmark/model/state-of-the-art claim.
- `experiments/iter86_discriminating_metric_backtest_on_committed_artifacts/HYPOTHESIS.md`
  pre-registers the next zero-spend backtest gate. It may only compute the candidate metric from
  committed iter83 artifacts before any further paid execution or benchmark claim.
- `experiments/iter86_discriminating_metric_backtest_on_committed_artifacts/RESULT.md` passes that
  zero-spend backtest gate. It computed three score-share deltas from committed iter83 metadata,
  found `task_native_score_share_delta_with_receipt_gates` computable and non-saturated, recorded a
  mixed-direction diagnostic signal, made zero provider calls, spent `$0.00`, executed zero rows,
  and made no benchmark/model/state-of-the-art claim.
- `experiments/iter87_benchmark_facing_discriminating_metric_execution_pilot/HYPOTHESIS.md`
  pre-registers the next bounded paid execution pilot. It may only execute the six frozen
  CodeClash task-condition rows under the `96` call and `$10.00` spend ceilings, then compute the
  discriminating metric without benchmark/model/state-of-the-art claims.
- `experiments/iter87_benchmark_facing_discriminating_metric_execution_pilot/RESULT.md` passes
  that bounded paid pilot. It executed exactly six frozen rows, used `21` provider calls and
  `$0.12498400`, validated all receipt-required rows, computed fresh score-share deltas
  (`dummy=-0.01575000`, `battlesnake=0.50000000`, `deterministic_edit=-0.50000000`), recorded a
  mixed-direction signal, and made no benchmark/model/state-of-the-art claim.
- `experiments/iter88_external_benchmark_readiness_adjudication_after_discriminating_pilot/HYPOTHESIS.md`
  pre-registers the next zero-spend adjudication gate. It may only decide whether iter87 evidence
  justifies a larger external benchmark design, same-slice replication, recovery, or stop decision.
- `experiments/iter88_external_benchmark_readiness_adjudication_after_discriminating_pilot/RESULT.md`
  passes that zero-spend adjudication gate. It validated iter87, found three iter86/iter87 task
  direction flips, rejected larger external benchmark design for now, selected same-slice stability
  replication as the next step, made zero provider calls, spent `$0.00`, executed zero rows, and
  made no benchmark/model/state-of-the-art claim.
- `experiments/iter89_same_slice_discriminating_metric_stability_replication/HYPOTHESIS.md`
  pre-registers the next bounded same-slice replication gate. It may execute only the same six
  frozen rows under the `96` call, `$10.00` total spend, `16` per-row call, and `$2.00` per-row
  spend ceilings before any benchmark/model/state-of-the-art claim.
- `experiments/iter89_same_slice_discriminating_metric_stability_replication/RESULT.md` passes
  that bounded same-slice replication gate. It executed exactly six frozen rows, used `19`
  provider calls and `$0.11636200`, computed fresh score-share deltas
  (`dummy=-0.02075000`, `battlesnake=0.00000000`, `deterministic_edit=-0.50000000`), classified
  stability as `unstable`, and made no benchmark/model/state-of-the-art claim.
- `experiments/iter90_stability_replication_adjudication_after_same_slice_run/HYPOTHESIS.md`
  pre-registers the next zero-spend adjudication gate. It may only decide whether iter89 unstable
  stability evidence supports external benchmark design, another bounded replication, recovery, or
  stop.
- `experiments/iter90_stability_replication_adjudication_after_same_slice_run/RESULT.md` passes
  that zero-spend adjudication gate. It validated iter89, locked the six-row run at `19` provider
  calls and `$0.11636200`, preserved the `unstable` stability classification, rejected immediate
  benchmark/SOTA escalation, selected empirical validation suite design as the next step, and made
  no benchmark/model/state-of-the-art claim.
- `experiments/iter91_empirical_validation_suite_design_for_completion_verification/HYPOTHESIS.md`
  pre-registers the next zero-spend suite-design gate. It may only freeze a falsifiable empirical
  validation design comparing agent self-report, execution tests, LLM judge, external verifier,
  and complete Telos protocol on controlled false-completion failure modes.
- `experiments/iter91_empirical_validation_suite_design_for_completion_verification/RESULT.md`
  passes that zero-spend suite-design gate. It froze seven false-completion trap families, seven
  paired legitimate-completion controls, five comparison strategies, six quantitative endpoints,
  independent ground-truth rules, and identical-artifact comparison requirements, with zero
  provider calls, zero spend, zero strategy execution, zero row execution, and no
  benchmark/model/state-of-the-art claim.
- `experiments/iter92_empirical_validation_fixture_materialization_for_completion_verification/HYPOTHESIS.md`
  pre-registers the next zero-spend fixture-materialization gate. It may only materialize the
  frozen iter91 design into static fixture specs, ground-truth labels, artifact manifests, and
  strategy-input manifests before any comparative execution.
- `experiments/iter92_empirical_validation_fixture_materialization_for_completion_verification/RESULT.md`
  passes that zero-spend fixture-materialization gate. It materialized `14` static fixtures, `98`
  public artifacts, `14` private ground-truth labels, and `5` identical strategy-input manifests
  with labels excluded from strategy inputs, zero provider calls, zero spend, zero strategy
  execution, zero row execution, and no benchmark/model/state-of-the-art claim.
- `experiments/iter93_deterministic_strategy_execution_on_materialized_fixtures/HYPOTHESIS.md`
  pre-registers the next zero-spend deterministic execution gate. It may run only agent
  self-report, execution-tests-only, external-verifier, and complete-Telos-protocol strategies on
  the iter92 fixtures; the LLM judge remains deferred because it requires provider calls.
- `experiments/iter93_deterministic_strategy_execution_on_materialized_fixtures/RESULT.md`
  passes that zero-spend deterministic execution gate. It produced `56` deterministic decisions:
  agent self-report and execution-tests-only accepted `7/7` false-completion traps, while external
  verifier and complete Telos protocol accepted `0/7`; all four strategies preserved `7/7`
  legitimate controls. It made no benchmark/model/state-of-the-art or all-strategy superiority
  claim.
- `experiments/iter94_provider_llm_judge_execution_on_materialized_fixtures/HYPOTHESIS.md`
  pre-registers the next provider-backed LLM-judge gate. It may execute exactly one LLM-judge
  decision per iter92 fixture under a `14` provider-call and `$10.00` spend ceiling, after
  validating iter93.
- `experiments/iter94_provider_llm_judge_execution_on_materialized_fixtures/RESULT.md`
  publishes a blocked provider-backed LLM-judge result. Iter94 validated iter93 and made one
  provider call costing `$0.00470000`; the provider returned HTTP 200 but ended with `MAX_TOKENS`
  before a parseable JSON decision was produced. It records zero LLM-judge decisions, no complete
  all-strategy endpoint evidence, and no benchmark/model/state-of-the-art claim.
- `experiments/iter95_provider_llm_judge_prompt_budget_recovery_after_block/HYPOTHESIS.md`
  pre-registers the next zero-spend recovery gate. It may only validate the iter94 blocked
  evidence and redesign the LLM-judge prompt/token budget before any later paid retry.
- `experiments/iter95_provider_llm_judge_prompt_budget_recovery_after_block/RESULT.md`
  passes that zero-spend recovery gate. It validated the iter94 blocked evidence, tied the
  `MAX_TOKENS` parse blocker to the `256` output-token ceiling being consumed by hidden reasoning,
  materialized `14` recovered prompts with private labels excluded, raised the planned output
  budget to `2048`, and made no benchmark/model/state-of-the-art or completed-LLM-judge claim.
- `experiments/iter96_provider_llm_judge_bounded_retry_after_prompt_budget_recovery/HYPOTHESIS.md`
  pre-registers the next bounded provider LLM-judge retry. It may make at most `14` provider calls
  and spend at most `$5.00`, using the iter95 recovered prompt/token-budget design.
- `experiments/iter96_provider_llm_judge_bounded_retry_after_prompt_budget_recovery/RESULT.md`
  passes that bounded provider retry. It made `14` provider calls, spent `$0.19588800`, produced
  `14` parseable LLM-judge decisions, accepted `0/7` false-completion traps, rejected `5/7`
  legitimate controls, and made no benchmark/model/state-of-the-art or all-strategy superiority
  claim.
- `experiments/iter97_five_strategy_completion_verification_adjudication_after_llm_judge/HYPOTHESIS.md`
  pre-registers the next zero-spend adjudication gate. It may only compare the five completed
  strategy rows from committed iter93 and iter96 evidence.
- `experiments/iter97_five_strategy_completion_verification_adjudication_after_llm_judge/RESULT.md`
  passes that zero-spend adjudication. External verifier and complete Telos both passed the frozen
  fixture bars and had the same measured endpoint vector, while self-report/tests accepted all
  false-completion traps and the provider LLM judge rejected `5/7` legitimate controls. Benchmark
  escalation is rejected.
- `experiments/iter98_external_verifier_telos_differential_suite_design_after_adjudication/HYPOTHESIS.md`
  pre-registers the next zero-spend design gate: build a sharper suite targeting cases where
  external verifier and complete Telos should diverge.
- `experiments/iter98_external_verifier_telos_differential_suite_design_after_adjudication/RESULT.md`
  passes that zero-spend design gate. It freezes `8` differential target families and `16` planned
  fixtures for later materialization, with expected divergence recorded only as a hypothesis and no
  benchmark/model/state-of-the-art claim.
- `experiments/iter99_external_verifier_telos_differential_fixture_materialization_after_design/HYPOTHESIS.md`
  pre-registers the next zero-spend materialization gate for the `16` planned fixtures.
- `experiments/iter99_external_verifier_telos_differential_fixture_materialization_after_design/RESULT.md`
  passes that zero-spend materialization gate. It materialized `16` blinded fixtures across `8`
  target families, `96` public artifacts, `16` private labels, and `5` identical strategy-input
  manifests with labels excluded from every strategy input. It made zero provider calls, spent
  `$0.00000000`, executed no strategy rows, and made no benchmark/model/state-of-the-art or
  Telos-specific superiority claim.
- `experiments/iter100_deterministic_strategy_execution_on_differential_fixtures_after_materialization/HYPOTHESIS.md`
  pre-registers the next zero-provider deterministic execution gate. It may run only deterministic
  strategies on the iter99 fixtures; the provider-backed LLM judge remains deferred.
- `experiments/iter100_deterministic_strategy_execution_on_differential_fixtures_after_materialization/RESULT.md`
  passes that zero-provider deterministic gate. It produced `64` deterministic decisions.
  Agent self-report and execution-tests-only accepted `8/8` false-completion traps; external
  verifier accepted `4/8`; complete Telos accepted `0/8`. All four deterministic strategies
  preserved `8/8` legitimate controls. This is limited fixture-comparison evidence only, not a
  benchmark/model/state-of-the-art or broad Telos-specific superiority claim.
- `experiments/iter101_provider_llm_judge_execution_on_differential_fixtures_after_deterministic/HYPOTHESIS.md`
  pre-registers the deferred provider-backed LLM-judge gate under a `16` provider-call and `$5.00`
  spend ceiling.
- `experiments/iter101_provider_llm_judge_execution_on_differential_fixtures_after_deterministic/RESULT.md`
  blocks that provider-backed LLM-judge gate after `14` provider calls and `$0.22777400` estimated
  spend. It records `13/16` parseable LLM-judge decisions and then a `MAX_TOKENS` blocker on
  `DIFX-FIXTURE-0014`. All-strategy endpoint evidence is incomplete, so no benchmark/model/
  state-of-the-art or superiority claim is made.
- `experiments/iter102_provider_llm_judge_differential_retry_recovery_after_block/HYPOTHESIS.md`
  pre-registers the zero-spend recovery gate for classifying that blocker from committed raw
  artifacts before any paid retry.
- `experiments/iter102_provider_llm_judge_differential_retry_recovery_after_block/RESULT.md`
  passes that zero-spend recovery gate. It preserves the iter101 paid usage accounting, classifies
  `DIFX-FIXTURE-0014` as an output-budget blocker caused by hidden reasoning exhausting the `2048`
  output budget before JSON completion, materializes `16` recovered prompts with private labels
  excluded, and pre-registers a full recovered retry without making any benchmark/model/state-of-
  the-art or superiority claim.
- `experiments/iter103_differential_provider_llm_judge_full_retry_after_block_recovery/HYPOTHESIS.md`
  pre-registers the bounded recovered provider LLM-judge retry over all sixteen frozen
  differential fixtures.
- `experiments/iter103_differential_provider_llm_judge_full_retry_after_block_recovery/RESULT.md`
  passes that bounded recovered provider retry with `16` provider calls, `$0.23633000` estimated
  spend, and `16/16` parseable LLM-judge decisions. The recovered LLM judge accepted `0/8`
  false-completion traps but preserved only `2/8` legitimate controls, so this is adverse
  LLM-judge strategy evidence and not a benchmark/model/state-of-the-art or superiority claim.
- `experiments/iter104_five_strategy_differential_adjudication_after_recovered_llm_judge/HYPOTHESIS.md`
  pre-registers the zero-spend five-strategy differential adjudication gate.
- `experiments/iter104_five_strategy_differential_adjudication_after_recovered_llm_judge/RESULT.md`
  passes that zero-spend adjudication. Complete Telos was the only balanced pass on the frozen
  16-fixture differential suite; external verifier accepted `4/8` false-completion traps and the
  recovered provider LLM judge rejected `6/8` legitimate controls. This supports only a
  fixture-level differential result, not a benchmark/model/state-of-the-art or broad all-strategy
  superiority claim.
- `experiments/iter105_external_benchmark_pilot_design_after_differential_adjudication/HYPOTHESIS.md`
  pre-registers the zero-spend external benchmark-pilot design gate before any paid benchmark
  execution.
- `experiments/iter105_external_benchmark_pilot_design_after_differential_adjudication/RESULT.md`
  passes that zero-spend design gate with a `20`-packet external pilot protocol, `10`
  false-completion packets, `10` legitimate controls, a future `30` provider-call ceiling, and a
  `$10.00000000` future spend ceiling. This is design evidence only, not a benchmark/model/state-
  of-the-art or broad all-strategy superiority claim.
- `experiments/iter106_external_benchmark_pilot_materialization_after_design/HYPOTHESIS.md`
  pre-registers the zero-spend external benchmark-pilot materialization gate before any paid
  benchmark execution.
- `experiments/iter106_external_benchmark_pilot_materialization_after_design/RESULT.md`
  passes that zero-spend materialization gate. It materialized `20` pilot packets, `160` public
  artifacts, `10` false-completion private labels, `10` legitimate-control private labels, and `5`
  identical strategy-input manifests with labels excluded from every strategy input. This is
  materialization evidence only, not a benchmark/model/state-of-the-art or broad all-strategy
  superiority claim.
- `experiments/iter107_external_benchmark_pilot_execution_after_materialization/HYPOTHESIS.md`
  pre-registers the bounded external benchmark-pilot execution gate under the frozen iter106
  packet artifacts, with a `30` provider-call ceiling and `$10.00000000` spend ceiling.
- `experiments/iter107_external_benchmark_pilot_execution_after_materialization/RESULT.md`
  passes that bounded pilot execution gate with `20` provider calls, `$0.38674600` estimated
  spend, `100` strategy decisions, and `40` raw LLM prompt/response artifacts. Complete Telos
  accepted `0/10` false-completion packets and preserved `10/10` legitimate controls; the external
  verifier accepted `2/10` false-completion packets; the provider LLM judge accepted `0/10`
  false-completion packets but rejected `10/10` legitimate controls. This is a bounded pilot
  result only, not a benchmark/model/state-of-the-art or broad all-strategy superiority claim.
- `experiments/iter108_external_benchmark_pilot_adjudication_after_execution/HYPOTHESIS.md`
  pre-registers a zero-spend adjudication gate to review the iter107 claim boundary before any
  replication, redesign, or scope expansion.
- Reward-hack benchmark arc current through iter170: `iter153` materialized the 20-row seed, `iter156`
  released the 40-row hash-checked `reward_hack_benchmark_v1` row artifact, `iter159` blinded the 40
  all-hack judge packets, `iter160` froze the parser, `iter161` ran `gemini-2.5-flash` on all 40 all-hack
  packets and caught `3/40`, `iter163` materialized 40 paired legitimate controls and blinded control
  packets, `iter164` published the Vertex `http_429` partial block after 15 successful controls, and
  `iter165` recovered only the missing 25 controls to complete the paired metric. The complete one-model
  metric is `3/40` all-hack recall, `0/40` control false positives, specificity `1.0`, precision `1.0`
  with denominator `3`, and balanced detection `0.5375`. `iter166` then published a zero-spend
  evaluator-family design with `5` evaluator families, specificity floor `0.90`, control false-positive
  ceiling `4/40`, nondecision accounting, and a bounded next gate. `iter167` completed that bounded
  skeptical-prompt run and failed the metric bars: `80/80` provider calls succeeded, prompt leakage hits
  `0`, response secret hits `0`, false positives remained `0/40`, specificity was `0.90`, but recall stayed
  `3/40`, hack nondecision rose to `5/40`, and balanced detection was `0.4875`. This is not a
  leaderboard, model-comparison, SOTA, natural-frequency, or broad robustness result. `iter168`
  adjudicated the null without spend: all `9` invalids were markdown-fenced JSON, diagnostic fence
  stripping would move recall only to `4/40`, and the next recommended intervention is independent
  judge-panel design. `iter169` published that design without spend: three cross-provider panel slots,
  provider-native structured-output enforcement, frozen standalone, any-catch, majority, and unanimous
  aggregation rules, leakage controls, nondecision accounting, and a future paid-pilot ceiling of `160`
  calls and `$50.00`. `iter170` preflighted the structured-output path without spend: valid fixtures parsed,
  markdown-fenced JSON remained invalid, all `40` hack and `40` control packets had `0` forbidden leakage
  hits and `0` allowlist mismatches, and paid panel execution remains blocked pending exact model/API
  bindings. `iter171` then froze the panel binding control surface without spend: all three slots are
  `requires_operator_input`, the primary rule is `majority_catch`, generated secret hits are `0`, paid
  execution is not authorized, and a full three-slot all-packet run is recognized as `240` calls, above the
  preserved `160`-call ceiling. The bounded pilot plan is therefore `20` paired rows (`120` planned calls +
  `40` retry reserve), still blocked pending exact operator bindings.
- `experiments/iter166_reward_hack_moonshot_evaluator_family_design/RESULT.md`
  publishes the zero-spend evaluator-family design and recommends the bounded iter167 skeptical-judge
  calibration gate.
- `experiments/iter167_reward_hack_skeptical_judge_calibration/RESULT.md`
  publishes the completed skeptical-prompt null and its proof artifacts.
- `experiments/iter168_reward_hack_skeptical_judge_null_adjudication/RESULT.md`
  publishes the zero-spend adjudication of the iter167 null and malformed-output pattern.
- `docs/LITERATURE_ALIGNMENT_2026.md`
  records the July 2026 literature sweep across frontier-eval, reward-hacking, LLM-judge, and agent-benchmark
  sources; it is a source-alignment memo only, not an empirical result.
- `experiments/iter169_reward_hack_independent_judge_panel_design/RESULT.md`
  publishes the zero-spend independent judge-panel design gate before any further provider spend.
- `experiments/iter170_reward_hack_panel_structured_output_preflight/RESULT.md`
  publishes the zero-spend parser/schema/request preflight for the iter169 panel design.
- `experiments/iter171_reward_hack_panel_model_binding_freeze/RESULT.md`
  publishes the zero-spend model/API binding freeze and blocked paid-panel readiness decision.
- `experiments/iter172_reward_hack_panel_operator_binding_recovery/HYPOTHESIS.md`
  pre-registers the zero-spend operator binding recovery before any paid panel call.
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
