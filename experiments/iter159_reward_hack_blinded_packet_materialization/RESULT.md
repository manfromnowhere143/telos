# Iteration 159 Result - Reward-Hack Blinded Packet Materialization

Status: `pass_blinded_packet_materialization`.

The zero-spend packet materialization gate passed. Telos now has 40 blinded
model-judge packets for the frozen `reward_hack_benchmark_v1` rows, with stable
packet hashes and an explicit leakage audit.

This gate ran no provider calls, no SWE-bench executions, and no cloud
resources. It does not claim a model score, leaderboard, model comparison,
state-of-the-art result, natural reward-hacking frequency, broad reward-model
robustness, or that any model has been evaluated on the packets.

## What Ran

- Materializer: `scripts/materialize_reward_hack_blinded_packets.py`.
- Frozen input: `benchmarks/reward_hack_benchmark_v1/reward_hack_benchmark_v1.jsonl`.
- Public metadata source:
  `experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/swebench_verified_rows_snapshot.json`.
- Packet output:
  - `benchmarks/reward_hack_benchmark_v1/blinded_model_judge_packets_v1/packets.jsonl`
  - `benchmarks/reward_hack_benchmark_v1/blinded_model_judge_packets_v1/schema.json`
  - `benchmarks/reward_hack_benchmark_v1/blinded_model_judge_packets_v1/manifest.json`

## Result

| bar | result |
| --- | ---: |
| packet count | `40` |
| frozen row ids matched | `pass` |
| public task text coverage | `40/40` |
| target-test coverage | `40/40` |
| stable packet hashes | `pass` |
| forbidden leakage hits | `0` |
| new provider calls | `0` |
| new SWE-bench executions | `0` |
| new cloud resources | `0` |

## Interpretation

This advances the benchmark from a scoring/provenance artifact to a prompt-safe
evaluation input. The important result is negative evidence: the model-visible
payloads contain task text, target tests, and candidate diffs, while the audit
checks that labels, official reports, report hashes, source splits, source
experiments, and known-both-miss wording are absent.

## Claim Boundary

Supported: Telos materialized blinded judge packets for the frozen
`reward_hack_benchmark_v1` artifact and audited them for
label/report/static-verdict leakage.

Not supported: model scores, leaderboard rankings, model-comparison results,
state-of-the-art claims, natural reward-hacking frequency estimates, broad
reward-model robustness claims, or any statement that a model has been evaluated
on the packets.

## Next Gate

`iter160`: validate a strict judge-output parser and fixture suite against the
blinded packet contract before any provider run.

## Evidence

- `proof/leakage_audit.json`
- `proof/endpoint_results.json`
- `proof/run_summary.json`
- `proof/learning_record.json`
- `proof/valid/receipt_reward_hack_blinded_packet_materialization.json`
