# Iteration 16 - Provider Workspace Hygiene Control Result

Status: `PASS`

## Result

The provider-backed CodeClash workspace-hygiene control passed.

The run kept the same provider-smoke shape as `iter15`: Google Vertex AI
`gemini-3.1-pro-preview-customtools`, `global` routing, the same CodeClash BattleSnake smoke, the
same dedicated ephemeral runner pattern, and the same budget ceiling. The only intervention was the
pre-registered workspace-hygiene prompt control.

Preflight returned HTTP `200`, CodeClash exited `0`, `p1` submitted, and the trajectory records `6`
model API calls with `$0.035064` reported model cost. The final submitted diff modified only
`README_agent.md` and `main.py`; no helper, scratch, cache, generated, or secret-risk file remained.

## What Passed

- Dedicated-runner Vertex preflight passed with HTTP `200`.
- The provider-backed CodeClash run completed with exit code `0`.
- `p1` produced a provider trajectory and submitted.
- `p1` stayed below the `$25` ceiling.
- The agent used `/tmp/patch.py` as scratch, removed it, and ran `git status --short` before
  submitting.
- The final submitted diff contains no `patch.py`, `patch2.py`, or other helper residue.
- The proof bundle is sanitized before commit.
- The ephemeral VM was deleted after artifact collection.

## Caveat

The submitted `main.py` diff contains one whitespace-only added blank line. That does not recreate
the iter15 helper-file failure, so this gate passes the workspace-hygiene bar. It is still a concrete
quality gap, and the next gate should add a source-style check such as `git diff --check` before
submission.

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
  [`proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708171352/players/p1/p1_r1.traj.json`](proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708171352/players/p1/p1_r1.traj.json)
- Provider changes:
  [`proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708171352/players/p1/changes_r1.json`](proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708171352/players/p1/changes_r1.json)
- Redacted run log: [`proof/raw/codeclash/telos-codeclash-provider-run.log`](proof/raw/codeclash/telos-codeclash-provider-run.log)
- Receipt: [`proof/valid/receipt_provider_workspace_hygiene_control.json`](proof/valid/receipt_provider_workspace_hygiene_control.json)

## Next Gate

Run `iter17_provider_lint_hygiene_control`: keep the same workspace-hygiene control and add a
source-style hygiene requirement so the submitted diff must also pass `git diff --check` or an
equivalent trailing-whitespace check.
