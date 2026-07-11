# Iteration 103 Result - Differential Provider LLM Judge Full Retry After Block Recovery

Status: `PASS`.

## Summary

This gate ran the recovered provider-backed LLM-judge strategy over the frozen iter99 differential
fixtures after iter102 output-budget recovery. Deterministic strategies were not rerun, private
labels stayed out of prompts, and no benchmark/model/SOTA or broad superiority claim is made.

- iter102 validation clean: `true`,
- materialized fixture count: `16`,
- LLM judge decision count: `16`,
- expected LLM judge decision count: `16`,
- provider calls attempted: `16`,
- provider call ceiling: `16`,
- provider spend: `$0.23633000`,
- provider spend ceiling: `$5.00000000`,
- prompt tokens: `14995`,
- candidate tokens: `1057`,
- thoughts tokens: `16138`,
- labels used in LLM-judge prompts: `false`,
- all-strategy endpoint evidence complete: `true`,
- next gate: `experiments/iter104_five_strategy_differential_adjudication_after_recovered_llm_judge/HYPOTHESIS.md`,
- benchmark/model/SOTA claim: `false`,
- blockers: `none`,
- failures: `none`.

## LLM Judge Endpoint Row

| strategy | false-completion acceptance | false rejection | legitimate preservation |
| --- | ---: | ---: | ---: |
| `llm_judge` | `0.00000000` | `0.75000000` | `0.25000000` |

## Claim Boundary

This is bounded recovered provider LLM-judge fixture-comparison evidence. It is not a benchmark
result, SWE-bench score, leaderboard result, production/live-domain result, model-superiority
result, broad Telos-specific superiority result, all-strategy superiority result, or state-of-the-
art result.

## Evidence

- `proof/iter102_validation.json`
- `proof/model_binding.json`
- `proof/prompt_manifest.json`
- `proof/raw/llm_judge/`
- `proof/decision_manifest.json`
- `proof/decisions/llm_judge/`
- `proof/provider_usage.json`
- `proof/endpoint_results.json`
- `proof/claim_boundary.json`
- `proof/redaction_scan.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_differential_provider_llm_judge_full_retry_after_block_recovery.json`
