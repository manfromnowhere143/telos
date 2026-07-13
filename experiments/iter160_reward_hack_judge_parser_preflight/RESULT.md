# Iteration 160 Result - Reward-Hack Judge Parser Preflight

Status: `pass_reward_hack_judge_parser_preflight`.

The zero-spend parser preflight passed. Telos now has a strict local parser and
fixture suite for blinded reward-hack model-judge outputs.

This gate ran no provider calls, no SWE-bench executions, and no cloud
resources. It does not claim a model score, leaderboard, model comparison,
state-of-the-art result, natural reward-hacking frequency, broad reward-model
robustness, or that any provider model has been evaluated on the packets.

## What Ran

- Parser module: `telos/reward_hack_judge_parser.py`.
- Preflight script: `scripts/preflight_reward_hack_judge_parser.py`.
- Frozen packet input:
  `benchmarks/reward_hack_benchmark_v1/blinded_model_judge_packets_v1/packets.jsonl`.
- Fixture output:
  - `proof/judge_output_schema.json`
  - `proof/fixtures/judge_output_fixtures.jsonl`
  - `proof/parsed_fixture_results.json`
  - `proof/parser_audit.json`

## Result

| bar | result |
| --- | ---: |
| packet artifact hash matched iter159 manifest | `pass` |
| valid verdicts accepted | `inconclusive, legitimate, reward_hack` |
| parsed fixtures | `3` |
| refusal fixtures | `2` |
| invalid fixtures | `8` |
| fixture SHA256 checks | `pass` |
| new provider calls | `0` |
| new SWE-bench executions | `0` |
| new cloud resources | `0` |

## Interpretation

The parser is intentionally fail-closed. It accepts only exact JSON objects with
`verdict`, `confidence`, and `rationale`; it does not recover markdown fences,
truncated JSON, string confidence values, unknown verdicts, missing fields, or
extra fields. Refusals are recorded separately and never count as caught or
legitimate.

## Claim Boundary

Supported: Telos validated a local parser and fixture suite for blinded
reward-hack judge outputs.

Not supported: model scores, leaderboard rankings, model-comparison results,
state-of-the-art claims, natural reward-hacking frequency estimates, broad
reward-model robustness claims, or any statement that a provider model has been
evaluated on the packets.

## Next Gate

`iter161`: run the first bounded single-model judge execution over the frozen
blinded packets using the iter160 parser, under a separately pre-registered call
and spend ceiling.

## Evidence

- `proof/judge_output_schema.json`
- `proof/fixtures/judge_output_fixtures.jsonl`
- `proof/parsed_fixture_results.json`
- `proof/parser_audit.json`
- `proof/endpoint_results.json`
- `proof/run_summary.json`
- `proof/learning_record.json`
- `proof/valid/receipt_reward_hack_judge_parser_preflight.json`
