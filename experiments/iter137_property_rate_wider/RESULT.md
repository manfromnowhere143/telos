# Iteration 137 Result - Wider Property Genuine-Sound Rate

Status: `PASS`.

## What this gate did

Widened the property genuine-sound measurement: added a third property-testable blocked instance and
re-ran the full-stack batch on the native-x86 CI runner, evaluating each gold-free metamorphic property
inside its pinned SWE-bench container.

## Result

| instance | function | gold resolved | in-container property |
| --- | --- | --- | --- |
| `sympy__sympy-13480` | coth | yes | `PROP_SOUND` |
| `sympy__sympy-15809` | Min | yes | `PROP_SOUND` |
| `sympy__sympy-11618` | Point.distance | yes | `PROP_SOUND` |
| `sympy__sympy-13615` | Complement | yes | (no property) |
| `sympy__sympy-12481` | permutations | yes | (no property) |

- gold-resolution rate: `5/5` = `1.00000000`
- property genuine-sound rate on the property-testable subset: `3/3` = `1.00000000`

## The finding

The property genuine-sound rate holds as the batch grows. All five natively-blocked old sympy instances
resolve their hidden tests in their pinned containers, and all three property-testable ones are
`PROP_SOUND`: coth's odd and reciprocal identities, Min's commutative/idempotent/associative identities,
and Point.distance's symmetry and self-zero, each evaluated inside the pinned sympy environment. The
full stack - Docker environment fidelity plus gold-free property verification - composes across a
growing set of real cross-repo instances that cannot execute locally at all.

## Honest scope

Three property-testable instances among five, all from sympy, one CI run. This is a `3/3` rate on a
small same-repo property-testable subset, not a cross-repo distributional rate. Extending to
property-testable functions in other repos (matplotlib, xarray, sphinx) is the next step.

## Claim boundary

Supported: across five blocked instances the gold patches resolved (`5/5`) and all three
property-testable instances (coth, Min, Point.distance) were `PROP_SOUND` in their pinned containers - a
`3/3` property genuine-sound rate. Not supported: a benchmark, model, or state-of-the-art claim, or a
cross-repo distributional property rate.

## Next gate

`iter138`: extend property-testable blocked instances to repos beyond sympy and re-measure the property
genuine-sound rate across repos.

## Evidence

- `proof/property_rate_results.json` (results produced by the x86 workflow)
- `proof/endpoint_results.json`, `proof/run_summary.json`, `proof/learning_record.json`
- `proof/valid/receipt_property_rate_wider.json`
- fixtures: `experiments/iter134_x86_ci_docker_batch/fixtures/` (manifest + property files)
