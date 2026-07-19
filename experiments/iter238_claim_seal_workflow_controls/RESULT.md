# Iter238 result — public-claim, seal, and workflow controls

Status: **running.** The completed-evidence checks and a fixed read-only live
observation pass, but the direct-child successor seal, exact-proposed-head CI,
two-parent merge, and merged-master verification remain pending. No final
support verdict is licensed before those acceptance steps complete.

The prospective protocol is
[`HYPOTHESIS.md`](HYPOTHESIS.md), introduced at commit
`f8ef99b30ae3b97672b656c8b47d5b22cb27b649` with SHA-256
`54ec55dfabfe8fad85f5eb58f78ae9e8965a9f5f63e5c4339ff4ce50402f80ff`.
Its bytes remain unchanged.

This was a `$0` engineering-integrity gate. It made no provider or model call,
ran no scientific container, changed no scientific numerator or label, and
made no claim about model behaviour, detector efficacy, transfer, population
rate, benchmark validity, independent semantic truth, or state of the art.

## Provisional verdict

The completed-evidence checks pass at pre-seal head
`e7e79b0137b15fdf6f4d4cf60ee706b1ae8af1d6`, together with the later
read-only observation retained here:

- every quantitative atom in the declared current surfaces resolves to a
  stable claim projection or an exact typed non-claim;
- internally regenerated claims rebuild, while historical and external
  records retain their limitations;
- the merged-iter237 protected bytes remain unchanged;
- receipt replacement, protected-byte changes, workflow lifecycle drift, and
  claim-boundary mutations fail their known-bad fixtures;
- the historical workflows are retired on GitHub without dispatching,
  rerunning, enabling, deleting, or editing them; and
- the complete CI-derived closure passes locally and remotely on both required
  Python versions.

These results are provisional. Acceptance bar 11 is unevaluated until these
completed-evidence bytes are committed, the exact-tree successor seal is
appended in its direct child, and required Linux CI passes on that exact
proposed merge head. The subsequent two-parent merge and merged-master
verification are also pending. No timeout or green predecessor run substitutes
for those steps.

## C1 — complete current quantitative-claim coverage

The canonical
[`mission/claim_registry.json`](../../mission/claim_registry.json) and
[`proof/claim_coverage_report.json`](proof/claim_coverage_report.json) retain:

- `613` claims and `1,243` public bindings;
- `432` typed non-claims;
- `6` internally regenerated empirical claims;
- `30` external-citation claims;
- `473` historical or external records whose semantic metadata remains
  explicitly unresolved;
- `0` unclassified atoms, `0` conflicting projections, and `0` stale
  superseded assertions; and
- four preregistered public surfaces plus two supplemental hardening surfaces.

The corrected reviewed binding authorization is
`7e753a14712eca0e0b32787e2b57a32714e895d7de1ed64076961ff951aba3ca`.
The registry SHA-256 is
`65c6716e102ec7612f17a174bce0fb715117c071d312fed75425cda08cdec076`;
the report SHA-256 is
`51211f9e95651418a95680e61de2b379da647808c99e179b237f43769ad4b7e5`.

Coverage is lexical and provenance-complete for its declared surfaces. It is
not semantic adjudication. The `473` unresolved records are excluded from
scientific reuse rather than silently upgraded by a green count.

## C2 — retrospective and prospective byte integrity

The first seal-registry record is explicitly retrospective at merged iter237
commit `7307e0c1c4083443698cfde8f0ab20a27518717c`. It protects:

- `9,089` blobs below `experiments/`, manifest SHA-256
  `2582145c64c6e9994281deb39112cf4be1297d4f9dc28861d0efe5ec8cbb3149`;
- `23` released benchmark blobs, manifest SHA-256
  `17bcf1c6c72262d565da4984cd1963ab8b07cf914395236cbb85b1968cfa0189`;
- four historical root/runner blobs, manifest SHA-256
  `2c337ed1a3130a8fb87ce8176fab900620780e4c142b31cf927d81a6053a3d45`;
  and
- `29` historical workflow blobs, manifest SHA-256
  `e6cec9eac6632f25641290706c38d8cc176bde0279de9282505c81990f43631b`.

Only the previously absent
`experiments/iter238_claim_seal_workflow_controls/` component is admitted.
Pre-existing protected files cannot be modified, deleted, renamed, chmodded,
replaced by a symlink, or extended below an old protected path.

An integration failure exposed an over-strong first implementation: it treated
every commit under the absent iter238 component as a one-time file addition,
making a transparent correction to a newly introduced generated report
unrecoverable without rewriting Git history. The corrected invariant is
baseline-additive: regular files introduced inside the open component may
receive same-mode, pre-seal corrections retained in history. Deletion, rename,
mode/type change, every modification to `HYPOTHESIS.md`, and every post-seal
change still fail. The end-to-end fixture covers
addition → same-mode correction → exact-tree seal → rejected post-seal
correction.

The exact iter238 successor snapshot is intentionally not in this result
commit. The next commit must append it and change only
`mission/seal_registry.json`.

## C3 — sealed-receipt equality

`scripts/receipt_sealing.py::verify_against_source` now requires the current
receipt bytes and Git mode to equal the receipt's introducing Git blob, in
addition to verifying every bound historical source blob. A known-bad
temporary repository replaces a committed v2 receipt with different,
internally valid JSON; the guard rejects the replacement for source-blob
inequality.

This establishes the registered byte and ancestry properties. It does not
establish that generated prose, a signature, or a receipt is scientifically
correct.

## C4 — workflow lifecycle and world contact

The repository registry contains exactly `30` workflow files:
`ci.yml` is the sole active continuous control and the other `29` files are
historical and retired. GitHub also exposes one registered platform service,
Dependency Graph, making the live inventory `31` objects.

The retirement ran from committed source
`a1f1fec0a79989bb7b454cb4e8b1cc8ae8c8409c`. Its
[`receipt`](proof/workflow_retirement_receipt.json), SHA-256
`6248ab05e59be0b4383d6ebb4e009b595bb6118c10e9f82ad3a9a49c6aa40f71`,
records:

- `29` disable PUT requests;
- `0` dispatches, `0` reruns, `0` enables, `0` workflow deletions, and `0` run
  deletions;
- `32` cumulative GET requests in the pre-disable snapshot and `93` cumulative
  GET requests after per-workflow verification and the post-disable snapshot;
  and
- all `29` historical workflows `disabled_manually`, with `ci.yml` and
  Dependency Graph active.

The fixed read-only follow-up observation at `2026-07-19T14:52:04Z` is
[`proof/raw/post_retirement_live_audit.json`](proof/raw/post_retirement_live_audit.json),
SHA-256
`0d73aa0f01401b807c0d5d452a3f1512275e9101c040bf816e5fe42984f70d97`.
It is bound to proposed-evidence head
`e7e79b0137b15fdf6f4d4cf60ee706b1ae8af1d6` and the HEAD-committed workflow
registry SHA-256
`d491e59817b95a83ff2a099d052919156b9028dcdc2b5ef1f2729f1bb6f13414`.
It used exactly three GET requests and records zero requests in every mutation
class.

At that observation:

- all `29` historical workflows remained `disabled_manually`;
- `ci.yml` and Dependency Graph remained active;
- iter204 retained exactly `0` workflow-dispatch runs;
- its push-run count remained `172`; and
- its latest run remained failure `29681435632`, created before retirement.

The unchanged iter204 workflow file retains SHA-256
`84f7f8b228624ff7244991e317e7f8146a6aacd93f803c1df983b6cceae4deb4`.
The unchanged iter204 count and latest ID between the retirement receipt and
the later observation establish that no new iter204 push failure was observed
after retirement through that time. The observation is mutable server state,
not timeless proof.

The controlled retirement and final-audit instruments account for `96` GET
requests and `29` disable PUT requests in total. Ordinary read-only `gh`
queries used to inspect pull-request CI are outside those instruments, so no
claim is made about a universal count of all read-only GitHub requests.

## C5 — pre-seal local and remote evidence

At exact proposed-evidence head
`e7e79b0137b15fdf6f4d4cf60ee706b1ae8af1d6`:

- the current pointer, bootstrap, handoff, README, paper, and active gate
  agreed;
- known-bad fixtures for an unregistered paper number, conflicting
  README/paper value, removed missingness, stale active gate, unregistered
  workflow, executable job-level `runner.temp`, and protected-byte change all
  failed;
- all `292` commands derived from `.github/workflows/ci.yml` passed locally
  under Python `3.11.15`;
- the same `292` commands passed locally under Python `3.12.2`;
- push-event run `29691579467` passed Linux jobs `verify py3.11` and
  `verify py3.12`; and
- pull-request run `29691580755` passed Linux jobs `verify py3.11` and
  `verify py3.12`.

The local results are macOS/arm64 evidence. The named GitHub runs are
pre-seal Linux evidence; they do not satisfy acceptance bar 11 for the later
successor-seal proposed merge head. Neither is independent scientific ground
truth.

The first completed-evidence commit
`30727245643af7b1d0f97851cbf8ad576931c6b0` subsequently passed the same
`292`-command local closure under both required interpreters. Push run
`29692594995` and pull-request run `29692596412` each passed both Linux jobs on
attempt `1`, without a manual rerun. The successor-seal preflight then exposed
failure 12 below, so these green predecessor runs did not license sealing or
acceptance. Corrected-head and successor-seal-head CI remain pending.

## Failures and corrections retained during the iteration

The failures below are part of the result rather than being hidden behind the
final green state:

1. The first claim-registry design used proximity heuristics that could
   misclassify empirical values as identifiers. It was rejected and replaced
   by exact atom resolution, reviewed stable IDs, and adversarial migration
   replay.
2. The bootstrap writer inherited mode `0600` from `mkstemp`; current-state
   validation rejected the generated artifacts. The writer now publishes
   regular mode-`0644` files, with a known-good mode fixture.
3. Future-migration replay cloned the current registry/report and then asked a
   bootstrap that correctly refuses overwrite to initialize them. The replay
   now removes only those cloned outputs before rebuilding.
4. The current-state guard still expected claim-registry schema v2 after the
   registry advanced to v3. The expectation and fixture were corrected.
5. README simplification removed required historical release-manifest links.
   The base manifest, self-coverage report, and negative-guard report are
   visible again, and both public-sync and negative public-sync guards pass.
6. The initial seal-history rule rejected a same-mode correction to a file
   created inside the open successor component. It was replaced by the
   baseline-additive rule described above without changing the preregistration
   or any protected predecessor byte.
7. The first forced future-migration replay bypassed source-digest, seal, and
   prior-report checks and produced `68` adversarial failures. Forced replay
   was narrowed to the same fail-closed prior-evidence checks as ordinary
   migration before the candidate was accepted.
8. The first material-correction design reassigned only the changed public
   binding when one internal claim had multiple live bindings. That could
   leave an unchanged sibling bound to the corrected predecessor. Migration
   now requires every sibling reassignment, reciprocal lineage, and one exact
   historical source per prior binding.
9. An intermediate migration design rebuilt only the current generation of a
   correction chain, losing older material-lineage authority after a
   wording-only rebind and a later migration. Multi-generation replay now
   retains the complete reachable supersession component and rejects
   disconnected or unreachable lineage.
10. The first wording-only rebind path checked the visible atom but could
    accept drift in regenerated value, derivation, or sources. It now permits
    only an exact wording relocation and rejects any scientific-field change,
    which must use explicit material-correction lineage.
11. Freezing the current handoff changed one curated historical binding while
    the curated projection table still named its predecessor. Exact surface
    replay exposed the stale binding; the curated authority was updated and
    the migration fixture now requires exact live binding coverage.
12. The first post-result successor-seal preflight made the claim guard fail:
    the internal-prerequisite manifest hashed the whole append-only seal
    registry, so the preregistered seal-only child invalidated C1 merely by
    appending its own seal. No seal commit was created. Dependency schema v2
    now binds the canonical unique
    `iter237-merged-historical-baseline` record instead of its mutable
    container. A known-bad fixture proves an unrelated successor append leaves
    that projection unchanged, while baseline mutation, duplication, duplicate
    JSON keys, and non-finite JSON still fail.
13. The first post-result Python 3.11 closure invocation selected an
    unprovisioned interpreter and stopped because `pytest` was absent before
    repository tests ran. A subsequent hash-enforced macOS install correctly
    rejected the arm64 PyYAML wheel because `requirements-ci.txt` contains the
    authorized Linux-wheel hashes. Local reruns therefore used isolated
    environments with the exact pinned versions; only GitHub Linux CI supplies
    hash-enforced dependency evidence.

Every correction that affected a committed artifact is visible in ordinary
Git history; the material rejected pre-commit designs observed during this
iteration are disclosed above. No amend, rebase, force push, or
protected-evidence rewrite was used.

## Limits and next transition

This gate makes repository claims more auditable; it does not make the
programme's science stronger. In particular:

- fresh-cohort concentration remains `inconclusive`;
- fix-size transfer remains `untested`;
- recurrence remains limited to repeated solver runs on one fixed convenience
  cohort;
- the released labels remain operational reference-differential labels; and
- independent semantic ground truth remains absent.

The direct child of this completed-evidence commit must append an exact-tree
successor snapshot for the iter238 component and no other change. Required
exact-head CI, a two-parent merge, and merged-master CI then remain mandatory.

After iter238 is merged, repository governance is the next zero-provider-spend
engineering gate: required checks and review policy must become enforced
repository state rather than a house procedure. GROUND-TRUTH-1 remains blocked
on independent conflict-screened humans and a separately approved budget.
Models may be evaluated as detectors; they may not become the semantic
authority.
