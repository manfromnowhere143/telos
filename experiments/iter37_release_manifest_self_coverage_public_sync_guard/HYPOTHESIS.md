# Iteration 37 - Release Manifest Self-Coverage Public Sync Guard

Status: pre-registered, result pending.

## Purpose

`iter35` and `iter36` add a self-coverage report and negative-fixture guard for the
release-manifest reviewer packet. Public prose should now surface that self-coverage layer without
bypassing the original release manifest or hiding failed/null evidence.

## Frozen Input

- Release manifest:
  `experiments/iter31_claim_boundary_release_manifest/proof/claim_boundary_release_manifest.json`.
- Self-coverage report:
  `experiments/iter35_release_manifest_self_coverage_guard/proof/self_coverage_report.json`.
- Self-coverage negative guard:
  `experiments/iter36_release_manifest_self_coverage_negative_guard/proof/negative_guard_report.json`.
- Public prose: `README.md`, `docs/REPORT.md`, `docs/NEXT_PHASE.md`, and `CONTINUITY.md`.
- Provider/model: no provider call allowed for this gate.
- Compute: local CPU only.

## Verification Plan

Create a local public-sync report that checks public prose against both the release manifest and the
self-coverage proof packet. The report must verify that:

- public prose references the release manifest as the claim-boundary reviewer entry point,
- public prose references the self-coverage result and active self-coverage negative guard,
- `iter23` and `iter25` remain visible as failed/null evidence,
- the changed `iter24` candidate remains separate from original `iter21` provider logic,
- no new leaderboard, SWE-bench, production/live-domain, or model-superiority claim is made.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- no provider, API, GPU, or cloud spend occurs,
- the release manifest, self-coverage report, and self-coverage negative guard load locally,
- all checked public prose files exist,
- public prose stays inside the claim boundaries,
- command output and proof artifacts are committed,
- no leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.

## Falsifiers

Publish blocked/null evidence if:

- required source artifacts cannot be loaded,
- public prose cannot be checked without mutating proof artifacts.

Publish a quality failure, not a clean pass, if:

- public prose hides the release manifest,
- public prose hides the self-coverage report or negative guard,
- failed/null gates are hidden,
- original provider logic and changed candidate logic are conflated,
- the report widens the claim beyond committed local evidence.

## Scope Boundary

This is a public documentation guard. It is not a provider rerun, not a benchmark result, and not a
production/live-domain verification.
