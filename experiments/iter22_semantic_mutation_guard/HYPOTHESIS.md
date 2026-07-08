# Iteration 22 - Semantic Mutation Guard

Status: pre-registered, result pending.

## Purpose

Test the verifier, not the provider. `iter20` and `iter21` passed semantic cases, but a verifier that
never fails is not trustworthy. This gate checks whether the deterministic semantic suite catches
targeted regressions when boundary, self-collision, or opponent-collision logic is removed from the
reconstructed `iter21` bot.

## Frozen Input

- Source proof: `experiments/iter21_opponent_collision_control/proof/`.
- Reconstructed submitted bot:
  `experiments/iter21_opponent_collision_control/proof/reconstructed/main.py`.
- Semantic cases:
  `experiments/iter21_opponent_collision_control/proof/semantic_report.json`.
- Provider/model: no provider call allowed for this gate.
- Compute: local CPU only.

## Verification Plan

Build a local mutation harness that:

- loads the reconstructed `iter21` `main.py`,
- runs the clean semantic suite and confirms it still passes,
- creates targeted mutants that remove or bypass one safety layer at a time,
- reruns the same semantic cases against each mutant,
- records which cases fail for each mutant.

Minimum mutants:

- boundary mutant: allows one out-of-bounds move,
- self-collision mutant: allows one non-tail own-body move,
- opponent-collision mutant: allows one non-tail opponent-body move.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- no provider, API, GPU, or cloud spend occurs,
- the clean reconstructed bot still passes the twelve `iter21` semantic cases,
- each targeted mutant fails at least one corresponding semantic case,
- command output and mutation report are committed,
- no leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.

## Falsifiers

Publish blocked/null evidence if:

- the reconstructed `iter21` bot cannot be loaded locally,
- the clean reconstructed bot no longer passes the frozen semantic cases,
- the mutation harness cannot create meaningful targeted mutants without changing the test cases.

Publish a quality failure, not a clean pass, if:

- a boundary mutant passes all boundary cases,
- a self-collision mutant passes all self-collision cases,
- an opponent-collision mutant passes all opponent-collision cases,
- the result treats provider game score as verifier evidence.

## Scope Boundary

This gate validates the semantic verifier's failure sensitivity for the narrow BattleSnake safety
suite. It is not a provider rerun, not a benchmark result, and not a production/live-domain check.
