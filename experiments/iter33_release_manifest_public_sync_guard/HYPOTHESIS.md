# Iteration 33 - Release Manifest Public Sync Guard

Status: pre-registered, result pending.

## Purpose

The release manifest now has a negative guard. This gate should make sure public prose uses that
manifest as the reviewer entry point without bypassing the manifest's claim boundaries.

## Frozen Input

- Release manifest:
  `experiments/iter31_claim_boundary_release_manifest/proof/claim_boundary_release_manifest.json`.
- Release-manifest negative guard report:
  `experiments/iter32_claim_boundary_release_manifest_negative_guard/proof/negative_guard_report.json`.
- Public prose files: `README.md`, `docs/REPORT.md`, `docs/NEXT_PHASE.md`, and `CONTINUITY.md`.
- Provider/model: no provider call allowed for this gate.
- Compute: local CPU only.

## Verification Plan

Create a local guard that checks public prose against the release manifest. The guard must verify
that public prose:

- references the release manifest as the review entry point,
- keeps `iter23` and `iter25` visible as failed/null evidence,
- keeps the changed `iter24` candidate separate from original `iter21` provider logic,
- does not claim leaderboard, SWE-bench, production/live-domain, model-superiority, or original
  `iter21` occupied-tail safety evidence.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- no provider, API, GPU, or cloud spend occurs,
- the release manifest and iter32 negative guard are valid source artifacts,
- every checked public prose file exists,
- public prose references the release manifest and stays inside its claim boundaries,
- command output and proof artifacts are committed,
- no leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.

## Falsifiers

Publish blocked/null evidence if:

- required source artifacts cannot be loaded,
- public prose cannot be checked without mutating the release manifest.

Publish a quality failure, not a clean pass, if:

- public prose bypasses the release manifest,
- failed/null gates are hidden,
- original provider logic and changed candidate logic are conflated,
- public prose widens the claim beyond committed local evidence.

## Scope Boundary

This is a public documentation synchronization guard. It is not a provider rerun, not a benchmark
result, and not a production/live-domain verification.
