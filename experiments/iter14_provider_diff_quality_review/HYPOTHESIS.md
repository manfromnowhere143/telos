# Iteration 14 - Provider Diff Quality Review

Status: pre-registered, result pending.

## Purpose

Review the first completed provider-backed CodeClash diff from `iter13` before spending on another
provider run.

The goal is to decide whether the Telos receipt protocol needs a stricter diff-quality bar for
provider-agent smokes. This gate is offline and must not call a model.

## Frozen Inputs

- Source result:
  `experiments/iter13_provider_model_pilot_retry_after_access_recovery/RESULT.md`.
- Provider trajectory:
  `experiments/iter13_provider_model_pilot_retry_after_access_recovery/proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708155545/players/p1/p1_r1.traj.json`.
- Provider diff:
  `experiments/iter13_provider_model_pilot_retry_after_access_recovery/proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708155545/players/p1/changes_r1.json`.
- Task prompt:
  `configs/test/telos_battlesnake_vertex_gemini_pilot.yaml` from the iter09 overlay.

## Bars

The gate passes only if all hold:

- no provider/model/API/GPU spend occurs,
- the review reconstructs the `p1` modified-file set and key diff hunks from committed artifacts,
- the review judges whether the `main.py` boundary edit satisfies the local task intent,
- the review judges whether retaining `patch.py` should be a future smoke-gate failure,
- the result publishes a concrete next-bar decision for future provider smokes,
- no leaderboard, SWE-bench, production, or live-domain claim is made.

## Falsifiers

Publish blocked/null evidence if:

- the committed `iter13` diff artifacts are insufficient to reconstruct the edit,
- the review would require another model call,
- the review cannot separate task-quality claims from game-score claims,
- the result would silently excuse the `patch.py` helper-file issue instead of deciding a future
  bar.

## Scope Boundary

This is a local evidence-quality review. It must not rerun CodeClash, call Vertex, call another
provider model, or change the provider smoke result.
