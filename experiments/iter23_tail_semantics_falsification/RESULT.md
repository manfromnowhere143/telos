# Iteration 23 - Tail Semantics Falsification Result

Status: `FAIL`

## Result

The tail-semantics falsification gate found a quality failure under the frozen
`tail_remains_occupied` assumption.

The verifier loaded the reconstructed `iter21` bot from committed proof artifacts and ran four
local CPU-only cases. The two non-tail controls passed, but both occupied-tail risk cases left the
forbidden `left` move in the observed safe-move list:

| case | status | observed safe moves |
|---|---|---|
| `own-tail-left-occupied-risk` | fail | `up,left,right` |
| `opponent-tail-left-occupied-risk` | fail | `up,left,right` |
| `own-non-tail-left-control` | pass | `up,right` |
| `opponent-non-tail-left-control` | pass | `up,right` |

The selected move was `up` in these runs because the harness probes `random.choice` deterministically
by returning the first safe move. That does not rescue the gate: the frozen bar fails if an occupied
self-tail or opponent-tail cell remains in the safe-move list while safer alternatives exist.

## What Failed

- The occupied self-tail risk case left `left` in the safe-move list.
- The occupied opponent-tail risk case left `left` in the safe-move list.
- The gate therefore cannot claim that the submitted `iter21` bot avoids all occupied tail cells.

## What Still Passed

- The reconstructed `iter21` bot imported locally.
- No provider, API, GPU, or cloud spend occurred.
- The verifier recorded the exact tail-occupancy assumption: `tail_remains_occupied`.
- The two non-tail controls still excluded the forbidden move.
- The proof artifacts, command output, review, learning record, and receipt are committed.

## What This Does Not Claim

- This does not invalidate the narrower `iter21` non-tail body collision result.
- This does not claim a CodeClash leaderboard result.
- This does not claim a SWE-bench result.
- No production/live-domain behavior changed.
- No provider model was called in this gate.
- The one-game provider score from earlier gates is not verifier evidence here.

## Evidence

- Summary: [`proof/run_summary.json`](proof/run_summary.json)
- Tail semantics report: [`proof/tail_semantics_report.json`](proof/tail_semantics_report.json)
- Command output: [`proof/command_output.txt`](proof/command_output.txt)
- Review: [`proof/review.md`](proof/review.md)
- Learning record: [`proof/learning_record.json`](proof/learning_record.json)
- Receipt: [`proof/valid/receipt_tail_semantics_falsification.json`](proof/valid/receipt_tail_semantics_falsification.json)

## Next Gate

Run `iter24_tail_safety_control`: pre-register a control that either models tail occupancy
explicitly or keeps the claim limited to non-tail body segments.
