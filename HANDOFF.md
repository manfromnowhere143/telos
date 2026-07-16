# HANDOFF - dynamic state snapshot

Generated: 2026-07-16T05:04:53Z by `scripts/make_handoff.py`. Read the Current Gate section first.

TELOS is a standalone repository. Resolve its root with `git rev-parse --show-toplevel`, then run every TELOS command from that root.

## Repository State

```text
source_branch: agent/iter206-iter205-admission-recovery
source_commit: e7c2ec28daa746dbcfb5812d3771ab981ff984c0
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
- experiments/iter203_iter202_safety_recovery: RESULT PUBLISHED
- experiments/iter204_iter203_infrastructure_recovery: RESULT PUBLISHED
- experiments/iter205_iter204_workflow_context_recovery: RESULT PUBLISHED
- experiments/iter206_iter205_admission_history_recovery: HYPOTHESIS ACTIVE, result pending
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
- experiments/iter95_provider_llm_judge_prompt_budget_recovery_after_block: RESULT PUBLISHED
- experiments/iter96_provider_llm_judge_bounded_retry_after_prompt_budget_recovery: RESULT PUBLISHED
- experiments/iter97_five_strategy_completion_verification_adjudication_after_llm_judge: RESULT PUBLISHED
- experiments/iter98_external_verifier_telos_differential_suite_design_after_adjudication: RESULT PUBLISHED
- experiments/iter99_external_verifier_telos_differential_fixture_materialization_after_design: RESULT PUBLISHED

## Current Gate

- Active gate: `experiments/iter206_iter205_admission_history_recovery/HYPOTHESIS.md`.
- Frozen upstream gate recorded by runtime-bound `CONTINUITY.md`: `experiments/iter202_natural_rate_scaled/HYPOTHESIS.md`. It remains an
  immutable historical authority; it is not the current execution instruction.
- Iter202 stopped at its static-safety boundary after producing the fixed provider corpus. No scenario or
  official-harness execution occurred, so it is a safety-protocol null with no `N`, `k`, or `u`.
- Iter203's sole canonical workflow run `29460393525`, attempt `1`, failed at
  the first container invocation on every row. It is a sealed execution-infrastructure null; never rerun it.
- The frozen iter204 public-null artifact is a **two-row closure snapshot** containing parse-failure runs
  `29465584664` and `29465924803`. That artifact remains exact
  historical evidence and must not be rewritten merely because the server's append-only history grew.
- At the later iter205 admission gate, the live iter204 history was a **four-row iter205 admission baseline**.
  Rows `1..2` were the frozen closure rows; rows `3..4` were publication parse failures
  `29468669956` and `29468768706`. All four were attempt-`1` push
  failures at the invalid iter204 workflow path with zero jobs, zero artifacts, unavailable logs reported as
  HTTP `404`, and zero iter204 `workflow_dispatch` runs.
- Iter205 source PR `#7` merged as `4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f`; primary CI run
  `29468769187`, attempt `1`, completed successfully. Workflow object
  `314141096` is active at exact name/path `iter205-execute` /
  `.github/workflows/iter205-execute.yml`, with zero all-event runs and zero dispatch runs.
- Iter205 is a **pre-dispatch admission-history null**: its read-only gate expected two iter204 rows and found
  four. No iter205 dispatch request was issued, and no dispatch API response or rejection exists. No iter205
  workflow run or downstream scientific process occurred,
  and iter205 contributes no `N`, `k`, or `u`; those quantities are absent, not zero. Preserve its terminal
  receipt, public metadata manifest `6d2216038c7e1f19337795be806bf77eb39150a9be119828bc2967ed160c72ba`, learning record, and frozen source.
- No credential, credit, billing, quota, or authentication deficit is the iter205/iter206 blocker; do not
  reinterpret the admission-history null as one.
- Iter206 is the active, separately versioned pre-publication/pre-dispatch recovery. Scientific inputs and
  semantics remain frozen: `50` patches in the same order, eight shards, `29` admitted witnesses, `9`
  rejected witnesses with `21` findings, one absent witness, and unchanged certification, scenario,
  missingness, adjudication, and blind-judge rules.
- The corrected iter200 convenience sample remains exploratory and nonrandom, with `N=24`, `k=1`, and `u=6`.
  Report its descriptive sensitivities together as `1/24` confirmed lower, `7/24` worst-case missing upper,
  and `1/18` complete-case; the historical `1/15` is scenario-eligible chronology only.
- The detector correction remains binding: iter197 and iter201 are protocol `FAIL`; the property instrument
  is a locator-assisted, gold-validated property pipeline, not an independently gold-free detector. Iter201
  retains judge catches `20/22`, `8/88` response nondecisions, paired-gold sensitivities `3/22` observed
  lower, `6/22` missing upper, and `3/19` complete-case; property catches are `6/22`, all within the judge set.
- Current local guards are `scripts/validate_iter205_pre_dispatch_null.py`,
  `scripts/build_iter206_runtime_manifest.py`, `scripts/validate_iter206_publication_safety.py`, and
  `scripts/validate_iter206_runtime_recovery.py`. The execution path is bound to
  `scripts/collect_iter206_execution.py`, `scripts/adjudicate_iter206_admission_history_recovery.py`, and
  `scripts/run_iter206_admission_history_recovery_blind_judge.py`.
- Never dispatch or operationally re-enter iter202, iter203, iter204, or iter205. Never issue a workflow
  rerun. Missing infrastructure evidence is never a negative scientific outcome.
- No population-frequency, model-comparison, leaderboard, deployment, or state-of-the-art claim is authorized.

## Iter206 Local Seal and Exact Pickup Boundary

Before any remote action, complete one exact two-commit local seal. First finish and validate every mutable
source, test, documentation, and evidence byte, then create source commit A without `HANDOFF.md` or the two
not-yet-generated iter206 derived records. With only `HANDOFF.md` dirty, generate it exactly once from A.
Never regenerate it after that point. Generate the publication-safety receipt and then the runtime manifest,
validate the sealed bytes without invoking the handoff generator, and create seal commit B containing exactly
`HANDOFF.md` plus those two derived records. Require a clean tree, then push A and B together in the single
allowed branch publication.

A new session must inspect the local history and guards before acting. If clean seal commit B exists and both
derived records reproduce, the exact pickup boundary is the one-push publication envelope below; do not
regenerate any seal byte. If B is absent or incomplete, finish the local seal without remote or provider action.

## Iter206 One-Push Publication Envelope

Finalize and adversarially review every iter206 source, test, documentation, runtime, and handoff byte
locally before publication. Push branch `agent/iter206-iter205-admission-recovery` exactly once at its final tip. Make no later
source push, update-branch action, rebase, force-push, or remote branch mutation. The branch and pull-request
CI pair must pass at attempt `1`; a failure requiring changed bytes closes iter206 rather than authorizing a
second push.

Merge exactly once with a two-parent merge commit—never squash or rebase. The merge's first parent must be
`4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f`, and its second parent must be the single final release-branch tip. The resulting
master commit must pass one exact attempt-`1` primary `ci.yml` push run with both required verification jobs.
Only then may the read-only exact-six preflight below be considered. A missing, malformed, or seventh iter204
row; any iter205 run; nonempty pre-dispatch iter206 history; wrong merge parent; extra publication event; or
source change closes iter206 before dispatch.

## Exact Authorized Iter206 Dispatch

Run this block once only after the one-push, one-merge envelope and green primary CI are complete. Before its
sole state-changing line, it proves the exact repository and merge, local guards, active workflow objects,
empty iter205 and iter206 histories, the exact six-row iter204 admission snapshot, zero jobs/artifacts and
HTTP-`404` logs for all six parser records, zero iter204 dispatches, exactly one successful release-branch
`push` CI run and one successful release-branch `pull_request` CI run with their exact jobs, and exact primary
CI jobs. Read-only
transport failure before the dispatch request may be resolved by restarting the full preflight. A confirmed
invariant mismatch closes iter206. Once execution reaches the dispatch request line, never re-enter this block.

```bash
set -euo pipefail
test "$(git branch --show-current)" = master
git fetch origin master
test -z "$(git status --porcelain)"
HEAD_SHA="$(git rev-parse HEAD)"
test "$HEAD_SHA" = "$(git rev-parse origin/master)"
[[ "$HEAD_SHA" =~ ^[0-9a-f]{40}$ ]]
test "$(git rev-list --parents -n 1 "$HEAD_SHA" | wc -w | tr -d ' ')" = 3
FIRST_PARENT="$(git rev-parse "$HEAD_SHA^1")"
SECOND_PARENT="$(git rev-parse "$HEAD_SHA^2")"
test "$FIRST_PARENT" = "4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f"
REPO="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
test "$REPO" = "manfromnowhere143/telos"
python3 -I -S scripts/validate_iter205_pre_dispatch_null.py
python3 -I -S scripts/build_iter206_runtime_manifest.py --check
python3 -I -S scripts/validate_iter206_publication_safety.py --check
python3 -I -S scripts/validate_iter206_runtime_recovery.py

ITER206_WORKFLOW_BINDING="$(gh api -X GET "repos/$REPO/actions/workflows/iter206-execute.yml" --jq '[.id,.name,.path,.state] | @tsv')"
ITER206_WORKFLOW_ID="$(printf '%s\n' "$ITER206_WORKFLOW_BINDING" | cut -f1)"
[[ "$ITER206_WORKFLOW_ID" =~ ^[1-9][0-9]*$ ]]
test "$ITER206_WORKFLOW_BINDING" = "$ITER206_WORKFLOW_ID"$'	iter206-execute	.github/workflows/iter206-execute.yml	active'
ITER206_ALL_COUNT="$(gh api --paginate -X GET "repos/$REPO/actions/workflows/$ITER206_WORKFLOW_ID/runs" -f per_page=100 --jq '.workflow_runs | length' | awk '{ total += $1 } END { print total + 0 }')"
ITER206_DISPATCH_COUNT="$(gh api --paginate -X GET "repos/$REPO/actions/workflows/$ITER206_WORKFLOW_ID/runs" -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs | length' | awk '{ total += $1 } END { print total + 0 }')"
test "$ITER206_ALL_COUNT" -eq 0
test "$ITER206_DISPATCH_COUNT" -eq 0

ITER205_WORKFLOW_BINDING="$(gh api -X GET "repos/$REPO/actions/workflows/314141096" --jq '[.id,.name,.path,.state] | @tsv')"
test "$ITER205_WORKFLOW_BINDING" = $'314141096	iter205-execute	.github/workflows/iter205-execute.yml	active'
ITER205_ALL_COUNT="$(gh api --paginate -X GET "repos/$REPO/actions/workflows/314141096/runs" -f per_page=100 --jq '.workflow_runs | length' | awk '{ total += $1 } END { print total + 0 }')"
ITER205_DISPATCH_COUNT="$(gh api --paginate -X GET "repos/$REPO/actions/workflows/314141096/runs" -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs | length' | awk '{ total += $1 } END { print total + 0 }')"
test "$ITER205_ALL_COUNT" -eq 0
test "$ITER205_DISPATCH_COUNT" -eq 0

ITER204_WORKFLOW_BINDING="$(gh api -X GET "repos/$REPO/actions/workflows/314113289" --jq '[.id,.name,.path,.state] | @tsv')"
test "$ITER204_WORKFLOW_BINDING" = $'314113289	.github/workflows/iter204-execute.yml	.github/workflows/iter204-execute.yml	active'
ITER204_HISTORY="$(
  gh api --paginate -X GET "repos/$REPO/actions/workflows/314113289/runs" -f per_page=100 \
    --jq '.workflow_runs[] | [.run_number,.id,.workflow_id,.name,.path,.event,.status,.conclusion,.run_attempt,.head_branch,.head_sha,(.pull_requests | length),.head_repository.full_name] | @tsv' \
    | LC_ALL=C sort -n -k1,1
)"
test "$(printf '%s\n' "$ITER204_HISTORY" | sed '/^$/d' | wc -l | tr -d ' ')" -eq 6
ITER204_RELEASE_RUN_ID="$(printf '%s\n' "$ITER204_HISTORY" | awk -F '	' '$1 == 5 { print $2 }')"
ITER204_PRIMARY_RUN_ID="$(printf '%s\n' "$ITER204_HISTORY" | awk -F '	' '$1 == 6 { print $2 }')"
[[ "$ITER204_RELEASE_RUN_ID" =~ ^[1-9][0-9]*$ ]]
[[ "$ITER204_PRIMARY_RUN_ID" =~ ^[1-9][0-9]*$ ]]
test "$ITER204_RELEASE_RUN_ID" != "$ITER204_PRIMARY_RUN_ID"
EXPECTED_ITER204_HISTORY="$(printf '%s\n' \
  $'1	29465584664	314113289	.github/workflows/iter204-execute.yml	.github/workflows/iter204-execute.yml	push	completed	failure	1	agent/iter204-infrastructure-recovery	8342315dd2fa7ec865bd7c654ec4ec098675dfab	0	manfromnowhere143/telos' \
  $'2	29465924803	314113289	.github/workflows/iter204-execute.yml	.github/workflows/iter204-execute.yml	push	completed	failure	1	master	c1137f896b7ee3c9a26ee35bcda2c5f5c6b79446	0	manfromnowhere143/telos' \
  $'3	29468669956	314113289	.github/workflows/iter204-execute.yml	.github/workflows/iter204-execute.yml	push	completed	failure	1	agent/iter205-workflow-context-recovery	a336b4909329d392f6db5f6098792e07a17f28cb	0	manfromnowhere143/telos' \
  $'4	29468768706	314113289	.github/workflows/iter204-execute.yml	.github/workflows/iter204-execute.yml	push	completed	failure	1	master	4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f	0	manfromnowhere143/telos' \
  $'5	'"$ITER204_RELEASE_RUN_ID"$'	314113289	.github/workflows/iter204-execute.yml	.github/workflows/iter204-execute.yml	push	completed	failure	1	agent/iter206-iter205-admission-recovery	'"$SECOND_PARENT"$'	0	manfromnowhere143/telos' \
  $'6	'"$ITER204_PRIMARY_RUN_ID"$'	314113289	.github/workflows/iter204-execute.yml	.github/workflows/iter204-execute.yml	push	completed	failure	1	master	'"$HEAD_SHA"$'	0	manfromnowhere143/telos')"
test "$ITER204_HISTORY" = "$EXPECTED_ITER204_HISTORY"
ITER204_DISPATCH_COUNT="$(gh api --paginate -X GET "repos/$REPO/actions/workflows/314113289/runs" -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs | length' | awk '{ total += $1 } END { print total + 0 }')"
test "$ITER204_DISPATCH_COUNT" -eq 0
for ITER204_RUN_ID in 29465584664 29465924803 29468669956 29468768706 "$ITER204_RELEASE_RUN_ID" "$ITER204_PRIMARY_RUN_ID"; do
  test "$(gh api -X GET "repos/$REPO/actions/runs/$ITER204_RUN_ID/attempts/1/jobs" -f per_page=100 --jq '[.total_count,(.jobs | length)] | @tsv')" = $'0	0'
  test "$(gh api -X GET "repos/$REPO/actions/runs/$ITER204_RUN_ID/artifacts" -f per_page=100 --jq '[.total_count,(.artifacts | length)] | @tsv')" = $'0	0'
  set +e
  LOG_DIAGNOSTIC="$(gh api -X GET "repos/$REPO/actions/runs/$ITER204_RUN_ID/logs" 2>&1)"
  LOG_STATUS=$?
  set -e
  test "$LOG_STATUS" -ne 0
  printf '%s\n' "$LOG_DIAGNOSTIC" | grep -F 'Not Found' >/dev/null
  printf '%s\n' "$LOG_DIAGNOSTIC" | grep -E 'HTTP[^0-9]*404' >/dev/null
done

verify_release_ci() {
  local event="$1"
  local run_payload binding run_id jobs_payload job_rows job_summary job_ids
  run_payload="$(gh api -X GET "repos/$REPO/actions/workflows/ci.yml/runs" -f event="$event" -f head_sha="$SECOND_PARENT" -f page=1 -f per_page=100)"
  test "$(jq -r '[.total_count, (.workflow_runs | length)] | @tsv' <<< "$run_payload")" = $'1	1'
  test "$(jq -r '.workflow_runs | type' <<< "$run_payload")" = array
  test "$(jq -r '[.workflow_runs[] | type] | all(. == "object")' <<< "$run_payload")" = true
  binding="$(jq -r '.workflow_runs[] | [.id,.conclusion,.event,.head_branch,.head_sha,.path,.run_attempt,.status,.head_repository.full_name] | @tsv' <<< "$run_payload")"
  run_id="$(printf '%s\n' "$binding" | cut -f1)"
  [[ "$run_id" =~ ^[1-9][0-9]*$ ]]
  test "$(printf '%s\n' "$binding" | cut -f2-)" = $'success	'"$event"$'	agent/iter206-iter205-admission-recovery	'"$SECOND_PARENT"$'	.github/workflows/ci.yml	1	completed	manfromnowhere143/telos'
  jobs_payload="$(gh api -X GET "repos/$REPO/actions/runs/$run_id/attempts/1/jobs" -f page=1 -f per_page=100)"
  test "$(jq -r '[.total_count, (.jobs | length)] | @tsv' <<< "$jobs_payload")" = $'2	2'
  test "$(jq -r '.jobs | type' <<< "$jobs_payload")" = array
  test "$(jq -r '[.jobs[] | type] | all(. == "object")' <<< "$jobs_payload")" = true
  job_rows="$(jq -r '.jobs[] | [.name,.conclusion,.head_sha,.id,.run_attempt,.status,.html_url] | @tsv' <<< "$jobs_payload" | LC_ALL=C sort)"
  job_summary="$(printf '%s\n' "$job_rows" | cut -f1-3,5-6)"
  test "$job_summary" = "$(printf '%s\n' \
    $'verify py3.11	success	'"$SECOND_PARENT"$'	1	completed' \
    $'verify py3.12	success	'"$SECOND_PARENT"$'	1	completed')"
  job_ids="$(printf '%s\n' "$job_rows" | cut -f4)"
  test "$(printf '%s\n' "$job_ids" | LC_ALL=C sort -u | wc -l | tr -d ' ')" -eq 2
  while IFS= read -r job_id; do [[ "$job_id" =~ ^[1-9][0-9]*$ ]]; done <<< "$job_ids"
  while IFS=$'	' read -r _ _ _ job_id _ _ html_url; do
    test "$html_url" = "https://github.com/$REPO/actions/runs/$run_id/job/$job_id"
  done <<< "$job_rows"
  printf '%s\n' "$run_id"
}
RELEASE_PUSH_CI_RUN_ID="$(verify_release_ci push)"
RELEASE_PULL_REQUEST_CI_RUN_ID="$(verify_release_ci pull_request)"
test "$RELEASE_PUSH_CI_RUN_ID" != "$RELEASE_PULL_REQUEST_CI_RUN_ID"

CI_RUNS_PAYLOAD="$(gh api -X GET "repos/$REPO/actions/workflows/ci.yml/runs" -f branch=master -f event=push -f head_sha="$HEAD_SHA" -f page=1 -f per_page=100)"
test "$(jq -r '[.total_count, (.workflow_runs | length)] | @tsv' <<< "$CI_RUNS_PAYLOAD")" = $'1	1'
test "$(jq -r '.workflow_runs | type' <<< "$CI_RUNS_PAYLOAD")" = array
test "$(jq -r '[.workflow_runs[] | type] | all(. == "object")' <<< "$CI_RUNS_PAYLOAD")" = true
CI_BINDING="$(jq -r '.workflow_runs[] | [.id,.status,.conclusion,.event,.head_branch,.head_sha,.run_attempt,.path] | @tsv' <<< "$CI_RUNS_PAYLOAD")"
CI_RUN_ID="$(printf '%s\n' "$CI_BINDING" | cut -f1)"
[[ "$CI_RUN_ID" =~ ^[1-9][0-9]*$ ]]
test "$(printf '%s\n' "$CI_BINDING" | cut -f2-)" = $'completed	success	push	master	'"$HEAD_SHA"$'	1	.github/workflows/ci.yml'
PRIMARY_CHECK_ROWS=""
PRIMARY_CHECK_HISTORY_COMPLETE=0
for page in $(seq 1 10); do
  CHECKS_PAYLOAD="$(gh api -X GET "repos/$REPO/commits/$HEAD_SHA/check-runs" -f filter=all -f page="$page" -f per_page=100)"
  test "$(jq -r '.check_runs | type' <<< "$CHECKS_PAYLOAD")" = array
  test "$(jq -r '[.check_runs[] | type] | all(. == "object")' <<< "$CHECKS_PAYLOAD")" = true
  CHECK_PAGE_ROWS="$(jq -r '.check_runs[] | [.name,.status,.conclusion,.app.slug,.id,.details_url,(.id | type),(.app | type)] | @tsv' <<< "$CHECKS_PAYLOAD")"
  if test -n "$CHECK_PAGE_ROWS"; then
    PRIMARY_CHECK_ROWS="${PRIMARY_CHECK_ROWS}${PRIMARY_CHECK_ROWS:+$'\n'}${CHECK_PAGE_ROWS}"
  fi
  CHECK_PAGE_COUNT="$(jq -r '.check_runs | length' <<< "$CHECKS_PAYLOAD")"
  if test "$CHECK_PAGE_COUNT" -lt 100; then
    PRIMARY_CHECK_HISTORY_COMPLETE=1
    break
  fi
done
test "$PRIMARY_CHECK_HISTORY_COMPLETE" -eq 1

verify_primary_check() {
  local name="$1"
  local candidates check_id expected_prefix
  expected_prefix="https://github.com/$REPO/actions/runs/$CI_RUN_ID/job/"
  candidates="$(printf '%s\n' "$PRIMARY_CHECK_ROWS" | awk -F '	' -v name="$name" -v prefix="$expected_prefix" '$1 == name && $2 == "completed" && $3 == "success" && $4 == "github-actions" && $7 == "number" && $8 == "object" && $6 == prefix $5 { print }')"
  test "$(printf '%s\n' "$candidates" | sed '/^$/d' | wc -l | tr -d ' ')" -eq 1
  check_id="$(printf '%s\n' "$candidates" | cut -f5)"
  [[ "$check_id" =~ ^[1-9][0-9]*$ ]]
  printf '%s\n' "$check_id"
}
PRIMARY_PY311_CHECK_ID="$(verify_primary_check 'verify py3.11')"
PRIMARY_PY312_CHECK_ID="$(verify_primary_check 'verify py3.12')"
test "$PRIMARY_PY311_CHECK_ID" != "$PRIMARY_PY312_CHECK_ID"

gh workflow run iter206-execute.yml --ref master \
  -f expected_primary_sha="$HEAD_SHA" \
  -f expected_workflow_id="$ITER206_WORKFLOW_ID" \
  -f expected_iter204_release_run_id="$ITER204_RELEASE_RUN_ID" \
  -f expected_iter204_primary_run_id="$ITER204_PRIMARY_RUN_ID"
RUN_ID=""
for observation in $(seq 1 12); do
  ITER206_ALL_COUNT="$(gh api --paginate -X GET "repos/$REPO/actions/workflows/$ITER206_WORKFLOW_ID/runs" -f per_page=100 --jq '.workflow_runs | length' | awk '{ total += $1 } END { print total + 0 }')"
  ITER206_DISPATCH_COUNT="$(gh api --paginate -X GET "repos/$REPO/actions/workflows/$ITER206_WORKFLOW_ID/runs" -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs | length' | awk '{ total += $1 } END { print total + 0 }')"
  test "$ITER206_ALL_COUNT" -le 1
  test "$ITER206_DISPATCH_COUNT" -le 1
  if test "$ITER206_ALL_COUNT" -eq 1 && test "$ITER206_DISPATCH_COUNT" -eq 1; then
    RUN_ID="$(gh api -X GET "repos/$REPO/actions/workflows/$ITER206_WORKFLOW_ID/runs" -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs[0].id // empty')"
    break
  fi
  sleep 5
done
if test -z "$RUN_ID"; then
  printf 'Iter206 dispatch request was entered but run discovery is incomplete; never reissue it. Use observation only.\n' >&2
  exit 75
fi
RUN_BINDING="$(gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '[.id,.workflow_id,.name,.event,.head_branch,.head_sha,.path,.run_number,.run_attempt] | @tsv')"
test "$RUN_BINDING" = "$RUN_ID"$'	'"$ITER206_WORKFLOW_ID"$'	iter206-execute	workflow_dispatch	master	'"$HEAD_SHA"$'	.github/workflows/iter206-execute.yml	1	1'
printf 'Canonical iter206 RUN_ID=%s APPROVED_SHA=%s; use only the observation block below.\n' "$RUN_ID" "$HEAD_SHA"
```

The dispatch-request allowance is consumed when the command is entered, including dispatch API rejection or
ambiguous client state. Never issue a second dispatch request, rerun, or replacement run. A temporarily absent, queued, or in-progress
run is not itself a null. If discovery or watching is interrupted, use only this read-only observation block.
No observation ever authorizes another dispatch request.

```bash
set -euo pipefail
test "$(git branch --show-current)" = master
git fetch origin master
test -z "$(git status --porcelain)"
REPO="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
test "$REPO" = "manfromnowhere143/telos"
ITER206_WORKFLOW_BINDING="$(gh api -X GET "repos/$REPO/actions/workflows/iter206-execute.yml" --jq '[.id,.name,.path,.state] | @tsv')"
ITER206_WORKFLOW_ID="$(printf '%s\n' "$ITER206_WORKFLOW_BINDING" | cut -f1)"
[[ "$ITER206_WORKFLOW_ID" =~ ^[1-9][0-9]*$ ]]
test "$ITER206_WORKFLOW_BINDING" = "$ITER206_WORKFLOW_ID"$'	iter206-execute	.github/workflows/iter206-execute.yml	active'
ITER206_ALL_COUNT="$(gh api --paginate -X GET "repos/$REPO/actions/workflows/$ITER206_WORKFLOW_ID/runs" -f per_page=100 --jq '.workflow_runs | length' | awk '{ total += $1 } END { print total + 0 }')"
ITER206_DISPATCH_COUNT="$(gh api --paginate -X GET "repos/$REPO/actions/workflows/$ITER206_WORKFLOW_ID/runs" -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs | length' | awk '{ total += $1 } END { print total + 0 }')"
test "$ITER206_ALL_COUNT" -eq 1
test "$ITER206_DISPATCH_COUNT" -eq 1
RUN_ID="$(gh api -X GET "repos/$REPO/actions/workflows/$ITER206_WORKFLOW_ID/runs" -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs[0].id // empty')"
test -n "$RUN_ID"
APPROVED_SHA="$(gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '.head_sha')"
RUN_BINDING="$(gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '[.id,.workflow_id,.name,.event,.head_branch,.head_sha,.path,.run_number,.run_attempt] | @tsv')"
test "$RUN_BINDING" = "$RUN_ID"$'	'"$ITER206_WORKFLOW_ID"$'	iter206-execute	workflow_dispatch	master	'"$APPROVED_SHA"$'	.github/workflows/iter206-execute.yml	1	1'
git merge-base --is-ancestor "$APPROVED_SHA" origin/master
gh run watch "$RUN_ID" || true
RUN_STATE="$(gh run view "$RUN_ID" --json status,conclusion --jq '[.status,(.conclusion // "")] | join(" ")')"
if test "${RUN_STATE%% *}" != completed; then
  printf 'Run %s is not terminal (%s); repeat only this read-only observation block.\n' "$RUN_ID" "$RUN_STATE" >&2
  exit 75
fi
RUN_CONCLUSION="${RUN_STATE#* }"
if test "$RUN_CONCLUSION" != success; then
  printf 'Run %s is terminal with conclusion=%s; preserve bounded failure evidence and close iter206.\n' "$RUN_ID" "$RUN_CONCLUSION" >&2
  exit 20
fi
printf 'Run %s completed successfully; continue to exact complete-artifact verification.\n' "$RUN_ID"
```

A terminal non-success run, authorization failure, smoke failure, shard failure, collector failure, parser
record, incomplete corpus, or extra run closes iter206 without retry. Preserve evidence at the exact available
boundary; never select partial artifacts or reinterpret infrastructure as science.

```bash
set -euo pipefail
test "$(git branch --show-current)" = master
git fetch origin master
test -z "$(git status --porcelain)"
REPO="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
test "$REPO" = "manfromnowhere143/telos"
ITER206_WORKFLOW_ID="$(gh api -X GET "repos/$REPO/actions/workflows/iter206-execute.yml" --jq '.id')"
test "$(gh api --paginate -X GET "repos/$REPO/actions/workflows/$ITER206_WORKFLOW_ID/runs" -f per_page=100 --jq '.workflow_runs | length' | awk '{ total += $1 } END { print total + 0 }')" -eq 1
test "$(gh api --paginate -X GET "repos/$REPO/actions/workflows/$ITER206_WORKFLOW_ID/runs" -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs | length' | awk '{ total += $1 } END { print total + 0 }')" -eq 1
RUN_ID="$(gh api -X GET "repos/$REPO/actions/workflows/$ITER206_WORKFLOW_ID/runs" -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs[0].id // empty')"
test "$(gh run view "$RUN_ID" --json attempt,status --jq '[.attempt,.status] | @tsv')" = $'1	completed'
RUN_CONCLUSION="$(gh run view "$RUN_ID" --json conclusion --jq '.conclusion // empty')"
test -n "$RUN_CONCLUSION"
if test "$RUN_CONCLUSION" = success; then
  printf 'Run succeeded; use complete-artifact collection instead of null collection.\n' >&2
  exit 2
fi
NULL_DIR="experiments/iter206_iter205_admission_history_recovery/proof/raw/execution_null_run_${RUN_ID}_attempt_1"
test ! -e "$NULL_DIR"
RAW_DIR="$(dirname "$NULL_DIR")"
STAGE="$(mktemp -d "$RAW_DIR/.iter206-null-stage.XXXXXX")"
cleanup() { if test -n "${STAGE:-}" && test -d "$STAGE"; then rm -rf -- "$STAGE"; fi; }
trap cleanup EXIT
gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '{id,name,workflow_id,head_branch,head_sha,path,event,status,conclusion,run_number,run_attempt,run_started_at,updated_at,html_url}' > "$STAGE/run.json"
gh api -X GET "repos/$REPO/actions/runs/$RUN_ID/jobs" -f filter=all -f per_page=100 | jq -S . > "$STAGE/jobs.json"
gh api -X GET "repos/$REPO/actions/runs/$RUN_ID/artifacts" -f per_page=100 | jq -S . > "$STAGE/artifacts.json"
if test "$(jq -r '.total_count' "$STAGE/artifacts.json")" -gt 0; then
  mkdir "$STAGE/artifacts"
  gh run download "$RUN_ID" --dir "$STAGE/artifacts"
fi
(cd "$STAGE" && find . -type f ! -name SHA256SUMS -exec shasum -a 256 '{}' + | LC_ALL=C sort > SHA256SUMS)
mv "$STAGE" "$NULL_DIR"
STAGE=""
trap - EXIT
printf 'Preserved terminal iter206 evidence at %s; publish a bounded null before any successor.\n' "$NULL_DIR"
```

After the sole run succeeds, re-prove its uniqueness and source, promote exactly one complete attempt-`1`
aggregate, validate it before the move, then adjudicate and run the checkpoint-aware blind judge.

```bash
set -euo pipefail
test "$(git branch --show-current)" = master
git fetch origin master
test -z "$(git status --porcelain)"
REPO="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
test "$REPO" = "manfromnowhere143/telos"
ITER206_WORKFLOW_ID="$(gh api -X GET "repos/$REPO/actions/workflows/iter206-execute.yml" --jq '.id')"
test "$(gh api --paginate -X GET "repos/$REPO/actions/workflows/$ITER206_WORKFLOW_ID/runs" -f per_page=100 --jq '.workflow_runs | length' | awk '{ total += $1 } END { print total + 0 }')" -eq 1
test "$(gh api --paginate -X GET "repos/$REPO/actions/workflows/$ITER206_WORKFLOW_ID/runs" -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs | length' | awk '{ total += $1 } END { print total + 0 }')" -eq 1
RUN_ID="$(gh api -X GET "repos/$REPO/actions/workflows/$ITER206_WORKFLOW_ID/runs" -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs[0].id // empty')"
APPROVED_SHA="$(gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '.head_sha')"
RUN_BINDING="$(gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '[.id,.workflow_id,.name,.event,.head_branch,.head_sha,.path,.run_number,.run_attempt] | @tsv')"
test "$RUN_BINDING" = "$RUN_ID"$'	'"$ITER206_WORKFLOW_ID"$'	iter206-execute	workflow_dispatch	master	'"$APPROVED_SHA"$'	.github/workflows/iter206-execute.yml	1	1'
test "$(git rev-parse HEAD)" = "$APPROVED_SHA"
test "$(gh run view "$RUN_ID" --json status,conclusion,attempt --jq '[.status,.conclusion,.attempt] | join(" ")')" = "completed success 1"
python3 -I -S scripts/validate_iter205_pre_dispatch_null.py
python3 -I -S scripts/build_iter206_runtime_manifest.py --check
EXECUTION_DIR="experiments/iter206_iter205_admission_history_recovery/proof/raw/execution"
test ! -e "$EXECUTION_DIR"
RAW_DIR="$(dirname "$EXECUTION_DIR")"
STAGE="$(mktemp -d "$RAW_DIR/.iter206-execution-stage.XXXXXX")"
cleanup() { if test -n "${STAGE:-}" && test -d "$STAGE"; then rm -rf -- "$STAGE"; fi; }
trap cleanup EXIT
gh run download "$RUN_ID" --name "iter206-execution-complete-$RUN_ID-attempt-1" --dir "$STAGE"
python3 -I -S scripts/collect_iter206_execution.py check \
  --execution-dir "$STAGE" \
  --aggregate-receipt "$STAGE/_telos_iter206_execution_complete.receipt.json" \
  --spec-index experiments/iter203_iter202_safety_recovery/proof/raw/specs/index.json \
  --runtime-manifest experiments/iter206_iter205_admission_history_recovery/proof/raw/runtime_manifest.json
mv "$STAGE" "$EXECUTION_DIR"
STAGE=""
trap - EXIT
python3 -I -S scripts/adjudicate_iter206_admission_history_recovery.py
python3 -I -S scripts/run_iter206_admission_history_recovery_blind_judge.py
```

If local adjudication or judging is interrupted after the complete artifact is promoted, do not redownload
or rerun anything. Revalidate the final corpus in place, reproduce deterministic adjudication, and resume only
the checkpoint-aware judge.

```bash
set -euo pipefail
test "$(git branch --show-current)" = master
git fetch origin master
git diff --quiet
git diff --cached --quiet
REPO="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
test "$REPO" = "manfromnowhere143/telos"
ITER206_WORKFLOW_ID="$(gh api -X GET "repos/$REPO/actions/workflows/iter206-execute.yml" --jq '.id')"
test "$(gh api --paginate -X GET "repos/$REPO/actions/workflows/$ITER206_WORKFLOW_ID/runs" -f per_page=100 --jq '.workflow_runs | length' | awk '{ total += $1 } END { print total + 0 }')" -eq 1
test "$(gh api --paginate -X GET "repos/$REPO/actions/workflows/$ITER206_WORKFLOW_ID/runs" -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs | length' | awk '{ total += $1 } END { print total + 0 }')" -eq 1
RUN_ID="$(gh api -X GET "repos/$REPO/actions/workflows/$ITER206_WORKFLOW_ID/runs" -f event=workflow_dispatch -f per_page=100 --jq '.workflow_runs[0].id // empty')"
APPROVED_SHA="$(gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '.head_sha')"
RUN_BINDING="$(gh api -X GET "repos/$REPO/actions/runs/$RUN_ID" --jq '[.id,.workflow_id,.name,.event,.head_branch,.head_sha,.path,.run_number,.run_attempt] | @tsv')"
test "$RUN_BINDING" = "$RUN_ID"$'	'"$ITER206_WORKFLOW_ID"$'	iter206-execute	workflow_dispatch	master	'"$APPROVED_SHA"$'	.github/workflows/iter206-execute.yml	1	1'
test "$(git rev-parse HEAD)" = "$APPROVED_SHA"
test "$(gh run view "$RUN_ID" --json status,conclusion,attempt --jq '[.status,.conclusion,.attempt] | join(" ")')" = "completed success 1"
EXECUTION_DIR="experiments/iter206_iter205_admission_history_recovery/proof/raw/execution"
test -d "$EXECUTION_DIR"
test ! -L "$EXECUTION_DIR"
python3 -I -S scripts/build_iter206_runtime_manifest.py --check
python3 -I -S scripts/collect_iter206_execution.py check \
  --execution-dir "$EXECUTION_DIR" \
  --aggregate-receipt "$EXECUTION_DIR/_telos_iter206_execution_complete.receipt.json" \
  --spec-index experiments/iter203_iter202_safety_recovery/proof/raw/specs/index.json \
  --runtime-manifest experiments/iter206_iter205_admission_history_recovery/proof/raw/runtime_manifest.json
python3 -I -S scripts/adjudicate_iter206_admission_history_recovery.py
python3 -I -S scripts/run_iter206_admission_history_recovery_blind_judge.py
```

## Verification Before Action

Run from the standalone TELOS repository root:

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
python3 scripts/build_iter202_solve_targets.py --check
python3 scripts/audit_iter202_sample_overlap.py --check
python3 scripts/build_iter203_safety_recovery.py --check
python3 scripts/build_iter203_runtime_manifest.py --check
python3 scripts/validate_iter203_infrastructure_null.py
python3 scripts/validate_iter204_pre_dispatch_null.py
python3 scripts/validate_iter205_pre_dispatch_null.py
python3 scripts/build_iter206_runtime_manifest.py --check
python3 scripts/validate_iter206_publication_safety.py --check
python3 scripts/validate_iter206_runtime_recovery.py
python3 scripts/validate_learning_ledger.py
python3 scripts/validate_handoff.py
```
