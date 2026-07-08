# Next Phase

## Current Action

Run `iter08_provider_model_pilot_slice` exactly as frozen in
[`../experiments/iter08_provider_model_pilot_slice/HYPOTHESIS.md`](../experiments/iter08_provider_model_pilot_slice/HYPOTHESIS.md).

The output is not a model score. It is a selected provider-model pilot specification:

- score candidate pilot designs,
- freeze exact provider and model identity,
- freeze task target, budget ceiling, and max API calls,
- define raw artifact retention, receipt fields, audit checks, and stop criteria,
- preserve the boundary that no paid execution occurs during the selection gate.

## Infrastructure Discipline

Available cloud and sandbox resources are escalation tools, not default proof. The order is:

1. local receipt validation,
2. local or GitHub-runner CodeClash smoke under Docker,
3. deterministic Mini-SWE-Agent behavior smoke,
4. deterministic edit-agent slice,
5. provider-model pilot selection with exact spend and evidence bars,
6. E2B or sandboxed execution only when isolation is needed and the gate records it,
7. GPU or provider model cloud only when a frozen gate names the spend and expected evidence.

No GPU or provider model run is authorized by `iter00`, `iter01`, `iter02`, `iter03`, `iter04`, or
`iter05`. `iter06`, `iter07`, and `iter08` also forbid provider model calls and GPU runs.

## After The Provider-Model Pilot Slice Gate

If the selection gate passes:

1. Publish the selected pilot spec and review.
2. Run the paid pilot only if the selected spec names model, budget, task, and expected evidence.
3. Escalate to sandbox/cloud only if the selected run requires isolation or compute.

If the selection gate fails:

1. Publish the failure.
2. Fix the concrete selection gap or choose a narrower pilot.
3. Do not start a paid model run.
