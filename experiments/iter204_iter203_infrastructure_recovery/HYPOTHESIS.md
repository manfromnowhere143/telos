# Iteration 204 - Observable Infrastructure Recovery for Fixed Iter202/Iter203 Evidence

Status: **ACTIVE POST-INFRASTRUCTURE-NULL / PRE-SCIENTIFIC-OUTPUT RECOVERY PROTOCOL**. Frozen after the
iter203 infrastructure failure was observed and diagnosed, but before any official certification command,
generated-scenario command, adjudication, or blind-judge call for this cohort has run. This is not a
conventional preregistration before all contact with the system: it is a narrow recovery designed with full
knowledge of the iter203 infrastructure null and with no patch-level scientific outcome available.

Date: 2026-07-16.

## Why a new iteration is required

The sole canonical iter203 dispatch was run `29460393525`, attempt `1`, at commit
`5c409f79c9333206cff9ed80d59c08aa347110f6`. Authorization passed, all eight shards assigned the complete
fixed set of `50` rows, and every image was pulled and digest-verified. Every first scientific Docker run
invocation returned exit `125` before container start or in-container command. No receipt-eligible log,
shard receipt, uploaded workflow artifact, official certification execution, or scenario execution exists;
collection was skipped.

The deterministic source/configuration diagnosis is the `local` log-driver configuration: compression
defaults on, while the runner fixed `max-file=1` without `compress=false`. Docker Engine `28.0.4` rejects
that combination. The source binding is Moby `v28.0.4`, peeled commit
`6430e49a55babd9b8f4d08e70ecb2b68900770fe`, path `daemon/logger/local/config.go`. The exact daemon stderr
was redirected into hidden temporary files and deleted by the attempt-`1` failure path; this diagnosis is
therefore bound to the committed argument vector and engine semantics, not represented as retained raw-run
stderr.

The retained public job logs identify Ubuntu runner image `20260714.240.1`; its primary release is
[`ubuntu24/20260714.240`](https://github.com/actions/runner-images/releases/tag/ubuntu24/20260714.240).
The bound logger semantics are in
[`daemon/logger/local/config.go`](https://github.com/moby/moby/blob/6430e49a55babd9b8f4d08e70ecb2b68900770fe/daemon/logger/local/config.go#L30-L33).

A source correction cannot be inserted into the immutable iter203 run or runtime manifest. Iter203 remains
an infrastructure null, with no attempt `2` and no replacement dispatch. Iter204 is an additive,
post-infrastructure-null/pre-scientific-output recovery. It preserves every iter202 and iter203 evidence byte,
uses no provider rerun, and changes only the infrastructure versioning, Docker logging option, failure
observability, preflight, and corresponding receipt bindings required to execute the already-fixed plan.

## Frozen inputs

Before any execution, iter204 must prove:

1. the complete iter202 provider/checkpoint inventory and iter202 runtime manifest reconstruct exactly;
2. the complete iter203 bridge, `50` model patches, `50` gold patches, `50` official specs/eval scripts,
   `29` byte-identical safety-admitted scenario copies, `9` rejected scenarios, one original absent scenario,
   and iter203 runtime manifest reconstruct exactly;
3. the iter203 runtime-manifest file SHA-256 is
   `8beb0e845dbc9e3a4ce56832f28a62d4fd58ceac20adbc6bc06d6aef41be47e1`;
4. the iter203 null is bound to run `29460393525`, attempt `1`, and source commit
   `5c409f79c9333206cff9ed80d59c08aa347110f6`;
5. there is no retained iter203 execution artifact or row outcome to reuse, select, discard, or reinterpret;
6. a new iter204 runtime manifest binds the immutable upstream inventory plus every new execution,
   observability, collection, authorization, and workflow byte.

No iter202 or iter203 provider response, checkpoint, patch, spec, scenario, disposition, bridge record,
runtime manifest, or null record may be mutated, regenerated, relabeled, or replaced. The same exact 50-row
ordinal order and `i mod 8` shard assignment remain fixed.

## Scientific invariance and bounded runtime correction

The production container policy remains unchanged except for one explicit local-driver option. The frozen
logging tuple is:

```text
--log-driver local
--log-opt max-size=3m
--log-opt max-file=1
--log-opt compress=false
```

Network isolation, dropped capabilities, `no-new-privileges`, PID/memory/CPU limits, immutable image
references and IDs, read-only mounts, timeouts, output limits, patch application, certification scripts,
safe-scenario policy, and all adjudication rules remain those frozen in iter203. There is no allowlist
change, scenario repair, provider retry, target change, resharding, or scientific-threshold change.

## Exact no-science smoke gate

Before any patch, spec, or scenario file is mounted and before any scientific shard starts, one dedicated
workflow job must:

1. derive global ordinal `0` from the frozen 50-row source plan;
2. pull and verify its locked image reference
   `swebench/sweb.eval.x86_64.django_1776_django-11490@sha256:6f1ae986b5d24929658d43b3944508d66ff72d3e1998deb5ab549057d950bc7d`
   and image ID `sha256:7b16a5dae05b95aaedd9f0eecb2f9878017722ad7583ebb20a7cb8d099c5f435`
   from the upstream runtime manifest;
3. invoke that image with `--rm`, the exact production network/privilege/PID/memory/CPU/logging tuple, no
   bind mounts, no provider environment, and no patch-, spec-, or scenario-derived input;
4. run exactly `bash --noprofile --norc -c 'printf "%s\n" TELOS_ITER204_LOG_DRIVER_SMOKE_OK'`;
5. require exit `0`, stdout exactly `TELOS_ITER204_LOG_DRIVER_SMOKE_OK` followed by one newline, and empty
   stderr;
6. cap the retained smoke diagnostic at exactly `65,536` bytes and retain a canonical smoke receipt binding
   the image identity, Docker client and server versions, hosted runner-image identity, exact argument
   vector, output bytes/hash, exit code, source commit, runtime manifest, workflow run, and run attempt.

The smoke container performs no repository checkout inside the image, patch application, test, scenario,
or behavioral measurement. Its output is infrastructure evidence only. Any smoke mismatch fails closed and
prevents all eight scientific shards from starting.

After the global smoke passes and before a row's certification container is started, the row must also pass
an inert `docker create` launch preflight with that row's exact immutable image and row-scoped read-only
certification mounts, the exact production isolation/logging arguments, and command
`bash --noprofile --norc -c 'exit 0'`. The created container is never started and is removed immediately.
This validates the row-specific create contract without applying a patch, invoking a spec, mounting a
scenario, or producing a scientific outcome. A create failure is infrastructure evidence and fails the
complete attempt.

## Visible bounded failure diagnostics

Every row-scoped `docker create` preflight and every failed container `docker create`/`docker run` launch
invocation—the fault surface exposed by iter203—must record its phase, fixed row ID, image identity, exit
code, and bounded combined stdout/stderr before cleanup. A failed launch invocation must promote that
record into a stable diagnostic path that the failure-only upload includes; the runner must not delete the
last diagnostic copy. Successful scientific launches retain their ordinary bounded result logs and shard
receipts, bound through the runtime manifest; they do not require duplicate diagnostic artifacts.
Diagnostic artifacts bind the new runtime manifest, commit, workflow run/attempt, shard, Docker client and
server versions, hosted runner-image identity, and argument-vector digest. A scientific-launch diagnostic
is capped at exactly `2,162,688` bytes. Diagnostics beyond the declared cap are an infrastructure failure,
never a truncated scientific outcome. Diagnostic files are
explicitly ineligible for certification, scenario, denominator, adjudication, or result
collection. Provider credentials remain unset in every mechanical execution and smoke process, and no
secret value or private identifier may enter a diagnostic.

## Measurement and adjudication

After the smoke receipt passes, iter204 executes exactly the frozen iter203 scientific plan:

1. certify all `50` fixed model patches through the official harness, independent of gold equivalence and
   scenario disposition;
2. execute only the `29` byte-identical safety-admitted witnesses under model and gold; never mount or run
   the `9` rejected programs or the original absent program;
3. collect exactly eight successful, same-run/same-attempt shard receipts into one aggregate corpus bound to
   both upstream runtime generations and the new iter204 runtime manifest;
4. adjudicate only the verified aggregate; keep every rejected, absent, failed, nondivergent, ambiguous, or
   missing witness unresolved rather than negative;
5. blind-judge only certified patches with a valid retained divergent safe witness, using the exact frozen
   two-judge prompt, models, endpoint families, caps, parser, blinding, and unanimity rule.

The iter203 definitions remain unchanged: `N` is every officially certified patch among all `50`; `k` is
the count with a retained divergent safe witness and both blind judges naming only the model output wrong;
`u` is every certified differing patch still missing a valid complete outcome. Report `k/N`, `(k+u)/N`,
and `k/(N-u)` together, with the frozen prior-outcome and provider-ledger strata and corrected descriptive
pooling of iter200 with the iter204 execution over the frozen iter202 cohort. The upper quantity is not an
upper bound on every semantically wrong patch, and complete-case values are sensitivity analysis only.

## Workflow identity and no-retry rule

Implementation, tests, this hypothesis, the new runtime manifest, and the new workflow must be committed and
pass primary-branch CI before dispatch. The first iter204 workflow dispatch on that exact approved 40-hex
commit is the sole canonical dispatch. Authorization must prove the canonical repository/ref, exact commit,
green required CI checks, the immutable iter203 failed-run anchor, `GITHUB_RUN_ATTEMPT=1`, and absence of
any earlier iter204 workflow dispatch across all commits before the smoke job starts.

There is no iter203 attempt `2`, no second iter203 dispatch, no iter204 attempt `2`, and no second iter204
dispatch. Any iter204 failure is sealed as observed and requires another separately identified iteration;
it may not be retried after inspecting partial output. Every receipt and artifact must bind canonical
iter204 attempt `1`. A source or protocol correction likewise requires another separately identified
iteration, never mutation of retained evidence.

## Bars and falsifiers

- exact frozen coverage: `50` model patches, `50` official specs, `29` safe witnesses, `9` rejected
  witnesses, one original absent witness, and the unchanged eight-shard assignment;
- exactly one successful smoke receipt must precede every scientific shard;
- the eligible workflow is globally the first iter204 dispatch and exactly run attempt `1`;
- the production and smoke Docker logging tuple must include exactly `compress=false` in addition to the
  three frozen iter203 log settings;
- no patch/spec/scenario mount or scientific command may begin before the smoke gate succeeds;
- every row passes the inert, never-started `docker create` preflight before its certification start;
- every failed container `docker create`/`docker run` launch invocation retains bounded, upload-visible
  diagnostics, while no diagnostic is accepted as result evidence;
- no solver or scenario provider call occurs;
- no iter203 outcome, deleted diagnostic, or absent artifact is imputed or selected;
- no rejected or unindexed scenario byte is copied, mounted, or executed;
- all `50` rows enter certification exactly once in a complete eligible attempt;
- all existing iter203 denominator, missingness, resource, judging, and publication-safety bars remain in
  force; preserve the historical pre-execution publication-safety receipt byte-for-byte, validate only its
  frozen scope, and require a separately identified current post-null/iter204 publication-safety scan.

The recovery is falsified by any upstream byte drift; a second/rerun iter203 attempt; a widened runtime
change; a smoke that uses scientific mounts or inputs; a shard starting before the smoke passes; deleted or
unbounded failure diagnostics; mixed run attempts; partial shard selection; provider regeneration; unsafe
scenario exposure; missingness imputed negative; or any claim that treats infrastructure events as patch
outcomes.

## Null and claim policy

A smoke failure is a new infrastructure null and authorizes no scientific execution. Incomplete all-row
certification or incomplete same-attempt collection is an execution-infrastructure null and yields no
denominator. Subsequent solve-yield and observed-lower-bound nulls retain the exact iter203 definitions.

At most, after complete execution and blind adjudication: for the fixed iter202 localized-solve outputs,
under a disclosed post-provider safety recovery and a separately disclosed post-infrastructure recovery,
`k` of `N` officially certified patches were strictly blind-confirmed naturally occurring
certified-yet-wrong, with mandatory missingness quantities and sensitivity strata. The descriptive pooled
quantity covers only the two disjoint fixed neutral-solve cohorts. No population-frequency,
model-comparison, leaderboard, deployment, state-of-the-art, or generalization claim is authorized.
