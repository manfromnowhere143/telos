# Iter244 — verified Python bootstrap

Status: **preregistered engineering recovery**.

Predecessor: exact Iter243 failed-evidence seal
`5fe53dadcd6ead074b5749875df267224d469eeb`. The prospective authorization is
commit `54f5bc4cb70a4c9913296f716f804145dd3bacad`, whose reference commit names
that predecessor and whose authorized path was absent there.

Budget: `$0.00`. Provider calls, model calls, scientific executions, workflow
dispatches, and workflow reruns: `0`.

## Triggering negative evidence

Iter243 failed all four required jobs before pytest collection. On push and
pull-request events, setup-python CPython 3.11.15 and 3.12.13 were regular and
owned by effective user 1001 but mode `0777`. The authenticated runner
correctly rejected both as `executable_world_writable`. This result remains a
failure and Iter244 may not weaken or reinterpret it.

## Frozen first-party assets

Iter244 uses only these actions/python-versions Ubuntu 24.04 x64 release
assets, as reported by GitHub's release API on 2026-07-22:

| Matrix | Exact version | Release tag | Asset ID | Bytes | SHA-256 |
| --- | --- | --- | ---: | ---: | --- |
| 3.11 | 3.11.15 | `3.11.15-27649667267` | 449621339 | 92521776 | `a972aa7e44f1596aa63274a9ac58dbc2349c321f3f78b1c0fc5a60d5d69a6402` |
| 3.12 | 3.12.13 | `3.12.13-27650778726` | 449635535 | 94990593 | `ce7d511228f095b5ea1ad5568543388870f5964688303f9ddc24ba06c336bfba` |

The release asset digest and the release's `hashes.sha256` entry agree for
each archive. There is no registered signature, Sigstore attestation, or
per-installed-file manifest. Archive verification therefore improves the
provenance boundary but cannot establish full runtime provenance.

## Registered question

Can Telos bootstrap each exact official Python archive from fixed HTTPS bytes,
verify its registered byte count and SHA-256 before extraction, install it in
an isolated owner-controlled tool cache, remove all group/world write before
any Python invocation, and then pass both required matrix members on normal
push and pull-request events without weakening the authenticated runner?

## Acceptance gates

1. The bootstrap maps only matrix labels `3.11` and `3.12` to the exact table
   above. Unknown labels, non-HTTPS URLs, redirects outside the frozen GitHub
   release URL, download errors, byte-count mismatch, or digest mismatch deny
   before extraction or execution.
2. The archive is extracted under a fresh mode-`0700` directory with a
   restrictive umask, without restoring archive ownership or unsafe writable
   permissions. The exact verified archive is the only source of the executed
   setup script.
3. The extracted tree is stripped of group/world write before its setup script
   executes. Installation uses a fresh owner-controlled tool-cache root rather
   than the preinstalled `/opt/hostedtoolcache` tree. The installed tree is
   stripped of group/world write and checked for residual writable paths
   before the first Python command.
4. The resolved interpreter is absolute, regular, owner-executable, owned by
   the effective user, contained inside the fresh tool-cache root, and not
   group/world writable. The existing runner and router still enforce all four
   isolation/import-path flags and reject every world-writable executable.
5. Workflow-order fixtures prove no Python or pip command precedes the verified
   bootstrap. Known-bad fixtures cover unknown labels, altered tag/asset/size/
   digest, failed verification, writable extracted/installed paths, unsafe
   output files, command reordering, and any setup-python reintroduction.
6. The workflow remains credential-minimal, uses immutable action references,
   bounded job time, hash-locked Python dependencies, fixed authenticated test
   routing, and normal push/pull-request triggers only.
7. The authenticated suite and complete CI-derived offline closure pass from
   clean committed bytes. The sealed Iter241, Iter242, and Iter243 experiment
   trees remain byte-identical.
8. One normal correction push and one pull-request event each pass Python 3.11
   and Python 3.12 on the exact candidate. No failed job is waived or relabeled.
9. The occurrence-specific GitGuardian object-ID findings remain separately
   classified; a still-red external check is reported honestly and supplies no
   general security approval.

## Falsifiers

- Any archive byte is extracted or executed before exact size and SHA-256
  verification.
- Any Python command runs before the extracted and installed trees are both
  non-group/world-writable.
- Compatibility requires accepting a world-writable interpreter, trusting a
  floating release manifest, or treating an environment label as provenance.
- The installed interpreter escapes the fresh owner-controlled tool-cache
  root, an output-command file is unsafe, or a residual writable path remains.
- Either required Python matrix member remains red after the Iter244
  correction.
- A sealed Iter241, Iter242, or Iter243 byte changes.

## Fixed conclusion boundary

Passing may support only `remote_repository_integration: supported` for the
exact corrected bytes, frozen archives, and observed GitHub runner image. It
cannot establish full runtime provenance beyond the archive boundary,
scientific truth, independent review, independent semantic ground truth,
general security, prevalence, detector efficacy, transfer, publication
readiness, or release readiness.

The operator separately authorized bounded feature-branch publication,
pull-request CI observation, exact-head correction pushes, readying, a
two-parent merge after required checks pass, and post-merge verification. No
force push, workflow dispatch or rerun, repository-setting change, provider or
model call, scientific execution, human contact, spending, paper submission,
release, deployment, or visibility change is authorized.
