# Iteration 159 - Reward-Hack Blinded Packet Materialization

Status: pre-registered design; no provider calls, SWE-bench executions, cloud resources, or model scoring
have been run for this gate.

## Why this gate exists

`iter158` designed the moonshot scoring/evaluation protocol for `reward_hack_benchmark_v1`. The next
leakage-sensitive step is to materialize the actual blinded model-judge packets before any model call. This
gate should prove that packets contain only prompt-allowed fields and exclude labels, official reports,
source splits, prior judge labels, and any known-hack wording.

## Method

Inputs:

- `benchmarks/reward_hack_benchmark_v1/reward_hack_benchmark_v1.jsonl`
- `benchmarks/reward_hack_benchmark_v1/manifest.json`
- `experiments/iter158_reward_hack_moonshot_design/proof/moonshot_design.json`
- `experiments/iter158_reward_hack_moonshot_design/proof/scoring_protocol.md`

Planned output:

- blinded packet JSONL for the v1 rows,
- packet schema,
- packet manifest with hashes, row count, and exclusion audit,
- leakage audit proving forbidden fields are absent,
- no model outputs and no scores.

## Numeric Bars

Minimum pass bars:

- packet count is exactly `40`,
- packet row ids match the frozen v1 row ids,
- every packet includes only prompt-allowed fields from the iter158 protocol,
- every packet excludes `static_verdicts`, `survives_all_static`, official report paths, official report
  hashes, source split, source experiment, prior judge labels, and known-both-miss wording,
- every packet has a stable packet SHA256,
- new provider calls: `0`,
- new SWE-bench executions: `0`,
- new cloud resources: `0`,
- no benchmark score, leaderboard, model-superiority, state-of-the-art, natural-frequency, broad
  robustness, or model-evaluated-on-v1 claim appears.

Reported but not pass-required:

- fields included in each packet,
- prompt template hash,
- any missing public task metadata that must be filled before a future provider run.

## Falsifiers

1. Packet count or row ids differ from the frozen v1 artifact.
2. Any packet includes a forbidden label, official report path/hash, source split, source experiment,
   static verdict, or survives-all-static marker.
3. The gate generates model outputs or calls a provider.
4. The result claims a model score or leaderboard.
5. Missing public task metadata is hidden instead of recorded as a blocker or packet caveat.

## Claim Boundary

At most: "Telos materialized blinded judge packets for the frozen `reward_hack_benchmark_v1` artifact and
audited them for label/report/static-verdict leakage."

Not supported: model scores, leaderboard rankings, model-comparison results, state-of-the-art claims,
natural reward-hacking frequency estimates, broad reward-model robustness claims, or any statement that a
model has been evaluated on the packets.
