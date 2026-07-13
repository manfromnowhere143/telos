# Mission Loop

Telos runs as a public evidence loop. The loop is compatible with Aweb/Maestro
orchestration, but the repository does not claim a private Aweb runner until a concrete capability
slug exists in Aweb discovery.

Machine-readable contract: [`../mission/loop.json`](../mission/loop.json).

## Current Boundary

- Active gate: [`../experiments/iter171_reward_hack_panel_model_binding_freeze/HYPOTHESIS.md`](../experiments/iter171_reward_hack_panel_model_binding_freeze/HYPOTHESIS.md)
- Active gate state: pre-registered zero-spend exact model/API binding freeze pending; iter161/iter165 may be
  cited only as a bounded paired single-model result (`3/40` all-hack recall, `0/40` control false
  positives, specificity `1.0`, balanced detection `0.5375`), iter166 may be cited only as a zero-spend
  evaluator-family design, and iter167 may be cited only as a completed skeptical-prompt null
  (`80/80` calls, `3/40` recall, `0/40` false positives, specificity `0.90`). Iter168 may be cited only
  as a zero-spend null adjudication showing all `9` invalids were markdown-fenced JSON and diagnostic
  repair would still reach only `4/40` recall. Iter169 may be cited only as a zero-spend independent
  judge-panel design with frozen slots, structured-output enforcement, aggregation rules, leakage controls,
  and future budget ceilings. Iter170 may be cited only as a zero-spend local structured-output/request
  preflight that keeps paid execution blocked pending exact bindings. No benchmark score, leaderboard,
  model-comparison result, state-of-the-art result, natural-frequency estimate, or broad robustness claim is
  allowed.
- Public runner: GitHub Actions plus local validators.
- Aweb discovery: checked again on 2026-07-13; no callable Telos/Maestro capability slug was returned by
  the Aweb MCP catalog.
- Claim allowed now: Telos is running through the public evidence loop.
- Claim not allowed now: Telos is already executing through a private Aweb/Maestro runtime.

## Loop Phases

1. Pre-register the gate in `experiments/*/HYPOTHESIS.md`.
2. Execute the smallest honest run with pinned upstream code and recorded environment.
3. Collect raw artifacts before interpretation.
4. Audit receipts, raw hashes, docs, learning records, and handoff state.
5. Publish `RESULT.md`, including null or blocked results at full weight.
6. Learn or stop from evidence only.
7. Regenerate `HANDOFF.md` so the next operator resumes without guessing.

## Refinement Rule

Refinement is allowed only after evidence identifies a concrete gap. If the hypothesis fails,
publish the null. If the harness is wrong, patch the harness or invariant and rerun the same gate.
If the result passes, publish proof before expanding scope.

The loop does not chase polish. It improves only when the evidence says a specific part of the
mission control system is not yet producing a trustworthy result.
