# Iteration 18 - Provider Behavior Depth Control Result

Status: `PASS`

## Result

The provider-backed CodeClash behavior-depth control passed with a recorded process caveat.

The run kept the same provider-smoke shape as `iter17`: Google Vertex AI `gemini-3.1-pro-preview-customtools`, `global` routing, the same CodeClash BattleSnake smoke, the same dedicated ephemeral runner pattern, and the same budget ceiling. The new intervention required one additional behavior-depth improvement beyond board-boundary checks while preserving final workspace and source-style hygiene.

Preflight returned HTTP `200`, CodeClash exited `0`, `p1` submitted, and the trajectory records `6` model API calls with `$0.036876` reported model cost. The final submitted diff modified only `README_agent.md` and `main.py`; no helper, scratch, cache, generated, or secret-risk file remained.

## What Passed

- Dedicated-runner Vertex preflight passed with HTTP `200`.
- The provider-backed CodeClash run completed with exit code `0`.
- `p1` produced a provider trajectory and submitted.
- `p1` stayed below the `$25` ceiling.
- The final submitted diff contains no `patch.py`, `patch2.py`, or other helper residue.
- The final submitted diff contains no added trailing whitespace.
- The agent ran `git diff --check`, saw two trailing-whitespace errors, fixed them, and reran `git diff --check` with return code `0` before submission.
- The final `main.py` diff includes Step 1 board-boundary checks and Step 2 self-collision prevention.
- The proof bundle is sanitized before commit.
- The ephemeral VM was deleted after artifact collection.

## Process Caveat

The trajectory does not show `git status --short`, even though the prompt asked for workspace inspection. The final changed-file set is still reconstructable from CodeClash `changes_r1.json` and is limited to `README_agent.md` and `main.py`, so this does not hide a helper-file residue issue. The next gate should make the final inspection command explicit and require `git status --short && git diff --check` immediately before submission.

## What This Does Not Claim

- No CodeClash leaderboard result is claimed.
- No SWE-bench result is claimed.
- No production/live-domain behavior changed.
- The one-game score is context only, not model-capability evidence.
- The run does not prove the edit is optimal or generally robust.
- The self-collision implementation is basic and conservative; it is not a claim of strong BattleSnake play.

## Evidence

- Summary: [`proof/run_summary.json`](proof/run_summary.json)
- Preflight: [`proof/preflight.json`](proof/preflight.json)
- Diff summary: [`proof/diff_summary.md`](proof/diff_summary.md)
- Review: [`proof/review.md`](proof/review.md)
- Provider trajectory:
  [`proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708180156/players/p1/p1_r1.traj.json`](proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708180156/players/p1/p1_r1.traj.json)
- Provider changes:
  [`proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708180156/players/p1/changes_r1.json`](proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708180156/players/p1/changes_r1.json)
- Redacted run log: [`proof/raw/codeclash/telos-codeclash-provider-run.log`](proof/raw/codeclash/telos-codeclash-provider-run.log)
- Receipt: [`proof/valid/receipt_provider_behavior_depth_control.json`](proof/valid/receipt_provider_behavior_depth_control.json)

## Next Gate

Run `iter19_provider_final_inspection_control`: keep the same behavior-depth target and require an explicit final `git status --short && git diff --check` after all fixes and immediately before submission.
