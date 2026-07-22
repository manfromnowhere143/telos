# Iter245 — offline verified Python bootstrap result

Status: **supported** for bounded repository integration.

## Exact outcomes

- `preregistration_integrity: valid`
- `remote_repository_integration: supported`
- `push_required_jobs: 2/2 passed`
- `pull_request_required_jobs: 2/2 passed`
- `hosted_bootstrap_observations: 4/4 passed`
- `final_sealed_head_checks: not_run`
- `merged_master_verification: not_run`
- `iter241_retry: not_authorized`
- `scientific_authority: absent`

The exact candidate was
`de22688f800e0fb46c15ecd851d2bf76e26b0a82`, with tree
`416c864123bd7451d250bcd6384c41d1670343a5`. Post-reboot local validation
passed 1,589 authenticated tests with exactly two seal-qualified deselections,
and all 293 CI-declared offline commands passed. That local Darwin/Python
3.14.2 evidence did not certify hosted Linux.

Normal push run `29920504274` and pull-request run `29920506702` both
completed successfully on attempt 1. Python 3.11.15 and 3.12.13 each passed on
both events using Ubuntu 24.04 image `20260714.240.1`, provisioner
`20260707.563`, and runner `2.336.0`.

Each hosted job authenticated its exact registered archive before parsing,
retained the exact registered byte count and SHA-256, rejected group/world
write in the extracted tree, did not run the upstream setup path, and observed
the downloaded interpreter only after containment and native-loader checks.
The first-Python observations reported isolated, ignore-environment,
no-user-site, and safe-path controls; contained prefixes, pip, and libpython;
and the later authenticated test route accepted an absolute regular
owner-executable mode-`0700` interpreter.

GitHub's pull-request synthetic merge was
`29b5b29981c684032151ef8d6d78a88d5bb77389`. Its ordered parents were live
`master` `6a9a4f66ec331011c9dfbe14b3a22259a5b585d5` followed by the exact candidate,
and its tree was byte-identical to the candidate tree.

The bounded machine-readable observation is retained in
[`proof/remote_ci_observation.json`](proof/remote_ci_observation.json). It binds
the exact run, job, runner, archive, bootstrap, trust, and synthetic-merge
identities without retaining unrestricted logs, environment values, temporary
paths, or credentials.

## Capture-contract limitation

The Iter245 hypothesis prospectively fixed the required evidence categories
and decision rule, but it did not freeze an exact hosted-result JSON schema or
semantic validator before the first push. The additive validator and known-bad
fixtures introduced with this result can check internal consistency and the
frozen gate identities; they are retrospective same-operator engineering
checks, not independent attestation or proof of command execution by
themselves. The GitHub run and job records remain the external observation
source.

## External security check

GitGuardian remained red for the already retained occurrences of Git commit
`6a9a4f66ec331011c9dfbe14b3a22259a5b585d5` and its Git tree
`76c6791ec2a051804a50f65b5297b709dea4f49c`. Exact Git-object classification
supports an occurrence-specific false-positive disposition, not a general
security approval. The external check is not one of the two strict required
pull-request checks and was not waived, rerun, or hidden.

## Fixed boundary

This result supports repository integration only for the exact candidate,
registered archives, observed runner image, and bounded bootstrap route. It
does not establish complete platform or transitive runtime provenance,
independent review, independent semantic ground truth, general security,
scientific truth, prevalence, detector efficacy, transfer, publication
readiness, or release readiness.

Iter241 remains failed. Iter242 remains supported local engineering evidence.
Iter243 and Iter244 remain failed engineering evidence. No provider or model
call, scientific execution, human contact, spending, paper submission,
publication, release, deployment, visibility change, or scientific authority
is granted.

The result must now be indexed, synchronized across the mutable current
surfaces, and sealed. Only the resulting exact sealed head may undergo fresh
normal push and pull-request checks before any ready or merge decision.
