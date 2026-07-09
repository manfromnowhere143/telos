# Iteration 24 - Tail Safety Control Result

Status: `PASS`

## Result

The tail-safety control passed for a clearly labeled changed candidate under the explicit
`tail_remains_occupied` assumption.

The verifier ran the same four `iter23` cases against two separate logic paths:

- `original_iter21`: the reconstructed provider-submitted bot from `iter21`.
- `changed_candidate_tail_occupied`: a local candidate generated from that source with own and
  opponent tail cells included in collision checks.

The original logic still failed the same two occupied-tail cases from `iter23`, while both non-tail
controls passed. The changed candidate passed all four cases:

| case | candidate status | candidate safe moves |
|---|---|---|
| `own-tail-left-occupied-risk` | pass | `up,right` |
| `opponent-tail-left-occupied-risk` | pass | `up,right` |
| `own-non-tail-left-control` | pass | `up,right` |
| `opponent-non-tail-left-control` | pass | `up,right` |

## What Passed

- No provider, API, GPU, or cloud spend occurred.
- The verifier recorded the exact tail-occupancy assumption: `tail_remains_occupied`.
- The verifier kept original submitted logic separate from changed candidate logic.
- The original `iter21` tail failure was preserved and recorded.
- The changed candidate blocked both occupied-tail moves while preserving the non-tail controls.
- Command output, proof artifacts, candidate source, patch manifest, review, learning record, and
  receipt are committed.

## Candidate Boundary

The candidate source is committed at [`proof/candidate/main.py`](proof/candidate/main.py). It is not
the original `iter21` submission. The patch manifest at
[`proof/candidate/patch_manifest.json`](proof/candidate/patch_manifest.json) records the two
intended changes:

- `my_body[:-1]` became `my_body` for own-body checks.
- `snake['body'][:-1]` became `snake['body']` for snake-body checks.

This result supports only the local candidate under the occupied-tail assumption. It does not rewrite
the historical `iter21` result.

## What This Does Not Claim

- This does not claim the original `iter21` bot was occupied-tail safe.
- This does not claim a CodeClash leaderboard result.
- This does not claim a SWE-bench result.
- No production/live-domain behavior changed.
- No provider model was called in this gate.
- This does not prove general BattleSnake strength or general autonomous-agent reliability.

## Evidence

- Summary: [`proof/run_summary.json`](proof/run_summary.json)
- Tail safety report: [`proof/tail_safety_report.json`](proof/tail_safety_report.json)
- Candidate source: [`proof/candidate/main.py`](proof/candidate/main.py)
- Candidate patch manifest: [`proof/candidate/patch_manifest.json`](proof/candidate/patch_manifest.json)
- Command output: [`proof/command_output.txt`](proof/command_output.txt)
- Review: [`proof/review.md`](proof/review.md)
- Learning record: [`proof/learning_record.json`](proof/learning_record.json)
- Receipt: [`proof/valid/receipt_tail_safety_control.json`](proof/valid/receipt_tail_safety_control.json)

## Next Gate

Run `iter25_tail_safety_mutation_guard`: prove the occupied-tail verifier catches a candidate that
reverts to tail-excluding checks.
