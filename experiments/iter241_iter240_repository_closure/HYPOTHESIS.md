# Iter241 — iter240 repository-closure capture

Status: **preregistered, not yet captured**. This hypothesis, the exact
request plan, the safe fixture, the known-bad fixture, the capture instrument,
the offline validator, and their tests must all exist and pass local preflight
before the attempt marker is created. The marker must be durably written
before the first GitHub API request. A marker without a complete retained
receipt is a failed attempt, never authority to retry.

Predecessor: authorization merge
`6a9a4f66ec331011c9dfbe14b3a22259a5b585d5`, with parents
`39e2484cba450fe5346349921572720b0e456fb7` and
`ceb8dfbb2ba451e76c71528a8ca5fcc75f5edc31`, and tree
`76c6791ec2a051804a50f65b5297b709dea4f49c`.

Prospective authorization: seal ID
`iter241-iter240-repository-closure-authorization` permits additions only
below `experiments/iter241_iter240_repository_closure`, plus synchronized
control-plane validation. It permits no GitHub write, settings mutation,
workflow dispatch or rerun, provider or model call, scientific execution,
human contact, spending, publication, or release.

Budget: `$0.00`. Planned requests: `GET=13`, `POST=0`, `PUT=0`, `PATCH=0`,
`DELETE=0`. Retries: `0`. Redirects: `0`.

## Disclosed observations

The takeover audit inspected mutable GitHub state before this preregistration.
The following are disclosed targets for a one-shot independent recapture, not
prospective discoveries:

- pull request `88` appeared merged with sealed head
  `f954696c935ad0b733dcd613b553e1799a7b3810`, base
  `b597b763f2eb52b2f4f2d36e7daaa31654be076b`, and merge
  `39e2484cba450fe5346349921572720b0e456fb7`;
- the sealed-head push and pull-request Actions runs appeared successful, and
  the merged-master Actions run appeared successful;
- the sealed-head check set also contained non-required GitGuardian check
  `88247740246`, whose formal conclusion was `failure` and whose output title
  was `9 secrets uncovered!`;
- pull request `88` appeared to have zero reviews; and
- ruleset `19177100` appeared active with no bypass actors and with zero
  required approvals.

Successful recapture may support only a time-bounded repository-engineering
closure. It may not rewrite the GitGuardian failure as success, infer review
from a merge, or establish security approval, independent ground truth,
semantic correctness, detector efficacy, transfer, or a population result.

## Registered question

Do thirteen fixed, read-only GitHub REST responses, retained with response
headers, request identifiers, ETags where returned, dates, byte counts, and
SHA-256 digests, jointly reproduce the exact iter240 pull-request, CI, merge,
branch, and ruleset closure described by the safe fixture?

The answer is `supported` only when every raw response and every cross-response
identity passes the independently implemented offline validator. Any missing,
ambiguous, paginated, oversized, non-`200`, differently versioned, or
semantically conflicting response makes the capture `failed`.

## Exact request plan

Every request uses method `GET`, host `api.github.com`, API version
`2026-03-10`, `Accept: application/vnd.github+json`, and
`Accept-Encoding: identity`. Responses are capped at five mebibytes. The
instrument follows no redirect, performs no retry, rejects any pagination
`Link`, and publishes no partial receipt.

| Order | Name | Fixed path |
| ---: | --- | --- |
| 1 | `pull_request_88` | `/repos/manfromnowhere143/telos/pulls/88` |
| 2 | `pull_request_88_timeline` | `/repos/manfromnowhere143/telos/issues/88/timeline?per_page=100&page=1` |
| 3 | `pull_request_88_reviews` | `/repos/manfromnowhere143/telos/pulls/88/reviews?per_page=100&page=1` |
| 4 | `sealed_push_run` | `/repos/manfromnowhere143/telos/actions/runs/29707762374` |
| 5 | `sealed_pr_run` | `/repos/manfromnowhere143/telos/actions/runs/29707871077` |
| 6 | `sealed_tip_check_runs` | `/repos/manfromnowhere143/telos/commits/f954696c935ad0b733dcd613b553e1799a7b3810/check-runs?filter=all&per_page=100&page=1` |
| 7 | `gitguardian_check_run` | `/repos/manfromnowhere143/telos/check-runs/88247740246` |
| 8 | `merge_commit` | `/repos/manfromnowhere143/telos/git/commits/39e2484cba450fe5346349921572720b0e456fb7` |
| 9 | `merged_master_run` | `/repos/manfromnowhere143/telos/actions/runs/29708028160` |
| 10 | `merged_master_check_runs` | `/repos/manfromnowhere143/telos/commits/39e2484cba450fe5346349921572720b0e456fb7/check-runs?filter=all&per_page=100&page=1` |
| 11 | `master_branch` | `/repos/manfromnowhere143/telos/branches/master` |
| 12 | `ruleset` | `/repos/manfromnowhere143/telos/rulesets/19177100` |
| 13 | `effective_rules` | `/repos/manfromnowhere143/telos/rules/branches/master?per_page=100&page=1` |

The exact ordered plan and the bytes of this hypothesis, both fixtures, the
capture instrument, the offline validator, the tests, and the seal-registry
validator are hashed into the attempt marker before request one.

## Acceptance gates

### G0 — local and authorization identity

`HEAD` must be the exact authorization merge. Its parents and tree must match
the registered values. The sealed iter240 head, its parent, tree, iter240
subtree, and merge topology must regenerate locally. The iter240 sealed path
must be clean relative to the named sealed commit. The open iter241 seal
authorization must validate.

### G1 — raw capture completeness

Exactly thirteen body files and thirteen header files must be retained. Every
inventory record binds the method, path, status, selected API version,
response date, GitHub request ID, ETag or explicit absence, raw header bytes,
and raw body bytes. Request IDs must be unique. Response dates must be
nondecreasing and fall within the bounded capture window with a five-minute
clock-skew tolerance.

### G2 — pull request, merge, and reviews

Pull request `88` must be closed and merged at
`2026-07-19T23:30:24Z`, with the exact sealed head and predecessor base. The
REST `merge_commit_sha` field may be either the exact merge or `null`, because
that mutable field was observed to become null after merge. A unique timeline
merge event and the raw Git commit must independently bind merge
`39e2484cba450fe5346349921572720b0e456fb7`, its two exact parents, tree
`1a6384324dd3e2a15121d981938a0bcee397c904`, and the zero-review array.

### G3 — required CI and unresolved non-required failure

The two sealed-head Actions runs and one merged-master Actions run must be
attempt one, complete, and successful. Four app-`15368` Actions checks on the
sealed head and two on the merge must have the exact registered IDs and
`success` conclusions.

Check `88247740246` must remain app `46505`, slug `gitguardian`, conclusion
`failure`, output title `9 secrets uncovered!`, and annotation count `0`.
It is non-required by the effective rules, but it is unresolved. Therefore
`required_ci` may be `supported`, while `all_checks_green` must be
`contradicted` and `non_required_security_check` must be `failed`.

### G4 — branch and technical floor

The captured `master` branch must be protected and point to the authorization
merge at capture time. Ruleset `19177100` must be active with no bypass actors,
current-user bypass `never`, request-policy digest
`7c8db8fe1104ccd86f6cb35701d83dda35786786641cbc3f3bfa3c2211da4038`,
and effective-rules digest
`1c28e4a105d215452cfe1f718a8598fcf4036fbde642b6906b00019630ea9e68`.
The technical floor requires zero approvals; it is not review assurance.

### G5 — bounded conclusion

The only accepted conclusion is:

```text
repository_closure: supported
required_ci: supported
all_checks_green: contradicted
non_required_security_check: failed
independent_review: blocked
independent_ground_truth: blocked
scientific_authority: none
```

The retained limitation text must say that GitHub state is mutable and
time-bounded, digests do not prove truth or chronology, zero write counts cover
only this instrument, the GitGuardian failure is unresolved, zero approvals do
not provide review, and no scientific or external action is authorized.

## Known-bad requirements

The fixture suite must reject at least: a wrong pull-request head or base; a
conflicting non-null REST merge SHA; a missing merge event; a nonempty review
array; an absent or failed required Actions check; a hidden or green
GitGuardian check; merge-parent or tree drift; failed merged-master CI; master
branch drift or loss of protection; inactive ruleset, bypass actor, or policy
digest drift; fabricated all-green, independent-review, independent-ground-
truth, or scientific authority; any write verb or nonzero write count; raw
body or header hash drift; and a duplicated GitHub request ID.

## Named falsifiers

- The attempt marker is created after request one, or an attempt is retried.
- Any method other than `GET` is used, a redirect is followed, or a repository,
  settings, workflow, or review write occurs.
- A raw response, header field, request ID, ETag, date, or hash is omitted.
- Required Actions success is presented as all checks green.
- The GitGuardian failure is omitted, converted to success, or presented as a
  resolved security finding.
- A merge or zero reviews is presented as independent review.
- Mutable GitHub state, a digest, a request ID, a signature, or this agent is
  presented as semantic or scientific authority.
- A provider, model, human, target, container, GPU, spend, publication, or
  release action occurs under this gate.
- A sealed iter240 byte changes.

Any falsifier makes the affected status `failed` or `invalid`; absence never
implies success or approval.

## External-action boundary

Allowed: deterministic offline reads of tracked Telos bytes; local tests and
validation; the single fixed thirteen-GET GitHub REST observation; ordinary
branch, commit, pull-request, and governed CI publication only after separate
root review.

Forbidden in this stage: GitHub or repository-setting writes, workflow
dispatch or rerun, review fabrication, provider or model calls, scientific
execution, target execution, human contact, containers, GPUs, spending,
publication, release, visibility change, or any edit to sealed evidence.
