# Iteration 23 - Tail Semantics Falsification

Status: pre-registered, result pending.

## Purpose

Test the caveat recorded in `iter21`: the submitted implementation excludes self and opponent tails
from collision checks. That may be safe when tails vacate, but it can be unsafe when a tail does not
move. This gate checks the caveat directly instead of expanding the claim.

This is a falsification gate, not a provider rerun. A clean result may be a failure/null if the
submitted behavior permits a move into a tail cell under a state where that tail should remain
occupied.

## Frozen Input

- Source proof: `experiments/iter21_opponent_collision_control/proof/`.
- Reconstructed submitted bot:
  `experiments/iter21_opponent_collision_control/proof/reconstructed/main.py`.
- Prior semantic suite:
  `experiments/iter21_opponent_collision_control/proof/semantic_report.json`.
- Provider/model: no provider call allowed for this gate.
- Compute: local CPU only.

## Verification Plan

Build a local semantic harness that creates tail-risk fixtures:

- own-tail occupied-risk case,
- opponent-tail occupied-risk case,
- one control case where a non-tail body segment remains correctly unsafe.

The verifier must state its tail-occupancy assumption explicitly. If the submitted bot selects a
tail cell under an occupied-tail assumption, publish that as a quality failure or null result, not as
a pass.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- no provider, API, GPU, or cloud spend occurs,
- the reconstructed bot imports locally,
- the verifier records the exact tail-occupancy assumption,
- the submitted bot does not select an occupied self-tail or opponent-tail cell when safer
  alternatives exist,
- command output and proof artifacts are committed,
- no leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.

## Falsifiers

Publish blocked/null evidence if:

- the reconstructed `iter21` bot cannot be loaded locally,
- the harness cannot encode a tail-occupancy assumption without changing submitted logic.

Publish a quality failure, not a clean pass, if:

- the bot can select an occupied self-tail cell when safer alternatives exist,
- the bot can select an occupied opponent-tail cell when safer alternatives exist,
- the result hides the tail-assumption boundary,
- the result treats provider game score as verifier evidence.

## Scope Boundary

This gate tests only the recorded tail-exclusion caveat. It is not a provider rerun, not a benchmark
result, and not a production/live-domain verification.
