# Iteration 15 - Provider Strict Diff Rerun Result

Status: `FAIL`

## Result

The provider-backed CodeClash rerun executed successfully, but it did not earn a clean pass under
the strict diff-quality bar from `iter14`.

The concrete execution path recovered after the Vertex location was made explicit as `global`:
preflight returned HTTP `200`, CodeClash exited `0`, `p1` submitted, and the provider trajectory
records `5` model API calls with `$0.037882` reported model cost.

The strict quality bar failed because the submitted diff left two unrequested helper files:
`patch.py` and `patch2.py`. Under the `iter14` decision, that is a quality failure, not a clean
provider-smoke pass.

## What Passed

- Dedicated-runner Vertex preflight passed with HTTP `200`.
- The frozen provider-backed CodeClash run completed with exit code `0`.
- `p1` produced a provider trajectory and submitted.
- `p1` stayed below the `$25` ceiling.
- The proof bundle is sanitized before commit.
- The ephemeral VM was deleted after artifact collection.

## What Failed

- Strict diff-quality status is `fail_unjustified_helper_files`.
- `p1` modified `README_agent.md`, `main.py`, `patch.py`, and `patch2.py`.
- `patch.py` and `patch2.py` are helper residue in the final submitted workspace.
- Therefore this is not a clean pass.

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
  [`proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708165140/players/p1/p1_r1.traj.json`](proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708165140/players/p1/p1_r1.traj.json)
- Provider changes:
  [`proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708165140/players/p1/changes_r1.json`](proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708165140/players/p1/changes_r1.json)
- Redacted run log: [`proof/raw/codeclash/telos-codeclash-provider-run.log`](proof/raw/codeclash/telos-codeclash-provider-run.log)
- Receipt: [`proof/valid/receipt_provider_strict_diff_rerun.json`](proof/valid/receipt_provider_strict_diff_rerun.json)

## Next Gate

Run `iter16_provider_workspace_hygiene_control`: keep the same provider-smoke shape, but add an
explicit workspace-hygiene control that requires scratch work to be deleted or kept outside the
submitted repository before final submission.
