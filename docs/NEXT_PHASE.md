# Next Phase

## Current Action

Run `iter06_deterministic_edit_slice` exactly as frozen in
[`../experiments/iter06_deterministic_edit_slice/HYPOTHESIS.md`](../experiments/iter06_deterministic_edit_slice/HYPOTHESIS.md).

The output is not a model score. It is a deterministic slice decision:

- find the smallest agent path that produces a non-empty code diff,
- keep provider API/GPU spend at zero,
- preserve trajectory or command-trace evidence,
- freeze the next executable gate before any provider-model run.

## Infrastructure Discipline

Available cloud and sandbox resources are escalation tools, not default proof. The order is:

1. local receipt validation,
2. local or GitHub-runner CodeClash smoke under Docker,
3. deterministic Mini-SWE-Agent behavior smoke,
4. deterministic edit-agent slice,
5. E2B or sandboxed execution only when isolation is needed and the gate records it,
6. GPU or provider model cloud only when a later frozen gate names the spend and expected evidence.

No GPU or provider model run is authorized by `iter00`, `iter01`, `iter02`, `iter03`, `iter04`, or
`iter05`. `iter06` also forbids provider model calls and GPU runs.

## After The Deterministic Edit Slice Gate

If the slice gate passes:

1. Publish the chosen slice and rejected candidates.
2. Freeze the first deterministic non-empty edit run.
3. Consider a provider-model run only after non-empty diff evidence is audited.
4. Escalate to sandbox/cloud only if the frozen run requires isolation or compute.

If the slice gate fails:

1. Publish the failure.
2. Fix the concrete artifact gap or choose a narrower edit path.
3. Do not start a model run.
