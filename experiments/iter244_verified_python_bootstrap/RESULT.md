# Iter244 — verified Python bootstrap result

Status: **failed**.

## Exact outcomes

- `preregistration_integrity: valid`
- `local_design_acceptance: failed`
- `implementation_candidate: invalid`
- `remote_repository_integration: not_run`
- `workflow_pushes: 0`
- `workflow_dispatches_or_reruns: 0`
- `iter241_retry: not_authorized`
- `scientific_authority: absent`

The preregistered asset identities were confirmed from GitHub's release API,
and both registered release tags resolve to source commit
`c2033aa6c313f068f4bde238bfaa5987ad4f2e79`. The exact tagged Linux setup
template has SHA-256
`901217d894a222bf53b1b576bb35037df703141bb368e0ab7acf52c7d659a305`.

The local implementation review found that the verified archive's setup path
would invoke Python, conditionally invoke `ensurepip`, and perform an unpinned
online forced pip upgrade before the candidate normalized and checked the
installed tree. That contradicts the registered no-Python-before-normalization
boundary and the hash-locked dependency boundary. The candidate also checked
archive member names without rejecting unsafe link targets or special member
types, and checked only the final download URL rather than every redirect hop.

These are Iter244 falsifiers. The uncommitted draft was deliberately discarded,
no Iter244 candidate was pushed, and no hosted result was requested. Local
static tests cannot substitute for the skipped bootstrap execution. The exact
design-review facts are retained in
[`proof/local_design_observation.json`](proof/local_design_observation.json).

## Fixed boundary

Iter243 remains failed remote integration evidence. Iter244 is a valid
preregistered negative engineering result, not a successful correction. Any
replacement must be a separately preregistered successor that installs the
verified archive without executing the upstream online setup path, validates
archive entry types and link targets before extraction, normalizes the final
tree before its first Python command, and proves the real bootstrap on the
hosted runner.

This result changes no scientific claim and grants no independent review,
independent semantic ground truth, general security, publication, release,
deployment, provider, model, scientific-execution, spending, or visibility
authority.
