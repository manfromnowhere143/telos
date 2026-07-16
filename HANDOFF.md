# HANDOFF — iter213 post-seal validation recovery

Generated: 2026-07-16T14:09:36Z from the exact clean source commit below. Read Current Gates first.

TELOS is a standalone repository. Resolve its root with `git rev-parse --show-toplevel`, then run every TELOS command from that root.

## Repository State

```text
handoff_schema: telos.iter213.handoff.v1
source_branch: agent/iter213-iter211-post-seal-validation-recovery
source_commit: f5cbb9df76f5fc2464e84f4d911313122d76545f
predecessor_seal: dc19e6f27f5a001632b5183ff798a6eacae6de33
publication_target: master
```

The source worktree was clean. This file is the sole allowed delta in the iter213 seal commit.

## Current Gates

Active gate: `experiments/iter207_claim_integrity_and_admission_recovery/HYPOTHESIS.md`

This remains sealed historical runtime authority only. It authorizes no current scientific execution.

Active publication gate: `experiments/iter213_iter211_post_seal_validation_recovery/HYPOTHESIS.md`

Prospective scientific gate (inactive): `experiments/iter212_tcp1_independent_cohort_and_custody_freeze/HYPOTHESIS.md`

Frozen upstream gate recorded by runtime-bound `CONTINUITY.md`: `experiments/iter202_natural_rate_scaled/HYPOTHESIS.md`

Local recovery status: **PASS; fresh publication seal pending**.

## Why Iter213 Exists

The exact iter211 source `1c99c9bf798fc2aadd1718a3ce77e2b55e9b0021` and handoff seal
`dc19e6f27f5a001632b5183ff798a6eacae6de33` remain unchanged. Their first complete post-seal suite passed
`648` tests and failed `3` non-scientific compatibility checks: one handoff heading assumption affected two
tests, and iter210 preflight compared a sealed experiment delta to additive descendant `HEAD`. The later
command catalog found the same title assumption in the detector-methodology surface scanner.

Diagnosis also found that iter210 and iter211 sealed-source discovery depended on whichever handoff was
currently displayed. Iter213 binds both iterations to their exact source/seal commits, verifies source Git
blobs on descendants, and accepts only the two registered current-gate and verification-heading families.
It does not weaken standing-claim scanning or change any TCP-1 artifact.

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

Receipt path: `experiments/iter213_iter211_post_seal_validation_recovery/proof/receipt_v2.json`

Receipt evidence count: `26`

Receipt closure SHA-256: `329bc6b2f19ee9f8e110e73af2c24cefa93e1363e9a24e553834ec90c09a7080`

Receipt SHA-256: `d3bf23942252fd6c1ec88500d861cd4851f92e6f92196d1a6be92ac846a4a403`

The receipt and predecessor guards read exact source Git blobs. The receipt proves byte identity, not
authorship, external chronology, licensing, independence, or semantic truth.

## Verification Before Action

Run from the repository root:

```bash
git status --short
git show --no-ext-diff --stat f5cbb9df76f5fc2464e84f4d911313122d76545f
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
python3 scripts/validate_handoff.py
```

Before publication, simulate a local two-parent merge whose first parent is current `master` and whose
second parent is the exact iter213 seal. Run iter210, iter211, iter213, receipt, mission, and handoff guards
inside that detached merge tree. Remove the temporary worktree/reference afterward.

## Publication Boundary

The seal commit must be the direct child of source `f5cbb9df76f5fc2464e84f4d911313122d76545f` and modify exactly `HANDOFF.md`. Publish that
unchanged source-plus-handoff tip once on `agent/iter213-iter211-post-seal-validation-recovery` and open one draft pull request against `master`.
Merge once with a two-parent merge commit only after exact-tip push and pull-request CI pass on Python 3.11
and 3.12 and no substantive review blocker remains. Do not amend, rebase, force-push, or extend the sealed
branch.

Repository publication authorizes no release, paper submission, provider request, GPU allocation,
scientific container or trajectory, workflow dispatch or rerun, deployment, payment, or scientific action.

## Scientific Boundary and Next Gate

Iter213 contributes no scientific `N`, `k`, `u`, benchmark score, effect estimate, model comparison,
population estimate, product-efficacy result, deployment claim, priority claim, or state-of-the-art claim.

After successful publication, the already-frozen iter212 hypothesis may begin only by filling real human,
model, task, hidden-test, control, runtime, isolation, timestamp, and budget evidence. It authorizes no model
call, accelerator allocation, or scientific trajectory. A separately versioned throughput gate remains
mandatory before any bounded pilot execution.
