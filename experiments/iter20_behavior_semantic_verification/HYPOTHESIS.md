# Iteration 20 - Behavior Semantic Verification

Status: pre-registered, result pending.

## Purpose

Verify the behavior claimed by the provider-submitted `iter19` diff with deterministic local tests
instead of relying on diff shape, one-game score, or provider prose.

This is not a provider rerun and not a leaderboard attempt. It is a zero-provider-spend verifier
gate: reconstruct the submitted `main.py` behavior and test whether the boundary and self-collision
safety cases actually change the move-safety outcome as intended.

## Frozen Input

- Source proof: `experiments/iter19_provider_final_inspection_control/proof/`.
- Submitted diff:
  `experiments/iter19_provider_final_inspection_control/proof/raw/codeclash/PvpTournament.BattleSnake.r1.s1.p2.p1.p2.260708185232/players/p1/changes_r1.json`.
- Target files in submitted diff: `README_agent.md`, `main.py`.
- Provider/model: no provider call allowed for this gate.
- Compute: local CPU only unless the verifier itself fails for an infrastructure reason.

## Verification Plan

Build a small deterministic verifier that reconstructs the submitted `main.py` from the committed
provider diff and checks targeted BattleSnake states:

- boundary-left: a head at `x == 0` must not select left when safer alternatives exist,
- boundary-right: a head at `x == board_width - 1` must not select right when safer alternatives
  exist,
- boundary-down: a head at `y == 0` must not select down when safer alternatives exist,
- boundary-up: a head at `y == board_height - 1` must not select up when safer alternatives exist,
- self-left: an own-body segment immediately left of the head must make left unsafe,
- self-right: an own-body segment immediately right of the head must make right unsafe,
- self-down: an own-body segment immediately below the head must make down unsafe,
- self-up: an own-body segment immediately above the head must make up unsafe.

The verifier may control randomness if the starter bot chooses randomly among safe moves. It should
assert the forbidden move is never selected across a fixed deterministic set of seeds or by
inspecting the safe-move set if that is easier and faithful to the code.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- the submitted diff is reconstructed from committed `iter19` artifacts,
- no provider, API, GPU, or cloud spend occurs,
- the verifier runs locally and records command output,
- all eight targeted behavior cases pass,
- the result records any formatting caveat from `iter19` separately from semantic behavior,
- no leaderboard, SWE-bench, production, or live-domain claim is made.

## Falsifiers

Publish blocked/null evidence if:

- the submitted `iter19` diff cannot be reconstructed from committed artifacts,
- the verifier cannot import or execute the reconstructed bot without a harness failure,
- the random choice behavior cannot be controlled or tested without changing the submitted logic.

Publish a quality failure, not a clean pass, if:

- any boundary case can select the forbidden out-of-bounds move,
- any self-collision case can select the forbidden own-body move,
- the verifier mutates the submitted behavior instead of testing it,
- the result tries to use the one-game score as semantic correctness evidence.

## Scope Boundary

This is semantic verification for the narrow boundary and self-collision behavior in the submitted
provider diff. It is not a general BattleSnake-strength evaluation, not a leaderboard run, not a
SWE-bench result, and not a production/live-domain verification.
