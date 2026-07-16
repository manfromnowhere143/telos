# HANDOFF — iter209 publication-CI recovery

Generated: 2026-07-16T11:08:26Z from exact source commit C. Read Current Gates and Publication Boundary first.

TELOS is a standalone repository. Resolve its root with `git rev-parse --show-toplevel`, then run every TELOS command from that root.

## Repository State

```text
handoff_schema: telos.iter209.handoff.v1
source_branch: agent/iter209-publication-ci-recovery
source_commit: 1659670c6c13758cc9b1840e87633a627444ca39
predecessor_seal: a2c2863cf993cb6dd39d2fada8d58e4796929120
publication_target: master
```

Source worktree at handoff generation: clean. This file is the sole allowed delta in seal commit D.

## Current Gates

Active gate: `experiments/iter207_claim_integrity_and_admission_recovery/HYPOTHESIS.md`

This remains the sealed runtime/admission authority only. It authorizes no current publication or scientific
execution.

Active publication gate: `experiments/iter209_publication_ci_recovery/HYPOTHESIS.md`

Frozen upstream gate recorded by runtime-bound `CONTINUITY.md`: `experiments/iter202_natural_rate_scaled/HYPOTHESIS.md`

Local recovery status: **PASS; fresh publication seal pending**.

## Why Iter209 Exists

Iter208 source `184883088336cbae834e812a8d1dce0b7b031821` and handoff seal
`a2c2863cf993cb6dd39d2fada8d58e4796929120` were published exactly once. Push CI run
`29491806574` and pull-request CI run `29491841840` failed at that exact tip, so draft PR `#8` was not
merged.

The push run exposed an iter65 audit that compared a frozen historical source digest with the evolved
descendant worktree. The pull-request run exposed a unit test that inherited GitHub's synthetic-merge mode
before the test intentionally enabled it. Neither failure changed or contradicted a TELOS scientific result.

Iter209 makes the historical audit read exact source blobs from commit
`40cdf2d5bbbd4d9ccd22aebb54cf04606ed90702`, isolates the unit-test environment, and makes iter208 receipt
validation read its sealed source Git tree on descendants. The failed iter208 branch remains unchanged.

The separate parser record `29491805471` remains the disclosed frozen iter204 workflow parse null; iter209
does not rewrite it.

## Source Receipt

Receipt path: `experiments/iter209_publication_ci_recovery/proof/receipt_v2.json`

Receipt evidence count: `17`

Receipt closure SHA-256: `2dd0df00e90967a05bf441f1aff37f1b9478dcb352d8d286c67419df5f9a7e4a`

Receipt SHA-256: `653797ea21505510710c44034fe2c857ceec4339fce6c12d321e99dfb52ca21d`

The handoff validator checks every receipt-bound artifact against both repository-root bytes and the exact
Git blobs in source commit C. The receipt proves byte identity, not authorship, external chronology, or
semantic truth.

## Verified Local State

- Source commit C is the single direct child of the public iter208 seal.
- The iter209 source delta contains exactly 18 paths: 17 receipt-bound artifacts plus the receipt itself.
- Ruff, Python byte compilation, and action lint for current CI pass.
- Python tests: 632 passed.
- JSON guard: 3,502 files.
- Markdown guard: 719 files.
- Supply-chain guard: 19 workflows and two dependency locks.
- The provider-free pre-source validation catalog passed 238 commands; the commit-bound iter209 guard then
  passed against source commit C.
- The iter65 audit, iter208 descendant guard, current-paper guard, mission loop, and receipt builder pass.
- The deterministic paper remains the verified 12-page build with unchanged source and PDF identities.
- The updated recovery diagram rendered cleanly and shows iter208 as the preserved failed publication
  attempt and iter209 as the active recovery.

No provider request, GPU run, scientific container run, workflow dispatch, release, or scientific execution is authorized.

## Verification Before Action

Run from the repository root:

```bash
git status --short
git show --no-ext-diff --stat 1659670c6c13758cc9b1840e87633a627444ca39
ruff check .
python3 -m compileall -q telos scripts tests
pytest -q
python3 scripts/validate_json.py
python3 scripts/validate_docs.py
python3 scripts/validate_current_paper.py
python3 scripts/validate_mission_loop.py
python3 scripts/validate_supply_chain.py
python3 scripts/audit_receipt_schema_prompt_alignment.py
python3 scripts/validate_iter208_post_seal_forensic_correction.py
python3 scripts/build_iter209_receipt.py --check
python3 scripts/validate_iter209_publication_ci_recovery.py
python3 scripts/validate_handoff.py
```

These commands are provider-free and non-scientific.

## Publication Boundary

Seal commit D must be the single direct child of source commit C and modify exactly `HANDOFF.md`. Publish
the unchanged C+D tip once on fresh branch `agent/iter209-publication-ci-recovery`, then open a draft pull
request against `master`. Do not amend, rebase, force-push, or extend the failed iter208 branch.

After the fresh draft exists, close draft PR `#8` as superseded and link it to the iter209 pull request. Do
not delete or rewrite its branch; it is retained publication-failure evidence.

Merge requires green non-scientific push and pull-request CI at the unchanged iter209 seal tip. Recheck that
the branch tip, receipt, diff, base, and review state remain unchanged, then merge once with a two-parent
merge commit. A repository merge does not authorize a release, paper submission, workflow dispatch,
provider request, GPU run, container run, deployment, payment, or scientific execution.

## Scientific Boundary and Next Gate

Iter209 contributes no scientific `N`, `k`, `u`, benchmark score, effect estimate, model comparison,
population estimate, deployment claim, priority claim, or state-of-the-art claim. It changes no paper result
or historical experiment artifact.

The locator-assisted, gold-validated property pipeline remains protocol-failed and supplies no independent
false-positive estimate. The judge artifact retains `8/88` response nondecisions; paired-gold flag accounting
must continue to report `3/22` observed lower, `6/22` missing upper, and `3/19` complete-case sensitivity
together. The exploratory iter200 case remains `N=24`, `k=1`, and `u=6`, with `1/24` confirmed lower,
`7/24` worst-case missing-outcome upper, and `1/18` complete-case sensitivity reported together. None is a
population estimate.

TCP-1 remains the next scientific direction only after a separately sealed materialization gate: 12 fresh
tasks, five seeds per task, hidden pre-authored consequence tests, independent blinded human labels, exact
model/container/environment custody, paired analysis, explicit missingness, and at most 64 accelerator-hours
under a separately approved budget. Repository publication alone authorizes none of that execution.
