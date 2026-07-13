#!/usr/bin/env python3
"""Iter155 remote runner wrapper for the frozen adaptive reward-hack expansion pool."""

from __future__ import annotations

import os

os.environ.setdefault(
    "TELOS_EXPANSION_EXPERIMENT",
    "experiments/iter155_adaptive_reward_hack_expansion",
)
os.environ.setdefault(
    "TELOS_SELECTED_POOL",
    "experiments/iter155_adaptive_reward_hack_expansion/proof/raw/adaptive_candidate_pool.json",
)
os.environ.setdefault("TELOS_RUN_ID_PREFIX", "iter155")
os.environ.setdefault("TELOS_RESULT_SCHEMA_VERSION", "telos.iter155.expansion_result_row.v1")
os.environ.setdefault("TELOS_METRICS_SCHEMA_VERSION", "telos.iter155.expansion_metrics.v1")
os.environ.setdefault(
    "TELOS_CLAIM_BOUNDARY",
    (
        "Constructed execution-verified both-miss row from iter155 adaptive expansion; not a "
        "released benchmark score, leaderboard, model-superiority result, SOTA claim, broad "
        "reward-model robustness claim, or natural-RL frequency claim."
    ),
)
os.environ.setdefault("TARGET_NEW_BOTH_MISS", "3")
os.environ.setdefault("CANDIDATE_LIMIT", "48")

from run_reward_hack_expansion_remote import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
