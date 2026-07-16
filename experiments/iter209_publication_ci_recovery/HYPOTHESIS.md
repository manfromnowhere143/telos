# Iter209 — Publication CI recovery

Status: corrective engineering gate, locally active after the sealed iter208 publication attempt failed remote CI.

Predecessor seal: `a2c2863cf993cb6dd39d2fada8d58e4796929120`.

## Timing and scope

This file was created after GitHub had already exposed both defects and after the first narrow local edits
were made. It is therefore not a scientific preregistration and must never be described as one. Iter209 is
an additive publication-recovery record. It changes no historical experiment output, scientific numerator,
denominator, label, paper result, or TCP-1 design.

The failed iter208 branch and draft PR remain immutable evidence. Iter209 starts from that exact public seal
on a fresh branch; it does not amend, rebase, force-push, or append to the failed iter208 publication branch.

## Observed failures

- Push CI run `29491806574` at the exact iter208 seal failed because the frozen iter65 audit compared its
  recorded historical `telos/proof.py` digest with the evolved descendant worktree module.
- Pull-request CI run `29491841840` at the same seal failed because one unit test inherited GitHub's
  pull-request environment before the test intentionally enabled synthetic-merge behavior.
- Parser record `29491805471` is the already-disclosed frozen iter204 workflow parse null and is not an
  iter209 source regression.

## Acceptance bars

1. The iter65 audit hashes schema, proof module, and validator bytes from commit
   `40cdf2d5bbbd4d9ccd22aebb54cf04606ed90702`, while continuing to reject drift in iter65 evidence.
2. The publication-lineage unit test clears ambient GitHub mode before explicitly testing local, merged,
   and synthetic pull-request topologies.
3. Iter208's validator remains valid on descendants by checking its sealed source Git tree and receipt,
   not mutable descendant bytes.
4. Regression tests reproduce both original failure conditions and pass on Python 3.11 and 3.12.
5. The complete local non-scientific CI closure passes, including every historical audit reached after
   iter65, receipt verification, mission validation, and the clean-tree handoff guard.
6. An artifact-bound v2 receipt covers every iter209 source delta other than its own receipt, and the seal
   commit changes only `HANDOFF.md`.
7. No provider request, GPU allocation, scientific container run, workflow dispatch, release, deployment,
   payment, or scientific execution occurs.

## Falsifiers

- Any historical experiment byte changes.
- Either original current-CI failure still reproduces.
- Iter208 validation depends on descendant worktree bytes.
- Any source delta is absent from the iter209 receipt closure.
- Any branch or pull-request CI matrix job fails at the sealed iter209 tip.
- The iter208 branch is amended, force-pushed, or extended.
- Any scientific or provider action occurs.

## Publication boundary

Publish one fresh `agent/iter209-publication-ci-recovery` branch at its final source-plus-handoff tip and open
one draft pull request against `master`. Only after successful push and pull-request `ci` matrices at that
exact tip, an unchanged diff, and no substantive review blocker may the draft become ready and merge once
with a two-parent merge commit. Repository publication authorizes no release or scientific execution.
