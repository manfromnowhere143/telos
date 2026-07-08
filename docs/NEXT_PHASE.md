# Next Phase

## Current Action

Run `iter09_provider_model_pilot_smoke` exactly as frozen in
[`../experiments/iter09_provider_model_pilot_smoke/HYPOTHESIS.md`](../experiments/iter09_provider_model_pilot_smoke/HYPOTHESIS.md).

The output is not a model score. It is a paid-provider smoke receipt:

- run only the selected Google Vertex AI `gemini-3.1-pro-preview-customtools` pilot,
- cap the run at 8 model invocations, 4096 output tokens per call, 45 minutes, and $25,
- preserve metadata, logs, trajectory, agent stats, diff-scope artifacts, and cost evidence,
- produce a valid Telos receipt,
- publish blocked/null evidence if preflight, endpoint resolution, cost accounting, or artifact
  capture fails.

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
`iter05`. `iter06`, `iter07`, and `iter08` also forbid provider model calls and GPU runs. `iter09`
authorizes only the single frozen paid smoke.

## After The Provider-Model Pilot Smoke Gate

If the smoke gate passes:

1. Publish the receipt, parsed artifacts, cost evidence, and review.
2. Decide whether a second provider run is justified by the evidence.
3. Do not start sweeps or leaderboard submissions without a new frozen gate.

If the smoke gate fails:

1. Publish the failure.
2. Fix only the concrete preflight, adapter, or artifact gap.
3. Do not broaden provider scope.
