# Iter222 — TCP-1 agent-solvable admission evidence

Status: prospective materialization gate. Recorded before any model metadata is fetched, any transparency
token is obtained, or any isolation rehearsal is run.

Predecessor merged master: `b38d8921d30ca665692afc024b4f0e3706902f78`.

## Purpose

TCP-1 admission stands at `2` passing local-design gates and `9` blocked external gates
(`experiments/iter211_tcp1_materialization_preflight/proof/admission_report.json`). Of the nine, six require
external humans, hardware, a budget, or a paid throughput run. Three do **not**: they can be filled with
independently verifiable evidence by an agent at zero spend and zero accelerator use.

This gate fills exactly those three, and no others:

1. `model_license_cutoff_and_weight_binding` — bind one license-compatible open-weight model's license,
   documented training cutoff, and exact weight and tokenizer digests, from source-linked public records,
   without downloading weights.
2. `external_transparency_timestamp` — obtain a real RFC 3161 timestamp token over the frozen commitment
   digest from a public timestamp authority, and retain a token that independently verifies.
3. `hostile_isolation_rehearsal` — run the registered five-attack rehearsal against the iter211 isolation
   contract and retain logs showing every attack denied, with positive controls proving the rehearsal
   detects a weakened contract.

It deliberately does **not** fill runtime/container/hardware binding (needs the real machine), the cohort,
hidden tests, controls, reviewers, throughput preflight, or budget. Admission moves from `2/11` to `5/11`.
`execution_authorized` stays `false`.

## Why this is not self-consistency (Standard 9)

Every bar here fails on something outside this repository:

- the model digests come from the HuggingFace API and must match what that service serves at fetch time; a
  fabricated digest fails against the live record;
- the timestamp token is signed by a third-party authority's private key and verifies only against that
  authority's certificate chain; this repository cannot mint it;
- the isolation rehearsal's positive controls require that a deliberately weakened contract lets an attack
  through — a rehearsal that passes both the real and the weakened contract is inert and fails its own bar.

A Git commit is still not a transparency timestamp, a published digest is still not proof the weights run,
and a denied rehearsal is still not a proof of runtime isolation. Those remain admission conditions, recorded
as limitations, not erased by this gate.

## Model binding

- Produce a source-linked candidate menu of at least three permissively licensed (SPDX `Apache-2.0` or
  `MIT`) open-weight instruction models, each with its HuggingFace repository, license, and a public,
  authoritative training-cutoff source.
- Freeze one default before any downstream use.
- For the default, retrieve from the HuggingFace API and commit: the resolved repository commit SHA, the
  per-file SHA-256 digest of every weight shard and of the tokenizer, and the license identifier. No weight
  bytes are downloaded; only the service's published metadata is recorded.
- Record explicitly that a published digest proves byte identity of the served artifact, not that the model
  loads, runs, or has the claimed capabilities.

## External transparency timestamp

- Freeze a commitment file listing the model binding digest, the isolation rehearsal digest, and this
  hypothesis digest.
- Obtain an RFC 3161 timestamp token over that commitment's SHA-256 from a public timestamp authority.
- Verify the token against the authority's published certificate chain and commit both the token and the
  verification transcript.
- If no authority is reachable at run time, publish a blocked result recording the attempt; do not fabricate
  a token or substitute a Git commit for it.

## Hostile isolation rehearsal

- For each of the five registered attacks — path traversal and symlink escape, environment and process-table
  disclosure, network access to grader and evidence services, artifact overwrite and receipt substitution,
  control-identity and label inference — run a deterministic reference attack against the iter211 isolation
  contract and confirm it is denied, retaining an independent log line per attack.
- Positive control per attack: run the same attack against a deliberately weakened contract and confirm the
  rehearsal reports it as **not** denied. An attack the rehearsal cannot catch under a weakened contract does
  not certify the real contract.
- The rehearsal exercises the contract's declared deny rules deterministically; it does not run the selected
  model, enter the cohort, or allocate any accelerator.

## Acceptance bars

1. At least three source-linked model candidates, one frozen default, with license, cutoff source, resolved
   commit SHA, and weight plus tokenizer SHA-256 digests retrieved from the live public record.
2. A real RFC 3161 timestamp token over the frozen commitment that verifies against its authority's chain,
   with a committed verification transcript — or a blocked result if no authority is reachable.
3. All five registered attacks denied by the real contract, and all five reported as not-denied against the
   weakened contract, with independently retained logs.
4. An updated admission view showing exactly these three gates flipped to pass, the other six still blocked,
   and `execution_authorized=false`.
5. Every generated artifact is bound by a receipt whose sealed source blobs verify.
6. No historical experiment or raw evidence byte changes.

## Falsifiers

- Any model digest, license, or cutoff is invented or does not match the live public record at fetch time.
- A timestamp token is fabricated, self-signed by this repository, or a Git commit is described as the
  external timestamp.
- The isolation rehearsal passes the real contract without also catching the attack under the weakened
  contract.
- Any admission gate beyond the three named here is described as filled.
- `execution_authorized` becomes true, or any provider call, GPU allocation, container, trajectory, workflow
  dispatch, payment, or release occurs.
- A published digest is described as proving the model runs, or a denied rehearsal as proving runtime
  isolation.
- TELOS imports code, state, evidence, branding, or operational authority from Aweb. TELOS, Sentinel, Inbar,
  and Odeya remain related projects that are separate from Aweb.

## Execution envelope

Allowed: read-only public metadata retrieval (HuggingFace API), a single RFC 3161 timestamp request to a
public authority, local deterministic isolation rehearsal, provider-free tests, and repository publication.
Forbidden: downloading model weights, any model or provider inference, any accelerator, any container build
or run, and any scientific trajectory.

## Claim boundary

A passing iter222 establishes three filled admission prerequisites — a bound model identity, an external
transparency anchor, and a rehearsed isolation contract. It establishes no model behavior, no detector
efficacy, no cohort, no throughput, no population rate, and no state of the art. It does not authorize TCP-1
execution. The scientific question remains blocked pending the six human, hardware, and budget gates.

## Publication boundary

After every local gate passes, create one receipt-bound source commit directly above merged master
`b38d892`, and one handoff-only seal commit. Run the derived CI closure, then publish the branch once and open
one draft pull request against `master`. Merge with a two-parent merge commit only after exact-tip push and
pull-request CI pass on Python 3.11 and 3.12, the secret scan is non-blocking, and no substantive review
blocker remains. Publication authorizes no TCP-1 execution or release.
