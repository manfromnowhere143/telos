# Iteration 31 - Claim Boundary Release Manifest

Status: pre-registered, result pending.

## Purpose

The semantic evidence chain now includes a claim-boundary matrix, public prose guards, negative
fixtures, and a schema guard. This gate should publish a reviewer-facing release manifest that ties
those artifacts together without making a new benchmark or behavior claim.

## Frozen Input

- Claim matrix: `experiments/iter27_semantic_claim_boundary_matrix/proof/claim_boundary_matrix.json`.
- Public-claim guard report:
  `experiments/iter28_public_claim_surface_guard/proof/public_claim_surface_report.json`.
- Negative guard report:
  `experiments/iter29_public_claim_surface_negative_guard/proof/negative_guard_report.json`.
- Schema guard report:
  `experiments/iter30_boundary_matrix_schema_guard/proof/schema_guard_report.json`.
- Provider/model: no provider call allowed for this gate.
- Compute: local CPU only.

## Verification Plan

Create a machine-readable release manifest for the claim-boundary proof packet. The manifest must
list the source proof artifacts, hashes, statuses, claim boundaries, null/failure rows, and
forbidden claim classes. A local audit must verify that:

- every referenced artifact exists,
- recorded hashes match current files,
- `iter23` and `iter25` remain visible as failed/null gates,
- the changed `iter24` candidate is not conflated with original `iter21` provider logic,
- the manifest does not claim leaderboard, SWE-bench, production/live-domain, or
  model-superiority evidence.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- no provider, API, GPU, or cloud spend occurs,
- the release manifest validates against committed proof artifacts,
- the manifest includes the explicit failed/null gates,
- all artifact hashes match,
- command output and proof artifacts are committed,
- no leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.

## Falsifiers

Publish blocked/null evidence if:

- required source artifacts cannot be loaded,
- the manifest cannot be generated without changing prior proof artifacts.

Publish a quality failure, not a clean pass, if:

- any manifest hash is stale,
- failed/null gates are hidden,
- original provider logic and changed candidate logic are conflated,
- the manifest widens the claim beyond committed local evidence.

## Scope Boundary

This is a release-manifest and reviewer-navigation gate. It is not a provider rerun, not a
benchmark result, and not a production/live-domain verification.
