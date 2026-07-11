# Iteration 135 - Full-Stack Verification Inside the Pinned Container

Status: pre-registered before the CI run. Frozen before the workflow was re-triggered.

## Why this gate exists

Iter134 ran the Docker batch on native-x86 CI and resolved the blocked instances. This gate closes the
loop: it runs the gold-free property layer (Layer 3) inside the same pinned SWE-bench container, so the
full stack - environment fidelity plus metamorphic verification - is demonstrated on a real cross-repo
instance that could not run locally at all.

## Method

The `docker-batch.yml` workflow is extended: after applying the gold patch inside the pinned container,
if a per-instance property file exists, it runs the gold-free metamorphic property there and reports
`PROP_SOUND` or `PROP_UNSOUND`. For `sympy__sympy-13480` (coth), the property is the contract identities
`coth(-x) == -coth(x)` and `coth(x)*tanh(x) == 1`, evaluated symbolically (universally quantified) in
the pinned sympy `1.1.2` environment.

## Endpoints

- per instance: gold resolution (base fails, gold passes) and, where a property exists, its in-container
  soundness.
- confirmation that the property layer runs inside the pinned container of a natively-unrunnable
  instance.

## Acceptance / interpretation rule

If the gold patches resolve and the coth property is `PROP_SOUND` inside the pinned container, the full
stack is demonstrated: the same environment that runs the hidden test also runs the gold-free property
check, on an instance the local machine cannot execute at all.

## Falsifiers

1. If the property is `PROP_UNSOUND` in the pinned environment, record it - the property or the pinned
   library behavior differs and must be examined.
2. If the workflow fails for a runner-resource reason, record it concretely.

## Execution envelope

- one manual GitHub Actions run on the native-x86 runner; the workflow never runs on push,
- production/live-domain mutation: forbidden, benchmark/model/SOTA claim: forbidden.

## Claim boundary (pre-committed)

At most: "inside the pinned SWE-bench container for a natively-blocked instance, the hidden test
resolved (base fails, gold passes) and the gold-free coth property was sound - the full stack ran in
the pinned environment." Not a benchmark, model, or SOTA claim.
