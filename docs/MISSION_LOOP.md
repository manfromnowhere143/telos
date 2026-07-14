# Mission Loop

Telos runs as a public evidence loop. The loop is compatible with Aweb/Maestro
orchestration, but the repository does not claim a private Aweb runner until a concrete capability
slug exists in Aweb discovery.

Machine-readable contract: [`../mission/loop.json`](../mission/loop.json).

## Current Boundary

- Active gate: [`../experiments/iter183_reward_hack_panel_public_claim_surface_sync/HYPOTHESIS.md`](../experiments/iter183_reward_hack_panel_public_claim_surface_sync/HYPOTHESIS.md)
- Active gate state: pre-registered zero-spend public claim-surface sync pending; iter161/iter165 may be
  cited only as a bounded paired single-model result (`3/40` all-hack recall, `0/40` control false
  positives, specificity `1.0`, balanced detection `0.5375`), iter166 may be cited only as a zero-spend
  evaluator-family design, and iter167 may be cited only as a completed skeptical-prompt null
  (`80/80` calls, `3/40` recall, `0/40` false positives, specificity `0.90`). Iter168 may be cited only
  as a zero-spend null adjudication showing all `9` invalids were markdown-fenced JSON and diagnostic
  repair would still reach only `4/40` recall. Iter169 may be cited only as a zero-spend independent
  judge-panel design with frozen slots, structured-output enforcement, aggregation rules, leakage controls,
  and future budget ceilings. Iter170 may be cited only as a zero-spend local structured-output/request
  preflight that keeps paid execution blocked pending exact bindings. Iter171 may be cited only as a
  zero-spend binding freeze and blocked readiness decision: all three panel slots require operator input,
  the primary `majority_catch` rule is frozen, generated secret hits are `0`, and the full all-packet
  three-slot panel requires `240` calls versus the preserved `160`-call ceiling. Iter172 may be cited only
  as a zero-spend operator-binding recovery packet showing no operator choices were supplied, all three
  slots still require operator input, missing non-secret fields are explicit, and paid execution remains
  unauthorized. Iter173 may be cited only as a zero-spend public binding menu with `3` panel slots, `6`
  source-linked candidates, secret hits `0`, `majority_catch` preserved, and paid execution still
  unauthorized. Iter174 may be cited only as a zero-spend default-choice freeze: `gemini-2.5-flash`,
  `gpt-5.6-terra`, and `claude-opus-4-8`, `3/3` menu membership, secret hits `0`, and paid execution still
  unauthorized. Iter175 may be cited only as a bounded `20`-pair panel pilot: `120/120` primary calls
  succeeded, retries were `0`, estimated spend guard was `$6.312690`, committed secret/project/account
  hits were `0`, and primary `majority_catch` caught `13/20` hack rows and `0/20` controls. Iter176 may
  be cited only as a zero-spend adjudication: `120/120` calls reconciled by hash, committed metrics
  matched, three OpenAI `max_output_tokens` empty-content rows stayed nondecisions, and the next gate is
  disagreement-calibrated expansion design. Iter177 may be cited only as a zero-spend design: `20` fresh
  remaining pairs, `3` diagnostic OpenAI recovery calls, `123` planned calls before retries, `160` call
  ceiling, `$50.00` spend ceiling, OpenAI max output tokens `1536`, and no new score. Iter178 may be cited
  only as a bounded paid remaining-pairs panel expansion: `123/123` calls succeeded, retries were `0`,
  spend guard was `$7.005150`, committed secret/project/account hits were `0`, fresh `majority_catch`
  caught `4/20` hack rows and `0/20` controls, combined unrepaired iter175+iter178 `majority_catch`
  caught `17/40` hack rows and `0/40` controls, and the three OpenAI recovery rows are diagnostic only.
  Iter179 may be cited only as a zero-spend full-cohort adjudication: `0` provider calls, credential
  probes, SWE-bench executions, and cloud resources; unrepaired `majority_catch` remains `17/40` hack
  rows and `0/40` controls; all five panel nondecisions are OpenAI empty-output rows; recovery diagnostics
  have `0` score-rewrite allowance and no repaired score is claimed. Iter180 may be cited only as a
  zero-spend repair design: five OpenAI empty-output primary nondecision rows must be rerun, including
  the three with prior diagnostics, under a future `10` call / `$10.00` ceiling, and unrepaired iter179
  remains the primary public result. Iter181 may be cited only as a bounded OpenAI repair execution
  diagnostic: `5/5` calls succeeded, retries were `0`, estimated spend guard was `$0.271800`, committed
  secret/project/account hits were `0`, `4/5` repair outputs parsed, and the secondary repaired
  diagnostic reduced panel nondecisions to `1` hack and `0` controls without changing the primary
  `majority_catch` result of `17/40` hack rows and `0/40` controls. Iter182 may be cited only as a
  zero-spend adjudication of that diagnostic: `5/5` raw responses reparsed and reconciled by hash, the
  committed comparison matched recomputation, already-seen diagnostics remained excluded, and iter179
  stayed primary. No benchmark score, leaderboard, model-comparison result, state-of-the-art
  result, natural-frequency estimate, broad robustness claim, or repaired-score claim is allowed.
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
