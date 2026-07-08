# Iteration 02 - Public Task Slice

Status: pre-registered, result pending.

## Purpose

Freeze the first public task slice for a real Telos agent-attempt experiment.

The previous gates selected the target family and validated the receipt protocol. This gate chooses
the smallest public task surface that can produce a real completion receipt without spending cloud
or model budget prematurely.

## Hypothesis

At least one public software-agent slice will clear the first-run bar:

- public source and license are inspectable,
- task can be run or replayed locally,
- artifacts can support a Telos receipt,
- first attempt can fail clearly,
- no cloud spend is required for the initial harness smoke.

## Candidate Slices

Score these candidates:

1. CodeClash single-arena smoke: one arena, one short round, local open-source harness.
2. SWE-bench Verified single-instance dry harness: one human-validated task, local patch/test
   artifact inspection.
3. Hybrid replay: use public CodeClash trajectory artifacts plus SWE-bench-style receipt fields.

## Bars

The gate passes only if it publishes:

- `proof/slice.json` with selected slice, source URL, license note, expected artifacts, and
  first-run command,
- `proof/decision.md` explaining why the selected slice is the cheapest faithful next run,
- a first-run falsifier,
- no secrets, no API keys, no cloud spend.

## Falsifiers

Publish a null and stop if:

- the selected task cannot be reproduced from public sources,
- the harness requires hidden credentials,
- the expected artifacts cannot support `test`, `artifact`, or `diff_scope` evidence,
- the first-run command is too expensive for a local smoke,
- the task slice is so small that it cannot falsify receipt quality.

## Scope Boundary

This gate selects the first public task slice. It does not run a model, claim a benchmark score, or
compare agents.
