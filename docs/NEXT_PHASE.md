# Next Phase

## Current Action

Run `iter05_agent_behavior_smoke` exactly as frozen in
[`../experiments/iter05_agent_behavior_smoke/HYPOTHESIS.md`](../experiments/iter05_agent_behavior_smoke/HYPOTHESIS.md).

The output is not a model score. It is a deterministic agent-path receipt:

- run the selected BattleSnake instant-submit PvP config,
- preserve metadata, logs, trajectory, agent stats, and diff-scope artifacts,
- produce a valid Telos receipt,
- keep provider API/GPU spend at zero.

## Infrastructure Discipline

Available cloud and sandbox resources are escalation tools, not default proof. The order is:

1. local receipt validation,
2. local or GitHub-runner CodeClash smoke under Docker,
3. deterministic Mini-SWE-Agent behavior smoke,
4. E2B or sandboxed execution only when isolation is needed and the gate records it,
5. GPU or provider model cloud only when a later frozen gate names the spend and expected evidence.

No GPU or provider model run is authorized by `iter00`, `iter01`, `iter02`, `iter03`, `iter04`, or
`iter05`.

## After The Agent-Behavior Smoke Gate

If the smoke gate passes:

1. Publish the receipt and parsed artifacts.
2. Freeze the first non-trivial edit-agent run.
3. Consider a provider-model run only after the deterministic path proves receipt quality.
4. Escalate to sandbox/cloud only if the frozen run requires isolation or compute.

If the smoke gate fails:

1. Publish the failure.
2. Fix the concrete artifact gap or choose a narrower deterministic agent path.
3. Do not start a model run.
