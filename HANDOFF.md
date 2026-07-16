# HANDOFF — iter208 publication-only state

Generated: 2026-07-16T10:32:04Z from exact source commit A. Read Current Gates and Publication Boundary first.

TELOS is a standalone repository. Resolve its root with `git rev-parse --show-toplevel`, then run every TELOS command from that root.

## Repository State

```text
handoff_schema: telos.iter208.handoff.v1
source_branch: agent/iter208-post-seal-forensic-correction
source_commit: 184883088336cbae834e812a8d1dce0b7b031821
predecessor_seal: f4ee0d5bcb3b4abee7ebf1683be5b9edda263c28
publication_target: master
```

Source worktree at handoff generation: clean. This file is the sole allowed delta in seal commit B.

## Current Gates

Active gate: `experiments/iter207_claim_integrity_and_admission_recovery/HYPOTHESIS.md`

This is the sealed runtime/admission authority only. Its remote publication, dispatch, provider, container,
and scientific authorizations were never exercised and are superseded for publication.

Active publication gate: `experiments/iter208_post_seal_forensic_correction/HYPOTHESIS.md`

Frozen upstream gate recorded by runtime-bound `CONTINUITY.md`: `experiments/iter202_natural_rate_scaled/HYPOTHESIS.md`

Local correction status: **PASS; publication seal pending**.

## What Iter208 Established

- The forensic audit reconstructed the evidence from raw artifacts and preserved every historical
  experiment byte.
- Current paper and README claims no longer imply a causal recall direction, semantic ground truth,
  prevalence, model ranking, deployment efficacy, priority, or state of the art.
- Receipt v2 binds exact artifact paths, byte counts, SHA-256 digests, media types, producers, and one
  order-independent closure; v1 remains readable as historical evidence.
- The paper contains current 2026 related work and is positioned as a forensic real-task case series.
- The README, six Mermaid diagrams, paper, mission contract, citation metadata, audit, roadmap, and CI
  describe one bounded project state.
- Current cloud configuration is explicit and the active judge cannot redirect a bearer token through a
  caller-supplied endpoint.
- TCP-1 remains design-only and unexecuted.
- Iter200 remains exploratory with `1/24` confirmed lower, `7/24` worst-case missing-outcome upper, and
  `1/18` complete-case sensitivity reported together; these are not population bounds.

The receipt proves byte identity, not authorship, external chronology, or semantic truth.

## Source Receipt

Receipt path:
`experiments/iter208_post_seal_forensic_correction/proof/receipt_v2.json`

Receipt evidence count: `34`

Receipt closure SHA-256: `f2d6e85527c68ce1203a89f882feab15017240986103285c9264592ec60bb22c`

Receipt SHA-256: `dd9ff29b7b52d06e414eade5790cc33dce3e3456b5066f2346f70680f504596b`

The handoff validator rechecks every receipt-bound artifact both from repository-root bytes and from the
Git blobs in source commit A.

## Verified Local State

- Ruff and byte compilation: pass.
- Python tests: 624 passed.
- JSON guard: 3,500 files.
- Markdown guard: 717 files.
- Supply-chain guard: 19 workflows and two dependency locks.
- Paper: deterministic 12 pages, all fonts embedded, all pages visually inspected.
- Mermaid: all six diagrams rendered and visually inspected.
- Iter207 exact-seal claim, runtime, publication-safety, and recovery guards: pass.
- Iter208 final artifact guard and mission loop: pass.
- Provider calls, GPU scientific runs, scientific container runs, workflow dispatches, pushes, merges, and
  releases before source commit A: zero.

Known static-analysis exclusions remain bounded historical evidence: Bash-valid literal commitish braces in
the frozen iter203/iter204 workflows, iter204's documented unavailable job-level runner context, one
style-only warning in the frozen iter134 Docker runner, and one parsed-but-unused frozen iter207 smoke
manifest column.

## Verification Before Action

Run from the repository root:

```bash
git status --short
git show --no-ext-diff --stat 184883088336cbae834e812a8d1dce0b7b031821
ruff check .
python3 -m compileall -q telos scripts tests
pytest -q
python3 scripts/validate_json.py
python3 scripts/validate_docs.py
python3 scripts/validate_current_paper.py
python3 scripts/validate_mission_loop.py
python3 scripts/validate_supply_chain.py
python3 scripts/audit_iter207_claim_integrity.py --check
python3 scripts/build_iter207_runtime_manifest.py --check
python3 scripts/validate_iter207_publication_safety.py --check
python3 scripts/validate_iter207_runtime_recovery.py
python3 scripts/validate_iter208_post_seal_forensic_correction.py
python3 scripts/validate_handoff.py
```

No command above contacts a model provider, allocates a GPU, executes the scientific container cohort, or
dispatches a workflow.

## Publication Boundary

Seal commit B must be the single direct child of source commit A and modify exactly `HANDOFF.md`. Publish
the unchanged A+B tip to branch `agent/iter208-post-seal-forensic-correction` once, then open a draft pull
request. Do not amend, force-push, or add a follow-up commit after remote CI begins.

Merge requires green non-scientific branch and pull-request CI at the unchanged seal tip. Review the exact
two-commit delta again before merge. A repository merge does not authorize a release, paper submission,
workflow dispatch, provider call, GPU run, scientific container run, or scientific execution.

No provider call, GPU run, scientific container run, workflow dispatch, or release is authorized.

## Scientific and Strategic Boundary

The defensible scientific core is one exploratory strict certified-yet-wrong existence case plus a
22-row, eight-repository corpus of official-harness-resolved, gold-assisted targeted reference
differentials. The corpus is not independent semantic ground truth. Detector measurements remain
exploratory where their protocols failed.

The locator-assisted, gold-validated property pipeline remains protocol-failed and supplies no independent
false-positive estimate. The judge artifact has `8/88` response nondecisions; paired-gold flag accounting
must retain `3/22` observed lower, `6/22` missing upper, and `3/19` complete-case sensitivity.

The strategic direction is to build a reusable evidence and assurance substrate: complete trajectory
custody, pre-authored consequence checks, independent human labels, explicit missingness, standard
attestations, and independent replication. No private person's endorsement or funding decision is inferred.

## Next Research Gate

The next scientific path is TCP-1 only after a separately sealed iter209 materialization gate:

- 12 fresh tasks and five seeds per task;
- hidden consequence tests frozen before model output;
- two blinded independent human labels plus adjudication;
- exact weights, tokenizer, inference engine, source, and container digests;
- full trajectory and resource custody;
- exact paired primary analysis and explicit missingness;
- at most 64 accelerator-hours plus a separately approved monetary budget.

The local Apple M1 Pro host is not suitable for the full pilot. Repository publication alone authorizes none
of this execution.
