# Iteration 134 - Docker Batch on a Native-x86 CI Runner

Status: pre-registered before the CI run. Frozen before the workflow was triggered.

## Why this gate exists

Iter133 found that local batch Docker is unreliable under arm64 emulation and belongs on a native-x86
CI runner. This gate builds that runner: a manual GitHub Actions workflow (`docker-batch.yml`,
`workflow_dispatch` only, so it never affects the main CI) that pulls the official SWE-bench images on
the native-x86 runner and runs each instance's hidden test on base and gold.

## Method

Three natively-blocked old sympy instances (`13480`, `13615`, `12481`), with gold and test patches
committed as fixtures. The workflow, on `ubuntu-latest` (native x86, no emulation), serially pulls each
image, runs the FAIL_TO_PASS test on base and on gold inside the container, removes the image to
respect runner disk, and uploads a results JSON.

## Endpoints

- per instance: whether the image pulled, and the base and gold hidden-test outcomes on x86.
- the batch gold-resolution count on the native-x86 runner.

## Acceptance / interpretation rule

If the workflow runs the batch on x86 and each gold patch resolves its hidden test (base fails, gold
passes), the Docker batch is confirmed at cross-repo scale on the correct execution environment,
closing the operational item iter133 identified. If the CI runner hits its own limit (disk, time),
record that concretely.

## Falsifiers

1. If the workflow fails for a runner-resource reason (disk, time), record it concretely rather than as
   a method failure.
2. Do not claim a gold-resolution count the workflow did not actually produce.

## Execution envelope

- one manual GitHub Actions run on the native-x86 runner; the workflow never runs on push,
- production/live-domain mutation: forbidden, benchmark/model/SOTA claim: forbidden.

## Claim boundary (pre-committed)

At most: "a manual x86 CI workflow pulled the official SWE-bench images and ran three natively-blocked
instances' hidden tests, with base failing and gold passing for `N/3`." Not a benchmark, model, or SOTA
claim.
