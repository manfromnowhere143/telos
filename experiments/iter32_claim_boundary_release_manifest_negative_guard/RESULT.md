# Iteration 32 - Claim Boundary Release Manifest Negative Guard Result

Status: `PASS`

## Result

The claim-boundary release-manifest negative guard passed.

The real `iter31` release manifest still passed its audit. Five generated malformed manifest
fixtures were then evaluated, and all five failed for the expected reasons:

| fixture | detected error code |
|---|---|
| `stale_artifact_hash` | `stale_artifact_hash` |
| `hidden_failed_null_rows` | `hidden_failed_null_rows` |
| `candidate_original_conflation` | `candidate_original_conflation` |
| `forbidden_claim_made` | `forbidden_claim_made` |
| `missing_source_artifact` | `missing_source_artifact` |

## What Passed

- No provider, API, GPU, or cloud spend occurred.
- The real release manifest still passed its audit.
- Every malformed manifest fixture failed for the expected reason.
- Fixture manifests are separate proof artifacts and did not mutate the real manifest.
- No leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.

## Claim Boundary

This gate tests the release-manifest audit. It does not add behavior evidence, does not rerun
CodeClash, and does not convert local semantic gates into a benchmark result.

## What This Does Not Claim

- This does not claim a CodeClash leaderboard result.
- This does not claim a SWE-bench result.
- No production/live-domain behavior changed.
- No provider model was called in this gate.
- This does not prove general BattleSnake strength or general autonomous-agent reliability.

## Evidence

- Summary: [`proof/run_summary.json`](proof/run_summary.json)
- Negative guard report: [`proof/negative_guard_report.json`](proof/negative_guard_report.json)
- Fixtures: [`proof/fixtures`](proof/fixtures)
- Command output: [`proof/command_output.txt`](proof/command_output.txt)
- Review: [`proof/review.md`](proof/review.md)
- Learning record: [`proof/learning_record.json`](proof/learning_record.json)
- Receipt: [`proof/valid/receipt_claim_boundary_release_manifest_negative_guard.json`](proof/valid/receipt_claim_boundary_release_manifest_negative_guard.json)

## Next Gate

Run `iter33_release_manifest_public_sync_guard`: verify public prose points to the release manifest
as the reviewer entry point without bypassing its claim boundaries.
