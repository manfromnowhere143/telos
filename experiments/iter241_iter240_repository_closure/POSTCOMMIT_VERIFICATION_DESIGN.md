# Additive postcommit verification design

Status: `reviewed for local engineering closure` on 2026-07-21. The operator
directed recovery of the interrupted local successor work. This document is
not self-authorizing and grants no push, pull request, merge, workflow,
settings, provider, scientific, publication, spending, or release action.

This design routes future verification through a validated successor seal,
not through ancestry alone. It preserves the failed one-shot attempt and its
additive correction. It cannot convert the attempt or repository closure to
supported, and it cannot authorize an iter241 retry.

## Frozen capture-time evidence

The capture ran only from authorization HEAD
`6a9a4f66ec331011c9dfbe14b3a22259a5b585d5`. Its armed marker freezes the
hypothesis, both original fixtures, capture instrument, frozen validator,
seal-registry validator, and original test file. The marker, all twenty-six
response artifacts, original receipt, and pre-arm record are also immutable.

The frozen validator's exact-HEAD check and historical pass remain evidence of
what executed. They are invalid as closure authority because its `dict.get`
projection conflated an omitted `merge_commit_sha` member with explicit null,
and the capture producer called the same projection. Independently, the
capture passed `http.client.HTTPResponse.getheaders()` through canonical JSON,
so it retained thirteen canonicalized returned header-pair documents totaling
34,439 bytes, not the required exact response header-section bytes. Those wire
bytes were never retained and are not reconstructible from the documents.

The additive correction adjudicator is the current retained interpretation
guard. It must run on every later head and must continue to classify:

```text
attempt: failed
capture_completeness: failed
raw_header_byte_fidelity: failed
repository_closure: failed
frozen_validator_acceptance: invalid
required_ci: supported
all_checks_green: contradicted
non_required_security_check: failed
independent_review: blocked
independent_ground_truth: blocked
scientific_authority: none
retry_authority: none
```

## Seal-qualified successor routing

A future router must default deny. `git merge-base --is-ancestor` is necessary
topology evidence but is never sufficient routing authority.

The runner and every authority-bearing source must be regular committed bytes
that agree exactly across the worktree, Git index, and `HEAD` before the router
is executed. A worktree-only hash is insufficient because a locally replaced
runner and router could otherwise agree with each other while differing from
the candidate commit being qualified.

Routing may change only on a head that contains a seal-registry record which:

1. has record type `successor_path_snapshot` and names
   `iter241-iter240-repository-closure-authorization` as its predecessor;
2. names an exact reference commit and an exact-tree protected set for
   `experiments/iter241_iter240_repository_closure`;
3. passes the full seal-registry validator, including predecessor lifecycle,
   reference topology, path manifest, blob count, and exact protected bytes;
4. is reachable from the current head, while the current iter241 subtree is
   byte-identical to the sealed reference subtree; and
5. retains both independent completeness falsifiers, the failed closure, and
   the no-retry vector verbatim.

A descendant without that valid seal is unqualified. A valid ancestor with a
changed iter241 subtree is also unqualified. Missing, ambiguous, open, or
malformed seal state fails closed.

The separately authorized router should independently recheck the
authorization commit's tree and parents, the sealed iter240 commit and subtree,
the governed iter240 merge, the successor-seal reference commit, and the
current exact iter241 subtree. It must perform no GitHub request or write.

## Pytest routing

The two frozen capture-time assertions below require the authorization HEAD
and will correctly fail on a later commit:

- `tests/test_iter240_repository_closure.py::test_local_authorization_and_sealed_iter240_bytes`
- `tests/test_iter240_repository_closure.py::test_retained_capture_validates_when_present`

Only those exact node IDs may be skipped, and only after the seal-qualified
predicate above passes. Ancestry alone must not trigger a skip. A meta-test
must pin the two-node allowlist and reject an unsealed descendant, a wrong
predecessor seal, a stale manifest, a changed subtree, a missing reference,
and a non-descendant.

Every correction test and the remaining frozen tests must still run. The
frozen validator may be exercised to demonstrate its historical behavior, but
its pass must never be routed into current closure acceptance.

Pytest plugin autoload, environment-selected plugins, every repository
`conftest.py`, and any tracked test module declaring `pytest_plugins` must be
denied before collection. A known-bad tracked plugin fixture must demonstrate
that the guard fires; ignoring only untracked plugin files is insufficient.

## Exact lint treatment

The frozen validator contains one unused `os` import. Editing it would change a
marker-bound hash. `pyproject.toml` therefore contains one per-file ignore:
only `F401`, only for
`scripts/validate_iter240_repository_closure.py`. A meta-test requires the
per-file-ignore mapping to contain exactly that one file and one rule and also
pins the frozen validator digest. A directory exclusion or global `F401`
suppression is forbidden.

## Experiment-index finalization

The experiment-index generator intentionally recognizes retained artifacts
from committed Git bytes. At correction checkpoint `aef4892`, `HEAD` and the
Git index retain the complete failed interpretation while the mechanically
regenerated worktree index is the sole expected index delta. The reviewed
control checkpoint must commit that exact generated index together with the
final runner, router, tests, and this design. Afterward, the index may list the
hypothesis and corrected result only while committed `HEAD`, index, and
worktree bytes agree. An old supported `RESULT.md`, receipt, claim artifact,
or registry is never an acceptable staging source.

The workflow-registry tests likewise compare committed bytes. Precommit
staged-versus-HEAD failures are not authority for a broad test exclusion.

## Acceptance boundary

Postcommit verification is acceptable only when the correction adjudicator,
seal registry, claim registry, workflow registry, current-state guard,
experiment index, exact lint meta-test, focused tests, and authenticated full
offline suite all pass from clean candidate bytes. Every current mandatory
test entrypoint must invoke the authenticated runner rather than bare pytest.
A green postcommit run supports only the integrity of the retained failed-
attempt correction. It does not repair capture completeness, raw-header-byte
fidelity, or repository closure; provide security approval or independent
review; authorize a retry; or create scientific authority.
