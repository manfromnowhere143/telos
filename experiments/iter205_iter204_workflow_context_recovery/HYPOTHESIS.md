# Iteration 205 - Workflow-Context Recovery for the Fixed Iter202/Iter203 Corpus

Status: **ACTIVE PRE-DISPATCH / PRE-SCIENTIFIC-OUTPUT WORKFLOW-CONTEXT RECOVERY**. Frozen after
iter204 closed as a pre-dispatch infrastructure null and before any iter205 dispatch request, workflow
run, provider call, container invocation, patch application, official certification, scenario execution,
adjudication, or blind-judge outcome. This is a separately identified recovery designed with full
knowledge of the iter204 admission failure. It is not a retry or mutation of iter204.

Date: 2026-07-16.

## Why a new iteration is required

The approved iter204 source commit was `c1137f896b7ee3c9a26ee35bcda2c5f5c6b79446`. Primary
`ci.yml` push run `29465925393`, attempt `1`, completed successfully with both required jobs. The public
workflow API nevertheless exposes two iter204 records created by `push` validation of the invalid
workflow source:

- run `29465584664`, attempt `1`, at source
  `8342315dd2fa7ec865bd7c654ec4ec098675dfab`;
- run `29465924803`, attempt `1`, at the approved primary-branch merge commit.

Both have event `push`, conclusion `failure`, zero jobs, zero artifacts, and no available log download.
They are infrastructure parse-failure records, not dispatch runs or scientific attempts. The complete
read-only public query contains exactly zero iter204 `workflow_dispatch` runs.

After primary CI passed, at least one locally observed iter204 dispatch API request returned HTTP `422`
while parsing line `318`, column `36`: `runner.temp` was referenced from job-level `env`, where that
context is unavailable. The exact request count is not publicly auditable and is not asserted; the
conservative observed lower bound is one. The rejected request created no run, so it has no run ID, run
attempt, public workflow-dispatch job log, or public workflow-dispatch run log.

No iter204 provider process, container create/run invocation, patch application, certification, scenario,
adjudication, or judge process started. Iter204 produced no scientific artifact and contributes no `N`,
`k`, or `u`; those quantities are absent, not zero. Its frozen no-retry rule requires the workflow-context
correction to occur only under a separately identified iteration.

## Immutable evidence anchors

Before any iter205 dispatch, a deterministic guard must reproduce the exact normalized iter204 admission
null and every public snapshot it binds. The following hashes and identities are frozen:

- iter204 approved merge/source commit:
  `c1137f896b7ee3c9a26ee35bcda2c5f5c6b79446`;
- iter204 primary CI: run `29465925393`, attempt `1`, successful, with required jobs
  `verify py3.11` and `verify py3.12` successful;
- iter204 workflow object: ID `314113289`, server-name fallback
  `.github/workflows/iter204-execute.yml`, path `.github/workflows/iter204-execute.yml`, state `active`;
  workflow-source SHA-256
  `84f7f8b228624ff7244991e317e7f8146a6aacd93f803c1df983b6cceae4deb4`;
- iter204 hypothesis SHA-256
  `7f6b9e0ba0ba0077115e64e38239a6eeafb2b18797fdd160a3eb9c0297396dfd`;
- iter204 runtime-manifest SHA-256
  `bf2062825e604d9439b0d29375d7e5219a1064ae4a33701efb74a62f81a59a45`;
- iter204 runtime closure: `294` files, closure SHA-256
  `d0992ff4a10c931ebc1f582a98c4719475513d63f89e25ae58707c4b5d0a1cfb`;
- iter204 pre-execution publication-safety receipt SHA-256
  `8cdfdaa6139076b730556743ce1e9c8519fcc27782d2efd19b1645610ac91308`;
- iter204 pre-dispatch infrastructure-null receipt SHA-256
  `59fcde5ff323a406d4ea3c3ab0de30db31a9d1bd7367e6b2a5a29194bc741aa8`;
- iter204 public-dispatch-metadata manifest SHA-256
  `8f20922002f3029e96d60078ace644e0cf56f758c692c3f35a07d5fe7f19081b`;
- iter203 runtime-manifest SHA-256
  `8beb0e845dbc9e3a4ce56832f28a62d4fd58ceac20adbc6bc06d6aef41be47e1`;
- iter203 sole canonical run `29460393525`, attempt `1`;
- iter203 hypothesis SHA-256
  `c11970a62f8a76d77cdcb42c0e7e76d1a652306d71b0c2b1ae134171abb9e5eb`;
- iter203 upstream-protocol-null SHA-256
  `43260655374b00f18b4791301b3569b599b0a2439fc84dfb36dd36e8a4f3b6ea`;
- iter203 pre-execution publication-safety receipt SHA-256
  `78a90912e2d2ced4d861737668b1e98ec5653e5c2ca8b12342bbf52d1f847d81`.

For release-boundary provenance only, the iter204 merge commit contained `CONTINUITY.md` with SHA-256
`f1697422382aafe9928464536e94fee3b65fd939c7e3b47420b65407e65d26aa` and `HANDOFF.md` with
SHA-256 `29be9c8e04d6c1bcb61782200b8e6bcffee761b283b7bb532c700ff7e8162bd8`. They are historical
iter204 release records at that commit, not immutable current-facing instructions for iter205.

No iter202, iter203, or iter204 provider response, checkpoint, patch, official spec, eval script, image
lock, scenario, safety disposition, source manifest, runtime manifest, null receipt, or public metadata
snapshot may be mutated, regenerated, relabeled, selected, or replaced.

## Exact allowed delta

Iter205 may change only the following additive runtime-bound surfaces:

1. mechanically change iter204 identities to separately versioned iter205 identities across the new
   workflow path/name, experiment path, schemas, environment fields, artifact names, sentinel text,
   diagnostics, shard receipts, aggregate receipt, collector, adjudicator, and judge wrappers;
2. move the iter205 smoke-receipt path expression using `runner.temp` from job-level `env` to the exact
   execution step's `env`, where the runner context is available;
3. add guards that bind and validate the iter204 pre-dispatch infrastructure-null receipt and its exact
   public metadata snapshots; and
4. strengthen server-side workflow-object, all-event history, dispatch-history, current-run, and upstream
   iter204-history validation required to prevent another ambiguous admission.

The change in item 2 is context plumbing only. It may not change the smoke command, scientific input,
container arguments, shard assignment, execution limits, evidence eligibility, or outcome rule. Any other
source delta requires a new protocol before dispatch; it may not be folded into iter205.

## Frozen scientific plan

Iter205 executes exactly the already-fixed iter203/iter204 scientific plan:

1. preserve all `50` model patches, all `50` paired gold patches, all `50` official specs and eval
   scripts, their exact byte hashes, and their exact global ordinal order;
2. preserve exactly eight zero-based shards, with global row ordinal `i` assigned only to shard
   `i mod 8`, the same ordered membership, and at most seven rows per shard;
3. certify every one of the `50` fixed model patches through the official harness, independent of gold
   equivalence and scenario disposition;
4. preserve the existing scenario disposition: exactly `29` byte-identical safety-admitted witnesses,
   `9` rejected witnesses, and one original absent witness;
5. mount and execute only the current row's indexed safety-admitted witness under model and gold; never
   copy, mount, run, repair, replace, or reinterpret a rejected or absent witness;
6. preserve the immutable image references and IDs, no-network and least-privilege container policy,
   resource and output bounds, timeout treatment, patch application, official certification framing, and
   scenario comparison from iter204; and
7. preserve all denominator, missingness, adjudication, blinding, prompt, endpoint-family, model,
   token-cap, parser, unanimity, prior-use-stratum, and descriptive-pooling rules from iter203/iter204.

There is no solver call, scenario-generation call, provider regeneration, target replacement, resharding,
safety-policy change, scenario repair, threshold change, or scientific reinterpretation. No scientific
input or expected outcome is introduced by this workflow-context recovery.

The exact local logging tuple remains:

```text
--log-driver local
--log-opt max-size=3m
--log-opt max-file=1
--log-opt compress=false
```

The inert no-science smoke remains required before any shard. Its only mechanical identity update is the
iter205 sentinel and receipt schema. It uses the frozen global ordinal-`0` image, no mounts, no patch-,
spec-, or scenario-derived input, and the exact production isolation/logging tuple. Each row retains the
never-started `docker create` preflight and visible bounded launch diagnostics declared by iter204.
Diagnostics remain infrastructure evidence and are never eligible as certification, scenario,
adjudication, denominator, or rate evidence.

## Server-side admission and sole-dispatch rule

Implementation, tests, this hypothesis, the new runtime manifest, and the new workflow must be committed
and pass primary-branch CI before any dispatch request. Immediately before dispatch, a read-only
server-side preflight must prove all of the following:

1. `.github/workflows/iter205-execute.yml` resolves to a workflow object whose name is exactly
   `iter205-execute`, path is exactly `.github/workflows/iter205-execute.yml`, and state is exactly
   `active`;
2. the complete unfiltered iter205 workflow history is empty across all events and commits;
3. the complete iter205 history filtered to `workflow_dispatch` is empty;
4. the approved source is an exact 40-hex commit on `master`, descends from the frozen iter204 merge, and
   has one successful completed primary `ci.yml` push run with both required verification jobs green; and
5. the iter204 server history still contains exactly the two declared `push` parse-failure records, each
   with zero jobs and artifacts, and contains zero `workflow_dispatch` runs.

Only after that preflight may exactly one iter205 dispatch request be issued for the approved commit.
Authorization inside the created run must re-prove the workflow object, approved source and primary CI,
the exact iter204 history, and that the complete all-event iter205 history and complete iter205 dispatch
history each contain exactly the current run. The current event must be `workflow_dispatch`, its path and
source must match, and both the workflow's run-attempt value and `GITHUB_RUN_ATTEMPT` must equal `1`.

There is no iter205 attempt `2`, workflow rerun, second dispatch request, or replacement run. Any API
rejection, parser record, authorization failure, smoke failure, shard failure, collector failure, mixed
attempt, or incomplete same-run eight-shard corpus closes iter205 as an infrastructure null and advances
recovery to separately identified iter206. A dispatch request rejected before run creation is not called
attempt `1`; it has no run attempt. It still closes iter205 and may not be reissued.

Declared row-level scientific missingness after a complete eligible aggregate remains `u` under the
frozen measurement policy; it is not confused with an incomplete execution corpus.

## Evidence custody, measurement, and adjudication

After authorization and the exact no-science smoke succeed:

1. all eight shards must run under one workflow run, attempt `1`, and cover the exact frozen membership;
2. every successful shard must emit the separately versioned iter205 shard receipt binding its exact log
   set, runtime manifest, upstream manifests, approved commit, workflow run, run attempt, smoke receipt,
   observed host record, and primary-CI authorization;
3. the collector must accept exactly eight uniquely named successful attempt-`1` shard artifacts from
   that run, reject every missing, extra, duplicate, colliding, debug, mixed-provenance, or hash-drift
   input, merge without overwrite, and produce one canonical iter205 aggregate receipt; and
4. adjudication and blind judging may consume only an exact in-memory log snapshot reverified against that
   complete aggregate and the iter205 runtime manifest.

The scientific definitions remain unchanged. `N` is every officially certified patch among all `50`.
`k` is the count with a retained divergent safety-admitted witness and both blind judges naming only the
model output wrong. `u` is every certified differing patch still missing a valid complete scientific
outcome. Report together the confirmed lower quantity `k/N`, the declared-missing-outcome upper quantity
`(k+u)/N`, and complete-case sensitivity `k/(N-u)`, with the frozen strata and corrected descriptive
pooling rules. Missing outcomes are never silently negative, and the upper quantity is not a bound on all
semantically wrong patches.

## Bars and falsifiers

- the iter204 null receipt and public metadata manifest reproduce at their frozen hashes;
- the exact frozen iter203 and iter204 runtime-manifest bytes and hashes validate as immutable historical
  anchors, including the recorded `294`-file iter204 closure, while the new iter205 runtime manifest
  deterministically reconstructs the current allowed source plus those frozen inputs;
- iter205 contains only the four classes of allowed delta declared above;
- server admission proves the exact active workflow object and empty pre-dispatch all-event and dispatch
  histories;
- exactly one dispatch request is made, and only a created attempt-`1` run is eligible;
- the exact `50` rows and order, eight-shard assignment, `29` safety-admitted witnesses, `9` rejected
  witnesses, and one absent witness remain unchanged;
- no scientific command begins before the exact smoke succeeds;
- no solver or scenario provider call occurs;
- all `50` fixed rows enter official certification exactly once in a complete eligible corpus;
- no rejected, absent, or unindexed scenario byte is mounted or executed;
- no infrastructure metadata, diagnostic, missing artifact, or absent run is interpreted as a patch
  outcome;
- every reported positive has official certification, a retained divergent safety-admitted witness, and
  two strict blind confirmations; and
- every declared missing outcome remains explicit under the frozen `u` policy.

The recovery is falsified by any upstream byte drift; in-place iter204 correction; unexpected iter205
workflow history; a second request or run; any run attempt other than `1`; source outside the approved
primary commit; a delta beyond the declared workflow-context scope; target, order, shard, image, scenario,
container, adjudication, or judge drift; partial shard selection; mixed attempts; unsafe scenario exposure;
provider regeneration; missingness imputed negative; or a claim that treats infrastructure events as
science.

## Null and claim policy

A server-object mismatch, nonempty pre-dispatch history, parser record, API rejection, authorization
failure, smoke failure, incomplete shard set, or collector failure is an iter205 infrastructure null. It
produces no denominator and requires iter206; no iter205 retry is permitted. Inability to validate any
frozen input at its exact historical bytes and hash is a provenance null and forbids dispatch. After a
complete eligible aggregate, the existing solve-yield and observed-lower-bound null rules remain
unchanged.

At most, after complete execution and blind adjudication: for the fixed iter202 localized-solve outputs,
under the disclosed post-provider safety recovery and two separately disclosed infrastructure recoveries,
`k` of `N` officially certified patches were strictly blind-confirmed naturally occurring
certified-yet-wrong, with mandatory missingness quantities and sensitivity strata. Any pooled quantity is
descriptive for the two fixed, disjoint neutral-solve cohorts only. No population-frequency,
model-comparison, leaderboard, deployment, or generalization claim is authorized.
