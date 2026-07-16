# Iter211 result — TCP-1 materialization preflight

Status: **PASS for deterministic materialization preflight; SCIENTIFIC EXECUTION BLOCKED**.

## Result

TCP-1 now has a machine-readable protocol, five public deterministic seeds, task/trajectory/label/aggregate
schemas, a frozen analysis-input contract, executable statistical accounting, separate control accounting,
resource ceilings, an isolation threat model, and explicit candidate/reviewer/runtime ledgers. The packet is
reproducible without a model, GPU, hidden-test repository, or private runtime.

The admission decision is intentionally blocked: `2` of `11` gates pass and `9` remain blocked. In
particular, there are `0/12` admitted tasks, `0/5` filled independent reviewer roles, no selected model or
documented cutoff, no weight/tokenizer/engine/container/hardware binding, no hidden-test or control
commitments, no hostile isolation rehearsal, no external transparency timestamp, no throughput preflight,
and no approved monetary budget.

The exact five seeds are generated from the first four bytes of
`SHA-256("telos-tcp1-seed-v1:" + index)` for indices `1..5`; their committed values live in
`proof/protocol.json`. Seed freezing does not make a task cohort exist.

## What passed

- deterministic generation and byte-for-byte checking of `17` protocol artifacts, including a canonical
  hash-chained trace-event schema;
- exact merged-baseline custody for iter210 PR `#10`, branch push CI `29496323167`, pull-request CI
  `29496355871`, merge `fb348eb1f67c0605679cd56a1cfa210cf192db03`, and merged-master CI
  `29496560409`;
- a fail-closed completion rule requiring visible-grader, full-trajectory-policy, hidden-consequence, and
  receipt success, with missing/conflicting evidence producing abstention and no completion claim;
- a one-sided exact conditional McNemar implementation, two-sided Wilson intervals, deterministic
  task-cluster bootstrap, explicit missingness, and strict separation of controls from the primary endpoint;
- an adversarial isolation contract covering path/symlink escape, environment disclosure, grader-network
  access, receipt substitution, trace suppression, and label/control leakage;
- a corrected forward sequence beginning with a separately versioned human/cohort/custody freeze before any
  throughput or GPU gate.

## Why execution is blocked

Hashes can establish byte identity, but not license, human independence, chronology, task freshness, or
semantic truth. A Git commit is not the required external pre-output transparency timestamp. A documented
model cutoff reduces one contamination risk but does not prove non-exposure. A selected twelve-task pilot
cannot establish a population rate or model ranking. Those limitations are admission conditions, not prose
disclaimers to add after a run.

The full structured blocker list is in `proof/admission_report.json`; the adversarial reasoning is in
`proof/review.md`.

## Zero-action and claim boundary

This iteration made three read-only `gh` CLI metadata queries. The CLI's internal HTTP request count was not
instrumented, so no exact request count is claimed. It made zero remote mutations before source sealing,
provider/model calls, GPU allocations, accelerator-hours, scientific containers, scientific trajectories,
workflow dispatches or reruns, deployments, payments, and releases.

Iter211 contributes no scientific `N`, `k`, `u`, benchmark score, effect estimate, model comparison,
population estimate, product-efficacy result, deployment claim, priority claim, or state-of-the-art claim.
Its receipt remains `blocked` at the scientific-execution objective even though the local materialization
preflight passes.

## Next gate

The separately versioned next gate is
`experiments/iter212_tcp1_independent_cohort_and_custody_freeze/HYPOTHESIS.md`. It may fill real reviewer,
model, task, hidden-test, control, isolation, timestamp, and budget evidence, but it authorizes no model call,
GPU allocation, or scientific trajectory.
