# Iteration 29 - Public Claim Surface Negative Guard

Status: pre-registered, result pending.

## Purpose

Prove the `iter28` public-claim guard is not only passing the current prose because it is too weak.
The next gate should feed known bad public-claim fixtures into the guard logic and verify those
fixtures fail.

## Frozen Input

- Public-claim report: `experiments/iter28_public_claim_surface_guard/proof/public_claim_surface_report.json`.
- Claim matrix: `experiments/iter27_semantic_claim_boundary_matrix/proof/claim_boundary_matrix.json`.
- Provider/model: no provider call allowed for this gate.
- Compute: local CPU only.

## Verification Plan

Build local negative fixtures that contain known overclaims:

- original `iter21` occupied-tail safety claimed,
- failed/null gates hidden or relabeled as clean passes,
- changed-candidate evidence described as original provider-submitted behavior,
- benchmark or production claims inserted into public prose.

The guard must fail those fixtures while keeping the real public prose passing.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- no provider, API, GPU, or cloud spend occurs,
- the real public prose still passes the guard,
- every negative fixture fails for the expected reason,
- the guard records the exact overclaim detected for each fixture,
- command output and proof artifacts are committed,
- no leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.

## Falsifiers

Publish blocked/null evidence if:

- the `iter28` report or `iter27` matrix cannot be loaded,
- negative fixtures cannot be evaluated without mutating real public prose.

Publish a quality failure, not a clean pass, if:

- any overclaim fixture passes,
- the guard cannot distinguish real prose from fixture prose,
- the result widens into benchmark or production claims.

## Scope Boundary

This is a negative-fixture guard for public documentation checks. It is not a provider rerun, not a
benchmark result, and not a production/live-domain verification.
