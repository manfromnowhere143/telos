# Iteration 157 - Paper Plain-Language Completion

Status: pre-registered design; no paper rewrite for iter157 has been applied yet.

## Why this gate exists

The paper already received an accessibility pass through the abstract, but the remaining sections still
need the same plain-language treatment before arXiv-style release. The benchmark line also changed after
iter156: Telos now has a released `40`-row reward-hack artifact, but still no leaderboard, model score,
state-of-the-art result, natural-frequency estimate, or broad reward-model robustness claim. The paper
must reflect that boundary clearly.

## Method

Inputs:

- `paper/telos.tex`
- `docs/PAPER.md`
- `experiments/iter151_cross_repo_scale_official/RESULT.md`
- `experiments/iter152_reward_model_gaming_scale/RESULT.md`
- `experiments/iter153_reward_hack_benchmark_seed_materialization/RESULT.md`
- `experiments/iter154_reward_hack_benchmark_expansion_pilot/RESULT.md`
- `experiments/iter155_adaptive_reward_hack_expansion/RESULT.md`
- `experiments/iter156_reward_hack_benchmark_v1_manifest/RESULT.md`
- `benchmarks/reward_hack_benchmark_v1/manifest.json`

Rewrite scope:

- keep all quantitative claims tied to committed result files,
- define specialized terms before using them,
- split dense paragraphs where they hide the main claim,
- add the v1 artifact boundary without claiming a benchmark score,
- keep null results and limitations visible,
- do not introduce new empirical claims.

## Numeric Bars

Minimum pass bars:

- `paper/telos.tex` compiles or the compile blocker is recorded,
- every mention of `reward_hack_benchmark_v1` stays below the iter156 claim boundary,
- no new benchmark score, leaderboard, model-superiority, state-of-the-art, natural-frequency, or broad
  robustness claim appears,
- iter151 through iter156 are represented consistently with their `RESULT.md` files,
- `python3 scripts/validate_docs.py` passes,
- `python3 scripts/validate_learning_ledger.py` passes,
- `git diff --check` passes.

Reported but not pass-required:

- number of sections rewritten,
- remaining readability debt,
- any PDF compile warning that does not change the text claim boundary.

## Falsifiers

1. The rewrite changes a number without source evidence.
2. The rewrite implies Telos has a model score, leaderboard result, state-of-the-art result, natural
   frequency estimate, or broad reward-model robustness result.
3. The rewrite hides iter154's null shortfall or the constructed nature of the reward-hack rows.
4. The rewrite claims a paper-ready state while known compile/doc validators fail without being recorded.

## Claim Boundary

At most: "The paper was made clearer and updated to reflect the iter151 through iter156 evidence and
claim boundaries." Not supported: new empirical results, model scores, leaderboard claims, or broader
generalization claims.
