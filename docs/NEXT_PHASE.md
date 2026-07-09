# Next Phase

## Current Action

Run `iter41_public_task_protocol_effect_runner_recovery` exactly as frozen in
[`../experiments/iter41_public_task_protocol_effect_runner_recovery/HYPOTHESIS.md`](../experiments/iter41_public_task_protocol_effect_runner_recovery/HYPOTHESIS.md).

The output is not a leaderboard score. It is a bounded runner-recovery gate:

- keep
  [`../experiments/iter31_claim_boundary_release_manifest/proof/claim_boundary_release_manifest.json`](../experiments/iter31_claim_boundary_release_manifest/proof/claim_boundary_release_manifest.json)
  as the claim-boundary reviewer entry point,
- keep
  [`../experiments/iter35_release_manifest_self_coverage_guard/proof/self_coverage_report.json`](../experiments/iter35_release_manifest_self_coverage_guard/proof/self_coverage_report.json)
  and
  [`../experiments/iter36_release_manifest_self_coverage_negative_guard/proof/negative_guard_report.json`](../experiments/iter36_release_manifest_self_coverage_negative_guard/proof/negative_guard_report.json)
  visible as self-coverage reviewer evidence,
- keep `iter23` and `iter25` visible as failed/null evidence,
- keep the changed `iter24` candidate separate from original `iter21` provider logic,
- keep the `iter35` self-coverage report visible,
- keep the `iter36` self-coverage negative guard visible,
- use only the frozen task identifiers, baseline and Telos-instrumented conditions, and before-data
  metrics from
  [`../experiments/iter39_public_task_protocol_effect_slice/proof/protocol_effect_slice.json`](../experiments/iter39_public_task_protocol_effect_slice/proof/protocol_effect_slice.json),
- use the blocked preflight evidence from
  [`../experiments/iter40_public_task_protocol_effect_execution/proof/preflight.json`](../experiments/iter40_public_task_protocol_effect_execution/proof/preflight.json),
- recover only Docker and pinned CodeClash runner readiness before retrying provider-backed
  execution,
- stop and publish blocked/null evidence if runner or artifact controls remain unavailable,
- keep provider model calls at `0`,
- keep provider spend at `$0.00`,
- do not make production/live-domain, leaderboard, SWE-bench, model-superiority, or
  state-of-the-art claims.

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
`iter12` authorized a minimal access probe. `iter13` through `iter19` stayed inside their frozen
provider-smoke and quality-control gates. `iter20` through `iter23` returned to local semantic
verification. `iter23` failed locally under the explicit `tail_remains_occupied` assumption.
`iter24` passed locally for a changed candidate under the same assumption. `iter25` failed the full
mutation-guard bar because a single own-tail mutation left the self-snake fallback path intact.
`iter26` passed the compound own-tail mutation guard. `iter27` passed the claim-boundary matrix.
`iter28` passed the public claim-surface guard. `iter29` passed the negative public-claim fixture
guard. `iter30` passed the boundary-matrix schema guard. `iter31` passed the claim-boundary release
manifest. `iter32` passed the release-manifest negative guard. `iter33` passed the public-sync
guard. `iter34` passed the public-sync negative guard. `iter35` passed the release-manifest
self-coverage guard. `iter36` passed the self-coverage negative guard. `iter37` passed the
self-coverage public-sync guard. `iter38` passed the self-coverage public-sync negative guard.
`iter39` passed the public-task protocol-effect slice-selection gate. `iter40` blocked before
provider execution because Docker and pinned CodeClash runner readiness were not established.
`iter41` authorizes only runner recovery and does not authorize provider model calls, GPU,
leaderboard, SWE-bench result, production, live-domain behavior, model-superiority, or
state-of-the-art claims.

## After The Runner-Recovery Gate

If the runner-recovery gate passes:

1. Publish Docker, pinned CodeClash, dependency, config-path, artifact, and zero-provider-call
   evidence.
2. Pre-register a retry of the frozen protocol-effect execution.
3. Do not widen model, budget, task, or claim scope.

If the runner-recovery gate blocks or fails:

1. Publish the blocked/null or quality-failure result.
2. Correct only the specific runner, artifact, or harness gap.
3. Keep prior proof artifacts unchanged unless the evidence identifies a real structural gap.
