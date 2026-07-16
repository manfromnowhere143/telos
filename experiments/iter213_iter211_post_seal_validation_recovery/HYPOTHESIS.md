# Iter213 — Iter211 post-seal validation recovery

Status: corrective publication-engineering gate recorded after the first complete iter211 post-seal test
suite exposed three non-scientific compatibility defects.

Predecessor seal: `dc19e6f27f5a001632b5183ff798a6eacae6de33`.

## Timing and scope

This is not a scientific preregistration. Iter211 source
`1c99c9bf798fc2aadd1718a3ce77e2b55e9b0021` and handoff seal
`dc19e6f27f5a001632b5183ff798a6eacae6de33` remain unchanged. No iter211 artifact, TCP-1 seed, protocol,
schema, analysis rule, blocker, admission decision, or scientific claim may change. Iter212's prospective
independent-cohort hypothesis also remains unchanged and inactive.

## Observed post-seal failure

The first full `pytest -q` at the exact iter211 seal produced `648` passes and `3` failures:

1. the standing-claim scanner accepted only the historical `Verification Before Action` handoff heading,
   while iter211 correctly used `Verification Before Publication`;
2. iter210's compatibility test ran its frozen experiment-delta check against the current descendant `HEAD`,
   incorrectly treating additive iter211/iter212 experiment paths as mutations of iter210;
3. iter210 and iter211 sealed receipt/topology discovery still relied on the currently displayed handoff,
   so a later iteration's handoff could hide an otherwise valid sealed ancestor.

The subsequent provider-free command catalog found the same handoff-title assumption in the independent
detector-methodology current-surface scanner. It is the same compatibility class and is repaired under the
same exact-title-family rule.

The machine record is `proof/post_seal_failure.json`.

## Acceptance bars

1. Standing-claim extraction accepts exactly the singular/plural current-gate headings and the historical or
   publication verification headings, while preserving fail-closed missing-marker behavior.
2. Iter210 source and seal are fixed to their exact published commits and validate from arbitrary later
   descendants without reading mutable descendant bytes.
3. Iter211 source and seal are fixed to their exact local commits and validate from arbitrary later
   descendants without requiring iter211 to remain the displayed handoff.
4. Sealed iter210/iter211 receipt checks read exact source Git blobs, refuse rewriting, and retain exact
   parent/delta/receipt closure checks.
5. Regression tests exercise both handoff title families and exact sealed descendant resolution.
6. Iter211 remains a blocked scientific-execution receipt; iter212 remains inactive; no model, task, human,
   hidden test, budget, provider, GPU, container, trajectory, workflow dispatch, or release is introduced.
7. README, roadmap, mission, CI, result, receipt, and handoff record the post-seal failure and additive
   recovery without rewriting predecessor evidence.
8. The complete provider-free suite and mission catalog pass at the exact iter213 seal, including a local
   two-parent synthetic-merge simulation.

## Falsifiers

- Any iter211 or earlier experiment byte changes.
- Any iter212 byte changes or its independent-cohort gate is treated as active.
- A sealed receipt verifies current descendant files instead of exact source Git blobs.
- A later additive experiment is interpreted as a mutation of iter210 or iter211.
- Handoff heading compatibility disables the standing-claim scan or accepts an absent/ambiguous boundary.
- Any scientific execution, provider request, accelerator allocation, dispatch, deployment, payment, or
  release occurs.
- Either fresh branch or pull-request CI matrix fails at the unchanged iter213 tip.

## Publication boundary

Create one source commit directly above the iter211 seal, derive an artifact-bound receipt, and create one
handoff-only seal commit. Publish the unchanged branch once, open one draft pull request against `master`,
and merge once with a two-parent merge commit only after exact-tip push and pull-request CI pass on Python
3.11 and 3.12 and no substantive review blocker remains. Publication authorizes no release or science.
