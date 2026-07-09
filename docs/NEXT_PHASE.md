# Next Phase

## Current Action

Run `iter50_provider_compatible_execution_wrapper_recovery` exactly as frozen in
[`../experiments/iter50_provider_compatible_execution_wrapper_recovery/HYPOTHESIS.md`](../experiments/iter50_provider_compatible_execution_wrapper_recovery/HYPOTHESIS.md).

The output is not a leaderboard score. It is a zero-spend wrapper-recovery gate required before the
two-pair provider-compatible execution retry can honestly run:

- keep
  [`../experiments/iter31_claim_boundary_release_manifest/proof/claim_boundary_release_manifest.json`](../experiments/iter31_claim_boundary_release_manifest/proof/claim_boundary_release_manifest.json)
  as the claim-boundary reviewer entry point,
- keep
  [`../experiments/iter35_release_manifest_self_coverage_guard/proof/self_coverage_report.json`](../experiments/iter35_release_manifest_self_coverage_guard/proof/self_coverage_report.json)
  and
  [`../experiments/iter36_release_manifest_self_coverage_negative_guard/proof/negative_guard_report.json`](../experiments/iter36_release_manifest_self_coverage_negative_guard/proof/negative_guard_report.json)
  visible as self-coverage reviewer evidence,
- keep `iter23` and `iter25` visible as failed/null evidence,
- keep the changed `iter24` candidate separate from original `iter21` provider logic,
- keep the `iter35` self-coverage report visible,
- keep the `iter36` self-coverage negative guard visible,
- use only the frozen task identifiers, baseline and Telos-instrumented conditions, and before-data
  metrics from
  [`../experiments/iter39_public_task_protocol_effect_slice/proof/protocol_effect_slice.json`](../experiments/iter39_public_task_protocol_effect_slice/proof/protocol_effect_slice.json),
- use the blocked preflight evidence from
  [`../experiments/iter40_public_task_protocol_effect_execution/proof/preflight.json`](../experiments/iter40_public_task_protocol_effect_execution/proof/preflight.json),
- use the isolated-runner evidence from
  [`../experiments/iter41_public_task_protocol_effect_runner_recovery/proof/runner_recovery_report.json`](../experiments/iter41_public_task_protocol_effect_runner_recovery/proof/runner_recovery_report.json),
- use the blocked execution-retry evidence from
  [`../experiments/iter42_public_task_protocol_effect_execution_retry/proof/preflight.json`](../experiments/iter42_public_task_protocol_effect_execution_retry/proof/preflight.json),
- use the recovered provider-harness evidence from
  [`../experiments/iter43_provider_execution_harness_recovery/proof/run_summary.json`](../experiments/iter43_provider_execution_harness_recovery/proof/run_summary.json),
- use the blocked execution-after-harness evidence from
  [`../experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/proof/run_summary.json`](../experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/proof/run_summary.json),
- use the assembled executor manifest from
  [`../experiments/iter45_public_task_condition_executor_assembly/proof/executor_manifest.json`](../experiments/iter45_public_task_condition_executor_assembly/proof/executor_manifest.json),
- use the blocked execution-with-assembled-executor evidence from
  [`../experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor/proof/run_summary.json`](../experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor/proof/run_summary.json),
- use the command-binding recovery evidence from
  [`../experiments/iter47_provider_task_condition_command_binding_recovery/proof/command_binding_report.json`](../experiments/iter47_provider_task_condition_command_binding_recovery/proof/command_binding_report.json),
- use the refrozen provider-compatible slice from
  [`../experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/proof/provider_compatible_slice.json`](../experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/proof/provider_compatible_slice.json),
- use the blocked iter49 preflight from
  [`../experiments/iter49_provider_compatible_protocol_effect_execution_retry/proof/preflight.json`](../experiments/iter49_provider_compatible_protocol_effect_execution_retry/proof/preflight.json),
- recover a committed dry-run wrapper at `scripts/run_provider_compatible_protocol_effect_pairs.py`,
- dry-run exactly the two selected BattleSnake PvP condition pairs,
- keep all four excluded Dummy/deterministic-edit pairs visible as exclusions,
- keep provider model calls at `0`,
- keep provider spend at `$0.00`,
- keep cloud runner startup at `0` unless a separate lifecycle-only preflight is published first,
- forbid GPU use,
- do not modify, stop, start, delete, or reuse Sentinel-named resources,
- do not make production/live-domain, leaderboard, SWE-bench, model-superiority, or
  state-of-the-art claims.

## Infrastructure Discipline

Available cloud and sandbox resources are escalation tools, not default proof. The order is:

1. local receipt validation,
2. local or GitHub-runner CodeClash smoke under Docker,
3. deterministic Mini-SWE-Agent behavior smoke,
4. deterministic edit-agent slice,
5. provider-model pilot selection with exact spend and evidence bars,
6. E2B or sandboxed execution only when isolation is needed and the gate records it,
7. GPU or provider model cloud only when a frozen gate names the spend and expected evidence.

No GPU or provider model run is authorized by `iter00`, `iter01`, `iter02`, `iter03`, `iter04`, or
`iter05`. `iter06`, `iter07`, and `iter08` also forbid provider model calls and GPU runs. `iter09`
authorized only the single frozen paid smoke, but it stopped before spend because preflight failed.
`iter10` restored the credential path without calling a model. `iter11` authorized only the same
single frozen paid smoke under the original `$25` ceiling; it blocked on Vertex predict permission.
`iter12` authorized a minimal access probe. `iter13` through `iter19` stayed inside their frozen
provider-smoke and quality-control gates. `iter20` through `iter23` returned to local semantic
verification. `iter23` failed locally under the explicit `tail_remains_occupied` assumption.
`iter24` passed locally for a changed candidate under the same assumption. `iter25` failed the full
mutation-guard bar because a single own-tail mutation left the self-snake fallback path intact.
`iter26` passed the compound own-tail mutation guard. `iter27` passed the claim-boundary matrix.
`iter28` passed the public claim-surface guard. `iter29` passed the negative public-claim fixture
guard. `iter30` passed the boundary-matrix schema guard. `iter31` passed the claim-boundary release
manifest. `iter32` passed the release-manifest negative guard. `iter33` passed the public-sync
guard. `iter34` passed the public-sync negative guard. `iter35` passed the release-manifest
self-coverage guard. `iter36` passed the self-coverage negative guard. `iter37` passed the
self-coverage public-sync guard. `iter38` passed the self-coverage public-sync negative guard.
`iter39` passed the public-task protocol-effect slice-selection gate. `iter40` blocked before
provider execution because Docker and pinned CodeClash runner readiness were not established.
`iter41` passed runner recovery through isolated GitHub Actions CodeClash runs at zero provider
spend. `iter42` blocked before provider execution because the provider-capable execution harness,
cost capture, and raw-artifact redaction controls were not recovered. `iter43` passed provider
harness recovery with a non-GPU runner lifecycle probe, zero provider model calls, zero full
task-condition pairs, and zero provider spend. `iter44` blocked before provider execution because
the recovered harness still disables full protocol-effect execution and requires a future
task-condition gate. `iter45` authorizes only executor assembly and dry-run validation; it does not
authorize provider model calls, cloud runner startup, GPU, leaderboard, SWE-bench result,
production, live-domain behavior, model-superiority, or state-of-the-art claims.
`iter45` passed that dry-run executor assembly with six frozen pairs and zero spend. `iter46`
blocked before provider execution because provider overlays were not bound into the per-pair
commands and the recovered harness still disabled full task-condition execution. `iter47`
blocked and narrowed the command surface to two provider-ready BattleSnake PvP pairs while keeping
four incompatible pairs visible. `iter48` passed the zero-spend provider-compatible slice refreeze,
selecting the two BattleSnake pairs and excluding four historical pairs with reasons. `iter49`
blocked before provider execution because the required two-pair execution wrapper was missing and
the recovered harness still disabled full task-condition execution. `iter50` authorizes only
zero-spend provider-compatible execution wrapper recovery. Provider calls, paid execution, GPU use,
Sentinel resource modification, excluded-pair execution, and benchmark/model overclaims remain
forbidden.

## After The Wrapper-Recovery Gate

If the wrapper-recovery gate passes:

1. Publish the exact wrapper dry-run plan and rejection evidence for excluded pairs.
2. Pre-register the next two-pair paid execution retry only if cost, raw artifact, receipt,
   redaction, metric, and lifecycle capture are represented by committed code.
3. Keep the future paid retry within the existing `16` invocation and `$10.00` ceilings unless a
   new gate narrows or changes them before data.

If the wrapper-recovery gate blocks or fails:

1. Publish the blocked/null or quality-failure result.
2. Correct only the specific wrapper, command, config, overlay, artifact, cost, redaction,
   lifecycle, receipt, or metric gap.
3. Keep prior proof artifacts unchanged unless the evidence identifies a real structural gap.
