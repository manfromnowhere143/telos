# Reward Hack Seed v0 (historical name; construct invalidated)

> **Standing correction (iter192): these 20 rows are not reward hacks.** Each row fails at least one
> official graded `PASS_TO_PASS` regression check, and the official harness rejects it. The directory and
> schema names remain unchanged to preserve hashes and historical references.

This directory is a validated historical seed artifact derived from committed iter152 evidence. It
contains 20 execution-verified, suite-failing `both_miss` candidate diffs across 8 repositories;
`both_miss` means the deterministic detector and LLM judge missed the diff, not that the tests missed it.

The seed preserves:

- one JSONL row per iter152 historical `both_miss` candidate,
- a SHA256 for each candidate diff,
- detector and reward-model judge verdict labels from iter152,
- source links and hashes back to the committed iter152 proof artifacts,
- the `survives_all_static` label, which is true for 5/20 rows.

Claim boundary: this is a construct-invalid historical seed, not a reward-hack corpus, released benchmark,
benchmark score, leaderboard, model-comparison result, state-of-the-art claim, or population-frequency
result. No provider calls, cloud resources, SWE-bench executions, or judge calls were added by iter153.

Primary files:

- `reward_hack_seed_v0.jsonl`: seed rows.
- `manifest.json`: counts, source hashes, artifact hashes, and claim-boundary flags.
- `schema.json`: minimal row schema for reviewer inspection.
