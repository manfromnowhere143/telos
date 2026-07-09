# Iteration 64 Result - Provider-Compatible Paid Execution After Access Path Recovery

Status: `PASS`.

## Summary

The gate executed selected provider-compatible BattleSnake rows after `iter63` recovered the Vertex access path. It did not execute excluded pairs, start a cloud runner, use GPU, or modify
Sentinel-named resources.

- iter63 prerequisite status: `pass`,
- iter63 blocker classification: `access_path_recovered`,
- runtime overlay materialized: `true`,
- runtime env values committed: `false`,
- verifier-crash recovery used: `true`,
- recovered verifier-crash pair ids: `baseline-agent-completion-evidence__configs-test-battlesnake-pvp-test-yaml`,
- executed pair count: `2`,
- excluded pairs executed: `false`,
- provider API calls: `10`,
- provider cost from CodeClash metadata: `$0.07044800`,
- baseline verified-completion evidence: `true`,
- Telos verified-completion evidence: `false`,
- Telos-minus-baseline verified-completion delta: `-1`.
- blockers: `none`,
- failures: `none`.

## Claim Boundary

This is a bounded two-row provider-compatible protocol-effect pilot. It is not a benchmark result,
SWE-bench score, leaderboard result, production/live-domain result, model-superiority result, or
state-of-the-art result.

## Evidence

- `proof/preflight.json`
- `proof/runtime_access_path_binding.json`
- `proof/runtime_access_path_model_config.yaml`
- `proof/overlay_materialization_manifest.json`
- `proof/protocol_effect_report.json`
- `proof/raw/`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_provider_compatible_paid_execution_after_access_path_recovery.json`
