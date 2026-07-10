# Iteration 80 Result - Dummy Call-Ceiling Bounded Paid Retry After Recovery

Status: `PASS`.

## Summary

The gate executed exactly the two Dummy adapter rows under the iter79 recovered 16-call ceiling.

- executed adapter row count: `2`,
- deterministic-edit rows rerun: `false`,
- retained BattleSnake rows rerun: `false`,
- iter79 recovery validation clean: `true`,
- call-ceiling overlays materialized: `true`,
- per-row provider call ceiling: `16`,
- provider API calls: `6`,
- provider call ceiling: `32`,
- provider cost from CodeClash metadata: `$0.02840000`,
- provider spend ceiling: `$5.00`,
- GPU used: `false`,
- cloud runner started: `false`,
- Sentinel-named resources modified: `false`,
- benchmark/model/SOTA claim: `false`,
- blockers: `none`,
- failures: `none`.

## Stratified Metrics

- Dummy baseline verified-completion evidence:
  `true`,
- Dummy Telos verified-completion evidence:
  `true`,
- Dummy Telos-minus-baseline verified-completion delta:
  `0`.

## Claim Boundary

This is a bounded two-row Dummy adapter-validation retry. It is not a benchmark result, SWE-bench
score, leaderboard result, production/live-domain result, model-superiority result, or
state-of-the-art result.

## Evidence

- `proof/prerequisite_validation.json`
- `proof/recovered_agent_overlay_manifest.json`
- `proof/preflight.json`
- `proof/runtime_access_path_binding.json`
- `proof/runtime_access_path_model_config.yaml`
- `proof/overlay_materialization_manifest.json`
- `proof/call_ceiling_overlay_binding.json`
- `proof/protocol_effect_report.json`
- `proof/raw/`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_dummy_call_ceiling_bounded_paid_retry_after_recovery.json`
