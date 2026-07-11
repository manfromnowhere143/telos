# Iteration 104 Result - Five-Strategy Differential Adjudication After Recovered LLM Judge

Status: `PASS`.

## Summary

This zero-spend gate adjudicated the completed iter100/iter103 five-strategy differential fixture
evidence. It supports a fixture-level differential claim only; it does not claim a benchmark
result, model superiority, broad all-strategy superiority, or state of the art.

| strategy | false-completion acceptance | false rejection | legitimate preservation |
| --- | ---: | ---: | ---: |
| `agent_self_report` | `1.00000000` | `0.00000000` | `1.00000000` |
| `execution_tests_only` | `1.00000000` | `0.00000000` | `1.00000000` |
| `llm_judge` | `0.00000000` | `0.75000000` | `0.25000000` |
| `external_verifier` | `0.50000000` | `0.00000000` | `1.00000000` |
| `complete_telos_protocol` | `0.00000000` | `0.00000000` | `1.00000000` |

## Interpretation

- Self-report and visible tests accepted every false-completion trap.
- The recovered provider LLM judge accepted no false-completion trap but rejected `6/8`
  legitimate controls.
- External verifier accepted `4/8` false-completion traps while complete Telos accepted `0/8`.
- Complete Telos was the only balanced pass on this frozen differential fixture suite.
- Immediate benchmark claims are rejected; the next step is an external benchmark-pilot design gate.

## Claim Boundary

Claim supported now: On the frozen 16-fixture differential suite, complete Telos was the only strategy with 0/8 false-completion acceptance and 8/8 legitimate-control preservation; external verifier accepted 4/8 false-completion traps and the provider LLM judge rejected 6/8 legitimate controls.

Claim not supported now: No benchmark result, SWE-bench score, leaderboard result, production/live-domain result, model-superiority result, broad all-strategy superiority result, or state-of-the-art result is supported.

- provider calls in this gate: `0`
- provider spend in this gate: `$0.00000000`
- strategy execution in this gate: `0`
- row execution in this gate: `0`
- next gate: `experiments/iter105_external_benchmark_pilot_design_after_differential_adjudication/HYPOTHESIS.md`
- benchmark/model/SOTA claim: `false`
- blockers: `none`
- failures: `none`

## Evidence

- `proof/iter103_prerequisite_validation.json`
- `proof/five_strategy_differential_endpoint_table.json`
- `proof/strategy_comparison.json`
- `proof/adverse_result_register.json`
- `proof/next_step_decision.json`
- `proof/claim_boundary.json`
- `proof/redaction_scan.json`
- `proof/run_summary.json`
- `proof/valid/receipt_five_strategy_differential_adjudication_after_recovered_llm_judge.json`
