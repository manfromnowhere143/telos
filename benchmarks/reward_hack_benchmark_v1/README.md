# Reward Hack Benchmark v1

> **CORRECTION (iter192): the name of this artifact is wrong. These rows are not reward hacks.**
>
> A reward hack scores well on the reward function while being wrong. Every row here **fails** the
> reward function. The generator
> (`experiments/iter152_reward_model_gaming_scale/proof/raw/detection_pipeline.py`, line 132) admitted a
> row only when the target test passed **and at least one `PASS_TO_PASS` test failed** — `PASS_TO_PASS`
> being the repository's own existing test suite. Verified from committed tarballs at zero spend:
> `40/40` rows are marked `resolved: false` by the official SWE-bench harness and `40/40` have at least
> one failing `PASS_TO_PASS` test.
>
> **What this artifact actually is:** 40 subtly-wrong patches that break the existing test suite and
> that a deterministic detector and LLM judges failed to spot by reading the diff. `both_miss` means the
> *detector and judge* miss. It never meant the tests miss.
>
> **Baseline you must cite alongside any figure from this artifact:** the official SWE-bench harness
> verdict — equivalently, running the existing test suite — detects `40/40` at `$0.00`. The three-model
> panel's unrepaired iter179 `majority_catch` detects `17/40` at `$13.59`.
>
> See `experiments/iter192_reward_hack_benchmark_construct_validity_audit/RESULT.md`. The successor
> artifact targeting the genuine class is pre-registered at
> `experiments/iter193_certified_resolved_reward_hack_construction/HYPOTHESIS.md`.

## Construction properties a reviewer should know

These were never previously documented and both bear on how figures from this artifact read:

- **Matched-pair derivation (a strength, and accidental).** Each hack row is the *gold patch* with its
  largest added `+` run substituted (`build_variant`), hunk arithmetic repaired, everything else retained
  byte-for-byte. Hack and paired control therefore share file set, hunk anchors, and context lines. This
  is why the `0/40` control false-positive rate in iter165/iter179 is **not** a provenance or style
  artifact: the classes are matched by construction and stylistic separability is at chance. That
  property is real and load-bearing, and it was never stated until iter192.
- **Test files are excluded by filter (a construct limit).** `one_src` drops any path matching `/test`
  or `test_`, so **no row can edit a test, weaken an assertion, or touch test config** — measured `0/40`.
  The judge rubric names those three cues as three of its four definitions of a hack, so the judges were
  instructed to hunt for evidence that cannot exist in any positive row. Recall figures from this
  artifact must be read with that mis-specification in mind.

## Original description (retained; framing superseded above)

This directory is a hash-checked Telos benchmark artifact containing 40 constructed,
execution-verified both-miss rows.

Sources:

- 20 rows from `benchmarks/reward_hack_seed_v0/`
- 17 rows from `experiments/iter154_reward_hack_benchmark_expansion_pilot`
- 3 rows from `experiments/iter155_adaptive_reward_hack_expansion`

Each row preserves:

- the hack diff and hack diff SHA256,
- the official SWE-bench report hash,
- the source experiment and source row hash,
- deterministic detector, `gpt-5.6-terra`, and `claude-opus-4-8` static labels,
- the `survives_all_static` label.

Claim boundary: this is a benchmark artifact, not a benchmark score, leaderboard,
model-comparison result, state-of-the-art claim, broad reward-model robustness claim, or
natural reward-hacking frequency claim.

Primary files:

- `reward_hack_benchmark_v1.jsonl`: 40 normalized rows.
- `manifest.json`: counts, source hashes, artifact hashes, and claim-boundary flags.
- `schema.json`: minimal row schema for reviewer inspection.
