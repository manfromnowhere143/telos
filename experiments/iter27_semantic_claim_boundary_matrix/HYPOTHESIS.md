# Iteration 27 - Semantic Claim Boundary Matrix

Status: pre-registered, result pending.

## Purpose

Summarize the semantic evidence chain without inflating it. Iterations `20` through `26` now contain
provider-submitted logic, reconstructed local verifiers, a tail-semantics falsification, changed
candidate controls, a failed mutation guard, and a compound mutation guard that resolves the specific
own-tail redundancy.

This gate should produce a machine-checkable claim-boundary matrix so readers can see exactly which
claims apply to original provider logic, which apply only to changed candidates, which gates failed,
and which verifier-strength claims are supported.

## Frozen Input

- Results and proof summaries for `iter20` through `iter26`.
- Provider/model: no provider call allowed for this gate.
- Compute: local CPU only.

## Verification Plan

Build a local matrix artifact that records, for each relevant claim:

- subject under test: original provider logic, reconstructed original logic, changed candidate, or
  verifier harness,
- status: pass, fail/null, blocked, or pending,
- evidence artifact paths,
- scope boundary,
- explicit exclusions such as no leaderboard, SWE-bench, production, live-domain, or model
  capability claim.

The matrix must be validated by an audit script and reflected in the README/report without changing
the underlying proof artifacts.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- no provider, API, GPU, or cloud spend occurs,
- the matrix includes `iter20` through `iter26`,
- failed/null gates remain visible as failed/null,
- original provider logic and changed candidate logic are not conflated,
- evidence paths exist for every non-pending row,
- command output and proof artifacts are committed,
- no leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.

## Falsifiers

Publish blocked/null evidence if:

- required prior proof artifacts are missing,
- the matrix cannot distinguish original logic from changed candidate logic,
- evidence paths cannot be validated.

Publish a quality failure, not a clean pass, if:

- any failed/null gate is hidden or relabeled as a clean pass,
- the matrix implies the original `iter21` bot was occupied-tail safe,
- the matrix treats provider game score as verifier evidence,
- the result widens into benchmark or production claims.

## Scope Boundary

This is a documentation and machine-readable claim-boundary gate. It is not a provider rerun, not a
benchmark result, and not a production/live-domain verification.
