# HANDOFF - dynamic state snapshot

Generated: 2026-07-16T02:42:19Z by `scripts/make_handoff.py`. Read the Current Gate section before consulting the
runtime-bound `CONTINUITY.md` upstream record.

TELOS is a standalone repository. Resolve its root with `git rev-parse --show-toplevel`, then run every TELOS command from that root.

## Repository State

```text
source_branch: agent/iter205-workflow-context-recovery
source_commit: c1137f896b7ee3c9a26ee35bcda2c5f5c6b79446
publication_target: master
```

Working tree:

```text
 M .github/workflows/ci.yml
 M README.md
 M docs/COMPLETION_VERIFICATION_REPORT.md
 M docs/LITERATURE_ALIGNMENT_2026.md
 M docs/MISSION_LOOP.md
 M docs/NEXT_PHASE.md
 M docs/REPORT.md
 M mission/loop.json
 M paper/README.md
 M paper/telos.pdf
 M paper/telos.tex
 M results/README.md
 M scripts/make_handoff.py
 M scripts/validate_current_paper.py
 M scripts/validate_detector_methodology_correction.py
 M scripts/validate_handoff.py
 M scripts/validate_mission_loop.py
 M scripts/validate_supply_chain.py
 M tests/test_detector_methodology_correction.py
 M tests/test_iter204_infrastructure_recovery.py
 M tests/test_make_handoff.py
 M tests/test_mission_loop_guard.py
 M tests/test_supply_chain_guard.py
?? .github/workflows/iter205-execute.yml
?? experiments/iter204_iter203_infrastructure_recovery/RESULT.md
?? experiments/iter204_iter203_infrastructure_recovery/proof/pre_dispatch_infrastructure_null.json
?? experiments/iter204_iter203_infrastructure_recovery/proof/raw/public_dispatch_metadata/
?? experiments/iter205_iter204_workflow_context_recovery/
?? scripts/adjudicate_iter205_workflow_context_recovery.py
?? scripts/build_iter205_runtime_manifest.py
?? scripts/capture_iter205_runtime_host.py
?? scripts/ci_iter205_execute.sh
?? scripts/ci_iter205_smoke.sh
?? scripts/collect_iter205_execution.py
?? scripts/prepare_iter205_output_directory.py
?? scripts/publish_iter205_runtime_diagnostic.py
?? scripts/run_iter205_workflow_context_recovery_blind_judge.py
?? scripts/validate_iter204_pre_dispatch_null.py
?? scripts/validate_iter205_publication_safety.py
?? scripts/validate_iter205_runtime_recovery.py
?? tests/test_iter204_pre_dispatch_null.py
?? tests/test_iter205_workflow_context_recovery.py
```

## Experiments

- experiments/iter00_target_survey: RESULT PUBLISHED
- experiments/iter01_receipt_dry_run: RESULT PUBLISHED
- experiments/iter02_public_task_slice: RESULT PUBLISHED
- experiments/iter03_codeclash_smoke: RESULT PUBLISHED
- experiments/iter04_agent_behavior_slice: RESULT PUBLISHED
- experiments/iter05_agent_behavior_smoke: RESULT PUBLISHED
- experiments/iter06_deterministic_edit_slice: RESULT PUBLISHED
- experiments/iter07_deterministic_edit_smoke: RESULT PUBLISHED
- experiments/iter08_provider_model_pilot_slice: RESULT PUBLISHED
- experiments/iter09_provider_model_pilot_smoke: RESULT PUBLISHED
- experiments/iter100_deterministic_strategy_execution_on_differential_fixtures_after_materialization: RESULT PUBLISHED
- experiments/iter101_provider_llm_judge_execution_on_differential_fixtures_after_deterministic: RESULT PUBLISHED
- experiments/iter102_provider_llm_judge_differential_retry_recovery_after_block: RESULT PUBLISHED
- experiments/iter103_differential_provider_llm_judge_full_retry_after_block_recovery: RESULT PUBLISHED
- experiments/iter104_five_strategy_differential_adjudication_after_recovered_llm_judge: RESULT PUBLISHED
- experiments/iter105_external_benchmark_pilot_design_after_differential_adjudication: RESULT PUBLISHED
- experiments/iter106_external_benchmark_pilot_materialization_after_design: RESULT PUBLISHED
- experiments/iter107_external_benchmark_pilot_execution_after_materialization: RESULT PUBLISHED
- experiments/iter108_external_benchmark_pilot_adjudication_after_execution: HYPOTHESIS ONLY (inactive or superseded)
- experiments/iter109_real_trajectory_tamper_detection_pilot: RESULT PUBLISHED
- experiments/iter10_provider_auth_recovery: RESULT PUBLISHED
- experiments/iter110_adversarial_hardening_hacker_fixer_loop: RESULT PUBLISHED
- experiments/iter111_llm_judge_steelman_baseline: RESULT PUBLISHED
- experiments/iter112_stealth_divergence_judge_vs_detector: RESULT PUBLISHED
- experiments/iter113_native_execution_ground_truth: RESULT PUBLISHED
- experiments/iter114_batch_native_execution: RESULT PUBLISHED
- experiments/iter115_wider_batch_native_execution: RESULT PUBLISHED
- experiments/iter116_executed_hack_catch_rate: RESULT PUBLISHED
- experiments/iter117_precision_coverage_boundary: RESULT PUBLISHED
- experiments/iter118_both_miss_stealth_class: RESULT PUBLISHED
- experiments/iter119_metamorphic_defense: RESULT PUBLISHED
- experiments/iter11_provider_model_pilot_retry: RESULT PUBLISHED
- experiments/iter120_generalized_metamorphic: RESULT PUBLISHED
- experiments/iter121_gold_free_property_oracle: RESULT PUBLISHED
- experiments/iter122_automatic_property_generation: RESULT PUBLISHED
- experiments/iter123_visible_test_anchor_filter: RESULT PUBLISHED
- experiments/iter124_property_generation_at_scale: RESULT PUBLISHED
- experiments/iter125_harness_synthesizer: RESULT PUBLISHED
- experiments/iter126_gold_free_soundness_gate: RESULT PUBLISHED
- experiments/iter127_structured_input_residuals: RESULT PUBLISHED
- experiments/iter128_property_strategy_taxonomy: RESULT PUBLISHED
- experiments/iter129_applicability_and_strategy_selection: RESULT PUBLISHED
- experiments/iter12_vertex_model_access_recovery: RESULT PUBLISHED
- experiments/iter130_cross_repo_widening: RESULT PUBLISHED
- experiments/iter131_symbolic_evaluation: RESULT PUBLISHED
- experiments/iter132_docker_harness_prototype: RESULT PUBLISHED
- experiments/iter133_docker_batch_environment_bound: RESULT PUBLISHED
- experiments/iter134_x86_ci_docker_batch: RESULT PUBLISHED
- experiments/iter135_full_stack_in_container: RESULT PUBLISHED
- experiments/iter136_full_stack_batch_scale: RESULT PUBLISHED
- experiments/iter137_property_rate_wider: RESULT PUBLISHED
- experiments/iter138_applicability_survey: RESULT PUBLISHED
- experiments/iter139_property_derivability: RESULT PUBLISHED
- experiments/iter13_provider_model_pilot_retry_after_access_recovery: RESULT PUBLISHED
- experiments/iter140_both_miss_construction_hardness: RESULT PUBLISHED
- experiments/iter141_frontier_hacker_fixer_both_miss: RESULT PUBLISHED
- experiments/iter142_frontier_both_miss_rate: RESULT PUBLISHED
- experiments/iter143_frontier_judge_robustness: RESULT PUBLISHED
- experiments/iter144_cross_repo_both_miss_sympy: RESULT PUBLISHED
- experiments/iter145_judge_panel_before_execution: RESULT PUBLISHED
- experiments/iter146_protocol_effect_gate_and_repair: RESULT PUBLISHED
- experiments/iter147_legitimate_completion_control: RESULT PUBLISHED
- experiments/iter148_protocol_effect_replication: RESULT PUBLISHED
- experiments/iter149_gold_free_oracle_intervention: RESULT PUBLISHED
- experiments/iter14_provider_diff_quality_review: RESULT PUBLISHED
- experiments/iter150_gold_free_oracle_rate: RESULT PUBLISHED
- experiments/iter151_cross_repo_scale_official: RESULT PUBLISHED
- experiments/iter152_reward_model_gaming_scale: RESULT PUBLISHED
- experiments/iter153_reward_hack_benchmark_seed_materialization: RESULT PUBLISHED
- experiments/iter154_reward_hack_benchmark_expansion_pilot: RESULT PUBLISHED
- experiments/iter155_adaptive_reward_hack_expansion: RESULT PUBLISHED
- experiments/iter156_reward_hack_benchmark_v1_manifest: RESULT PUBLISHED
- experiments/iter157_paper_plain_language_completion: RESULT PUBLISHED
- experiments/iter158_reward_hack_moonshot_design: RESULT PUBLISHED
- experiments/iter159_reward_hack_blinded_packet_materialization: RESULT PUBLISHED
- experiments/iter15_provider_strict_diff_rerun: RESULT PUBLISHED (FAIL)
- experiments/iter160_reward_hack_judge_parser_preflight: RESULT PUBLISHED
- experiments/iter161_reward_hack_single_model_judge_execution: RESULT PUBLISHED
- experiments/iter162_reward_hack_legitimate_control_design: RESULT PUBLISHED
- experiments/iter163_reward_hack_legitimate_control_materialization: RESULT PUBLISHED
- experiments/iter164_reward_hack_single_model_control_evaluation: RESULT PUBLISHED
- experiments/iter165_reward_hack_control_evaluation_rate_limit_recovery: RESULT PUBLISHED
- experiments/iter166_reward_hack_moonshot_evaluator_family_design: RESULT PUBLISHED
- experiments/iter167_reward_hack_skeptical_judge_calibration: RESULT PUBLISHED (FAIL)
- experiments/iter168_reward_hack_skeptical_judge_null_adjudication: RESULT PUBLISHED
- experiments/iter169_reward_hack_independent_judge_panel_design: RESULT PUBLISHED
- experiments/iter16_provider_workspace_hygiene_control: RESULT PUBLISHED
- experiments/iter170_reward_hack_panel_structured_output_preflight: RESULT PUBLISHED
- experiments/iter171_reward_hack_panel_model_binding_freeze: RESULT PUBLISHED
- experiments/iter172_reward_hack_panel_operator_binding_recovery: RESULT PUBLISHED
- experiments/iter173_reward_hack_panel_public_binding_menu: RESULT PUBLISHED
- experiments/iter174_reward_hack_panel_default_choice_freeze: RESULT PUBLISHED
- experiments/iter175_reward_hack_panel_bounded_paid_pilot: RESULT PUBLISHED
- experiments/iter176_reward_hack_panel_result_adjudication: RESULT PUBLISHED
- experiments/iter177_reward_hack_panel_disagreement_calibrated_expansion_design: RESULT PUBLISHED
- experiments/iter178_reward_hack_panel_remaining_pairs_paid_expansion: RESULT PUBLISHED
- experiments/iter179_reward_hack_panel_full_cohort_adjudication: RESULT PUBLISHED
- experiments/iter17_provider_lint_hygiene_control: RESULT PUBLISHED
- experiments/iter180_reward_hack_panel_openai_nondecision_repair_design: RESULT PUBLISHED
- experiments/iter181_reward_hack_panel_openai_nondecision_repair_execution: RESULT PUBLISHED
- experiments/iter182_reward_hack_panel_repair_execution_adjudication: RESULT PUBLISHED
- experiments/iter183_reward_hack_panel_public_claim_surface_sync: RESULT PUBLISHED
- experiments/iter184_reward_hack_panel_frontier_research_alignment_design: RESULT PUBLISHED
- experiments/iter185_reward_hack_panel_miss_property_probe_design: RESULT PUBLISHED
- experiments/iter186_reward_hack_panel_property_probe_packet_materialization: RESULT PUBLISHED
- experiments/iter187_reward_hack_property_generator_schema_preflight: RESULT PUBLISHED
- experiments/iter188_telos_mission_data_process_audit_design: RESULT PUBLISHED
- experiments/iter189_telos_mission_evidence_data_process_audit: RESULT PUBLISHED
- experiments/iter18_provider_behavior_depth_control: RESULT PUBLISHED
- experiments/iter190_reward_hack_property_generator_bounded_execution: RESULT PUBLISHED
- experiments/iter191_reward_hack_property_execution_contract_design: HYPOTHESIS ONLY (inactive or superseded)
- experiments/iter192_reward_hack_benchmark_construct_validity_audit: RESULT PUBLISHED
- experiments/iter193_certified_resolved_reward_hack_construction: RESULT PUBLISHED
- experiments/iter194_certified_resolved_oracle_and_runner_fix: RESULT PUBLISHED
- experiments/iter195_synthesized_input_differential_oracle: RESULT PUBLISHED
- experiments/iter196_detector_vs_certified_hacks: RESULT PUBLISHED
- experiments/iter197_gold_free_oracle_vs_certified_hacks: RESULT PUBLISHED (FAIL)
- experiments/iter198_findings_paper_synthesis_and_accessibility: RESULT PUBLISHED
- experiments/iter199_benchmark_expansion_across_repos: RESULT PUBLISHED
- experiments/iter19_provider_final_inspection_control: RESULT PUBLISHED
- experiments/iter200_natural_certified_yet_wrong_rate: RESULT PUBLISHED
- experiments/iter201_detectors_on_full_benchmark: RESULT PUBLISHED (FAIL)
- experiments/iter202_natural_rate_scaled: RESULT PUBLISHED
- experiments/iter203_iter202_safety_recovery: RESULT PUBLISHED
- experiments/iter204_iter203_infrastructure_recovery: RESULT PUBLISHED
- experiments/iter205_iter204_workflow_context_recovery: HYPOTHESIS ACTIVE, result pending
- experiments/iter20_behavior_semantic_verification: RESULT PUBLISHED
- experiments/iter21_opponent_collision_control: RESULT PUBLISHED
- experiments/iter22_semantic_mutation_guard: RESULT PUBLISHED
- experiments/iter23_tail_semantics_falsification: RESULT PUBLISHED (FAIL)
- experiments/iter24_tail_safety_control: RESULT PUBLISHED
- experiments/iter25_tail_safety_mutation_guard: RESULT PUBLISHED (FAIL)
- experiments/iter26_own_tail_redundancy_mutation_guard: RESULT PUBLISHED
- experiments/iter27_semantic_claim_boundary_matrix: RESULT PUBLISHED
- experiments/iter28_public_claim_surface_guard: RESULT PUBLISHED
- experiments/iter29_public_claim_surface_negative_guard: RESULT PUBLISHED
- experiments/iter30_boundary_matrix_schema_guard: RESULT PUBLISHED
- experiments/iter31_claim_boundary_release_manifest: RESULT PUBLISHED
- experiments/iter32_claim_boundary_release_manifest_negative_guard: RESULT PUBLISHED
- experiments/iter33_release_manifest_public_sync_guard: RESULT PUBLISHED
- experiments/iter34_release_manifest_public_sync_negative_guard: RESULT PUBLISHED
- experiments/iter35_release_manifest_self_coverage_guard: RESULT PUBLISHED
- experiments/iter36_release_manifest_self_coverage_negative_guard: RESULT PUBLISHED
- experiments/iter37_release_manifest_self_coverage_public_sync_guard: RESULT PUBLISHED
- experiments/iter38_release_manifest_self_coverage_public_sync_negative_guard: RESULT PUBLISHED
- experiments/iter39_public_task_protocol_effect_slice: RESULT PUBLISHED
- experiments/iter40_public_task_protocol_effect_execution: RESULT PUBLISHED
- experiments/iter41_public_task_protocol_effect_runner_recovery: RESULT PUBLISHED
- experiments/iter42_public_task_protocol_effect_execution_retry: RESULT PUBLISHED
- experiments/iter43_provider_execution_harness_recovery: RESULT PUBLISHED
- experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery: RESULT PUBLISHED
- experiments/iter45_public_task_condition_executor_assembly: RESULT PUBLISHED
- experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor: RESULT PUBLISHED
- experiments/iter47_provider_task_condition_command_binding_recovery: RESULT PUBLISHED
- experiments/iter48_provider_compatible_protocol_effect_slice_refreeze: RESULT PUBLISHED
- experiments/iter49_provider_compatible_protocol_effect_execution_retry: RESULT PUBLISHED
- experiments/iter50_provider_compatible_execution_wrapper_recovery: RESULT PUBLISHED
- experiments/iter51_provider_compatible_protocol_effect_execution_with_wrapper: RESULT PUBLISHED
- experiments/iter52_provider_condition_runtime_separation_recovery: RESULT PUBLISHED
- experiments/iter53_provider_compatible_protocol_effect_execution_after_condition_recovery: RESULT PUBLISHED
- experiments/iter54_provider_pair_executor_recovery: RESULT PUBLISHED
- experiments/iter55_provider_compatible_paid_execution_after_executor_recovery: RESULT PUBLISHED
- experiments/iter56_provider_auth_recovery_for_paid_protocol_effect: RESULT PUBLISHED
- experiments/iter57_provider_compatible_paid_execution_after_auth_recovery: RESULT PUBLISHED
- experiments/iter58_codeclash_vertex_dependency_recovery: RESULT PUBLISHED
- experiments/iter59_provider_compatible_paid_execution_after_dependency_recovery: RESULT PUBLISHED
- experiments/iter60_provider_model_binding_recovery: RESULT PUBLISHED
- experiments/iter61_vertex_quota_project_binding_recovery: RESULT PUBLISHED
- experiments/iter62_vertex_bearer_token_path_recovery: RESULT PUBLISHED
- experiments/iter63_vertex_access_path_parity_recheck: RESULT PUBLISHED
- experiments/iter64_provider_compatible_paid_execution_after_access_path_recovery: RESULT PUBLISHED
- experiments/iter65_receipt_schema_prompt_alignment: RESULT PUBLISHED
- experiments/iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment: RESULT PUBLISHED
- experiments/iter67_provider_compatible_expanded_slice_refreeze: RESULT PUBLISHED
- experiments/iter68_provider_compatible_task_surface_adapter_recovery: RESULT PUBLISHED
- experiments/iter69_codeclash_task_surface_source_snapshot_recovery: RESULT PUBLISHED
- experiments/iter70_provider_compatible_expanded_adapter_completion: RESULT PUBLISHED
- experiments/iter71_provider_compatible_expanded_slice_after_adapter_completion: RESULT PUBLISHED
- experiments/iter72_provider_compatible_expanded_paid_execution_after_slice_refreeze: RESULT PUBLISHED
- experiments/iter73_expanded_receipt_prompt_recovery_after_paid_block: RESULT PUBLISHED
- experiments/iter74_provider_compatible_expanded_paid_retry_after_receipt_prompt_recovery: RESULT PUBLISHED
- experiments/iter75_provider_compatible_runtime_adc_recovery_after_paid_retry_block: RESULT PUBLISHED
- experiments/iter76_runtime_adc_recheck_after_operator_refresh: RESULT PUBLISHED
- experiments/iter77_runtime_adc_recheck_after_application_default_login: RESULT PUBLISHED
- experiments/iter78_provider_compatible_expanded_paid_retry_after_adc_recovery: RESULT PUBLISHED
- experiments/iter79_dummy_row_call_ceiling_recovery_after_paid_retry_block: RESULT PUBLISHED
- experiments/iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery: RESULT PUBLISHED
- experiments/iter81_expanded_stratified_adapter_validation_consolidation: RESULT PUBLISHED
- experiments/iter82_benchmark_facing_protocol_effect_slice_design: RESULT PUBLISHED
- experiments/iter83_benchmark_facing_protocol_effect_execution_pilot: RESULT PUBLISHED
- experiments/iter84_benchmark_facing_null_signal_adjudication: RESULT PUBLISHED
- experiments/iter85_discriminating_task_metric_redesign: RESULT PUBLISHED
- experiments/iter86_discriminating_metric_backtest_on_committed_artifacts: RESULT PUBLISHED
- experiments/iter87_benchmark_facing_discriminating_metric_execution_pilot: RESULT PUBLISHED
- experiments/iter88_external_benchmark_readiness_adjudication_after_discriminating_pilot: RESULT PUBLISHED
- experiments/iter89_same_slice_discriminating_metric_stability_replication: RESULT PUBLISHED
- experiments/iter90_stability_replication_adjudication_after_same_slice_run: RESULT PUBLISHED
- experiments/iter91_empirical_validation_suite_design_for_completion_verification: RESULT PUBLISHED
- experiments/iter92_empirical_validation_fixture_materialization_for_completion_verification: RESULT PUBLISHED
- experiments/iter93_deterministic_strategy_execution_on_materialized_fixtures: RESULT PUBLISHED
- experiments/iter94_provider_llm_judge_execution_on_materialized_fixtures: RESULT PUBLISHED
- experiments/iter95_five_strategy_completion_verification_adjudication_after_llm_judge: artifacts only
- experiments/iter95_provider_llm_judge_prompt_budget_recovery_after_block: RESULT PUBLISHED
- experiments/iter96_provider_llm_judge_bounded_retry_after_prompt_budget_recovery: RESULT PUBLISHED
- experiments/iter97_five_strategy_completion_verification_adjudication_after_llm_judge: RESULT PUBLISHED
- experiments/iter98_external_verifier_telos_differential_suite_design_after_adjudication: RESULT PUBLISHED
- experiments/iter99_external_verifier_telos_differential_fixture_materialization_after_design: RESULT PUBLISHED

## Current Gate

- Active gate: `experiments/iter205_iter204_workflow_context_recovery/HYPOTHESIS.md`.
- Frozen upstream gate recorded by runtime-bound `CONTINUITY.md`: `experiments/iter202_natural_rate_scaled/HYPOTHESIS.md`. It is retained as
  an exact historical execution authority and is not the current recovery instruction.
- Standing detector correction: iter197 and iter201 are protocol `FAIL`, with retained exploratory
  diagnostics. Both property prompts used candidate-diff-derived locators. Iter197 additionally violated
  its visible-anchor and independent-control requirements; iter201 explicitly registered gold validation,
  so gold use there is an interpretation limit rather than another deviation. The accurate label is
  **locator-assisted, gold-validated property pipeline**. Iter196 has no confirmed property-only catch:
  `django-11211` was judge-unadjudicated. Iter201 retains judge
  catches `20/22` with `8/88` unparseable responses (`5/22` hack rows, `3/22` gold rows). Report
  gold-control flags as `3/22` observed lower, `6/22` worst-case missing upper, and `3/19` complete-case.
  The property pipeline catches `6/22`, all within the judge set; no independent property false-positive
  estimate or ensemble benefit is established. All `44` judge rows were fresh, but the judge phase lacks an
  independent pre-output Git freeze. The retained artifact contains parsed labels and nondecision markers,
  not raw response text; prompt truncation and digest-unpinned historical property containers are disclosed.
- Standing iter200 result: this is an exploratory, nonrandom, gold-localized convenience sample. Its
  deterministic builder excludes all `66` unique iter193 Phase-A/iter199 target IDs before deriving `200`
  compatible rows across `9` repositories and the ordered `39`-target cohort. Its strict two-judge-only-model
  rule and missingness summaries were adopted after the original result, and a
  pre-output freeze is not independently timestamped in Git. The corrected denominator is complete (`37`
  valid/executed, `24` certified, `k=1`, `u=6`). Report `1/24` confirmed lower, `7/24` worst case over those
  six declared missing outcomes, and `1/18` complete-case sensitivity. The historical `1/15` is
  scenario-eligible chronology only. The `54` legacy execution logs lack explicit image/exit provenance
  and are accepted only as a frozen exact-byte corpus; the `20` backfill logs have stronger provenance.
  The retained blind-judge bundle stores parsed labels and derived booleans, not raw response text; exact
  response substance and parser fidelity cannot be re-audited.
- Iter202 retained provider evidence: access authorization succeeded; no access, authentication, billing,
  quota, or credit failure occurred. The retained stages completed `53/53` solver calls and
  `39/39` eligible scenario calls, producing `50` model patches and `38` extracted scenario programs.
  There was one original absent scenario. The frozen static-safety predicate
  admitted `29` programs and rejected `9` with `21` findings.
  Zero scenario execution and zero official-harness certification execution occurred.
- Iter202 disposition: the batch stopped at its frozen safety gate. Iter202 is a scenario-safety protocol/execution null,
  not a measured rate; it contributes no `N`, `k`, or `u`. Its provider outputs
  and runtime-bound files remain byte-preserved.
- Iter203 disposition: source PR `#5` merged as
  `5c409f79c9333206cff9ed80d59c08aa347110f6`, and primary-branch CI run `29460293066` passed. The sole
  canonical dispatch was workflow run `29460393525`, attempt `1`. Authorization,
  source, bridge, runtime, image-pull, and image-digest checks passed, but all `50/50` first Docker `run`
  invocations returned exit `125` across eight runners before any in-container command. Collection was
  skipped and the artifacts API reported zero uploaded workflow artifacts. No patch was applied.
  There were zero official certifications and zero scenarios executed. Iter203 is an
  execution-infrastructure null with no `N`, `k`, or `u`.
- Iter203 evidence limit and diagnosis:
  the exact daemon stderr was redirected into temporary files and not retained.
  The root cause is reconstructed from the frozen launcher tuple and version-matched Docker
  `28.0.4` source: the `local` driver used `max-file=1` while compression remained enabled by default. This
  was not an access, authentication, billing, quota, or credit failure. The eight exact raw public job logs
  are committed and hash-bound; do not rerun, replace, or reinterpret iter203.
- Iter204 disposition: approved source `c1137f896b7ee3c9a26ee35bcda2c5f5c6b79446` passed primary CI run
  `29465925393`, attempt `1`. The server retained exactly two iter204 workflow records.
  They are push parse-failure run `29465584664` at `8342315dd2fa7ec865bd7c654ec4ec098675dfab` and
  push parse-failure run `29465924803` at the approved merge. Both are completed attempt-`1`
  failures with zero jobs and zero artifacts. They are not dispatch runs. The complete iter204 history has
  zero `workflow_dispatch` runs; it is false to say that iter204 has zero workflow runs.
- Iter204 rejected-request boundary: at least one locally observed dispatch API request returned HTTP `422`
  before run creation because the workflow parser rejected a job-level `runner.temp` expression. The request
  has no run ID, no run attempt, and no public workflow-dispatch job or run log. The exact request count is not
  publicly auditable and is not asserted.
- Iter204 scientific disposition: no provider process, container create/run invocation, patch application,
  official certification, scenario execution, adjudication, or judge process started. Iter204 is a
  pre-dispatch infrastructure null and contributes no `N`, `k`, or `u`; those quantities are absent, not zero.
  Its runtime manifest at SHA-256 `bf2062825e604d9439b0d29375d7e5219a1064ae4a33701efb74a62f81a59a45` is exact-hash historical evidence.
  Never reconstruct that frozen manifest from the current tree or use it as a current-tree manifest.
- Iter205 recovery: the active, separately identified pre-dispatch and pre-scientific-output protocol preserves
  the same `50` patches and row order, eight shards, `29` admitted witnesses, `9` rejected witnesses, one absent
  witness, images, certification and scenario rules, missingness definitions, adjudication, and judge contract.
  Its only runtime correction moves the smoke-receipt `runner.temp` binding from job-level to step-level context;
  the remaining changes are mechanical iter205 identities, additive iter204-null guards, and stronger workflow
  admission checks. This is not a retry or in-place mutation of iter204.
- Publication/readiness evidence: published iter203 source PR `#5` merged as
  `5c409f79c9333206cff9ed80d59c08aa347110f6`; primary-branch CI run `29460293066` succeeded at that merge.
  Provider-free backfill run `29452243832` succeeded at source commit
  `b4a565d0f0bb61cff460ea4faa51f58e75a2c2fe` with pinned Node 24-native action revisions. It reproduced and
  hash-verified the exact specs under Python `3.11.15` and all `73` locked distributions, then validated all
  `37` committed execution pairs in the complete `74`-log corpus with zero model-provider calls. It reused
  the committed logs and did not re-execute containers.
- Frozen protocol checkpoint: keep `CONTINUITY.md` byte-identical. Its iter202 instructions are preserved
  for provenance; the published iter203 and iter204 nulls, active iter205 hypothesis, new iter205 runtime
  manifest, and generated handoff govern the additive recovery.
- No population-frequency, model-comparison, leaderboard, deployment, or state-of-the-art result is claimed.
- Next action: review the exact iter204 pre-dispatch null and the bounded iter205 source, smoke, diagnostics,
  runtime closure, collector, adjudicator, blind-judge binding, and preserved upstream bytes; commit the
  recovery; publish it through a pull request; and require green primary-branch CI. Only from that clean,
  green primary commit may the exact server-object and complete-history preflight authorize one iter205
  dispatch request. A created first global iter205 `workflow_dispatch` run at attempt `1` is the only eligible
  execution. Any API rejection, parser record, authorization failure, smoke failure, shard failure, collector
  failure, or incomplete corpus closes iter205 and requires iter206. Never re-enter the dispatch block, never
  rerun, and never issue a second iter205 request. Never dispatch the frozen iter202, iter203, or iter204
  workflows, execute a rejected scenario, or treat missing evidence as negative.
- Autonomous goal-tracking note: if the operator explicitly asks for a persistent
  autonomous run, use the session goal tracker if available; otherwise continue
  from this handoff, the active `HYPOTHESIS.md`, and the learning ledger. Consult
  `CONTINUITY.md` only as the frozen upstream record. Do not treat a session-level "pursuing goals" state as evidence; the
  committed repo artifacts remain the source of truth.

## Exact Authorized Iter205 Dispatch

Only after the iter205 recovery pull request is merged and primary-branch CI is green, run this from the
standalone TELOS repository. This block is intentionally non-idempotent. Before its sole request it proves
the exact active server workflow object; empty complete iter205 all-event and dispatch histories; the exact
two-record iter204 parse-failure history; and the approved commit's exact green primary CI and checks. A
transient read-only query failure before the request does not consume iter205's request allowance: resolve it
and rerun the complete preflight. A confirmed substantive preflight mismatch closes iter205.
Once execution reaches the request command, never re-enter this block. A confirmed API rejection or parser record closes
iter205 and advances to iter206. If client or network state is ambiguous, assume the request may have been
accepted and use only the read-only observe block. A rejected request has no run attempt, but still consumes
iter205's sole request allowance.

```bash
set -euo pipefail
git switch master
git pull --ff-only origin master
test -z "$(git status --porcelain)"
HEAD_SHA="$(git rev-parse HEAD)"
test "$HEAD_SHA" = "$(git rev-parse origin/master)"
git merge-base --is-ancestor c1137f896b7ee3c9a26ee35bcda2c5f5c6b79446 "$HEAD_SHA"
REPO="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
test "$REPO" = "manfromnowhere143/telos"
WORKFLOW_BINDING="$(gh api -X GET "repos/$REPO/actions/workflows/iter205-execute.yml" --jq '[.name,.path,.state] | @tsv')"
test "$WORKFLOW_BINDING" = $'iter205-execute	.github/workflows/iter205-execute.yml	active'
ITER205_ALL_COUNT="$(
  gh api --paginate -X GET "repos/$REPO/actions/workflows/iter205-execute.yml/runs" \
    -f per_page=100 --jq '.workflow_runs | length' \
    | awk '{ total += $1 } END { print total + 0 }'
)"
test "$ITER205_ALL_COUNT" -eq 0
ITER205_DISPATCH_COUNT="$(
  gh api --paginate -X GET "repos/$REPO/actions/workflows/iter205-execute.yml/runs" \
    -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs | length' \
    | awk '{ total += $1 } END { print total + 0 }'
)"
test "$ITER205_DISPATCH_COUNT" -eq 0
ITER204_WORKFLOW_BINDING="$(gh api -X GET "repos/$REPO/actions/workflows/314113289" --jq '[.id,.name,.path,.state] | @tsv')"
test "$ITER204_WORKFLOW_BINDING" = $'314113289	.github/workflows/iter204-execute.yml	.github/workflows/iter204-execute.yml	active'
ITER204_HISTORY="$(
  gh api --paginate -X GET "repos/$REPO/actions/workflows/314113289/runs" \
    -f per_page=100 \
    --jq '.workflow_runs[] | [.id,.event,.status,.conclusion,.run_attempt,.head_sha] | @tsv' \
    | LC_ALL=C sort
)"
EXPECTED_ITER204_HISTORY="$(printf '%s\n' \
  $'29465584664	push	completed	failure	1	8342315dd2fa7ec865bd7c654ec4ec098675dfab' \
  $'29465924803	push	completed	failure	1	c1137f896b7ee3c9a26ee35bcda2c5f5c6b79446')"
test "$ITER204_HISTORY" = "$EXPECTED_ITER204_HISTORY"
ITER204_DISPATCH_COUNT="$(
  gh api --paginate -X GET "repos/$REPO/actions/workflows/314113289/runs" \
    -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs | length' \
    | awk '{ total += $1 } END { print total + 0 }'
)"
test "$ITER204_DISPATCH_COUNT" -eq 0
for ITER204_RUN_ID in 29465584664 29465924803; do
  test "$(gh api -X GET "repos/$REPO/actions/runs/$ITER204_RUN_ID/jobs" -f per_page=100 --jq '.total_count')" -eq 0
  test "$(gh api -X GET "repos/$REPO/actions/runs/$ITER204_RUN_ID/artifacts" -f per_page=100 --jq '.total_count')" -eq 0
done
CI_BINDING="$(
  gh api --paginate -X GET "repos/$REPO/actions/workflows/ci.yml/runs" \
    -f branch=master -f event=push -f per_page=100 \
    --jq ".workflow_runs[] | select(.head_sha == \"$HEAD_SHA\") | [.id,.status,.conclusion,.event,.head_sha,.run_attempt] | @tsv"
)"
test "$(printf '%s\n' "$CI_BINDING" | sed '/^$/d' | wc -l | tr -d ' ')" -eq 1
CI_RUN_ID="$(printf '%s\n' "$CI_BINDING" | cut -f1)"
test "$(printf '%s\n' "$CI_BINDING" | cut -f2-)" = $'completed	success	push	'"$HEAD_SHA"$'	1'
CI_JOBS="$(gh api --paginate -X GET "repos/$REPO/actions/runs/$CI_RUN_ID/jobs" -f per_page=100 --jq '.jobs[] | [.name,.status,.conclusion] | @tsv' | LC_ALL=C sort)"
test "$CI_JOBS" = "$(printf '%s\n' $'verify py3.11	completed	success' $'verify py3.12	completed	success')"
gh workflow run iter205-execute.yml --ref master -f expected_primary_sha="$HEAD_SHA"
RUN_ID=""
for observation in $(seq 1 12); do
  ITER205_ALL_COUNT="$(gh api --paginate -X GET "repos/$REPO/actions/workflows/iter205-execute.yml/runs" -f per_page=100 --jq '.workflow_runs | length' | awk '{ total += $1 } END { print total + 0 }')"
  ITER205_DISPATCH_COUNT="$(gh api --paginate -X GET "repos/$REPO/actions/workflows/iter205-execute.yml/runs" -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs | length' | awk '{ total += $1 } END { print total + 0 }')"
  test "$ITER205_ALL_COUNT" -le 1
  test "$ITER205_DISPATCH_COUNT" -le 1
  if test "$ITER205_ALL_COUNT" -eq 1 && test "$ITER205_DISPATCH_COUNT" -eq 1; then
    RUN_ID="$(gh api -X GET "repos/$REPO/actions/workflows/iter205-execute.yml/runs" -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs[0].id // empty')"
    break
  fi
  sleep 5
done
if test -z "$RUN_ID"; then
  printf 'Iter205 request was entered but canonical run discovery is incomplete; never reissue it. Use only the read-only observe block.\n' >&2
  exit 75
fi
test "$ITER205_ALL_COUNT" -eq 1
test "$ITER205_DISPATCH_COUNT" -eq 1
RUN_BINDING="$(gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '[.event,.head_sha,.run_attempt,.path] | @tsv')"
test "$RUN_BINDING" = $'workflow_dispatch	'"$HEAD_SHA"$'	1	.github/workflows/iter205-execute.yml'
printf 'Canonical iter205 RUN_ID=%s APPROVED_SHA=%s; use only the observe block below.\n' "$RUN_ID" "$HEAD_SHA"
```

If dispatch discovery or local watching is interrupted, never re-enter the dispatch block. Use this
read-only block to resolve the sole global iter205 run, bind it to the approved commit and attempt `1`, and
wait for GitHub's terminal state. A queued or in-progress run and a local network/client interruption are
not null results. A discovery poll timeout or temporarily absent run is not by itself a null; wait and rerun
only this read-only block. A confirmed parser or non-dispatch record, or a substantive invariant mismatch,
closes iter205 and requires iter206. No observation ever authorizes another request.

```bash
set -euo pipefail
test "$(git branch --show-current)" = master
git fetch origin master
test -z "$(git status --porcelain)"
REPO="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
test "$REPO" = "manfromnowhere143/telos"
WORKFLOW_BINDING="$(gh api -X GET "repos/$REPO/actions/workflows/iter205-execute.yml" --jq '[.name,.path,.state] | @tsv')"
test "$WORKFLOW_BINDING" = $'iter205-execute	.github/workflows/iter205-execute.yml	active'
ITER205_ALL_COUNT="$(gh api --paginate -X GET "repos/$REPO/actions/workflows/iter205-execute.yml/runs" -f per_page=100 --jq '.workflow_runs | length' | awk '{ total += $1 } END { print total + 0 }')"
ITER205_DISPATCH_COUNT="$(gh api --paginate -X GET "repos/$REPO/actions/workflows/iter205-execute.yml/runs" -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs | length' | awk '{ total += $1 } END { print total + 0 }')"
test "$ITER205_ALL_COUNT" -eq 1
test "$ITER205_DISPATCH_COUNT" -eq 1
RUN_ID="$(gh api -X GET "repos/$REPO/actions/workflows/iter205-execute.yml/runs" -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs[0].id // empty')"
test -n "$RUN_ID"
APPROVED_SHA="$(gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '.head_sha')"
test -n "$APPROVED_SHA"
git merge-base --is-ancestor "$APPROVED_SHA" origin/master
CI_BINDING="$(gh api --paginate -X GET "repos/$REPO/actions/workflows/ci.yml/runs" -f branch=master -f event=push -f per_page=100 --jq ".workflow_runs[] | select(.head_sha == \"$APPROVED_SHA\") | [.id,.status,.conclusion,.event,.head_sha,.run_attempt] | @tsv")"
test "$(printf '%s\n' "$CI_BINDING" | sed '/^$/d' | wc -l | tr -d ' ')" -eq 1
CI_RUN_ID="$(printf '%s\n' "$CI_BINDING" | cut -f1)"
test "$(printf '%s\n' "$CI_BINDING" | cut -f2-)" = $'completed	success	push	'"$APPROVED_SHA"$'	1'
CI_JOBS="$(gh api --paginate -X GET "repos/$REPO/actions/runs/$CI_RUN_ID/jobs" -f per_page=100 --jq '.jobs[] | [.name,.status,.conclusion] | @tsv' | LC_ALL=C sort)"
test "$CI_JOBS" = "$(printf '%s\n' $'verify py3.11	completed	success' $'verify py3.12	completed	success')"
RUN_BINDING="$(gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '[.event,.head_sha,.run_attempt,.path] | @tsv')"
test "$RUN_BINDING" = $'workflow_dispatch	'"$APPROVED_SHA"$'	1	.github/workflows/iter205-execute.yml'
gh run watch "$RUN_ID" || true
RUN_STATE="$(gh run view "$RUN_ID" --json status,conclusion --jq '[.status,(.conclusion // "")] | join(" ")')"
if test "${RUN_STATE%% *}" != completed; then
  printf 'Run %s is not terminal (%s); rerun only this read-only observe block.\n' "$RUN_ID" "$RUN_STATE" >&2
  exit 75
fi
RUN_CONCLUSION="${RUN_STATE#* }"
if test "$RUN_CONCLUSION" != success; then
  printf 'Run %s is terminal with conclusion=%s; use the failure-evidence block below.\n' "$RUN_ID" "$RUN_CONCLUSION" >&2
  exit 20
fi
printf 'Run %s completed successfully; continue to complete-artifact verification.\n' "$RUN_ID"
```

A terminal non-success conclusion seals iter205 as an infrastructure null. Do not rerun it, do not issue
another request, and do not select partial shard output. Preserve the exact created attempt-`1` workflow
record before drafting the null and advancing to iter206. A request rejected before run creation has no
downloadable run evidence and must instead be reported at that exact bounded evidence level.

```bash
set -euo pipefail
test "$(git branch --show-current)" = master
git fetch origin master
test -z "$(git status --porcelain)"
REPO="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
test "$REPO" = "manfromnowhere143/telos"
ITER205_ALL_COUNT="$(gh api --paginate -X GET "repos/$REPO/actions/workflows/iter205-execute.yml/runs" -f per_page=100 --jq '.workflow_runs | length' | awk '{ total += $1 } END { print total + 0 }')"
ITER205_DISPATCH_COUNT="$(gh api --paginate -X GET "repos/$REPO/actions/workflows/iter205-execute.yml/runs" -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs | length' | awk '{ total += $1 } END { print total + 0 }')"
test "$ITER205_ALL_COUNT" -eq 1
test "$ITER205_DISPATCH_COUNT" -eq 1
RUN_ID="$(gh api -X GET "repos/$REPO/actions/workflows/iter205-execute.yml/runs" -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs[0].id // empty')"
test -n "$RUN_ID"
APPROVED_SHA="$(gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '.head_sha')"
test -n "$APPROVED_SHA"
git merge-base --is-ancestor "$APPROVED_SHA" origin/master
test "$(gh run view "$RUN_ID" --json attempt --jq '.attempt')" -eq 1
test "$(gh run view "$RUN_ID" --json event --jq '.event')" = workflow_dispatch
test "$(gh run view "$RUN_ID" --json status --jq '.status')" = completed
RUN_CONCLUSION="$(gh run view "$RUN_ID" --json conclusion --jq '.conclusion // empty')"
test -n "$RUN_CONCLUSION"
if test "$RUN_CONCLUSION" = success; then
  printf 'Run succeeded; use success collection, not null collection.\n' >&2
  exit 2
fi
NULL_DIR="experiments/iter205_iter204_workflow_context_recovery/proof/raw/execution_null_run_${RUN_ID}_attempt_1"
test ! -e "$NULL_DIR"
RAW_DIR="$(dirname "$NULL_DIR")"
STAGE="$(mktemp -d "$RAW_DIR/.iter205-null-stage.XXXXXX")"
cleanup() { if test -n "${STAGE:-}" && test -d "$STAGE"; then rm -rf -- "$STAGE"; fi; }
trap cleanup EXIT
gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '{id,name,head_branch,head_sha,path,event,status,conclusion,run_attempt,run_started_at,updated_at,html_url}' > "$STAGE/run.json"
gh api -X GET "repos/$REPO/actions/runs/$RUN_ID/jobs" -f per_page=100 | jq -S . > "$STAGE/jobs.json"
gh api -X GET "repos/$REPO/actions/runs/$RUN_ID/artifacts" -f per_page=100 | jq -S . > "$STAGE/artifacts.json"
gh api -X GET "repos/$REPO/actions/runs/$RUN_ID/logs" > "$STAGE/workflow-logs.zip"
ARTIFACT_COUNT="$(jq -r '.total_count' "$STAGE/artifacts.json")"
if test "$ARTIFACT_COUNT" -gt 0; then
  mkdir "$STAGE/artifacts"
  gh run download "$RUN_ID" --dir "$STAGE/artifacts"
fi
(
  cd "$STAGE"
  find . -type f ! -name SHA256SUMS -exec shasum -a 256 '{}' + | LC_ALL=C sort > SHA256SUMS
)
mv "$STAGE" "$NULL_DIR"
STAGE=""
trap - EXIT
printf 'Preserved terminal iter205 null evidence at %s; publish the null and open iter206 before execution.\n' "$NULL_DIR"
```

After the sole run succeeds, re-prove its global uniqueness and attempt identity, download its complete
artifact into the previously absent execution directory, verify it, and derive adjudication before any
blind-judge call:

```bash
set -euo pipefail
test "$(git branch --show-current)" = master
git fetch origin master
test -z "$(git status --porcelain)"
REPO="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
test "$REPO" = "manfromnowhere143/telos"
ITER205_ALL_COUNT="$(
  gh api --paginate -X GET "repos/$REPO/actions/workflows/iter205-execute.yml/runs" \
    -f per_page=100 --jq '.workflow_runs | length' \
    | awk '{ total += $1 } END { print total + 0 }'
)"
ITER205_DISPATCH_COUNT="$(
  gh api --paginate -X GET "repos/$REPO/actions/workflows/iter205-execute.yml/runs" \
    -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs | length' \
    | awk '{ total += $1 } END { print total + 0 }'
)"
test "$ITER205_ALL_COUNT" -eq 1
test "$ITER205_DISPATCH_COUNT" -eq 1
RUN_ID="$(gh api -X GET "repos/$REPO/actions/workflows/iter205-execute.yml/runs" -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs[0].id // empty')"
test -n "$RUN_ID"
APPROVED_SHA="$(gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '.head_sha')"
test -n "$APPROVED_SHA"
git merge-base --is-ancestor "$APPROVED_SHA" origin/master
test "$(git rev-parse HEAD)" = "$APPROVED_SHA"
git diff --quiet "$APPROVED_SHA" -- telos scripts .github/workflows/iter205-execute.yml experiments/iter203_iter202_safety_recovery experiments/iter204_iter203_infrastructure_recovery experiments/iter205_iter204_workflow_context_recovery
python3 -I -S scripts/build_iter205_runtime_manifest.py --check
test "$(gh run view "$RUN_ID" --json status,conclusion --jq '[.status,.conclusion] | join(" ")')" = "completed success"
RUN_ATTEMPT="$(gh run view "$RUN_ID" --json attempt --jq '.attempt')"
test "$RUN_ATTEMPT" -eq 1
EXECUTION_DIR="experiments/iter205_iter204_workflow_context_recovery/proof/raw/execution"
test ! -e "$EXECUTION_DIR"
RAW_DIR="$(dirname "$EXECUTION_DIR")"
STAGE="$(mktemp -d "$RAW_DIR/.iter205-execution-stage.XXXXXX")"
cleanup() { if test -n "${STAGE:-}" && test -d "$STAGE"; then rm -rf -- "$STAGE"; fi; }
trap cleanup EXIT
gh run download "$RUN_ID" --name "iter205-execution-complete-$RUN_ID-attempt-1" --dir "$STAGE"
python3 -I -S scripts/collect_iter205_execution.py check \
  --execution-dir "$STAGE" \
  --aggregate-receipt "$STAGE/_telos_iter205_execution_complete.receipt.json" \
  --spec-index experiments/iter203_iter202_safety_recovery/proof/raw/specs/index.json \
  --runtime-manifest experiments/iter205_iter204_workflow_context_recovery/proof/raw/runtime_manifest.json
mv "$STAGE" "$EXECUTION_DIR"
STAGE=""
trap - EXIT
python3 -I -S scripts/adjudicate_iter205_workflow_context_recovery.py
python3 -I -S scripts/run_iter205_workflow_context_recovery_blind_judge.py
```

If the complete artifact was already promoted into the final execution directory but local adjudication or
the checkpointed blind judge was interrupted, never redownload or rerun the workflow. Revalidate the final
evidence in place, reproduce deterministic adjudication, and resume only the checkpoint-aware judge. If
collector validation fails or the corpus is incomplete, seal iter205 and advance to iter206; do not repair,
replace, or select partial evidence.

```bash
set -euo pipefail
test "$(git branch --show-current)" = master
git fetch origin master
git diff --quiet
git diff --cached --quiet
REPO="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
test "$REPO" = "manfromnowhere143/telos"
ITER205_ALL_COUNT="$(gh api --paginate -X GET "repos/$REPO/actions/workflows/iter205-execute.yml/runs" -f per_page=100 --jq '.workflow_runs | length' | awk '{ total += $1 } END { print total + 0 }')"
ITER205_DISPATCH_COUNT="$(gh api --paginate -X GET "repos/$REPO/actions/workflows/iter205-execute.yml/runs" -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs | length' | awk '{ total += $1 } END { print total + 0 }')"
test "$ITER205_ALL_COUNT" -eq 1
test "$ITER205_DISPATCH_COUNT" -eq 1
RUN_ID="$(gh api -X GET "repos/$REPO/actions/workflows/iter205-execute.yml/runs" -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs[0].id // empty')"
test -n "$RUN_ID"
APPROVED_SHA="$(gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '.head_sha')"
test -n "$APPROVED_SHA"
git merge-base --is-ancestor "$APPROVED_SHA" origin/master
test "$(git rev-parse HEAD)" = "$APPROVED_SHA"
git diff --quiet "$APPROVED_SHA" -- telos scripts .github/workflows/iter205-execute.yml experiments/iter203_iter202_safety_recovery experiments/iter204_iter203_infrastructure_recovery experiments/iter205_iter204_workflow_context_recovery
python3 -I -S scripts/build_iter205_runtime_manifest.py --check
test "$(gh run view "$RUN_ID" --json status,conclusion,attempt --jq '[.status,.conclusion,.attempt] | join(" ")')" = "completed success 1"
EXECUTION_DIR="experiments/iter205_iter204_workflow_context_recovery/proof/raw/execution"
test -d "$EXECUTION_DIR"
test ! -L "$EXECUTION_DIR"
python3 -I -S scripts/collect_iter205_execution.py check   --execution-dir "$EXECUTION_DIR"   --aggregate-receipt "$EXECUTION_DIR/_telos_iter205_execution_complete.receipt.json"   --spec-index experiments/iter203_iter202_safety_recovery/proof/raw/specs/index.json   --runtime-manifest experiments/iter205_iter204_workflow_context_recovery/proof/raw/runtime_manifest.json
python3 -I -S scripts/adjudicate_iter205_workflow_context_recovery.py
python3 -I -S scripts/run_iter205_workflow_context_recovery_blind_judge.py
```

## Verification Before Action

Run:

```bash
python3 -m compileall telos scripts tests
ruff check .
pytest -q
python3 scripts/validate_json.py
python3 scripts/validate_docs.py
python3 scripts/validate_current_paper.py
python3 scripts/validate_mission_loop.py
python3 scripts/validate_supply_chain.py
python3 scripts/validate_detector_methodology_correction.py
python3 scripts/validate_iter200_corrected_result.py
python3 scripts/build_iter200_solve_targets.py --check
python3 scripts/build_iter202_solve_targets.py --check
python3 scripts/audit_iter202_sample_overlap.py --check
python3 scripts/build_iter202_image_lock.py --check
python3 scripts/build_iter203_safety_recovery.py --check
python3 scripts/build_iter203_runtime_manifest.py --check
python3 scripts/validate_iter203_publication_safety.py --check
python3 scripts/validate_iter203_infrastructure_null.py
python3 scripts/validate_iter204_pre_dispatch_null.py
python3 scripts/build_iter205_runtime_manifest.py --check
python3 scripts/validate_iter205_publication_safety.py --check
python3 scripts/validate_iter205_runtime_recovery.py
python3 scripts/validate_target_survey.py
python3 scripts/validate_public_slice.py
python3 scripts/validate_agent_behavior_slice.py
python3 scripts/validate_deterministic_edit_slice.py
python3 scripts/validate_provider_model_pilot_slice.py
python3 scripts/validate_receipts.py experiments/iter01_receipt_dry_run/proof
python3 scripts/validate_receipts.py experiments/iter03_codeclash_smoke/proof
python3 scripts/audit_codeclash_smoke.py
python3 scripts/validate_receipts.py experiments/iter05_agent_behavior_smoke/proof
python3 scripts/audit_agent_behavior_smoke.py
python3 scripts/validate_receipts.py experiments/iter07_deterministic_edit_smoke/proof
python3 scripts/audit_deterministic_edit_smoke.py
python3 scripts/validate_receipts.py experiments/iter09_provider_model_pilot_smoke/proof
python3 scripts/audit_provider_model_pilot_smoke.py
python3 scripts/validate_receipts.py experiments/iter10_provider_auth_recovery/proof
python3 scripts/audit_provider_auth_recovery.py
python3 scripts/validate_receipts.py experiments/iter11_provider_model_pilot_retry/proof
python3 scripts/audit_provider_model_pilot_retry.py
python3 scripts/validate_receipts.py experiments/iter12_vertex_model_access_recovery/proof
python3 scripts/audit_vertex_model_access_recovery.py
python3 scripts/validate_receipts.py experiments/iter13_provider_model_pilot_retry_after_access_recovery/proof
python3 scripts/audit_provider_model_pilot_after_access.py
python3 scripts/validate_receipts.py experiments/iter14_provider_diff_quality_review/proof
python3 scripts/audit_provider_diff_quality_review.py
python3 scripts/validate_receipts.py experiments/iter15_provider_strict_diff_rerun/proof
python3 scripts/audit_provider_strict_diff_rerun.py
python3 scripts/validate_receipts.py experiments/iter16_provider_workspace_hygiene_control/proof
python3 scripts/audit_provider_workspace_hygiene_control.py
python3 scripts/validate_receipts.py experiments/iter17_provider_lint_hygiene_control/proof
python3 scripts/audit_provider_lint_hygiene_control.py
python3 scripts/validate_receipts.py experiments/iter18_provider_behavior_depth_control/proof
python3 scripts/audit_provider_behavior_depth_control.py
python3 scripts/validate_receipts.py experiments/iter19_provider_final_inspection_control/proof
python3 scripts/audit_provider_final_inspection_control.py
python3 scripts/validate_receipts.py experiments/iter20_behavior_semantic_verification/proof
python3 scripts/audit_behavior_semantic_verification.py
python3 scripts/validate_receipts.py experiments/iter21_opponent_collision_control/proof
python3 scripts/audit_opponent_collision_control.py
python3 scripts/validate_receipts.py experiments/iter22_semantic_mutation_guard/proof
python3 scripts/audit_semantic_mutation_guard.py
python3 scripts/validate_receipts.py experiments/iter23_tail_semantics_falsification/proof
python3 scripts/audit_tail_semantics_falsification.py
python3 scripts/validate_receipts.py experiments/iter24_tail_safety_control/proof
python3 scripts/audit_tail_safety_control.py
python3 scripts/validate_receipts.py experiments/iter25_tail_safety_mutation_guard/proof
python3 scripts/audit_tail_safety_mutation_guard.py
python3 scripts/validate_receipts.py experiments/iter26_own_tail_redundancy_mutation_guard/proof
python3 scripts/audit_own_tail_redundancy_mutation_guard.py
python3 scripts/validate_receipts.py experiments/iter27_semantic_claim_boundary_matrix/proof
python3 scripts/audit_semantic_claim_boundary_matrix.py
python3 scripts/validate_receipts.py experiments/iter28_public_claim_surface_guard/proof
python3 scripts/audit_public_claim_surface_guard.py
python3 scripts/validate_receipts.py experiments/iter29_public_claim_surface_negative_guard/proof
python3 scripts/audit_public_claim_surface_negative_guard.py
python3 scripts/validate_receipts.py experiments/iter30_boundary_matrix_schema_guard/proof
python3 scripts/audit_boundary_matrix_schema_guard.py
python3 scripts/validate_receipts.py experiments/iter31_claim_boundary_release_manifest/proof
python3 scripts/audit_claim_boundary_release_manifest.py
python3 scripts/validate_receipts.py experiments/iter32_claim_boundary_release_manifest_negative_guard/proof
python3 scripts/audit_claim_boundary_release_manifest_negative_guard.py
python3 scripts/validate_receipts.py experiments/iter33_release_manifest_public_sync_guard/proof
python3 scripts/audit_release_manifest_public_sync_guard.py
python3 scripts/validate_receipts.py experiments/iter34_release_manifest_public_sync_negative_guard/proof
python3 scripts/audit_release_manifest_public_sync_negative_guard.py
python3 scripts/validate_receipts.py experiments/iter35_release_manifest_self_coverage_guard/proof
python3 scripts/audit_release_manifest_self_coverage_guard.py
python3 scripts/validate_receipts.py experiments/iter36_release_manifest_self_coverage_negative_guard/proof
python3 scripts/audit_release_manifest_self_coverage_negative_guard.py
python3 scripts/validate_receipts.py experiments/iter37_release_manifest_self_coverage_public_sync_guard/proof
python3 scripts/audit_release_manifest_self_coverage_public_sync_guard.py
python3 scripts/validate_receipts.py experiments/iter38_release_manifest_self_coverage_public_sync_negative_guard/proof
python3 scripts/audit_release_manifest_self_coverage_public_sync_negative_guard.py
python3 scripts/validate_receipts.py experiments/iter39_public_task_protocol_effect_slice/proof
python3 scripts/audit_public_task_protocol_effect_slice.py
python3 scripts/validate_receipts.py experiments/iter40_public_task_protocol_effect_execution/proof
python3 scripts/audit_public_task_protocol_effect_execution.py
python3 scripts/validate_receipts.py experiments/iter41_public_task_protocol_effect_runner_recovery/proof
python3 scripts/audit_public_task_protocol_effect_runner_recovery.py
python3 scripts/validate_receipts.py experiments/iter42_public_task_protocol_effect_execution_retry/proof
python3 scripts/audit_public_task_protocol_effect_execution_retry.py
python3 scripts/validate_receipts.py experiments/iter43_provider_execution_harness_recovery/proof
python3 scripts/audit_provider_execution_harness_recovery.py
python3 scripts/validate_receipts.py experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/proof
python3 scripts/audit_public_task_protocol_effect_execution_after_harness_recovery.py
python3 scripts/validate_receipts.py experiments/iter45_public_task_condition_executor_assembly/proof
python3 scripts/audit_public_task_condition_executor_assembly.py
python3 scripts/validate_receipts.py experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor/proof
python3 scripts/audit_public_task_protocol_effect_execution_with_assembled_executor.py
python3 scripts/validate_receipts.py experiments/iter47_provider_task_condition_command_binding_recovery/proof
python3 scripts/audit_provider_task_condition_command_binding_recovery.py
python3 scripts/validate_receipts.py experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/proof
python3 scripts/audit_provider_compatible_protocol_effect_slice_refreeze.py
python3 scripts/validate_receipts.py experiments/iter49_provider_compatible_protocol_effect_execution_retry/proof
python3 scripts/audit_provider_compatible_protocol_effect_execution_retry.py
python3 scripts/validate_receipts.py experiments/iter50_provider_compatible_execution_wrapper_recovery/proof
python3 scripts/audit_provider_compatible_execution_wrapper_recovery.py
python3 scripts/validate_receipts.py experiments/iter51_provider_compatible_protocol_effect_execution_with_wrapper/proof
python3 scripts/audit_provider_compatible_protocol_effect_execution_with_wrapper.py
python3 scripts/validate_receipts.py experiments/iter52_provider_condition_runtime_separation_recovery/proof
python3 scripts/audit_provider_condition_runtime_separation_recovery.py
python3 scripts/validate_receipts.py experiments/iter53_provider_compatible_protocol_effect_execution_after_condition_recovery/proof
python3 scripts/audit_provider_compatible_protocol_effect_execution_after_condition_recovery.py
python3 scripts/validate_receipts.py experiments/iter54_provider_pair_executor_recovery/proof
python3 scripts/audit_provider_pair_executor_recovery.py
python3 scripts/validate_receipts.py experiments/iter55_provider_compatible_paid_execution_after_executor_recovery/proof
python3 scripts/audit_provider_compatible_paid_execution_after_executor_recovery.py
python3 scripts/validate_receipts.py experiments/iter56_provider_auth_recovery_for_paid_protocol_effect/proof
python3 scripts/audit_provider_auth_recovery_for_paid_protocol_effect.py
python3 scripts/validate_receipts.py experiments/iter57_provider_compatible_paid_execution_after_auth_recovery/proof
python3 scripts/audit_provider_compatible_paid_execution_after_auth_recovery.py
python3 scripts/validate_receipts.py experiments/iter58_codeclash_vertex_dependency_recovery/proof
python3 scripts/audit_codeclash_vertex_dependency_recovery.py
python3 scripts/validate_receipts.py experiments/iter59_provider_compatible_paid_execution_after_dependency_recovery/proof
python3 scripts/audit_provider_compatible_paid_execution_after_dependency_recovery.py
python3 scripts/validate_receipts.py experiments/iter60_provider_model_binding_recovery/proof
python3 scripts/audit_provider_model_binding_recovery.py
python3 scripts/validate_receipts.py experiments/iter61_vertex_quota_project_binding_recovery/proof
python3 scripts/audit_vertex_quota_project_binding_recovery.py
python3 scripts/validate_receipts.py experiments/iter62_vertex_bearer_token_path_recovery/proof
python3 scripts/audit_vertex_bearer_token_path_recovery.py
python3 scripts/validate_receipts.py experiments/iter63_vertex_access_path_parity_recheck/proof
python3 scripts/audit_vertex_access_path_parity_recheck.py
python3 scripts/validate_receipts.py experiments/iter64_provider_compatible_paid_execution_after_access_path_recovery/proof
python3 scripts/audit_provider_compatible_paid_execution_after_access_path_recovery.py
python3 scripts/validate_receipts.py experiments/iter65_receipt_schema_prompt_alignment/proof
python3 scripts/audit_receipt_schema_prompt_alignment.py
python3 scripts/validate_receipts.py experiments/iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment/proof
python3 scripts/audit_provider_compatible_paid_execution_after_receipt_prompt_alignment.py
python3 scripts/validate_receipts.py experiments/iter67_provider_compatible_expanded_slice_refreeze/proof
python3 scripts/audit_provider_compatible_expanded_slice_refreeze.py
python3 scripts/validate_receipts.py experiments/iter68_provider_compatible_task_surface_adapter_recovery/proof
python3 scripts/audit_provider_compatible_task_surface_adapter_recovery.py
python3 scripts/validate_receipts.py experiments/iter69_codeclash_task_surface_source_snapshot_recovery/proof
python3 scripts/audit_codeclash_task_surface_source_snapshot_recovery.py
python3 scripts/validate_receipts.py experiments/iter70_provider_compatible_expanded_adapter_completion/proof
python3 scripts/audit_provider_compatible_expanded_adapter_completion.py
python3 scripts/validate_receipts.py experiments/iter71_provider_compatible_expanded_slice_after_adapter_completion/proof
python3 scripts/audit_provider_compatible_expanded_slice_after_adapter_completion.py
python3 scripts/validate_receipts.py experiments/iter72_provider_compatible_expanded_paid_execution_after_slice_refreeze/proof
python3 scripts/audit_provider_compatible_expanded_paid_execution_after_slice_refreeze.py
python3 scripts/validate_receipts.py experiments/iter73_expanded_receipt_prompt_recovery_after_paid_block/proof
python3 scripts/audit_expanded_receipt_prompt_recovery_after_paid_block.py
python3 scripts/validate_receipts.py experiments/iter74_provider_compatible_expanded_paid_retry_after_receipt_prompt_recovery/proof
python3 scripts/audit_provider_compatible_expanded_paid_retry_after_receipt_prompt_recovery.py
python3 scripts/validate_receipts.py experiments/iter75_provider_compatible_runtime_adc_recovery_after_paid_retry_block/proof
python3 scripts/audit_provider_compatible_runtime_adc_recovery_after_paid_retry_block.py
python3 scripts/validate_receipts.py experiments/iter76_runtime_adc_recheck_after_operator_refresh/proof
python3 scripts/audit_runtime_adc_recheck_after_operator_refresh.py
python3 scripts/validate_receipts.py experiments/iter77_runtime_adc_recheck_after_application_default_login/proof
python3 scripts/audit_runtime_adc_recheck_after_application_default_login.py
python3 scripts/validate_receipts.py experiments/iter78_provider_compatible_expanded_paid_retry_after_adc_recovery/proof
python3 scripts/audit_provider_compatible_expanded_paid_retry_after_adc_recovery.py
python3 scripts/validate_receipts.py experiments/iter79_dummy_row_call_ceiling_recovery_after_paid_retry_block/proof
python3 scripts/audit_dummy_row_call_ceiling_recovery_after_paid_retry_block.py
python3 scripts/validate_receipts.py experiments/iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery/proof
python3 scripts/audit_dummy_call_ceiling_bounded_paid_retry_after_recovery.py
python3 scripts/validate_receipts.py experiments/iter81_expanded_stratified_adapter_validation_consolidation/proof
python3 scripts/audit_expanded_stratified_adapter_validation_consolidation.py
python3 scripts/validate_receipts.py experiments/iter82_benchmark_facing_protocol_effect_slice_design/proof
python3 scripts/audit_benchmark_facing_protocol_effect_slice_design.py
python3 scripts/validate_receipts.py experiments/iter83_benchmark_facing_protocol_effect_execution_pilot/proof
python3 scripts/audit_benchmark_facing_protocol_effect_execution_pilot.py
python3 scripts/validate_receipts.py experiments/iter84_benchmark_facing_null_signal_adjudication/proof
python3 scripts/audit_benchmark_facing_null_signal_adjudication.py
python3 scripts/validate_receipts.py experiments/iter85_discriminating_task_metric_redesign/proof
python3 scripts/audit_discriminating_task_metric_redesign.py
python3 scripts/validate_receipts.py experiments/iter86_discriminating_metric_backtest_on_committed_artifacts/proof
python3 scripts/audit_discriminating_metric_backtest_on_committed_artifacts.py
python3 scripts/validate_receipts.py experiments/iter87_benchmark_facing_discriminating_metric_execution_pilot/proof
python3 scripts/audit_benchmark_facing_discriminating_metric_execution_pilot.py
python3 scripts/validate_receipts.py experiments/iter88_external_benchmark_readiness_adjudication_after_discriminating_pilot/proof
python3 scripts/audit_external_benchmark_readiness_adjudication_after_discriminating_pilot.py
python3 scripts/validate_receipts.py experiments/iter89_same_slice_discriminating_metric_stability_replication/proof
python3 scripts/audit_same_slice_discriminating_metric_stability_replication.py
python3 scripts/validate_receipts.py experiments/iter90_stability_replication_adjudication_after_same_slice_run/proof
python3 scripts/audit_stability_replication_adjudication_after_same_slice_run.py
python3 scripts/validate_receipts.py experiments/iter91_empirical_validation_suite_design_for_completion_verification/proof
python3 scripts/audit_empirical_validation_suite_design_for_completion_verification.py
python3 scripts/validate_receipts.py experiments/iter92_empirical_validation_fixture_materialization_for_completion_verification/proof
python3 scripts/audit_empirical_validation_fixture_materialization_for_completion_verification.py
python3 scripts/validate_receipts.py experiments/iter93_deterministic_strategy_execution_on_materialized_fixtures/proof
python3 scripts/audit_deterministic_strategy_execution_on_materialized_fixtures.py
python3 scripts/validate_receipts.py experiments/iter94_provider_llm_judge_execution_on_materialized_fixtures/proof
python3 scripts/audit_provider_llm_judge_execution_on_materialized_fixtures.py
python3 scripts/validate_receipts.py experiments/iter95_provider_llm_judge_prompt_budget_recovery_after_block/proof
python3 scripts/audit_provider_llm_judge_prompt_budget_recovery_after_block.py
python3 scripts/validate_receipts.py experiments/iter96_provider_llm_judge_bounded_retry_after_prompt_budget_recovery/proof
python3 scripts/audit_provider_llm_judge_bounded_retry_after_prompt_budget_recovery.py
python3 scripts/validate_receipts.py experiments/iter97_five_strategy_completion_verification_adjudication_after_llm_judge/proof
python3 scripts/audit_five_strategy_completion_verification_adjudication_after_llm_judge.py
python3 scripts/validate_receipts.py experiments/iter98_external_verifier_telos_differential_suite_design_after_adjudication/proof
python3 scripts/audit_external_verifier_telos_differential_suite_design_after_adjudication.py
python3 scripts/validate_receipts.py experiments/iter99_external_verifier_telos_differential_fixture_materialization_after_design/proof
python3 scripts/audit_external_verifier_telos_differential_fixture_materialization_after_design.py
python3 scripts/validate_receipts.py experiments/iter100_deterministic_strategy_execution_on_differential_fixtures_after_materialization/proof
python3 scripts/audit_deterministic_strategy_execution_on_differential_fixtures_after_materialization.py
python3 scripts/validate_receipts.py experiments/iter101_provider_llm_judge_execution_on_differential_fixtures_after_deterministic/proof
python3 scripts/audit_provider_llm_judge_execution_on_differential_fixtures_after_deterministic.py
python3 scripts/validate_receipts.py experiments/iter102_provider_llm_judge_differential_retry_recovery_after_block/proof
python3 scripts/audit_provider_llm_judge_differential_retry_recovery_after_block.py
python3 scripts/validate_receipts.py experiments/iter103_differential_provider_llm_judge_full_retry_after_block_recovery/proof
python3 scripts/audit_differential_provider_llm_judge_full_retry_after_block_recovery.py
python3 scripts/validate_receipts.py experiments/iter104_five_strategy_differential_adjudication_after_recovered_llm_judge/proof
python3 scripts/audit_five_strategy_differential_adjudication_after_recovered_llm_judge.py
python3 scripts/validate_receipts.py experiments/iter105_external_benchmark_pilot_design_after_differential_adjudication/proof
python3 scripts/audit_external_benchmark_pilot_design_after_differential_adjudication.py
python3 scripts/validate_receipts.py experiments/iter106_external_benchmark_pilot_materialization_after_design/proof
python3 scripts/audit_external_benchmark_pilot_materialization_after_design.py
python3 scripts/validate_receipts.py experiments/iter107_external_benchmark_pilot_execution_after_materialization/proof
python3 scripts/audit_external_benchmark_pilot_execution_after_materialization.py
python3 scripts/validate_learning_ledger.py
python3 scripts/validate_json.py
python3 scripts/make_handoff.py
python3 scripts/validate_handoff.py
```
