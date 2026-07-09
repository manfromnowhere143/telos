# Iteration 61 - Vertex Quota Project Binding Recovery

Status: pre-registered, result pending.

## Purpose

Recover the provider quota-project/header binding that blocked `iter60`.

`iter60` proved that adding `vertex_location: global` changes the `iter59` model-not-found failure
into a redacted Vertex `CONSUMER_INVALID`/permission response in the LiteLLM path. Earlier direct
REST evidence from `iter56` succeeded with the same model and global location while sending
`X-Goog-User-Project`. This gate may only recover the missing quota-project/header path for
LiteLLM/CodeClash. It may not execute a BattleSnake row or broaden the task slice.

This is not a leaderboard run, not a SWE-bench score, not a production/live-domain result, not a
model-superiority result, and not a state-of-the-art claim.

## Frozen Input

- Iter60 blocked run summary:
  `experiments/iter60_provider_model_binding_recovery/proof/run_summary.json`.
- Iter60 model-binding recovery report:
  `experiments/iter60_provider_model_binding_recovery/proof/model_binding_recovery_report.json`.
- Iter60 recovered overlay:
  `experiments/iter60_provider_model_binding_recovery/proof/recovered_overlay/configs/mini/telos_vertex_gemini_3_1_pro_customtools.yaml`.
- Iter56 successful direct Vertex access probe:
  `experiments/iter56_provider_auth_recovery_for_paid_protocol_effect/proof/vertex_access_probe.json`.

## Execution Envelope

The gate may perform only quota-project/header recovery checks:

- inspect the LiteLLM Vertex adapter and CodeClash Mini-SWE-Agent config path,
- test a minimal LiteLLM probe with a secret-safe quota-project/header injection path,
- write a recovered wrapper/config artifact only if it does not commit project, account,
  service-account, token, VM, zone, or credential material,
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

1. preflight showing iter60 is a clean blocked result with redacted `CONSUMER_INVALID` evidence,
2. exact before/after quota-project/header binding mechanism,
3. exact provider probe command(s), if any, with redacted logs,
4. provider call and cost counts,
5. proof that zero BattleSnake rows and zero excluded pairs executed,
6. proof that no GPU, Sentinel resource, cloud runner, production/live-domain action, or overclaim
   occurred,
7. redaction scan over all committed artifacts,
8. human-readable adversarial review,
9. machine-readable run summary with artifact hashes,
10. a next gate that retries the same two selected BattleSnake rows only if this recovery passes.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- iter60 is a blocked result after setting `vertex_location: global`,
- the iter60 blocked probe contains redacted `CONSUMER_INVALID` evidence,
- the recovered binding path lets LiteLLM call the same model through Vertex without committing
  project/account/credential material,
- provider calls are `<= 2`,
- provider spend is `<= $0.05`,
- zero BattleSnake rows execute,
- zero excluded pairs execute,
- no GPU, Sentinel resource, cloud runner, production/live-domain mutation, or overclaim occurs,
- every committed artifact passes redaction.

## Falsifiers

Publish blocked evidence if:

- iter60 proof is missing, failed, or does not contain the named quota-project/header blocker,
- no secret-safe LiteLLM quota-project/header path can be identified inside the call/spend ceiling,
- exact cost/call evidence cannot be committed safely,
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

If successful, this gate may claim only that the LiteLLM Vertex quota-project/header blocker was
recovered for a future retry of the same two-row pilot. It may not claim a protocol-effect result,
benchmark result, SWE-bench score, leaderboard position, production/live-domain behavior, model
superiority, or state-of-the-art result.
