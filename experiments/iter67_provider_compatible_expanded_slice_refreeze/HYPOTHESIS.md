# Iteration 67 - Provider-Compatible Expanded Slice Refreeze

Status: pre-registered, result pending.

## Purpose

Use the measured `iter66` two-row result to decide and freeze the smallest legitimate expanded
provider-compatible protocol-effect slice. This gate does not execute provider rows. It selects the
next task set, commands, metrics, exclusions, and claim boundary before any additional paid run.

`iter66` is a real bounded provider-backed pilot: both selected BattleSnake rows executed, both
baseline and Telos had verified-completion evidence, the Telos receipt validated, the primary
Telos-minus-baseline verified-completion delta was `0`, 8 provider calls occurred, and CodeClash
metadata cost was `$0.059378`. That is not enough for a benchmark/model/state-of-the-art claim.
The next honest step is to freeze a broader slice only if compatibility and evidence controls are
concrete before spend.

## Execution Envelope

This gate is local-only.

Hard ceilings:

- provider model invocations: `0`,
- provider spend: `$0.00`,
- row execution: forbidden,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

## Required Evidence

The proof packet must include:

1. machine-readable read of the `iter66` primary and secondary metrics,
2. compatibility survey over available CodeClash task surfaces and prior exclusions,
3. exact proposed expanded slice rows or a no-expansion decision,
4. command materialization plan for each selected row,
5. exclusion reasons for every candidate not selected,
6. provider/API and spend ceilings for the next paid gate,
7. raw artifact, receipt, redaction, and audit plan,
8. human-readable adversarial review,
9. machine-readable run summary with artifact hashes,
10. valid Telos receipt for this local slice-freeze gate.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- iter66 proof receipt and audit pass,
- the expanded slice decision is explicit and machine-readable,
- every selected row has a concrete command plan and receipt/audit plan,
- every excluded row has a concrete compatibility or validity reason,
- provider calls remain `0`,
- provider spend remains `$0.00`,
- no row, GPU, cloud runner, Sentinel mutation, production/live-domain mutation, or overclaim
  occurs.

## Falsifiers

Publish blocked/null evidence if:

- iter66 proof or audit evidence is missing,
- available task-surface metadata cannot be read,
- compatibility cannot be determined without running provider rows,
- no expanded slice can be selected without changing task semantics or prompt conditions.

Publish a quality failure if:

- any provider call, provider spend, row execution, GPU, cloud runner, Sentinel mutation,
  production/live-domain mutation, or excluded-pair execution occurs,
- selected rows lack command, receipt, redaction, cost, or artifact plans,
- unsupported benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only that the next provider-compatible slice is frozen before
execution, or that expansion is not currently justified under the evidence controls. It may not
claim benchmark performance, model superiority, production/live-domain behavior, leaderboard
standing, or state-of-the-art status.
