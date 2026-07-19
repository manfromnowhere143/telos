# Iter236 — reconstruct the $0 transfer analysis as committed, regenerable evidence

Status: pre-registered before any iter236 script, proof artifact, or result exists.

Predecessor merged master: `27e8f5a`.

## What kind of iteration this is, stated first

This is a **reconstruction**, not a discovery experiment, and the distinction is load-bearing.

The numbers under audit already exist as prose. Their values were fixed by
`docs/HANDOFF-2026-07-18-iter234.md` before this iteration began, so the usual purpose of pre-registration —
preventing a design from being conditioned on an outcome it has already seen — does not apply in its normal
form. What is pre-registered here instead is **the reproduction criterion**: which numbers must reproduce,
from which committed inputs, and what is written down if they do not.

Dressing reconstruction up as prospective discovery would be the inflation this repository's own rules
forbid. It is stated plainly instead.

## Why iter236 exists

`docs/HANDOFF-2026-07-18-iter234.md:74-89` records a `$0` analysis that redirected the programme's forward
plan. It concluded that the fix-size predictor **does not transfer**, and on that basis instructed successors
not to pursue cohort selection by fix size. `docs/HANDOFF-2026-07-18-iter235.md:224-231` carries the
instruction forward as an established negative, and `experiments/iter235_witness_recovery/HYPOTHESIS.md:29-30`
cites it as part of iter235's own motivation.

**No committed artifact regenerates any of it.** `git show --stat ca632bc` touched exactly one file — the
handoff — and no script under `scripts/` or `experiments/` computes a Mann-Whitney statistic. The strings
`added_per_f2p` and `added_per_graded` occur in exactly one file in the repository, the handoff prose.

This violates the standard the same documents assert. `docs/HANDOFF-2026-07-18-iter235.md:69-73`: *"Every
number must regenerate from committed artifacts. Never assert a number you have not re-derived."*

Three properties make it worth an iteration rather than a footnote:

1. **The CI closure cannot detect it.** `run_ci_closure.py` derives its 285 commands from `ci.yml`. An
   analysis that was never registered is invisible to it, so a green closure is not evidence that every
   published number regenerates. This is a demonstrated blind spot in the closure's coverage, not a
   hypothetical one.
2. **It is the instruction that stops a successor re-running the analysis.** A successor is asked to abandon
   a research direction on the authority of numbers they cannot check.
3. **It moved a headline in the convenient direction.** The analysis justified *not* spending budget.
   `docs/HANDOFF-2026-07-18-iter235.md:36-38` names surprisingly convenient results as the moment to distrust
   the instrument. This one was never instrumented.

## Inputs, all committed, all offline

- `experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/swebench_verified_rows_snapshot.json`
  — all `500` SWE-bench Verified rows with gold `patch`, `FAIL_TO_PASS`, `PASS_TO_PASS`.
- `experiments/iter202_natural_rate_scaled/proof/raw/solve_targets.json` — the `53`-target cohort.
- `experiments/iter224_natural_rate_scale_n/proof/iter200_per_candidate.json` and
  `experiments/iter228_fresh_diverse_cohort/proof/iter200_per_candidate.json` — the two null cohorts.
- `experiments/iter233_natural_benchmark_release/release/answers/answers.json` — the frozen `13/54` labels.
- `scripts/build_iter202_solve_targets.py`, `scripts/build_iter228_cohort.py` — the eligibility rules.

No provider call, no container, no network, no download. Budget `$0`.

## Claims under audit, with the reproduction bar for each

A claim **reproduces** only if the rebuilt value equals the recorded value exactly, under a derivation rule
committed in this iteration. "Close enough" is not a pass; a mismatch is recorded as a mismatch.

| # | Claim of record | Source of record | Bar |
| --- | --- | --- | --- |
| C1 | hacked median `4` added source lines vs `1` | handoff iter234:84 | exact |
| C2 | one-sided `p=0.0027` | handoff iter234:85 | exact to 4 significant figures |
| C3 | held-out median `5`, higher than hacked | handoff iter234:85 | exact |
| C4 | `>=4` keeps `61%` of `447` | handoff iter234:86 | exact to the stated precision |
| C5 | `added_per_f2p` selects `50%` | handoff iter234:87 | exact to the stated precision |
| C6 | `added_per_graded` selects `41%` | handoff iter234:87 | exact to the stated precision |
| C7 | `0` positives from `59` solved patches | handoff iter234:81, iter235:138, iter235 HYPOTHESIS:29 | exact |
| C8 | paper's `p=0.008`, two-sided | `paper/telos.tex:405` | exact to the stated precision |

## Named falsifiers

Each of these, if it occurs, is published as the result rather than repaired away:

- **F1** — any of C1–C8 fails to reproduce. The handoff's redirection was then partly unfounded, and that is
  stated in the record at full weight.
- **F2** — a claim cannot be evaluated because its derivation rule is unrecoverable from the record. It is
  reported as **unverifiable**, never as reproduced. Specifically: `docs/HANDOFF-2026-07-18-iter234.md:87`
  states six predictors were tested but names only three. The other three are unrecorded and this iteration
  **cannot** verify them. They are reported as an irrecoverable gap, and the "whole family is negative"
  declaration is demoted to an assertion.
- **F3** — this iteration's own derivation rule is chosen to make a number reproduce. The rule for "added
  source lines" is committed **before** any figure is published, and its exclusion rule for test files is
  the one already used by `build_iter202_solve_targets.py`, imported rather than restated, per the structural
  invariant rule.

## The uncomfortable consequence, pre-committed

If C7 fails to reproduce, then `experiments/iter235_witness_recovery/HYPOTHESIS.md` — a **sealed
pre-registration** — carries a misstated denominator in its motivation. That sealed file is **not edited**.
The correction is additive: recorded here, with a pointer added to iter235's `RESULT.md`, per the
never-edit-sealed-evidence rule.

If C8 fails to reproduce, `paper/telos.tex` carries a published statistic that does not regenerate, and the
paper is corrected before any submission. Paper submission remains operator-only regardless of outcome.

## A confounder this iteration also settles

`build_iter202_solve_targets.py:82` requires a `build_solve_patch` round-trip; `build_iter228_cohort.py:79`
does not, and the two implementations of the added-run test differ (exact equality with a reset versus
substring matching without one). The `53`-target cohort is enriched and the fresh cohorts are null, so a
difference in how they were drawn is a candidate explanation for the programme's largest open question.

This was found by **reading the two builders' source**, not by inspecting outcomes, so testing it is
instrument-validity selection and not outcome selection.

- **C9** — every iter224 and iter228 target is eligible under iter202's stricter rule.

If C9 holds, the cohorts are comparable on this axis and the enrichment question is untouched by it — a
negative result, published as such, that closes a question a reviewer would otherwise raise. If C9 fails, the
null-cohort comparison is confounded and the enrichment mystery has a mundane candidate answer.

## What iter236 does not do

- It does **not** test a new susceptibility predictor. Six were already tested on `53` rows with `10`
  positives and reported as fishing; adding a seventh under a new iteration number would launder that error.
- It does **not** widen, loosen, or reinterpret any instrument to make a number reproduce.
- It does **not** touch `validate_iter202_runtime_freeze.py`. That failure is a claim-boundary decision
  reserved to the operator.
- It establishes **no** model behaviour, detector efficacy, cohort, rate, or population frequency. A
  reproduced number is evidence that the record is internally sound, not that the underlying science is
  stronger.

## Acceptance bars

1. A committed builder regenerates C1–C9 from the listed inputs with `--check`, offline.
2. Every claim is reported reproduced, mismatched, or unverifiable, with no fourth category.
3. The builder is registered in `ci.yml` so the closure covers it.
4. The derivation rule for added source lines is imported from `build_iter202_solve_targets.py`, not restated.
5. No sealed artifact is edited.
6. Mismatches are propagated to every document carrying the affected number, and the propagation is listed.
