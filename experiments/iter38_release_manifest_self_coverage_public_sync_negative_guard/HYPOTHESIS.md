# Iteration 38 - Release Manifest Self-Coverage Public Sync Negative Guard

Status: pre-registered, result pending.

## Purpose

`iter37` should verify that public prose surfaces the release-manifest self-coverage layer while
keeping the release manifest as the claim-boundary reviewer entry point. This gate will prove that
the public-sync guard rejects malformed public prose.

## Frozen Input

- Public-sync report:
  `experiments/iter37_release_manifest_self_coverage_public_sync_guard/proof/public_sync_report.json`.
- Source public prose: `README.md`, `docs/REPORT.md`, `docs/NEXT_PHASE.md`, and `CONTINUITY.md`.
- Source proof artifacts from `iter31`, `iter35`, and `iter36`.
- Provider/model: no provider call allowed for this gate.
- Compute: local CPU only.

## Verification Plan

Create malformed public-prose fixtures that remove or corrupt the release-manifest and
self-coverage references. The guard must verify that real public prose still passes and that each
malformed fixture fails for the expected reason.

Fixtures should cover at least:

- missing release-manifest reference,
- missing self-coverage report reference,
- missing self-coverage negative guard reference,
- hidden `iter23` or `iter25` failed/null evidence,
- changed-candidate/original-provider conflation,
- forbidden leaderboard, SWE-bench, production/live-domain, or model-superiority claim.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- no provider, API, GPU, or cloud spend occurs,
- the real public prose still passes the self-coverage public-sync guard,
- every malformed public-prose fixture fails for the expected reason,
- fixture files remain separate from real public prose,
- command output and proof artifacts are committed,
- no leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.

## Falsifiers

Publish blocked/null evidence if:

- the `iter37` public-sync report cannot be loaded,
- fixtures cannot be generated without mutating real public prose or proof artifacts.

Publish a quality failure, not a clean pass, if:

- real public prose no longer passes,
- any malformed fixture passes,
- any fixture mutates real public prose,
- the result widens the claim beyond committed local evidence.

## Scope Boundary

This is a negative-fixture guard for public prose. It is not a provider rerun, not a benchmark
result, and not a production/live-domain verification.
