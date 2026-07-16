# Iter222 result — TCP-1 agent-solvable admission evidence

Status: PASS. Three admission gates filled with independently verifiable evidence at zero spend. TCP-1
scientific execution remains BLOCKED.

## Result

TCP-1 admission moves from `2/11` to **5/11** passing gates. The three newly filled gates are exactly those
an agent can fill without external humans, hardware, a budget, or any model inference, and each is backed by
evidence that fails if fabricated:

| Gate | Evidence | World-contact check |
| --- | --- | --- |
| `model_license_cutoff_and_weight_binding` | `proof/model_binding.json` | live HuggingFace digests; a wrong digest fails against the service |
| `external_transparency_timestamp` | `proof/transparency_timestamp.json` + `timestamp_token.tsr` | RFC 3161 token signed by a third-party authority; re-verifies offline against its chain |
| `hostile_isolation_rehearsal` | `proof/isolation_rehearsal.json` | five attacks denied, five positive controls fire on a weakened contract |

The remaining `6` gates stay blocked and `execution_authorized` stays `false`.

## Model binding

The default model is `Qwen/Qwen2.5-7B-Instruct` (SPDX `Apache-2.0`), resolved at commit
`a09a35458c702b33eeacc393d103063234e8bc28`, with the SHA-256 of all four `safetensors` weight shards and the
tokenizer retrieved live from the HuggingFace API. Two further permissively licensed candidates
(`Mistral-7B-Instruct-v0.3`, `Llama-3.1-8B-Instruct`) are recorded in the menu, the last flagged as a
community-license, menu-only option. No weight bytes were downloaded.

A published digest proves byte identity of the served artifact. It does not prove the model loads, runs, or
has any capability, and it is not a training-provenance or license-compliance proof. Those remain open
conditions, not claims this gate makes.

## External transparency timestamp

A commitment binding the model-binding digest, the isolation-rehearsal digest, and the sealed hypothesis
digest was timestamped by `freetsa.org` under RFC 3161. The token verifies against the authority's published
certificate chain, re-verifies offline from the committed token and chain, and carries the authority's stated
time. This is an external anchor independent of this repository's Git history: a Git commit is not a
transparency timestamp, and this repository cannot mint the authority's signature. The token attests
existence-at-time, not authorship or semantic truth.

## Hostile isolation rehearsal

Each of the five registered attacks — path traversal and symlink escape, environment and process-table
disclosure, network access to grader and evidence services, artifact overwrite and receipt substitution,
control-identity and label inference — is denied by the iter211 isolation contract. For each, a positive
control removes the corresponding deny rule and confirms the rehearsal then reports the attack as **not**
denied. A rehearsal that could not catch the attack under a weakened contract would be inert; all five
controls fire.

This rehearses the declared contract policy, not a live sandbox. A denied attack proves the registered
attacks are covered by the contract's deny rules. It does not prove runtime isolation of a real agent
process, which requires the still-unbound runtime, container, and hardware and remains a separate admission
gate.

## Bars

| Bar | Requirement | Observed | Verdict |
| --- | --- | --- | --- |
| 1 | ≥3 source-linked candidates, one default with live license/cutoff/commit/weight+tokenizer digests | 3 candidates, Qwen2.5-7B-Instruct default, 4 weight shards | pass |
| 2 | Real RFC 3161 token verifying against its chain, with transcript | verified, re-verifies offline | pass |
| 3 | Five attacks denied by real contract; five not-denied under weakened contract | 5/5 denied, 5/5 controls fire | pass |
| 4 | Admission view shows exactly these three flipped, six blocked, execution unauthorized | 5 pass / 6 blocked / false | pass |
| 5 | Every artifact bound by a receipt whose sealed source blobs verify | verified | pass |
| 6 | No historical experiment or raw evidence byte changes | verified | pass |

## Claim boundary

Iter222 fills three admission prerequisites: a bound model identity, an external transparency anchor, and a
rehearsed isolation contract. It establishes no model behavior, no detector efficacy, no cohort, no
throughput, no population rate, and no state of the art. It does not authorize TCP-1 execution.

The six remaining blockers require external humans (five conflict-screened reviewers, two task authors, two
hidden-test authors), the real runtime, container, and hardware, a paid one-task throughput preflight, and an
approved monetary budget. None of those is an agent-solvable gate, and none is claimed here.

## Zero-action boundary

`0` model or provider inference calls, `0` GPU allocations, `0` accelerator-hours, `0` scientific containers,
`0` repository test executions, `0` trajectories, `0` workflow dispatches, `0` payments, `0` releases, and
`$0.00` spent. The only network actions were read-only HuggingFace metadata retrieval and a single RFC 3161
timestamp request to a public authority. No weight bytes were downloaded.

## Reproduction

```bash
python3 scripts/build_iter222_model_binding.py --check
python3 scripts/run_iter222_isolation_rehearsal.py --check
python3 scripts/build_iter222_transparency_timestamp.py --check
python3 scripts/build_iter222_admission_view.py --check
python3 scripts/validate_iter222_tcp1_agent_solvable_admission_evidence.py
python3 scripts/build_iter222_receipt.py --check
```

## Next gate

The six remaining gates are not agent-solvable and are the substance of the unchanged, inactive
`experiments/iter212_tcp1_independent_cohort_and_custody_freeze/HYPOTHESIS.md`. They require operator action:
recruiting and conflict-screening five reviewers, independent task and hidden-test authoring, binding the
real runtime and hardware, and approving a monetary budget. No autonomous gate can fill them.
