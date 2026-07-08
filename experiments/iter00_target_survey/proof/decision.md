# Decision

Decision: `HYBRID_OVERLAY_SELECTED`

Selected target:

```text
telos_codeclash_swebench_overlay
```

## Rationale

Telos needs a first target that exposes the gap between proxy success and real completion without
requiring a large private harness. The selected line combines two public anchors:

- **CodeClash** for goal-oriented, multi-round software engineering with codebase evolution,
  competition logs, trajectories, and public ELO anchors.
- **SWE-bench Verified** for human-validated coding-agent patch tasks, stable public instance
  count, and test/diff artifacts.

The first Telos experiment should not claim to improve either benchmark. It should test whether a
receipt protocol can identify unsupported completion claims, over-editing, unverified work, and
stop-boundary errors on public software-agent tasks.

## First Run Shape

Freeze `iter01` as a receipt-dry-run on a small public coding task slice:

1. replay or run one simple baseline agent attempt,
2. emit a Telos proof receipt,
3. verify test/build/diff evidence,
4. classify the attempt as `complete`, `proxy_pass`, `fail`, or `blocked`,
5. stop if any receipt field cannot be independently validated.

## Baseline Anchor

The baseline is not yet a model score. The first baseline is the public task/benchmark contract:

- CodeClash: goal-oriented software engineering, public ELO/trajectory anchor.
- SWE-bench Verified: 500 human-validated coding-agent instances and public `% Resolved` metric.

`iter01` must freeze the exact task slice and the first measurable Telos metric before any run.
