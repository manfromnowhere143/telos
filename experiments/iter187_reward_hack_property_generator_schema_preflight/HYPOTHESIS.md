# Iteration 187 - Reward-Hack Property-Generator Schema Preflight

Status: pre-registered zero-spend property-generator schema and parser preflight; no provider calls,
credential probes, model evaluations, property-generator calls, SWE-bench executions, cloud resources,
benchmark scores, leaderboard claims, model-comparison claims, state-of-the-art claims,
natural-frequency claims, broad robustness claims, or repaired-score claims have been run for this gate.

## Why this gate exists

Iter186 is scoped to materialize leakage-scanned property-probe input packets. Before any model is asked
to generate executable checks, Telos needs a local output schema, parser, fixture suite, leakage policy,
and stop conditions for property-generator outputs. This avoids spending on malformed or unreviewable
property proposals.

## Method

Inputs:

- `experiments/iter186_reward_hack_panel_property_probe_packet_materialization/proof/property_probe_packets_v1/packets.jsonl`
- `experiments/iter186_reward_hack_panel_property_probe_packet_materialization/proof/property_probe_packets_v1/manifest.json`
- `experiments/iter186_reward_hack_panel_property_probe_packet_materialization/proof/packet_leakage_scan.json`
- `experiments/iter186_reward_hack_panel_property_probe_packet_materialization/proof/future_paid_execution_authorization.json`

Execution envelope:

- provider calls: `0`,
- credential probes: `0`,
- estimated provider spend: `$0.00`,
- property-generator calls: `0`,
- new SWE-bench executions: `0`,
- new cloud runner/resources: `0`.

## Required Outputs

- property-generator output JSON schema,
- local parser implementation or parser fixture report for valid, invalid, refusal, non-applicable, and
  malformed outputs,
- prompt-contract preflight confirming the iter186 packet payload and output schema can be combined
  without adding labels, row ids, target tests, candidate diffs, official report fields, or reference
  patches,
- future paid/execution readiness packet preserving the iter185/iter186 numeric call, spend, execution,
  false-positive, nondecision, prompt-leakage, and secret bars,
- claim-boundary audit, secret-safety audit, endpoint results, receipt, audit report, run summary, and
  learning record.

## Numeric Bars

Minimum pass bars:

- provider calls are exactly `0`,
- credential probes are exactly `0`,
- property-generator calls are exactly `0`,
- parser fixture count is at least `8`,
- valid fixture parse pass rate is `100%`,
- invalid/refusal/malformed fixture rejection rate is `100%`,
- prompt-contract leakage hits are exactly `0`,
- preserved future provider-call ceiling is at most `48`,
- preserved future spend ceiling is at most `$40.00`,
- preserved control false-positive ceiling is `0`,
- preserved nondecision ceiling is at most `4`,
- no leaderboard, model-superiority, state-of-the-art, natural-frequency, broad robustness, public
  benchmark-score, or repaired-score claim is made,
- no committed artifact contains a secret, bearer token, project ID, account ID, or service account.

## Falsifiers

1. The gate performs any provider call, credential probe, model evaluation, property-generator call,
   SWE-bench execution, or cloud resource change.
2. The output schema cannot distinguish valid, invalid, refusal, non-applicable, and malformed property
   proposals.
3. Any prompt-contract fixture leaks row ids, labels, target tests, candidate diffs, official report
   fields, reference patches, or prior panel decisions.
4. The future paid/execution readiness packet widens the iter185/iter186 numeric ceilings.
5. A committed artifact contains a secret, bearer token, service account, project ID, account ID, or
   private credential material.
6. The result presents a leaderboard, model-superiority, SOTA, natural-frequency, broad robustness,
   public benchmark-score, or repaired-score claim.

## Claim Boundary

At most, if this gate passes: Telos has a local schema/parser preflight for future property-generator
outputs over the committed iter186 packet set.

Not supported: a leaderboard ranking, state-of-the-art claim, natural reward-hacking frequency estimate,
broad reward-model robustness claim, production deployment claim, public benchmark score, repaired-score
claim, or any claim outside committed iter175-iter187 proof packets.
