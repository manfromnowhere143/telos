# Iter208 — post-seal forensic correction

Status at creation: pre-execution correction gate.

## Predecessor

The immutable predecessor is the iter207 local handoff seal:

f4ee0d5bcb3b4abee7ebf1683be5b9edda263c28

Iter208 must not rewrite that commit or any frozen historical raw artifact. It exists because an
independent post-seal audit found publication issues after the iter207 seal.

## Hypothesis

A separately versioned correction can remove the unsupported paper claim, position TELOS honestly against
the July 2026 frontier, strengthen active evidence semantics, and make the project boundary explicit
without changing any historical scientific outcome.

## Required corrections

1. Replace the unsupported conclusion claim that shared-gold-line triggers may bias recall downward with
   the evidenced statement that no causal direction or magnitude is established.
2. Add directly relevant 2026 primary-source work and explicitly withdraw priority, state-of-the-art,
   prevalence, model-ranking, and deployment interpretations.
3. Condense infrastructure chronology in the paper conclusion while retaining the complete history in
   repository evidence and README.
4. Add artifact-bound receipt v2 while preserving receipt v1 compatibility.
5. Migrate the active Aweb-era score name to project-independent terminology while preserving frozen
   iter00 readability.
6. Remove the active hard-coded Vertex project locator.
7. Record the durable boundary: TELOS, Sentinel, Inbar, and Odeya are related to one another and separate
   from Aweb.
8. Synchronize README status, diagrams, paper, machine-readable proof, and handoff before publication.
9. Add conservative citation metadata without inventing a DOI, archive, affiliation, or publication state.

## Acceptance criteria

- The full test suite, lint, compilation, document guards, current-paper guard, and iter208 guard pass.
- The paper rebuild is deterministic, every font is embedded, and every rendered page is visually clean.
- All iter208 evidence artifacts are bound by receipt v2 and verify from a clean checkout.
- A source commit is followed by a minimal handoff seal commit whose exact scope is machine-checked.
- The final tree is clean.

## Falsifiers

Iter208 fails or remains open if:

- any frozen historical artifact changes;
- the unsupported directional claim survives anywhere on a current claim surface;
- an external source is represented more strongly than it supports;
- receipt v2 accepts traversal, symlink substitution, duplicate artifacts, or byte drift;
- the paper or README implies independent semantic ground truth for the 22-row corpus;
- any provider call, GPU run, container scientific run, workflow dispatch, push, merge, or release occurs
  before the correction gate is complete;
- a final independent audit finds a material contradiction.

## Authorization boundary

This iteration authorizes local source edits and local, provider-free validation. By the operator's later
2026-07-16 amendment, one final branch publication and a draft pull request are permitted only after the
local source commit, artifact-bound receipt, minimal handoff seal, and independent post-seal audit all pass.
Merge is permitted only after non-scientific branch and pull-request CI pass at that exact tip and the
reviewed diff remains unchanged. This amendment does not authorize a model-provider call, GPU allocation,
scientific container run, workflow dispatch, release, or scientific execution.
