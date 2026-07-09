# Iteration 26 - Own-Tail Redundancy Mutation Guard

Status: pre-registered, result pending.

## Purpose

Respond to the `iter25` mutation-guard failure without hiding it. The own-tail exclusion mutant did
not fail its target case because the `iter24` candidate has redundant own-tail protection: after the
direct own-body check, it also iterates through `board.snakes`, which includes our own snake.

This gate should create a compound own-tail mutant that removes both protection paths and prove that
the occupied-tail verifier catches the intended own-tail regression.

## Frozen Input

- Source proof: `experiments/iter25_tail_safety_mutation_guard/proof/`.
- Candidate source: `experiments/iter24_tail_safety_control/proof/candidate/main.py`.
- Mutation report: `experiments/iter25_tail_safety_mutation_guard/proof/mutation_report.json`.
- Provider/model: no provider call allowed for this gate.
- Compute: local CPU only.

## Verification Plan

Build a local mutation harness that starts from the `iter24` changed candidate and creates one
compound own-tail mutant:

- revert `my_body` back to `my_body[:-1]`, and
- exclude our own snake from the later `board.snakes` collision loop.

The clean candidate must still pass all four frozen cases. The compound own-tail mutant must fail
the own occupied-tail case while the non-tail controls still pass.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- no provider, API, GPU, or cloud spend occurs,
- the clean `iter24` candidate imports locally and passes the four frozen cases,
- the compound own-tail mutant fails `own-tail-left-occupied-risk`,
- the compound own-tail mutant leaves the non-tail controls passing,
- the verifier records the exact tail-occupancy assumption,
- command output and proof artifacts are committed,
- no leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.

## Falsifiers

Publish blocked/null evidence if:

- the candidate source cannot be loaded locally,
- the compound mutant cannot be created without changing the test cases,
- the harness cannot state the tail-occupancy assumption.

Publish a quality failure, not a clean pass, if:

- the compound own-tail mutant still passes the own occupied-tail target case,
- the clean candidate no longer passes the frozen cases,
- the result hides that this is a compound mutant,
- the result treats provider game score as verifier evidence.

## Scope Boundary

This is a local mutation guard for the own-tail redundancy found in `iter25`. It is not a provider
rerun, not a benchmark result, and not a production/live-domain verification.
