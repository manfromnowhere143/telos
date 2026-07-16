# HANDOFF — iter219 temporal consequence-test yield (published null)

Generated: 2026-07-17 from the exact clean source commit below. Read Current Gates first.

TELOS is a standalone repository. Resolve its root with `git rev-parse --show-toplevel`, then run every TELOS command from that root.

## Repository State

```text
handoff_schema: telos.iter219.handoff.v1
source_branch: agent/iter219-temporal-consequence-test-yield
source_commit: 78348446598bb4bb87ee5cda115f29d64db5237e
predecessor_merge: 470ca3627b7635d9a315cf2811ceb2eed6575fb9
publication_target: master
```

The source worktree was clean. This file is the sole allowed delta in the iter219 seal commit.

## Current Gates

Active gate: `experiments/iter207_claim_integrity_and_admission_recovery/HYPOTHESIS.md`

This remains sealed historical runtime authority only. It authorizes no current scientific execution.

Active publication gate: `experiments/iter219_temporal_consequence_test_yield/HYPOTHESIS.md`

Prospective scientific gate (inactive): `experiments/iter212_tcp1_independent_cohort_and_custody_freeze/HYPOTHESIS.md`

Frozen upstream gate recorded by runtime-bound `CONTINUITY.md`: `experiments/iter202_natural_rate_scaled/HYPOTHESIS.md`

Local status: **NULL published; fresh publication seal pending**.

## Why Iter219 Exists

Iter214 merged as `470ca3627b7635d9a315cf2811ceb2eed6575fb9` with green push, pull-request, and
merged-master CI, closing the publication-engineering line that ran from iter208. That line produced ten
consecutive iterations with no scientific `N`.

TCP-1 admission is blocked at `2` passing local-design gates, `9` blocked external gates. Two of those
blockers — the twelve-task cohort and its independently authored hidden consequence tests — otherwise
require recruited humans. Iter219 tested one cheap alternative at zero spend: could the tests maintainers add
*after* a task serve as those hidden consequence tests?

## The Result

**Iter219 is a NULL. Sealed bar `2` fails.**

Across `482` included SWE-bench Verified instances at the primary `365`-day window, tests added after a task
reference its touched symbols at forward `0.4066` (Wilson `95%` `[0.3637, 0.4511]`), while the backward
within-repository control `0.4336` is higher: difference `-0.0270` at `p = 0.925`. Tests written before a fix
cannot be consequence tests for it, so the forward rate is baseline repository vocabulary, not targeting.

Exposure is balanced (`0.942`), so the null is not an exposure artifact. Both sides had comparable numbers of
added tests; no instance had zero on either side.

## Read This Before Citing Any Iter219 Number

The cross-repository control alone reads `0.4066` versus `0.1660` at `p = 3.48e-24`. That is a false
positive. Django symbols do not appear in SymPy tests for trivial vocabulary reasons, so that control
estimates identifier specificity, never temporal targeting: **a control that cannot fail for the right reason
manufactures significance.** The backward within-repository control was added by a pre-data amendment
recorded while repositories were still cloning and before any instance was scored, and the pre-data `A2`
amendment is the only reason that false positive was not published.

This falsifies static symbol-name matching as a detector at this granularity. It does NOT falsify the
harvest hypothesis: the instrument cannot see a consequence test that drives changed code through a public
API without ever naming the changed symbol, which `psf__requests-1142` was verified to be before any
aggregate existed. A null must not be reported as evidence that maintainer consequence tests are absent, and
does not by itself justify purchasing human annotators.

The median instance touches `1` symbol while its window offers roughly `800` added tests, so the screen has a
`~40%` noise floor and near-zero discriminating power. Do not rebuild it with a retuned threshold.

## Sample and Missingness

`500` seen, `482` included, `18` excluded: `15` `no_enclosing_symbol` (module-level-only patches) and `3`
`window_commit_unresolvable`. Symbol extraction succeeded on `100%` of included instances.

## TCP-1 Boundary

Iter219 contributes no scientific `N`, `k`, `u`, benchmark score, effect estimate, model comparison,
population estimate, product-efficacy result, deployment claim, priority claim, or state-of-the-art claim.

Iter211's five deterministic seeds, `17` generated protocol artifacts, `2` passing local-design gates, `9`
blocked external gates, and `execution_authorized=false` remain unchanged. There are zero admitted tasks,
filled reviewer roles, model calls, GPU allocations, accelerator-hours, scientific containers, or
trajectories. Iter212 remains unchanged and inactive.

The standing exploratory iter200 sensitivities remain `1/24` confirmed lower, `7/24` worst-case missing
upper, and `1/18` complete-case; they must be reported together and are not a population rate.

The standing detector correction also remains binding: the property instrument is a locator-assisted,
gold-validated property pipeline, not an independent detector. Iter201 retains `8/88` judge-response
nondecisions; gold-control flag sensitivities are `3/22` observed lower, `6/22` worst-case missing upper, and
`3/19` complete-case. The property catches are a subset of judge catches and establish no ensemble gain or
independent false-positive rate.

## Source Receipt

Receipt path: `experiments/iter219_temporal_consequence_test_yield/proof/receipt_v2.json`

The receipt and predecessor guards read exact source Git blobs. The receipt proves byte identity, not
authorship, external chronology, licensing, independence, or semantic truth.

## Verification Before Publication

Run from the repository root:

```bash
git status --short
ruff check .
python3 -m compileall -q telos scripts tests
pytest -q
python3 scripts/validate_json.py
python3 scripts/validate_docs.py
python3 scripts/validate_current_paper.py
python3 scripts/validate_mission_loop.py
python3 scripts/validate_supply_chain.py
python3 scripts/build_iter214_receipt.py --check
python3 scripts/validate_iter214_tcp1_cross_platform_numeric_recovery.py
python3 scripts/build_iter219_receipt.py --check
python3 scripts/validate_iter219_temporal_consequence_test_yield.py
python3 scripts/validate_handoff.py
```

Before publication, simulate a local two-parent merge whose first parent is current `master` and whose
second parent is the exact iter219 seal. Run the full provider-free test suite, mission catalog, receipts,
predecessor guards, iter219 guard, and handoff guard inside that detached merge tree. Remove the temporary
worktree and reference afterward.

Re-running the measurement is optional and provider-free. It requires roughly `1.7 GB` of read-only public
clones and takes about an hour; the committed report already binds the dataset revision and every analyzed
head SHA, so the guard verifies the result without re-cloning.

## Publication Boundary

The seal commit must be the direct child of the iter219 source commit and modify exactly `HANDOFF.md`.
Publish that unchanged source-plus-handoff tip once on `agent/iter219-temporal-consequence-test-yield` and
open one draft pull request against `master`. Merge once with a two-parent merge commit only after exact-tip
push and pull-request CI pass on Python 3.11 and 3.12, the secret scan is non-blocking, and no substantive
review blocker remains. Do not amend, rebase, force-push, extend, or rerun a sealed failed branch.

Repository publication authorizes no release, paper submission, provider request, GPU allocation,
scientific container or trajectory, workflow dispatch or rerun, deployment, payment, or scientific action.

## Scientific Boundary and Next Gates

The honest successor to iter219 is **not** a retuned version of its screen. Token overlap is falsified at
this granularity; widening or narrowing its threshold would be fitting the instrument to a known answer.

An executed-coverage gate would answer the question this screen could not: run a later-added test against the
task's base commit and against its gold patch, and observe whether the changed lines are exercised and
whether the verdict differs. It requires containers and per-instance environments, is materially more
expensive than iter219, and is **not** authorized by this handoff.

The unchanged iter212 hypothesis may still proceed only by filling real human, model, task, hidden-test,
control, runtime, isolation, timestamp, and budget evidence. Iter215 is the later non-cohort throughput
preflight; iter216 is bounded execution; iter217 is blinded adjudication; and iter218 is independent
replication. No later stage is authorized by this handoff.
