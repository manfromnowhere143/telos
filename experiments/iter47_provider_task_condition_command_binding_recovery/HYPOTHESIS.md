# Iteration 47 - Provider Task-Condition Command Binding Recovery

Status: pre-registered, result pending.

## Purpose

`iter46` blocked before provider execution because the assembled `iter45` manifest enumerated six
task-condition pairs but did not bind provider overlays into each pair command, and the recovered
`iter43` harness still disabled full protocol-effect execution.

This gate must recover the missing command binding without provider spend. The output should be a
secret-safe, auditable command surface that either:

1. concretely binds each frozen pair to the provider-backed execution path, or
2. blocks and narrows the claim if any public task surface cannot honestly be provider-backed under
   the frozen protocol-effect design.

## Frozen Input

- Protocol-effect slice:
  `experiments/iter39_public_task_protocol_effect_slice/proof/protocol_effect_slice.json`.
- Provider overlay files:
  `experiments/iter09_provider_model_pilot_smoke/proof/overlay/`.
- Provider harness:
  `scripts/run_ephemeral_vertex_codeclash_provider.py`.
- Executor manifest:
  `experiments/iter45_public_task_condition_executor_assembly/proof/executor_manifest.json`.
- Blocked execution result:
  `experiments/iter46_public_task_protocol_effect_execution_with_assembled_executor/RESULT.md`.

## Verification Plan

1. Enumerate the same six frozen task-condition pairs.
2. For each pair, produce a command-binding record with:
   - pair id,
   - task id,
   - condition id,
   - exact public config,
   - exact provider overlay config or a recorded reason no provider overlay can bind,
   - exact future command,
   - raw artifact destination,
   - cost/call stats source,
   - redaction scan source,
   - receipt expectation,
   - runner lifecycle expectation.
3. Keep provider model calls at `0`.
4. Keep provider spend at `$0.00`.
5. Do not start a cloud runner.
6. Do not request or use GPU.
7. Do not modify Sentinel-named resources.
8. Audit that no pair was dropped, duplicated, renamed, or silently converted from provider-backed
   to deterministic/no-provider execution.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- exactly six task-condition command-binding records exist,
- every record names either a concrete provider-backed config/overlay or an explicit blocking
  incompatibility,
- provider-backed records include the Vertex model config and cost limit path,
- no record claims provider-backed execution through a public config that lacks the provider
  overlay,
- the harness plan is updated or wrapped so a future paid gate can run only the audited command
  surface,
- provider model API calls remain `0`,
- provider spend remains `$0.00`,
- no cloud runner starts,
- no GPU is used,
- no Sentinel-named resource is modified,
- no benchmark, leaderboard, SWE-bench, production, live-domain, model-superiority, or
  state-of-the-art result is claimed.

## Falsifiers

Publish blocked/null evidence if:

- any pair cannot be represented as a concrete provider-backed command,
- the public task surface and provider overlay semantics conflict,
- the harness cannot be safely wrapped without exposing credentials or identifiers,
- artifact, cost, redaction, lifecycle, receipt, or metric destinations are missing.

Publish a quality failure, not a clean pass, if:

- a pair is dropped, renamed, duplicated, or silently skipped,
- a deterministic/no-provider command is labeled provider-backed,
- provider calls or spend occur in this recovery gate,
- a cloud runner starts,
- GPU is requested or used,
- Sentinel-named resources are modified,
- unsupported benchmark/model/production claims appear.

## Scope Boundary

This is a command-binding recovery gate. It is not a provider-backed six-pair execution, not a
leaderboard run, not a SWE-bench result, not a production/live-domain verification, and not a
general model-superiority or state-of-the-art claim.
