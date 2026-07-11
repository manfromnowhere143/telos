# Iteration 136 - Scaling the Full-Stack Batch and the Property Genuine-Sound Rate

Status: pre-registered before the CI run. Frozen before the workflow was re-triggered.

## Why this gate exists

Iter135 ran the full stack (gold resolution plus a gold-free property) inside one pinned container. This
gate scales it: it adds a second property-testable blocked instance and measures the property
genuine-sound rate across the property-testable subset, on the native-x86 runner.

## Method

The batch now covers four blocked old sympy instances; two are property-testable with gold-free
metamorphic properties evaluated inside their pinned containers:

- `sympy__sympy-13480` (coth): `coth(-x) == -coth(x)`, `coth(x)*tanh(x) == 1`.
- `sympy__sympy-15809` (Min): `Min(a,b) == Min(b,a)`, `Min(a,a) == a`, `Min(Min(a,b),c) == Min(a,b,c)`.

The `docker-batch.yml` workflow runs, per instance, gold resolution and (where a property file exists)
the in-container property check.

## Endpoints

- gold resolution across the four instances.
- property genuine-sound rate across the property-testable subset (`PROP_SOUND` count over instances
  with a property).

## Acceptance / interpretation rule

If the gold patches resolve and both property-testable instances report `PROP_SOUND` in their pinned
containers, the property genuine-sound rate is `2/2` at cross-repo scale in the pinned environments.
Any `PROP_UNSOUND` is recorded and examined.

## Falsifiers

1. If a property is `PROP_UNSOUND` in the pinned environment, record it rather than hide it.
2. If the workflow fails for a runner-resource reason, record it concretely.

## Execution envelope

- one manual GitHub Actions run on the native-x86 runner; the workflow never runs on push,
- production/live-domain mutation: forbidden, benchmark/model/SOTA claim: forbidden.

## Claim boundary (pre-committed)

At most: "across four blocked instances the gold patches resolved and both property-testable instances
(`coth`, `Min`) were `PROP_SOUND` in their pinned containers - a `2/2` property genuine-sound rate on
the property-testable subset." Not a benchmark, model, or SOTA claim.
