# Next Phase

## Current Action

Run `iter02_public_task_slice` exactly as frozen in
[`../experiments/iter02_public_task_slice/HYPOTHESIS.md`](../experiments/iter02_public_task_slice/HYPOTHESIS.md).

The output is not a model score. It is a public-slice decision:

- choose the first public task slice,
- publish the expected artifact contract,
- name the first-run falsifier,
- keep cloud spend at zero.

## Infrastructure Discipline

Available cloud and sandbox resources are escalation tools, not default proof. The order is:

1. local receipt validation,
2. local public-task harness smoke,
3. E2B or sandboxed execution when isolation matters,
4. GPU or cloud only when the frozen gate names the spend and the expected evidence.

No cloud run is authorized by `iter00`, `iter01`, or `iter02`.

## After The Public Slice Gate

If the slice gate passes:

1. Write the first public-task run `HYPOTHESIS.md`.
2. Freeze the primary Telos metric.
3. Run only the smallest public-task harness that can falsify receipt quality.
4. Escalate to E2B/cloud only if the frozen run requires isolation or compute.

If the slice gate fails:

1. Publish the failure.
2. Choose a narrower public task slice or publish the null.
3. Do not start a model run.
