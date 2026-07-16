# HANDOFF — iter214 TCP-1 cross-platform numeric recovery

Generated: 2026-07-16T14:40:34Z from the exact clean source commit below. Read Current Gates first.

TELOS is a standalone repository. Resolve its root with `git rev-parse --show-toplevel`, then run every TELOS command from that root.

## Repository State

```text
handoff_schema: telos.iter214.handoff.v1
source_branch: agent/iter214-tcp1-cross-platform-numeric-recovery
source_commit: 48910a55d3f46bd11f360fa4f0501a1d8e9312a1
predecessor_seal: dbe008211022e0abdff5bc9e47e871b02b6d5501
publication_target: master
```

The source worktree was clean. This file is the sole allowed delta in the iter214 seal commit.

## Current Gates

Active gate: `experiments/iter207_claim_integrity_and_admission_recovery/HYPOTHESIS.md`

This remains sealed historical runtime authority only. It authorizes no current scientific execution.

Active publication gate: `experiments/iter214_tcp1_cross_platform_numeric_recovery/HYPOTHESIS.md`

Prospective scientific gate (inactive): `experiments/iter212_tcp1_independent_cohort_and_custody_freeze/HYPOTHESIS.md`

Frozen upstream gate recorded by runtime-bound `CONTINUITY.md`: `experiments/iter202_natural_rate_scaled/HYPOTHESIS.md`

Local recovery status: **PASS; fresh publication seal pending**.

## Why Iter214 Exists

The exact iter213 source `f5cbb9df76f5fc2464e84f4d911313122d76545f` and seal
`dbe008211022e0abdff5bc9e47e871b02b6d5501` were published unchanged on draft PR `#11`. Push CI run
`29505707609` and pull-request CI run `29505789397` both failed on Python 3.11 and 3.12 at the same test.
Linux returned `2.7755575615628914e-17` for the Wilson lower endpoint at `k=0, n=10`; the local runtime
returned exact `0.0`. All other `656` tests passed in each failed job. The iter213 branch and PR remain
unchanged, were not rerun, and must not be merged.

Adding the iter214 evidence also exposed one remaining iter213 descendant-mode path that compared later
experiment files with the iter213 predecessor. A sealed iter213 now validates its immutable source Git blobs,
receipt, and source/seal topology. No iter213 experiment byte changes.

## Pre-data Mathematical Amendment

The Wilson calculation is unchanged for every interior case. Only its mathematically exact binomial
boundaries are canonicalized after calculation: `lower=0.0` when `successes==0`, and `upper=1.0` when
`successes==trials`. This removes platform-dependent one-ULP cancellation residue without changing an
endpoint, confidence level, cohort, control, missingness rule, threshold, or scientific claim. The amendment
was recorded before any TCP-1 data, model output, task, hidden test, trajectory, or semantic label exists.

## TCP-1 Boundary

Iter211's five deterministic seeds, `17` generated protocol artifacts, `2` passing local-design gates, `9`
blocked external gates, and `execution_authorized=false` remain unchanged. There are zero admitted tasks,
filled reviewer roles, model calls, GPU allocations, accelerator-hours, scientific containers, or
trajectories. Iter212 remains unchanged and inactive.

The standing exploratory iter200 sensitivities remain `1/24` confirmed lower, `7/24` worst-case missing
upper, and `1/18` complete-case; they must be reported together and are not a population rate.

The standing detector correction also remains binding: the property instrument is a
locator-assisted, gold-validated property pipeline, not an independent detector. Iter201 retains `8/88` judge-response
nondecisions; gold-control flag sensitivities are `3/22` observed lower, `6/22` worst-case missing upper, and
`3/19` complete-case. The property catches are a subset of judge catches and establish no ensemble gain or
independent false-positive rate.

## Source Receipt

Receipt path: `experiments/iter214_tcp1_cross_platform_numeric_recovery/proof/receipt_v2.json`

Receipt evidence count: `21`

Receipt closure SHA-256: `51e110df29358b19aa1fe40f89073734092ed6de283a831582f59535b185d8c2`

Receipt SHA-256: `a1ff11f179dc40b3464dd8ae26bf62999b356e3f5c30348dd165712b388e89f7`

The receipt and predecessor guards read exact source Git blobs. The receipt proves byte identity, not
authorship, external chronology, licensing, independence, or semantic truth.

## Verification Before Publication

Run from the repository root:

```bash
git status --short
git show --no-ext-diff --stat 48910a55d3f46bd11f360fa4f0501a1d8e9312a1
ruff check .
python3 -m compileall -q telos scripts tests
pytest -q
python3 scripts/validate_json.py
python3 scripts/validate_docs.py
python3 scripts/validate_current_paper.py
python3 scripts/validate_mission_loop.py
python3 scripts/validate_supply_chain.py
python3 scripts/build_iter210_receipt.py --check
python3 scripts/validate_iter210_pr_synthetic_merge_recovery.py
python3 scripts/build_iter211_receipt.py --check
python3 scripts/validate_iter211_tcp1_materialization_preflight.py
python3 scripts/build_iter213_receipt.py --check
python3 scripts/validate_iter213_post_seal_validation_recovery.py
python3 scripts/build_iter214_receipt.py --check
python3 scripts/validate_iter214_tcp1_cross_platform_numeric_recovery.py
python3 scripts/validate_handoff.py
```

Before publication, simulate a local two-parent merge whose first parent is current `master` and whose
second parent is the exact iter214 seal. Run the full provider-free test suite, mission catalog, receipts,
predecessor guards, iter214 guard, and handoff guard inside that detached merge tree. Remove the temporary
worktree and reference afterward.

## Publication Boundary

The seal commit must be the direct child of source `48910a55d3f46bd11f360fa4f0501a1d8e9312a1` and modify exactly `HANDOFF.md`. Publish that
unchanged source-plus-handoff tip once on `agent/iter214-tcp1-cross-platform-numeric-recovery` and open one draft pull request against `master`.
After the successor PR exists, close PR `#11` as superseded without deleting or modifying its branch. Merge
once with a two-parent merge commit only after exact-tip push and pull-request CI pass on Python 3.11 and
3.12, the secret scan is non-blocking, and no substantive review blocker remains. Do not amend, rebase,
force-push, extend, or rerun a sealed failed branch.

Repository publication authorizes no release, paper submission, provider request, GPU allocation,
scientific container or trajectory, workflow dispatch or rerun, deployment, payment, or scientific action.

## Scientific Boundary and Next Gates

Iter214 contributes no scientific `N`, `k`, `u`, benchmark score, effect estimate, model comparison,
population estimate, product-efficacy result, deployment claim, priority claim, or state-of-the-art claim.

The unchanged iter212 hypothesis may proceed only by filling real human, model, task, hidden-test, control,
runtime, isolation, timestamp, and budget evidence. Iter215 is the later non-cohort throughput preflight;
iter216 is bounded execution; iter217 is blinded adjudication; and iter218 is independent replication. No
later stage is authorized by this handoff.
