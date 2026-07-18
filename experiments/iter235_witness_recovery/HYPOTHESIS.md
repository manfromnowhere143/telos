# Iter235 — recover the 41 certified patches whose outcome was never adjudicated

Status: prospective, pre-registered before any iter235 witness, execution, judgement, or result exists.

Predecessor merged master: `4639b90`.

## Why iter235 exists

Across six natural-rate runs, `125` model patches were certified by the official harness. **`41` of them were
never adjudicated**: certified, not gold-equivalent, and lacking a usable gold-differential witness.

| run | certified | unadjudicated |
| --- | --- | --- |
| iter200 | 24 | 5 |
| iter223 | 29 | 5 |
| iter225 | 25 | 7 |
| iter226 | 17 | 8 |
| iter227 | 14 | 6 |
| iter229 | 16 | 10 |

Those `41` are exactly the `u` term that forces every natural-rate result to report `k/N`, `(k+u)/N`, and
`k/(N-u)` rather than a point estimate. They are the single largest source of uncertainty in the published
rates, and **the expensive compute for them is already spent** — solving and certification are done. Only the
witness stage failed.

The benchmark's `13` positives span only `11` unique instances, which caps every downstream interval near
`±0.2` and left iter234's independence endpoint underpowered. A `$0` analysis (recorded in
`docs/HANDOFF-2026-07-18-iter234.md`) established that the two obvious ways to get more positives do not work:
fresh cohorts yielded `0` from `59` solved patches, and the `p=0.008` fix-size lead does not transfer, since
selecting `>=4` added source lines keeps `61%` of held-out SWE-bench Verified. Witness recovery is what
remains, and it is cheap.

## What is being fixed

The witness generator was written once and shipped without a validity gate. The exercise generator had the
same defect until iter232 added one — a static gate plus a validate-and-retry loop — which took coverage from
`51/67` (six defective) to `65/67`. Iter235 applies that same treatment to the witness stage:

- a static validity gate (parses, AST-safe, prints a `RESULT=` observable, no always-raising format, parses
  on the oldest interpreter in the benchmark);
- a **paired in-container preflight**: a witness is adjudicable only if it produces a `RESULT=` on **both**
  the gold patch and the candidate patch. A witness that runs on one arm only cannot establish divergence;
- up to three regeneration attempts per row.

**The regeneration trigger is instrument failure only** — a row is selected because it has no adjudicable
witness, never because of its label, its divergence, or any outcome. Outcomes do not exist for these rows;
that is the point.

## Gold, and why it is not a leak here

The witness generator has always seen the gold hunk. It must: a *gold-differential* witness exists to compare
gold behaviour against candidate behaviour, and it is the ground-truth labelling instrument, not a detector.
The gold-free detectors of iter230, iter231, iter232, and iter234 never see a witness or its output. Iter235
changes nothing about that boundary.

## Adjudication is reused, not reinvented

Recovered witnesses are adjudicated by the **existing frozen protocol**: the two blind judges, with a strict
positive requiring official certification, a retained gold-differential divergence, and BOTH judges naming
ONLY the model. `both`, `neither`, invalid, or missing never confirm. No new rule is written for iter235, and
the existing rule is not modified.

## Endpoints

- **Recovery rate**: how many of the `41` gain an adjudicable witness, per run and in total.
- **New confirmed positives**, and the updated `k`, `N`, and `u` for each of the six runs.
- The **corrected natural-rate figures** stated beside the currently published ones, never in place of them.
- Every row still unadjudicated after three attempts, listed individually with its reason.

## Pre-registered expectation

1. Recovery will be **partial**. Some of the `41` are unadjudicable for reasons no retry fixes — a patch whose
   changed behaviour cannot be reached from importable code, or whose divergence is not observable in a short
   script. A recovery rate near `100%` would be evidence the gate is too permissive, not that the loop is good.
2. Among recovered rows, the confirmed rate will be **at or below** the observed rate among already-adjudicable
   certified patches (~`13/84`). Rows that resisted witnessing are plausibly the harder, less observable ones.
3. Recovery will **shrink `u` more than it grows `k`** in every run. That is still a win: `u` is what makes the
   published upper bounds wide.

The falsifiable claim is 3. If recovery adds positives without shrinking `u`, or shrinks `u` without adding
positives, both are informative and both get published.

## Consequence, pre-committed

Recovering these rows **changes published numbers** in six experiments and in the paper's natural-rate
paragraph. That correction is committed to here in advance so it cannot be avoided: the original figures stay
in their `RESULT.md` files, and iter235 reports the corrected `k/N` and `u` beside them with the reason.

If recovery yields **zero** confirmed positives, that is a clean negative: witness attrition was not hiding
positives, the `u` term was inflating uncertainty without concealing signal, and the enrichment question
returns to needing a genuinely better cohort-selection rule — which the `$0` analysis says nobody has.

## Acceptance bars

1. The `41` target rows are derived mechanically from committed per-candidate evidence, and the derivation is
   reproducible.
2. Every committed witness passes the static gate and the paired in-container preflight.
3. Adjudication uses the existing frozen judge protocol unchanged, with both judges naming only the model.
4. Corrected `k`, `N`, `u` are reported per run beside the published values, with the missing-outcome triple.
5. Container execution uses pinned images under the established isolation flags and a wall-clock row ceiling.
6. No sealed predecessor evidence byte changes; no runtime-manifest-pinned file is edited; the frozen iter230
   benchmark is not altered.

## Falsifiers

- A row is regenerated because of its label, divergence, or any outcome rather than instrument failure.
- The judge protocol is modified, or a new confirmation rule is introduced.
- Corrected figures replace published ones instead of being reported beside them.
- A witness is counted as adjudicable without producing a `RESULT=` on **both** arms.
- The frozen benchmark is altered, or a manifest-pinned file is edited.

## Claim boundary

Iter235 recovers measurement outcomes that were already paid for. It establishes no new cohort, no new
detector, and no population rate. Corrected rates remain cohort-specific lower bounds from a nonrandom
convenience sample, exactly as the originals are. A larger `k` would not make `13`-positive intervals narrow;
it would make them less dominated by missing data.

## Execution envelope

Allowed: witness-generation provider calls bounded at three attempts per row, safe container execution of
validated witnesses against committed gold and candidate patches, the existing two blind judges, local
analysis, repository publication. Estimated provider spend under `$40`. Forbidden: re-solving, re-certifying,
altering the frozen benchmark or any sealed evidence, modifying the judge protocol, and selecting rows by
outcome.
