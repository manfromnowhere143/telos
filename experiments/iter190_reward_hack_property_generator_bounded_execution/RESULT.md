# Iteration 190 Result - Reward-Hack Property-Generator Bounded Execution

Status: `null`.

## What this gate did

This gate did not call a provider. It froze the full `24`-packet planned property-generator schedule and
then stopped before spend because the execution surface cannot satisfy the pre-registered local/container
execution bar without inventing an unregistered adapter.

The stopped-before-spend decision is the result: a paid property-generator run would currently produce
prose proposals, but the committed schema has no direct runnable artifact field and this local runtime is
not a ready SWE-bench/container execution surface.

## Pre-Spend Findings

- Planned primary property-generator calls: `24`.
- Provider calls executed: `0`.
- Estimated provider spend: `$0.00`.
- Prompt leakage hits: `0`.
- Response secret/private identifier hits: `0` (no provider responses were produced).
- Local/container execution attempts counted: `0`.
- New SWE-bench execution attempts: `0`.
- Control false positives: `0`.
- Hack property failures: `0`.
- Forbidden positive claim hits: `0`.
- Secret/private identifier hits in artifacts: `0`.

Execution-surface blockers:

- `property_generator_schema_has_no_direct_runnable_artifact_fields`
- `swebench_python_package_not_installed`
- `docker_runtime_not_available_for_container_execution`
- `local_machine_arch_is_arm64_not_native_x86_for_swebench_containers`

Failed pass bars:

- `local_or_container_execution_attempts_at_least_20`
- `nondecisions_at_most_4`
- `hack_property_failures_at_least_4`

## Interpretation

Iter190 confirms that the next improvement is not another verdict-only judge and not a paid prose-only
property call. The missing piece is an execution contract: either a restricted property DSL or a
sandboxed, provider-compatible code artifact with deterministic adapter boundaries. Without that, Telos
would be counting prose as execution evidence, which would violate the mission standard.

## Claim Boundary

At most, this gate supports a null pre-spend execution-surface finding over the committed iter186 packet
set. The public panel metric remains unrepaired iter179 `majority_catch`: `17/40` hack rows and `0/40`
controls.

No leaderboard ranking, state-of-the-art claim, natural reward-hacking frequency estimate, broad
reward-model robustness claim, production deployment claim, model-superiority claim, public benchmark
score, repaired-score claim, or claim outside committed proof packets is supported.

## Evidence

- `proof/scheduled_property_generator_call_manifest.json`
- `proof/raw/scheduled_prompts/`
- `proof/prompt_leakage_scan.json`
- `proof/execution_surface_preflight.json`
- `proof/execution_attempt_audit.json`
- `proof/pass_bar_audit.json`
- `proof/claim_boundary_audit.json`
- `proof/forbidden_claim_scan.json`
- `proof/secret_safety_audit.json`
- `proof/endpoint_results.json`
- `proof/audit_report.json`
- `proof/run_summary.json`
- `proof/valid/receipt_reward_hack_property_generator_bounded_execution.json`

## Next Gate

The active next gate is
`experiments/iter191_reward_hack_property_execution_contract_design/HYPOTHESIS.md`: design the execution contract/harness before any more
property-generator spend.
