# Iteration 63 - Vertex Access Path Parity Recheck

Status: pre-registered, result pending.

## Purpose

Determine whether the current blocker is stale provider access or a LiteLLM-specific request path
gap.

`iter56` recorded a passing direct REST Vertex probe. `iter61` and `iter62` showed that LiteLLM can
accept runtime quota-project and bearer-token headers, but still returns redacted `CONSUMER_INVALID`
evidence. This gate may only run a current direct REST probe and, if justified, one matching
LiteLLM probe to compare access-path parity. It may not execute a BattleSnake row.

This is not a leaderboard run, not a SWE-bench score, not a production/live-domain result, not a
model-superiority result, and not a state-of-the-art claim.

## Frozen Input

- Iter62 blocked run summary:
  `experiments/iter62_vertex_bearer_token_path_recovery/proof/run_summary.json`.
- Iter62 redacted LiteLLM probe stderr:
  `experiments/iter62_vertex_bearer_token_path_recovery/proof/litellm_bearer_probe_stderr.txt`.
- Iter56 historical direct Vertex access probe:
  `experiments/iter56_provider_auth_recovery_for_paid_protocol_effect/proof/vertex_access_probe.json`.

## Execution Envelope

The gate may perform only current access-path parity checks:

- run one current direct REST probe using suppressed ADC bearer token and `X-Goog-User-Project`,
- run at most one matching LiteLLM probe only if direct REST currently passes or the comparison is
  needed to classify the blocker,
- commit no token, project, account, service-account, VM, zone, or credential material,
- execute no BattleSnake row,
- execute no excluded historical pair,
- use no GPU,
- modify no Sentinel-named resource,
- make no production/live-domain mutation.

Hard ceilings:

- provider model invocations: `<= 2`,
- provider spend or bounded spend: `<= $0.05`,
- cloud runner: forbidden,
- BattleSnake row execution: forbidden.

## Required Evidence

The proof packet must include:

1. preflight showing iter62 is a clean blocked result with redacted `CONSUMER_INVALID` evidence,
2. current direct REST probe status with redacted logs,
3. current LiteLLM probe status if run,
4. exact provider call and cost/bounded-cost counts,
5. blocker classification: `direct_rest_now_blocked`, `litellm_specific_parity_gap`, or
   `access_path_recovered`,
6. proof that zero BattleSnake rows and zero excluded pairs executed,
7. proof that no GPU, Sentinel resource, cloud runner, production/live-domain action, or overclaim
   occurred,
8. redaction scan over all committed artifacts,
9. human-readable adversarial review,
10. machine-readable run summary with artifact hashes.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- iter62 is a blocked result after runtime bearer-token/header LiteLLM probing,
- current direct REST and current LiteLLM probes both reach the selected Vertex global model,
- provider calls are `<= 2`,
- provider spend or bounded spend is `<= $0.05`,
- zero BattleSnake rows execute,
- zero excluded pairs execute,
- no GPU, Sentinel resource, cloud runner, production/live-domain mutation, or overclaim occurs,
- every committed artifact passes redaction.

## Falsifiers

Publish blocked evidence if:

- iter62 proof is missing, failed, or does not contain the named access-path blocker,
- current direct REST access no longer passes,
- direct REST passes but LiteLLM still blocks,
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

If successful, this gate may claim only that the current direct REST and LiteLLM access paths both
reach the selected Vertex global model under secret-safe runtime credentials. It may not claim a
protocol-effect result, benchmark result, SWE-bench score, leaderboard position,
production/live-domain behavior, model superiority, or state-of-the-art result.
