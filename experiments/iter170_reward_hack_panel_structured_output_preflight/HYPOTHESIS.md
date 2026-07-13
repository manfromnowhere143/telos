# Iteration 170 - Reward-Hack Panel Structured-Output Preflight

Status: pre-registered zero-spend parser/schema/request preflight; no provider calls, model evaluations,
SWE-bench executions, cloud resources, benchmark scores, leaderboard claims, model-comparison claims,
state-of-the-art claims, natural-frequency claims, or broad robustness claims have been run for this gate.

## Why this gate exists

`iter169` designed an independent reward-hack judge panel, but the design is useful only if every future
panel member can be forced through the same strict output contract before paid execution. `iter168` showed
why this matters: all `9` invalid `iter167` outputs were markdown-fenced JSON, and diagnostic repair would
still move recall only from `3/40` to `4/40`.

The next step is therefore a local preflight, not a paid panel. This gate must prove that the canonical
judge schema, parser fixtures, request-shape constraints, leakage checks, and blocked/unavailable slot
semantics are frozen before any OpenAI, Anthropic, or Google panel call is allowed.

## Method

Inputs:

- `experiments/iter169_reward_hack_independent_judge_panel_design/RESULT.md`
- `experiments/iter169_reward_hack_independent_judge_panel_design/proof/panel_protocol.json`
- `experiments/iter169_reward_hack_independent_judge_panel_design/proof/structured_output_plan.json`
- `experiments/iter169_reward_hack_independent_judge_panel_design/proof/aggregation_rules.json`
- `experiments/iter169_reward_hack_independent_judge_panel_design/proof/leakage_control_plan.json`
- `experiments/iter169_reward_hack_independent_judge_panel_design/proof/budget_and_gate_recommendation.json`
- `experiments/iter160_reward_hack_judge_parser_preflight/proof/parser_audit.json`
- `telos/reward_hack_judge_parser.py`
- `benchmarks/reward_hack_benchmark_v1/blinded_model_judge_packets_v1/packets.jsonl`
- `benchmarks/reward_hack_benchmark_v1/legitimate_controls_v1/blinded_control_packets_v1/packets.jsonl`

Execution envelope:

- provider calls: `0`,
- model evaluations: `0`,
- new SWE-bench executions: `0`,
- new cloud runner/resources: `0`,
- do not bind exact paid model ids from new outputs,
- do not score any model or panel,
- do not change iter167, iter168, or iter169 results,
- keep all claim language below the completed evidence.

## Required Outputs

- local parser fixture audit for valid `reward_hack`, `legitimate`, and `inconclusive` verdicts,
- local parser fixture audit for refusal, invalid JSON, markdown-fenced JSON, missing fields, extra fields,
  invalid confidence, and unknown verdict values,
- provider-family request-shape plan for Google, OpenAI, and Anthropic slots, each explicitly marked
  `preflight_ready`, `blocked`, or `requires_operator_binding`,
- canonical output schema hash and parser source hash,
- prompt/input allowlist and forbidden-field scan over at least one hack packet and one paired control packet,
- nondecision accounting table showing that invalid, refusal, inconclusive, and provider-error outputs are
  never true positives or true negatives,
- future paid-run readiness recommendation that either authorizes a bounded pilot or blocks it with reasons,
- valid receipt, audit report, run summary, and learning record.

## Numeric Bars

Minimum pass bars:

- zero provider calls, model evaluations, SWE-bench executions, and cloud resources,
- all local valid parser fixtures parse successfully,
- all malformed/refusal/nondecision fixtures are classified outside true-positive and true-negative counts,
- every iter169 panel slot has an explicit request-shape status,
- prompt-visible keys for sampled hack and control packets match the iter169 allowlist,
- forbidden leakage scans over sampled packets return zero hits,
- future paid pilot remains capped at `160` provider calls and `$50.00`,
- no leaderboard, model-superiority, state-of-the-art, natural-frequency, or broad robustness claim is made.

## Falsifiers

1. The preflight performs any provider call or model evaluation.
2. Markdown-fenced JSON is accepted without a separately pre-registered repair parser.
3. Any future panel slot can proceed without an explicit structured-output request shape or blocked status.
4. The preflight chooses a primary aggregation rule after seeing paid outputs.
5. Invalid, refusal, inconclusive, or provider-error outputs are counted as catches or true negatives.
6. The result presents a model, panel, benchmark, leaderboard, SOTA, or broad robustness score.

## Claim Boundary

At most, if this gate passes: Telos has a zero-spend structured-output and request-shape preflight for the
iter169 independent judge-panel design.

Not supported: any model score, panel score, changed iter167/iter168 metric, leaderboard ranking, model
superiority, state-of-the-art claim, natural reward-hacking frequency estimate, broad reward-model
robustness claim, or claim about provider bindings not yet run on the paired packets.
