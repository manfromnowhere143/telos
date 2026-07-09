# Iteration 27 - Semantic Claim Boundary Matrix Result

Status: `PASS`

## Result

The semantic claim-boundary matrix passed.

The matrix covers `iter20` through `iter26` and separates claims by subject under test:

- reconstructed original provider logic,
- changed candidate logic,
- verifier-harness strength evidence,
- failed/null evidence.

It keeps the two failed/null gates visible:

- `iter23_original_occupied_tail_falsification`,
- `iter25_tail_safety_mutation_guard_miss`.

It also records that original `iter21` occupied-tail safety is not claimed. The occupied-tail pass
belongs only to the changed `iter24` candidate, and the mutation-strength claims belong only to the
verifier-harness rows.

## What Passed

- No provider, API, GPU, or cloud spend occurred.
- The matrix includes `iter20` through `iter26`.
- Failed/null gates remain visible as failed/null.
- Original provider logic and changed candidate logic are not conflated.
- Evidence paths exist for every row.
- No leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.

## Matrix Summary

| claim id | subject | status |
|---|---|---|
| `iter20_original_boundary_self_semantics` | reconstructed original provider logic | pass |
| `iter21_original_opponent_body_semantics` | reconstructed original provider logic | pass |
| `iter22_original_semantic_mutation_guard` | verifier harness | pass |
| `iter23_original_occupied_tail_falsification` | reconstructed original provider logic | null |
| `iter24_changed_candidate_occupied_tail_control` | changed candidate | pass |
| `iter25_tail_safety_mutation_guard_miss` | verifier harness | null |
| `iter26_compound_own_tail_redundancy_guard` | verifier harness | pass |

## Claim Boundary

The matrix does not claim that the original `iter21` provider-submitted bot was occupied-tail safe.
It does not convert failed/null gates into clean passes. It does not use provider game score as
verifier evidence.

## What This Does Not Claim

- This does not claim a CodeClash leaderboard result.
- This does not claim a SWE-bench result.
- No production/live-domain behavior changed.
- No provider model was called in this gate.
- This does not prove general BattleSnake strength or general autonomous-agent reliability.

## Evidence

- Summary: [`proof/run_summary.json`](proof/run_summary.json)
- Claim matrix: [`proof/claim_boundary_matrix.json`](proof/claim_boundary_matrix.json)
- Command output: [`proof/command_output.txt`](proof/command_output.txt)
- Review: [`proof/review.md`](proof/review.md)
- Learning record: [`proof/learning_record.json`](proof/learning_record.json)
- Receipt: [`proof/valid/receipt_semantic_claim_boundary_matrix.json`](proof/valid/receipt_semantic_claim_boundary_matrix.json)

## Next Gate

Run `iter28_public_claim_surface_guard`: audit README/report prose against the claim-boundary matrix.
