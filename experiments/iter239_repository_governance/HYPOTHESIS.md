# Iter239 — repository-governance enforcement gate

Status: prospective. This document is introduced in the atomic activation
commit after the registry-only authorization commit. That activation commit
also introduces the exact claim-registry migration and coverage report plus
the control-plane validation needed to make the authority transition atomic.
It precedes every governance policy, mutation driver, CI-name change, formal
live observation, GitHub setting mutation, retained governance receipt,
governance validator, governance known-bad fixture, and result.

Predecessor: merged iter238 master
`fb87af7eb15b5235a722a7bb3fd3a48962019188`, the two-parent merge of
`7307e0c1c4083443698cfde8f0ab20a27518717c` and sealed iter238 tip
`84d3593ca3e98c9a442b572e37bfc29401a61911`.

Prospective authorization: registry-only direct child
`849b1c3d0b2ddedc8f3ab0a985aca15db56c3814`, seal ID
`iter239-repository-governance-authorization`, authorizes additions only below
`experiments/iter239_repository_governance` until an exact-tree successor
seal. It does not itself authorize a GitHub mutation.

## Why this iteration exists

The two-parent merge and exact-head CI procedure is a house procedure, not an
enforced repository invariant. A preliminary read-only GitHub observation on
2026-07-19 found the public repository's default branch `master` at merged
iter238 with `protected: false`, no classic branch-protection object, no
repository rulesets, and no effective rules. Merge-commit, squash, and rebase
methods were all enabled. The only checks on merged master were GitHub Actions
checks `verify py3.11` and `verify py3.12`, both supplied by app ID `15368`;
neither was required.

The current workflow gives push and pull-request jobs the same names. GitHub
required-check contexts do not encode the triggering event separately. A
push-event success could therefore be indistinguishable from the intended
pull-request integration check if the current names were made required.

The same observation found one direct collaborator with write or
administration authority: repository owner `manfromnowhere143`. A one-approval
rule is unsatisfiable for owner-authored work at this boundary. An
administrator bypass would make the apparent review requirement nonbinding.
Setting the review count to zero is not review assurance; leaving every
orthogonal protection absent until a reviewer appears would preserve
avoidable risk.

This gate therefore installs a currently satisfiable no-bypass technical floor
within the frozen scope and reports independent review as `blocked`. It
changes no scientific label, numerator, denominator, detector result,
population inference, or ground-truth status.

## External semantics used by this design

GitHub's current ruleset documentation says that:

- a pull-request rule can require every change to be associated with an open
  pull request without requiring that pull request to be approved;
- the rule can restrict the allowed merge methods;
- required checks can be strict and can be bound to one GitHub App; and
- deletion and non-fast-forward rules block their respective ref updates.

The API contract is the GitHub REST API version `2026-03-10`. The design
references:

- `https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets`;
- `https://docs.github.com/en/rest/repos/rules?apiVersion=2026-03-10`;
- `https://docs.github.com/en/rest/about-the-rest-api/api-versions?apiVersion=2026-03-10`.

Those external pages define platform semantics; they are not Telos scientific
authority. The retained live response and effective-rule projection, not a
documentation paraphrase, determine this gate's server-state result.

## Authority and budget

Budget: `$0` external/provider spend.

Allowed:

- offline derivation from committed bytes and authenticated read-only GitHub
  GETs;
- additions within the authorized iter239 path: this hypothesis, an exact
  policy, strict validators, known-bad fixtures, before/after observations,
  one mutation intent, one request receipt, and a result;
- synchronized mutable current-state, handoff, README, registry/report,
  validation, CI, and tests required to activate and close this engineering
  gate;
- changing only the active CI job display name so push and pull-request
  contexts become event-specific; its commands, triggers, permissions,
  runners, matrix, and dependency installation remain unchanged;
- one repository-ruleset creation request, only after the exact payload,
  source commit, open pull request, check provenance, and preconditions are
  committed and every preceding gate passes;
- ordinary branch publication, pull-request creation or update, required CI,
  a two-parent merge after the satisfiable acceptance bars are green, and
  merged-master verification.

Forbidden:

- inviting a collaborator, changing a collaborator's role, inventing a
  reviewer identity, self-approval, model approval, or representing zero
  approvals as review;
- any bypass actor or bypass mode, an administrator exception, or a direct,
  force, or deletion probe against `master`;
- changing repository visibility, ownership, name, default branch,
  credentials, Actions token permissions, workflow allowlists, secrets,
  environments, releases, Pages, security products, or vulnerability
  settings;
- a classic branch-protection write in parallel with the ruleset;
- disabling a required check, accepting a check from an unspecified app,
  allowing squash or rebase at the integration boundary, requiring linear
  history, or adding a merge queue without a separately designed
  `merge_group` workflow;
- provider or model calls, scientific containers or workflows, spend,
  publication, release, or paper submission;
- editing a sealed experiment or protected historical artifact;
- merging while exact-head acceptance is failed, pending, stale, or
  unevaluated.

A timeout, ambiguous API response, missing reviewer, owner authority, old
green CI, or configuration-shaped JSON never implies acceptance.

## G0 — preregistration and exact preconditions

Introduce this hypothesis with only its exact claim-registry migration and
coverage report as the atomic iter239 activation evidence. Commit that
activation before governance implementation, formal observation, or world
mutation. Then freeze a machine-readable policy naming:

- repository `manfromnowhere143/telos`;
- default branch `master`;
- merged-master anchor
  `fb87af7eb15b5235a722a7bb3fd3a48962019188`;
- expected public visibility;
- expected zero existing repository rulesets and effective rules;
- the expected absent classic branch-protection response;
- the exact collaborator inventory and role;
- the exact event-specific check contexts and app ID;
- the fixed endpoint, API version, request method, and canonical request-body
  digest;
- a finite operation budget.

The formal mutation precondition is observed after this hypothesis is
committed. The driver must stop before POST if repository identity,
visibility, default branch, default-branch SHA, existing rules, collaborators,
check provenance, Actions controls, or merge settings differ from the frozen
policy. Drift yields `inconclusive` and zero mutation requests.

## G1 — event-specific required-check candidates

Change the CI job name exactly from:

`verify py${{ matrix.python-version }}`

to:

`verify ${{ github.event_name }} py${{ matrix.python-version }}`

The required pull-request contexts become:

- `verify pull_request py3.11`;
- `verify pull_request py3.12`.

Both must originate from GitHub Actions app or integration ID `15368`. Push
runs remain separately visible as:

- `verify push py3.11`;
- `verify push py3.12`.

Before ruleset creation, an exact current branch head must receive attempt-one
success on both push and pull-request events. A focused offline guard must
accept only the exact job-display-name substitution. It must reject name drift
and every other workflow-byte or parsed-structure change, including trigger,
permission, runner, matrix, dependency, command, step-level or job-level
condition, `continue-on-error`, and path-filtering drift that could turn a
skipped or weakened job into an accepted required check.

## G2 — strict retained before-state

Capture paginated authenticated GET evidence immediately before mutation.
Retain raw response bytes or canonical projections plus SHA-256 digests,
observation time, HTTP and API version, pagination completeness, and exact GET
count for at least:

- repository metadata and merge settings;
- the default-branch object and head;
- classic branch protection;
- repository rulesets and the exact named-rule lookup;
- effective rules for `master`;
- direct collaborators and pending invitations;
- source-head push and pull-request checks, their runs, events, attempts, and
  app identities;
- Actions enablement and allowed-actions policy;
- default workflow-token and approval permissions;
- fork-pull-request approval policy.

Strict parsing rejects duplicate JSON keys, non-finite numbers, unexpected
repository or branch identity, omitted pages, duplicate objects, ambiguous
check names, or partial errors. A branch-protection `404` is classified
`absent` only when the branch object independently says `protected: false`
and effective rules are empty. The observation proves mutable server state
only at its recorded time.

## G3 — one active no-bypass technical-floor ruleset

The only authorized mutation body is:

```json
{
  "name": "telos-default-branch-technical-floor-v1",
  "target": "branch",
  "enforcement": "active",
  "bypass_actors": [],
  "conditions": {
    "ref_name": {
      "include": [
        "~DEFAULT_BRANCH",
        "refs/heads/master"
      ],
      "exclude": []
    }
  },
  "rules": [
    {
      "type": "deletion"
    },
    {
      "type": "non_fast_forward"
    },
    {
      "type": "pull_request",
      "parameters": {
        "allowed_merge_methods": [
          "merge"
        ],
        "dismiss_stale_reviews_on_push": false,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_approving_review_count": 0,
        "required_review_thread_resolution": true
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "do_not_enforce_on_create": false,
        "required_status_checks": [
          {
            "context": "verify pull_request py3.11",
            "integration_id": 15368
          },
          {
            "context": "verify pull_request py3.12",
            "integration_id": 15368
          }
        ],
        "strict_required_status_checks_policy": true
      }
    }
  ]
}
```

The two ref selectors currently identify the same branch. Their joint purpose
is to keep the named `master` branch protected if the default changes and to
apply the technical floor to a future default branch. This does not authorize
changing the default branch.

The pull-request rule requires PR association, merge-commit mode, and
conversation resolution. Its approval count is exactly zero. It does not
establish review or independence.

No linear-history, signature, deployment, merge-queue, lock, creation-block,
update-restriction, wildcard, code-scanning, code-quality, or required-reviewer
rule may appear.

The mutation client permits GET plus one literal POST to the fixed GitHub API
origin. It must reject redirects, cross-origin URLs, non-TLS endpoints,
methods other than GET or POST, a second POST, and every PATCH, PUT, or DELETE
request. The client must persist a canonical pre-state and fsynced mutation
intent before POST.

An ambiguous POST is resolved by GET, never by retry. If exactly one active
ruleset with the exact committed policy exists, it may be classified
`ambiguous_applied`; an absent, duplicate, inactive, or mismatched object is
not success. A mismatched created object yields `failed`; this iteration may
not delete or weaken it.

## G4 — retained after-state and effective-rule evidence

After POST, capture the created ruleset by numeric ID, the complete ruleset
inventory, default-branch object, effective rules, repository metadata, and
ruleset history. Acceptance requires:

- exactly one repository ruleset with the exact name;
- exact repository source, branch target, ref condition, and active
  enforcement;
- zero bypass actors;
- the exact four-rule technical floor;
- `master` reported protected;
- effective rules that reproduce deletion, non-fast-forward,
  pull-request/merge-only, conversation-resolution, and both app-bound strict
  check requirements;
- no unrelated change in the retained compared projections; and
- exact zero unrelated requests by this driver.

Unexpected concurrent drift in a compared projection yields `inconclusive`;
the retained endpoints and driver receipt do not establish a universal
negative about all repository settings.

The receipt records exact GET and POST counts and exact zero PATCH, PUT,
DELETE, collaborator-invite, role-change, visibility, branch-update,
force-push, branch-deletion, workflow-dispatch, rerun, enable, disable,
workflow-delete, run-delete, release, and publication requests.

Server-added identifiers, timestamps, links, and normalization are represented
separately from the committed request body. They must never be silently
rewritten into the preregistration.

## G5 — fail-closed instruments and operational check

A credential-free validator must rebuild the request projection and verify the
retained policy, before-state, intent, after-state, and receipt. Known-bad
fixtures must fail for:

- nonempty bypass actors;
- evaluate or disabled enforcement;
- a wrong ref, missing selector, or wildcard;
- missing deletion or non-fast-forward;
- approval count one, or an omitted count, at this documented
  zero-review boundary;
- squash or rebase as an allowed merge method;
- a linear-history or unregistered extra rule;
- conversation resolution disabled;
- a missing, extra, or duplicate check;
- the right check name from the wrong or unspecified app;
- a push-event context substituted for a pull-request context;
- any `ci.yml` byte or parsed-structure change outside the exact job
  display-name substitution;
- stale default-branch or source-head identity;
- incomplete pagination, a duplicate JSON key, or a non-finite value;
- a second mutation request;
- an ambiguous write treated as success without exact GET reconciliation;
- prose claiming independent review.

After activation, an ordinary new commit on the iter239 pull request must
produce a retained time-bounded observation in which every non-check merge
requirement is satisfied, the exact required checks are pending, and the
check rollup makes the PR non-mergeable. Attempt-one success for both exact
app-bound checks on that same head must then be followed by a retained
transition to mergeable, subject only to GitHub's normal mergeability
recalculation. If the state stays blocked or unknown, the operational check is
not accepted. Do not probe enforcement by risking a direct, force, or deletion
update to `master`.

## G6 — closure, seal, and remote acceptance

Full local tests, lint, compile, JSON, docs, current-state, current-paper,
claim, seal, workflow, supply-chain, governance, and CI-derived closure must
pass. The result must separately state:

- `technical-control status: supported` only if G0 through G5 pass;
- `independent-review status: blocked` because no eligible independent
  write-capable reviewer exists;
- `overall governance status: blocked` until the review upgrade is both
  satisfiable and enforced.

A completed-evidence commit must contain the final result and exact retained
observations. Its direct child may append only the exact-tree iter239
successor seal. Required Linux Python 3.11 and 3.12 CI must pass on the exact
sealed tip, with no rerun substitution. Merge is then permitted only as a
two-parent merge commit whose tree equals the sealed tip. Merged-master CI and
one final read-only effective-rule observation must pass.

## Acceptance bars

1. This hypothesis is introduced no later than the atomic activation evidence
   and before every governance implementation, formal observation, and GitHub
   mutation.
2. Before-state evidence is complete, exact, and says there was no effective
   protection.
3. Push and pull-request contexts are event-distinct, attempt-one successful,
   current-head checks from GitHub Actions app ID `15368`.
4. Exactly one authorized POST occurs under exact frozen preconditions; every
   other mutation count is zero.
5. One active ruleset has no bypass actors and exposes the exact four-rule
   technical floor on both `master` and the default-branch selector.
6. Pull requests, merge-commit mode, conversation resolution, strict current
   integration checks, deletion blocking, and non-fast-forward blocking are
   effective-rule requirements.
7. Every known-bad fixture fails for its intended reason, and the exact
   retained evidence passes.
8. With all non-check merge requirements satisfied, live pull-request metadata
   and check rollup show the required-check gate fail closed while checks are
   pending and show the same head become mergeable after both required checks
   pass, without risking a direct-master mutation.
9. Local closure and exact-head Linux Python 3.11 and 3.12 CI pass; the final
   merge has two parents and a tree identical to the sealed tip; merged-master
   CI passes.
10. The result preserves the zero-approval and sole-collaborator facts and
    does not call the repository independently reviewed, scientifically
    validated, secure, tamper-proof, autonomous, state of the art, or
    production-ready.

## Named falsifiers

- An actor on the ruleset can bypass any rule.
- A direct, force, or deletion update remains permitted by the retained
  effective-rule projection.
- Either required check is absent, ambiguous, accepted from any app, stale,
  skipped through workflow control flow, or not required against the current
  base.
- `master` can receive a squash or rebase merge under the active rule.
- A pending or failed required check is reported as mergeable.
- The validator accepts a known-bad governance object or incomplete
  observation.
- The mutation executes after observed precondition drift, retries an
  ambiguous write, or sends an unregistered mutation.
- A zero-approval PR rule is described as independent review.
- A green governance control is promoted to scientific truth, detector
  efficacy, transfer, prevalence, or independent semantic ground truth.

## Consequence

If the technical floor passes, Telos gains enforced PR association, exact
app-bound pull-request CI, merge-only integration mode, conversation
resolution, and deletion and force-push resistance. The exact two-parent
topology remains a separately checked merge outcome because the merge-method
rule does not itself prove parent count.

Telos does not gain an independent reviewer, protection against the repository
owner editing or deleting the ruleset itself, authorship or chronology
guarantees, scientific authority, or a general security baseline.

The next governance recovery is triggered only after the operator supplies
and authorizes a real conflict-screened human identity who can hold
write-capable review authority. A separate preregistered mutation must then
require at least one approval, dismiss stale approvals, require approval of
the latest reviewable push by someone other than its pusher, retain
before/after evidence, and prove the rule is satisfiable without a bypass. No
agent may invite or select that reviewer autonomously.

GROUND-TRUTH-1 remains blocked on independent conflict-screened humans and
separately approved funding. Models may later be evaluated as detectors; they
may not become review or semantic-ground-truth authority.
