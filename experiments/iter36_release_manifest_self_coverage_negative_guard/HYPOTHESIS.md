# Iteration 36 - Release Manifest Self-Coverage Negative Guard

Status: pre-registered, result pending.

## Purpose

`iter35` should publish a self-coverage report for the release-manifest reviewer packet. This gate
will test that the self-coverage audit is not only checking the happy path by evaluating malformed
self-coverage fixtures.

## Frozen Input

- Self-coverage report:
  `experiments/iter35_release_manifest_self_coverage_guard/proof/self_coverage_report.json`.
- Source proof packets from `iter31` through `iter34`.
- Provider/model: no provider call allowed for this gate.
- Compute: local CPU only.

## Verification Plan

Create negative fixtures that mutate copies of the self-coverage report or its source summaries.
The guard must verify that each malformed fixture fails for the expected reason while the real
`iter35` self-coverage report still passes.

Fixtures should cover at least:

- missing a required `iter31` through `iter34` self-verification gate,
- stale artifact hash,
- hidden failed/null gates,
- changed-candidate/original-provider conflation,
- forbidden leaderboard, SWE-bench, production/live-domain, or model-superiority claim.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- no provider, API, GPU, or cloud spend occurs,
- the real `iter35` self-coverage report still passes,
- every malformed fixture fails for the expected reason,
- fixture files remain separate from real proof artifacts,
- command output and proof artifacts are committed,
- no leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.

## Falsifiers

Publish blocked/null evidence if:

- the `iter35` self-coverage report cannot be loaded,
- fixtures cannot be generated without mutating real proof artifacts.

Publish a quality failure, not a clean pass, if:

- real self-coverage no longer passes,
- any malformed fixture passes,
- any fixture mutates source proof artifacts,
- the result widens the claim beyond committed local evidence.

## Scope Boundary

This is a negative-fixture guard for self-coverage validation. It is not a provider rerun, not a
benchmark result, and not a production/live-domain verification.
