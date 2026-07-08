# Next Phase

## Current Action

Run `iter11_provider_model_pilot_retry` exactly as frozen in
[`../experiments/iter11_provider_model_pilot_retry/HYPOTHESIS.md`](../experiments/iter11_provider_model_pilot_retry/HYPOTHESIS.md).

The output is not a leaderboard score. It is the first paid provider-backed agent-attempt smoke:

- keep the already frozen model, task, and budget unchanged,
- verify ADC again before the run without printing tokens, API keys, account emails, credential
  JSON, or project identifiers,
- run the one-round CodeClash BattleSnake provider smoke only under the `$25` ceiling,
- publish blocked/null evidence if the provider endpoint, LiteLLM, CodeClash, cost accounting, or
  credential path fails.

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
`iter10` restored the credential path without calling a model. `iter11` authorizes only the same
single frozen paid smoke under the original `$25` ceiling.

## After The Provider Pilot Retry Gate

If the provider smoke passes:

1. Publish the raw artifacts, receipt, cost record, diff summary, and review.
2. Freeze the first analysis gate from the observed agent behavior.
3. Do not start sweeps or leaderboard submissions.

If the provider smoke blocks or fails:

1. Publish the failure.
2. Do not widen model, budget, or task scope.
3. Keep the blocker explicit in `HANDOFF.md`.
