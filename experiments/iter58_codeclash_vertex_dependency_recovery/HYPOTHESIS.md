# Iteration 58 - CodeClash Vertex Dependency Recovery

Status: pre-registered, result pending.

## Purpose

Recover the concrete provider-runner dependency that blocked `iter57`, without executing either
paid BattleSnake row.

The question is narrow:

> Can the pinned local CodeClash checkout import the Vertex auth dependency required by LiteLLM
> (`google.auth`) while keeping the pinned checkout, frozen configs, exact command manifest, spend
> ceiling, and claim boundary unchanged?

This is not a benchmark run, not a SWE-bench score, not a leaderboard result, not a
production/live-domain result, not a model-superiority result, and not a state-of-the-art claim.

## Frozen Input

- Iter57 blocked summary:
  `experiments/iter57_provider_compatible_paid_execution_after_auth_recovery/proof/run_summary.json`.
- Iter57 dependency evidence:
  `experiments/iter57_provider_compatible_paid_execution_after_auth_recovery/proof/dependency_block_evidence.json`.
- Iter54 command manifest:
  `experiments/iter54_provider_pair_executor_recovery/proof/command_manifest.json`.
- Pinned local CodeClash checkout:
  `/tmp/telos-codeclash` at commit `381cdfa05a35e8acd35853b9fc7e13005121b127`.

## Execution Envelope

Allowed actions:

- inspect the pinned CodeClash venv and package state,
- install only the minimal missing Vertex auth dependency into the local CodeClash virtualenv,
- verify `import google.auth` from the CodeClash venv,
- verify the pinned CodeClash commit and frozen config hashes are unchanged,
- run Docker and ADC readiness probes with token output suppressed,
- write a machine-readable dependency-recovery report.

Forbidden actions:

- executing either iter57 BattleSnake command,
- executing any excluded Dummy or deterministic-edit pair,
- provider model calls,
- provider spend above `$0.00`,
- GPU use,
- Sentinel-named resource mutation,
- cloud runner startup,
- production/live-domain mutation,
- committed credential, account, project, service-account, VM, zone, or provider-private residue,
- benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or state-of-the-art
  claims.

## Clean-Pass Bar

The gate can pass only if:

- iter57 is a clean blocked result caused by the missing CodeClash Vertex dependency,
- `google.auth` imports successfully from `/tmp/telos-codeclash/.venv/bin/python`,
- the pinned CodeClash commit remains unchanged,
- the iter54 command manifest and the two frozen provider configs remain unchanged,
- no paid BattleSnake row or excluded pair executes,
- provider call and spend counts remain zero,
- no GPU, Sentinel resource, cloud runner, production/live-domain mutation, or overclaim occurs,
- the next action is limited to retrying the same exact two-row paid pilot.

## Falsifiers

Publish blocked evidence if:

- the missing dependency cannot be installed into the local CodeClash virtualenv,
- `google.auth` still cannot import after recovery,
- dependency recovery would require changing the pinned CodeClash source checkout or frozen configs,
- Docker or ADC readiness regresses before the retry can be authorized,
- redaction cannot prove artifacts are secret-safe.

Publish a quality failure if:

- either paid BattleSnake row runs,
- any excluded pair runs,
- any provider model call or provider spend occurs,
- any GPU is used,
- any Sentinel-named resource is modified,
- committed artifacts contain credential, account, project, service-account, VM, zone, or
  provider-private residue,
- unsupported benchmark, leaderboard, SWE-bench, production/live-domain, model-superiority, or
  state-of-the-art claims appear.

## Claim Boundary

If successful, this gate may claim only local CodeClash Vertex dependency readiness for retrying
the exact iter57 two-row paid pilot. It may not claim a protocol-effect result, benchmark result,
SWE-bench score, leaderboard position, production/live-domain behavior, model superiority, or
state-of-the-art result.
