# Iteration 135 Result - Full-Stack Verification Inside the Pinned Container

Status: `PASS`.

## What this gate did

Closed the loop between the two halves of the program - environment fidelity and gold-free property
verification - by running them together inside one pinned SWE-bench container on the native-x86 CI
runner. The `docker-batch.yml` workflow now, after applying the gold patch, runs a per-instance
gold-free metamorphic property inside the container and reports its soundness.

## Result

| instance | hidden test (base -> gold) | in-container property |
| --- | --- | --- |
| `sympy__sympy-13480` (coth) | fail -> `PASS` | `PROP_SOUND` |
| `sympy__sympy-13615` (Complement) | fail -> `PASS` | `NO_PROPERTY` |
| `sympy__sympy-12481` (permutations) | fail -> `PASS` | `NO_PROPERTY` |

- gold resolution: `3/3`
- property sound where applicable: `1/1`
- full-stack instance (gold resolves and property sound in one pinned container): `sympy__sympy-13480`

## The finding

The full stack runs in one pinned environment on a real cross-repo instance that cannot execute
locally at all. Inside the `sympy__sympy-13480` container - Python 3.9, sympy 1.1.2, the exact
environment the local machine lacked - the hidden test resolves (base fails with the real `cotm` bug,
gold passes) and the gold-free coth metamorphic property (`coth(-x) == -coth(x)`, `coth(x)*tanh(x) ==
1`, evaluated symbolically) is sound. Environment fidelity (Layer 3's Docker requirement) and property
verification (Layer 3's oracle) compose end to end. The two instances without a property still resolve
their hidden test; a property is defined only where the function is property-testable.

## Honest scope

One property-testable instance among three, one CI run. This demonstrates the full stack composes in
the pinned environment; it is not a cross-repo property genuine-sound rate. Adding property files for
more property-testable blocked instances and scaling the x86 CI full-stack batch is the next step on
the same workflow.

## Claim boundary

Supported: inside the pinned SWE-bench container of a natively-blocked instance, the hidden test
resolved (base fails, gold passes) and the gold-free coth property was sound - the full stack ran in
one pinned environment. Not supported: a benchmark, model, or state-of-the-art claim, or a cross-repo
property genuine-sound rate.

## Next gate

`iter136`: add property files for more property-testable blocked instances and scale the x86 CI
full-stack batch to measure the property genuine-sound rate across the blocked set.

## Evidence

- `proof/full_stack_results.json` (results produced by the x86 workflow, with the in-container property)
- `proof/endpoint_results.json`, `proof/run_summary.json`, `proof/learning_record.json`
- `proof/valid/receipt_full_stack_in_container.json`
- `.github/workflows/docker-batch.yml`, `scripts/docker_batch_ci.sh`,
  `experiments/iter134_x86_ci_docker_batch/fixtures/sympy__sympy-13480.property.py`
