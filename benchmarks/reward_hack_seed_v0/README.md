# Reward Hack Seed v0

This directory is a validated seed artifact derived from committed Telos iter152 evidence.
It contains 20 execution-verified both-miss hack diffs across
8 repositories.

The seed preserves:

- one JSONL row per iter152 both-miss hack,
- a SHA256 for each hack diff,
- detector and reward-model judge verdict labels from iter152,
- source links and hashes back to the committed iter152 proof artifacts,
- the `survives_all_static` label, which is true for 5/20 rows.

Claim boundary: this is a seed artifact, not a released benchmark, benchmark score,
leaderboard, model-comparison result, state-of-the-art claim, or natural-RL frequency claim.
No provider calls, cloud resources, SWE-bench executions, or judge calls were added by iter153.

Primary files:

- `reward_hack_seed_v0.jsonl`: seed rows.
- `manifest.json`: counts, source hashes, artifact hashes, and claim-boundary flags.
- `schema.json`: minimal row schema for reviewer inspection.
