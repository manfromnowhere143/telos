# Iter211 — TCP-1 materialization preflight

Status: prospective zero-execution protocol/materialization gate, recorded after the verified iter210 merge
and before any TCP-1 task selection, model output, accelerator allocation, or scientific execution.

Predecessor merged master: `fb348eb1f67c0605679cd56a1cfa210cf192db03`.

## Purpose

Turn the TCP-1 roadmap design into a deterministic, reviewable admission packet and frozen analysis
implementation. This iteration tests whether TELOS can state every prerequisite precisely enough to refuse
an attractive but scientifically unauditable GPU run.

The expected honest outcome is split:

1. protocol, schemas, analysis code, threat model, and missing-prerequisite accounting can pass locally;
2. scientific execution admission must remain blocked while real external dependencies are absent.

This is not a scientific preregistration timestamp. The task cohort, hidden consequence tests, model,
reviewers, runtime, hardware, external timestamp, and approved monetary budget do not yet exist in the
evidence set.

## Frozen pilot shape

- `12` fresh coding tasks selected only after one open-weight model and its authoritative training cutoff are
  bound;
- `5` deterministic public seeds per task, for `60` natural trajectories;
- legitimate-implementation and deterministic-integrity controls retained under separate denominators;
- two independent task/test authors, two independent blinded semantic labelers, and a third adjudicator,
  with at least five distinct humans and no role overlap;
- complete model, tokenizer, inference-engine, sampling, source, container, hardware, trajectory, grader,
  resource, receipt, and attestation custody;
- one-sided exact conditional McNemar primary test, Wilson intervals for simple rates, and a deterministic
  task-cluster bootstrap sensitivity;
- at least ten independently adjudicated proxy-passing semantic failures for an interpretable primary
  detector comparison;
- `64` accelerator-hours total, including at most `2` hours for a one-task/one-seed non-cohort throughput
  preflight, plus a separately approved monetary budget.

## Acceptance bars

1. Machine-readable schemas cover task, canonical hash-chained trace events, trajectory, blinded human-label,
   analysis-input, and aggregate custody without embedding hidden test content in the agent-visible
   repository.
2. The protocol freezes seed derivation, gate semantics, endpoints, missingness, controls, falsifiers,
   resource ceilings, and forbidden inferences before any scientific output.
3. Analysis primitives implement the frozen exact paired test, Wilson intervals, separate control
   accounting, and deterministic task-cluster sensitivity, with adversarial unit tests.
4. Candidate, reviewer, execution-binding, resource, isolation, and control ledgers expose every absent
   prerequisite as structured missingness. Empty fields are never interpreted as ready.
5. An admission report returns materialization-preflight `pass`, scientific-execution `blocked`, and
   `execution_authorized=false` while any prerequisite is absent.
6. The exact merged iter210 baseline and its successful push, pull-request, and merged-master CI runs are
   bound as non-scientific predecessor evidence.
7. README, roadmap, mission state, CI, diagrams, result, review, receipt, and handoff tell the same bounded
   story and correct the roadmap numbering displaced by iter209/iter210 publication recovery.
8. No historical experiment or raw evidence byte changes.

## Falsifiers

- Any provider/model request, GPU allocation, scientific container, trajectory, workflow dispatch, rerun,
  deployment, payment, or release occurs.
- A candidate task, reviewer identity, model field, hardware field, timestamp, hidden test, budget, or
  scientific result is invented or inferred from absence.
- Execution becomes authorized with any blocked admission gate.
- Controls enter the natural-cohort endpoint or an LLM judge defines semantic ground truth.
- Hash identity is described as proving authorship, chronology, licensing, independence, or semantic truth.
- The selected pilot is described as a population estimate, model ranking, product-efficacy result,
  deployment-safety result, priority claim, or state of the art.
- TELOS imports code, state, evidence, branding, or operational authority from Aweb. TELOS, Sentinel, Inbar,
  and Odeya remain related projects that are separate from Aweb.

## Execution envelope

Allowed actions are local source/document generation, deterministic provider-free tests, read-only public
metadata verification, and eventual repository publication under the boundary below. Scientific execution
is explicitly unauthorized.

## Publication boundary

After every local gate passes, create one source commit directly above the merged iter210 master baseline,
derive an artifact-bound receipt, and create one handoff-only seal commit. The unchanged sealed branch may be
published once and opened as a draft pull request. Merge is allowed only after both Python CI jobs pass for
the exact push and pull-request tip and the two-parent merge topology is verified. Repository publication
does not authorize TCP-1 execution or a release.
