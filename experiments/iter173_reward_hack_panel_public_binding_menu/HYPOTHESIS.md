# Iteration 173 - Reward-Hack Panel Public Binding Menu

Status: pre-registered zero-spend public binding-menu gate; no provider calls, credential probes, model
evaluations, SWE-bench executions, cloud resources, benchmark scores, leaderboard claims,
model-comparison claims, state-of-the-art claims, natural-frequency claims, or broad robustness claims have
been run for this gate.

## Why this gate exists

`iter172` is expected to block if no operator-supplied non-secret binding choices are present. The next
autonomous move is not a paid call. It is to build a current, source-linked public menu of acceptable
non-secret model/API binding choices for the Google, OpenAI, and Anthropic panel slots, so an operator can
choose without exposing credentials or private project/account identifiers.

## Method

Inputs:

- `experiments/iter172_reward_hack_panel_operator_binding_recovery/RESULT.md`
- `experiments/iter172_reward_hack_panel_operator_binding_recovery/proof/operator_binding_packet.json`
- `experiments/iter172_reward_hack_panel_operator_binding_recovery/proof/missing_operator_inputs.json`
- official public provider documentation for Google Gemini/Vertex structured output, OpenAI structured
  output, and Anthropic structured output/model availability, captured with source URLs and retrieval dates.

Execution envelope:

- provider calls: `0`,
- credential probes: `0`,
- model evaluations: `0`,
- new SWE-bench executions: `0`,
- new cloud runner/resources: `0`,
- do not read or print secrets,
- do not test live credentials,
- do not choose by observing model outputs,
- only cite public documentation or committed Telos artifacts.

## Required Outputs

- public binding menu for each panel slot with candidate model IDs/API routes, source URLs, and safe
  credential-source route labels,
- rejection reasons for any tempting but non-compliant option,
- operator-choice template containing placeholders only,
- secret-safety audit showing no committed artifact contains tokens, project IDs, service accounts, bearer
  strings, or credential material,
- readiness decision: `menu_ready_for_operator_choice` or `blocked_with_reasons`,
- valid receipt, audit report, run summary, and learning record.

## Numeric Bars

Minimum pass bars:

- zero provider calls, credential probes, model evaluations, SWE-bench executions, and cloud resources,
- at least one source-linked public candidate or explicit blocked reason per slot,
- no committed artifact contains secrets or private project/account identifiers,
- the iter171 `majority_catch` primary aggregation rule remains frozen,
- future paid pilot remains capped at `160` provider calls and `$50.00`,
- no leaderboard, model-superiority, state-of-the-art, natural-frequency, or broad robustness claim is made.

## Falsifiers

1. The gate performs any provider call, credential probe, or model evaluation.
2. The gate prints or commits secrets, bearer strings, project IDs, service accounts, or private account data.
3. A candidate is presented without a public source URL or without a safe private-identifier policy.
4. The primary aggregation rule changes after iter171.
5. The result authorizes a paid pilot above `160` calls or `$50.00`.
6. The result presents a model, panel, benchmark, leaderboard, SOTA, or broad robustness score.

## Claim Boundary

At most, if this gate passes: Telos has a zero-spend public binding menu and operator-choice template for
the iter169-iter172 independent judge-panel path.

Not supported: any model score, panel score, changed iter167/iter168 metric, leaderboard ranking, model
superiority, state-of-the-art claim, natural reward-hacking frequency estimate, broad reward-model
robustness claim, or claim about provider calls not actually run on the paired packets.
