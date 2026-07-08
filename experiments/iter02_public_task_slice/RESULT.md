# Iteration 02 - Public Task Slice Result

Status: `PASS`

## Result

The first public Telos slice is:

```text
codeclash_dummy_swebench_receipt_slice
```

It is a CodeClash-first slice with SWE-bench Verified receipt fields used as the supporting
artifact contract.

## Decision

Selected candidate:

```text
codeclash_dummy_tournament_plus_swebench_receipt_fields
```

This keeps the target aligned with the `iter00` decision instead of collapsing the work to
SWE-bench alone. The first executable public slice is the CodeClash dummy tournament config:

```text
configs/test/dummy.yaml
```

The supporting receipt substrate is pinned to one SWE-bench Verified row:

```text
astropy__astropy-12907
```

That supporting row provides issue text, base commit, patch hash, test-patch hash,
`FAIL_TO_PASS`, and `PASS_TO_PASS` structure for the first Telos receipt design.

## What Was Verified

- CodeClash public repository cloned and pinned.
- CodeClash license inspected as MIT.
- `uv` installed locally.
- CodeClash environment synced under Python 3.11.
- CodeClash non-Docker dummy-arena unit smoke passed.
- SWE-bench Verified dataset is public and ungated.
- SWE-bench Verified row 0 metadata and hashes were fetched from the public rows API.

## Concrete Blocker For The Tournament Run

The full no-LLM CodeClash dummy tournament was attempted, but Docker engine calls on this machine
timed out. The partial CodeClash log reached:

```text
Checking if container codeclash/dummy exists
```

This is not a benchmark failure and not a model result. It is an infrastructure precondition for
the next gate.

## First-Run Falsifier

The next gate fails if the CodeClash dummy tournament cannot produce:

- tournament logs,
- game logs,
- parsed round scores,
- a valid Telos receipt with `artifact`, `test`, and `diff_scope` evidence.

If local Docker remains unavailable, the next gate may use an isolated sandbox only after the
pre-registered run states the sandbox, expected receipts, and spend boundary.

## What This Does Not Claim

- No model has been evaluated.
- No CodeClash leaderboard result is claimed.
- No SWE-bench result is claimed.
- No cloud or GPU spend was used.

## Evidence

- Frozen slice: [`proof/slice.json`](proof/slice.json)
- Decision: [`proof/decision.md`](proof/decision.md)
- Sources: [`proof/sources.md`](proof/sources.md)
- Local readiness: [`proof/local_readiness.md`](proof/local_readiness.md)
- Learning record: [`proof/learning_record.json`](proof/learning_record.json)
