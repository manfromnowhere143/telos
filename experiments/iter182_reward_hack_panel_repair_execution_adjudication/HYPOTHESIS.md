# Iteration 182 - Reward-Hack Panel Repair Execution Adjudication

Status: pre-registered zero-spend adjudication gate; no provider calls, credential probes, model
evaluations, SWE-bench executions, cloud resources, benchmark scores, leaderboard claims,
model-comparison claims, state-of-the-art claims, natural-frequency claims, broad robustness claims, or
repaired-score claims have been run for this gate.

## Why this gate exists

Iter181 may add fresh OpenAI repair outputs for the five prior nondecision rows. Before any public-facing
wording changes, those outputs must be adjudicated from committed proof with the unrepaired iter179
primary result preserved unless a later gate explicitly changes the claim boundary.

## Method

Inputs:

- `experiments/iter181_reward_hack_panel_openai_nondecision_repair_execution/RESULT.md`
- `experiments/iter181_reward_hack_panel_openai_nondecision_repair_execution/proof/provider_call_ledger.jsonl`
- `experiments/iter181_reward_hack_panel_openai_nondecision_repair_execution/proof/repair_output_table.json`
- `experiments/iter181_reward_hack_panel_openai_nondecision_repair_execution/proof/unrepaired_vs_repaired_diagnostic_comparison.json`
- `experiments/iter181_reward_hack_panel_openai_nondecision_repair_execution/proof/claim_boundary_decision.json`

Adjudication envelope:

- provider calls: `0`,
- credential probes: `0`,
- estimated provider spend: `$0.00`,
- new SWE-bench executions: `0`,
- new cloud runner/resources: `0`,
- primary public result remains iter179 unrepaired unless separately justified,
- no already-seen diagnostic output can enter score evidence.

## Required Outputs

- recomputation of iter181 repaired diagnostic from raw parsed outputs,
- audit that iter179 unrepaired primary metrics were not mutated,
- claim-boundary decision for README/paper language,
- secret-safety audit, endpoint results, receipt, audit report, run summary, and learning record.

## Numeric Bars

Minimum pass bars:

- provider calls are exactly `0`,
- credential probes are exactly `0`,
- committed iter181 parsed outputs reconcile to the provider ledger by call id and hash,
- any repaired diagnostic uses only fresh iter181 outputs,
- already-seen iter178 diagnostics remain excluded,
- unrepaired iter179 remains identifiable as the primary public metric,
- no committed artifact contains a secret, bearer token, project ID, account ID, or service account,
- no leaderboard, model-superiority, state-of-the-art, natural-frequency, broad robustness, public
  benchmark-score, or repaired-score claim is made.

## Falsifiers

1. The gate performs any provider call, credential probe, model evaluation, SWE-bench execution, or cloud
   resource change.
2. The adjudication cannot reconcile iter181 outputs to raw evidence.
3. Already-seen diagnostics are counted as score evidence.
4. The unrepaired iter179 primary result is hidden or mutated.
5. A committed artifact contains a secret, bearer token, service account, project ID, account ID, or
   private credential material.
6. The result presents a leaderboard, model-superiority, SOTA, natural-frequency, broad robustness, public
   benchmark-score, or repaired-score claim.

## Claim Boundary

At most, if this gate passes: Telos has an adjudicated bounded OpenAI repair diagnostic, still reported
separately from the unrepaired iter179 primary result.

Not supported: a leaderboard ranking, state-of-the-art claim, natural reward-hacking frequency estimate,
broad reward-model robustness claim, production deployment claim, public benchmark score, repaired-score
claim, or any claim outside committed iter175-iter182 proof packets.
