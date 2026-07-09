# Iteration 28 - Public Claim Surface Guard

Status: pre-registered, result pending.

## Purpose

Use the `iter27` claim-boundary matrix to audit the public prose surface. The README and report now
summarize a long semantic evidence chain with passes, nulls, changed candidates, and verifier-strength
evidence. The risk is not missing proof; the risk is prose that accidentally overclaims beyond the
matrix.

This gate should verify that public documentation stays aligned with the machine-readable boundary.

## Frozen Input

- Claim matrix: `experiments/iter27_semantic_claim_boundary_matrix/proof/claim_boundary_matrix.json`.
- Public prose: `README.md`, `docs/REPORT.md`, `docs/NEXT_PHASE.md`, and `CONTINUITY.md`.
- Provider/model: no provider call allowed for this gate.
- Compute: local CPU only.

## Verification Plan

Build a local guard that checks:

- the README references `iter23`, `iter25`, and their failure/null status,
- the README references the changed-candidate boundary for `iter24`,
- the public prose does not claim original `iter21` occupied-tail safety,
- the public prose does not claim CodeClash leaderboard, SWE-bench, production, live-domain, or
  model-superiority results,
- the active gate points to the next pre-registered gate.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- no provider, API, GPU, or cloud spend occurs,
- the guard reads the committed `iter27` matrix,
- every checked public prose file exists,
- failed/null gates remain visible in public prose,
- original provider logic and changed candidate logic are not conflated in public prose,
- command output and proof artifacts are committed,
- no leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.

## Falsifiers

Publish blocked/null evidence if:

- the claim matrix cannot be loaded,
- required public prose files are missing.

Publish a quality failure, not a clean pass, if:

- README or report implies the original `iter21` bot was occupied-tail safe,
- failed/null gates are hidden or softened into clean passes,
- changed candidate evidence is described as original provider-submitted behavior,
- public prose widens into benchmark or production claims.

## Scope Boundary

This is a public documentation guard. It is not a provider rerun, not a benchmark result, and not a
production/live-domain verification.
