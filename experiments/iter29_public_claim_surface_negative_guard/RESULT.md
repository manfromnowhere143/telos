# Iteration 29 - Public Claim Surface Negative Guard Result

Status: `PASS`

## Result

The public claim-surface negative guard passed.

The real public prose still passed the guard. Four generated overclaim fixtures were then evaluated,
and all four failed for the expected reasons:

| fixture | detected checks |
|---|---|
| `original_iter21_tail_overclaim` | `forbidden_claims:README.md`, `original_iter21_occupied_tail_not_claimed` |
| `hidden_nulls` | `required_snippets:README.md`, `required_snippets:CONTINUITY.md`, `matrix_nulls_visible_publicly` |
| `changed_candidate_conflated` | `required_snippets:README.md`, `required_snippets:docs/REPORT.md`, `changed_candidate_boundary_visible` |
| `benchmark_result_overclaim` | `forbidden_claims:README.md` |

## What Passed

- No provider, API, GPU, or cloud spend occurred.
- The real public prose still passed the guard.
- Every negative fixture failed for the expected reason.
- The exact overclaim checks are recorded for each fixture.
- Fixture prose is committed under proof artifacts and did not mutate real public prose.
- No leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.

## Claim Boundary

This gate tests the public documentation guard itself. It does not add behavior evidence. It proves
that known bad prose shapes are caught while the real public prose remains aligned with the
claim-boundary matrix.

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
- Receipt: [`proof/valid/receipt_public_claim_surface_negative_guard.json`](proof/valid/receipt_public_claim_surface_negative_guard.json)

## Next Gate

Run `iter30_boundary_matrix_schema_guard`: make the claim-boundary matrix schema explicit and
machine-validated.
