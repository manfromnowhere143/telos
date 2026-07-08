# Next Phase

## Current Action

Run `iter12_vertex_model_access_recovery` exactly as frozen in
[`../experiments/iter12_vertex_model_access_recovery/HYPOTHESIS.md`](../experiments/iter12_vertex_model_access_recovery/HYPOTHESIS.md).

The output is not a leaderboard score. It is an access-recovery result:

- verify whether the selected Vertex model path is reachable by the runner identity,
- keep tokens, account emails, credential JSON, and project identifiers out of committed logs,
- use only minimal provider-access probes, not a CodeClash run,
- either recover `gemini-3.1-pro-preview-customtools` predict access or freeze a new reachable
  provider-model slice before retrying the smoke.

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
authorized only the single frozen paid smoke, but it stopped before spend because preflight failed.
`iter10` restored the credential path without calling a model. `iter11` authorized only the same
single frozen paid smoke under the original `$25` ceiling; it blocked on Vertex predict permission.
`iter12` does not authorize CodeClash. It only recovers or replaces the provider access path.

## After The Vertex Access Recovery Gate

If access recovery passes:

1. Freeze the exact next provider smoke retry with model, region, runner, and budget.
2. Preserve the same evidence bars and redaction rules.
3. Do not start sweeps or leaderboard submissions.

If access recovery blocks or fails:

1. Publish the failure.
2. Do not widen model, budget, or task scope.
3. Keep the blocker explicit in `HANDOFF.md`.
