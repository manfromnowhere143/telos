# Iteration 102 - Provider LLM Judge Differential Retry Recovery After Block

Status: pre-registered, result pending.

## Purpose

Recover from a blocked iter101 provider LLM-judge execution without hiding the paid evidence. This
is a zero-spend recovery gate.

## Execution Envelope

Hard ceilings:

- prerequisite: iter101 blocked evidence must validate cleanly,
- provider model invocations: `0`,
- provider spend: `$0.00`,
- LLM-judge execution: `0`,
- deterministic strategy rerun: `0`,
- row execution: `0`,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must validate the iter101 blocked result, classify the blocker from committed raw
artifacts, preserve all paid usage accounting, and decide whether a later retry is justified.
