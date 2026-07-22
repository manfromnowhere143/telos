# Iter245 — offline verified Python bootstrap

Status: **preregistered engineering recovery**.

Predecessor: exact Iter244 failed-evidence seal introduced at
`7ef61b16d444ead6c828c1d5450d6e34ee8e18ac`. The prospective authorization is
commit `97adfc90628d584e3261a9f21ce6da1a4fc6e0a7`, whose reference commit names
that predecessor and whose authorized path was absent there.

Budget: `$0.00`. Provider calls, model calls, scientific executions, workflow
dispatches, and workflow reruns: `0`.

## Triggering negative evidence

Iter244 failed local design acceptance before publication. Its pinned upstream
setup path would execute downloaded Python and an unpinned online pip upgrade
before the installed tree was normalized and checked. The discarded candidate
also lacked complete archive-link and redirect-hop validation. No Iter244
candidate was pushed and there is no Iter244 hosted outcome to reinterpret.

## Frozen release assets

Only these actions/python-versions Ubuntu 24.04 x64 release assets are in
scope. GitHub's release API reported their identities on 2026-07-22, and both
release tags resolve to source commit
`c2033aa6c313f068f4bde238bfaa5987ad4f2e79`:

| Matrix | Exact version | Release tag | Asset ID | Bytes | SHA-256 |
| --- | --- | --- | ---: | ---: | --- |
| 3.11 | 3.11.15 | `3.11.15-27649667267` | 449621339 | 92521776 | `a972aa7e44f1596aa63274a9ac58dbc2349c321f3f78b1c0fc5a60d5d69a6402` |
| 3.12 | 3.12.13 | `3.12.13-27650778726` | 449635535 | 94990593 | `ce7d511228f095b5ea1ad5568543388870f5964688303f9ddc24ba06c336bfba` |

The registered digest authenticates archive bytes, not authorship, build
provenance, semantic correctness, or every installed file independently.
There is no registered signature, Sigstore attestation, or per-file upstream
manifest.

## Registered question

Can Telos replace setup-python with an exact-archive bootstrap that performs
no downloaded-code execution and no unregistered dependency resolution,
extracts through one isolated root-owned system-Python verifier, normalizes and
checks the complete extracted tree before the downloaded interpreter's first
command, and then passes each required push and pull-request matrix member
without weakening the authenticated runner's world-write denial?

## Acceptance gates

1. The shell bootstrap maps only matrix labels `3.11` and `3.12` to the exact
   asset table. It begins at the exact registered HTTPS release URL, permits at
   most one HTTPS redirect, requires the final host to be GitHub's release-asset
   host, and denies a different scheme, host, tag, filename, redirect count,
   byte count, or SHA-256 before archive parsing.
2. Before any downloaded Python command, the bootstrap resolves
   `/usr/bin/python3`, requires a regular root-owned owner-executable that is
   not group/world writable, and invokes it with isolated, safe-path, no-site,
   credential-stripped flags solely to validate and extract the verified
   archive. No environment label grants trust.
3. The archive verifier rejects duplicate or non-canonical names, absolute or
   escaping paths, control characters, excessive sizes or inventory, hard
   links, devices, FIFOs, sockets, unknown member types, absolute or escaping
   symbolic-link targets, link cycles, and links whose terminal target is not
   in the verified archive inventory. Known-bad fixtures exercise each class.
4. Extraction is manual into a fresh mode-`0700` directory. Parent components
   must remain real directories; regular files use exclusive no-follow
   creation; symbolic links are created only after every directory and regular
   file; archive owner, special-mode, group-write, and world-write bits are not
   restored. The archive's `setup.sh` is retained non-executable and never run.
5. Before the downloaded interpreter's first command, every extracted regular
   file and directory is owned by the effective user and not group/world
   writable; every symbolic link resolves inside the extraction root to a
   retained regular file or directory; and the resolved interpreter is an
   absolute contained regular owner-executable with the same ownership and
   permission properties.
6. The first downloaded-interpreter observation uses isolated and safe-path
   flags, confirms the registered exact Python version, and confirms bundled
   pip without upgrading it. Only afterward may the existing hash-locked
   requirements installation run. No bootstrap step contacts a package index
   or executes `setup.sh`, `ensurepip`, or pip installation.
7. Workflow-order fixtures prove no untrusted Python or pip command precedes
   the verified bootstrap. The workflow remains credential-minimal, uses
   immutable action references, bounded job time, the fixed authenticated test
   route, normal push/pull-request triggers only, and an exact digest binding
   for both bootstrap sources.
8. The authenticated suite and complete CI-derived offline closure pass from
   clean committed bytes. Local closure explicitly does not certify the hosted
   download/extraction path; that path must execute in every required hosted
   job.
9. One normal correction push and one pull-request event each pass Python 3.11
   and Python 3.12 on the exact candidate. No failed job is waived, rerun,
   relabeled, or replaced by a local result.
10. Sealed Iter241 through Iter244 experiment trees remain byte-identical. The
    occurrence-specific GitGuardian object-ID classification remains separate;
    a red external check is reported honestly and supplies no general security
    approval.

## Falsifiers

- Any archive byte is parsed before exact size and SHA-256 verification, or a
  download crosses more than the single registered HTTPS redirect boundary.
- The upstream setup script, ensurepip, or a pip install/upgrade runs during
  bootstrap; any downloaded Python command precedes complete tree validation.
- Any hard link, special member, unsafe path or symbolic link is admitted, any
  write follows an archive-created symlink, or an extracted path escapes the
  fresh root.
- The root-owned system verifier fails its executable or isolation checks, the
  downloaded interpreter escapes the extraction root, or any retained path is
  foreign-owned or group/world writable.
- Compatibility requires accepting the hosted world-writable interpreter,
  trusting a floating manifest, weakening the authenticated runner, or
  treating an environment label as provenance.
- Either required Python matrix member remains red after the Iter245
  correction, or a sealed predecessor byte changes.

## Fixed conclusion boundary

Passing may support only `remote_repository_integration: supported` for the
exact corrected repository bytes, frozen archives, and observed GitHub runner
image. It cannot establish complete build or runtime provenance, scientific
truth, independent review, independent semantic ground truth, general
security, prevalence, detector efficacy, transfer, publication readiness, or
release readiness.

The operator separately authorized bounded feature-branch publication,
pull-request CI observation, exact-head correction pushes, readying, a
two-parent merge after required checks pass, and post-merge verification. No
force push, workflow dispatch or rerun, repository-setting change, provider or
model call, scientific execution, human contact, spending, paper submission,
release, deployment, or visibility change is authorized.
