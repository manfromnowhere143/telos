# Iter241 result correction — iter240 repository-closure attempt

Status: **failed**. The one-shot capture attempt completed, but it did not
satisfy the preregistered response-completeness contract for independent
reasons: a required JSON member was omitted, and exact response header-section
bytes were never retained. Capture completeness, raw-header-byte fidelity, and
repository closure are therefore `failed`, and iter241 has no retry authority.

This is an additive architecture-and-evidence correction. Every marker-bound
instrument, the armed attempt marker, all retained response artifacts, the
original receipt, and the pre-arm record remain byte-identical. No GitHub,
provider, model, scientific, publication, spending, or other external action
was taken during the correction.

## Corrected status vector

```text
attempt: failed
capture_completeness: failed
repository_closure: failed
raw_header_byte_fidelity: failed
frozen_validator_acceptance: invalid
required_ci: supported
all_checks_green: contradicted
non_required_security_check: failed
independent_review: blocked
independent_ground_truth: blocked
scientific_authority: none
retry_authority: none
```

Positive component observations remain visible, but they cannot repair the
failed conjunction. Required Actions success does not erase the retained
GitGuardian failure, and neither a merge nor an empty review array supplies
independent review.

## Independent completeness falsifiers

### Omitted pull-request member

The retained body
[`proof/raw/iter240_repository_closure/pull_request_88.json`](proof/raw/iter240_repository_closure/pull_request_88.json)
does not contain a `merge_commit_sha` member. Omission is not explicit JSON
`null`.

The frozen validator constructed `rest_merge_commit_sha` with
`pull.get("merge_commit_sha")`. Python's `dict.get` returns `None` for both an
omitted member and a member whose value is explicit null. The frozen
projection therefore converted the omission into a null-valued field and
accepted it under the safe fixture. The original receipt's null projection is
not evidence that the raw response contained an explicit null member.

The hypothesis required every response field needed by the registered
contract to be present and named an omitted response field as a falsifier.
Consequently the attempt and repository closure are failed. The original
frozen-validator pass is preserved as historical execution evidence but is
invalid as closure authority.

### Unretained raw response-header bytes

The preregistered G1 contract required every inventory record to bind raw
header bytes. Parsed and reserialized substitutes do not satisfy that byte-
fidelity requirement. The frozen capture did not retain the HTTP response
header-section bytes. It called `http.client.HTTPResponse.getheaders()`,
converted the parsed name/value pairs into a JSON object, and encoded that
object with canonical JSON.

Those files preserve useful returned header pairs, ordering, duplicate pairs,
selected values, and the canonical JSON bytes that were written. They do not
preserve the exact wire/header-section bytes, including their original byte
serialization, and the lost representation cannot be reconstructed from the
parsed pairs. The historical `raw_headers_*` field and filename labels do not
change the retained representation.

Consequently `raw_header_byte_fidelity` and `capture_completeness` are
`failed`, independently of the omitted `merge_commit_sha` member. The original
projection's `raw_header_hashes_match: true` means only that the canonicalized
JSON document hashes matched; it is invalid as raw-header-byte authority.

## Common-mode correction

The capture producer called the frozen validator's `document_projection`, and
that function seeded its result from a deep copy of the safe fixture. The
producer and validator therefore shared the exact projection logic at the
decisive boundary. Prior wording that called this an independent projection or
independent validation is retracted.

The additive adjudicator
[`../../scripts/adjudicate_iter241_repository_closure_correction.py`](../../scripts/adjudicate_iter241_repository_closure_correction.py)
does not import the frozen validator. It binds the hypothesis, attempt marker,
original receipt, pre-arm record, all marker-bound instruments, and all
twenty-six retained response artifacts. It tests object-member presence
separately from value and deterministically distinguishes omitted, explicit-
null, exact-SHA, and conflicting-SHA cases. It also distinguishes exact raw
header-section bytes from parsed and canonically reserialized header pairs.

The correction receipt is
[`proof/iter240_repository_closure_correction.json`](proof/iter240_repository_closure_correction.json),
SHA-256
`854523c490ee0eb9807b4ed3da52677edffd148e754bd233ea2cdc09a12231c4`.
It records the conversational defect report only as a trigger for
reinspection, not as independent review or attestation.

## Preserved component observations

The following retained observations still validate against exact source
bytes:

- thirteen JSON response bodies totaling `134661` bytes;
- thirteen canonicalized documents of returned header name/value pairs
  totaling `34439` bytes;
- thirteen distinct GitHub request IDs and nondecreasing response dates;
- an empty PR-review array;
- the exact PR timeline merge and raw Git merge topology;
- the protected branch and active ruleset observation;
- three successful attempt-one Actions runs and the registered required check
  set; and
- GitGuardian check `88247740246`, completed with formal conclusion `failure`,
  title `9 secrets uncovered!`, and zero annotations.

The header artifacts are thirteen canonicalized JSON documents of returned
header pairs totaling `34439` bytes. They are not raw HTTP wire bytes or exact
header-section bytes, and prior wording that described them as raw header bytes
is corrected. Their bounded pair-level observations remain useful, but they do
not repair raw-header-byte fidelity or capture completeness.

These observations support `required_ci: supported` and the named topology and
ruleset component observations. They also require
`all_checks_green: contradicted` and
`non_required_security_check: failed`. They do not satisfy the registered
repository-closure conjunction after the response-member omission.
They likewise cannot repair the independent raw-header-byte falsifier.

## Frozen evidence and retry boundary

The exclusive attempt marker remains armed. Its rule that any marker forbids a
retry still applies. No second GET attempt is authorized by this correction,
and a timeout, missing field, unavailable reviewer, or validator defect never
creates retry or approval authority.

The original result receipt remains retained at
[`proof/iter240_repository_closure.json`](proof/iter240_repository_closure.json),
SHA-256
`b37b19a288445311ae4a7ba04313b87646c79240adf156e345ddc75cbefab874`.
It is not rewritten. Its supported closure projection is superseded by the
additive correction receipt for current interpretation.

## Reproduction

```bash
python3 scripts/adjudicate_iter241_repository_closure_correction.py
pytest -q tests/test_iter241_repository_closure_correction.py
ruff check scripts/validate_iter240_repository_closure.py
```

The last command passes only through the exact one-file, one-rule `F401`
per-file exception required to preserve the marker-bound validator unchanged.
The exception is pinned by a meta-test.

## Scientific boundary

The failed capture-completeness and repository-closure attempt changes no
scientific result. Fresh-
cohort concentration remains inconclusive, fix-size transfer remains untested,
and independent semantic ground truth remains blocked. No security approval,
independent review, detector efficacy, population result, state-of-the-art
claim, publication, or release is earned.
