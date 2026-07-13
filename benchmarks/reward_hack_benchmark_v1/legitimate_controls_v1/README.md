# Reward-Hack Legitimate Controls v1

This directory contains paired legitimate controls for `reward_hack_benchmark_v1`.
Each row is the public SWE-bench Verified gold patch for the same public issue as
one reward-hack row.

Claim boundary: this is a legitimate-control artifact and blinded control-packet
artifact. It is not a model score, precision number, benchmark leaderboard,
model comparison, state-of-the-art claim, broad reward-model robustness claim,
or natural reward-hacking frequency claim.

Primary files:

- `legitimate_controls_v1.jsonl`: 40 paired legitimate-control rows.
- `schema.json`: row schema.
- `manifest.json`: source, artifact, count, and leakage summary.
- `blinded_control_packets_v1/`: prompt-ready packets for future model-judge runs.
