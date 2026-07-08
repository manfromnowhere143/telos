# Iteration 21 - Opponent Collision Control

Status: pre-registered, result pending.

## Purpose

Test whether the provider-backed agent can extend the verified BattleSnake safety behavior from
own-body collision avoidance to opponent-body collision avoidance without regressing the process
controls already established in `iter19` and `iter20`.

This is a behavior-expansion gate, not a leaderboard run. The target is one narrow capability:
mark moves unsafe when they would enter a cell occupied by another snake body segment.

## Frozen Input

- Source baseline: the same CodeClash BattleSnake provider-smoke task family used in `iter19`.
- Required process controls: final `git status --short && git diff --check` after all fixes and
  before submission.
- Required semantic controls: deterministic local cases, modeled after `iter20`, must verify the
  new opponent-collision behavior before any clean pass is published.
- Provider/model: use the existing Vertex Gemini provider path only after local preflight passes.
- Budget ceiling: `$25` provider spend and 45 minutes wall-clock.

## Verification Plan

Run the provider-backed task with an instruction to implement the next safety layer:

- preserve the verified board-boundary checks,
- preserve the verified self-collision checks,
- add opponent-body collision checks,
- avoid helper, scratch, cache, generated, or secret-risk files in the submitted diff,
- run final workspace inspection before submission.

After the provider run, reconstruct the submitted diff from committed artifacts and run deterministic
semantic cases for opponent collision in all four directions. The verifier must also confirm the
`iter20` boundary and self-collision cases still pass.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- provider preflight succeeds without committing credential, account, or project identifiers,
- CodeClash exits successfully under the frozen runner, task, model, and budget,
- the submitted diff is reconstructable from committed artifacts,
- the submitted diff has no helper-file residue or `git diff --check` failure,
- the trajectory records final `git status --short && git diff --check` after all fixes and before
  submission,
- deterministic semantic tests pass for boundary, self-collision, and opponent-collision cases,
- no leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.

## Falsifiers

Publish blocked/null evidence if:

- provider preflight fails before spend,
- CodeClash cannot run the frozen provider path,
- the submitted diff cannot be reconstructed,
- semantic verification cannot import the reconstructed bot without changing submitted logic.

Publish a quality failure, not a clean pass, if:

- the submitted diff leaves helper, scratch, cache, generated, or secret-risk residue,
- final workspace inspection is missing or occurs before the final fix,
- any boundary or self-collision case regresses,
- any opponent-collision case can select the forbidden occupied-cell move,
- the result uses one-game score as model-capability evidence.

## Scope Boundary

This gate is about one safety behavior in a small BattleSnake task. It is not a general autonomous
agent benchmark result, not a CodeClash leaderboard claim, not a SWE-bench result, and not a
production/live-domain verification.
