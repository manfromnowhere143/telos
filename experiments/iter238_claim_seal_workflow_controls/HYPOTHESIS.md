# Iter238 — public-claim, seal, and workflow-control gate

Status: prospective. This document is committed before any iter238 registry,
validator, retirement receipt, server-side workflow retirement, result, or
known-bad fixture exists.

Predecessor: merged iter237 master commit
`7307e0c1c4083443698cfde8f0ab20a27518717c`, the two-parent merge of
`27e8f5ab44db637be24eb8eee96b283cc2cf0da4` and iter237 tip
`b7fc930b2b153577b58c0efb30f8b0a44289a4d4`.

## Why this iteration exists

Iter237 corrected the current scientific boundary and made repeated typed
numeric and platform-`libm` defects structural. Exact remote Linux Python 3.11
and 3.12 CI passed on the iter237 tip, PR #85 merged with two parents, and
merged-master CI passed.

That gate also established a limit: the closure regenerates registered
commands and claims. It does not discover every quantitative assertion in
mutable prose. A pre-implementation inventory found approximately 1,704
numeric-looking occurrences in `README.md`, 329 in `paper/telos.tex`, 83 in
the current handoff, and 12 in `mission/current.json`. Many are identifiers,
dates, versions, hashes, citations, protocol parameters, or examples, but a
T1--T4-only registry would not be complete.

Two further control failures were observed before this pre-registration:

1. `scripts/receipt_sealing.py::verify_against_source` reads and validates the
   receipt from its introducing commit but does not require the current receipt
   path to equal that Git blob. An internally valid descendant replacement can
   therefore cause the helper to validate the old receipt while the caller
   validates unrelated current JSON.
2. GitHub exposes thirty repository workflow files as active. Only `ci.yml`
   is a continuous control. The other twenty-nine are one-shot historical
   `workflow_dispatch` files. The sealed iter204 file contains
   `${{ runner.temp }}` in job-level `env`, where that context is unavailable.
   GitHub consequently created 170 zero-job push failures through merged
   iter237 master even though the file declares no push trigger. The local
   supply-chain guard validates YAML, action pins, runners, permissions, and
   dependency locks but not lifecycle or expression-context availability.

This is a zero-provider-spend engineering-integrity gate. It changes no
scientific numerator, label, model result, detector score, or population
inference.

## Authority and budget

Budget: `$0` external/provider spend.

Allowed:

- offline inspection and deterministic derivation from committed repository
  bytes;
- additive iter238 artifacts, registries, validators, tests, and known-bad
  fixtures;
- simplification of mutable README duplication while retaining links to sealed
  experiment records;
- synchronized changes to mutable current-state, README, paper source/PDF,
  dated handoff, validation tooling, CI, and tests;
- correcting `scripts/receipt_sealing.py` so current sealed receipts must equal
  their introducing Git blobs;
- after the registry and exact IDs are frozen, disabling only the twenty-nine
  registered historical workflow IDs through GitHub's workflow-disable API;
- read-only GitHub observations needed to bind the retirement receipt;
- local and ordinary push/pull-request CI for this engineering gate.

Forbidden:

- provider or model calls, model judgments, scientific containers, solver
  runs, scientific workflow dispatches, workflow reruns, workflow enables,
  workflow deletions, or run deletions;
- editing, renaming, relocating, or deleting the sealed iter204 workflow as
  the means of retirement;
- editing a pre-existing experiment, benchmark, sealed root handoff,
  `CONTINUITY.md`, sealed mission loop, or frozen iter200 execution driver;
- treating retrospective digests as evidence of authorship, chronology,
  independence, semantic truth, or scientific correctness;
- hiring, payment, purchase, release, paper submission, or scientific
  publication;
- merging iter238 while any acceptance bar remains failed or unevaluated.

Timeout, an unavailable reviewer, a mutable registry edit, or old green CI
never implies acceptance.

## C1 — complete current public-claim coverage

Create one canonical `mission/claim_registry.json`.

The registry must distinguish:

- internally regenerated empirical claims;
- historical empirical claims retained on mutable current surfaces;
- external-citation claims that do not regenerate locally;
- protocol parameters and worked examples;
- dates, versions, identifiers, hashes, paths, iteration numbers, and run IDs.

“Historical” is a claim category, not an exemption. Whole-file allowlisting is
forbidden.

Before coverage is frozen, the mutable README may remove duplicated
quantitative historical narration and replace it with status-plus-link
indexing. Sealed experiment results remain untouched and visible.

The declared current public surfaces are:

- `README.md`, including Mermaid labels;
- `paper/telos.tex`;
- the current dated operational handoff;
- `mission/current.json`.

Every quantitative token or written cardinal remaining in those surfaces must
resolve to either a stable registered claim projection or one typed non-claim
category. Unclassified spans fail. Every empirical claim must record:

- stable ID, revision, exact status, kind, unit, cohort, independence boundary,
  value, missingness, and excluded inferences;
- derivation mode and an argv array rather than a shell string;
- source paths, SHA-256 digests, and referenced seal IDs;
- stable source-surface bindings, never line-number authority;
- supersession links forming an acyclic chain.

Internally regenerated claims must be rebuilt offline in a credential-stripped
environment and compared with the strict typed comparator. External-citation
claims are reported separately and never counted as local regeneration.

The coverage report must retain exact surface digests and report registered
claim count, public binding count, classified non-claim count, unclassified
count, internally regenerated count, external-citation count, and superseded
claims still visible. Acceptance requires zero unclassified spans and zero
conflicting projections.

## C2 — retrospective seal registry

Create one canonical `mission/seal_registry.json`.

Its first record is explicitly a retrospective integrity capture at merged
master `7307e0c1c4083443698cfde8f0ab20a27518717c`, not a claim that all
legacy bytes were originally sealed on 2026-07-19.

At minimum it protects:

- all 9,089 blobs present below `experiments/` at the reference commit;
- the exact 23-blob `benchmarks/` tree;
- `HANDOFF.md`;
- `CONTINUITY.md`;
- `mission/loop.json`;
- `scripts/ci_iter200_execute.sh`;
- `.github/workflows/iter204-execute.yml`.

The baseline may admit additions only below the exact
`experiments/iter238_claim_seal_workflow_controls/` component path. A
lookalike prefix is not admitted. No authorization may modify, delete, rename,
chmod, replace, or add inside a pre-existing protected path.

Tree manifests use regular Git blobs ordered by UTF-8 POSIX path and hash:

`path NUL mode NUL decimal-byte-count NUL sha256(blob-bytes) LF`.

Symlinks, submodules, noncanonical paths, control characters, and ambiguous
overlaps fail. Git SHA-1 ancestry is retained, but every protected byte set
also receives an independent SHA-256 manifest.

Registry evolution is append-only across committed ancestor versions.
Corrections use new superseding records. Existing record IDs and canonical
content may not be rewritten or removed.

The validator must compare reference bytes to the index, working tree, mode,
and nonignored untracked inventory with rename detection disabled. A clean
`git diff` alone is insufficient.

After the completed iter238 evidence commit exists, a separate successor-seal
commit must append a record freezing the iter238 tree from that preceding
commit.

## C3 — sealed-receipt equality

`verify_against_source` must require:

- the current receipt bytes equal the receipt blob at the introducing commit;
- the Git entry and current path are regular files with the expected mode;
- every bound historical artifact continues to match the receipt's source Git
  blobs.

A known-bad temporary Git repository must replace a committed v2 receipt with
different, internally valid JSON. The old helper behavior would pass; the new
guard must fail specifically because the current receipt differs from its
source blob.

This repair is a guard correction. It is not evidence that any current receipt
was already corrupted.

## C4 — workflow lifecycle registry and retirement

Create `mission/workflow_registry.json` with a default-deny policy and an exact
bijection over repository workflow files.

Allowed classifications:

- `active_control`;
- `authorized_one_shot`;
- `historical_retired`;
- `platform_service`.

At this boundary:

- `.github/workflows/ci.yml` is the sole `active_control`, with exact push and
  pull-request triggers and desired server state `active`;
- there are zero `authorized_one_shot` workflows;
- the other twenty-nine repository workflows are `historical_retired`, have
  no execution authority, retain exact byte digests, and require desired state
  `disabled_manually`;
- GitHub's platform-generated `dynamic/dependabot/update-graph` workflow is an
  explicit `platform_service`, not an unregistered exception.

The offline validator must:

- parse canonical JSON with duplicate-key rejection;
- require unique paths and numeric workflow IDs;
- verify file digests, seal links, classification, exact triggers, desired
  state, and current-gate consistency;
- use GitHub-compatible YAML 1.2 boolean semantics;
- reject unregistered workflow files;
- reject `runner.*` in executable job-level `env`;
- permit the exact iter204 defect only when its unchanged bytes are classified
  historical, have no authority, and carry a retirement receipt.

A separate read-only live audit must enumerate the paginated GitHub workflow
inventory and require exact IDs, paths, and server states. It may perform GET
requests only.

The retirement mutation must:

1. capture complete pre-disable workflow objects and run-count projections;
2. disable iter204 first by its frozen numeric ID;
3. disable the remaining twenty-eight frozen historical IDs;
4. GET and verify `disabled_manually` after every request;
5. leave `ci.yml` and Dependency Graph active;
6. record exact zero counts for dispatch, rerun, enable, delete-workflow, and
   delete-run operations;
7. retain raw observation digests and state that server state is proven only
   at the observation time.

An ambiguous response is resolved by a GET. No enable request is permitted.

## C5 — current-state and CI integration

The current pointer, current handoff, README, registries, and active gate must
agree. A stale pointer to an existing predecessor hypothesis must fail; merely
checking that a path exists is insufficient.

The claim, seal, and workflow offline validators run in required CI and
therefore in the derived local closure. The live GitHub audit remains a
separate world-contact observation and must not be mislabeled deterministic
offline closure.

CI output must distinguish:

- registered command closure;
- public-claim coverage;
- retrospective protected-byte coverage;
- workflow-file lifecycle coverage;
- mutable live server-state observation.

## Acceptance bars

1. Every declared current public quantitative span is classified, with zero
   unclassified spans and zero conflicting claim projections.
2. Every internally regenerated claim exactly rebuilds; external-citation
   claims remain explicitly external.
3. All pre-iter238 protected bytes and modes match merged master; only the
   exact additive iter238 experiment path is admitted.
4. Receipt replacement, sealed-byte mutation/deletion/rename/chmod/symlink,
   old-directory addition, and lookalike-successor fixtures fail.
5. Valid additive iter238 evidence and a mutable README-only fixture pass.
6. Exactly thirty repository workflow files are registered; exactly one is an
   active continuous control; exactly twenty-nine are historical and retired.
7. All twenty-nine historical GitHub workflows are observed
   `disabled_manually`; CI and Dependency Graph remain active.
8. Iter204 retains its original bytes and zero dispatches/reruns; no new
   zero-job push failure occurs after retirement.
9. Known-bad fixtures for an unregistered paper number, conflicting
   README/paper value, removed missingness, existing-but-stale active gate,
   unregistered workflow, executable job-level `runner.temp`, and illegal
   sealed-byte change all fail for the intended reason.
10. Full local tests, lint, compile, JSON/docs/current-paper/current-state,
    supply-chain, all new validators, and the CI-derived closure pass.
11. Required remote Linux Python 3.11 and 3.12 CI pass on the exact proposed
    merge head.
12. The result reports every failure, limitation, mutation, request count, and
    remaining scientific boundary without turning engineering integrity into a
    scientific result.

## Named falsifiers

- A public number can be inserted or changed without a registry/coverage
  failure.
- Missingness can disappear from one surface while the numerator/denominator
  remains accepted.
- A pre-existing experiment or benchmark byte can change under an “additive”
  authorization.
- A valid-looking descendant receipt can differ from its introducing blob and
  still pass.
- A workflow can exist on disk or on GitHub without exact classification.
- A retired workflow remains active or creates a post-retirement push failure.
- Iter204 is repaired in place, dispatched, rerun, enabled, renamed, or
  deleted.
- A mutable GitHub observation is reported as timeless proof.
- Green engineering controls are promoted to independent semantic ground truth.

## Consequence

If this gate passes, Telos may preregister GROUND-TRUTH-1. It may not claim a
validated benchmark, detector efficacy, transfer, population rate, or
independent semantic truth.

GROUND-TRUTH-1 still requires separately admitted conflict-screened humans,
blinded consequence authorship, independent valid implementations, retained
raw rationale, and an explicitly approved budget. LLMs may be evaluated as
detectors; they may not become the ground-truth authority.
