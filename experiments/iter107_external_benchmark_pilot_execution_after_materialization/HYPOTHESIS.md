# Iteration 107 - External Benchmark Pilot Execution After Materialization

Status: pre-registered, result pending.

## Purpose

Execute the materialized iter106 external benchmark pilot under the frozen strategy-input manifests
and publish pass, null, adverse, or blocked evidence. This gate tests whether the complete Telos
protocol reduces false-completion acceptance on the 20 frozen packets while preserving legitimate
completion controls.

## Execution Envelope

Hard ceilings:

- prerequisite: iter106 materialization evidence must validate cleanly,
- provider model invocations: at most `30`,
- provider spend: at most `$10.00000000`,
- benchmark packet executions: at most `20` materialized packets,
- strategy set: `agent_self_report`, `execution_tests_only`, `llm_judge`, `external_verifier`,
  and `complete_telos_protocol`,
- strategy inputs: only the public iter106 packet artifacts and hashes,
- private labels: unavailable to every strategy until scoring,
- GPU use: forbidden,
- cloud runner startup: forbidden,
- Sentinel-named resource mutation: forbidden,
- production/live-domain mutation: forbidden,
- benchmark/model/SOTA claim: forbidden.

The result may claim at most a bounded external pilot result if the full receipt and audit packet
support it. It may not claim a benchmark leaderboard result, SWE-bench score, broad model
superiority, all-strategy superiority, or state-of-the-art result.

## Required Evidence

The proof packet must include validated iter106 evidence, raw strategy outputs, provider usage and
cost records, endpoint results, adverse/null result register, private-label scoring after strategy
outputs are frozen, redaction scan, claim boundary, and a valid receipt. Any label leak, budget
overrun, missing raw output, unsupported claim, or unregistered retry must stop the gate and publish
the blocker or adverse result.
