# Iter210 — Pull-request synthetic-merge recovery

Status: corrective publication-engineering gate, locally active after iter209 push CI passed and iter209
pull-request CI failed.

Predecessor seal: `91f9258730bf5520d86c9235d7ed2f03724ea103`.

## Timing and scope

This gate was recorded after the remote failure and initial diagnosis. It is not a scientific preregistration.
Iter210 changes no historical experiment artifact, paper result, empirical count, model output, or TCP-1
design. The published iter209 branch and draft PR remain unchanged.

## Observed remote state

- Push CI run `29493772108` passed Python 3.11 and 3.12 at the exact iter209 seal.
- Pull-request CI run `29494386126` failed both jobs at the iter209 guard because GitHub checked out a
  synthetic merge commit and the guard compared `HEAD^..HEAD` instead of seal-D-parent to seal D.
- GitGuardian passed. Parser record `29493771124` remains the frozen iter204 workflow parse null and is not
  an iter210 source regression.

## Acceptance bars

1. Iter209 validation resolves its exact public source and handoff commits whenever that seal is an ancestor
   of the current checkout, including push, pull-request merge, merged-master, and later-descendant modes.
2. Iter209 receipt checking reads exact source Git blobs on descendants and refuses to rewrite a sealed
   receipt.
3. Iter210 source and seal identity is derived from the handoff plus exact Git parent topology; it never
   assumes a pull-request checkout's `HEAD` is the branch tip.
4. Regression tests cover sealed-descendant receipt verification and branch-tip resolution.
5. The complete provider-free local closure passes, including an actual local two-parent synthetic-merge
   simulation.
6. An artifact-bound v2 receipt covers every iter210 source path except its own receipt, and the handoff seal
   changes only `HANDOFF.md`.
7. No provider request, GPU run, scientific container run, workflow dispatch, release, deployment, payment,
   or scientific execution occurs.

## Falsifiers

- The iter209 branch is amended, force-pushed, or extended.
- Push, PR, merge, or descendant topology selects the wrong branch tip.
- Any receipt checks mutable descendant bytes instead of its sealed source when sealed mode applies.
- Any historical experiment byte changes.
- Any iter210 source path is absent from the receipt closure.
- Either fresh push or pull-request CI matrix fails at the exact iter210 tip.
- Any scientific or provider action occurs.

## Publication boundary

Publish one fresh `agent/iter210-pr-synthetic-merge-recovery` branch at its final source-plus-handoff tip and
open one draft pull request against `master`. Preserve PR #9 and its branch as failed-publication evidence.
Only an unchanged exact tip with green push and pull-request CI on Python 3.11 and 3.12, no substantive review
blocker, and verified two-parent lineage may merge. Repository publication authorizes no release or science.
