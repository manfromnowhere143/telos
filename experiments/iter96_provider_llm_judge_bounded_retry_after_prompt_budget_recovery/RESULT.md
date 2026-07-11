# Iteration 96 Result - Provider LLM Judge Bounded Retry After Prompt Budget Recovery

Status: `PASS`.

## Summary

This gate retried the provider-backed LLM-judge strategy over the frozen iter92 fixtures using the
iter95 recovered prompt/token-budget design. It does not claim benchmark/model/SOTA status.

- iter95 validation clean: `true`,
- materialized fixture count: `14`,
- LLM judge decision count: `14`,
- expected LLM judge decision count: `14`,
- provider calls attempted: `14`,
- provider call ceiling: `14`,
- provider spend: `$0.19588800`,
- provider spend ceiling: `$5.00000000`,
- prompt tokens: `10590`,
- candidate tokens: `1109`,
- thoughts tokens: `13450`,
- labels used in LLM-judge prompts: `false`,
- all-strategy endpoint evidence complete: `true`,
- next gate: `experiments/iter97_five_strategy_completion_verification_adjudication_after_llm_judge/HYPOTHESIS.md`,
- benchmark/model/SOTA claim: `false`,
- blockers: `none`,
- failures: `none`.

## LLM Judge Endpoint Row

| strategy | false-completion acceptance | false rejection | legitimate preservation |
| --- | ---: | ---: | ---: |
| `llm_judge` | `0.00000000` | `0.71428571` | `0.28571429` |

## Claim Boundary

This is bounded fixture-comparison evidence. It is not a benchmark result, SWE-bench score,
leaderboard result, production/live-domain result, model-superiority result, or state-of-the-art
result.

## Evidence

- `proof/iter95_prerequisite_validation.json`
- `proof/model_binding.json`
- `proof/recovered_prompt_manifest.json`
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
- `proof/valid/receipt_provider_llm_judge_bounded_retry_after_prompt_budget_recovery.json`
