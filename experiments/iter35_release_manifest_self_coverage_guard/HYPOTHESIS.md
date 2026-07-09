# Iteration 35 - Release Manifest Self-Coverage Guard

Status: pre-registered, result pending.

## Purpose

The release manifest currently indexes the claim-boundary matrix and the earlier semantic proof
packet. Since `iter31` through `iter34` add manifest, negative-manifest, public-sync, and
public-sync-negative proof gates, this gate should verify that the reviewer packet accounts for
those self-verification artifacts without rewriting prior evidence.

## Frozen Input

- Release manifest:
  `experiments/iter31_claim_boundary_release_manifest/proof/claim_boundary_release_manifest.json`.
- Manifest and public-sync proof summaries from `iter31` through `iter34`.
- Provider/model: no provider call allowed for this gate.
- Compute: local CPU only.

## Verification Plan

Create a local self-coverage report for the release-manifest reviewer packet. The report must list
the `iter31` through `iter34` proof artifacts, hashes, statuses, and claim boundaries. It must
verify that:

- every referenced artifact exists,
- recorded hashes match current files,
- each self-verification gate is a clean local pass,
- failed/null gates from the original semantic chain remain visible,
- no new leaderboard, SWE-bench, production/live-domain, or model-superiority claim is made.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- no provider, API, GPU, or cloud spend occurs,
- the self-coverage report validates against committed proof artifacts,
- `iter31` through `iter34` are all represented with matching hashes,
- original failed/null gates remain visible,
- command output and proof artifacts are committed,
- no leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.

## Falsifiers

Publish blocked/null evidence if:

- required source artifacts cannot be loaded,
- self-coverage cannot be checked without mutating prior proof artifacts.

Publish a quality failure, not a clean pass, if:

- any self-coverage hash is stale,
- any self-verification gate is hidden,
- failed/null gates are hidden,
- the report widens the claim beyond committed local evidence.

## Scope Boundary

This is a self-coverage guard for the release-manifest reviewer packet. It is not a provider rerun,
not a benchmark result, and not a production/live-domain verification.
