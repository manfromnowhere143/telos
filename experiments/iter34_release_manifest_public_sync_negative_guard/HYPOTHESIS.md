# Iteration 34 - Release Manifest Public Sync Negative Guard

Status: pre-registered, result pending.

## Purpose

The `iter33` public-sync guard keeps public prose aligned with the release manifest. This gate
should prove that the public-sync guard rejects deliberately malformed public-prose fixtures before
that guard is treated as stable.

## Frozen Input

- Public-sync report:
  `experiments/iter33_release_manifest_public_sync_guard/proof/public_sync_report.json`.
- Public-sync verifier: `scripts/verify_release_manifest_public_sync_guard.py`.
- Public prose files: `README.md`, `docs/REPORT.md`, `docs/NEXT_PHASE.md`, and `CONTINUITY.md`.
- Provider/model: no provider call allowed for this gate.
- Compute: local CPU only.

## Verification Plan

Generate malformed copies of public prose without mutating real public prose. The negative guard
must prove the public-sync checks reject fixtures covering:

- missing release-manifest references,
- hidden failed/null gates,
- changed-candidate/original-provider conflation,
- original `iter21` occupied-tail overclaim,
- leaderboard or SWE-bench result overclaim.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- no provider, API, GPU, or cloud spend occurs,
- the real public prose still passes the public-sync guard,
- every malformed public-prose fixture fails for the expected reason,
- fixture files remain separate from real public prose,
- command output and proof artifacts are committed,
- no leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.

## Falsifiers

Publish blocked/null evidence if:

- the public-sync report cannot be loaded,
- fixtures cannot be evaluated without mutating real public prose.

Publish a quality failure, not a clean pass, if:

- any malformed public-prose fixture passes,
- public prose can bypass the release manifest,
- failed/null gates can be hidden,
- original provider logic and changed candidate logic can be conflated,
- forbidden benchmark or production claims can be added without audit failure.

## Scope Boundary

This is a negative-fixture guard for public documentation. It is not a provider rerun, not a
benchmark result, and not a production/live-domain verification.
