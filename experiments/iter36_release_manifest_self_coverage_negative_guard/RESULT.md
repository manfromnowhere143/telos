# Iteration 36 - Release Manifest Self-Coverage Negative Guard Result

Status: `PASS`

## Result

The release-manifest self-coverage negative guard passed.

The real `iter35` self-coverage report still passed. Five generated malformed self-coverage report
fixtures were then evaluated, and all five failed for the expected reasons:

| fixture | detected failures |
|---|---|
| `missing_self_verification_gate` | missing `iter34` gate, wrong gate count |
| `stale_artifact_hash` | stale `iter31` summary hash |
| `hidden_failed_nulls` | failed/null gates hidden |
| `candidate_original_conflation` | changed-candidate boundary hidden |
| `forbidden_benchmark_claim` | forbidden leaderboard or SWE-bench claim |

## What Passed

- No provider, API, GPU, or cloud spend occurred.
- The real `iter35` self-coverage report still passed.
- Every malformed self-coverage fixture failed for the expected reason.
- Fixture files are committed under proof artifacts and did not mutate real proof artifacts.
- No leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.

## Claim Boundary

This gate tests the self-coverage guard itself. It does not add behavior evidence, does not rerun
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
- Receipt: [`proof/valid/receipt_release_manifest_self_coverage_negative_guard.json`](proof/valid/receipt_release_manifest_self_coverage_negative_guard.json)

## Next Gate

Run `iter37_release_manifest_self_coverage_public_sync_guard`: verify public prose surfaces the
self-coverage report and negative guard without bypassing the release manifest or widening claims.
