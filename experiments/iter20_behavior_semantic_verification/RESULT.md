# Iteration 20 - Behavior Semantic Verification Result

Status: `PASS`

## Result

The deterministic semantic verifier passed.

It reconstructed the `iter19` submitted `main.py` from the committed
`changes_r1.json` artifact, imported that reconstructed file locally, and inspected the submitted
bot's safe-move set by replacing only `random.choice` with a probe. The submitted boundary and
self-collision logic was not changed by the verifier.

All eight targeted cases passed: four board-boundary cases and four own-body adjacency cases. This
was a local CPU verification with zero provider spend, zero provider API calls, no GPU use, and no
cloud runner.

## What Passed

- The submitted diff was reconstructed from committed `iter19` proof artifacts.
- Reconstructed files were limited to `README_agent.md` and `main.py`.
- The reconstructed `main.py` imported and exposed `move(game_state)`.
- The verifier recorded the observed safe-move list by probing `random.choice`.
- `boundary-left`, `boundary-right`, `boundary-down`, and `boundary-up` all excluded the forbidden
  out-of-bounds move.
- `self-left`, `self-right`, `self-down`, and `self-up` all excluded the forbidden own-body move.
- The semantic report, command output, review, learning record, and receipt are committed.

## Caveat

This result verifies only the eight pre-registered safety cases. It does not prove strong
BattleSnake play, food seeking, opponent collision avoidance, hazard handling, or general strategic
quality.

The `iter19` formatting caveat remains: the provider diff contains extra empty added blank lines.
That caveat is separate from the semantic behavior tested here.

## What This Does Not Claim

- This does not claim a CodeClash leaderboard result.
- This does not claim a SWE-bench result.
- No production/live-domain behavior changed.
- No provider model was called in this gate.
- The one-game score from `iter19` is not used as semantic correctness evidence.

## Evidence

- Summary: [`proof/run_summary.json`](proof/run_summary.json)
- Semantic report: [`proof/semantic_report.json`](proof/semantic_report.json)
- Command output: [`proof/command_output.txt`](proof/command_output.txt)
- Reconstructed `main.py`: [`proof/reconstructed/main.py`](proof/reconstructed/main.py)
- Review: [`proof/review.md`](proof/review.md)
- Receipt: [`proof/valid/receipt_behavior_semantic_verification.json`](proof/valid/receipt_behavior_semantic_verification.json)

## Next Gate

Run `iter21_opponent_collision_control`: expand from self-collision safety to opponent-collision
safety, while preserving the strict final-inspection and semantic-verification discipline from
`iter19` and `iter20`.
