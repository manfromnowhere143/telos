# Iteration 13 - Provider Model Pilot Retry After Access Recovery Result

Status: `PASS`

## Result

The provider-model CodeClash smoke passed after Vertex access recovery.

The run used the original selected model, `gemini-3.1-pro-preview-customtools`, from an ephemeral
Google Compute Engine VM attached to the dedicated Telos runner identity. The preflight reached the
same Vertex endpoint with HTTP `200`, then the frozen one-round, one-simulation BattleSnake
CodeClash task completed with exit code `0`.

This is a provider-smoke result, not a leaderboard, SWE-bench, production, or general model
capability result.

## What Passed

- Dedicated-runner Vertex preflight passed with HTTP `200`.
- CodeClash completed the frozen BattleSnake provider smoke.
- `p1` produced a Mini-SWE-Agent trajectory.
- `p1` submitted with exit status `Submitted`.
- `p1` recorded `5` model API calls.
- `p1` recorded model cost `$0.030392000000000002`, below the frozen `$25` ceiling.
- `p1` changed `main.py`, added `README_agent.md`, and left `patch.py`.
- The ephemeral VM was deleted after artifact collection.

## What The Agent Did

The provider-backed agent made a small BattleSnake edit: it implemented the board-boundary check in
`main.py` so moves that would leave the board are marked unsafe. It also added a short
`README_agent.md` note.

The agent left `patch.py`, the helper script it used to edit `main.py`. That is not hidden; it is
recorded as a diff-hygiene issue for the next offline review gate.

## What This Does Not Claim

- No CodeClash leaderboard result is claimed.
- No SWE-bench result is claimed.
- No production/live-domain behavior changed.
- The one-game score is context only, not evidence of model superiority.
- The run does not prove the edit is optimal or generally robust.

## Evidence

- Summary: [`proof/run_summary.json`](proof/run_summary.json)
- Preflight: [`proof/preflight.json`](proof/preflight.json)
- Diff summary: [`proof/diff_summary.md`](proof/diff_summary.md)
- Provider trajectory:
  [`proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708155545/players/p1/p1_r1.traj.json`](proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708155545/players/p1/p1_r1.traj.json)
- Provider changes:
  [`proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708155545/players/p1/changes_r1.json`](proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708155545/players/p1/changes_r1.json)
- Redacted run log: [`proof/raw/codeclash/telos-codeclash-provider-run.log`](proof/raw/codeclash/telos-codeclash-provider-run.log)
- Receipt: [`proof/valid/receipt_provider_model_pilot_after_access.json`](proof/valid/receipt_provider_model_pilot_after_access.json)
- Review: [`proof/review.md`](proof/review.md)
- Learning record: [`proof/learning_record.json`](proof/learning_record.json)

## Next Gate

Run `iter14_provider_diff_quality_review` before spending on another provider run. The next gate is
offline: replay the `p1` diff against the task intent, check the helper-file hygiene issue, and
decide whether the receipt protocol needs a stricter diff-quality bar.
