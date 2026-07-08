# Iteration 21 - Opponent Collision Control Result

Status: `PASS`

## Result

The provider-backed opponent-collision control passed.

Vertex preflight returned HTTP `200`. CodeClash exited `0`. `p1` submitted with `5` model API calls
and `$0.043329999999999994` reported model cost. The submitted diff changed only
`README_agent.md` and `main.py`.

The submitted `main.py` was reconstructed from committed artifacts and tested locally. All twelve deterministic semantic cases passed. The cases cover four board-boundary cases, four self-collision cases, and four opponent-body collision cases.

## What Passed

- Provider preflight passed before the CodeClash run.
- The ephemeral runner completed and was deleted after artifact collection.
- The submitted diff is limited to `README_agent.md` and `main.py`.
- The trajectory shows `/tmp/edit.py` scratch use without committed helper residue.
- The agent ran `git status --short && git diff --check`, saw a trailing-whitespace failure, fixed
  it, and reran `git status --short && git diff --check` with return code `0` before submission.
- The semantic verifier passed all boundary, self-collision, and opponent-collision cases.
- No binary round archives are committed.

## Caveats

The provider trajectory needed the same redaction-placeholder JSON repair seen in earlier provider
runs. The private field remains redacted; the committed trajectory is parseable; the repair is
recorded in `proof/run_summary.json`.

The submitted implementation excludes tails for self and opponent collision checks. The semantic
cases therefore place the forbidden adjacent body segment before the tail. This is a deliberate test
boundary, not a claim about all tail-movement edge cases.

## What This Does Not Claim

- This does not claim a CodeClash leaderboard result.
- This does not claim a SWE-bench result.
- No production/live-domain behavior changed.
- The one-game score is not model-capability evidence.
- This does not prove general BattleSnake strength or general autonomous-agent reliability.

## Evidence

- Summary: [`proof/run_summary.json`](proof/run_summary.json)
- Preflight: [`proof/preflight.json`](proof/preflight.json)
- Raw summary: [`proof/raw_summary.json`](proof/raw_summary.json)
- Semantic report: [`proof/semantic_report.json`](proof/semantic_report.json)
- Command output: [`proof/command_output.txt`](proof/command_output.txt)
- Diff summary: [`proof/diff_summary.md`](proof/diff_summary.md)
- Review: [`proof/review.md`](proof/review.md)
- Receipt: [`proof/valid/receipt_opponent_collision_control.json`](proof/valid/receipt_opponent_collision_control.json)

## Next Gate

Run `iter22_semantic_mutation_guard`: mutate the reconstructed behavior by removing boundary,
self-collision, and opponent-collision checks, and prove the semantic verifier fails those mutants.
