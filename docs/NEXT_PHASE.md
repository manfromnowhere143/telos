# Next Phase

## Current Action

Run `iter38_release_manifest_self_coverage_public_sync_negative_guard` exactly as frozen in
[`../experiments/iter38_release_manifest_self_coverage_public_sync_negative_guard/HYPOTHESIS.md`](../experiments/iter38_release_manifest_self_coverage_public_sync_negative_guard/HYPOTHESIS.md).

The output is not a leaderboard score. It is a negative public-sync guard for the release-manifest
self-coverage layer:

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
- prove malformed public prose that hides self-coverage or bypasses claim boundaries is rejected,
- do not call a provider model, run CodeClash, or make production/live-domain claims.

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
self-coverage public-sync guard. `iter38` does not authorize provider, GPU, cloud, CodeClash,
leaderboard, SWE-bench, production, or live-domain behavior.

## After The Release Manifest Self-Coverage Public Sync Negative Guard

If the negative guard passes:

1. Publish proof that malformed public prose is rejected.
2. Keep the release manifest as the claim-boundary reviewer entry point.
3. Do not expand to provider, leaderboard, SWE-bench, or production claims.

If the negative guard fails:

1. Publish the quality failure.
2. Correct only the negative-fixture harness or specific stale public reference.
3. Keep prior proof artifacts unchanged unless the evidence identifies a real structural gap.
