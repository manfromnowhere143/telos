# Iteration 26 - Own-Tail Redundancy Mutation Guard Result

Status: `PASS`

## Result

The own-tail redundancy mutation guard passed.

The verifier started from the `iter24` changed candidate, confirmed the clean candidate still passed
all four frozen cases under `tail_remains_occupied`, then created a compound own-tail mutant that
removed both protection paths identified by `iter25`:

- direct own-tail protection: `my_body` became `my_body[:-1]`,
- self-snake fallback protection: our own snake was excluded from the later `board.snakes` loop.

The compound mutant failed the own occupied-tail target case. The observed safe moves for
`own-tail-left-occupied-risk` became `up,left,right`, so the forbidden occupied-tail move reappeared
and the verifier detected the regression. The non-tail controls still passed.

## What Passed

- No provider, API, GPU, or cloud spend occurred.
- The clean `iter24` candidate imported locally and passed all four frozen cases.
- The compound own-tail mutant failed `own-tail-left-occupied-risk`.
- The compound own-tail mutant left the non-tail controls passing.
- The opponent-tail case still passed, keeping the failure localized to the compound own-tail
  mutation.
- The verifier recorded the exact tail-occupancy assumption: `tail_remains_occupied`.
- Command output, proof artifacts, compound mutant, review, learning record, and receipt are
  committed.

## Claim Boundary

This resolves the specific `iter25` verifier-design caveat: a direct own-tail mutation alone was not
enough because another protection path remained. The compound mutant proves the occupied-tail
verifier catches the intended own-tail regression once both paths are removed.

This is still a local verifier-strength result for a changed candidate. It does not rewrite the
historical `iter21` provider submission or claim benchmark performance.

## What This Does Not Claim

- This does not claim a CodeClash leaderboard result.
- This does not claim a SWE-bench result.
- No production/live-domain behavior changed.
- No provider model was called in this gate.
- This does not prove general BattleSnake strength or general autonomous-agent reliability.

## Evidence

- Summary: [`proof/run_summary.json`](proof/run_summary.json)
- Redundancy report: [`proof/redundancy_report.json`](proof/redundancy_report.json)
- Compound mutant: [`proof/mutants/own_tail_compound_exclusion.py`](proof/mutants/own_tail_compound_exclusion.py)
- Compound manifest: [`proof/mutants/own_tail_compound_manifest.json`](proof/mutants/own_tail_compound_manifest.json)
- Command output: [`proof/command_output.txt`](proof/command_output.txt)
- Review: [`proof/review.md`](proof/review.md)
- Learning record: [`proof/learning_record.json`](proof/learning_record.json)
- Receipt: [`proof/valid/receipt_own_tail_redundancy_mutation_guard.json`](proof/valid/receipt_own_tail_redundancy_mutation_guard.json)

## Next Gate

Run `iter27_semantic_claim_boundary_matrix`: publish a machine-checkable matrix that separates
original provider logic, changed candidates, failed gates, and verifier-strength evidence.
