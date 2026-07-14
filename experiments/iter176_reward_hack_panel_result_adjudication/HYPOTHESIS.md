# Iteration 176 - Reward-Hack Panel Result Adjudication

Status: pre-registered zero-spend adjudication gate; no provider calls, credential probes, model
evaluations, SWE-bench executions, cloud resources, benchmark scores, leaderboard claims,
model-comparison claims, state-of-the-art claims, natural-frequency claims, or broad robustness claims
have been run for this gate.

## Why this gate exists

`iter175` completed the first bounded three-provider panel pilot under frozen defaults. Before expanding
the panel, publishing stronger claims, or spending again, this gate must rederive the result from raw
proof artifacts, inspect invalid/nondecision and disagreement patterns, and decide what the pilot actually
supports.

## Method

Inputs:

- `experiments/iter175_reward_hack_panel_bounded_paid_pilot/RESULT.md`
- `experiments/iter175_reward_hack_panel_bounded_paid_pilot/proof/provider_call_ledger.jsonl`
- `experiments/iter175_reward_hack_panel_bounded_paid_pilot/proof/parsed_judge_outputs.jsonl`
- `experiments/iter175_reward_hack_panel_bounded_paid_pilot/proof/per_slot_metrics.json`
- `experiments/iter175_reward_hack_panel_bounded_paid_pilot/proof/panel_metrics.json`
- `experiments/iter175_reward_hack_panel_bounded_paid_pilot/proof/prompt_response_hash_manifest.json`
- frozen iter171/iter174 schedule, default-choice, and aggregation-rule artifacts.

Adjudication envelope:

- provider calls: `0`,
- credential probes: `0`,
- model evaluations: `0`,
- new SWE-bench executions: `0`,
- new cloud runner/resources: `0`,
- recompute all headline counts from committed ledger/parser artifacts,
- inspect invalid outputs without repairing or changing the iter160 parser,
- report row-level slot disagreements and panel nondecisions,
- preserve `majority_catch` as the primary rule and report `any_catch`, `unanimous_catch`, and standalone
  slot metrics only as secondary evidence.

## Required Outputs

- metric recomputation audit,
- invalid-output audit,
- row-level disagreement matrix,
- panel-rule comparison table,
- claim-boundary decision,
- next-gate recommendation,
- secret-safety audit, endpoint results, receipt, audit report, run summary, and learning record.

## Numeric Bars

Minimum pass bars:

- `120/120` iter175 attempted calls are accounted for by hash,
- every iter175 parsed-output row maps to exactly one scheduled call,
- recomputed primary `majority_catch` counts match the committed iter175 panel metrics or any mismatch is
  published as a correction,
- invalid/nondecision rows are reported but not converted into catches or legitimate decisions,
- total new provider calls, credential probes, SWE-bench executions, and cloud resources are all `0`,
- no committed artifact contains a secret, private project/account identifier, service-account value,
  bearer token, or API key,
- no leaderboard, model-superiority, state-of-the-art, natural-frequency, broad robustness, or public
  benchmark-score claim is made.

## Falsifiers

1. The gate makes any provider call, credential probe, model evaluation, SWE-bench execution, or cloud
   resource change.
2. Recomputed counts cannot be reconciled with the iter175 ledger and parsed-output artifacts.
3. Invalid, refusal, or inconclusive outputs are counted as true positives or true negatives.
4. A row, model, parser, aggregation rule, or metric denominator is changed after seeing iter175 outputs.
5. A committed artifact contains a secret, bearer token, service account, project ID, account ID, or private
   credential material.
6. The result presents a leaderboard, model-superiority, SOTA, natural-frequency, broad robustness, or public
   benchmark-score claim.

## Claim Boundary

At most, if this gate passes: Telos has an independently rederived and adjudicated bounded `20`-pair panel
pilot under the iter174 frozen defaults.

Not supported: a leaderboard ranking, state-of-the-art claim, natural reward-hacking frequency estimate,
broad reward-model robustness claim, production deployment claim, or any claim about rows, models, calls,
or outputs outside the iter175 proof packet.
