# Continuity

Read this file before changing the repository. It carries the stable operating rules; `HANDOFF.md`
carries the dynamic state.

## Standard

1. **Pre-register before data.** Every experiment gets a `HYPOTHESIS.md` with numeric bars and
   named falsifiers before any result.
2. **Nulls publish at full weight.** A failed gate is a result, not a footnote.
3. **Evidence or it did not happen.** Every number in a result must regenerate from committed
   proof artifacts or cited public sources.
4. **No inflated language.** Confidence comes from receipts, not adjectives.
5. **Corrections stay visible.** If a claim is wrong, correct it in place and explain the reason.
6. **Cheap-first.** Offline gates run before API spend, GPU spend, or long harness runs.
7. **One operator at a time.** Keep the repo handoff-ready after every state change.
8. **Mission loop is explicit.** The public loop contract lives at `mission/loop.json`. Do not claim
   private Aweb/Maestro execution unless Aweb discovery returns a concrete Telos capability slug.

## Current Research Arc

This repo is separate from Sentinel. It keeps Sentinel's operating standard and changes the domain:
autonomous agent completion proof.

Current gate:

- `experiments/iter145_judge_panel_before_execution/HYPOTHESIS.md`

Claim-boundary reviewer entry point:

- `experiments/iter31_claim_boundary_release_manifest/proof/claim_boundary_release_manifest.json`

Self-coverage reviewer entry points:

- `experiments/iter35_release_manifest_self_coverage_guard/proof/self_coverage_report.json`
- `experiments/iter36_release_manifest_self_coverage_negative_guard/proof/negative_guard_report.json`

Current claim:

- `iter00_target_survey` selected a hybrid Telos overlay on CodeClash + SWE-bench Verified.
- `iter01_receipt_dry_run` passed: valid receipt accepted, invalid receipt rejected, learning
  record validated.
- `iter02_public_task_slice` passed: selected a CodeClash-first no-LLM smoke slice with SWE-bench
  Verified receipt fields.
- `iter03_codeclash_smoke` passed: GitHub Actions ran the no-LLM CodeClash dummy tournament and
  produced a valid Telos receipt.
- `iter04_agent_behavior_slice` passed: selected the deterministic Mini-SWE-Agent BattleSnake PvP
  smoke as the first real agent-behavior run.
- `iter05_agent_behavior_smoke` passed: GitHub Actions ran the deterministic Mini-SWE-Agent
  BattleSnake PvP smoke and produced a valid, audited Telos receipt.
- `iter06_deterministic_edit_slice` passed: selected a CodeClash overlay that should produce a
  non-empty `telos_marker.py` diff through the Mini-SWE-Agent path at zero provider cost.
- `iter07_deterministic_edit_smoke` passed: GitHub Actions ran the deterministic Mini-SWE-Agent
  edit smoke, captured a non-empty `p1` diff creating `telos_marker.py`, and produced a valid,
  audited Telos receipt.
- `iter08_provider_model_pilot_slice` passed: selected a local-first Google Vertex AI
  `gemini-3.1-pro-preview-customtools` CodeClash pilot with a $25 ceiling and no model-result
  claim.
- `iter09_provider_model_pilot_smoke` blocked before spend: ADC token refresh required
  interactive reauthentication, so no paid model call or CodeClash provider run occurred.
- `iter10_provider_auth_recovery` passed: local ADC refresh now succeeds with token output
  suppressed, required Google services are visible by service name, and no credential material or
  project/account identifier is committed.
- `iter11_provider_model_pilot_retry` blocked: an ephemeral GCE runner executed the frozen
  CodeClash path and reached Vertex, but the selected `gemini-3.1-pro-preview-customtools` model
  path returned `aiplatform.endpoints.predict` permission denial until the run hit the 45-minute
  ceiling. No provider trajectory, cost, or API-call stats are claimed.
- `iter12_vertex_model_access_recovery` passed: a dedicated Telos runner identity reached the
  original Vertex custom-tools endpoint from an ephemeral GCE VM through metadata credentials,
  returned HTTP `200` with one candidate and usage metadata, deleted the probe VM, and kept the
  original model selection.
- `iter13_provider_model_pilot_retry_after_access_recovery` passed: the dedicated runner completed
  the frozen Vertex Gemini CodeClash provider smoke with exit code `0`, `p1` trajectory present,
  `5` API calls, `$0.030392000000000002` reported model cost, and a visible diff-hygiene issue
  because `p1` left `patch.py`.
- `iter14_provider_diff_quality_review` passed: no provider/model/API/GPU spend occurred; the
  `p1` diff was reconstructed from committed artifacts; the `main.py` boundary edit was judged to
  satisfy the local Step 1 task intent; and unreferenced helper files such as `patch.py` now fail
  future clean-pass provider-smoke quality gates.
- `iter15_provider_strict_diff_rerun` failed the clean diff-quality bar: the provider-backed rerun
  recovered with explicit `global` Vertex routing, CodeClash exited `0`, `p1` submitted with `5`
  model API calls and `$0.037882` reported cost, but the submitted diff left `patch.py` and
  `patch2.py`, so the strict status is `fail_unjustified_helper_files`.
- `iter16_provider_workspace_hygiene_control` passed the concrete helper-residue bar: the same
  provider-smoke shape completed with exit code `0`, `p1` submitted with `6` model API calls and
  `$0.035064` reported cost, used `/tmp/patch.py` as scratch, removed it, ran
  `git status --short`, and submitted only `README_agent.md` plus `main.py`. The result records a
  style caveat because the submitted `main.py` diff contains one whitespace-only added blank line.
- `iter17_provider_lint_hygiene_control` passed the clean workspace-and-lint bar: the same
  provider-smoke shape completed with exit code `0`, `p1` submitted with `5` model API calls and
  `$0.02864` reported cost, used `/tmp/patch.py` as scratch, removed it, ran
  `git status --short && git diff --check`, and submitted only `README_agent.md` plus `main.py`
  with no helper residue or added trailing whitespace.
- `iter18_provider_behavior_depth_control` passed with a process caveat: the same provider-smoke
  shape completed with exit code `0`, `p1` submitted with `6` model API calls and `$0.036876`
  reported cost, removed `/tmp/patch.py`, fixed an initial `git diff --check` trailing-whitespace
  failure, submitted only `README_agent.md` plus `main.py`, and added source-evident Step 2
  self-collision prevention. The caveat is that the trajectory does not show `git status --short`.
- `iter19_provider_final_inspection_control` passed the final-inspection bar: the same
  provider-smoke shape completed with exit code `0`, `p1` submitted with `5` model API calls and
  `$0.034589999999999996` reported cost, removed `/tmp/edit.py`, fixed an initial
  `git status --short && git diff --check` trailing-whitespace failure, then ran
  `git status --short && git diff --check` with return code `0` immediately before submission. The
  submitted diff still changed only `README_agent.md` plus `main.py` and retained source-evident
  self-collision prevention.
- `iter20_behavior_semantic_verification` passed: the submitted `iter19` diff was reconstructed
  from committed artifacts, imported locally, and verified with eight deterministic safety cases.
  All four boundary cases and all four self-collision cases excluded the forbidden move; no
  provider call, API call, GPU, cloud runner, production change, leaderboard run, or SWE-bench run
  occurred.
- `iter21_opponent_collision_control` passed: the provider-backed run completed with exit code `0`,
  `p1` submitted with `5` model API calls and `$0.043329999999999994` reported cost, final
  inspection ran clean after whitespace repair, and the reconstructed submitted bot passed twelve
  deterministic semantic cases covering boundary, self-collision, and opponent-body collision
  behavior. The result records tail-exclusion semantics and a repaired redaction placeholder.
- `iter22_semantic_mutation_guard` passed: the clean reconstructed `iter21` bot still passed all
  twelve frozen semantic cases, and targeted mutants disabling boundary, self-collision, and
  opponent-collision behavior each failed the corresponding semantic case family. No provider,
  API, GPU, or cloud spend occurred.
- `iter23_tail_semantics_falsification` failed under the explicit `tail_remains_occupied`
  assumption: occupied self-tail and opponent-tail cases left the forbidden tail move in the
  safe-move list while both non-tail controls still passed. No provider, API, GPU, cloud runner,
  production change, leaderboard run, or SWE-bench run occurred.
- `iter24_tail_safety_control` passed for a clearly labeled changed candidate: the original
  `iter21` tail failure remained visible, while the candidate that includes own and opponent tails
  in collision checks passed all four local cases under `tail_remains_occupied`. No provider, API,
  GPU, cloud runner, production change, leaderboard run, or SWE-bench run occurred.
- `iter25_tail_safety_mutation_guard` failed the full mutation-guard bar: the clean `iter24`
  candidate still passed, and the opponent-tail exclusion mutant was detected, but the direct
  own-tail exclusion mutant still passed because the later `board.snakes` loop checks our own snake.
  No provider, API, GPU, cloud runner, production change, leaderboard run, or SWE-bench run
  occurred.
- `iter26_own_tail_redundancy_mutation_guard` passed: a compound mutant removed both direct
  own-tail checking and the self-snake fallback path, causing the own occupied-tail target case to
  fail while non-tail controls still passed. No provider, API, GPU, cloud runner, production
  change, leaderboard run, or SWE-bench run occurred.
- `iter27_semantic_claim_boundary_matrix` passed: a machine-checkable matrix now separates original
  provider logic, changed candidate logic, failed/null gates, and verifier-strength evidence across
  `iter20` through `iter26`. It explicitly does not claim original `iter21` occupied-tail safety.
  No provider, API, GPU, cloud runner, production change, leaderboard run, or SWE-bench run
  occurred.
- `iter28_public_claim_surface_guard` passed: README, report, next-phase, and continuity prose were
  checked against the `iter27` matrix. Failed/null gates remained visible, changed-candidate
  boundaries remained visible, and original `iter21` occupied-tail safety was not claimed. No
  provider, API, GPU, cloud runner, production change, leaderboard run, or SWE-bench run occurred.
- `iter29_public_claim_surface_negative_guard` passed: real public prose still passed, and four
  generated overclaim fixtures failed for the expected reasons. No provider, API, GPU, cloud
  runner, production change, leaderboard run, or SWE-bench run occurred.
- `iter30_boundary_matrix_schema_guard` passed: the current `iter27` claim-boundary matrix
  validated, and five malformed matrix fixtures failed for the expected schema reasons. No
  provider, API, GPU, cloud runner, production change, leaderboard run, or SWE-bench run occurred.
- `iter31_claim_boundary_release_manifest` passed: a reviewer-facing manifest indexed the
  claim-boundary matrix, public guards, schema guard, and 33 referenced proof artifacts with
  matching hashes. No provider, API, GPU, cloud runner, production change, leaderboard run, or
  SWE-bench run occurred.
- `iter32_claim_boundary_release_manifest_negative_guard` passed: the real release manifest still
  passed its audit, and five malformed manifest fixtures failed for expected reasons. No provider,
  API, GPU, cloud runner, production change, leaderboard run, or SWE-bench run occurred.
- `iter33_release_manifest_public_sync_guard` passed: README, report, next-phase, and continuity
  prose reference the release manifest and remain inside its claim boundaries. No provider, API,
  GPU, cloud runner, production change, leaderboard run, or SWE-bench run occurred.
- `iter34_release_manifest_public_sync_negative_guard` passed: real public prose still passed, and
  five malformed public-prose fixtures failed for expected reasons. No provider, API, GPU, cloud
  runner, production change, leaderboard run, or SWE-bench run occurred.
- `iter35_release_manifest_self_coverage_guard` passed: the release-manifest reviewer packet's
  own `iter31` through `iter34` proof gates are represented with matching hashes across 49 proof
  artifacts, while `iter23` and `iter25` remain visible as failed/null evidence. No provider, API,
  GPU, cloud runner, production change, leaderboard run, or SWE-bench run occurred.
- `iter36_release_manifest_self_coverage_negative_guard` passed: the real `iter35` self-coverage
  report still passed, and five malformed self-coverage fixtures failed for expected reasons. No
  provider, API, GPU, cloud runner, production change, leaderboard run, or SWE-bench run occurred.
- `iter37_release_manifest_self_coverage_public_sync_guard` passed: README, report, next-phase,
  and continuity prose surface the release-manifest self-coverage report and negative guard while
  keeping the release manifest as the claim-boundary reviewer entry point. No provider, API, GPU,
  cloud runner, production change, leaderboard run, or SWE-bench run occurred.
- `iter38_release_manifest_self_coverage_public_sync_negative_guard` passed: real public prose
  still passed, and six malformed public-prose fixtures failed for expected reasons. No provider,
  API, GPU, cloud runner, production change, leaderboard run, or SWE-bench run occurred.
- `iter39_public_task_protocol_effect_slice` passed: a public task protocol-effect slice froze
  three executable CodeClash task surfaces, one SWE-bench Verified receipt anchor, baseline and
  Telos-enforced conditions, before-data metrics, and a bounded provider execution gate. No
  provider, API, GPU, cloud runner, production change, leaderboard run, or SWE-bench run occurred.
- `iter40_public_task_protocol_effect_execution` blocked before provider execution: the secret-safe
  preflight found Vertex service readiness but did not establish Docker daemon readiness or a
  pinned CodeClash checkout, so zero task-condition pairs ran, zero provider model calls occurred,
  zero spend occurred, and no benchmark/model result is claimed.
- `iter41_public_task_protocol_effect_runner_recovery` passed: local Docker still did not answer a
  bounded readiness probe, but the isolated GitHub Actions path passed the dummy, BattleSnake
  behavior, and deterministic edit CodeClash runner checks at the frozen CodeClash commit with zero
  provider model calls and zero provider spend.
- `iter42_public_task_protocol_effect_execution_retry` blocked before provider execution: the
  `iter41` runner evidence was accepted and Google/Vertex readiness was visible without committed
  identifiers, but no provider-capable GitHub workflow, GitHub provider secret boundary, committed
  reusable provider execution harness, cost-capture harness, raw-artifact redaction harness, or
  runner-lifecycle harness was recovered. Six task-condition pairs were planned, zero started, zero
  provider model calls occurred, zero spend occurred, and no benchmark/model result is claimed.
- `iter43_provider_execution_harness_recovery` passed: the reusable provider harness is committed,
  a separate non-GPU Telos VM lifecycle probe created and deleted its own runner, the post-probe
  Telos VM count was zero, a Sentinel-named VM count was observed but not touched, prior provider
  cost/artifact controls were validated, zero provider model calls occurred, zero full
  task-condition pairs ran, and no benchmark/model result is claimed.
- `iter44_public_task_protocol_effect_execution_after_harness_recovery` blocked before provider
  execution: the recovered harness and `iter43` controls were accepted, but the harness still
  disables full protocol-effect execution and requires a future task-condition gate. Six
  task-condition pairs remain planned, zero started, zero provider model calls occurred, zero spend
  occurred, no cloud runner started, and no benchmark/model result is claimed.
- `iter45_public_task_condition_executor_assembly` passed: the executor manifest now represents the
  three frozen CodeClash task surfaces across the two frozen conditions as six dry-run pairs. Each
  pair has artifact, cost, redaction, lifecycle, receipt, and metric plans. Zero provider model
  calls occurred, zero spend occurred, no cloud runner started, no GPU was used, and no
  benchmark/model result is claimed.
- `iter46_public_task_protocol_effect_execution_with_assembled_executor` blocked before provider
  execution: the `iter45` manifest was accepted, but provider overlays were not bound into the
  pair commands, and the recovered harness still disabled full task-condition execution. Six pairs
  remained planned, zero started, zero provider model calls occurred, zero spend occurred, no cloud
  runner started, no GPU was used, no Sentinel-named resources were modified, and no
  benchmark/model result is claimed.
- `iter47_provider_task_condition_command_binding_recovery` blocked and narrowed the provider
  command surface: the existing Vertex provider overlay can bind the two BattleSnake PvP condition
  pairs, but it cannot honestly bind the Dummy or deterministic-edit pairs without changing task
  semantics. Zero provider model calls occurred, zero spend occurred, no cloud runner started, no
  GPU was used, no Sentinel-named resources were modified, and no benchmark/model result is
  claimed.
- `iter48_provider_compatible_protocol_effect_slice_refreeze` passed: the next provider-compatible
  slice is now the two BattleSnake PvP condition pairs, while four Dummy and deterministic-edit
  pairs remain visible historical exclusions with reasons. Zero provider model calls occurred, zero
  spend occurred, no cloud runner started, no GPU was used, no Sentinel-named resources were
  modified, and no benchmark/model result is claimed.
- `iter49_provider_compatible_protocol_effect_execution_retry` blocked before provider execution:
  the two-pair slice remained valid and provider-ready, but the required committed execution wrapper
  was missing and the existing provider harness still disabled full task-condition execution. Two
  pairs remained planned, zero started, zero provider model calls occurred, zero spend occurred, no
  cloud runner started, no GPU was used, no Sentinel-named resources were modified, and no
  benchmark/model result is claimed.
- `iter50_provider_compatible_execution_wrapper_recovery` passed as a zero-spend dry run: the
  committed wrapper emits exactly two selected BattleSnake pair plans, rejects all four historical
  Dummy/deterministic-edit exclusions, and records artifact, cost, redaction, receipt, lifecycle,
  and metric destinations for the future paid retry. Zero provider model calls occurred, zero spend
  occurred, no cloud runner started, no GPU was used, no Sentinel-named resources were modified, and
  no benchmark/model result is claimed.
- `iter51_provider_compatible_protocol_effect_execution_with_wrapper` blocked before provider
  execution: the iter50 wrapper remained dry-run-only, the recovered provider harness still
  disabled full task-condition execution, and the baseline/Telos rows shared the same runtime
  command, overlay, and agent prompt apart from output directory. Two pairs remained planned, zero
  started, zero provider model calls occurred, zero spend occurred, no cloud runner started, no GPU
  was used, no Sentinel-named resources were modified, and no benchmark/model result is claimed.
- `iter52_provider_condition_runtime_separation_recovery` passed as a zero-spend readiness gate:
  the wrapper now exposes a disabled-by-default execution mode, the baseline and Telos rows have
  distinct runtime commands, provider overlays, and agent prompts, and the Telos row has a concrete
  receipt validation path before verified completion can be accepted. Zero provider model calls
  occurred, zero spend occurred, no cloud runner started, no GPU was used, no Sentinel-named
  resources were modified, and no benchmark/model result is claimed.
- `iter53_provider_compatible_protocol_effect_execution_after_condition_recovery` blocked before
  provider execution: condition separation was ready, but the pair executor still intentionally
  raised, the base harness still disabled full protocol-effect execution, the pinned CodeClash
  checkout was not ready, and Docker readiness timed out. Zero provider model calls occurred, zero
  spend occurred, no cloud runner started, no GPU was used, no Sentinel-named resources were
  modified, and no benchmark/model result is claimed.
- `iter54_provider_pair_executor_recovery` passed as a zero-spend readiness gate: the pinned
  CodeClash checkout was ready, six recovered overlay files were copied with matching hashes,
  exact baseline/Telos commands were materialized without execution, Docker daemon readiness was
  proven through the current Docker Desktop binary, and the stale `/usr/local/bin/docker` symlink
  caveat was recorded. Zero provider model calls occurred, zero spend occurred, no cloud runner
  started, no GPU was used, no Sentinel-named resources were modified, and no benchmark/model
  result is claimed.
- `iter55_provider_compatible_paid_execution_after_executor_recovery` blocked before provider
  execution: the iter54 executor was ready, but non-interactive ADC refresh required
  reauthentication and active-user impersonation of the dedicated Telos runner lacked token-creator
  access. Zero provider model calls occurred, zero spend occurred, no cloud runner started, no GPU
  was used, no Sentinel-named resources were modified, and no benchmark/model result is claimed.
- `iter56_provider_auth_recovery_for_paid_protocol_effect` passed: local ADC was repaired
  non-interactively and the selected Vertex endpoint answered one minimal access probe with usage
  metadata under a `$0.01` spend bound. No paid BattleSnake row ran, no excluded pair ran, no cloud
  runner started, no GPU was used, no Sentinel-named resources were modified, and no
  benchmark/model result is claimed.
- `iter57_provider_compatible_paid_execution_after_auth_recovery` blocked before provider model
  calls: one selected baseline-row attempt reached round-0 raw evidence, but LiteLLM could not
  import `google.auth` from the pinned CodeClash virtualenv. The Telos row and all excluded rows
  remained unattempted, committed metadata records zero provider calls and zero cost, no cloud
  runner started, no GPU was used, no Sentinel-named resources were modified, and no
  benchmark/model result is claimed.
- `iter58_codeclash_vertex_dependency_recovery` passed: the local CodeClash virtualenv now imports
  `google.auth`, the pinned CodeClash commit and frozen provider configs remained unchanged, no
  paid BattleSnake row ran, no excluded pair ran, no provider model call or spend occurred, no GPU
  was used, no Sentinel-named resources were modified, and no benchmark/model result is claimed.
- `iter59_provider_compatible_paid_execution_after_dependency_recovery` blocked after executing
  both selected BattleSnake rows: both rows made one provider call, recorded zero cost in
  CodeClash metadata, returned a redacted `vertex_model_not_found_or_access_denied` provider
  response, produced no verified-completion evidence, executed no excluded pairs, used no GPU, and
  modified no Sentinel-named resources.
- `iter60_provider_model_binding_recovery` blocked after adding `vertex_location: global` to the
  recovered provider model overlay: the LiteLLM probe reached the global Vertex endpoint but
  returned a redacted `CONSUMER_INVALID` quota-project response. One provider call occurred, no
  BattleSnake row or excluded pair executed, no GPU or cloud runner was used, and no Sentinel-named
  resource was modified.
- `iter61_vertex_quota_project_binding_recovery` blocked after proving the Mini-SWE-Agent/LiteLLM
  `extra_headers` path exists: one bounded LiteLLM probe with `X-Goog-User-Project` still returned
  a redacted `CONSUMER_INVALID` response. One provider call occurred, no BattleSnake row or
  excluded pair executed, no GPU or cloud runner was used, and no Sentinel-named resource was
  modified.
- `iter62_vertex_bearer_token_path_recovery` blocked after proving LiteLLM custom headers can
  override the default Authorization header: one bounded LiteLLM probe with runtime bearer-token
  and quota-project headers still returned redacted `CONSUMER_INVALID` evidence. One provider call
  occurred, no BattleSnake row or excluded pair executed, no GPU or cloud runner was used, and no
  Sentinel-named resource was modified.
- `iter63_vertex_access_path_parity_recheck` passed after current direct REST and LiteLLM probes
  both reached the selected Vertex global model through the recovered runtime credential/header
  path. Two provider calls occurred, observed LiteLLM cost was `$0.000014`, no BattleSnake row or
  excluded pair executed, no GPU or cloud runner was used, and no Sentinel-named resource was
  modified.
- `iter64_provider_compatible_paid_execution_after_access_path_recovery` passed as the first
  bounded two-row provider-backed protocol-effect measurement. Baseline verified-completion
  evidence was `true`; Telos verified-completion evidence was `false` because the Telos row
  receipt candidate failed schema validation; the primary delta was `-1`; 10 provider calls and
  `$0.070448` CodeClash metadata cost were recorded; excluded pairs stayed unattempted; and no
  GPU, cloud runner, Sentinel mutation, production/live-domain change, benchmark claim, model
  claim, or state-of-the-art claim occurred.
- `iter65_receipt_schema_prompt_alignment` passed as a zero-spend local prompt/schema recovery:
  the iter64 Telos receipt candidate was classified as schema-incomplete because it omitted eight
  required Telos proof fields, the recovered prompt overlay now names the required fields and
  digest rule, the local valid fixture passes, and the malformed fixture fails.
- `iter66_provider_compatible_paid_execution_after_receipt_prompt_alignment` passed as a bounded
  two-row paid retry using the recovered iter65 overlay. Both selected rows executed, baseline and
  Telos both had verified-completion evidence, the Telos receipt validated, the primary delta was
  `0`, 8 provider calls and `$0.059378` CodeClash metadata cost were recorded, and no excluded
  pair, GPU, cloud runner, Sentinel mutation, production/live-domain change, benchmark claim, model
  claim, or state-of-the-art claim occurred.
- `iter67_provider_compatible_expanded_slice_refreeze` blocked locally with zero provider calls,
  zero spend, no row execution, no GPU, no cloud runner, and no Sentinel mutation. The committed
  candidate universe still has only the two provider-ready BattleSnake rows already executed in
  `iter66`; four Dummy/deterministic-edit rows remain incompatible until adapter recovery.
- `iter68_provider_compatible_task_surface_adapter_recovery` blocked locally with zero provider
  calls, zero spend, no row execution, no GPU, no cloud runner, and no Sentinel mutation. Two
  deterministic-edit adapter rows were planned from committed `iter06` source, but two Dummy rows
  remain rejected because `configs/test/dummy.yaml` has no committed source snapshot.
- `iter69_codeclash_task_surface_source_snapshot_recovery` passed locally with zero provider
  calls, zero spend, no row execution, no GPU, no cloud runner, and no Sentinel mutation. It copied
  `configs/test/dummy.yaml` from the pinned CodeClash Git blob at
  `381cdfa05a35e8acd35853b9fc7e13005121b127` into committed source-only snapshots with hash
  `b8e856447fc71c79bb5e042dc530127480d670d84fd51c03e2c2e7f58c630e97`.
- `iter70_provider_compatible_expanded_adapter_completion` passed locally with zero provider
  calls, zero spend, no row execution, no GPU, no cloud runner, and no Sentinel mutation. Four
  Dummy/deterministic-edit adapter rows and eight overlay files are planned as planning evidence
  only, not execution evidence.
- `iter71_provider_compatible_expanded_slice_after_adapter_completion` passed locally with zero
  provider calls, zero spend, no row execution, no GPU, no cloud runner, and no Sentinel mutation.
  The provider-compatible expanded slice is frozen as six stratified rows: two already executed
  BattleSnake rows are retained as prior paid evidence and four adapter-planned
  Dummy/deterministic-edit rows are selected for a bounded future paid gate. Cross-surface pooling,
  benchmark claims, model claims, and state-of-the-art claims remain forbidden.
- `iter72_provider_compatible_expanded_paid_execution_after_slice_refreeze` blocked after executing
  exactly the four adapter-planned rows under the frozen ceiling. It recorded `17` provider calls
  and `$0.057646` CodeClash metadata cost under the `32` call and `$10.00` ceilings. The two
  retained BattleSnake rows were not rerun. Deterministic-edit baseline verified-completion
  evidence was `true`; Dummy baseline, Dummy Telos, and deterministic-edit Telos verified
  completion evidence were `false`. Both receipt-required rows produced parseable but
  schema-incomplete receipt candidates, so the result blocks without a quality failure.
- `iter73_expanded_receipt_prompt_recovery_after_paid_block` passed locally with zero provider
  calls, zero spend, no row execution, no GPU, no cloud runner, and no Sentinel mutation. It
  classified the two iter72 receipt-required failures with exact missing-field lists, recovered two
  expanded receipt-enforced prompt overlays, proved local valid fixtures pass, and proved a
  malformed fixture fails closed.
- `iter74_provider_compatible_expanded_paid_retry_after_receipt_prompt_recovery` blocked before
  adapter-row execution because Google ADC refresh failed non-interactively. Iter72 and iter73
  prerequisite receipt/audit checks passed, but runtime overlays were not materialized. Zero
  provider calls, zero spend, zero row execution, no GPU, no cloud runner, and no Sentinel mutation
  occurred.
- `iter75_provider_compatible_runtime_adc_recovery_after_paid_retry_block` blocked with zero
  provider calls, zero spend, and zero row execution. Iter74 receipt/audit checks passed, CodeClash
  was pinned, Docker was ready, `google.auth` imported, and gcloud project availability was proven
  with stdout suppressed, but ADC refresh still required interactive reauthentication. No credential
  material was committed.
- `iter76_runtime_adc_recheck_after_operator_refresh` blocked with zero provider calls, zero spend,
  and zero row execution. Iter75 receipt/audit checks passed, CodeClash stayed pinned, Docker was
  ready, `google.auth` imported, and gcloud project availability was proven with stdout suppressed,
  but ADC still required `interactive_reauthentication_required`. No credential material was
  committed.
- `iter77_runtime_adc_recheck_after_application_default_login` passed with zero provider calls, zero
  spend, and zero row execution. Iter76 receipt/audit checks passed, CodeClash stayed pinned, Docker
  was ready, `google.auth` imported, gcloud project availability was proven with stdout suppressed,
  ADC token output was suppressed, and no credential material was committed.
- `iter78_provider_compatible_expanded_paid_retry_after_adc_recovery` blocked after exactly four
  selected adapter-planned rows executed under ceiling. Provider usage was `9` calls and
  `$0.03987600`. Both deterministic-edit rows had verified-completion evidence and both Dummy rows
  hit the per-row global call ceiling before verified-completion evidence could be accepted.
- `iter79_dummy_row_call_ceiling_recovery_after_paid_retry_block` passed with zero provider calls,
  zero spend, and zero row execution. Both iter78 Dummy failures are classified from committed raw
  artifacts as per-row global call-ceiling blockers at the frozen `8` call ceiling;
  deterministic-edit evidence remains retained and not rerun.
- `iter80_dummy_call_ceiling_bounded_paid_retry_after_recovery` passed after exactly two Dummy
  adapter rows executed under the recovered `16` call per-row ceiling. Provider usage was `6` calls
  and `$0.02840000`. Dummy baseline and Dummy Telos both had verified-completion evidence;
  deterministic-edit and BattleSnake rows were not rerun.
- `iter81_expanded_stratified_adapter_validation_consolidation` passed with zero provider calls,
  zero spend, and zero row execution in the gate. It validated iter66, iter78, and iter80 source
  packets, accounted for `23` committed source-packet provider calls and `$0.12765400`, preserved
  six successful rows as separated BattleSnake/deterministic-edit/Dummy adapter-validation strata,
  and retained two iter78 Dummy rows only as diagnostic blocked evidence.
- `iter82_benchmark_facing_protocol_effect_slice_design` passed with zero provider calls, zero
  spend, and zero row execution. It froze a future six-row CodeClash public task-condition paid
  pilot with a `96` provider-call ceiling, `$10.00` total spend ceiling, `$2.00` per-row spend
  ceiling, no cloud runner/GPU/Sentinel/live-domain mutation, and SWE-bench Verified retained only
  as a receipt-field anchor.
- `iter83_benchmark_facing_protocol_effect_execution_pilot` published blocked/null evidence after
  executing exactly the six frozen CodeClash public task-condition rows. Provider usage was `21`
  calls and `$0.11319400`, all row artifacts and receipts stayed under the `96` call and `$10.00`
  ceilings, and Dummy, BattleSnake, and deterministic-edit Telos-minus-baseline deltas were all
  `0`.
- `iter84_benchmark_facing_null_signal_adjudication` passed with zero provider calls, zero spend,
  and zero row execution. It classified the iter83 null/no-signal result as
  `verified_completion_metric_saturated`, selected `redesign_task_metric` as the next step, and
  kept the null/no-signal blocker visible.
- `iter85_discriminating_task_metric_redesign` passed with zero provider calls, zero spend, and
  zero row execution. It froze `task_native_score_share_delta_with_receipt_gates` as the candidate
  metric contract for a zero-spend backtest and did not authorize future paid execution.
- `iter86_discriminating_metric_backtest_on_committed_artifacts` passed with zero provider calls,
  zero spend, and zero row execution. It computed three score-share deltas from committed iter83
  metadata, found the metric computable and non-saturated but mixed-direction, and pre-registered a
  bounded six-row paid replication gate.
- `iter87_benchmark_facing_discriminating_metric_execution_pilot` passed as a bounded six-row
  paid pilot. It executed exactly the frozen rows, used `21` provider calls and `$0.12498400`,
  validated all receipt-required rows, and computed fresh mixed-direction score-share deltas:
  Dummy `-0.01575000`, BattleSnake `0.50000000`, deterministic-edit `-0.50000000`.
- `iter88_external_benchmark_readiness_adjudication_after_discriminating_pilot` passed with zero
  provider calls, zero spend, and zero row execution. It found three task-direction flips between
  iter86 and iter87, rejected larger external benchmark design for now, and selected one bounded
  same-slice stability replication.
- `iter89_same_slice_discriminating_metric_stability_replication` passed as a bounded six-row paid
  replication. It executed exactly the frozen rows, used `19` provider calls and `$0.11636200`,
  computed fresh score-share deltas of Dummy `-0.02075000`, BattleSnake `0.00000000`, and
  deterministic-edit `-0.50000000`, and classified stability as `unstable`.
- `iter90_stability_replication_adjudication_after_same_slice_run` passed with zero provider calls,
  zero spend, and zero row execution. It validated iter89, locked the unstable stability evidence,
  rejected immediate benchmark/SOTA escalation and another paid same-slice replication for now, and
  selected empirical validation suite design as the next defensible scientific milestone.
- `iter91_empirical_validation_suite_design_for_completion_verification` passed with zero provider
  calls, zero spend, zero strategy execution, and zero row execution. It froze seven
  false-completion trap families, seven paired legitimate-completion controls, five comparison
  strategies, six quantitative endpoints, independent ground-truth rules, and identical-artifact
  comparison requirements.
- `iter92_empirical_validation_fixture_materialization_for_completion_verification` passed with
  zero provider calls, zero spend, zero strategy execution, and zero row execution. It materialized
  `14` static fixtures, `98` public artifacts, `14` private ground-truth labels, and `5` identical
  strategy-input manifests, with labels excluded from every strategy input.
- `iter93_deterministic_strategy_execution_on_materialized_fixtures` passed with zero provider
  calls, zero spend, zero LLM-judge execution, and zero row execution. It produced `56`
  deterministic decisions: agent self-report and execution-tests-only accepted `7/7`
  false-completion traps, while external verifier and complete Telos protocol accepted `0/7`;
  all four deterministic strategies preserved `7/7` legitimate controls.
- `iter94_provider_llm_judge_execution_on_materialized_fixtures` blocked after one provider call
  and `$0.00470000` spend. The provider returned HTTP 200, but the response ended with
  `MAX_TOKENS` before a parseable JSON decision was produced. No LLM-judge decision or
  all-strategy endpoint was recorded.
- `iter95_provider_llm_judge_prompt_budget_recovery_after_block` passed with zero provider calls,
  zero spend, zero LLM-judge execution, and zero row execution. It diagnosed the iter94 blocker as
  a `256` output-token ceiling consumed by hidden reasoning, materialized `14` recovered prompts
  with private labels excluded, and pre-registered a bounded retry.
- `iter96_provider_llm_judge_bounded_retry_after_prompt_budget_recovery` passed with `14`
  provider calls, `$0.19588800` spend, and `14` parseable LLM-judge fixture decisions. The LLM
  judge accepted `0/7` false-completion traps but rejected `5/7` legitimate controls, preserving
  that adverse strategy evidence for adjudication.
- `iter97_five_strategy_completion_verification_adjudication_after_llm_judge` passed with zero
  provider calls, zero spend, zero strategy execution, and zero row execution. It adjudicated the
  five-strategy table: self-report/tests failed the false-completion bar, the provider LLM judge
  failed legitimate-control preservation, and complete Telos was not distinguished from the simpler
  external verifier.
- `iter98_external_verifier_telos_differential_suite_design_after_adjudication` passed with zero
  provider calls, zero spend, zero strategy execution, and zero row execution. It designed `8`
  differential target families and `16` planned fixtures focused on protocol-specific evidence
  where complete Telos might separate from generic external verification. Expected divergence is a
  hypothesis only, not a result.
- `iter99_external_verifier_telos_differential_fixture_materialization_after_design` passed with
  zero provider calls, zero spend, zero strategy execution, and zero row execution. It materialized
  `16` blinded fixtures, `96` public artifacts, `16` private labels, and `5` identical
  strategy-input manifests with labels excluded from every strategy input.
- `iter100_deterministic_strategy_execution_on_differential_fixtures_after_materialization` passed
  with zero provider calls, zero spend, no provider-backed strategy execution, and `64`
  deterministic decisions. External verifier accepted `4/8` false-completion traps while complete
  Telos accepted `0/8`; all deterministic strategies preserved `8/8` legitimate controls.
- `iter101_provider_llm_judge_execution_on_differential_fixtures_after_deterministic` blocked after
  `14` provider calls and `$0.22777400` estimated spend. It produced `13/16` parseable LLM-judge
  decisions, then `DIFX-FIXTURE-0014` hit `MAX_TOKENS`; all-strategy endpoint evidence remains
  incomplete.
- `iter102_provider_llm_judge_differential_retry_recovery_after_block` passed with zero provider
  calls, zero spend, zero LLM-judge execution, and zero row execution. It preserved iter101 paid
  usage, tied the `DIFX-FIXTURE-0014` blocker to hidden reasoning exhausting the `2048` output
  budget, materialized `16` recovered prompts with private labels excluded, and pre-registered a
  full `16`-fixture retry under one recovered `4096`-token config.
- `iter103_differential_provider_llm_judge_full_retry_after_block_recovery` passed with `16`
  provider calls and `$0.23633000` estimated spend. It produced `16/16` parseable recovered
  LLM-judge decisions, accepted `0/8` false-completion traps, but preserved only `2/8` legitimate
  controls, making it adverse LLM-judge strategy evidence.
- `iter104_five_strategy_differential_adjudication_after_recovered_llm_judge` passed with zero
  provider calls and zero spend. Complete Telos was the only balanced pass on the frozen
  16-fixture differential suite; external verifier accepted `4/8` false-completion traps and the
  recovered LLM judge rejected `6/8` legitimate controls. This is a fixture-level differential
  result, not a benchmark/model/SOTA claim.
- `iter105_external_benchmark_pilot_design_after_differential_adjudication` passed with zero
  provider calls, zero spend, and zero benchmark/task execution. It designed a `20`-packet external
  pilot with `10` false-completion packets, `10` legitimate controls, a future `30` provider-call
  ceiling, and a `$10.00000000` future spend ceiling. This is design evidence only, not a
  benchmark/model/SOTA claim.
- `iter106_external_benchmark_pilot_materialization_after_design` passed with zero provider calls,
  zero spend, zero benchmark/task execution, zero strategy execution, and zero row execution. It
  materialized `20` pilot packets, `160` public artifacts, `10` false-completion private labels,
  `10` legitimate-control private labels, and `5` identical public-only strategy-input manifests.
- `iter107_external_benchmark_pilot_execution_after_materialization` passed with `20` provider
  calls, `$0.38674600` estimated spend, `100` strategy decisions, and `40` raw LLM prompt/response
  artifacts. Complete Telos accepted `0/10` false-completion packets and preserved `10/10`
  legitimate controls; the external verifier accepted `2/10` false-completion packets; the LLM
  judge accepted `0/10` false-completion packets but rejected `10/10` legitimate controls. This is
  a bounded 20-packet pilot result only.
- No model, benchmark leaderboard, SWE-bench, all-strategy superiority, or SOTA result is claimed.
- The next gate may only adjudicate the committed iter107 bounded pilot result and claim boundary
  with zero provider calls, zero spend, zero strategy execution, and zero benchmark packet
  execution. It must use no GPU or cloud runner, mutate no Sentinel resources, make no
  production/live-domain behavior change, and make no benchmark/model/SOTA or broad all-strategy
  superiority claims.

## Required Verification

Run before and after material changes:

```bash
ruff check .
pytest -q
python3 scripts/validate_docs.py
python3 scripts/validate_mission_loop.py
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
python3 scripts/validate_handoff.py
python3 scripts/make_handoff.py
```

If `make_handoff.py` changes `HANDOFF.md`, commit that change with the state change that caused it.

## Handoff Rule

Before stopping:

1. Commit or clearly leave the work uncommitted with a reason.
2. Regenerate `HANDOFF.md`.
3. State whether any experiment is in flight.
4. Never imply a result exists before `RESULT.md` and proof artifacts exist.
