# Next Phase

## Current Action

Run `iter04_agent_behavior_slice` exactly as frozen in
[`../experiments/iter04_agent_behavior_slice/HYPOTHESIS.md`](../experiments/iter04_agent_behavior_slice/HYPOTHESIS.md).

The output is not a model score. It is a run-selection gate:

- choose the smallest CodeClash run with real agent behavior,
- publish the expected artifact contract,
- name the first-run falsifier,
- keep model/API/GPU spend at zero unless a later gate explicitly changes that.

## Infrastructure Discipline

Available cloud and sandbox resources are escalation tools, not default proof. The order is:

1. local receipt validation,
2. local or GitHub-runner CodeClash smoke under Docker,
3. deterministic agent-behavior smoke,
4. E2B or sandboxed execution only when isolation is needed and the gate records it,
5. GPU or model cloud only when a later frozen gate names the spend and expected evidence.

No GPU or model run is authorized by `iter00`, `iter01`, `iter02`, `iter03`, or `iter04`.

## After The Agent-Behavior Slice Gate

If the slice gate passes:

1. Run the selected deterministic or instant-submit agent-behavior smoke.
2. Publish the receipt and parsed artifacts.
3. Freeze the first model-agent run only after the behavior smoke clears.
4. Escalate to sandbox/cloud only if the frozen run requires isolation or compute.

If the slice gate fails:

1. Publish the failure.
2. Choose a narrower agent-behavior slice or publish the null.
3. Do not start a model run.
