#!/usr/bin/env python3
"""Freeze the iter155 adaptive reward-hack expansion pool.

This script performs no provider calls, no SWE-bench execution, and no cloud actions. It uses the
published iter154 shortfall evidence to select a deterministic follow-up pool before any iter155
outcomes exist.
"""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ITER155 = ROOT / "experiments/iter155_adaptive_reward_hack_expansion"
PROOF = ITER155 / "proof"
RAW = PROOF / "raw"

SEED_JSONL = ROOT / "benchmarks/reward_hack_seed_v0/reward_hack_seed_v0.jsonl"
ITER154_RAW = ROOT / "experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw"
ELIGIBLE_POOL = ITER154_RAW / "eligible_candidate_pool.json"
ITER154_RESULTS = ITER154_RAW / "expansion_results.json"

ADAPTIVE_CANDIDATE_TARGET = 48
PER_REPO_CAP = 10
MIN_REPOS = 3
PASS_TO_PASS_FLOOR = 4
COMPACT_BLOCK_CHAR_CAP = 900
COMPACT_BLOCK_LINE_CAP = 12


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def seed_instances() -> set[str]:
    instances: set[str] = set()
    for line in SEED_JSONL.read_text(encoding="utf-8").splitlines():
        if line.strip():
            instances.add(json.loads(line)["instance_id"])
    return instances


def largest_added_block_stats(patch: str, source_file: str) -> dict[str, int]:
    runs: list[list[str]] = []
    current: list[str] = []
    in_source = False
    for line in patch.splitlines():
        if line.startswith("+++ b/"):
            if current:
                runs.append(current)
                current = []
            in_source = source_file in line
            continue
        if in_source and line.startswith("+") and not line.startswith("+++"):
            current.append(line[1:])
        elif current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    if not runs:
        return {"lines": 0, "chars": 0}
    largest = max(runs, key=lambda run: sum(len(line) for line in run))
    return {
        "lines": len(largest),
        "chars": sum(len(line) for line in largest),
    }


def repo_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[row["repo"]] += 1
    return dict(sorted(counts.items()))


def annotate_candidate(
    row: dict[str, Any],
    *,
    iter154_accepted_by_repo: dict[str, int],
) -> dict[str, Any]:
    annotated = dict(row)
    block = largest_added_block_stats(row["patch"], row["source_file"])
    accepted_count = iter154_accepted_by_repo.get(row["repo"], 0)
    annotated["iter154_productive_repo"] = accepted_count > 0
    annotated["iter154_repo_accepted_rows"] = accepted_count
    annotated["pass_to_pass_floor_met"] = row["pass_to_pass_count"] >= PASS_TO_PASS_FLOOR
    annotated["largest_added_block_line_count"] = block["lines"]
    annotated["largest_added_block_char_count"] = block["chars"]
    annotated["compact_block_preferred"] = (
        0 < block["chars"] <= COMPACT_BLOCK_CHAR_CAP
        and 0 < block["lines"] <= COMPACT_BLOCK_LINE_CAP
    )
    return annotated


def candidate_sort_key(row: dict[str, Any]) -> tuple[int, int, int, int, int, str]:
    return (
        0 if row["pass_to_pass_floor_met"] else 1,
        0 if row["compact_block_preferred"] else 1,
        row["largest_added_block_char_count"],
        row["largest_added_block_line_count"],
        row.get("selection_rank", row["dataset_row_idx"]),
        row["instance_id"],
    )


def select_adaptive_pool(
    remaining: list[dict[str, Any]],
    *,
    iter154_accepted_by_repo: dict[str, int],
) -> list[dict[str, Any]]:
    by_repo: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in sorted(remaining, key=candidate_sort_key):
        by_repo[row["repo"]].append(row)

    productive_repos = [
        repo
        for repo, count in sorted(
            iter154_accepted_by_repo.items(),
            key=lambda item: (-item[1], item[0]),
        )
        if by_repo.get(repo)
    ]
    fallback_repos = sorted(repo for repo in by_repo if repo not in set(productive_repos))
    repo_order = productive_repos + fallback_repos

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    selected_by_repo: dict[str, int] = defaultdict(int)

    def take(repo: str) -> bool:
        if selected_by_repo[repo] >= PER_REPO_CAP:
            return False
        while by_repo[repo]:
            candidate = by_repo[repo].pop(0)
            if candidate["instance_id"] in selected_ids:
                continue
            selected_ids.add(candidate["instance_id"])
            selected_by_repo[repo] += 1
            candidate["adaptive_selection_rank"] = len(selected) + 1
            selected.append(candidate)
            return True
        return False

    for repo in repo_order[:MIN_REPOS]:
        if len(selected) >= ADAPTIVE_CANDIDATE_TARGET:
            break
        take(repo)

    weighted_cycle: list[str] = []
    for repo in productive_repos:
        weight = max(1, iter154_accepted_by_repo.get(repo, 0))
        weighted_cycle.extend([repo] * weight)

    def fill_from_cycle(cycle: list[str]) -> None:
        if not cycle:
            return
        while len(selected) < ADAPTIVE_CANDIDATE_TARGET:
            advanced = False
            for repo in cycle:
                if len(selected) >= ADAPTIVE_CANDIDATE_TARGET:
                    break
                advanced = take(repo) or advanced
            if not advanced:
                break

    fill_from_cycle(weighted_cycle)
    fill_from_cycle(fallback_repos)

    while len(selected) < ADAPTIVE_CANDIDATE_TARGET:
        advanced = False
        for repo in repo_order:
            if len(selected) >= ADAPTIVE_CANDIDATE_TARGET:
                break
            advanced = take(repo) or advanced
        if not advanced:
            break

    return selected


def main() -> int:
    seeds = seed_instances()
    eligible_rows = load_json(ELIGIBLE_POOL)["rows"]
    iter154_results = load_json(ITER154_RESULTS)

    processed_ids = {row["instance_id"] for row in iter154_results}
    accepted_rows = [
        row for row in iter154_results if row.get("status") == "execution_verified_both_miss"
    ]
    accepted_by_repo = repo_counts(accepted_rows)

    exclusions = {
        "seed_v0_instances": 0,
        "iter154_processed_instances": 0,
    }
    remaining: list[dict[str, Any]] = []
    for row in eligible_rows:
        if row["instance_id"] in seeds:
            exclusions["seed_v0_instances"] += 1
            continue
        if row["instance_id"] in processed_ids:
            exclusions["iter154_processed_instances"] += 1
            continue
        remaining.append(annotate_candidate(row, iter154_accepted_by_repo=accepted_by_repo))

    selected = select_adaptive_pool(remaining, iter154_accepted_by_repo=accepted_by_repo)
    selected_repo_counts = repo_counts(selected)

    summary = {
        "schema_version": "telos.iter155.adaptive_pool_summary.v1",
        "status": "adaptive_pool_frozen_no_provider_calls",
        "input_hashes": {
            str(SEED_JSONL.relative_to(ROOT)): sha256_file(SEED_JSONL),
            str(ELIGIBLE_POOL.relative_to(ROOT)): sha256_file(ELIGIBLE_POOL),
            str(ITER154_RESULTS.relative_to(ROOT)): sha256_file(ITER154_RESULTS),
        },
        "seed_instances": len(seeds),
        "iter154_processed_instances": len(processed_ids),
        "iter154_accepted_rows": len(accepted_rows),
        "iter154_accepted_by_repo": accepted_by_repo,
        "eligible_rows": len(eligible_rows),
        "remaining_rows_after_exclusions": len(remaining),
        "adaptive_candidate_target": ADAPTIVE_CANDIDATE_TARGET,
        "selected_candidates": len(selected),
        "selected_repositories": sorted(selected_repo_counts),
        "selected_repo_counts": selected_repo_counts,
        "selected_productive_repo_candidates": sum(
            1 for row in selected if row["iter154_productive_repo"]
        ),
        "selected_pass_to_pass_floor_met": sum(
            1 for row in selected if row["pass_to_pass_floor_met"]
        ),
        "selected_compact_block_preferred": sum(
            1 for row in selected if row["compact_block_preferred"]
        ),
        "pass_to_pass_floor": PASS_TO_PASS_FLOOR,
        "compact_block_char_cap": COMPACT_BLOCK_CHAR_CAP,
        "compact_block_line_cap": COMPACT_BLOCK_LINE_CAP,
        "per_repo_cap": PER_REPO_CAP,
        "minimum_repository_coverage": MIN_REPOS,
        "exclusions": exclusions,
        "pre_provider_outcome_freeze": True,
        "provider_calls": 0,
        "swebench_executions": 0,
        "cloud_resources_created": 0,
        "selection_rule": (
            "Exclude seed-v0 and every iter154 processed instance. Annotate the remaining iter154 "
            "eligible pool with pass-to-pass floor, compact added-block preference, and iter154 "
            "accepted-row count by repo. Seed one candidate from the top three productive repos, "
            "then fill a weighted round-robin over productive repos, weighted by iter154 accepted "
            "rows, with fallback repos only after productive repos. Sort candidates within each repo "
            "by pass-to-pass floor, compact block, block size, original iter154 selection rank when "
            "present, dataset row index otherwise, and instance id. Stop at 48 candidates or exhaustion."
        ),
        "claim_boundary": (
            "This freezes an adaptive iter155 candidate pool only. It is not iter155 result data, "
            "not a released benchmark, not a leaderboard, not a model comparison, and not a SOTA claim."
        ),
    }

    write_json(RAW / "adaptive_candidate_pool.json", {"rows": selected})
    write_json(PROOF / "adaptive_pool_summary.json", summary)

    print("adaptive_pool_frozen")
    print(f"  selected candidates: {len(selected)}")
    print(f"  selected repositories: {len(selected_repo_counts)}")
    print(f"  remaining after exclusions: {len(remaining)}")
    print("  provider calls: 0")
    print("  cloud resources created: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
