# Iteration 60 - Provider Model Binding Recovery

Status: pre-registered, result pending.

## Purpose

Recover the exact provider model binding that blocked `iter59`.

`iter59` executed both selected provider-compatible BattleSnake rows, but both commands failed after
one provider invocation each because Vertex returned a redacted
`vertex_model_not_found_or_access_denied` error for the configured model. This gate may only repair
that named blocker. It may not execute a BattleSnake row or broaden the task slice.

This is not a leaderboard run, not a SWE-bench score, not a production/live-domain result, not a
model-superiority result, and not a state-of-the-art claim.

## Frozen Input

- Iter59 blocked run summary:
  `experiments/iter59_provider_compatible_paid_execution_after_dependency_recovery/proof/run_summary.json`.
- Iter59 protocol-effect report:
  `experiments/iter59_provider_compatible_paid_execution_after_dependency_recovery/proof/protocol_effect_report.json`.
- Iter54 command manifest:
  `experiments/iter54_provider_pair_executor_recovery/proof/command_manifest.json`.
- Iter54 overlay-copy manifest:
  `experiments/iter54_provider_pair_executor_recovery/proof/overlay_copy_manifest.json`.
- Refrozen provider-compatible slice:
  `experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/proof/provider_compatible_slice.json`.

## Execution Envelope

The gate may perform only model-binding recovery checks:

- inspect the pinned CodeClash provider config files and recovered overlays,
- query or probe provider model availability only as needed to select an accessible non-GPU model,
- update the local recovered provider config overlay only if the artifact records the before/after
  model binding and proves the selected model is accessible,
- run no BattleSnake condition row,
- execute no excluded historical pair,
- use no GPU,
- modify no Sentinel-named resource,
- make no production/live-domain mutation.

Hard ceilings:

- provider model invocations: `<= 2`,
- provider spend: `<= $0.05`,
- cloud runner: forbidden unless a later gate separately pre-registers it,
- BattleSnake row execution: forbidden.

## Required Evidence

The proof packet must include:

1. preflight showing iter59 is a clean blocked result with
   `vertex_model_not_found_or_access_denied`,
2. exact before/after model binding values,
3. exact provider probe command(s), if any, with redacted logs,
4. provider call and cost counts,
5. proof that zero BattleSnake rows and zero excluded pairs executed,
6. proof that no GPU, Sentinel resource, cloud runner, production/live-domain action, or overclaim
   occurred,
7. redaction scan over all committed artifacts,
8. human-readable adversarial review,
9. machine-readable run summary with artifact hashes,
10. a next gate that retries the same two selected BattleSnake rows only if this recovery passes.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- iter59 is a blocked result with `vertex_model_not_found_or_access_denied`,
- before/after model binding values are recorded,
- the selected replacement binding is accessible under the local ADC context,
- provider calls are `<= 2`,
- provider spend is `<= $0.05`,
- zero BattleSnake rows execute,
- zero excluded pairs execute,
- no GPU, Sentinel resource, cloud runner, production/live-domain mutation, or overclaim occurs,
- every committed artifact passes redaction.

## Falsifiers

Publish blocked evidence if:

- iter59 proof is missing, failed, or does not name `vertex_model_not_found_or_access_denied`,
- no accessible provider model binding can be identified inside the spend/call ceiling,
- exact cost/call evidence cannot be committed safely,
- redaction cannot prove artifacts are secret-safe.

Publish a quality failure if:

- any BattleSnake row executes,
- any excluded historical pair executes,
- provider calls exceed `2`,
- spend exceeds `$0.05`,
- any GPU is used,
- any Sentinel-named resource is modified,
- committed artifacts contain credential, account, project, service-account, VM, zone, token, or
  credential material,
- unsupported benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only that the provider model binding blocker was recovered for a
future retry of the same two-row pilot. It may not claim a protocol-effect result, benchmark result,
SWE-bench score, leaderboard position, production/live-domain behavior, model superiority, or
state-of-the-art result.
