# Iteration 94 Result - Provider LLM Judge Execution on Materialized Fixtures

Status: `BLOCKED`.

## Summary

This gate attempted the provider-backed LLM-judge strategy over the frozen iter92 materialized
fixtures after validating iter93. It does not claim benchmark/model/SOTA status.

- iter93 validation clean: `true`,
- materialized fixture count: `14`,
- LLM judge decision count: `0`,
- expected LLM judge decision count: `14`,
- provider calls attempted: `1`,
- provider call ceiling: `14`,
- provider spend: `$0.00470000`,
- provider spend ceiling: `$10.00000000`,
- prompt tokens: `838`,
- candidate tokens: `11`,
- thoughts tokens: `241`,
- labels used in LLM-judge prompts: `false`,
- all-strategy endpoint evidence complete: `false`,
- next gate: `experiments/iter95_provider_llm_judge_prompt_budget_recovery_after_block/HYPOTHESIS.md`,
- benchmark/model/SOTA claim: `false`,
- blockers: `LLM judge response could not be parsed for EVC-FIXTURE-0001`,
- failures: `none`.

## Claim Boundary

This is bounded fixture-comparison evidence. It is not a benchmark result, SWE-bench score,
leaderboard result, production/live-domain result, model-superiority result, or state-of-the-art
result.

## Evidence

- `proof/iter93_prerequisite_validation.json`
- `proof/model_binding.json`
- `proof/judge_prompt_template.md`
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
- `proof/valid/receipt_provider_llm_judge_execution_on_materialized_fixtures.json`
