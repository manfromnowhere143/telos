# HANDOFF — iter221 cross-platform guard tolerance

Generated: 2026-07-17 from the exact clean source commit below. Read Current Gates first.

TELOS is a standalone repository. Resolve its root with `git rev-parse --show-toplevel`, then run every TELOS command from that root.

## Repository State

```text
handoff_schema: telos.iter221.handoff.v1
source_branch: agent/iter221-cross-platform-guard-tolerance
source_commit: ef5bbdaa2d678543a6f75396161c0fbcd39bef57
predecessor_seal: 3cee092420c2d13227005c8d78e584ec69da832f
publication_target: master
```

The source worktree was clean. This file is the sole allowed delta in the iter221 seal commit.

## Current Gates

Active gate: `experiments/iter207_claim_integrity_and_admission_recovery/HYPOTHESIS.md`

This remains sealed historical runtime authority only. It authorizes no current scientific execution.

Active publication gate: `experiments/iter221_cross_platform_guard_tolerance/HYPOTHESIS.md`

Prospective scientific gate (inactive): `experiments/iter212_tcp1_independent_cohort_and_custody_freeze/HYPOTHESIS.md`

Frozen upstream gate recorded by runtime-bound `CONTINUITY.md`: `experiments/iter202_natural_rate_scaled/HYPOTHESIS.md`

Local status: **PASS; fresh publication seal pending**.

## The Science Is Unchanged

Iter219 remains a NULL and its evidence is unchanged. Iter220 and iter221 are publication plumbing only.

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

## Why Iter221 Exists

Push CI run `29540341974` and pull-request CI run `29540356205` both failed on Python 3.11 and 3.12 at
`Iter219 temporal consequence-test yield guard`:

```text
iter219: delta=180: control Wilson interval does not recompute
```

The interval was correct. The guard compared stored Wilson intervals to recomputed ones bit-exactly, and
`wilson_interval` calls `sqrt`, whose last-place result depends on the platform `libm`. The report was
computed on macOS; Linux recomputes to within one unit in the last place and exact equality fails on a
correct value.

Iter214 canonicalized the two mathematically exact Wilson boundaries. Interior values have no exact form to
canonicalize and stay platform-dependent, so iter214 could not have prevented this: same bug class, interior
rather than boundary. `exact_one_sided_mcnemar` is unaffected — it sums `comb()` over exact integers and
divides by `2**n`, and IEEE 754 division is exactly specified.

CI stops a job at its first failing step. Iter219's CI died at the detector guard and never reached this one;
iter220 repaired that step, CI advanced, and the next latent defect reached daylight for the first time.

PR `#13` and PR `#14` remain unchanged, were not rerun, and must not be merged.

## Read This Before Your Next Publication

Two lessons compound here, and neither is the sentence or the float.

**A guard must never assert bit-exact floating-point equality across machines.** IEEE 754 does not promise it
for `sqrt`-derived values. Wilson intervals now compare at `rel_tol=1e-9`: one unit in the last place is
about `1e-16` relative, and the coarsest tampering that could change a reported digit is about `1e-4`, so the
tolerance sits safely between. Integer counts, yields, exposure totals, and the exact paired test keep exact
comparison, because each is exactly reproducible everywhere.

**Run `python3 scripts/run_ci_closure.py` before any push.** It derives every guard command from
`.github/workflows/ci.yml` and cannot drift from CI. But know its limit: it runs on this machine, and **a
clean macOS closure cannot certify CI's Linux runners**. Use `--python python3.11` to match CI's interpreter,
and design guards to be platform-independent rather than verified on one platform. The laptop is not the
world.

## TCP-1 Boundary

Iter221 contributes no scientific `N`, `k`, `u`, benchmark score, effect estimate, model comparison,
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

Receipt path: `experiments/iter221_cross_platform_guard_tolerance/proof/receipt_v2.json`

The receipt and predecessor guards read exact source Git blobs. The receipt proves byte identity, not
authorship, external chronology, licensing, independence, or semantic truth.

## Verification Before Publication

Run the derived closure first; it supersedes every hand-listed subset:

```bash
git status --short
python3 scripts/run_ci_closure.py
python3 scripts/build_iter221_receipt.py --check
python3 scripts/validate_iter221_cross_platform_guard_tolerance.py
python3 scripts/validate_handoff.py
pytest -q
```

Before publication, simulate a local two-parent merge whose first parent is current `master` and whose
second parent is the exact iter221 seal. Run the derived closure inside that detached merge tree. Remove the
temporary worktree and reference afterward.

## Publication Boundary

The seal commit must be the direct child of the iter221 source commit and modify exactly `HANDOFF.md`.
Publish that unchanged source-plus-handoff tip once on `agent/iter221-cross-platform-guard-tolerance` and
open one draft pull request against `master`. After the successor PR exists, close PR `#14` as superseded
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
