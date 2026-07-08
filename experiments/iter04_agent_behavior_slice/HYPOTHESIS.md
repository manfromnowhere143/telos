# Iteration 04 - Agent Behavior Slice

Status: pre-registered, result pending.

## Purpose

Freeze the smallest CodeClash run that introduces real agent behavior while preserving the Telos
receipt standard proven in `iter03`.

This gate selects the run. It does not claim a model score.

## Hypothesis

At least one public CodeClash configuration can introduce non-trivial agent behavior and still
remain cheap, reproducible, and receipt-checkable.

## Candidate Runs

Score these before running:

1. CodeClash `configs/test/battlesnake_pvp_test.yaml`: instant-submit mini agent versus dummy,
   one simulation.
2. CodeClash `configs/test/battlesnake_ladder_smoke.yaml`: instant-submit climber against one
   dummy rung.
3. A custom one-round CodeClash config derived from `configs/test/dummy.yaml` with a deterministic
   scripted edit agent.

## Bars

The gate passes only if it publishes:

- selected config and exact source commit,
- expected artifacts and receipt fields,
- cost and runtime boundary,
- first-run falsifier,
- reason it is stronger than the dummy-agent smoke.

## Falsifiers

Publish a null and stop if:

- every candidate requires provider API keys,
- the run cannot produce diff-scope evidence,
- the run only repeats dummy-agent behavior,
- the run is too expensive for a first real-agent smoke,
- the artifact contract cannot be stated before execution.

## Scope Boundary

No leaderboard score is claimed by this gate. No GPU run is authorized.
