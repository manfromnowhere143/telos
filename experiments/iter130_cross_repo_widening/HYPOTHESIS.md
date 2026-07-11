# Iteration 130 - Cross-Repo Widening Beyond Django

Status: pre-registered; executed with the honest bounds recorded transparently.

## Why this gate exists

The property-based third layer was measured on six django-utils single-function candidates (iter129).
The ledger's next action was to widen beyond django and re-measure. This gate attempts that on
sympy - a pure-Python repo with math functions that have clean metamorphic identities - and records
the bounds that widening actually hits.

## Method

- Method generality: on real modern sympy, test contract/metamorphic identities of hyperbolic
  functions (`coth`, `cosh`, `sinh`, `tanh`) over random rationals, and count violations against the
  real implementation.
- Instance-level feasibility: attempt to tie the method to specific SWE-bench sympy instances and
  record what blocks it.

## Endpoints

- `sympy_identities_sound`: how many tested identities hold with zero violations under real execution.
- the bounds encountered: environment fidelity, applicability, and numeric-vs-symbolic precision.

## Acceptance / interpretation rule

Descriptive. If the property-based method holds on sympy math functions, method generality beyond
django is demonstrated. Whatever bounds block instance-level tie-in (Python-version fidelity, the
single-function applicability criterion, numeric precision) are recorded as the honest scaling ceiling
rather than hidden.

## Falsifiers

1. If a genuine mathematical identity shows violations, distinguish a real property failure from a
   numeric-precision artifact and record which.
2. If instance-level tie-in is blocked, name the concrete blocker rather than claim success.

## Execution envelope

- native execution on modern sympy, no provider calls, no GPU, no cloud,
- production/live-domain mutation: forbidden, benchmark/model/SOTA claim: forbidden.

## Claim boundary (pre-committed)

At most: "the property-based method generalizes to sympy math functions (`N/4` identities sound under
real execution); instance-level cross-repo scale is bounded by environment fidelity and the
single-function applicability criterion, and numeric checking needs symbolic care." Not a benchmark,
model, or SOTA claim.
