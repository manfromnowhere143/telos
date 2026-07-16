# Iteration 207 - Claim-Integrity and Admission Recovery

Status: **ACTIVE PRE-RESULT SUCCESSOR GATE**. This is a retrospective deterministic correction over
already-inspected repository evidence, not a conventional preregistration and not a new scientific
measurement. The claim-integrity findings motivated this document. The audit made exactly two authenticated,
read-only GitHub metadata GETs to verify historical CI projection semantics. It made no iter207 provider call,
credential read or probe, container execution, scientific execution, remote mutation, publication, dispatch
request, or judge call.

Date: 2026-07-16.

Iter206 was locally sealed before the pre-publication claim audit flagged material historical claim defects,
including an apparent iter192 prior-baseline contradiction. Iter207's deeper patch-custody audit narrows
that item to the conservative novelty adjudication below. Iter206's frozen publication envelope does not
permit either correction to be folded into iter206. Iter207 is
therefore separately identified. This document first freezes the deterministic correction layer and then
freezes the unchanged scientific runtime plus the separately versioned admission recovery. No `RESULT.md`
may exist until both layers reach one valid terminal state.

## Custody and interpretation rule

All iter151-iter206 frozen hypotheses, raw outputs, receipts, logs, patches, retained prompts/responses,
provider checkpoints, and prior Git objects are immutable inputs. This gate does not rewrite them.
Historical `RESULT.md` files and selected `proof/learning_record.json` files are interpretation surfaces,
not raw evidence: iter207 may relabel only the exact paths enumerated and hash-bound in the correction
ledger, while their iter206-seal blobs remain preserved in Git. No other iter151-iter206 experiment path may
change. This gate adds a correction ledger, one conservative novelty-scope correction, and one strict
protocol-failure subreceipt.

Every corrected entry separates two questions:

1. **Did the executed gate satisfy its stated protocol?** A violated bar or falsifier is `FAIL`, even when
   later evidence is interesting.
2. **What narrower empirical statement do the retained bytes support?** A protocol failure does not erase
   genuine execution logs, but those logs must be described as exploratory and only at the scope they
   establish.

The canonical offline generator is `scripts/audit_iter207_claim_integrity.py`. It writes only:

- `proof/corrections/iter192_novelty_scope_correction.json`;
- `proof/strict/iter195_protocol_failure.json`; and
- `proof/claim_integrity_correction.json`.

`python3 scripts/audit_iter207_claim_integrity.py --check` must reproduce all three byte-for-byte without
network, provider, secret, container, or remote access.

## Frozen corrections

### Iter192 - conservative novelty `FAIL`; literal v1 trigger indeterminate

Iter192's deterministic `40/40` construct correction remains supported: the v1 rows are unresolved and
each has a `PASS_TO_PASS` failure. Frozen falsifier 5 required an earlier baseline *for v1*. Iter151 predates
v1 and retained no accepted patch bytes or hashes. Nineteen of its twenty instance IDs also occur in v1,
but exact row identity is neither proven nor refuted; the literal v1-specific trigger is indeterminate.

Iter151 had already reported the same class-level official-harness/test-suite mechanism: proxy resolution
`0/20`, explicitly definitional because every both-miss start fails `PASS_TO_PASS`. Iter192's lexical search
returned zero, but that string-level result cannot support conceptual firstness. The novelty interpretation
is therefore conservatively adjudicated `FAIL`, while the retained row-level findings remain `40/40`
unresolved and `40/40` with a regression failure. Separately,
historical tarballs contain `139` harness-resolved hack-tagged evaluations across `65` instance IDs. The
committed decision evidence binds only `23` iter152 discarded instance IDs, `17` of which overlap the
harness-resolved set; it does not bind all `139` evaluations to discard decisions or preserve their patch
bytes. Conceptual firstness is withdrawn; no row-identical prior v1 baseline is asserted.

### Iter195 - strict protocol `FAIL`; ten exploratory differentials retained

Iter195 has exactly three protocol failures:

1. The registered design said input synthesis would not see the gold patch or gold diff. The executed
   provider prompt contained labeled `GOLD` and `VARIANT` hunks.
2. The registered design required a twenty-input generator and at least ten clean gold executions per
   trusted generator. The runner instead generated one targeted script per candidate and treated one clean
   gold execution as a validated scenario.
3. The registered design required raw synthesis prompts and leakage scans for every accepted row. No
   dedicated raw prompt, raw response, or leakage-scan artifact is retained.

Chronology is explicit. The hypothesis was committed before Phase A. The deviating runner and Phase-A
outputs first entered Git together, followed by the execution output commit. The protocol was therefore
prospectively strict enough to fail; the later result may not replace its bars.

The defensible exploratory result is retained precisely: `16` certified candidates entered Phase A;
`16` provider calls produced `15` single scenarios; `30` paired logs retain their execution; `13/15` gold
runs were clean; and `10` official-harness-resolved variants produced clean output different from gold on
their single targeted scenario. Because the scenario provider saw both hunks, this is gold-assisted,
reference-differential evidence. It is not a passed synthesized-input oracle and does not establish global
semantic inequivalence.

### Iter199 - gold-assisted construction; registration timing unsubstantiated

Iter199 reused iter195's exact scenario generator and passed both the gold and variant hunks to the
scenario provider. Its retained `42 -> 23 -> 20 -> 12` funnel is therefore an exploratory gold-assisted
construction/witness result, not a gold-blind oracle.

The hypothesis, target file, adversary outputs, and scenario outputs first entered Git in the same commit.
Git therefore does not independently establish the statement that the targets and protocol were frozen
before provider output. The `12` retained official-harness-certified, clean reference differentials remain
usable under that narrower chronology and method description; no prospective or frequency claim follows.

### Iter196 - partial and blocked, not a completed two-detector gate

Iter196 registered two detectors but delivered only Detector A. Detector B moved to iter197. The corrected
iter196 audit records `blocked`, while its result accurately says `partial`; the registered both-detector
bar was not met. The historical third panel member was unavailable in that run, which is not a claim about
current runtime availability. The retained `44` parsed labels and their missing-outcome sensitivities are
exploratory. Raw provider response text is absent, so parser fidelity cannot be re-audited.

### Iter179 - score-producing spend guard excludes diagnostics

The unrepaired `17/40` primary panel score is produced by `240` calls: iter175's `120` primary calls with
an estimated spend guard of `$6.312690`, plus iter178's `120` fresh primary calls with a guard of
`$6.815400`. Their score-producing total is `$13.128090` (about `$13.13`). These are conservative guards
derived partly from character-based token estimates, not provider invoices.

Iter178 also made three diagnostic-only calls with a `$0.189750` guard, bringing its whole-run guard to
`$7.005150` and the iter175+iter178 run total to `$13.317840`. Iter181 later added five repair-diagnostic
calls with a `$0.271800` guard. The resulting `$13.589640`, which rounds to `$13.59`, includes both excluded
diagnostic stages and must not be attributed to the unrepaired score.

### Iter201 - four-row shared-line diagnostic is disclosure-only

The historical `leakage_shared_gold_lines` diagnostic deterministically identifies four candidate rows:
`django__django-11211`, `matplotlib__matplotlib-24627`, `astropy__astropy-12907`, and
`sympy__sympy-11618`. Each judge received the candidate's own diff; the gold patch was not supplied as a
comparison reference. This diagnostic must be disclosed but is not causal evidence and is not an
additional invalidation.

Iter201 remains `FAIL` for the separate, already-recorded protocol deviation: property generation used a
candidate-diff-derived source/function locator despite the registered diff-independent description.

### Iter200 - original run attribution is bounded

The corrected exploratory funnel remains `N=24`, `k=1`, `u=6`. The `54` original execution logs are
retained as an exact-byte corpus, but they contain no embedded reference to claimed run `29391238359` and
there is no committed original artifact-download receipt that independently rebinds those bytes to that
run. The run ID is therefore a historical attribution, not independently proven by the retained log corpus.

The later denominator backfill is different: run `29422735843`, its artifact identity, the `20` new logs,
and preservation of the original `54` are receipt-bound. The original attribution limit does not erase the
historical log bytes, but it must accompany any provenance claim. The result remains additionally bounded
by the already-disclosed absence of raw historical judge response text.

### Iter202 - interrupted usage remains unknown and conservatively charged

The interrupted pre-freeze solver invocation initiated at least one provider request, retained and used no
provider output, and has unknown exact completed-call count and spend. Its `53` calls and estimated `$2.65`
are conservative ceiling charges for bookkeeping, not recovered actual usage.

The later retained run is separate: `53` solver calls plus `39` scenario calls, estimated at `$4.60` in
the committed summaries. The conservative ledger therefore carries `145` charged calls and `$7.25` of
estimated-or-charged spend, while explicitly refusing to present either total as exact actual usage. Iter202
is a scenario-safety protocol/execution null and contributes no `N`, `k`, or `u`.

## Numeric bars

- frozen evidence inputs modified by this audit: exactly `0`; exact historical interpretation surfaces
  relabeled under the ledger allowlist: `12`, with their iter206-seal blobs hash-bound;
- authenticated read-only GitHub metadata GETs: exactly `2`, used only to verify historical CI projection
  semantics;
- provider calls, credential reads/probes, containers, scientific executions, remote mutations, dispatch
  requests, and judge calls: exactly `0`;
- conservative novelty-scope corrections: exactly `1`, for iter192;
- strict protocol-failure subreceipts: exactly `1`, for iter195;
- iter195 protocol failures: exactly `3`, with no bar merged into another;
- iter195 retained execution accounting: `16` candidates, `15` scenarios, `30` logs, `13` clean gold
  scenarios, and `10` clean gold-versus-variant differentials;
- iter199 registration chronology binds the hypothesis, targets, adversary outputs, and scenario outputs to
  their common first Git commit;
- iter196 remains partial/blocked and never becomes a completed two-detector gate;
- iter179 score-producing call guard: exactly `$13.128090` across `240` primary calls; the whole source-run
  guard is `$13.317840`, and the through-iter181 diagnostic path is `$13.589640`;
- iter201 shared-line diagnostic rows: exactly `4`, disclosure-only;
- iter200 original/backfill log partition: exactly `54 + 20 = 74`;
- iter202 interrupted exact calls/spend remain `null`, with minimum initiated requests `1` and ceiling charge
  `53` / `$2.65`; and
- all generated correction artifacts reproduce byte-for-byte under `--check`.

## Falsifiers

1. Any frozen hypothesis, raw output, receipt, log, patch, retained prompt/response, or provider-checkpoint
   byte is rewritten or deleted, any prior Git object is made unreachable, or any historical interpretation
   surface outside the ledger's exact allowlist changes.
2. Iter192 is described as either a strict literal-trigger failure or an unqualified pass, rather than a
   conservative novelty `FAIL` with an indeterminate literal v1-specific trigger.
3. Iter195 remains a strict protocol `PASS` in the standing claim boundary.
4. The iter192 `40/40` recount is erased merely because its novelty interpretation failed.
5. Iter195 is described as gold-blind, twenty-input validated, or as a passed synthesized-input oracle.
6. The ten iter195 differentials are generalized beyond official-harness resolution plus one clean targeted
   gold-versus-variant output difference per retained row.
7. Iter199 is described as independently Git-frozen before its retained provider outputs or as a gold-blind
   witness method.
8. Iter196 is described as completing both registered detectors.
9. The iter201 four-row diagnostic is hidden, treated as causal, or used as an additional protocol
   invalidation.
10. The rounded `$13.59` through-repair guard is attributed to the unrepaired iter179 primary score, or any
    estimated guard is described as a provider invoice.
11. Claimed iter200 run `29391238359` is presented as independently rebound by the original `54` logs.
12. Iter202's ceiling charge is presented as exact actual usage, or its null is assigned numeric `N`, `k`,
    or `u`.
13. A public correction silently removes retained negative, partial, null, missingness, chronology,
    provenance, or mutable-image limitations.
14. A `RESULT.md` is created before both the correction and separate runtime admission recovery finish.

## Claim boundary

At most, this deterministic audit corrects the historical validity and provenance classifications above
from committed evidence. It supports a narrower exploratory benchmark statement: `22` official-harness-
resolved elicited variants have retained clean, gold-assisted, targeted reference-differential witnesses,
ten from protocol-failed iter195 and twelve from chronology-limited iter199. It does not establish a passed
gold-blind synthesized-input oracle, global semantic wrongness, prospective benchmark prevalence, natural
frequency, model superiority, a leaderboard, deployment performance, or state of the art.

This correction section is not an iter207 result and, by itself, authorizes no runtime or remote action.

## Combined successor and immutable recovery anchors

The runtime part of iter207 is an additive continuation of the locally sealed, never-published iter206
recovery. Before any iter207 remote publication or scientific output, it binds:

- primary base `4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f`;
- iter206 source commit `e7c2ec28daa746dbcfb5812d3771ab981ff984c0` and local seal commit
  `a2a05ef2ed05a0c457076f2bd5f1475507190685`;
- iter206 hypothesis SHA-256
  `3e1185f5a79bf0cbd85ee046065ff9caf17fe7c1ccaa2c519be053510b1c4f26`;
- iter206 runtime-manifest SHA-256
  `749bad5d40f7117ddcfffce314c1d9fd390ec8663ec2226d8cbd158dc41a942b`;
- iter206 pre-publication claim-integrity-null SHA-256
  `8db0bda547f3a9a5ffd0333e7a75f00d7b95551cc4cfa2f374345794f746e93b`;
- iter205 workflow object `314141096`, its exact name/path/state, and its empty complete all-event and
  dispatch histories; and
- every iter203--iter205 scientific/runtime anchor already transitively bound by the iter206 manifest.

Iter206 stopped before any remote branch push, pull request, merge, workflow run, dispatch request,
provider call, container invocation, patch application, certification, scenario, adjudication, or judge.
It contributes no `N`, `k`, or `u`. Its original hypothesis, workflow, manifest, safety receipt, and pending
learning record remain immutable historical bytes; its additive terminal null is the standing disposition.

## Exact allowed delta

Iter207 may make only these additive changes:

1. publish the deterministic claim-integrity ledger and the public relabels required by its frozen bars;
2. add the exact iter206 pre-publication null, terminal learning record, and offline guards without mutating
   any sealed iter206 byte;
3. mechanically version the never-executed iter206 runtime wrappers, schemas, artifacts, sentinel, and
   workflow as iter207 while preserving all scientific and container semantics;
4. replace only iter206 publication identities with the iter207 one-push/one-merge identities below; and
5. bind the newly published iter206 workflow object and its empty complete histories in addition to the
   already-bound iter205 workflow and empty histories.

No target, patch, gold patch, spec, eval script, scenario byte, safety disposition, image, row order, shard,
container command, limit, timeout, certification rule, missingness rule, judge prompt/model/parser,
adjudication rule, or reporting endpoint may change. Any other delta requires a separately versioned gate
before publication or dispatch.

## Frozen exact-four baseline and exact-six admission

The admission-time iter204 baseline remains ordered by `run_number`:

| run number | run ID | branch | source SHA |
|---:|---:|---|---|
| `1` | `29465584664` | `agent/iter204-infrastructure-recovery` | `8342315dd2fa7ec865bd7c654ec4ec098675dfab` |
| `2` | `29465924803` | `master` | `c1137f896b7ee3c9a26ee35bcda2c5f5c6b79446` |
| `3` | `29468669956` | `agent/iter205-workflow-context-recovery` | `a336b4909329d392f6db5f6098792e07a17f28cb` |
| `4` | `29468768706` | `master` | `4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f` |

All four rows have workflow ID `314113289`, fallback name/path
`.github/workflows/iter204-execute.yml`, event `push`, attempt `1`, completed/failure state, zero jobs, zero
artifacts, and HTTP `404` log-download responses. Its dispatch history is empty.

After the one iter207 branch push and merge, the pre-dispatch snapshot must contain exactly six iter204
rows with run numbers `1..6`: rows `1..4` exactly as above, row `5` at the exact final iter207 branch tip,
and row `6` at the approved primary merge. Every row retains the same parse-failure signature. A missing,
seventh, malformed, duplicated, or differently ordered row closes iter207 before dispatch. This is an
authorization-time snapshot, not a claim that later server history remains permanently at six.

## Frozen scientific and execution plan

The fixed iter203--iter206 plan is unchanged:

1. all `50` model patches, paired gold patches, official specs, eval scripts, byte hashes, and global row
   order remain fixed;
2. eight zero-based shards assign ordinal `i` only to shard `i mod 8`, with at most seven rows per shard;
3. every model patch enters official certification independently of gold equivalence or scenario
   availability;
4. exactly `29` safety-admitted witnesses, `9` rejected witnesses with `21` findings, and one original
   absent witness retain their exact bytes and dispositions;
5. only a row's indexed admitted witness may be mounted and executed under model and gold; rejected or
   absent witnesses may not be copied, mounted, run, repaired, replaced, or reinterpreted;
6. immutable image references/IDs, no-network and least-privilege container policy, resource/output bounds,
   timeouts, patch application, certification, comparison, diagnostics, and local logging remain unchanged;
7. the no-science smoke uses the frozen ordinal-`0` image, no mounts, no scientific input, and the exact
   production isolation/logging tuple before any shard; and
8. denominator, missingness, blinding, endpoints, models, token caps, parser, unanimity, prior-use strata,
   adjudication, and descriptive-pooling rules remain unchanged.

The exact local logging tuple remains `local`, `max-size=3m`, `max-file=1`, `compress=false`. Every row
retains a never-started `docker create` preflight and bounded visible diagnostics. Diagnostics are
infrastructure evidence only. No solver, scenario generator, provider regeneration, target replacement,
resharding, safety repair, or threshold change is authorized.

## One-push, one-merge publication envelope

All source, correction evidence, documentation, paper, runtime evidence, tests, handoff bytes, and
adversarial reviews must be final locally before publication. Then, and only then:

1. push `agent/iter207-claim-integrity-admission-recovery` exactly once at its final release tip;
2. require exactly one completed/successful attempt-`1` `ci.yml` push run and one completed/successful
   attempt-`1` pull-request run at that tip, each with only `verify py3.11` and `verify py3.12` successful;
3. merge exactly once with two parents, without squash or rebase, with first parent exactly
   `4f7dd39bb171fd89c1bb7da3f265aa00aa6df63f` and second parent exactly the final branch tip;
4. require exactly one completed/successful attempt-`1` primary `ci.yml` push run at the merge with both
   required jobs; and
5. make no follow-up source push, update-branch action, rebase, force-push, or other remote mutation.

Any extra iter204 parser row, branch push, primary push, primary change, CI failure requiring a source
change, or wrong merge form closes iter207 before dispatch. A read-only transient before the dispatch
request may be rechecked from the beginning; it does not authorize mutation.

## Dual-workflow emptiness and sole-dispatch rule

After publication and before any dispatch request, a read-only preflight must prove:

1. the exact source, merge parents, final-tip push/PR CI pair, and primary CI described above;
2. iter204 workflow `314113289` and the exact-six snapshot described above, with empty dispatch history;
3. iter205 workflow `314141096` remains active at its exact name/path with empty complete all-event and
   dispatch histories;
4. `.github/workflows/iter206-execute.yml` resolves structurally to an active workflow object at its exact
   name/path with empty complete all-event and dispatch histories;
5. `.github/workflows/iter207-execute.yml` resolves structurally to a distinct active workflow object at
   its exact name/path with empty complete all-event and dispatch histories; and
6. the discovered iter204 row-`5` and row-`6` run IDs plus the distinct iter206 and iter207 workflow IDs are
   passed as exact dispatch inputs.

Only after every predicate passes may exactly one iter207 dispatch request be issued. The created run must
re-prove all identities, histories, merge/CI bindings, and input-bound IDs; iter207 all-event and dispatch
histories must then contain only that current run. Its event is `workflow_dispatch`; run number and both
attempt values are exactly `1`. Iter205 and iter206 histories must remain empty.

There is no iter207 attempt `2`, rerun, second dispatch request, replacement run, or update push. Once the
sole request command is reached, the allowance is consumed. Rejection, ambiguous client/network state,
parser record, authorization failure, smoke failure, shard failure, collector failure, incomplete corpus,
or any extra iter207 run closes the gate. Ambiguity permits observation only, never another request.

## Chain of custody, endpoints, and terminal policy

All eight shards must belong to one workflow run and attempt. Each successful shard receipt binds its exact
logs, runtime/upstream manifests, approved source, run, attempt, smoke, observed host, and authorization.
The collector accepts exactly eight uniquely named successful attempt-`1` artifacts, rejects missing,
extra, duplicate, colliding, debug, mixed-provenance, or hash-drift inputs, merges without overwrite, and
emits one canonical aggregate. Adjudication and blind judging consume only an in-memory log snapshot
reverified against that aggregate and the iter207 runtime manifest.

`N` is every officially certified patch among all `50`. `k` counts rows with a retained divergent admitted
witness and both blind judges naming only the model output wrong. `u` counts certified differing patches
still missing a valid complete scientific outcome. Report confirmed lower `k/N`, declared-missing-outcome
upper `(k+u)/N`, and complete-case sensitivity `k/(N-u)` together, with the frozen strata. The upper quantity
is only over declared missing pipeline outcomes and is not a bound on all semantically wrong patches.

A publication, admission, authorization, smoke, shard, collector, or incomplete-corpus failure is an
infrastructure null with no denominator and no retry. Frozen-input or correction-ledger validation failure
is a provenance null and forbids dispatch. Only a complete eligible aggregate may support the bounded,
descriptive fixed-cohort quantities above. No population frequency, model comparison, leaderboard,
deployment, or generalization claim is authorized.
