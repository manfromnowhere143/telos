# Iteration 130 Result - Cross-Repo Widening Beyond Django

Status: `PASS`.

## What this gate did

Attempted to widen the property-based third layer beyond django, onto sympy, and recorded both the
method generality and the bounds the widening actually hits.

## Method generality on real sympy

On real modern sympy (`1.12.dev`, Python 3.11), contract/metamorphic identities of hyperbolic
functions held under real execution:

| identity | property | violations |
| --- | --- | ---: |
| coth odd | `coth(-x) == -coth(x)` | `0/25` |
| coth reciprocal | `coth(x) * tanh(x) == 1` | `0/25` |
| cosh even | `cosh(-x) == cosh(x)` | `0/25` |
| Pythagorean | `cosh(x)**2 - sinh(x)**2 == 1` | `1/24` |

Method generality: `3/4` sound. The property-based method - contract properties auto-classified as
transforms - works on a second repo's functions, not only django utils.

## The three honest bounds cross-repo widening hit

1. Environment fidelity. The clean single-function sympy instances in the dataset are pre-3.10 and
   import removed stdlib (`from collections import Mapping`); they need Python <= 3.9, which is not
   available, so they do not run natively. This is the same wall the official SWE-bench Docker harness
   solves with pinned per-instance Python, first seen in iter114/iter124 and now confirmed cross-repo.
2. Applicability. The modern sympy instances that do run are edge-case bug fixes (e.g. a zero-equality
   or a units issue), not clean single testable functions, so they fail the iter129 single-function
   applicability criterion. The intersection of "modern enough to run" and "a clean single function"
   is small.
3. Numeric versus symbolic. The one violation (`1/24` on the Pythagorean identity) is a
   float-precision false positive at a large argument - the identity is exact symbolically. Sound
   numeric property checking needs symbolic evaluation or per-function tolerance.

## The finding

The property-based method generalizes beyond django as a method - its identities hold on sympy math
functions under real execution. But scaling it to arbitrary SWE-bench instances cross-repo is bounded
by a compound of environment fidelity, the single-function applicability criterion, and numeric
precision. This is not a failure of the idea; it is a precise map of what the next infrastructure must
provide: pinned per-instance environments (the Docker harness) and symbolic property evaluation.

## Claim boundary

Supported: the property-based method holds on `3/4` sympy hyperbolic identities under real execution;
instance-level cross-repo scale is bounded by environment fidelity, applicability, and numeric-vs-
symbolic precision, each recorded concretely. Not supported: a benchmark, model, or state-of-the-art
claim, or a cross-repo instance-level rate.

## Next gate

`iter131`: adopt symbolic property evaluation (exact equality) to remove numeric artifacts, and scope
the Docker harness as the path to full cross-repo instance coverage.

## Evidence

- `proof/sympy_identity_results.json` (observed native-execution identity soundness)
- `proof/endpoint_results.json`, `proof/run_summary.json`, `proof/learning_record.json`
- `proof/valid/receipt_cross_repo_widening.json`
- `scripts/run_cross_repo_widening.py`
