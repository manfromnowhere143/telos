# Iteration 203 Result - Docker-Configuration Infrastructure Null

Status: **INFRASTRUCTURE NULL**. The sole canonical iter203 dispatch, GitHub Actions run
[`29460393525`](https://github.com/manfromnowhere143/telos/actions/runs/29460393525), attempt `1`, failed
before any in-container certification or scenario command started. This result seals that run; it does not
reinterpret it as a scientific outcome.

## Canonical run

- approved source commit: `5c409f79c9333206cff9ed80d59c08aa347110f6`;
- workflow authorization: successful;
- execution matrix: all `8/8` shards reached the frozen runner and assigned all `50` fixed rows;
- image provenance: all `50/50` assigned images were pulled and digest-verified;
- first Docker `run` invocation for every row: raw exit `125` before any in-container command; no
  container start is counted;
- receipt-eligible execution logs: `0`;
- shard receipts: `0`;
- uploaded workflow artifacts: `0`;
- collection job: skipped because every shard failed closed;
- official certification executions: `0`;
- generated-scenario executions: `0`.

Each failed Docker invocation redirected its engine diagnostic into a hidden temporary row log. The failure
branch then deleted that file, and the failure upload retained nothing. The eight exact public shard logs
prove all `50` row-level `CERTIFICATION_INFRA_FAIL exit=125` events. The canonicalized public jobs response
records successful authorization, eight failed shard jobs, and skipped collection; the canonicalized
artifacts response records `total_count=0`. Runner control flow proves no scenario path was reached. The
exact daemon stderr is not retained in attempt `1`. The normalized snapshot in
`proof/infrastructure_null.json` is hand-authored evidence derived from those workflow records, not a raw
workflow artifact.

## Root cause

The deterministic source/configuration diagnosis is that the runner selected Docker's `local` log driver
with `max-size=3m` and `max-file=1` but did not override compression. In Docker Engine `28.0.4`, local-driver
compression is enabled by default and is invalid when `max-file` is `1`. This diagnosis follows from the
committed argument vector and engine source semantics, not from preserved attempt-`1` daemon stderr.

The implementation binding is Moby tag `v28.0.4`, peeled commit
`6430e49a55babd9b8f4d08e70ecb2b68900770fe`, file `daemon/logger/local/config.go`. The narrow correction is
to retain the frozen driver, size, and file-count policy while adding `compress=false`.

The public runner record identifies Ubuntu runner image `20260714.240.1`; its primary release is
[`ubuntu24/20260714.240`](https://github.com/actions/runner-images/releases/tag/ubuntu24/20260714.240).
The relevant Moby source is
[`daemon/logger/local/config.go`](https://github.com/moby/moby/blob/6430e49a55babd9b8f4d08e70ecb2b68900770fe/daemon/logger/local/config.go#L30-L33).

This is a harness-configuration fault. It is not a patch failure, a certification result, a scenario
result, or a provider-availability result. The mechanical workflow made no provider call and did not depend
on provider credits or credentials.

## Scientific interpretation

Iter203 contributes no `N`, `k`, or `u`; those quantities are absent, not zero. There is no valid
certification outcome and no scenario execution. Iter203 provides no update to the corrected iter200 result
and no pooled analysis. No patch-level outcome may be inferred from an image pull, digest verification,
Docker exit `125`, missing diagnostic, or absent workflow artifact.

The iter202 and iter203 provider, bridge, solution, specification, scenario, and runtime-bound bytes remain
fixed. Because correcting the Docker arguments changes runtime-bound source, iter203 attempt `1` must not be
rerun or replaced. Recovery proceeds only under the separately identified iter204 protocol in
[`../iter204_iter203_infrastructure_recovery/HYPOTHESIS.md`](../iter204_iter203_infrastructure_recovery/HYPOTHESIS.md).

## Claim boundary

Supported: the authorized iter203 workflow exposed a deterministic Docker logging-configuration defect and
failed before all `50` planned scientific container commands, leaving no official execution corpus.

Not supported: any solve-yield, certification, wrongness, missingness, rate, pooled, population-frequency,
model-comparison, leaderboard, deployment, state-of-the-art, or generalization claim.

## Evidence

- public workflow run `29460393525`, attempt `1`;
- `proof/infrastructure_null.json` - normalized public workflow evidence and exact public job-log hashes;
- `proof/raw/public_workflow_logs/` - exact eight raw public job-log API responses and manifest;
- `proof/raw/public_workflow_metadata/` - canonicalized public jobs/artifacts API responses and manifest;
- `HYPOTHESIS.md` - the frozen iter203 protocol;
- `proof/raw/runtime_manifest.json` - the frozen iter203 runtime manifest.
