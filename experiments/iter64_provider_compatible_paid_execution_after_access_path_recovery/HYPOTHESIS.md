# Iteration 64 - Provider-Compatible Paid Execution After Access Path Recovery

Status: pre-registered, result pending.

## Purpose

Retry the exact two-row provider-compatible protocol-effect pilot only after `iter63` proved that
both current direct REST and LiteLLM access paths reach the selected Vertex global model.

The question remains:

> On the frozen provider-compatible BattleSnake PvP slice, does the Telos receipt-enforced
> condition change verified-completion evidence relative to the baseline raw-evidence condition?

This is not a leaderboard run, not a SWE-bench score, not a production/live-domain result, not a
model-superiority result, and not a state-of-the-art claim.

## Frozen Input

- Iter63 access-path recovery summary:
  `experiments/iter63_vertex_access_path_parity_recheck/proof/run_summary.json`.
- Iter63 direct REST probe:
  `experiments/iter63_vertex_access_path_parity_recheck/proof/direct_rest_probe.json`.
- Iter63 LiteLLM parity probe:
  `experiments/iter63_vertex_access_path_parity_recheck/proof/litellm_parity_probe.json`.
- Iter62 secret-safe bearer-token/header template:
  `experiments/iter62_vertex_bearer_token_path_recovery/proof/recovered_runtime_binding/bearer_token_path_binding.json`.
- Iter54 command manifest:
  `experiments/iter54_provider_pair_executor_recovery/proof/command_manifest.json`.
- Iter54 overlay-copy manifest:
  `experiments/iter54_provider_pair_executor_recovery/proof/overlay_copy_manifest.json`.
- Iter52 separated runtime overlays:
  `experiments/iter52_provider_condition_runtime_separation_recovery/proof/recovered_overlay/`.
- Refrozen provider-compatible slice:
  `experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/proof/provider_compatible_slice.json`.

## Execution Envelope

The gate may execute only the two selected BattleSnake PvP condition rows:

- `baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml`,
- `telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml`.

All four historical Dummy/deterministic-edit pairs remain rejected and unattempted.

The provider access path is frozen to the iter63-proven LiteLLM shape:

- `model_name`: `vertex_ai/gemini-3.1-pro-preview-customtools`,
- `vertex_location`: `global`,
- `vertex_project`: runtime env `TELOS_VERTEX_PROJECT`,
- `extra_headers.Authorization`: runtime env `Bearer ${TELOS_VERTEX_BEARER_TOKEN}`,
- `extra_headers.X-Goog-User-Project`: runtime env `TELOS_VERTEX_QUOTA_PROJECT`,
- token acquisition: `gcloud auth application-default print-access-token --quiet` with token output
  suppressed,
- committed artifacts must contain only placeholders or redacted values, never the token, project,
  account, service-account, VM, zone, or credential path.

Hard ceilings:

- provider model invocations: `<= 16`,
- provider spend: `<= $10.00`,
- GPU use: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- cloud runner: not needed for the local ADC-backed retry unless a preflight records a separate
  Telos-named non-GPU runner with teardown proof.

## Required Evidence

The proof packet must include:

1. preflight showing iter63 passed, both access-path probes passed, and no excluded pair is
   selected,
2. exact commands for both selected condition rows,
3. proof that the runtime Vertex project, bearer token, and quota project are injected only from
   environment and never committed,
4. raw logs, metadata, trajectory when available, diff scope, and arena/test result for each row,
5. provider call and cost counts from committed CodeClash metadata,
6. redaction scan over all committed raw artifacts,
7. Telos receipt artifact and successful `python3 scripts/validate_receipts.py` output for the
   Telos row before verified completion is accepted,
8. teardown proof for any Telos cloud runner created by the gate,
9. exact primary and secondary metric counts,
10. human-readable adversarial review,
11. machine-readable run summary with artifact hashes.

## Metrics

Primary metric:

- verified completion evidence difference: Telos verified-completion count minus baseline
  verified-completion count across the two frozen rows.

Secondary metrics:

- row task success,
- false completion or proxy-game detection,
- artifact completeness,
- provider calls,
- provider cost,
- latency when available,
- receipt-validation status,
- redaction status,
- excluded-pair execution count.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- iter63 is a clean pass with `blocker_classification=access_path_recovered`,
- exactly two selected BattleSnake condition rows execute,
- zero excluded pairs execute,
- provider calls are `<= 16`,
- provider spend is `<= $10.00`,
- no GPU is requested or used,
- no Sentinel-named resource is modified,
- every committed artifact passes redaction,
- the Telos row has a valid receipt before verified completion is accepted,
- any cloud runner started by this gate is torn down and recorded,
- metrics are exact counts, not prose-only interpretation,
- claim boundary forbids benchmark, leaderboard, SWE-bench, production/live-domain,
  model-superiority, and state-of-the-art claims.

## Falsifiers

Publish blocked/null evidence if:

- iter63 proof is missing, blocked, failed, or not validated,
- direct REST or LiteLLM access-path readiness regresses before row execution,
- provider credentials, Docker readiness, or CodeClash dependency readiness regresses before
  execution,
- exact cost/call capture cannot be committed safely,
- redaction cannot prove artifacts are secret-safe,
- Telos receipt validation cannot run before completion acceptance.

Publish a quality failure if:

- any excluded historical pair is attempted,
- provider calls exceed `16`,
- provider spend exceeds `$10.00`,
- any GPU is used,
- any Sentinel-named resource is modified,
- committed artifacts contain credential, account, project, service-account, VM, zone, token, or
  credential-path residue,
- unsupported benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only a bounded two-row provider-compatible protocol-effect pilot
with exact evidence counts. It may not claim a benchmark result, SWE-bench score, leaderboard
position, production/live-domain behavior, model superiority, or state-of-the-art result.
