# Iteration 32 - Claim Boundary Release Manifest Negative Guard

Status: pre-registered, result pending.

## Purpose

The `iter31` release manifest makes the claim-boundary proof packet easier to audit. This gate
should prove the manifest audit fails deliberately malformed manifest fixtures before the manifest is
treated as a stable reviewer entry point.

## Frozen Input

- Release manifest:
  `experiments/iter31_claim_boundary_release_manifest/proof/claim_boundary_release_manifest.json`.
- Release-manifest audit:
  `scripts/audit_claim_boundary_release_manifest.py`.
- Provider/model: no provider call allowed for this gate.
- Compute: local CPU only.

## Verification Plan

Generate malformed copies of the release manifest without mutating the real manifest. The negative
guard must prove the audit rejects fixtures covering:

- stale artifact hashes,
- hidden failed/null rows,
- changed-candidate/original-provider conflation,
- forbidden claim classes marked as made,
- missing source artifacts.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- no provider, API, GPU, or cloud spend occurs,
- the real release manifest still passes its audit,
- every malformed manifest fixture fails for the expected reason,
- fixture files remain separate from the real manifest,
- command output and proof artifacts are committed,
- no leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.

## Falsifiers

Publish blocked/null evidence if:

- the release manifest cannot be loaded,
- fixtures cannot be evaluated without mutating the real manifest.

Publish a quality failure, not a clean pass, if:

- any malformed manifest fixture passes,
- stale hashes are accepted,
- failed/null rows can be hidden,
- original provider logic and changed candidate logic can be conflated,
- forbidden claim classes can be marked as made without audit failure.

## Scope Boundary

This is a negative-fixture guard for the release-manifest audit. It is not a provider rerun, not a
benchmark result, and not a production/live-domain verification.
