# Iteration 25 - Tail Safety Mutation Guard Result

Status: `FAIL`

## Result

The tail-safety mutation guard found a verifier-design caveat.

The clean `iter24` changed candidate still passed all four frozen cases under
`tail_remains_occupied`. The opponent-tail exclusion mutant was detected: it reintroduced
`snake['body'][:-1]`, and the opponent occupied-tail case failed as expected.

The own-tail exclusion mutant was not detected. Reverting only the direct own-body check from
`my_body` to `my_body[:-1]` did not make the own occupied-tail case fail, because the candidate also
iterates over `board.snakes`, which includes our own snake, and that later snake-body check still
blocked the own tail.

| mutation | target | status | failed cases |
|---|---|---|---|
| `own_tail_exclusion` | `own-tail-left-occupied-risk` | missed | none |
| `opponent_tail_exclusion` | `opponent-tail-left-occupied-risk` | detected | `opponent-tail-left-occupied-risk` |

## What Failed

- The pre-registered clean-pass bar required both targeted tail-exclusion mutants to be detected.
- The own-tail exclusion mutant escaped because another path still protected the own tail.
- The gate therefore cannot claim the mutation guard fully validates the occupied-tail verifier.

## What Still Passed

- No provider, API, GPU, or cloud spend occurred.
- The clean `iter24` candidate imported locally and passed all four frozen cases.
- The opponent-tail exclusion mutant failed the opponent occupied-tail case.
- Non-tail controls still passed for both mutants.
- The verifier recorded the exact tail-occupancy assumption: `tail_remains_occupied`.
- Command output, proof artifacts, mutants, review, learning record, and receipt are committed.

## Claim Boundary

This failure does not invalidate the `iter24` candidate pass. It narrows the verifier-strength
claim: a single direct own-body mutation is not enough to test own-tail regression because the
candidate has redundant self-snake protection through the later snake loop.

## What This Does Not Claim

- This does not claim a CodeClash leaderboard result.
- This does not claim a SWE-bench result.
- No production/live-domain behavior changed.
- No provider model was called in this gate.
- This does not prove general BattleSnake strength or general autonomous-agent reliability.

## Evidence

- Summary: [`proof/run_summary.json`](proof/run_summary.json)
- Mutation report: [`proof/mutation_report.json`](proof/mutation_report.json)
- Mutants: [`proof/mutants`](proof/mutants)
- Command output: [`proof/command_output.txt`](proof/command_output.txt)
- Review: [`proof/review.md`](proof/review.md)
- Learning record: [`proof/learning_record.json`](proof/learning_record.json)
- Receipt: [`proof/valid/receipt_tail_safety_mutation_guard.json`](proof/valid/receipt_tail_safety_mutation_guard.json)

## Next Gate

Run `iter26_own_tail_redundancy_mutation_guard`: remove both the direct own-tail check and the
self-snake fallback path so the own-tail mutation actually creates the intended regression.
