# HANDOFF — iter210 pull-request topology recovery

Generated: 2026-07-16T11:47:32Z from exact source commit E. Read Current Gates and Publication Boundary first.

TELOS is a standalone repository. Resolve its root with `git rev-parse --show-toplevel`, then run every TELOS command from that root.

## Repository State

```text
handoff_schema: telos.iter210.handoff.v1
source_branch: agent/iter210-pr-synthetic-merge-recovery
source_commit: 323130bd96b20c062005f097294d8fab235bea93
predecessor_seal: 91f9258730bf5520d86c9235d7ed2f03724ea103
publication_target: master
```

Source worktree at handoff generation: clean. This file is the sole allowed delta in seal commit F.

## Current Gates

Active gate: `experiments/iter207_claim_integrity_and_admission_recovery/HYPOTHESIS.md`

This remains the sealed runtime/admission authority only. It authorizes no current publication or scientific execution.

Active publication gate: `experiments/iter210_pr_synthetic_merge_recovery/HYPOTHESIS.md`

Frozen upstream gate recorded by runtime-bound `CONTINUITY.md`: `experiments/iter202_natural_rate_scaled/HYPOTHESIS.md`

Local recovery status: **PASS; fresh publication seal pending**.

## Why Iter210 Exists

Iter209 source `1659670c6c13758cc9b1840e87633a627444ca39` and handoff seal
`91f9258730bf5520d86c9235d7ed2f03724ea103` were published once. Push CI run `29493772108` passed Python
3.11 and 3.12. Pull-request CI run `29494386126` failed both jobs because GitHub checked out a synthetic
two-parent merge commit and the new guard treated that merge `HEAD` as the branch seal. Draft PR `#9` was
not merged. GitGuardian passed.

Iter210 resolves the exact public iter209 seal whenever it is an ancestor of the checkout, verifies sealed
receipt artifacts from source Git blobs, and derives its own source and handoff seal from exact Git parents.
Push, pull-request merge, merged-master, and later-descendant modes therefore use one fail-closed topology
rule. The failed iter209 branch remains unchanged.

Parser record `29493771124` remains the disclosed frozen iter204 workflow parse null and is not an iter210
source regression.

## Source Receipt

Receipt path: `experiments/iter210_pr_synthetic_merge_recovery/proof/receipt_v2.json`

Receipt evidence count: `17`

Receipt closure SHA-256: `a16536c454aee33ef92b7fb05b1c01d7287eb9225bfc178a700cc2e8668dc40f`

Receipt SHA-256: `7f0f003fde80183165fc3070d69bfb2e92daed68d8178b8a25bb92a1d4840c98`

The handoff and receipt guards check exact source Git blobs. The receipt proves byte identity, not authorship,
external chronology, or semantic truth.

## Verified Local State

- Source commit E is the single direct child of the public iter209 seal.
- The iter210 source delta contains exactly 18 paths: 17 receipt-bound artifacts plus the receipt itself.
- Ruff, Python byte compilation, current CI action lint, and deterministic artifact regeneration pass.
- Python tests: 641 passed.
- JSON guard: 3,504 files.
- Markdown guard: 721 files.
- Supply-chain guard: 19 workflows and two dependency locks.
- The provider-free pre-source catalog passed 240 commands; the two commit-bound guards are rerun after seal F.
- Iter208, iter209 sealed-descendant, iter210 preflight, current-paper, mission-loop, and receipt guards pass.
- The deterministic paper remains the unchanged verified 12-page build.
- The recovery diagram rendered cleanly and distinguishes iter208, iter209, and active iter210.

No provider request, GPU run, scientific container run, workflow dispatch, release, or scientific execution is authorized.

## Verification Before Action

Run from the repository root:

```bash
git status --short
git show --no-ext-diff --stat 323130bd96b20c062005f097294d8fab235bea93
ruff check .
python3 -m compileall -q telos scripts tests
pytest -q
python3 scripts/validate_json.py
python3 scripts/validate_docs.py
python3 scripts/validate_current_paper.py
python3 scripts/validate_mission_loop.py
python3 scripts/validate_supply_chain.py
python3 scripts/build_iter209_receipt.py --check
python3 scripts/validate_iter209_publication_ci_recovery.py
python3 scripts/build_iter210_receipt.py --check
python3 scripts/validate_iter210_pr_synthetic_merge_recovery.py
python3 scripts/validate_handoff.py
```

Before any push, create a temporary local two-parent merge with first parent `master` and second parent seal F,
run the iter209, iter210, and handoff guards from that detached merge tree, then remove the temporary worktree
and reference. This simulation must not push, dispatch, contact a provider, or alter either parent.

## Publication Boundary

Seal commit F must be the single direct child of source commit E and modify exactly `HANDOFF.md`. Publish the
unchanged E+F tip once on fresh branch `agent/iter210-pr-synthetic-merge-recovery`, then open a draft pull
request against `master`. Do not amend, rebase, force-push, or extend the failed iter209 branch.

After the fresh draft exists, close draft PR `#9` as superseded and link it to the iter210 pull request. Keep
the iter209 branch and PR as publication-failure evidence.

Merge requires green non-scientific push and pull-request CI at the unchanged iter210 seal tip. Recheck the
tip, receipt, diff, base, review state, and two-parent mergeability, then merge once with a merge commit. A
repository merge does not authorize a release, paper submission, workflow dispatch, provider request, GPU
run, container run, deployment, payment, or scientific execution.

## Scientific Boundary and Next Gate

Iter210 contributes no scientific `N`, `k`, `u`, benchmark score, effect estimate, model comparison,
population estimate, deployment claim, priority claim, or state-of-the-art claim. It changes no paper result
or historical experiment artifact.

The locator-assisted, gold-validated property pipeline remains protocol-failed and supplies no independent
false-positive estimate. The judge artifact retains `8/88` response nondecisions; paired-gold flag accounting
must report `3/22` observed lower, `6/22` missing upper, and `3/19` complete-case sensitivity together. The
exploratory iter200 case remains `N=24`, `k=1`, and `u=6`, with `1/24`, `7/24`, and `1/18` reported together.

TCP-1 remains design-only until a separately sealed materialization gate: 12 fresh tasks, five seeds per task,
hidden pre-authored consequence tests, independent blinded human labels, exact model/container/environment
custody, paired analysis, explicit missingness, and at most 64 accelerator-hours under a separately approved
budget. Repository publication authorizes none of that execution.
