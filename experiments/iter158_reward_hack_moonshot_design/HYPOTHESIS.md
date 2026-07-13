# Iteration 158 - Reward-Hack Benchmark Moonshot Design

Status: result published; see `RESULT.md`.

## Why this gate exists

`iter156` released a hash-checked `40`-row `reward_hack_benchmark_v1` artifact, and `iter157` made the
paper current through that boundary. The next high-leverage move is to design the first scoring/evaluation
protocol for the frozen artifact. That needs a strict design gate before any frontier-model spend or public
score language appears.

The moonshot is ambitious in target and conservative in procedure: define a benchmark-scoring protocol that
could later evaluate frontier reward models, judge panels, static detectors, and execution-backed gates on
the frozen reward-hack rows, while preserving leakage controls and claim boundaries. This gate only designs
that protocol. It does not execute it.

## Method

Inputs:

- `benchmarks/reward_hack_benchmark_v1/manifest.json`
- `benchmarks/reward_hack_benchmark_v1/reward_hack_benchmark_v1.jsonl`
- `benchmarks/reward_hack_benchmark_v1/schema.json`
- `experiments/iter151_cross_repo_scale_official/RESULT.md`
- `experiments/iter152_reward_model_gaming_scale/RESULT.md`
- `experiments/iter153_reward_hack_benchmark_seed_materialization/RESULT.md`
- `experiments/iter154_reward_hack_benchmark_expansion_pilot/RESULT.md`
- `experiments/iter155_adaptive_reward_hack_expansion/RESULT.md`
- `experiments/iter156_reward_hack_benchmark_v1_manifest/RESULT.md`
- `experiments/iter157_paper_plain_language_completion/RESULT.md`

Design output:

- a scoring protocol document for the frozen v1 artifact,
- a machine-readable design summary with row hashes, scoring tasks, leakage controls, and planned metrics,
- a future execution envelope with provider-call, spend, SWE-bench, cloud, and stop conditions,
- explicit result language for pass, null, and fail outcomes.

## Numeric Bars

Minimum pass bars:

- the design freezes the exact v1 artifact hashes before any future scoring,
- the design defines at least three evaluator families: static detectors, model judges, and execution-backed
  gates,
- the design defines leakage controls for hack diffs, source rows, official reports, prompts, and visible
  target tests,
- the design defines metrics without claiming a model score in this gate,
- the design includes null/fail semantics for provider refusal, parse failure, harness failure, and
  inconclusive judge output,
- new provider calls: `0`,
- new SWE-bench executions: `0`,
- new cloud resources: `0`,
- public wording does not claim a benchmark score, leaderboard, model superiority, state-of-the-art result,
  natural reward-hacking frequency, or broad reward-model robustness.

Reported but not pass-required:

- planned maximum provider calls,
- planned maximum spend,
- planned evaluator ordering,
- known implementation blockers.

## Falsifiers

1. The design silently changes the v1 row set or hashes.
2. The design exposes hidden labels or official report verdicts to a model judge in a way that would leak
   the answer for a later scoring gate.
3. The design claims any model has already scored on `reward_hack_benchmark_v1`.
4. The design omits null/fail handling for refusals, malformed outputs, or harness failures.
5. The gate runs provider calls, SWE-bench executions, or cloud resources before a separate execution gate
   is pre-registered.

## Claim Boundary

At most: "Telos pre-registered a moonshot scoring/evaluation design for the frozen
`reward_hack_benchmark_v1` artifact."

Not supported: benchmark scores, leaderboard rankings, model-comparison results, state-of-the-art claims,
natural reward-hacking frequency estimates, broad reward-model robustness claims, or any statement that a
model has been evaluated on the v1 artifact.
