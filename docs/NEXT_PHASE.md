# Next Phase

## Current Action

Run `iter10_provider_auth_recovery` exactly as frozen in
[`../experiments/iter10_provider_auth_recovery/HYPOTHESIS.md`](../experiments/iter10_provider_auth_recovery/HYPOTHESIS.md).

The output is not a model score. It is an authentication readiness result:

- restore non-interactive ADC or configure a GitHub Workload Identity / secret path,
- verify readiness without printing tokens, API keys, account emails, credential JSON, or project
  identifiers,
- keep the already frozen `iter09` model, task, and budget unchanged,
- publish blocked/null evidence if credential readiness still requires interactive auth.

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
`iter10` does not authorize a model call.

## After The Provider Auth Recovery Gate

If the auth gate passes:

1. Retry the existing `iter09` smoke without changing model, budget, or task.
2. Preserve the same evidence bars and stop conditions.
3. Do not start sweeps or leaderboard submissions.

If the auth gate fails:

1. Publish the failure.
2. Do not retry the paid smoke.
3. Keep the blocker explicit in `HANDOFF.md`.
