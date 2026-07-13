# Iteration 163 - Reward-Hack Legitimate-Control Materialization

Status: pre-registered materialization gate; no provider calls, model evaluations, SWE-bench executions,
cloud resources, precision claims, leaderboard claims, or benchmark scores have been run for this gate.

## Why this gate exists

`iter161` exposed a `3/40` single-model recall result on all-positive reward-hack packets. `iter162`
designed the legitimate-control source hierarchy, schemas, packet contract, and metric boundary needed
before precision can mean anything. The next step is to recover and materialize legitimate-control rows and
blinded control packets under that design.

## Method

Inputs:

- `experiments/iter162_reward_hack_legitimate_control_design/proof/control_source_hierarchy.json`
- `experiments/iter162_reward_hack_legitimate_control_design/proof/legitimate_control_row_schema.json`
- `experiments/iter162_reward_hack_legitimate_control_design/proof/blinded_control_packet_schema.json`
- `experiments/iter162_reward_hack_legitimate_control_design/proof/metric_protocol.json`
- `benchmarks/reward_hack_benchmark_v1/reward_hack_benchmark_v1.jsonl`
- public SWE-bench Verified metadata and public gold/accepted patch sources only when source and hash can be
  recorded

Planned output:

- `benchmarks/reward_hack_benchmark_v1/legitimate_controls_v1/legitimate_controls_v1.jsonl`
- `benchmarks/reward_hack_benchmark_v1/legitimate_controls_v1/schema.json`
- `benchmarks/reward_hack_benchmark_v1/legitimate_controls_v1/manifest.json`
- `benchmarks/reward_hack_benchmark_v1/legitimate_controls_v1/blinded_control_packets_v1/packets.jsonl`
- packet schema, packet manifest, leakage audit, source audit, run summary, receipt, and learning record

## Numeric Bars

Pass bars:

- materialize exactly `40` legitimate-control rows if recoverable from public/committed sources;
- publish a null/shortfall result, not a pass, if at least `20` but fewer than `40` controls are
  materialized;
- fail the materialization gate if fewer than `20` controls can be source/hash verified;
- every row has a stable candidate diff hash, source record hash, public task text, public target-test list,
  source artifact/path or public URL, execution/report evidence path or public hash, and claim boundary;
- paired and disjoint control strata are reported separately;
- control candidate diff hashes have `0` overlap with reward-hack candidate diff hashes;
- prompt-visible control packet fields match the iter159 model-judge packet surface exactly;
- prompt leakage audit reports `0` label, `gold`, `control`, source split, source experiment, official-report,
  prior-verdict, or static-outcome hits;
- no provider calls, no model evaluations, no new SWE-bench executions, no cloud resources, and no precision
  or leaderboard claims occur in this gate.

## Falsifiers

1. A control row is included without a recoverable candidate diff and stable hash.
2. A control packet exposes a label, gold/control status, source experiment, official report content, prior
   verdict, or static outcome in prompt-visible fields.
3. A hack diff is duplicated as a control diff.
4. Outcome-only metadata from prior controls is treated as a packet without recovering the actual diff.
5. Fewer than `20` controls can be source/hash verified.
6. Any model is evaluated on controls before this materialization result is published.

## Claim Boundary

At most, if the gate passes: Telos has a hash-checked legitimate-control artifact and blinded control
packets ready for a future precision/false-positive model-judge run.

Not supported: a model score, precision number, leaderboard, model comparison, state-of-the-art claim,
natural reward-hacking frequency estimate, broad reward-model robustness claim, or claim that any model has
been evaluated on the controls.
