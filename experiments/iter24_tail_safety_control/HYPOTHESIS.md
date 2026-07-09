# Iteration 24 - Tail Safety Control

Status: pre-registered, result pending.

## Purpose

Respond to the `iter23` quality failure without hiding it. The previous gate showed that the
reconstructed `iter21` bot leaves occupied self-tail and opponent-tail cells in the safe-move list
under an explicit `tail_remains_occupied` assumption, while non-tail controls still pass.

This gate should produce a bounded tail-safety result. A clean result can come from either:

1. an explicit local verifier that models tail occupancy and proves the candidate behavior blocks
   occupied tail cells when safer alternatives exist, or
2. a narrowed claim that remains limited to non-tail body segments and does not imply tail-cell
   safety.

## Frozen Input

- Source proof: `experiments/iter23_tail_semantics_falsification/proof/`.
- Tail failure report:
  `experiments/iter23_tail_semantics_falsification/proof/tail_semantics_report.json`.
- Reconstructed submitted bot:
  `experiments/iter21_opponent_collision_control/proof/reconstructed/main.py`.
- Provider/model: no provider call allowed for this gate unless a later pre-registration explicitly
  freezes a provider run and budget.
- Compute: local CPU only.

## Verification Plan

Build a local control that separates two claims:

- non-tail collision safety, already supported by `iter21` through `iter23`, and
- occupied-tail safety, which `iter23` falsified for the reconstructed `iter21` bot.

The verifier must keep the tail-occupancy assumption explicit in every artifact. If it tests a
changed candidate, the changed source must be committed as test input and must not be confused with
the originally submitted `iter21` logic.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- no provider, API, GPU, or cloud spend occurs,
- the verifier records whether it is testing original submitted logic or a changed candidate,
- the verifier records the exact tail-occupancy assumption,
- occupied-tail cases either pass under an explicit model or the published claim is narrowed to
  non-tail body segments only,
- command output and proof artifacts are committed,
- no leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.

## Falsifiers

Publish blocked/null evidence if:

- the source logic under test cannot be loaded locally,
- the harness cannot state the tail-occupancy assumption,
- the harness mutates submitted logic while presenting it as the original `iter21` bot.

Publish a quality failure, not a clean pass, if:

- the result claims occupied-tail safety while an occupied tail move remains in the safe-move list,
- the result hides whether original or changed logic was tested,
- the result treats provider game score as verifier evidence,
- the result widens from local semantic controls to benchmark or production claims.

## Scope Boundary

This gate is a local semantic control. It is not a provider rerun, not a benchmark result, and not a
production/live-domain verification.
