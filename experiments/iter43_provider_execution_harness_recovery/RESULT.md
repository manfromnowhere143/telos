# Iteration 43 Result - Provider Execution Harness Recovery

Status: `PASS`.

## Summary

The provider execution harness was recovered without running the frozen six task-condition pairs.

- committed harness: `scripts/run_ephemeral_vertex_codeclash_provider.py`,
- lifecycle probe mode: `execute`,
- non-GPU Telos VM created: `true`,
- Telos VM deleted: `true`,
- running Telos VM count after probe: `0`,
- running Sentinel-named VM count observed: `1`,
- provider model API calls: `0`,
- provider spend: `$0.00`,
- cloud-runner estimated spend bound: `$0.10`,
- full task-condition pairs executed: `0`,
- cost parser validated from prior provider artifacts: `true`,
- raw artifact retention validated from prior provider artifacts: `true`,
- redaction scan passed: `true`.

No account identifier, project identifier, service-account email, credential material, VM name, or
zone is committed in the proof.

## What Is Now Authorized

- Pre-register and run the frozen protocol-effect execution after harness recovery in
  `experiments/iter44_public_task_protocol_effect_execution_after_harness_recovery/HYPOTHESIS.md`.
- Keep the iter39 task slice, provider boundary, metric plan, and claim boundaries unchanged.
- Execute only under the recovered harness, cost capture, redaction scan, runner lifecycle, and
  artifact-retention controls.

## What Remains Forbidden

- No benchmark result is claimed.
- No SWE-bench score is claimed.
- No leaderboard result is claimed.
- No production or live-domain result is claimed.
- No model-superiority or state-of-the-art result is claimed.
- No hidden provider spend or unlogged model call is allowed.

## Evidence

- `proof/provider_execution_harness_report.json`
- `proof/run_summary.json`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/valid/receipt_provider_execution_harness_recovery.json`
