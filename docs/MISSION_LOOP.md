# Mission Loop

Telos runs as a public evidence loop. The loop is compatible with Aweb/Maestro
orchestration, but the repository does not claim a private Aweb runner until a concrete capability
slug exists in Aweb discovery.

Machine-readable contract: [`../mission/loop.json`](../mission/loop.json).

## Current Boundary

- Active gate: [`../experiments/iter166_reward_hack_moonshot_evaluator_family_design/HYPOTHESIS.md`](../experiments/iter166_reward_hack_moonshot_evaluator_family_design/HYPOTHESIS.md)
- Active gate state: pre-registered moonshot evaluator-family design pending; iter161/iter165 may be cited
  only as a bounded paired single-model result (`3/40` all-hack recall, `0/40` control false positives,
  specificity `1.0`, balanced detection `0.5375`). No benchmark score, leaderboard, model-comparison
  result, state-of-the-art result, natural-frequency estimate, or broad robustness claim is allowed.
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
