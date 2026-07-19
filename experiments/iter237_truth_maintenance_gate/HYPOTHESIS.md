# Iter237 — truth-maintenance gate before further science

Status: prospective, pre-registered before any iter237 implementation, correction
artifact, result, or current-state pointer exists.

Predecessor: draft iter236 branch at
`9a556e3ed0402ef5390ec7f8e2aa325a03e716a1`; merged master remains
`27e8f5a`.

## Why this iteration exists

Iter236 did the right first thing: it reconstructed a prose-only analysis and
showed that two figures of record do not regenerate. A fresh independent audit
then found that the branch cannot be merged as written.

The problem is not the reconstructed arithmetic. The problem is the inference
and the control plane around it:

1. Iter236 measures how common a selector is among rows with **no held-out
   susceptibility labels**, then concludes that the selector “enriches
   nothing” and “does not transfer.” Selector prevalence is not predictive
   enrichment.
2. The two fresh cohorts have `k=0`, `N=37`, and `u=13` in total. Those
   thirteen certified outcomes remain unknown and were not included in
   iter235 witness recovery. The current README and paper nonetheless describe
   the rate as concentrated in the reused cohort.
3. The current paper still carries the non-regenerating `p=0.008`, stale
   pre-iter235 cross-solver counts, and conclusions stronger than its
   missingness and label quality permit.
4. The iter236 builder restates a source-selection predicate its
   pre-registration required it to import, and its tolerant comparator accepts
   JSON type changes such as `62` to `62.0`.
5. The draft branch edits the sealed iter235 result in place. A correction
   pointer is useful, but changing a sealed predecessor is not append-only.
6. Iter221’s prohibition on bit-exact comparison of libm-derived values scans
   only the iter219 guard. Iter236 repeated the same defect at a new site.
7. `AGENTS.md` sends every new session to the sealed iter222 `HANDOFF.md`,
   while `mission/loop.json`, README, the paper, and the latest dated handoff
   disagree about current state. Existing validators certify their own frozen
   surfaces and do not detect the split.

A green 286-command closure and 803 passing tests coexist with every defect
above. That is evidence that Telos has command closure, not claim closure.

## Kind of iteration

This is a zero-spend integrity correction, not a scientific experiment. The
audit findings were observed before this pre-registration, so they are not
prospective discoveries. This document freezes the repair acceptance bars and
the claim boundary before implementation.

Allowed:

- offline analysis of committed bytes;
- additive correction and mission-direction artifacts;
- repairs to active builders, validators, tests, README, paper source/PDF, and
  the mutable current-state pointer;
- restoration of a sealed predecessor to its merged-master bytes;
- local tests and local deterministic paper builds.

Forbidden:

- provider calls, model judgments, container experiments, workflow dispatch,
  publication submission, release, paid work, or scientific numerator changes;
- editing any sealed experiment hypothesis, result, proof, or raw evidence as
  the means of correction;
- treating a digest, model consensus, or gold differential as independent
  semantic ground truth;
- merging PR #85 while any acceptance bar below fails.

Budget: `$0`.

## Claims under audit

### T1 — transfer

The registered iter236 calculation can reproduce the three recorded selector
fractions. It cannot establish transfer or enrichment because the 447
non-cohort rows have no susceptibility outcomes.

Result categories:

- **supported** only if a preregistered, outcome-labelled held-out cohort exists
  and the selector improves a specified endpoint under its registered
  comparison;
- **contradicted** only if such a labelled comparison rejects that improvement;
- **untested** when only selector prevalence is available.

With the current inputs, T1 must be `untested`.

### T2 — fresh-cohort concentration

Iter224 and iter228 together contain `N=37` certified patches, `k=0` confirmed
patches, and `u=13` unadjudicated patches. A concentration claim is admitted
only if it survives the least-favourable missingness comparison:

`(k_fresh + u_fresh) / N_fresh < k_reused / N_reused`.

The current figures fail immediately: `13/37` is not below `5/29`. The current
state is `inconclusive`, not a concentration result.

### T3 — cross-solver evidence

The five fixed-cohort solver runs establish recurrence of at least one
operational certified-yet-wrong label across several solvers and providers.
Because targets, witness generator, judges, and many susceptible task
identities are reused, this is cross-solver recurrence on one convenience
cohort—not population generalization, a rate, model independence, or a model
ranking.

### T4 — benchmark labels

The released 13/54 evaluation set is an operational reference-differential
benchmark. Its 54 negative controls comprise 29 patches normalized-identical
to accepted patches and 25 patches with no divergence on one retained witness.
The latter are not independently proven semantically correct. Detector
false-positive figures over all 54 are therefore flag rates on mixed
reference-equivalent and unresolved controls unless independent adjudication
is added.

## Acceptance bars

1. **Sealed-byte discipline.** Every path under
   `experiments/iter235_witness_recovery/` is byte-identical to merged master.
   Corrections live only in iter236/iter237 and current mutable surfaces.
2. **Structural source-rule reuse.** Iter236 obtains the test-file exclusion
   decision by executing the imported iter202/solver predicate, not by
   restating its string conditions. A known-bad fixture containing the
   restatement fails.
3. **Strict typed numeric comparison.** Only float-versus-float values receive
   tolerance. Integers, booleans, strings, nulls, arrays, objects, and every
   cross-type change compare exactly or fail. Known-bad fixtures include
   `62` versus `62.0`, `"0.5"` versus `0.5`, and `True` versus `1`.
4. **Repository-wide libm guard.** One validator scans all active Python guard
   scripts, not a named predecessor, and rejects an exact artifact comparison
   in a script deriving values through libm or Wilson intervals. It must reject
   fixtures reproducing both the iter219 and iter236 bug classes.
5. **Scientific correction.** The active README and paper state T1–T4 at the
   boundaries above; the paper uses the registered asymptotic Mann–Whitney
   statistic (`U=331`, two-sided `p=0.005347` with tie and continuity
   correction) and labels the post-hoc comparison exploratory.
6. **Current counts.** The paper and README use the corrected per-run
   fixed-cohort counts from iter235: `5/29`, `2/25`, `3/17`, `4/14`, `1/16`,
   with `u=0,2,2,2,1`, and state that 17 patch-level positives correspond to
   12 unique tasks across all six measured runs.
7. **Current-state coherence.** A small mutable machine-readable pointer names
   the active gate, current dated handoff, paper revision, scientific status,
   and next authorized action. `AGENTS.md` reads this pointer first. A
   validator fails if the pointer, README, AGENTS bootstrap, or named files
   disagree. Frozen `HANDOFF.md` and `mission/loop.json` remain historical
   evidence and are labelled as such, not rewritten.
8. **Paper integrity.** Source and PDF hashes move together; the PDF is rebuilt
   deterministically twice and every rendered page is visually inspected.
9. **Honest closure.** Documentation says the closure covers registered CI
   commands and registered claims only. It never claims every published number
   is covered until a separate complete claim registry exists.
10. **World contact.** The full local closure passes under the oldest supported
    CI interpreter, and all required remote CI versions must pass before merge.

## Named falsifiers

- Any paper or README sentence still implies a measured population rate,
  fresh-cohort concentration, model independence, independent semantic ground
  truth, or validated transfer.
- Any sealed iter235 byte differs from merged master.
- Any current-state validator can pass while `AGENTS.md` routes a session only
  to the sealed iter222 baton.
- Either historical floating-point bug fixture passes the repository-wide
  numeric-guard validator.
- The corrected paper fails deterministic rebuild, hash validation, or
  page-by-page visual review.
- A local green result is treated as merge authority without the required
  remote CI evidence.

## What comes after this gate

No new solver purchase follows directly.

The next scientific gate is **GROUND-TRUTH-1**: independent, blinded human
semantic re-adjudication at unique-task level for the frozen 67-row benchmark
and the 13 missing fresh-cohort outcomes. Issue-only consequence tests are
frozen before reviewers inspect candidate patches; two independent engineers
label `wrong`, `valid`, or `unresolved`, with a third adjudicator for
disagreement. LLMs may be evaluated as detectors but may not supply ground
truth.

Only after that label and missingness repair should Telos attempt the larger
prospective assurance-delta study: private post-cutoff tasks, independently
authored hidden consequence tests, repeated agent runs, full trajectories, and
a comparison of visible tests, patch review, consequence tests, and
trajectory-plus-provenance evidence.
