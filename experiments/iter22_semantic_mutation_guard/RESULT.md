# Iteration 22 - Semantic Mutation Guard Result

Status: `PASS`

## Result

The semantic mutation guard passed.

The reconstructed `iter21` bot still passed all twelve frozen semantic cases. Three targeted mutants
were then generated locally from the same source without changing the test cases:

- `boundary_noop`: disabled board-boundary protection.
- `self_collision_noop`: disabled own-body protection.
- `opponent_collision_noop`: disabled opponent-body protection.

All three mutants were detected by the semantic suite. The boundary mutant failed all four boundary
cases, the self-collision mutant failed all four self-collision cases, and the opponent-collision
mutant failed all four opponent-collision cases.

## What Passed

- No provider, API, GPU, or cloud spend occurred.
- The clean reconstructed `iter21` bot passed all twelve frozen cases.
- The boundary mutant failed the corresponding boundary cases.
- The self-collision mutant failed the corresponding self-collision cases.
- The opponent-collision mutant failed the corresponding opponent-collision cases.
- The mutation report, command output, review, mutant sources, and receipt are committed.

## Caveat

The direct self-collision branch is not the only self-protection path in the submitted `iter21` bot:
the later `board.snakes` loop also includes our own snake. The self-collision mutant therefore
removes direct self protection and excludes the self snake from the later opponent loop so the mutant
actually creates the preregistered own-body regression.

## What This Does Not Claim

- This does not claim a CodeClash leaderboard result.
- This does not claim a SWE-bench result.
- No production/live-domain behavior changed.
- No provider model was called in this gate.
- This does not prove complete semantic coverage beyond the three targeted mutant families.

## Evidence

- Summary: [`proof/run_summary.json`](proof/run_summary.json)
- Mutation report: [`proof/mutation_report.json`](proof/mutation_report.json)
- Command output: [`proof/command_output.txt`](proof/command_output.txt)
- Review: [`proof/review.md`](proof/review.md)
- Mutants: [`proof/mutants`](proof/mutants)
- Receipt: [`proof/valid/receipt_semantic_mutation_guard.json`](proof/valid/receipt_semantic_mutation_guard.json)

## Next Gate

Run `iter23_tail_semantics_falsification`: test the recorded tail-exclusion caveat directly before
expanding the behavior claim.
