# Iter214 — TCP-1 cross-platform numeric recovery

Status: corrective pre-data analysis/publication gate recorded after exact iter213 push and pull-request CI
both failed on one Wilson-interval boundary assertion.

Predecessor seal: `dbe008211022e0abdff5bc9e47e871b02b6d5501`.

## Timing and scope

This is a separately versioned analysis and publication-validation amendment before any TCP-1 task,
trajectory, semantic label, hidden test, model output, or scientific result exists. Iter211, iter212, and
iter213 experiment bytes remain unchanged. Iter213's branch and draft PR `#11` remain fixed at the failed
tip; they must not be amended, force-pushed, extended, rerun, or merged.

## Observed remote failure

- push CI run `29505707609`: Python 3.11 and 3.12 both failed in
  `tests/test_tcp1.py::test_wilson_interval_and_exact_paired_test_are_frozen`;
- pull-request CI run `29505789397`: the same two jobs failed on the same assertion;
- Linux returned a lower Wilson endpoint of `2.7755575615628914e-17` for `k=0, n=10`, while the local
  macOS runtime returned exact `0.0`;
- all other tests passed (`656`), and no later CI step executed after pytest failed;
- the recurring iter204 workflow parser failure remains frozen historical infrastructure evidence.

The exact machine record is `proof/ci_failure.json`.

Adding the iter214 evidence also exposed one remaining iter213 descendant-mode defect locally: its sealed
receipt and topology resolved correctly, but a later validation path still compared additive descendant
experiment files with the iter213 predecessor. Iter214 makes a sealed iter213 validate only its immutable
source Git blobs, receipt, and source/seal topology, matching the existing iter211 fail-closed pattern. This
is publication-validation plumbing only; no predecessor experiment or TCP-1 method changes.

## Mathematical correction

For a binomial Wilson score interval, the lower boundary at `k=0` is mathematically exactly `0`, and the
upper boundary at `k=n` is mathematically exactly `1`. Algebraically equal floating-point terms can leave a
one-ULP residue whose sign depends on the platform `libm` implementation. Canonicalize only those two exact
boundary cases after the unchanged Wilson calculation:

- if `successes == 0`, set `lower = 0.0`;
- if `successes == trials`, set `upper = 1.0`.

No interior estimate, confidence level, test statistic, endpoint, cohort rule, missingness rule, threshold,
or claim boundary changes. The machine-readable amendment is `proof/analysis_amendment.json`.

## Acceptance bars

1. Wilson `0/n` lower and `n/n` upper endpoints are exact protocol values on Python 3.11 and 3.12.
2. Interior Wilson endpoints retain the existing formula and regression value for `0/10`'s upper endpoint.
3. The exact paired McNemar implementation, task-cluster bootstrap, control separation, and all TCP-1
   schemas remain unchanged.
4. Iter211's sealed receipt continues to verify exact source Git blobs; iter214 is the only source of the
   pre-data numerical amendment.
5. Sealed iter213 validation reads its own source Git blobs and topology, never additive descendant files.
6. Iter213 branch `dbe0082…` and PR `#11` remain unchanged as failed-publication evidence.
7. README, roadmap, mission, CI, result, receipt, and handoff disclose the cross-platform failure and the
   narrow mathematical correction.
8. The full provider-free suite and a disposable two-parent synthetic merge pass at the exact iter214 seal.
9. No provider/model request, task selection, hidden-test authoring, GPU allocation, scientific container,
   trajectory, workflow dispatch/rerun, deployment, payment, release, or scientific claim occurs.

## Falsifiers

- Any iter213 or earlier experiment byte changes.
- Any interior Wilson result, primary endpoint, alpha, cohort, control, missingness, or claim rule changes.
- Any sealed predecessor validator reads additive descendant experiment bytes as predecessor scope.
- Any TCP-1 data is observed before this amendment is sealed.
- The failed iter213 branch or PR is mutated or rerun.
- Fresh push or pull-request CI fails at the unchanged iter214 tip.
- Any scientific, provider, accelerator, dispatch, payment, deployment, or release action occurs.

## Publication boundary

Create one receipt-bound source commit directly above the iter213 seal and one handoff-only seal. Publish a
fresh branch once, open one draft PR against `master`, then close PR `#11` as superseded without deleting its
branch. Merge once with a two-parent merge commit only after exact-tip push and pull-request CI pass on
Python 3.11 and 3.12, GitGuardian is non-blocking, and no substantive review blocker remains. Publication
authorizes no release or science.
