# Iter240 — ground-truth admission design and missingness freeze

Status: **prospective design gate with a disclosed retrospective
reconstruction**. This document is introduced in the atomic activation commit
after the registry-only authorization commit. It precedes the iter240
builders, retained manifests, power curves, role-view schemas, validators,
known-bad fixtures, result, and every future ground-truth acquisition action.

Predecessor: merged iter239 master
`b597b763f2eb52b2f4f2d36e7daaa31654be076b`, the two-parent merge of
`fb87af7eb15b5235a722a7bb3fd3a48962019188` and sealed iter239 tip
`56fb78f5f8afcd8709fde1170e8422072626f367`.

Prospective authorization: registry-only direct child
`cf809ac0e06f37127553e99a2ab9b0705f8e2fae`, seal ID
`iter240-ground-truth-admission-design-authorization`, authorizes additions
only below `experiments/iter240_ground_truth_admission_design` until an
exact-tree successor seal. It authorizes no scientific or external execution.

Budget: `$0.00`. Provider calls: `0`. Model-judgment calls: `0`. Human
contacts: `0`. Scientific containers: `0`. GPU allocations: `0`. New solves,
target executions, witness generations, and adjudications: `0`.

## Why this gate exists

Iter237 corrected the fresh-cohort comparison to `k=0,N=37,u=13`. The thirteen
unadjudicated certified patches were previously treated as if they were
negative in one takeover analysis. Under least-favourable accounting they can
reverse the direction of the comparison with the reused reference-solver run.
No new-cohort purchase is interpretable while that missingness and the future
ground-truth sampling unit remain unresolved.

The retained labels are operational gold differentials. They are not
independent semantic ground truth. Reusing a model, a prior model judge, the
accepted patch alone, or agreement among models would reproduce the same
authority dependency rather than remove it.

This gate does two narrower things:

1. reconstructs, binds, and preserves what the current bytes can and cannot
   establish for all thirteen missing fresh-cohort rows; and
2. freezes the sampling frame, blinding contract, admission bars, and
   decision curves that a separately authorized GROUND-TRUTH-1 execution
   would need.

It does not execute GROUND-TRUTH-1, recover an outcome, validate a detector,
estimate a population rate, establish transfer, or authorize more data.

## Retrospective disclosure

The takeover audit inspected the relevant committed artifacts before this
hypothesis was written. The following are therefore disclosed observations to
be independently rebuilt, not prospective discoveries:

- the strict selector appeared to return thirteen distinct task identities:
  six from iter224 and seven from iter228;
- eight appeared to lack an admissible committed scenario: seven carried
  `excluded_unsafe` and one carried `no_scenario`;
- five appeared to have a scenario but no paired valid observable: three
  errored on both arms, and two emitted a result on the accepted arm while the
  candidate arm raised;
- no selected row appeared to carry a retained blind-judge verdict;
- the five historical scenario outcomes have already been exposed to the
  current investigation;
- the proposed combined future frame appeared to contain fifty-five candidate
  rows clustered in thirty-seven unique task identities: seventeen
  operational-positive patches on twelve task identities, twenty-five
  non-identical hard-control patches on fourteen task identities, and the
  thirteen missing patches on thirteen task identities, with two task
  identities shared by the positive and hard-control strata.

Iter240 may reproduce, contradict, or invalidate these observations. It may
not present successful reproduction as a pre-data finding. The critical
prospective contribution is the frozen selection, provenance, leakage,
blinding, power, and admission contract.

## Registered questions

### Q1 — retained-evidence recoverability

Do the committed iter224 and iter228 bytes contain a complete, admissible,
paired outcome and retained blind verdict for any row selected without reading
outcomes?

The expected answer from the disclosed audit is no. A contradictory rebuild
must be reported rather than reconciled by changing the selector or validity
rule.

### Q2 — task-clustered ground-truth frame

Can the current operational-positive, hard-control, and fresh-missing
candidate patches be assembled into one provenance-bound frame while
preserving stratum identity, repeated-task dependence, and missingness?

This is a frame-construction question, not an assertion that any row is
semantically right or wrong.

### Q3 — acquisition identifiability

What conclusions and sample sizes are possible under every missing-outcome
assignment and under explicit validity, completion, and discordance
assumptions?

Iter240 emits the full registered grid. It may not select one favourable
branch after seeing it.

## G0 — exact predecessor and source boundary

The builder must fail unless:

- `HEAD` descends from the exact authorization commit;
- the iter239 merged predecessor, sealed tip, and completed-evidence tree have
  the registered identities;
- every source path is a regular tracked Git blob;
- every source JSON object rejects duplicate keys and non-finite numbers;
- source hashes and exact JSON pointers are retained before derived values;
- all iter224, iter228, iter230, iter235, and iter237 source bytes remain
  unchanged; and
- no source is selected from a mutable network response, worktree-only file,
  model response, or prose summary.

The result may retain an additive remote-acceptance receipt for iter239. That
receipt is engineering evidence only and must state that GitHub state is
time-bounded and mutable.

## G1 — strict thirteen-row selection

Read only:

- `experiments/iter224_natural_rate_scale_n/proof/iter200_per_candidate.json`;
  and
- `experiments/iter228_fresh_diverse_cohort/proof/iter200_per_candidate.json`.

A row qualifies only when every typed predicate is true:

```text
certified_resolved is true
AND gold_equivalent_after_terminal_lf_normalization is false
AND outcome_complete is false
```

Python truthiness and numeric stand-ins for booleans are forbidden. Selection
must not read `status`, `diverges`, `gold_result`, `model_result`, scenario
output, execution logs, label files, or judge verdicts. `status` may be checked
only after selection as a consistency assertion.

The manifest must preserve source run, instance ID, repository, base commit,
model patch, accepted patch, specification, certification command and log,
evaluation script, both retained arm logs, scenario state, immutable image
repository digest and arm image IDs where present, plus SHA-256 for every
materialized input. A missing required artifact is missingness, never an empty
value or zero.

Acceptance requires exactly the source-derived census. No discretionary
subsample, repository cap, ranking, deduplication across different candidate
patches, or post-outcome exclusion is allowed.

## G2 — outcome-availability taxonomy

Only after the selected manifest is frozen may a separate diagnostic pass read
scenario and judge evidence. Each row receives exactly one availability state:

- `excluded_unsafe`;
- `no_scenario`;
- `paired_invalid_both_arms`;
- `paired_invalid_candidate_only`;
- `paired_valid_unjudged`;
- `paired_valid_judged`; or
- `source_inconsistent`.

`paired_valid` requires both registered immutable-image arms to apply, exit
zero, emit exactly one bounded parseable `RESULT`, and emit no error, timeout,
exception, or truncation sentinel. A candidate exception opposite a gold
result is not a recovered differential under this protocol. Neither is a
shared exception. Unsafe exclusions may not be run or relaxed.

Historical scenarios and their outcomes are diagnostic-only because this
investigation has already seen them. They are forbidden as a future primary
endpoint. No row leaves `u` without a later, separately preregistered,
outcome-masked measurement and whatever independent adjudication that later
claim requires.

The retained-evidence status is:

- `supported` only if at least one selected row already has paired-valid,
  blinded, protocol-admissible evidence under rules frozen before its outcome
  was exposed;
- otherwise `blocked`.

Nothing in this taxonomy may convert missingness, an exception, or absence
into a negative.

## G3 — task-clustered GROUND-TRUTH-1 frame

Build three strata mechanically:

1. every current patch-level operational positive from the six registered
   natural-rate runs, including retained valid iter235 recoveries;
2. every non-gold-identical, one-witness no-divergence hard control in the
   frozen iter230 evaluation set; and
3. every G1 fresh-missing row.

The builder must retain candidate-row identity and task identity separately.
The task is the inferential cluster. Multiple solvers or patches on one task
never become independent task samples. Strata remain separate even when a task
appears in more than one stratum.

For every frame row retain:

- source run and source-evidence pointers;
- task ID and repository;
- candidate-patch digest;
- operational stratum and label provenance;
- missingness and overlap flags; and
- whether any future role is permitted to see each field.

The frame is an acquisition inventory. “Positive” and “control” retain their
operational meanings; neither word implies independent semantic truth.

## G4 — prospective role views and leakage controls

Iter240 defines schemas and forbidden-field tests only. It creates no human
packet and contacts no person.

### Consequence author

May receive the issue, base commit, pre-fix repository state, and prospectively
registered public context. Must not receive any candidate patch, accepted
patch, Telos label, witness, prior scenario, execution outcome, solver or
provider identity, judge output, or stratum.

The consequence is frozen before candidate exposure. It must pass on the
accepted implementation and on a separately produced valid implementation
whose producer is independent of the candidate and consequence author. The
accepted patch alone is not a sufficient validity control.

### Independent semantic adjudicators

Two conflict-screened domain experts independently review a blinded packet
under a frozen rubric. A third conflict-screened adjudicator handles
disagreement. Conflicts, abstentions, invalid consequences, missing reviews,
and raw rationale remain visible.

No adjudicator may have produced the candidate, accepted patch, consequence,
or validity control. No model sample, model consensus, signature, repository
owner, or current agent substitutes for these roles.

### Outcome-masking broker

If a later recovery instrument is authorized, the broker freezes all attempts
and deterministic attempt order before releasing runtime values. At most three
attempts per row may be proposed under one frozen generator contract. The
first paired-valid attempt is selected regardless of equal or different
result. Invalid attempts never relax safety, and exhaustion remains `u`.

This future protocol is a design output only. Iter240 authorizes neither
generation nor execution.

## G5 — sensitivity and acquisition design

All calculations are deterministic and provider-free. The builder emits every
registered branch:

### Missingness branches

Enumerate integer `x` from zero through thirteen, where `x` is the number of
fresh operational positives after complete recovery. For each branch report:

- `x/37`;
- comparison with the reused reference-solver endpoint `5/29`;
- whether the registered strict least-favourable concentration inequality
  holds; and
- an explicitly exploratory one-sided Fisher exact value.

Fisher values illustrate sensitivity only. Cohorts are nonrandom operational
samples, labels are not independent semantic ground truth, and the result is
not a primary concentration test. No branch may be selected as “the” result.

### Zero-event upper bounds

For task-level `n`, the exact one-sided ninety-five-percent upper bound after
zero events is:

```text
1 - 0.05 ** (1 / n)
```

Emit the full registered grid for `n=1..500` and the first `n` whose bound is
at most each threshold in `{0.10, 0.05, 0.02, 0.01}`. Floating-point outputs
use a documented tolerance or canonical decimal representation; bit-exact
equality of libm-derived values is forbidden.

### Acquisition sensitivity

Report solves required to reach each task-level target over a frozen
certification-yield grid, retaining the historical fresh-cohort yield only as
one planning input. Solved rows never replace certified rows in a scientific
denominator. No sample-size calculation authorizes a purchase.

### Assurance-delta readiness

Detailed paired detector power is `blocked` until GROUND-TRUTH-1 measures:

- supported-label yield;
- consequence validity;
- adjudication completion;
- within-task discordance; and
- control false-rejection behavior.

The design may emit a nuisance-parameter grid, but it may not optimize the
grid post hoc or call an unsupported input an estimate.

## G6 — admission bars for a future GROUND-TRUTH-1

GROUND-TRUTH-1 remains blocked until a separate authorization binds actual
people, funding, data handling, and execution. Its minimum admission bars are:

- consequence validity at least ninety-five percent;
- adjudication completion at least ninety percent;
- zero critical candidate, label, witness, outcome, or role leakage;
- at least ten unique task identities with independently supported positive
  labels before any detector-efficacy gate;
- task-clustered analysis with all repeated patches retained as dependent;
- raw conflicts, abstentions, invalid artifacts, and missingness retained;
- no self-approval or shared producer/verifier authority; and
- no external action before an explicit budget and identity authorization.

These are protocol thresholds, not observed results.

## Engineering artifacts and closure

The implementation must add:

- one deterministic builder for the source manifest, availability taxonomy,
  task-clustered frame, and decision curves;
- one credential-free validator that independently reconstructs the evidence;
- strict role-view JSON schemas or machine-readable field policies;
- one materialization receipt binding every source and output;
- known-good and known-bad fixtures;
- a result with separate status fields; and
- a direct-child exact-tree successor seal after completed evidence.

Known-bad fixtures must fail for:

- twelve or fourteen selected missing rows;
- a duplicate task or silent row removal;
- integer `1` accepted as boolean `true`;
- selection that reads status, divergence, results, scenario output, logs, or
  judge evidence;
- missing source, patch, specification, log, image, pointer, or digest;
- changed source bytes or an unregistered source path;
- an old exposed scenario admitted as a recovered endpoint;
- a candidate-only exception admitted as a valid differential;
- a single-arm result, timeout, error sentinel, nonzero exit, duplicate result,
  or truncated output admitted as paired-valid;
- unsafe execution, a relaxed allowlist, mutable `:latest`, or a stale image;
- repeated patches counted as independent tasks;
- pooled strata or the solved denominator substituted for certified patches;
- a selected favourable missingness or power branch;
- direct bit-exact comparison of a libm-derived value;
- candidate, accepted patch, label, witness, prior judge, solver identity, or
  outcome leaking into the author view;
- model or owner authority represented as independent human ground truth;
- design completion represented as acquisition or spending authority; and
- any mutation of a sealed predecessor byte.

Local closure, all CI-derived commands, required Linux Python 3.11 and 3.12
pull-request checks, exact-tree sealing, a two-parent merge, merged-master CI,
and a read-only post-merge observation remain required engineering evidence.

## Result vocabulary

The result reports four independent fields:

- `design_preflight`: `supported`, `inconclusive`, or `failed`;
- `retained_evidence_recovery`: `supported` or `blocked`;
- `independent_ground_truth`: `blocked` unless separately executed and earned;
  and
- `cohort_acquisition`: `not_authorized`.

A green design preflight changes none of `k`, `N`, or `u`. It does not make
T2 supported.

## Named falsifiers

- Any selected missing row is assigned a semantic outcome from absence,
  exception, accepted-patch behavior, prior model prose, or consensus.
- A source selector or validity rule changes after diagnostic outcomes are
  read without a separately versioned prospective amendment.
- An exposed historical scenario becomes the future primary endpoint.
- A safety exclusion is executed or relaxed.
- Candidate rows are treated as independent when task identities repeat.
- Operational labels are described as independent semantic truth.
- A model, current agent, repository owner, or artifact producer approves its
  own consequential scientific claim.
- One favourable power or missingness branch replaces the complete grid.
- A design or CI pass authorizes people, providers, containers, GPUs, spending,
  publication, release, or new cohorts.
- A sealed predecessor artifact changes.

Any falsifier makes the affected result `failed` or `invalid`; it never becomes
missing-at-random.

## Consequence

If the gate passes, Telos will know exactly which current bytes are usable,
which missing outcomes remain unresolved, how candidate rows cluster by task,
what independent roles and leakage controls are required, and what future
measurements could identify. It will have a tamper-evident, ready-to-review
protocol rather than another unregistered judgment.

It will still lack independent semantic ground truth, validated detector
efficacy, a task-population estimate, fix-size transfer evidence, review
independence, and authority to spend or execute GROUND-TRUTH-1.

## External-action boundary

Allowed: deterministic offline reads of tracked repository bytes, local
provider-free builders and tests, documentation, ordinary branch and pull
request publication, continuous governed CI, and read-only GitHub
observations.

Forbidden: provider or model requests, model judgments as labels, human
recruitment or contact, collaborator changes, target execution, scientific
containers, GPU or accelerator use, witness or consequence generation,
adjudication, new solves or cohorts, re-certification, unsafe execution,
workflow dispatch or rerun, spending, release, paper submission, visibility
change, unrelated repository-setting mutation, and edits to sealed evidence.

A timeout, missing reviewer, unavailable Docker daemon, missing credential,
or incomplete artifact never implies approval or a negative outcome.
