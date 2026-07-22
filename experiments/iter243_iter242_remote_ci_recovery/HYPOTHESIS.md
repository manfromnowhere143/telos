# Iter243 — Iter242 remote CI recovery

Status: **preregistered engineering recovery**.

Predecessor: exact Iter242 successor seal
`5d81a2c844483b8451505ea61ded3dec271dc14e`. The prospective authorization is
commit `e82ba37286afb1bdbcca57a51186ad39c14117fb`, whose reference commit names
that predecessor and whose authorized path was absent there.

Budget: `$0.00`. Provider calls, model calls, scientific executions, workflow
dispatches, and workflow reruns: `0`.

## Triggering negative evidence

The first authorized publication of the exact Iter242 seal exposed a remote
integration failure that the retained local Darwin/Python 3.14.2 evidence did
not cover. Push run `29893324882` and pull-request run `29893361504` both
failed before pytest collection on Ubuntu 24.04 with setup-python CPython 3.11
and 3.12. The runner denied the documented `python3 -I` invocation at its
executable-trust predicate. Compile, lint, and the hash-locked dependency
installation had passed. These failures remain negative evidence and will not
be relabeled as successful tests.

Pull request 90 also reported four non-required GitGuardian generic
high-entropy findings. The flagged values appear in Git object-identity and
evidence-digest fields. That appearance is not sufficient to dismiss them;
each exact occurrence must be classified before any false-positive
disposition.

## Registered question

Can Telos make its authenticated Python boundary compatible with the exact
GitHub-hosted setup-python executable while preserving isolated invocation,
fixed-command routing, committed-source authentication, and rejection of an
executable writable by an untrusted principal, then pass both Python matrix
members on the branch and pull request?

## Acceptance gates

1. A bounded diagnostic reports only the three isolation flags, the resolved
   executable type and permission bits, and process/file ownership identifiers;
   it reports no environment values, tokens, credentials, or file contents.
2. Python 3.11 and 3.12 both show `isolated=1`, `ignore_environment=1`, and
   `no_user_site=1`; any missing flag remains a hard denial.
3. The accepted executable remains absolute, resolves to a regular file, has
   owner-execute permission, is owned by the effective user or root, and is not
   world-writable. Group write may be accepted only for a file owned by the
   effective user, because that owner already has mutation authority over the
   same file.
4. Known-bad tests reject a foreign-owned group-writable executable, every
   world-writable executable, a non-regular executable, missing execute
   permission, and every missing isolation flag. The runner and authenticated
   router enforce the same executable policy.
5. The sealed Iter241 and Iter242 experiment subtrees remain byte-identical,
   and existing fixed-command, source/index/HEAD, plugin, environment,
   snapshot, workflow, claim, seal, and mission-loop controls remain green.
6. The authenticated suite passes with exactly the registered marker-bound
   deselections, and the complete CI-derived offline closure passes from clean
   committed bytes.
7. A correction push and pull-request event each pass both required Ubuntu
   24.04 matrix members on Python 3.11 and 3.12. No failed check is waived or
   represented as green.
8. Each GitGuardian occurrence is proven from repository bytes to be a Git
   object identifier or SHA-256 evidence digest rather than a credential
   before any occurrence is marked false positive. That narrow disposition
   supplies no general security approval.

## Falsifiers

- Any isolation flag is absent on a documented CI invocation.
- Compatibility requires accepting a world-writable executable or a
  foreign-owned group-writable executable.
- The runner and router cannot share one testable policy without weakening
  fixed-command or committed-source authentication.
- Either required Python matrix member remains red after correction.
- A flagged security value cannot be proven to be an object identifier or
  evidence digest.
- A sealed Iter241 or Iter242 byte changes.

## Fixed conclusion boundary

Passing may support only `remote_repository_integration: supported` for the
exact corrected bytes and observed GitHub runs. It cannot establish scientific
truth, independent review, independent semantic ground truth, general
security, prevalence, detector efficacy, transfer, publication readiness, or
release readiness. Iter241 remains failed and cannot be retried by this gate.

The operator separately authorized bounded branch publication, pull-request
CI observation, readying, a two-parent merge after required checks pass, and
post-merge verification. No workflow dispatch or rerun, repository-setting
change, provider or model call, scientific execution, human contact, spending,
paper submission, release, deployment, or visibility change is authorized.
