# Iteration 41 - Public Task Protocol-Effect Runner Recovery

Status: pre-registered, result pending.

## Purpose

`iter40` is allowed to execute the frozen public task protocol-effect slice only when provider,
runner, artifact, and cost controls are ready. This gate recovers the runner side of that preflight
without starting a provider model run.

## Frozen Input

- Blocked execution-preflight evidence:
  `experiments/iter40_public_task_protocol_effect_execution/proof/preflight.json`.
- Frozen protocol-effect slice:
  `experiments/iter39_public_task_protocol_effect_slice/proof/protocol_effect_slice.json`.
- Pinned CodeClash commit: `381cdfa05a35e8acd35853b9fc7e13005121b127`.
- Required local or isolated runner checks:
  - Docker daemon answers a bounded readiness probe,
  - pinned CodeClash checkout exists at the expected commit or is freshly cloned to that commit,
  - `uv sync --python 3.11 --extra dev` completes for the pinned checkout,
  - the three frozen CodeClash config paths exist after applying the Telos overlay,
  - artifact destinations are writable,
  - no provider model call starts.

## Verification Plan

1. Run a secret-safe runner preflight with bounded timeouts.
2. Clone or refresh only the pinned CodeClash checkout if needed.
3. Install dependencies for the pinned checkout.
4. Verify the frozen config paths and Telos overlay paths exist.
5. Publish command output, preflight JSON, artifact hashes, receipt, and adversarial review.

## Clean-Pass Bar

The gate can publish a clean pass only if all hold:

- Docker readiness is recorded without hanging,
- pinned CodeClash commit matches `381cdfa05a35e8acd35853b9fc7e13005121b127`,
- dependency installation completes or a checked equivalent cache is recorded,
- all frozen task config paths are present,
- artifact destinations are writable,
- provider model API calls remain `0`,
- provider spend remains `$0.00`,
- no account identifier, project identifier, token, key, or credential path is committed,
- no benchmark, SWE-bench, leaderboard, production, live-domain, model-superiority, or
  state-of-the-art result is claimed.

## Falsifiers

Publish blocked/null evidence if:

- Docker still cannot answer readiness within the bounded timeout,
- the pinned CodeClash checkout cannot be created or verified,
- dependency installation fails,
- any frozen config path is missing,
- artifact destinations are not writable,
- the gate would require a provider model call to prove runner readiness.

Publish a quality failure, not a clean pass, if:

- provider model calls or paid spend occur,
- a different CodeClash commit is used,
- config paths are changed after registration,
- secret material or project/account identifiers appear in artifacts,
- the result claims benchmark/model performance.

## Scope Boundary

This is a runner-recovery gate. It does not execute the provider-backed protocol-effect task pairs
and does not produce a benchmark, SWE-bench, leaderboard, model-superiority, production, or
live-domain result.
