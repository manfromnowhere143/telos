# Iteration 206 - Admission-History Recovery for the Fixed Iter202/Iter203 Corpus

Status: **ACTIVE PRE-PUBLICATION / PRE-DISPATCH / PRE-SCIENTIFIC-OUTPUT ADMISSION-HISTORY
RECOVERY**. Frozen after iter205 closed at its read-only admission gate and before the first remote iter206
branch push, iter206 workflow publication, dispatch request, provider call, container invocation, patch
application, official certification, scenario execution, adjudication, or blind-judge outcome. This is a
separately identified recovery designed with full knowledge of the iter205 null. It is not a retry or
mutation of iter205.

Date: 2026-07-16.

## Why a new iteration is required

Iter205 feature head `a336b4909329d392f6db5f6098792e07a17f28cb` merged as
`4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f`. Primary `ci.yml` push run `29468769187`, attempt `1`,
completed successfully with both required verification jobs. The server accepted workflow object
`314141096` as active with exact name `iter205-execute` and path
`.github/workflows/iter205-execute.yml`. Complete read-only queries returned zero iter205 all-event runs
and zero iter205 `workflow_dispatch` runs.

The same preflight found that the still-active invalid iter204 workflow had appended two more `push`
parse-failure records while iter205 was published:

- run `29468669956`, run number `3`, at the iter205 feature head;
- run `29468768706`, run number `4`, at the iter205 primary merge.

Both additions, like iter204 run numbers `1` and `2`, are completed attempt-`1` `push` failures at the
exact iter204 path with zero jobs, zero artifacts, and HTTP `404` log-download responses. Iter204 still
has zero `workflow_dispatch` runs. Its frozen two-record artifact remains an exact timestamped closure
snapshot, while its append-only server history at the iter205 gate contained four records.

Iter205 preregistered an exact-two live-history predicate. Observing four was a substantive admission
mismatch, so the read-only dispatch block stopped before its dispatch request command. No iter205 dispatch
request was issued, and no dispatch API response or rejection exists. No iter205 workflow run, provider
process, container, patch, certification, scenario, adjudication, or judge process occurred. Iter205
contributes no `N`, `k`, or `u`; those quantities are absent, not zero. Its
no-retry rule requires a separately versioned recovery.

## Immutable evidence anchors

Before any iter206 remote publication or dispatch, the following iter205 bytes and identities are frozen:

- iter205 workflow source SHA-256
  `0bbc39c8b4abbe6ae7dcbd4f9dc5710f835ff06522d8c137b622a9ad6a5a0ad5`;
- iter205 hypothesis SHA-256
  `2b00f43f581176eaf4e134c7e3e3b2a9981f0767545a1f1b21397458bb215395`;
- iter205 runtime-manifest SHA-256
  `1d427fd8e778282127ee8d782c6eb6bb8d6d44e781edceb50ad078474968b04a`;
- iter205 runtime closure: `180` files, closure SHA-256
  `8755fd185f27ef1f45f0450609dfb0d3424a1ba824723458fbcd3f9eb8074986`;
- iter205 pre-execution publication-safety receipt SHA-256
  `1ba7adbea2fb6cf12488e8cf9a3438daadd22809d3d9944ae331bc031587d7da`;
- iter205 pending learning-record SHA-256
  `f38c6443bc74a55ee73404d91e791aa048d77b7c545a02f5bf51e79476a690c7`;
- iter205 feature head `a336b4909329d392f6db5f6098792e07a17f28cb`, merge
  `4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f`, pull request `7`, and successful primary CI run
  `29468769187`, attempt `1`;
- iter205 workflow object ID `314141096`, exact name/path/state, with zero all-event and dispatch runs;
- iter205 pre-dispatch admission-null receipt at
  `experiments/iter205_iter204_workflow_context_recovery/proof/pre_dispatch_admission_null.json`;
- iter205 public-admission-metadata manifest SHA-256
  `6d2216038c7e1f19337795be806bf77eb39150a9be119828bc2967ed160c72ba`;
- iter204 workflow ID `314113289` and the exact four-row baseline below; and
- the frozen iter204 and iter203 anchors already bound by the iter205 runtime manifest and validators.

No iter202, iter203, iter204, or iter205 provider response, checkpoint, patch, official spec, eval script,
image lock, scenario, safety disposition, source manifest, runtime manifest, null receipt, public metadata
snapshot, workflow, hypothesis, or pending learning record may be mutated, regenerated, relabeled,
selected, or replaced.

## Exact four-row iter204 baseline

The admission-time baseline is ordered by `run_number`:

| run number | run ID | branch | source SHA |
|---:|---:|---|---|
| `1` | `29465584664` | `agent/iter204-infrastructure-recovery` | `8342315dd2fa7ec865bd7c654ec4ec098675dfab` |
| `2` | `29465924803` | `master` | `c1137f896b7ee3c9a26ee35bcda2c5f5c6b79446` |
| `3` | `29468669956` | `agent/iter205-workflow-context-recovery` | `a336b4909329d392f6db5f6098792e07a17f28cb` |
| `4` | `29468768706` | `master` | `4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f` |

Every row must retain workflow ID `314113289`, exact fallback name/path
`.github/workflows/iter204-execute.yml`, event `push`, attempt `1`, completed/failure status, zero jobs,
zero artifacts, and HTTP `404` log-download response. The iter204 `workflow_dispatch` history must remain
empty.

## Exact allowed delta

Iter206 may change only these additive runtime-bound surfaces:

1. mechanically change iter205 identities to separately versioned iter206 identities across the new
   workflow, experiment, schemas, environment fields, artifact names, sentinel, diagnostics, receipts,
   collector, adjudicator, and judge wrappers;
2. add the exact iter205 pre-dispatch admission-null receipt, terminal learning record, public metadata,
   and offline guard;
3. replace only the iter205 exact-two upstream-history predicate with the exact-six publication-aware
   predicate below; and
4. bind the exact iter205 active workflow object and empty histories as additional upstream admission
   invariants.

No scientific input, command, smoke semantics, shard membership, image, container argument, resource
limit, certification, scenario, missingness, adjudication, judge, or reporting rule may change. Any other
delta requires a new protocol before publication or dispatch and may not be folded into iter206.

## Frozen scientific plan

Iter206 preserves the fixed iter203/iter204/iter205 scientific plan exactly:

1. all `50` model patches, paired gold patches, official specs, eval scripts, byte hashes, and global row
   order remain unchanged;
2. the same eight zero-based shards assign global row ordinal `i` only to shard `i mod 8`, with the same
   membership and at most seven rows per shard;
3. all `50` model patches enter official certification independent of gold equivalence or scenario
   disposition;
4. exactly `29` safety-admitted witnesses, `9` rejected witnesses with `21` findings, and one original
   absent witness retain their exact disposition and bytes;
5. only a row's indexed safety-admitted witness may be mounted and executed under model and gold; no
   rejected or absent witness may be copied, mounted, run, repaired, replaced, or reinterpreted;
6. immutable image references/IDs, no-network and least-privilege container policy, resource/output
   bounds, timeouts, logging, patch application, certification, scenario comparison, and diagnostics are
   unchanged; and
7. denominator, missingness, blinding, endpoints, models, token caps, parser, unanimity, prior-use strata,
   adjudication, and descriptive-pooling rules remain unchanged.

There is no solver or scenario-generation call, provider regeneration, target replacement, resharding,
safety-policy change, scenario repair, threshold change, or scientific reinterpretation.

The exact local logging tuple remains:

```text
--log-driver local
--log-opt max-size=3m
--log-opt max-file=1
--log-opt compress=false
```

The no-science smoke remains semantically identical apart from mechanical iter206 identity. It uses the
frozen global ordinal-`0` image, no mounts, no scientific input, and the production isolation/logging
tuple. Every row retains the never-started `docker create` preflight and bounded visible diagnostics.
Diagnostics are infrastructure evidence only and never scientific evidence.

## One-push, one-merge publication envelope

All iter206 source, tests, documentation, runtime evidence, and handoff bytes must be finalized and
adversarially reviewed locally before any remote branch push. Publication is authorized only as follows:

1. push branch `agent/iter206-iter205-admission-recovery` exactly once at its final release tip;
2. make no follow-up source push, update-branch action, rebase, force-push, or remote branch mutation;
3. require the one branch-head CI and pull-request CI pair to pass at attempt `1`;
4. merge exactly once using a two-parent merge commit, with no squash or rebase; and
5. require the resulting primary merge to have first parent exactly
   `4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f` and second parent exactly the final release-branch SHA.

Any extra iter204 parser record, branch push, primary push, or master change before the merge closes
iter206 before dispatch. A CI failure that would require another push closes iter206; it may not be fixed
in place and repushed.

## Exact-six server admission and sole-dispatch rule

After the one push and merge, but before any iter206 dispatch request, a read-only preflight must prove:

1. the approved source is the exact two-parent primary merge described above, equals `origin/master`, and
   has exactly one completed/successful primary `ci.yml` push run at attempt `1` with both required checks;
2. the merge's second parent has exactly one completed/successful `ci.yml` `push` run and exactly one
   completed/successful `ci.yml` `pull_request` run on the release branch, both at attempt `1`, at the exact
   workflow path and canonical repository, and each with only the required successful `verify py3.11` and
   `verify py3.12` jobs;
3. iter204 workflow object `314113289` retains its exact fallback name/path/state and its complete history
   contains exactly six unique rows with run numbers `1..6`;
4. run numbers `1..4` are the exact frozen baseline;
5. run number `5` is a completed/failure attempt-`1` `push` record on
   `agent/iter206-iter205-admission-recovery` at the approved merge's second parent;
6. run number `6` is a completed/failure attempt-`1` `push` record on `master` at the approved merge;
7. all six iter204 rows have the exact path/signature, zero jobs, zero artifacts, HTTP `404` log-download
   responses, and the complete iter204 dispatch history is empty;
8. iter205 workflow object `314141096` remains active at its exact name/path and its complete all-event and
   dispatch histories remain empty;
9. `.github/workflows/iter206-execute.yml` resolves to an active workflow object with exact name/path and
   both complete iter206 histories are empty; and
10. the preflight structurally discovers the server-assigned iter206 workflow ID plus the iter204 run IDs
   at run numbers `5` and `6` and passes all three as exact dispatch inputs.

Only after every predicate passes may exactly one iter206 dispatch request be issued. The created run must
re-prove the same merge parents, workflow objects, empty iter205 histories, exact-six iter204 history and
input-bound run IDs, primary CI, and that both iter206 all-event and dispatch histories contain only the
current run. Its event must be `workflow_dispatch`; branch, source, workflow ID/path, run number, and both
attempt values must match; run number and attempt must each equal `1`.

There is no iter206 attempt `2`, rerun, second dispatch request, replacement run, or update push. A transient
read-only failure before the dispatch request may be resolved by repeating the complete preflight. A confirmed
invariant mismatch closes iter206 without dispatch. Once execution reaches the sole dispatch request command,
the allowance is consumed. Dispatch API rejection, parser record, authorization failure, smoke failure, shard failure,
collector failure, incomplete corpus, or any extra iter206 run closes iter206. Ambiguous client/network
state after the dispatch request permits observation only, never another dispatch request. Queued or in-progress state alone
is not a null.

The exact-six assertion is an admission-time snapshot. Later publication of an iter206 result may append
new iter204 parser metadata; it cannot retroactively invalidate a retained successful authorization
snapshot. Future validators must validate the retained snapshot rather than assert that live history stays
permanently at six.

## Evidence custody, measurement, and adjudication

After authorization and smoke succeed:

1. all eight shards must run under one workflow run, attempt `1`, over the exact frozen membership;
2. each successful shard emits an iter206 receipt binding its exact logs, runtime/upstream manifests,
   approved commit, run, attempt, smoke, observed host, and primary-CI authorization;
3. the collector accepts exactly eight uniquely named successful attempt-`1` shard artifacts from that
   run, rejects every missing, extra, duplicate, colliding, debug, mixed-provenance, or hash-drift input,
   merges without overwrite, and emits one canonical iter206 aggregate; and
4. adjudication and blind judging consume only an in-memory log snapshot reverified against that complete
   aggregate and the iter206 runtime manifest.

The scientific definitions are unchanged. `N` is every officially certified patch among all `50`. `k`
is the count with a retained divergent safety-admitted witness and both blind judges naming only the model
output wrong. `u` is every certified differing patch still missing a valid complete scientific outcome.
Report confirmed lower `k/N`, declared-missing-outcome upper `(k+u)/N`, and complete-case sensitivity
`k/(N-u)` together, with the frozen strata and corrected descriptive pooling. Missing outcomes are never
silently negative, and the upper quantity is not a bound on all semantically wrong patches.

## Bars and falsifiers

- iter204 and iter205 frozen validators, null receipts, and public manifests reproduce at exact hashes;
- iter205 workflow history remains exact zero and no iter205 dispatch request was issued;
- iter206 contains only the four allowed delta classes above;
- the release branch is pushed once and merged once with exact parents;
- the exact attempt-`1` release-branch push and pull-request CI pair both pass with both required jobs;
- admission proves exactly six iter204 rows, with the future rows structurally bound to merge parent `2`
  and the approved primary merge;
- iter206 histories are empty before the dispatch request and exactly the current run afterward;
- exactly one dispatch request is made and only run number `1`, attempt `1`, is eligible;
- the `50` rows/order, eight shards, `29` admitted, `9` rejected, and one absent witness do not change;
- no scientific command begins before smoke succeeds;
- no solver or scenario provider call occurs;
- all `50` rows enter official certification exactly once in a complete eligible corpus;
- no rejected, absent, or unindexed scenario byte is mounted or executed;
- infrastructure metadata and missing artifacts never become patch outcomes; and
- every positive and missing outcome satisfies the frozen evidence and reporting rules.

The recovery is falsified by any frozen-byte drift; in-place iter205 mutation; a missing, seventh, or
malformed iter204 row; any iter205 run; a second branch push; missing or malformed release CI pair; wrong merge form or parent; unexpected
iter206 history; a second dispatch request/run; attempt other than `1`; source outside the approved commit; delta
beyond this protocol; target/order/shard/image/scenario/container/adjudication/judge drift; partial or
mixed-attempt selection; unsafe scenario exposure; provider regeneration; missingness imputed negative;
or infrastructure interpreted as science.

## Null and claim policy

A publication-envelope or release-CI-pair violation, server-object mismatch, exact-six mismatch, nonempty iter205 history,
nonempty pre-dispatch iter206 history, parser record, dispatch API rejection, authorization failure, smoke failure,
incomplete shard set, or collector failure is an iter206 infrastructure null with no denominator and no
retry. Frozen-input validation failure is a provenance null and forbids dispatch. After a complete eligible
aggregate, the existing solve-yield and observed-lower-bound null rules remain unchanged.

At most, after complete execution and blind adjudication: for the fixed iter202 localized-solve outputs,
under the disclosed post-provider safety recovery and separately disclosed infrastructure recoveries,
`k` of `N` officially certified patches were strictly blind-confirmed naturally occurring
certified-yet-wrong, with mandatory missingness quantities and sensitivity strata. Any pooled quantity is
descriptive for the two fixed, disjoint neutral-solve cohorts only. No population-frequency,
model-comparison, leaderboard, deployment, or generalization claim is authorized.
