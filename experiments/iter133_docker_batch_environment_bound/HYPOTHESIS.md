# Iteration 133 - Docker Batch and the Local Environment Bound

Status: pre-registered; executed with an honest environment bound recorded.

## Why this gate exists

Iter132 proved the Docker harness runs one natively-blocked instance's hidden test in a pinned Python
3.9. The ledger's next action was to batch it across a set of blocked instances and re-measure at
scale. This gate attempts that and records what the local environment can and cannot sustain.

## Method

Target five old sympy instances (pre-3.10, natively blocked): pull each official SWE-bench image and
run its FAIL_TO_PASS test on base and gold inside the container.

## Endpoints

- how many instances complete a clean base-fail/gold-pass Docker run locally.
- the concrete environment constraint if batch execution is unreliable.

## Acceptance / interpretation rule

If the local environment sustains the batch, report the cross-repo gold-resolution rate. If it does
not, record the concrete constraint (pull cost, daemon load, emulated-container flakiness) as an
honest bound on local execution, noting that the method itself is proven per iter132 and that
full-dataset batching is a native-x86 CI operation, not a research question.

## Falsifiers

1. If the local batch fails, name the concrete cause rather than claim a method failure.
2. Do not claim a cross-repo batch rate the local environment did not actually produce.

## Execution envelope

- Docker execution of official SWE-bench images under arm64 emulation, no provider calls,
- production/live-domain mutation: forbidden, benchmark/model/SOTA claim: forbidden.

## Claim boundary (pre-committed)

At most: "single-instance Docker execution is proven (iter132); local batch execution is unreliable in
this arm64-emulation environment for concrete infrastructure reasons, and full-dataset batching belongs
on a native-x86 CI runner." Not a benchmark, model, or SOTA claim, and not a claimed batch rate.
