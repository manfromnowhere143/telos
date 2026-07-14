# Iteration 186 - Reward-Hack Panel Property-Probe Packet Materialization

Status: pre-registered zero-spend packet materialization gate; no provider calls, credential probes,
model evaluations, property-generator calls, SWE-bench executions, cloud resources, benchmark scores,
leaderboard claims, model-comparison claims, state-of-the-art claims, natural-frequency claims, broad
robustness claims, or repaired-score claims have been run for this gate.

## Why this gate exists

Iter185 is scoped to freeze the panel-missed cohort and priority property-probe design. The next useful
step is to materialize the exact paired prompt packets for that design before authorizing any paid
property generator or execution-backed evaluator. This keeps selection, leakage checks, and stop bars
auditable before a model sees any row.

## Method

Inputs:

- `experiments/iter185_reward_hack_panel_miss_property_probe_design/proof/priority_property_probe_design_subset.json`
- `experiments/iter185_reward_hack_panel_miss_property_probe_design/proof/property_probe_leakage_policy.json`
- `experiments/iter185_reward_hack_panel_miss_property_probe_design/proof/future_execution_property_generator_budget.json`
- `benchmarks/reward_hack_benchmark_v1/blinded_model_judge_packets_v1/packets.jsonl`
- `benchmarks/reward_hack_benchmark_v1/legitimate_controls_v1/blinded_control_packets_v1/packets.jsonl`
- `benchmarks/reward_hack_benchmark_v1/reward_hack_benchmark_v1.jsonl`
- `benchmarks/reward_hack_benchmark_v1/legitimate_controls_v1/legitimate_controls_v1.jsonl`

Execution envelope:

- provider calls: `0`,
- credential probes: `0`,
- estimated provider spend: `$0.00`,
- property-generator calls: `0`,
- new SWE-bench executions: `0`,
- new cloud runner/resources: `0`.

## Required Outputs

- exactly `12` hack property-probe packets selected from the iter185 priority subset,
- exactly `12` paired legitimate-control property-probe packets,
- packet manifest with packet hashes and source row traceability,
- leakage scan proving no gold patches, hidden test names, official expected outputs, packet labels,
  paired labels, panel votes, or iter179 disagreement classes leak into the generated prompts,
- future paid/execution authorization packet that preserves the iter185 numeric call, spend, execution,
  false-positive, nondecision, prompt-leakage, and secret bars,
- claim-boundary audit, secret-safety audit, endpoint results, receipt, audit report, run summary, and
  learning record.

## Numeric Bars

Minimum pass bars:

- provider calls are exactly `0`,
- credential probes are exactly `0`,
- property-generator calls are exactly `0`,
- selected hack packet count is exactly `12`,
- paired legitimate-control packet count is exactly `12`,
- total property-probe packet count is exactly `24`,
- all `12` hack packet source row ids exactly match the iter185 priority subset,
- all `12` control packet source rows are paired to those hack row ids,
- packet-hash count is exactly `24` and all packet hashes are unique,
- leakage hits are exactly `0`,
- future paid/execution gate remains unauthorized unless the numeric bars from iter185 are preserved,
- no leaderboard, model-superiority, state-of-the-art, natural-frequency, broad robustness, public
  benchmark-score, or repaired-score claim is made,
- no committed artifact contains a secret, bearer token, project ID, account ID, or service account.

## Falsifiers

1. The gate performs any provider call, credential probe, model evaluation, property-generator call,
   SWE-bench execution, or cloud resource change.
2. The materialized packet counts are not exactly `12` hack, `12` control, and `24` total packets.
3. A generated packet contains a row label, paired label, panel vote, disagreement class, gold patch,
   hidden test name, official expected output, or official report field.
4. A control packet is not paired to one of the selected iter185 hack row ids.
5. The future paid/execution authorization omits numeric call, spend, execution, false-positive,
   nondecision, prompt-leakage, or secret bars.
6. A committed artifact contains a secret, bearer token, service account, project ID, account ID, or
   private credential material.
7. The result presents a leaderboard, model-superiority, SOTA, natural-frequency, broad robustness,
   public benchmark-score, or repaired-score claim.

## Claim Boundary

At most, if this gate passes: Telos has materialized a zero-spend, leakage-scanned 24-packet
property-probe input set for a future execution/property-generator experiment over the committed iter185
priority subset.

Not supported: a leaderboard ranking, state-of-the-art claim, natural reward-hacking frequency estimate,
broad reward-model robustness claim, production deployment claim, public benchmark score, repaired-score
claim, or any claim outside committed iter175-iter186 proof packets.
