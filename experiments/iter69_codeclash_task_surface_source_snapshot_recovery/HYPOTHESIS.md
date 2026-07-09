# Iteration 69 - CodeClash Task-Surface Source Snapshot Recovery

Status: pre-registered, result pending.

## Purpose

Recover the blocker named by `iter68`: the Dummy task surface is named in prior manifests but its
source config content is not committed, so provider-compatible adapters cannot be validated without
trusting uncommitted local checkout state.

This gate is local-only. It may snapshot required CodeClash task-source files from the pinned
checkout into a proof packet with hashes, but it must not execute rows, call a provider, or widen
the result claim.

## Execution Envelope

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

1. machine-readable read of the `iter68` blocked decision,
2. pinned CodeClash checkout path and commit, or a precise blocker if unavailable,
3. copied source snapshot for `configs/test/dummy.yaml`,
4. source hash and copied hash equality proof,
5. explicit statement that copied source files are task-surface evidence, not execution results,
6. redaction scan over copied files,
7. human-readable adversarial review,
8. machine-readable run summary with artifact hashes,
9. valid Telos receipt for this local source-snapshot gate.

## Clean-Pass Bar

The gate can pass only if:

- `iter68` is present and blocked for `committed_dummy_source_surface_missing`,
- the pinned checkout is readable at a recorded commit,
- every copied source snapshot hash matches its source file,
- provider calls, spend, row execution, GPU, cloud runner startup, Sentinel mutation, and
  live-domain mutation remain zero,
- no benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art result is claimed.

## Falsifiers

Publish blocked/null evidence if:

- the pinned checkout is unavailable or dirty in a way that prevents a trustworthy snapshot,
- source/copy hashes do not match,
- copied task source cannot be distinguished from generated adapter output.

Publish a quality failure if:

- any provider call, provider spend, row execution, GPU, cloud runner startup, Sentinel mutation,
  production/live-domain mutation, or hidden task mutation occurs,
- unsupported benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only that required CodeClash source-task files are committed as
snapshot evidence for later adapter recovery. It may not claim benchmark performance, model
superiority, production/live-domain behavior, leaderboard standing, or state-of-the-art status.
