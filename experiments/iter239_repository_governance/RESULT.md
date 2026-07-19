# Iter239 result — repository-governance enforcement gate

Status: **running.** G0 through G5 have complete retained evidence. The
completed-evidence commit, direct-child successor seal, exact sealed-head CI,
two-parent merge, merged-master CI, and final read-only effective-rule
observation remain pending. No predecessor run substitutes for those closure
steps.

The prospective protocol is
[`HYPOTHESIS.md`](HYPOTHESIS.md), introduced at activation commit
`746f225f6c3718a1c2190dc00496386600fb2c5c` with SHA-256
`6de481754d9f5397a96f0f410dfa8e1efdc3f23e9b020556309d1987627b64b6`.
Its bytes remain unchanged. The frozen
[`policy.json`](policy.json) has SHA-256
`c0cd140f004f760c568c02c3857c80d252c098fa1590453f3930480904b4531c`.

This was a `$0` repository-integrity gate. It made no provider or model call,
ran no scientific workflow or GPU job, changed no scientific result, and
made no claim about model behaviour, detector efficacy, transfer,
prevalence, benchmark validity, or semantic ground truth.

## G0–G5 verdict

technical-control status: supported

independent-review status: blocked

overall governance status: blocked

The first status is limited to the exact technical controls and observations
named below. The other two remain blocked because the repository had, and
still has, one direct collaborator: `manfromnowhere143` with administration
authority. The pull-request rule therefore requires exactly zero approvals.
That is an honest satisfiable boundary, not human review.

## Frozen source and precondition

The one-time transaction ran from exact commit
`6f06e0254ee47e70fdb632f902e5d7b450d5791a`. Before mutation, push run
`29699832948` and pull-request run `29699848550` each passed both Python 3.11
and Python 3.12 jobs on attempt `1` for that exact head. The pull-request
contexts were event-specific and supplied by GitHub Actions integration
`15368`.

The retained
[`before_state.json`](proof/before_state.json), SHA-256
`2e73da23dbb294e6354fbca39063eddedf53219ca9d574179f9af1aa9bf5b8f5`,
records 15 GET requests at `2026-07-19T19:05:51Z` and zero writes. It found:

- public repository `manfromnowhere143/telos`, default branch `master`;
- `master` at merged iter238
  `fb87af7eb15b5235a722a7bb3fd3a48962019188`;
- no classic branch-protection object, repository ruleset, named ruleset, or
  effective rule;
- one direct collaborator and no pending invitation;
- the frozen Actions, merge-setting, workflow-permission, and fork-policy
  projections; and
- open pull request `#87` at the exact transaction head.

No precondition drift was observed.

## One bounded mutation and retained receipt

The fsynced
[`mutation_intent.json`](proof/mutation_intent.json), SHA-256
`d9b8f940782dc4a331bc3608da0d95433561a2baae23b54b182bcf8612aab2c6`,
was persisted before dispatch. It binds one POST to the frozen ruleset
endpoint and request-body SHA-256
`7c8db8fe1104ccd86f6cb35701d83dda35786786641cbc3f3bfa3c2211da4038`.

The
[`mutation_receipt.json`](proof/mutation_receipt.json), SHA-256
`86da5a78b891694bd969a8adc309c238bc2f32d00ed97f30a1f4522defdc5674`,
records `outcome: applied` from `2026-07-19T19:05:35Z` through
`2026-07-19T19:06:05Z`. The instrument issued exactly 28 GET requests and one
POST. It issued zero PATCH, PUT, DELETE, branch-update, force-push,
branch-deletion, collaborator, visibility, workflow, run, release, or
publication mutations.

GitHub returned HTTP 201 and assigned ruleset ID `19177100`. The server added
only inert `required_reviewers: []`; the retained normalization reports no
semantic difference from the frozen request. The
[`after_state.json`](proof/after_state.json), SHA-256
`b8db7c38768c665d6d69488ecee780986baefde86cd56563813fd921ffcab530`,
records 13 of the receipt's 28 GET requests at
`2026-07-19T19:06:05Z`, no compared-projection drift, and:

- active enforcement on `~DEFAULT_BRANCH` and `refs/heads/master`;
- zero bypass actors and server field `current_user_can_bypass: never`;
- deletion and non-fast-forward rules;
- pull-request association, merge-commit-only integration, and conversation
  resolution;
- an approval count of zero; and
- strict required checks `verify pull_request py3.11` and
  `verify pull_request py3.12`, each bound to integration `15368`.

The default branch changed from `protected: false` in the retained
before-state to `protected: true` in the retained after-state. The effective
rules reproduce the same four-rule floor.

## Operational fail-closed observation

The
[`operational_check.json`](proof/operational_check.json), SHA-256
`6f861dd0c65f9009fb5adc796ce89fdb7f942980cf3dac3416d8f943dc8a7c61`,
binds the ruleset transaction source above to operational source
`f593b5048585052671276c03940ef4df9154724c`.

At `2026-07-19T19:11:43Z`, every non-check merge requirement was satisfied
while the two exact app-bound checks were in progress. GitHub reported
`merge_permitted: false`. At `2026-07-19T19:15:57Z`, the same pull-request
head, workflow run `29700162423`, and check-run IDs `88227770724` and
`88227770736` had attempt-one success; GitHub then reported
`merge_permitted: true`. Each phase used nine GET requests and zero mutation
requests. No direct, force, or deletion update to `master` was attempted.

This observation demonstrates a time-bounded pending-to-success transition
for pull request `#87`. It does not prove that future GitHub state cannot
drift.

## Instrument failure and correction

The first GET-only pending capture, after ordinary empty commit
`7c5ff50b27f0bede27666598a73bc1048ad1b41b`, failed before materializing an
operational stage because GitHub returned two byte-identical
`X-OAuth-Client-Id` response fields. The client rejected every duplicate
response field except `Link`. That mode had zero POST authority, and the
failure wrote no acceptance evidence.

Commit `f593b5048585052671276c03940ef4df9154724c` narrowed the transport rule:
multiple `Link` fields remain combined in wire order; an exact duplicate of
the unused informational OAuth client field is canonicalized once; a
conflicting value and every unrelated duplicate remain rejected. Tests cover
the accepted and rejected forms. The successful operational observation used
that corrected driver.

The historical instruments are separately pinned rather than flattened:

- transaction driver SHA-256 at `6f06e02`:
  `1b077763df27f2a7a533523dacb90400671c8097a3e8f50de2552270d6f56590`;
- operational driver SHA-256 at `f593b50`:
  `58d90362fa076cfce76e0a1a232a6fc35e4d1fcf5299909e4d11d4e8c468ec1a`;
- historical governance-validator SHA-256 at both phase commits:
  `bc65107b7fc568c3bf68aac12af6108493a594069be056be24d8d49368075bfe`.

The completed validator requires both exact commits, recomputes every
source-bound phase digest from Git, permits only the registered
driver-and-test transition between them, retains current stable-byte checks,
and binds its own corrected bytes to current `HEAD`. This preserves the
instrument correction as provenance rather than treating the transaction as
if it ran with later code.

## Limits and closure

The retained control does not provide an eligible reviewer, a broad
repository-hardening baseline, scientific validity, or protection against
the repository owner later changing or deleting the ruleset through a
separate settings operation. Generated prose, CI success, the ruleset, and
this result are not semantic adjudicators.

The completed-evidence commit must now pass the full local closure. Its direct
child may append only the exact-tree iter239 successor seal. Required Linux
Python 3.11 and 3.12 CI must pass on that sealed tip without rerun
substitution. Integration then requires a two-parent merge commit whose tree
equals the sealed tip, followed by merged-master CI and a final read-only
effective-rule observation.

The review upgrade remains a separate future mutation. It requires an
operator-supplied, conflict-screened human identity and a preregistered rule
that is both satisfiable and enforced without bypass. GROUND-TRUTH-1 remains
blocked on independent conflict-screened humans and separately approved
funding.
