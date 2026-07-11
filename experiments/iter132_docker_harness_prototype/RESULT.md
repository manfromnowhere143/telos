# Iteration 132 Result - Docker Harness Prototype

Status: `PASS`.

## What this gate did

Stopped scoping the environment-fidelity bound and closed it in practice: it ran a natively-blocked
instance's real hidden test inside the official SWE-bench Docker image.

## Result

Instance `sympy__sympy-13480`, blocked natively because it needs `collections.Mapping` (removed in
Python 3.10+) and only Python 3.11 was available.

- image pulled: `swebench/sweb.eval.x86_64.sympy_1776_sympy-13480` (x86 under arm64 emulation)
- pinned environment inside the container: Python `3.9.20`, sympy `1.1.2.dev`, `collections.Mapping`
  importable - exactly what the native harness lacked
- base + hidden test: `FAIL` (5 passed, 1 exception `NameError: name 'cotm' is not defined` - the real
  bug the instance fixes)
- gold + hidden test: `PASS` (6 passed, OK)

`environment_fidelity_bound_closed_for_instance = true`.

## The finding

The Docker harness works here. It provides the pinned Python 3.9 environment the native harness could
not, and inside it the real hidden test discriminates: it fails on the unfixed base with the genuine
bug and passes on the gold patch. The environment-fidelity bound that iter114, iter124, and iter130
measured is not just scoped - it is resolved in practice for this instance, using the official image,
with no new infrastructure to build and nothing required from the operator beyond a working Docker.

What remains is engineering, not open research: batch the same image mechanism across the
environment-fidelity-blocked instances, and route symbolic-capable functions to symbolic property
evaluation (iter131), to re-measure the property layer at full cross-repo scale.

## Claim boundary

Supported: the official SWE-bench Docker image ran the real hidden test for one natively-blocked
instance in a pinned Python 3.9 environment, failing on base and passing on gold. Not supported: a
benchmark, model, or state-of-the-art claim, or a claim of full-dataset Docker coverage - this is one
instance, and batching is the engineering next step.

## Next gate

`iter133`: batch the Docker harness across a set of environment-fidelity-blocked instances and
re-measure gold resolution and the property-layer genuine-sound rate at cross-repo scale.

## Evidence

- `proof/docker_run_results.json` (observed container run)
- `proof/endpoint_results.json`, `proof/run_summary.json`, `proof/learning_record.json`
- `proof/valid/receipt_docker_harness_prototype.json`
- `scripts/run_docker_harness_prototype.py`
