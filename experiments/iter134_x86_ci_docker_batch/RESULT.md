# Iteration 134 Result - Docker Batch on a Native-x86 CI Runner

Status: `PASS`.

## What this gate did

Built the native-x86 runner iter133 said the batch needed - a manual `docker-batch.yml` workflow
(`workflow_dispatch` only, so it never affects the main CI) - triggered it, and read what it produced.
The workflow ran on GitHub Actions `ubuntu-latest` (native x86, no emulation): it pulled each official
SWE-bench image, ran the FAIL_TO_PASS test on base and on gold inside the pinned container, and removed
each image to respect runner disk.

## Result

| instance | image pulled | base | gold |
| --- | --- | --- | --- |
| `sympy__sympy-13480` | yes | fail (2 passed, 1 exception) | `PASS` (3 passed, OK) |
| `sympy__sympy-13615` | yes | fail (0 passed, 1 failed) | `PASS` (1 passed, OK) |
| `sympy__sympy-12481` | yes | fail (0 passed, 1 exception) | `PASS` (1 passed, OK) |

- gold-resolution rate on the x86 runner: `3/3` = `1.00000000`
- workflow run: dispatched, `completed success`

## The finding

On the correct execution environment the Docker batch runs cleanly. All three natively-blocked old
sympy instances - which cannot run on the local Python 3.11 and were unreliable under local arm64
emulation (iter133) - resolve here: the real hidden test fails on the unfixed base with the genuine bug
and passes on the gold patch, each in its pinned environment, in seconds. The iter133 local-batch
failure was an arm64-emulation environment bound, not a method one, exactly as recorded. The batch is
now demonstrated end to end: single instance (iter132), local bound (iter133), native-x86 CI batch
(here).

## Honest scope

Three instances on one CI run. This confirms the batch mechanism on x86; it is not a full-dataset
resolution rate. Scaling to the whole environment-fidelity-blocked set, and running the property-layer
harness inside the pinned containers, is the straightforward next step on the same workflow.

## Claim boundary

Supported: a manual x86 CI workflow pulled the official SWE-bench images and ran three natively-blocked
instances' hidden tests, with base failing and gold passing for `3/3`. Not supported: a benchmark,
model, or state-of-the-art claim, or a full-dataset resolution rate.

## Next gate

`iter135`: scale the x86 CI Docker batch to more blocked instances and run the property-layer harness
inside the pinned containers to measure the property genuine-sound rate at full cross-repo scale.

## Evidence

- `proof/ci_batch_results.json` (results produced by the x86 workflow)
- `proof/endpoint_results.json`, `proof/run_summary.json`, `proof/learning_record.json`
- `proof/valid/receipt_x86_ci_docker_batch.json`
- `.github/workflows/docker-batch.yml`, `scripts/docker_batch_ci.sh`, `scripts/run_x86_ci_docker_batch.py`
- fixtures: `experiments/iter134_x86_ci_docker_batch/fixtures/`
