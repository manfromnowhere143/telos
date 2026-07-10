# Iteration 80 - Dummy Call-Ceiling Bounded Paid Retry After Recovery

Status: pre-registered, result pending.

## Purpose

Execute the smallest paid retry justified by iter79: only the two Dummy adapter rows from iter78,
with the per-row Mini-SWE-Agent global call ceiling raised from `8` to `16`. Iter79 classified both
iter78 Dummy failures as per-row global call-ceiling blockers and retained both deterministic-edit
rows as verified evidence that must not be rerun.

This gate is a bounded paid retry. It may make provider calls only for the two selected Dummy rows.
It must not rerun deterministic-edit rows, rerun retained BattleSnake rows, start a cloud runner,
use GPU, mutate Sentinel-named resources, mutate production/live-domain systems, or make
benchmark/model/SOTA claims.

## Execution Envelope

Hard ceilings:

- adapter rows to execute: `2`,
- selected rows:
  - `baseline-agent-completion-evidence__configs-test-dummy-yaml`,
  - `telos-receipt-enforced-completion-evidence__configs-test-dummy-yaml`,
- deterministic-edit rows to rerun: `0`,
- retained BattleSnake rows to rerun: `0`,
- per-row provider model invocation ceiling: `16`,
- total provider model invocation ceiling: `32`,
- per-row provider spend ceiling: `$2.50`,
- total provider spend ceiling: `$5.00`,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include:

1. receipt validation and audit validation of the iter79 recovery packet,
2. confirmation that iter78 deterministic-edit rows are retained and not rerun,
3. materialized provider-compatible Dummy-only overlays with recovered iter73 receipt prompt for
   the Telos row and a 16-call per-row ceiling,
4. raw command transcripts and copied CodeClash artifacts for exactly the two selected Dummy rows,
5. per-row provider call counts, costs, return codes, receipt status, and verified-completion
   status,
6. total provider calls and spend checked against the `32` call and `$5.00` ceilings,
7. redaction scan over committed proof artifacts,
8. explicit no-GPU/no-cloud/no-Sentinel/no-live-domain/no-benchmark claim boundary.

## Clean-Pass Bar

The gate can pass only if:

- iter79 proof validates as a clean recovery packet,
- exactly the two selected Dummy rows execute,
- no deterministic-edit or BattleSnake rows rerun,
- total provider calls are at or below `32`,
- total provider spend is at or below `$5.00`,
- every receipt-required row has a valid Telos receipt before verified completion is accepted,
- raw artifacts, metadata, transcripts, and receipt artifacts are committed,
- no token, project identifier, service-account, or credential material is committed,
- no GPU, cloud runner startup, Sentinel mutation, or live-domain mutation occurs,
- no benchmark/model/SOTA claim is made.

## Falsifiers

Publish blocked/null evidence if:

- iter79 receipt validation or audit fails,
- ADC, Docker, CodeClash pinning, or runtime overlay materialization fails before row execution,
- either selected Dummy row returns nonzero, times out, lacks raw evidence, or fails receipt
  validation when required,
- verified-completion evidence remains unavailable after the bounded call-ceiling recovery.

Publish a quality failure if:

- any unselected row executes,
- deterministic-edit or BattleSnake rows rerun,
- provider calls exceed `32`,
- provider spend exceeds `$5.00`,
- token, project identifier, service-account, or credential material is committed,
- GPU, cloud runner startup, Sentinel mutation, production/live-domain mutation, or hidden task
  mutation occurs,
- unsupported benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only a bounded Dummy adapter-validation retry result under the
iter79 call-ceiling recovery plan. It may not claim benchmark performance, model superiority,
production/live-domain behavior, leaderboard standing, SWE-bench standing, or state-of-the-art
status.
