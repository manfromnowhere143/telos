# Iter220 — iter219 publication CI recovery

Status: corrective publication-engineering gate recorded after exact iter219 push and pull-request CI both
failed on one required-phrase scan. This gate authorizes no scientific execution and changes no iter219
number.

Predecessor seal: `11e335e82100319a4f5f47d86eaea0c8e81edbbc`.

## Timing and scope

Iter219's null is unchanged. Its measurement, report, controls, bars, amendments, and claim boundary are
untouched. This gate repairs publication plumbing only. Iter219's branch and draft PR `#13` remain fixed at
the failed tip; they must not be amended, force-pushed, extended, rerun, or merged.

## Observed remote failure

- push CI run `29539630378`: Python 3.11 and 3.12 both failed at `Detector methodology-correction guard`;
- pull-request CI run `29539645041`: the same two jobs failed at the same step;
- exact message: `HANDOFF.md is missing corrected detector text: locator-assisted, gold-validated`;
- cause: `HANDOFF.md` wraps the required phrase as `locator-assisted,\ngold-validated`, and
  `scripts/validate_detector_methodology_correction.py` matches raw substrings with no whitespace
  normalization, so a Markdown line wrap defeats a correct sentence;
- every other guard, all `729` tests, and every iter219 receipt passed in each failed job.

The machine record is `proof/ci_failure.json`.

## The defect is not the sentence

**This is the fourth occurrence of one bug class in this repository.** A line wrap split this exact phrase
and broke the iter214 handoff seal in the previous session; the same class then defeated iter219's own `A1`
guard, and again defeated a blockquote-wrapped phrase in `validate_current_paper.py`. Reflowing prose repairs
one instance and leaves the trap armed for the next gate.

**The deeper defect is how the failure reached CI at all.** Iter219's local closure ran a hand-listed subset
of guards chosen from memory. `validate_detector_methodology_correction.py` was never in that list. CI runs
`252` guard commands; iter219 ran roughly `7` and called the result a full closure. A verification set chosen
by the same agent that wrote the change is not an independent check — it is the local expression of
Standard 9, where a gate is satisfied against one's own idea of the gate rather than the real one.

## Corrections

`C1` — normalize required-phrase scanning. `validate_detector_methodology_correction.py` collapses whitespace
runs and strips leading blockquote markers before matching, matching the normalizer already proven in
`validate_current_paper.py`. Snippet semantics do not change; no snippet depends on a newline or a `>`.

`C2` — make local closure equal CI closure. `scripts/run_ci_closure.py` parses `.github/workflows/ci.yml`,
executes every guard command it declares with the same environment overrides, and reports failures. The list
is derived from the workflow, never hand-maintained, so it cannot silently drift from what CI runs.

Neither correction touches an iter219 number, bar, amendment, control, or claim.

## Acceptance bars

1. `validate_detector_methodology_correction.py` passes on the unchanged iter219 sentence, and still fails
   when the required methodology text is genuinely absent rather than merely wrapped.
2. `run_ci_closure.py` derives its command list from `.github/workflows/ci.yml`, honours declared environment
   overrides, and reports the same single failure on the iter219 seal that CI reported.
3. Every guard CI runs passes locally at the iter220 seal, proven by `run_ci_closure.py` itself.
4. Iter219's `HYPOTHESIS.md`, `RESULT.md`, `proof/yield_report.json`, and `proof/analysis_amendment.json`
   remain byte-identical.
5. Iter219's branch and PR `#13` remain unchanged as failed-publication evidence.
6. The full provider-free suite and a disposable two-parent synthetic merge pass at the exact iter220 seal.
7. No provider request, model call, GPU allocation, container, repository test execution, workflow dispatch
   or rerun, payment, release, or scientific claim occurs.

## Falsifiers

- Any iter219 experiment byte changes.
- Any iter219 yield, control, interval, paired test, bar verdict, or claim boundary changes.
- The normalizer causes a required-phrase scan to pass while the required meaning is absent.
- `run_ci_closure.py` omits a guard command that `.github/workflows/ci.yml` runs.
- The failed iter219 branch or PR is mutated, extended, or rerun.
- Fresh push or pull-request CI fails at the unchanged iter220 tip.
- Any scientific, provider, accelerator, dispatch, payment, deployment, or release action occurs.

## Claim boundary

Iter220 contributes no scientific `N`, `k`, `u`, benchmark score, effect estimate, model comparison,
population estimate, or TCP-1 admission change. Iter219's null stands exactly as published. TCP-1 admission
remains `2/11` with `9` blocked and `execution_authorized=false`. Iter212 remains unchanged and inactive.

## Publication boundary

Create one receipt-bound source commit directly above the iter219 seal and one handoff-only seal. Publish the
fresh branch once, open one draft pull request against `master`, then close PR `#13` as superseded without
deleting or modifying its branch. Merge once with a two-parent merge commit only after exact-tip push and
pull-request CI pass on Python 3.11 and 3.12, the secret scan is non-blocking, and no substantive review
blocker remains. Publication authorizes no release or science.
