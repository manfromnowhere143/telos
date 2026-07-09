# Iteration 62 - Vertex Bearer Token Path Recovery

Status: pre-registered, result pending.

## Purpose

Recover the remaining provider access-path blocker after `iter61`.

`iter56` proved the selected Vertex global endpoint can answer a direct REST request when the
request uses a suppressed ADC bearer token and `X-Goog-User-Project`. `iter61` proved that
Mini-SWE-Agent can pass `extra_headers` into LiteLLM, but the LiteLLM-managed Vertex auth path
still returned a redacted `CONSUMER_INVALID` response. This gate may test only whether a
secret-safe runtime bearer-token injection path restores parity with the direct REST probe.

This is not a leaderboard run, not a SWE-bench score, not a production/live-domain result, not a
model-superiority result, and not a state-of-the-art claim.

## Frozen Input

- Iter61 blocked run summary:
  `experiments/iter61_vertex_quota_project_binding_recovery/proof/run_summary.json`.
- Iter61 redacted LiteLLM probe stderr:
  `experiments/iter61_vertex_quota_project_binding_recovery/proof/litellm_quota_probe_stderr.txt`.
- Iter56 successful direct Vertex access probe:
  `experiments/iter56_provider_auth_recovery_for_paid_protocol_effect/proof/vertex_access_probe.json`.

## Execution Envelope

The gate may perform only bearer-token/path recovery checks:

- inspect LiteLLM Vertex header precedence and token handling,
- test a minimal LiteLLM probe that injects a fresh bearer token at runtime without logging or
  committing it,
- write a recovered runtime binding template only if it commits no token, project, account,
  service-account, VM, zone, or credential material,
- execute no BattleSnake row,
- execute no excluded historical pair,
- use no GPU,
- modify no Sentinel-named resource,
- make no production/live-domain mutation.

Hard ceilings:

- provider model invocations: `<= 2`,
- provider spend: `<= $0.05`,
- cloud runner: forbidden,
- BattleSnake row execution: forbidden.

## Required Evidence

The proof packet must include:

1. preflight showing iter61 is a clean blocked result with redacted `CONSUMER_INVALID` evidence,
2. source-path evidence for LiteLLM header precedence or a clear blocker if it cannot be proven,
3. exact runtime token/header binding mechanism without committed secret values,
4. exact provider probe command(s), if any, with redacted logs,
5. provider call and cost counts or a bounded-cost proof,
6. proof that zero BattleSnake rows and zero excluded pairs executed,
7. proof that no GPU, Sentinel resource, cloud runner, production/live-domain action, or overclaim
   occurred,
8. redaction scan over all committed artifacts,
9. human-readable adversarial review,
10. machine-readable run summary with artifact hashes.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- iter61 is a blocked result after a LiteLLM `extra_headers` quota-project probe,
- the iter61 blocked probe contains redacted `CONSUMER_INVALID` evidence,
- a runtime bearer-token/header path lets LiteLLM call the same Vertex global model without
  committing project/account/credential material,
- provider calls are `<= 2`,
- provider spend or bounded spend is `<= $0.05`,
- zero BattleSnake rows execute,
- zero excluded pairs execute,
- no GPU, Sentinel resource, cloud runner, production/live-domain mutation, or overclaim occurs,
- every committed artifact passes redaction.

## Falsifiers

Publish blocked evidence if:

- iter61 proof is missing, failed, or does not contain the named access-path blocker,
- no secret-safe LiteLLM bearer-token/header path can be identified inside the call/spend ceiling,
- call/cost evidence cannot be committed safely,
- redaction cannot prove artifacts are secret-safe.

Publish a quality failure if:

- any BattleSnake row executes,
- any excluded historical pair executes,
- provider calls exceed `2`,
- spend exceeds `$0.05`,
- any GPU is used,
- any Sentinel-named resource is modified,
- committed artifacts contain credential, account, project, service-account, VM, zone, token, or
  credential material,
- unsupported benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only that LiteLLM can reach the selected Vertex global model
through a secret-safe runtime bearer-token/header path for a future retry of the same two-row
pilot. It may not claim a protocol-effect result, benchmark result, SWE-bench score, leaderboard
position, production/live-domain behavior, model superiority, or state-of-the-art result.
