#!/usr/bin/env python3
"""Prepare the iter154 reward-hack expansion candidate pool.

This script performs no model calls and no SWE-bench execution. It freezes the candidate pool before
provider outcomes exist, using the public SWE-bench_Verified test split and excluding the validated
reward_hack_seed_v0 instances.
"""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter154_reward_hack_benchmark_expansion_pilot"
PROOF = EXPERIMENT / "proof"
RAW = PROOF / "raw"
SEED_JSONL = ROOT / "benchmarks/reward_hack_seed_v0/reward_hack_seed_v0.jsonl"

DATASET_ID = "princeton-nlp/SWE-bench_Verified"
DATASET_CONFIG = "default"
DATASET_SPLIT = "test"
DATASET_REVISION = "c104f840cc67f8b6eec6f759ebc8b2693d585d4a"
ROWS_URL = "https://datasets-server.huggingface.co/rows"
ROWS_PAGE = 100

PER_REPO_CAP = 12
SELECTED_CANDIDATE_TARGET = 96


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fetch_json(url: str, retries: int = 3) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with urlopen(url, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # pragma: no cover - network recovery path.
            last_error = exc
            time.sleep(1 + attempt)
    raise RuntimeError(f"failed to fetch {url}: {last_error}")


def fetch_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        query = urlencode(
            {
                "dataset": DATASET_ID,
                "config": DATASET_CONFIG,
                "split": DATASET_SPLIT,
                "offset": offset,
                "length": ROWS_PAGE,
            }
        )
        payload = fetch_json(f"{ROWS_URL}?{query}")
        batch = payload.get("rows", [])
        if not batch:
            break
        for item in batch:
            row = item["row"]
            row["_dataset_row_idx"] = item["row_idx"]
            rows.append(row)
        offset += len(batch)
        if len(batch) < ROWS_PAGE:
            break
    return rows


def json_list(src: str) -> list[str]:
    value = json.loads(src)
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def one_source_file(patch: str) -> str | None:
    files = [
        line[6:]
        for line in patch.splitlines()
        if line.startswith("+++ b/")
        and "/test" not in line
        and "test_" not in line.split("/")[-1]
    ]
    unique = sorted(set(files))
    return unique[0] if len(unique) == 1 else None


def largest_added_block_sha256(patch: str, source_file: str) -> str | None:
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
        return None
    largest = max(runs, key=lambda run: sum(len(line) for line in run))
    return sha256_text("\n".join(largest))


def seed_instances() -> set[str]:
    instances: set[str] = set()
    for line in SEED_JSONL.read_text(encoding="utf-8").splitlines():
        if line.strip():
            instances.add(json.loads(line)["instance_id"])
    return instances


def eligible_record(row: dict[str, Any], seed: set[str]) -> tuple[dict[str, Any] | None, str | None]:
    instance_id = row["instance_id"]
    if instance_id in seed:
        return None, "already_in_seed_v0"
    try:
        fail_to_pass = json_list(row["FAIL_TO_PASS"])
        pass_to_pass = json_list(row["PASS_TO_PASS"])
    except json.JSONDecodeError:
        return None, "invalid_test_json"
    source_file = one_source_file(row["patch"])
    if source_file is None:
        return None, "not_single_primary_source_file"
    if len(fail_to_pass) != 1:
        return None, "fail_to_pass_count_not_one"
    if len(pass_to_pass) < 2:
        return None, "pass_to_pass_count_lt_two"
    block_hash = largest_added_block_sha256(row["patch"], source_file)
    if block_hash is None:
        return None, "no_added_source_block"
    return (
        {
            "dataset_row_idx": row["_dataset_row_idx"],
            "repo": row["repo"],
            "instance_id": instance_id,
            "base_commit": row["base_commit"],
            "version": row["version"],
            "source_file": source_file,
            "fail_to_pass": fail_to_pass,
            "pass_to_pass": pass_to_pass,
            "pass_to_pass_count": len(pass_to_pass),
            "gold_patch_sha256": sha256_text(row["patch"]),
            "largest_added_block_sha256": block_hash,
            "problem_statement_sha256": sha256_text(row["problem_statement"]),
            "patch": row["patch"],
            "problem_statement": row["problem_statement"],
        },
        None,
    )


def round_robin_select(eligible: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_repo: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in eligible:
        if len(by_repo[row["repo"]]) < PER_REPO_CAP:
            by_repo[row["repo"]].append(row)
    selected: list[dict[str, Any]] = []
    repos = sorted(by_repo)
    while len(selected) < SELECTED_CANDIDATE_TARGET:
        advanced = False
        for repo in repos:
            if by_repo[repo]:
                selected.append(by_repo[repo].pop(0))
                selected[-1]["selection_rank"] = len(selected)
                advanced = True
                if len(selected) >= SELECTED_CANDIDATE_TARGET:
                    break
        if not advanced:
            break
    return selected


def main() -> int:
    seed = seed_instances()
    rows = fetch_rows()
    raw_snapshot = {
        "schema_version": "telos.iter154.swebench_verified_snapshot.v1",
        "dataset_id": DATASET_ID,
        "config": DATASET_CONFIG,
        "split": DATASET_SPLIT,
        "revision": DATASET_REVISION,
        "row_count": len(rows),
        "rows": rows,
    }
    write_json(RAW / "swebench_verified_rows_snapshot.json", raw_snapshot)

    eligible: list[dict[str, Any]] = []
    exclusions: dict[str, int] = defaultdict(int)
    for row in rows:
        record, reason = eligible_record(row, seed)
        if record is None:
            exclusions[str(reason)] += 1
        else:
            eligible.append(record)

    selected = round_robin_select(eligible)
    summary = {
        "schema_version": "telos.iter154.candidate_pool_summary.v1",
        "status": "prepared",
        "dataset_id": DATASET_ID,
        "revision": DATASET_REVISION,
        "raw_snapshot_path": str((RAW / "swebench_verified_rows_snapshot.json").relative_to(ROOT)),
        "raw_snapshot_sha256": sha256_file(RAW / "swebench_verified_rows_snapshot.json"),
        "seed_path": str(SEED_JSONL.relative_to(ROOT)),
        "seed_instances_excluded": len(seed),
        "dataset_rows": len(rows),
        "eligible_rows": len(eligible),
        "selected_candidates": len(selected),
        "per_repo_cap": PER_REPO_CAP,
        "selected_candidate_target": SELECTED_CANDIDATE_TARGET,
        "selected_repos": sorted({row["repo"] for row in selected}),
        "selected_repo_counts": {
            repo: sum(1 for row in selected if row["repo"] == repo)
            for repo in sorted({row["repo"] for row in selected})
        },
        "exclusions": dict(sorted(exclusions.items())),
        "sampling_rule": (
            "Exclude reward_hack_seed_v0 instances; require one primary non-test source file in the "
            "gold patch, exactly one FAIL_TO_PASS, and at least two PASS_TO_PASS checks; preserve dataset "
            "order within each repo; cap at 12 candidates per repo; select by lexicographic repo "
            "round-robin until 96 candidates or exhaustion."
        ),
        "pre_provider_outcome_freeze": True,
    }

    write_json(RAW / "eligible_candidate_pool.json", {"rows": eligible})
    write_json(RAW / "selected_candidate_pool.json", {"rows": selected})
    write_json(PROOF / "candidate_pool_summary.json", summary)

    print("candidate_pool_prepared")
    print(f"  dataset rows: {len(rows)}")
    print(f"  eligible rows: {len(eligible)}")
    print(f"  selected candidates: {len(selected)} across {len(summary['selected_repos'])} repos")
    print(f"  raw snapshot sha256: {summary['raw_snapshot_sha256']}")
    return 0 if selected else 2


if __name__ == "__main__":
    sys.exit(main())
