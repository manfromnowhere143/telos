# Iteration 136 Result - Scaling the Full-Stack Batch

Status: `PASS`.

## What this gate did

Scaled the full-stack batch on the native-x86 CI runner: added a second property-testable blocked
instance and measured the property genuine-sound rate across the property-testable subset, with each
gold-free metamorphic property evaluated inside its pinned SWE-bench container.

## Result

| instance | function | gold resolved | in-container property |
| --- | --- | --- | --- |
| `sympy__sympy-13480` | coth | yes | `PROP_SOUND` |
| `sympy__sympy-15809` | Min | yes | `PROP_SOUND` |
| `sympy__sympy-13615` | Complement | yes | (no property) |
| `sympy__sympy-12481` | permutations | yes | (no property) |

- gold-resolution rate: `4/4` = `1.00000000`
- property genuine-sound rate on the property-testable subset: `2/2` = `1.00000000`

## The finding

The full stack composes across a batch. All four natively-blocked old sympy instances resolve their
hidden tests in their pinned containers, and both property-testable ones are `PROP_SOUND`: coth's odd
and reciprocal identities and Min's commutative, idempotent, and associative identities all hold,
evaluated symbolically inside the pinned sympy environment. Environment fidelity (Docker) and gold-free
property verification (Layer 3) now run together across a set of real cross-repo instances that cannot
execute locally at all - the local machine has no Python that imports these sympy versions.

## Honest scope

Two property-testable instances among four, one CI run. This is a `2/2` property genuine-sound rate on
a small property-testable subset, not a distributional rate over the whole dataset. Adding property
files for more property-testable blocked instances across additional repos, and re-running, is the
straightforward next step on the same workflow.

## Claim boundary

Supported: across four blocked instances the gold patches resolved (`4/4`) and both property-testable
instances (coth, Min) were `PROP_SOUND` in their pinned containers - a `2/2` property genuine-sound rate
on the property-testable subset. Not supported: a benchmark, model, or state-of-the-art claim, or a
dataset-wide property rate.

## Next gate

`iter137`: add property-testable blocked instances across additional repos and re-measure the property
genuine-sound rate at larger cross-repo scale.

## Evidence

- `proof/full_stack_batch_results.json` (results produced by the x86 workflow)
- `proof/endpoint_results.json`, `proof/run_summary.json`, `proof/learning_record.json`
- `proof/valid/receipt_full_stack_batch_scale.json`
- fixtures: `experiments/iter134_x86_ci_docker_batch/fixtures/` (manifest + property files)
