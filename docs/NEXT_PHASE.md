# Next Phase

## Current Action

Run `iter07_deterministic_edit_smoke` exactly as frozen in
[`../experiments/iter07_deterministic_edit_smoke/HYPOTHESIS.md`](../experiments/iter07_deterministic_edit_smoke/HYPOTHESIS.md).

The output is not a model score. It is a deterministic non-empty diff receipt:

- apply the committed CodeClash overlay,
- run the selected BattleSnake deterministic edit config,
- preserve metadata, logs, trajectory, agent stats, and diff-scope artifacts,
- prove `p1` modified `telos_marker.py`,
- keep provider API/GPU spend at zero,
- produce a valid Telos receipt.

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

## After The Deterministic Edit Smoke Gate

If the smoke gate passes:

1. Publish the receipt and parsed artifacts.
2. Freeze the first provider-model run only if it names model, budget, task, and expected evidence.
3. Escalate to sandbox/cloud only if the frozen run requires isolation or compute.

If the smoke gate fails:

1. Publish the failure.
2. Fix the concrete artifact gap or choose a narrower edit path.
3. Do not start a model run.
