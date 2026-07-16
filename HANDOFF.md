# HANDOFF — iter220 iter219 publication CI recovery

Generated: 2026-07-17 from the exact clean source commit below. Read Current Gates first.

TELOS is a standalone repository. Resolve its root with `git rev-parse --show-toplevel`, then run every TELOS command from that root.

## Repository State

```text
handoff_schema: telos.iter220.handoff.v1
source_branch: agent/iter220-iter219-publication-ci-recovery
source_commit: 5b7717715169a007574d51204dfe7636de748629
predecessor_seal: 11e335e82100319a4f5f47d86eaea0c8e81edbbc
publication_target: master
```

The source worktree was clean. This file is the sole allowed delta in the iter220 seal commit.

## Current Gates

Active gate: `experiments/iter207_claim_integrity_and_admission_recovery/HYPOTHESIS.md`

This remains sealed historical runtime authority only. It authorizes no current scientific execution.

Active publication gate: `experiments/iter220_iter219_publication_ci_recovery/HYPOTHESIS.md`

Prospective scientific gate (inactive): `experiments/iter212_tcp1_independent_cohort_and_custody_freeze/HYPOTHESIS.md`

Frozen upstream gate recorded by runtime-bound `CONTINUITY.md`: `experiments/iter202_natural_rate_scaled/HYPOTHESIS.md`

Local status: **PASS; fresh publication seal pending**.

## The Science Is Unchanged

Iter219 remains a NULL and its evidence is unchanged. Iter220 is publication plumbing only.

Across `482` included SWE-bench Verified instances at the primary `365`-day window: forward `0.4066`
(Wilson `95%` `[0.3637, 0.4511]`) against a backward within-repository control `0.4336` — difference
`-0.0270` at `p = 0.925`. Tests added before a task reference its symbols slightly more than tests added
after, so the forward rate is baseline repository vocabulary, not targeting.

The cross-repository control alone reads `0.4066` versus `0.1660` at `p = 3.48e-24`. That is a false
positive: **a control that cannot fail for the right reason manufactures significance.** Only the pre-data
`A2` amendment, recorded before any instance was scored, prevented its publication.

This falsifies static symbol-name matching as a detector at this granularity. It does NOT falsify the harvest
hypothesis: the instrument cannot see a consequence test that drives changed code through a public API
without naming the changed symbol. A null must not be reported as evidence that maintainer consequence tests
are absent.

## Why Iter220 Exists

Push CI run `29539630378` and pull-request CI run `29539645041` both failed on Python 3.11 and 3.12 at
`Detector methodology-correction guard`:

```text
HANDOFF.md is missing corrected detector text: locator-assisted, gold-validated
```

The sentence was correct. It wrapped across a line break, and the scanner matched raw substrings with no
whitespace normalization. **This is the fourth occurrence of that bug class here, and the second on this
exact phrase in this exact file** — it also broke the iter214 handoff seal one session earlier.

The iter219 branch and PR `#13` remain unchanged, were not rerun, and must not be merged.

## Read This Before Your Next Publication

The reflowed sentence is not the fix. The mechanism was this: iter219's local closure ran roughly `7` hand-listed guards while CI declares `257`. `validate_detector_methodology_correction.py` was never on that
list. A verification set chosen by the same agent that wrote the change is not an independent check — it is
Standard 9 at local scale, where the gate passes against your idea of the gate rather than the real one.

**Run `python3 scripts/run_ci_closure.py` before any push.** It parses `.github/workflows/ci.yml`, executes
every guard command CI declares with the workflow's own environment overrides, and cannot drift from CI
because it is derived from it. Do not hand-list guards again.

`scripts/validate_detector_methodology_correction.py` now normalizes whitespace and blockquote markers before
matching. A positive control proves it still fails when the methodology text is genuinely absent rather than
merely wrapped.

## TCP-1 Boundary

Iter220 contributes no scientific `N`, `k`, `u`, benchmark score, effect estimate, model comparison,
population estimate, product-efficacy result, deployment claim, priority claim, or state-of-the-art claim.

Iter211's five deterministic seeds, `17` generated protocol artifacts, `2` passing local-design gates, `9`
blocked external gates, and `execution_authorized=false` remain unchanged. There are zero admitted tasks,
filled reviewer roles, model calls, GPU allocations, accelerator-hours, scientific containers, or
trajectories. Iter212 remains unchanged and inactive.

The standing exploratory iter200 sensitivities remain `1/24` confirmed lower, `7/24` worst-case missing
upper, and `1/18` complete-case; they must be reported together and are not a population rate.

The standing detector correction also remains binding: the property instrument is a locator-assisted, gold-validated property pipeline, not an independent detector. Iter201 retains `8/88` judge-response
nondecisions; gold-control flag sensitivities are `3/22` observed lower, `6/22` worst-case missing upper, and
`3/19` complete-case. The property catches are a subset of judge catches and establish no ensemble gain or
independent false-positive rate.

## Source Receipt

Receipt path: `experiments/iter220_iter219_publication_ci_recovery/proof/receipt_v2.json`

The receipt and predecessor guards read exact source Git blobs. The receipt proves byte identity, not
authorship, external chronology, licensing, independence, or semantic truth.

## Verification Before Publication

Run the derived closure first; it supersedes every hand-listed subset:

```bash
git status --short
python3 scripts/run_ci_closure.py
python3 scripts/build_iter220_receipt.py --check
python3 scripts/validate_iter220_iter219_publication_ci_recovery.py
python3 scripts/validate_handoff.py
pytest -q
```

Before publication, simulate a local two-parent merge whose first parent is current `master` and whose
second parent is the exact iter220 seal. Run the derived closure inside that detached merge tree. Remove the
temporary worktree and reference afterward.

## Publication Boundary

The seal commit must be the direct child of the iter220 source commit and modify exactly `HANDOFF.md`.
Publish that unchanged source-plus-handoff tip once on `agent/iter220-iter219-publication-ci-recovery` and
open one draft pull request against `master`. After the successor PR exists, close PR `#13` as superseded
without deleting or modifying its branch. Merge once with a two-parent merge commit only after exact-tip push
and pull-request CI pass on Python 3.11 and 3.12, the secret scan is non-blocking, and no substantive review
blocker remains. Do not amend, rebase, force-push, extend, or rerun a sealed failed branch.

Repository publication authorizes no release, paper submission, provider request, GPU allocation,
scientific container or trajectory, workflow dispatch or rerun, deployment, payment, or scientific action.

## Scientific Boundary and Next Gates

The honest successor to iter219 is **not** a retuned version of its screen. Token overlap is falsified at
this granularity; widening or narrowing its threshold would be fitting the instrument to a known answer.

An executed-coverage gate would answer the question the screen could not: run a later-added test against the
task's base commit and against its gold patch, and observe whether the changed lines are exercised and
whether the verdict differs. It requires containers and per-instance environments and is **not** authorized
by this handoff.

The unchanged iter212 hypothesis may still proceed only by filling real human, model, task, hidden-test,
control, runtime, isolation, timestamp, and budget evidence. Iter215 is the later non-cohort throughput
preflight; iter216 is bounded execution; iter217 is blinded adjudication; and iter218 is independent
replication. No later stage is authorized by this handoff.
