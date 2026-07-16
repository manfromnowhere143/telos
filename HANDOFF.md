# HANDOFF - dynamic state snapshot

Generated: 2026-07-15T23:58:01Z by `scripts/make_handoff.py`. Read the Current Gate section before consulting the
runtime-bound `CONTINUITY.md` upstream record.

TELOS is a standalone repository at `/Users/danielwahnich/workspace/telos`. Run every TELOS command from this repository.

## Repository State

```text
source_branch: agent/iter203-safety-recovery
source_commit: c0b238a741f44076beacca8dc5cbdc94c5b25405
publication_target: master
```

Working tree:

```text
clean
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
- experiments/iter203_iter202_safety_recovery: HYPOTHESIS ACTIVE, result pending
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

- Active gate: `experiments/iter203_iter202_safety_recovery/HYPOTHESIS.md`.
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
- Iter202 retained provider evidence: governed credential readiness was verified without copying, naming,
  or printing secret material. The retained stages completed `53/53` solver calls and `39/39` eligible scenario calls,
  producing `50` model patches, `38` extracted scenario programs, and one original absent scenario. The frozen
  static-safety predicate admitted `29` programs and rejected `9` with `21` findings.
  Zero scenario execution and zero official-harness certification execution occurred.
- Iter202 disposition: the batch stopped at its frozen safety gate. Iter202 is a scenario-safety protocol/execution null,
  not a measured rate; it contributes no `N`, `k`, or `u`. Its provider outputs
  and runtime-bound files remain byte-preserved.
- Iter203 recovery: this is a separately identified post-provider, pre-execution protocol over sealed
  iter202 bytes. Its bridge and all-`50` certification specs are ready for source review. It certifies every
  valid patch, exposes only the `29` safety-admitted copies to scenario execution, and preserves every
  rejected or absent witness as unresolved rather than negative. It makes no result claim yet.
- Publication/readiness evidence: latest published source PR `#4` merged as
  `8b8809ed6b358d16eb08fe38f0f2edf4a284af0e`; primary-branch CI run `29454446264` succeeded at that merge.
  Provider-free backfill run `29452243832` succeeded at source commit
  `b4a565d0f0bb61cff460ea4faa51f58e75a2c2fe` with pinned Node 24-native action revisions. It reproduced and
  hash-verified the exact specs under Python `3.11.15` and all `73` locked distributions, then validated all
  `37` committed execution pairs in the complete `74`-log corpus with zero model-provider calls. It reused
  the committed logs and did not re-execute containers.
- Frozen protocol checkpoint: keep `CONTINUITY.md` byte-identical. Its iter202 instructions are preserved
  for provenance; the active iter203 hypothesis, bridge, runtime manifest, and generated handoff govern the
  additive recovery.
- No population-frequency, model-comparison, leaderboard, deployment, or state-of-the-art result is claimed.
- Next action: review the iter203 source, bridge, specs, runtime closure, and preserved iter202 evidence;
  commit the bounded recovery changes; publish them through a pull request; and require green primary-branch
  CI. Only from that clean, green primary commit may the iter203 execution workflow be dispatched.
  Never dispatch the frozen iter202 workflow, execute a rejected scenario, or treat missing evidence as negative.
- Autonomous goal-tracking note: if the operator explicitly asks for a persistent
  autonomous run, use the session goal tracker if available; otherwise continue
  from this handoff, the active `HYPOTHESIS.md`, and the learning ledger. Consult
  `CONTINUITY.md` only as the frozen upstream record. Do not treat a session-level "pursuing goals" state as evidence; the
  committed repo artifacts remain the source of truth.

## Exact Authorized Iter203 Dispatch

Only after the recovery pull request is merged and primary-branch CI is green, run this from the standalone
TELOS repository. The lookup makes session recovery idempotent: it reuses the sole canonical run for the
approved commit and dispatches only when no such run exists. A second dispatch for the same commit is forbidden.

```bash
set -euo pipefail
git switch master
git pull --ff-only origin master
test -z "$(git status --porcelain)"
HEAD_SHA="$(git rev-parse HEAD)"
test "$HEAD_SHA" = "$(git rev-parse origin/master)"
RUN_COUNT="$(gh run list --workflow iter203-execute.yml --branch master --event workflow_dispatch --commit "$HEAD_SHA" --limit 100 --json databaseId --jq 'length')"
test "$RUN_COUNT" -le 1
RUN_ID="$(gh run list --workflow iter203-execute.yml --branch master --event workflow_dispatch --commit "$HEAD_SHA" --limit 1 --json databaseId --jq '.[0].databaseId // empty')"
if test -z "$RUN_ID"; then
  gh workflow run iter203-execute.yml --ref master -f expected_primary_sha="$HEAD_SHA"
  for attempt in $(seq 1 12); do
    RUN_ID="$(gh run list --workflow iter203-execute.yml --branch master --event workflow_dispatch --commit "$HEAD_SHA" --limit 1 --json databaseId --jq '.[0].databaseId // empty')"
    test -n "$RUN_ID" && break
    sleep 5
  done
fi
test -n "$RUN_ID"
gh run watch "$RUN_ID" --exit-status
```

If that canonical run fails, do not dispatch again and do not select failed jobs. Preserve `RUN_ID` and rerun
the entire same run only:

```bash
set -euo pipefail
test "$(git branch --show-current)" = master
git pull --ff-only origin master
test -z "$(git status --porcelain)"
HEAD_SHA="$(git rev-parse HEAD)"
test "$HEAD_SHA" = "$(git rev-parse origin/master)"
RUN_COUNT="$(gh run list --workflow iter203-execute.yml --branch master --event workflow_dispatch --commit "$HEAD_SHA" --limit 100 --json databaseId --jq 'length')"
test "$RUN_COUNT" -eq 1
RUN_ID="$(gh run list --workflow iter203-execute.yml --branch master --event workflow_dispatch --commit "$HEAD_SHA" --limit 1 --json databaseId --jq '.[0].databaseId')"
gh run rerun "$RUN_ID"
gh run watch "$RUN_ID" --exit-status
```

After the canonical run succeeds, download its complete same-attempt artifact directly into the previously
absent execution directory, verify it, and derive adjudication before making any blind-judge call:

```bash
set -euo pipefail
test "$(git branch --show-current)" = master
git pull --ff-only origin master
test -z "$(git status --porcelain)"
HEAD_SHA="$(git rev-parse HEAD)"
test "$HEAD_SHA" = "$(git rev-parse origin/master)"
RUN_COUNT="$(gh run list --workflow iter203-execute.yml --branch master --event workflow_dispatch --commit "$HEAD_SHA" --limit 100 --json databaseId --jq 'length')"
test "$RUN_COUNT" -eq 1
RUN_ID="$(gh run list --workflow iter203-execute.yml --branch master --event workflow_dispatch --commit "$HEAD_SHA" --limit 1 --json databaseId --jq '.[0].databaseId')"
test "$(gh run view "$RUN_ID" --json status,conclusion --jq '[.status,.conclusion] | join(" ")')" = "completed success"
RUN_ATTEMPT="$(gh run view "$RUN_ID" --json attempt --jq '.attempt')"
EXECUTION_DIR="experiments/iter203_iter202_safety_recovery/proof/raw/execution"
if test ! -e "$EXECUTION_DIR"; then
  gh run download "$RUN_ID" --name "iter203-execution-complete-$RUN_ID-attempt-$RUN_ATTEMPT" --dir "$EXECUTION_DIR"
fi
test -d "$EXECUTION_DIR"
python3 -I -S scripts/collect_iter203_execution.py check \
  --execution-dir "$EXECUTION_DIR" \
  --aggregate-receipt "$EXECUTION_DIR/_telos_iter203_execution_complete.receipt.json" \
  --spec-index experiments/iter203_iter202_safety_recovery/proof/raw/specs/index.json \
  --runtime-manifest experiments/iter203_iter202_safety_recovery/proof/raw/runtime_manifest.json
python3 -I -S scripts/adjudicate_iter203_safety_recovery.py
python3 -I -S scripts/run_iter203_safety_recovery_blind_judge.py
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
