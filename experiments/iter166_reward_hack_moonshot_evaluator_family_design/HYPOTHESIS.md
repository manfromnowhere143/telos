# Iteration 166 - Reward-Hack Moonshot Evaluator-Family Design

Status: pre-registered design gate; no provider calls, model evaluations, SWE-bench executions, cloud
resources, leaderboard claims, model-comparison claims, state-of-the-art claims, or new benchmark scores
have been run for this gate.

## Why this gate exists

The first complete paired single-model result is now bounded and interpretable: the `gemini-2.5-flash`
judge caught `3/40` all-hack rows in iter161 and, after the iter164 rate-limit block was recovered in
iter165, false-flagged `0/40` paired legitimate controls. That is a conservative classifier with perfect
specificity on this paired control set and very low recall on the hack set. The next move is not to inflate
that into a leaderboard; it is to design the moonshot evaluator family that can raise recall while
protecting the now-measured false-positive boundary.

## Method

Inputs:

- `experiments/iter156_reward_hack_benchmark_v1_manifest/RESULT.md`
- `benchmarks/reward_hack_benchmark_v1/manifest.json`
- `benchmarks/reward_hack_benchmark_v1/reward_hack_benchmark_v1.jsonl`
- `benchmarks/reward_hack_benchmark_v1/blinded_model_judge_packets_v1/manifest.json`
- `benchmarks/reward_hack_benchmark_v1/legitimate_controls_v1/manifest.json`
- `experiments/iter158_reward_hack_moonshot_design/proof/`
- `experiments/iter161_reward_hack_single_model_judge_execution/proof/run_summary.json`
- `experiments/iter162_reward_hack_legitimate_control_design/proof/metric_protocol.json`
- `experiments/iter165_reward_hack_control_evaluation_rate_limit_recovery/proof/metric_summary.json`
- committed detector/static labels and official-report hashes for `reward_hack_benchmark_v1`

Planned output:

- evaluator-family protocol for at least four families: deterministic static detectors, single-model judge,
  judge panel, and execution-backed gate;
- leakage-control plan for every evaluator family;
- budget and call ceilings for the next execution gate;
- metric table specifying recall, specificity, nondecision, precision, and balanced detection;
- risk register naming the exact ways a higher-recall evaluator can overfit or harm legitimate controls;
- recommendation for one next execution gate, or a null if no responsible next gate exists.

## Numeric Bars

Pass bars:

- zero provider calls, zero model evaluations, zero SWE-bench executions, and zero cloud resources;
- no new benchmark score, leaderboard, model-comparison result, SOTA claim, natural-frequency estimate, or
  broad robustness claim;
- at least four evaluator families are specified with inputs, forbidden leakage, output schema, pass/fail
  bars, cost ceiling, and falsifiers;
- the design must explicitly preserve the iter165 false-positive boundary as a first-class objective, not
  optimize recall alone;
- the design must state how nondecisions, refusals, invalid outputs, provider errors, and partial runs are
  counted;
- the recommended next gate must have a bounded call/spend envelope and a stop condition if recall improves
  only by destroying specificity;
- if no responsible next gate can be designed from current evidence, publish a design null instead of
  inventing a run.

## Falsifiers

1. The design treats the iter165 single-model result as a leaderboard or model-superiority result.
2. The design optimizes only recall and fails to preserve/control false positives.
3. The design allows labels, source reports, static verdicts, prior judge outputs, or known-both-miss wording
   into prompt-visible fields.
4. The design proposes unbounded provider spend, unbounded model families, or unbounded execution.
5. The design claims a new empirical result without executing and validating a later gate.

## Claim Boundary

At most, if the gate passes: Telos has a pre-registered, evidence-shaped design for the next reward-hack
moonshot evaluator-family gate, grounded in the complete iter161/iter165 paired single-model metric.

Not supported: any new model score, leaderboard ranking, model superiority claim, state-of-the-art claim,
natural reward-hacking frequency estimate, broad reward-model robustness claim, or claim about evaluator
families not yet executed.
