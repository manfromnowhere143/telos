# Iteration 17 - Provider Lint Hygiene Control Result

Status: `PASS`

## Result

The provider-backed CodeClash workspace-and-lint-hygiene control passed.

The run kept the same provider-smoke shape as `iter16`: Google Vertex AI `gemini-3.1-pro-preview-customtools`, `global` routing, the same CodeClash BattleSnake smoke, the same dedicated ephemeral runner pattern, and the same budget ceiling. The only new intervention was the pre-registered source-style hygiene prompt control.

Preflight returned HTTP `200`, CodeClash exited `0`, `p1` submitted, and the trajectory records `5` model API calls with `$0.02864` reported model cost. The final submitted diff modified only `README_agent.md` and `main.py`; no helper, scratch, cache, generated, or secret-risk file remained.

## What Passed

- Dedicated-runner Vertex preflight passed with HTTP `200`.
- The provider-backed CodeClash run completed with exit code `0`.
- `p1` produced a provider trajectory and submitted.
- `p1` stayed below the `$25` ceiling.
- The agent used `/tmp/patch.py` as scratch, removed it, and ran `git status --short && git diff --check` before submitting.
- The combined pre-submit command returned code `0` and emitted no `git diff --check` whitespace errors.
- The final submitted diff contains no `patch.py`, `patch2.py`, or other helper residue.
- The final submitted diff contains no added trailing whitespace.
- The proof bundle is sanitized before commit.
- The ephemeral VM was deleted after artifact collection.

## Caveat

The submitted source edit remains shallow. It implements the local Step 1 boundary check in `main.py`; it does not implement self-collision handling, opponent collision handling, food strategy, or general game strength. That is the next concrete quality gap.

## What This Does Not Claim

- No CodeClash leaderboard result is claimed.
- No SWE-bench result is claimed.
- No production/live-domain behavior changed.
- The one-game score is context only, not model-capability evidence.
- The run does not prove the edit is optimal or generally robust.

## Evidence

- Summary: [`proof/run_summary.json`](proof/run_summary.json)
- Preflight: [`proof/preflight.json`](proof/preflight.json)
- Diff summary: [`proof/diff_summary.md`](proof/diff_summary.md)
- Review: [`proof/review.md`](proof/review.md)
- Provider trajectory:
  [`proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708173719/players/p1/p1_r1.traj.json`](proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708173719/players/p1/p1_r1.traj.json)
- Provider changes:
  [`proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708173719/players/p1/changes_r1.json`](proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708173719/players/p1/changes_r1.json)
- Redacted run log: [`proof/raw/codeclash/telos-codeclash-provider-run.log`](proof/raw/codeclash/telos-codeclash-provider-run.log)
- Receipt: [`proof/valid/receipt_provider_lint_hygiene_control.json`](proof/valid/receipt_provider_lint_hygiene_control.json)

## Next Gate

Run `iter18_provider_behavior_depth_control`: keep the same workspace and source-style hygiene controls, then require one additional narrow behavior-depth improvement beyond boundary checks, preferably self-collision prevention, or publish a null if the provider-backed agent cannot safely do it within the frozen command and budget limits.
