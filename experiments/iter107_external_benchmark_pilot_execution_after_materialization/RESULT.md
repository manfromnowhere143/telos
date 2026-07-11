# Iteration 107 Result - External Benchmark Pilot Execution After Materialization

Status: pass.

## Summary

The 20-packet materialized external pilot was executed across the frozen five strategy set, with private labels used only after strategy decisions were frozen.

- Strategy set: agent self-report, execution-tests-only, LLM judge, external verifier, complete Telos protocol.
- Provider calls: `20` of `30`.
- Estimated provider spend: `$0.38674600` of `$10.00000000`.
- Complete Telos false-completion acceptance rate: `0.00000000`.
- External verifier false-completion acceptance rate: `0.20000000`.
- LLM judge false-completion acceptance rate: `0.00000000`.
- Complete Telos legitimate-control preservation rate: `1.00000000`.
- Primary endpoint delta versus external verifier: `0.20000000`.
- Bounded pilot success: `True`.
- Bounded pilot null result: `False`.
- Bounded pilot adverse result: `False`.

## Claim Boundary

This is at most a bounded 20-packet external pilot execution result. It is not a benchmark leaderboard result, SWE-bench score, broad model result, all-strategy superiority claim, or state-of-the-art claim.

## Evidence

- `proof/iter106_prerequisite_validation.json`
- `proof/strategy_input_integrity.json`
- `proof/raw_strategy_outputs/`
- `proof/strategy_decisions/`
- `proof/provider_usage.json`
- `proof/endpoint_results.json`
- `proof/adverse_result_register.json`
- `proof/claim_boundary.json`
- `proof/valid/receipt_external_benchmark_pilot_execution_after_materialization.json`
