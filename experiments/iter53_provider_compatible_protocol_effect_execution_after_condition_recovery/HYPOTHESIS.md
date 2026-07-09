# Iteration 53 - Provider-Compatible Protocol-Effect Execution After Condition Recovery

Status: pre-registered, result pending.

## Purpose

Run the smallest honest paid external-value pilot only after `iter52` proves the baseline and Telos
rows are distinct runtime conditions.

The question is narrow:

> On the frozen provider-compatible BattleSnake PvP slice, does the Telos receipt-enforced condition
> change verified-completion evidence relative to the baseline raw-evidence condition?

This is not a leaderboard run, not a SWE-bench score, not a production/live-domain result, not a
model-superiority result, and not a state-of-the-art claim.

## Frozen Input

- Iter52 recovery summary:
  `experiments/iter52_provider_condition_runtime_separation_recovery/proof/run_summary.json`.
- Iter52 condition plan:
  `experiments/iter52_provider_condition_runtime_separation_recovery/proof/condition_runtime_separation_plan.json`.
- Iter52 recovered overlay:
  `experiments/iter52_provider_condition_runtime_separation_recovery/proof/recovered_overlay/`.
- Refrozen provider-compatible slice:
  `experiments/iter48_provider_compatible_protocol_effect_slice_refreeze/proof/provider_compatible_slice.json`.

## Execution Envelope

The gate may execute only the two selected BattleSnake PvP condition rows:

- `baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml`,
- `telos-receipt-enforced-completion-evidence__configs-test-battlesnake-pvp-test-yaml`.

All four historical Dummy/deterministic-edit pairs remain rejected and unattempted.

Hard ceilings:

- provider model invocations: `<= 16`,
- provider spend: `<= $10.00`,
- GPU use: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- cloud runner: Telos-named ephemeral non-GPU runner only after preflight, with teardown proof.

## Required Evidence

The proof packet must include:

1. preflight showing iter52 passed and no excluded pair is selected,
2. exact commands for both condition rows,
3. raw logs, metadata, trajectory when available, diff scope, and arena/test result for each row,
4. provider call and cost counts from committed metadata,
5. redaction scan over all committed raw artifacts,
6. Telos receipt artifact and successful `python3 scripts/validate_receipts.py` output for the
   Telos row before verified completion is accepted,
7. teardown proof for any Telos cloud runner created by the gate,
8. exact primary and secondary metric counts,
9. human-readable adversarial review,
10. machine-readable run summary with artifact hashes.

## Metrics

Primary metric:

- verified-completion rate over the two frozen condition rows.

Secondary metrics:

- proxy-pass receipt-fail rate,
- unsupported-claim rate,
- over-edit rate,
- evidence-missing rate,
- audit minutes per task,
- false-positive and false-negative audit counts,
- model API calls per pair,
- provider cost per pair.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- iter52 is a clean pass,
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

- iter52 proof is missing, blocked, failed, or not validated,
- provider credentials or runner readiness are insufficient before execution,
- exact cost/call capture cannot be committed safely,
- redaction cannot prove artifacts are secret-safe,
- Telos receipt validation cannot run before completion acceptance.

Publish a quality failure if:

- any excluded historical pair is attempted,
- provider calls exceed `16`,
- provider spend exceeds `$10.00`,
- any GPU is used,
- any Sentinel-named resource is modified,
- committed artifacts contain credential, account, project, service-account, VM, or zone residue,
- unsupported benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only a bounded two-row provider-compatible protocol-effect pilot
with exact evidence counts. It may not claim a benchmark result, SWE-bench score, leaderboard
position, production/live-domain behavior, model superiority, or state-of-the-art result.
