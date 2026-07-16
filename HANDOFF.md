# HANDOFF — iter222 agent-solvable TCP-1 admission evidence

Generated: 2026-07-17 from the exact clean source commit below. Read Current Gates first.

TELOS is a standalone repository. Resolve its root with `git rev-parse --show-toplevel`, then run every TELOS command from that root.

## Repository State

```text
handoff_schema: telos.iter222.handoff.v1
source_branch: agent/iter222-tcp1-agent-solvable-admission-evidence
source_commit: d1495a8758541685bad778e684e675580d969edb
predecessor_merge: b38d8921d30ca665692afc024b4f0e3706902f78
publication_target: master
```

The source worktree was clean. This file is the sole allowed delta in the iter222 seal commit.

## Current Gates

Active gate: `experiments/iter207_claim_integrity_and_admission_recovery/HYPOTHESIS.md`

This remains sealed historical runtime authority only. It authorizes no current scientific execution.

Active publication gate: `experiments/iter222_tcp1_agent_solvable_admission_evidence/HYPOTHESIS.md`

Prospective scientific gate (inactive): `experiments/iter212_tcp1_independent_cohort_and_custody_freeze/HYPOTHESIS.md`

Frozen upstream gate recorded by runtime-bound `CONTINUITY.md`: `experiments/iter202_natural_rate_scaled/HYPOTHESIS.md`

Local status: **PASS; fresh publication seal pending**.

## What Iter222 Did

TCP-1 admission moves from `2/11` to `5/11` passing gates. Three gates — and only the three an agent can fill
without external humans, hardware, a budget, or any model inference — are now filled with evidence that fails
if fabricated:

- `model_license_cutoff_and_weight_binding`: `Qwen/Qwen2.5-7B-Instruct` (Apache-2.0) at commit
  `a09a35458c70`, with the SHA-256 of all four weight shards and the tokenizer retrieved live from the
  HuggingFace API, plus a three-model candidate menu. No weight bytes were downloaded.
- `external_transparency_timestamp`: a real RFC 3161 token from `freetsa.org` over a commitment binding the
  model, isolation, and hypothesis digests. It verifies against the authority's chain and re-verifies offline.
- `hostile_isolation_rehearsal`: all five registered attacks denied by the iter211 isolation contract, each
  with a positive control that removes the deny rule and confirms the rehearsal then reports the attack as not
  denied.

execution_authorized stays false. `5` pass, `6` blocked.

## The Honesty Boundary — Read Before Citing Iter222

A published digest proves byte identity, not that the model runs. A denied rehearsal proves policy coverage,
not runtime isolation. A timestamp proves existence-at-time, not authorship or semantic truth. None of these
is a scientific result, and iter222 establishes no model behavior, detector efficacy, cohort, throughput, or
population rate.

The six remaining gates require external humans, real runtime and hardware, a paid throughput preflight, and an approved budget. They are the substance of the unchanged, inactive iter212 gate, and no autonomous
iteration can fill them. Do not describe iter222 as advancing the science; it advances the paperwork that must
precede the science.

## Standing Corrections (unchanged)

The standing exploratory iter200 sensitivities remain `1/24` confirmed lower, `7/24` worst-case missing upper,
and `1/18` complete-case; they must be reported together and are not a population rate.

The standing detector correction also remains binding, and iter197 and iter201 remain protocol `FAIL` with
exploratory diagnostics retained only: the property instrument is a locator-assisted, gold-validated property
pipeline, not an independent detector. Iter201 retains `8/88` judge-response
nondecisions; gold-control flag sensitivities are `3/22` observed lower, `6/22` worst-case missing upper, and
`3/19` complete-case. The property catches are a subset of judge catches and establish no ensemble gain or
independent false-positive rate.

## Verification Before Publication

Run the derived closure first; it supersedes every hand-listed subset:

```bash
git status --short
python3 scripts/run_ci_closure.py
python3 scripts/build_iter222_receipt.py --check
python3 scripts/validate_iter222_tcp1_agent_solvable_admission_evidence.py
python3 scripts/validate_handoff.py
pytest -q
```

Run `python3 scripts/run_ci_closure.py` before any push. It derives every guard from `.github/workflows/ci.yml`.
The three evidence builders re-verify offline, so re-running them is optional; only the model-binding and
timestamp builders touch the network, and only to re-fetch public metadata.

The receipt path is `experiments/iter222_tcp1_agent_solvable_admission_evidence/proof/receipt_v2.json`. The
receipt proves byte identity, not authorship, external chronology, licensing, independence, or semantic truth.

Before publication, simulate a local two-parent merge whose first parent is current `master` and whose second
parent is the exact iter222 seal. Run the derived closure inside that detached merge tree. Remove the
temporary worktree and reference afterward.

## Publication Boundary

The seal commit must be the direct child of the iter222 source commit and modify exactly `HANDOFF.md`.
Publish that unchanged source-plus-handoff tip once on `agent/iter222-tcp1-agent-solvable-admission-evidence`
and open one draft pull request against `master`. Merge with a two-parent merge commit only after exact-tip
push and pull-request CI pass on Python 3.11 and 3.12, the secret scan is non-blocking, and no substantive
review blocker remains. Do not amend, rebase, force-push, extend, or rerun a sealed failed branch.

Repository publication authorizes no release, paper submission, provider request, GPU allocation, scientific
container or trajectory, workflow dispatch or rerun, deployment, payment, or scientific action.

## Scientific Boundary and Next Gates

The next scientific step is not another admission gate — those are now exhausted for an agent. It is one of:

- **iter202** (frozen upstream gate): the natural-rate replication is pre-registered with resume steps in
  `CONTINUITY.md`. It needs roughly single-digit dollars and provider keys and produces the first real
  scientific `k/N` in over twenty iterations. It requires operator direction.
- **iter212** (inactive scientific gate): fill the six human, runtime, and budget prerequisites. Requires
  recruiting five reviewers, independent authoring, real hardware, and an approved budget.

No later stage — throughput preflight, bounded execution, blinded adjudication, replication — is authorized by
this handoff.
