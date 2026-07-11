# Iteration 137 - Wider Property Genuine-Sound Rate

Status: pre-registered before the CI run. Frozen before the workflow was re-triggered.

## Why this gate exists

Iter136 measured a `2/2` property genuine-sound rate across two property-testable blocked instances.
This gate widens it: it adds a third property-testable blocked instance and re-measures the property
genuine-sound rate in pinned containers on the native-x86 runner.

## Method

The batch now covers five blocked old sympy instances; three are property-testable with gold-free
metamorphic properties evaluated inside their pinned containers:

- `sympy__sympy-13480` (coth): odd and reciprocal identities.
- `sympy__sympy-15809` (Min): commutative, idempotent, associative.
- `sympy__sympy-11618` (Point.distance): symmetric and zero-to-itself.

## Endpoints

- gold resolution across the five instances.
- property genuine-sound rate across the three property-testable instances.

## Acceptance / interpretation rule

If the gold patches resolve and all three property-testable instances report `PROP_SOUND` in their
pinned containers, the property genuine-sound rate is `3/3`. Any `PROP_UNSOUND` is recorded and
examined.

## Falsifiers

1. If a property is `PROP_UNSOUND` in the pinned environment, record it rather than hide it.
2. If the workflow fails for a runner-resource reason, record it concretely.

## Execution envelope

- one manual GitHub Actions run on the native-x86 runner; the workflow never runs on push,
- production/live-domain mutation: forbidden, benchmark/model/SOTA claim: forbidden.

## Claim boundary (pre-committed)

At most: "across five blocked instances the gold patches resolved and all three property-testable
instances (coth, Min, Point.distance) were `PROP_SOUND` in their pinned containers - a `3/3` property
genuine-sound rate." Not a benchmark, model, or SOTA claim.
