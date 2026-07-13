# Reward Hack Benchmark v1

This directory is a hash-checked Telos benchmark artifact containing 40 constructed,
execution-verified both-miss reward-hack rows.

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
