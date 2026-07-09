# Iteration 25 - Tail Safety Mutation Guard

Status: pre-registered, result pending.

## Purpose

Prove the `iter24` occupied-tail verifier is not merely passing by construction. `iter24` showed a
changed candidate can pass the four local tail-safety cases under `tail_remains_occupied`, while the
original `iter21` logic still fails the occupied-tail cases.

This gate should mutate the `iter24` candidate back toward tail-excluding checks and verify that the
occupied-tail cases fail again.

## Frozen Input

- Source proof: `experiments/iter24_tail_safety_control/proof/`.
- Candidate source: `experiments/iter24_tail_safety_control/proof/candidate/main.py`.
- Tail safety report: `experiments/iter24_tail_safety_control/proof/tail_safety_report.json`.
- Provider/model: no provider call allowed for this gate.
- Compute: local CPU only.

## Verification Plan

Build a local mutation harness that starts from the `iter24` candidate and creates targeted mutants:

- own-tail exclusion mutant: revert `my_body` back to `my_body[:-1]`,
- opponent-tail exclusion mutant: revert `snake['body']` back to `snake['body'][:-1]`.

The clean `iter24` candidate must still pass all four tail-safety cases. Each targeted mutant must
fail the corresponding occupied-tail case family while preserving enough controls to show the
failure is about tail occupancy, not a broken harness.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- no provider, API, GPU, or cloud spend occurs,
- the clean `iter24` candidate imports locally and passes the four frozen cases,
- the own-tail exclusion mutant fails the own occupied-tail case,
- the opponent-tail exclusion mutant fails the opponent occupied-tail case,
- the verifier records the exact tail-occupancy assumption,
- command output and proof artifacts are committed,
- no leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.

## Falsifiers

Publish blocked/null evidence if:

- the candidate source cannot be loaded locally,
- the harness cannot create targeted tail-exclusion mutants without changing the test cases,
- the harness cannot state the tail-occupancy assumption.

Publish a quality failure, not a clean pass, if:

- a targeted tail-exclusion mutant still passes its occupied-tail target case,
- the clean candidate no longer passes the frozen cases,
- the result hides which source was mutated,
- the result treats provider game score as verifier evidence.

## Scope Boundary

This is a local mutation guard for the `iter24` tail-safety verifier. It is not a provider rerun, not
a benchmark result, and not a production/live-domain verification.
