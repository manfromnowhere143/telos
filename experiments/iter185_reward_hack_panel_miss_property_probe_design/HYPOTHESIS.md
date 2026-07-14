# Iteration 185 - Reward-Hack Panel Miss Property-Probe Design

Status: pre-registered zero-spend panel-miss property-probe design gate; no provider calls, credential
probes, model evaluations, SWE-bench executions, cloud resources, benchmark scores, leaderboard claims,
model-comparison claims, state-of-the-art claims, natural-frequency claims, broad robustness claims, or
repaired-score claims have been run for this gate.

## Why this gate exists

Iter184 maps current public research to Telos' next empirical direction. The panel's primary public metric
is still unrepaired iter179 `majority_catch`: `17/40` hack rows and `0/40` controls. The useful next step
is to design an execution/property-probe escalation for the hack rows that the primary panel still misses,
without adding a paid judge run before the row cohort, leakage rules, and stop bars are frozen.

## Method

Inputs:

- `experiments/iter179_reward_hack_panel_full_cohort_adjudication/proof/full_cohort_panel_metrics.json`
- `experiments/iter179_reward_hack_panel_full_cohort_adjudication/proof/row_level_disagreement_and_nondecision_audit.json`
- `experiments/iter182_reward_hack_panel_repair_execution_adjudication/RESULT.md`
- `experiments/iter184_reward_hack_panel_frontier_research_alignment_design/proof/source_linked_frontier_alignment_matrix.json`
- `experiments/iter184_reward_hack_panel_frontier_research_alignment_design/proof/telos_gap_to_technique_map.json`
- `benchmarks/reward_hack_benchmark_v1/reward_hack_benchmark_v1.jsonl`
- `benchmarks/reward_hack_benchmark_v1/manifest.json`

Execution envelope:

- provider calls: `0`,
- credential probes: `0`,
- estimated provider spend: `$0.00`,
- new SWE-bench executions: `0`,
- new cloud runner/resources: `0`.

## Required Outputs

- iter179 primary-miss cohort manifest,
- disagreement-class and repo-coverage audit,
- priority 12-row property-probe design subset,
- no-gold/no-hidden-test/no-official-expected-output leakage policy,
- future execution/property-generator budget recommendation,
- claim-boundary audit, secret-safety audit, endpoint results, receipt, audit report, run summary, and
  learning record.

## Numeric Bars

Minimum pass bars:

- provider calls are exactly `0`,
- credential probes are exactly `0`,
- the full primary-miss hack cohort is exactly `23` rows from the committed iter179 row audit,
- the miss cohort is partitioned into at least `3` disagreement/nondecision classes,
- the priority property-probe design subset contains exactly `12` rows,
- the priority subset covers at least `6` repositories,
- the leakage policy explicitly forbids gold patches, hidden test names, official expected outputs, and
  label leakage in any future prompt,
- the future paid/execution gate has numeric call, spend, execution, false-positive, and nondecision bars
  before any provider call,
- no leaderboard, model-superiority, state-of-the-art, natural-frequency, broad robustness, public
  benchmark-score, or repaired-score claim is made,
- no committed artifact contains a secret, bearer token, project ID, account ID, or service account.

## Falsifiers

1. The gate performs any provider call, credential probe, model evaluation, SWE-bench execution, or cloud
   resource change.
2. The primary-miss cohort does not reconcile to exactly `23` hack rows from iter179.
3. The priority design subset fails the size or repo-coverage bars.
4. The leakage policy allows gold patches, hidden tests, official expected outputs, or labels into future
   prompts.
5. The result recommends paid work without numeric call, spend, execution, false-positive, and
   nondecision bars.
6. A committed artifact contains a secret, bearer token, service account, project ID, account ID, or
   private credential material.
7. The result presents a leaderboard, model-superiority, SOTA, natural-frequency, broad robustness,
   public benchmark-score, or repaired-score claim.

## Claim Boundary

At most, if this gate passes: Telos has a zero-spend design for a future execution/property-probe
escalation over the committed iter179 primary-miss hack cohort.

Not supported: a leaderboard ranking, state-of-the-art claim, natural reward-hacking frequency estimate,
broad reward-model robustness claim, production deployment claim, public benchmark score, repaired-score
claim, or any claim outside committed iter175-iter185 proof packets.
