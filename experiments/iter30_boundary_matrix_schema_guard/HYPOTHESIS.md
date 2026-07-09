# Iteration 30 - Boundary Matrix Schema Guard

Status: pre-registered, result pending.

## Purpose

The claim-boundary matrix is now the source of truth for public semantic claims. This gate should
turn the matrix shape into an explicit schema guard so future rows remain structurally
machine-checkable.

## Frozen Input

- Claim matrix: `experiments/iter27_semantic_claim_boundary_matrix/proof/claim_boundary_matrix.json`.
- Negative guard report:
  `experiments/iter29_public_claim_surface_negative_guard/proof/negative_guard_report.json`.
- Provider/model: no provider call allowed for this gate.
- Compute: local CPU only.

## Verification Plan

Create a JSON schema or equivalent local validator for claim-boundary matrix rows. The guard must
validate the current matrix and fail intentionally malformed matrix fixtures, including:

- missing evidence paths,
- invalid status,
- original/candidate conflation,
- missing required no-claim exclusions,
- hidden failed/null rows.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- no provider, API, GPU, or cloud spend occurs,
- the current matrix validates,
- every malformed matrix fixture fails for the expected reason,
- the schema or validator is committed,
- command output and proof artifacts are committed,
- no leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.

## Falsifiers

Publish blocked/null evidence if:

- the current matrix cannot be loaded,
- fixtures cannot be evaluated without mutating the real matrix.

Publish a quality failure, not a clean pass, if:

- the current matrix fails validation,
- any malformed matrix fixture passes,
- the validator allows original/candidate conflation,
- the validator allows failed/null rows to be hidden.

## Scope Boundary

This is a schema/validator guard for the claim-boundary matrix. It is not a provider rerun, not a
benchmark result, and not a production/live-domain verification.
