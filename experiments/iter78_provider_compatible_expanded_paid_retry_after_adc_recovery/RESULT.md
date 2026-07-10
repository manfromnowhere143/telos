# Iteration 78 Result - Provider-Compatible Expanded Paid Retry After ADC Recovery

Status: `BLOCKED`.

## Summary

The gate retried the four iter71-selected adapter-planned rows after iter73 receipt prompt recovery.

- executed adapter row count: `4`,
- retained BattleSnake rows rerun: `false`,
- iter72 prerequisite validation clean: `true`,
- iter73 recovery validation clean: `true`,
- iter74 blocked retry validation clean: `true`,
- iter77 ADC readiness validation clean: `true`,
- recovered iter73 prompt overlays materialized: `true`,
- provider API calls: `9`,
- provider call ceiling: `32`,
- provider cost from CodeClash metadata: `$0.03987600`,
- provider spend ceiling: `$10.00`,
- GPU used: `false`,
- cloud runner started: `false`,
- Sentinel-named resources modified: `false`,
- benchmark/model/SOTA claim: `false`,
- blockers: `provider_command_nonzero_returncode`,
- failures: `none`.

## Stratified Metrics

- Dummy baseline verified-completion evidence:
  `false`,
- Dummy Telos verified-completion evidence:
  `false`,
- deterministic-edit baseline verified-completion evidence:
  `true`,
- deterministic-edit Telos verified-completion evidence:
  `true`.

## Claim Boundary

This is a bounded four-row adapter-validation retry under a stratified Telos protocol-effect
boundary. It is not a benchmark result, SWE-bench score, leaderboard result,
production/live-domain result, model-superiority result, or state-of-the-art result.

## Evidence

- `proof/prerequisite_validation.json`
- `proof/preflight.json`
- `proof/runtime_access_path_binding.json`
- `proof/runtime_access_path_model_config.yaml`
- `proof/overlay_materialization_manifest.json`
- `proof/recovered_prompt_overlay_binding.json`
- `proof/protocol_effect_report.json`
- `proof/raw/`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_provider_compatible_expanded_paid_retry_after_adc_recovery.json`
