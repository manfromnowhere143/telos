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

- `experiments/iter52_provider_condition_runtime_separation_recovery/HYPOTHESIS.md`

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
- No model or benchmark result is claimed yet.
- The next gate may recover only condition-separated provider-wrapper readiness at zero spend.
  Provider calls, cloud runner startup, GPU use, Sentinel resource modification, excluded-pair
  execution, and benchmark/model overclaims remain forbidden.

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
