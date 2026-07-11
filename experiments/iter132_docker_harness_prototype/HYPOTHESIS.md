# Iteration 132 - Docker Harness Prototype

Status: pre-registered before execution. Frozen before the container run.

## Why this gate exists

Iter130-iter131 identified environment fidelity as the last scaling bound: the clean single-function
sympy instances are pre-3.10 and cannot run on the available Python 3.11. Iter131 scoped the Docker
harness as the resolution. This gate stops scoping and runs it: it takes one natively-blocked instance
and executes its real hidden test inside the official SWE-bench Docker image.

## Method

For `sympy__sympy-13480` (blocked natively because it needs `collections.Mapping`, removed in Python
3.10+): pull the official image `swebench/sweb.eval.x86_64.sympy_1776_sympy-13480`, confirm its pinned
environment, then apply the hidden `test_patch` and run the FAIL_TO_PASS test on the base and on the
gold patch inside the container.

## Endpoints

- `pinned_python`: the container's Python version and whether `collections.Mapping` imports.
- `base_result` and `gold_result`: the real hidden-test outcomes inside the container.

## Acceptance / interpretation rule

If the container provides a Python the native harness lacks, the hidden test fails on base and passes
on gold inside it, then the Docker harness resolves the environment-fidelity bound in practice, not
just in scope. The bound moves from open to closed for this instance.

## Falsifiers

1. If the image does not pull or run in this environment, record the concrete blocker (arm64
   emulation, disk, auth) rather than claim success.
2. If base does not fail or gold does not pass inside the container, the harness did not reproduce the
   instance; record it.

## Execution envelope

- Docker execution of one official SWE-bench image (x86 under arm64 emulation), no provider calls,
- production/live-domain mutation: forbidden, benchmark/model/SOTA claim: forbidden.

## Claim boundary (pre-committed)

At most: "the official SWE-bench Docker image ran the real hidden test for one natively-blocked
instance in a pinned Python 3.9 environment, failing on base and passing on gold." Not a benchmark,
model, or SOTA claim, and not a claim of full-dataset Docker coverage.
