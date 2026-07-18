#!/usr/bin/env python3
"""Collect and verify the eight iter232 oracle shards into one execution directory.

Accepts evidence only when the eight shards form an exact, disjoint partition of the frozen 67-row
benchmark and all come from a single run attempt. A mixed-attempt bundle fails closed: rerunning
only the failed shards would silently mix evidence from two executor states, which is precisely how
a run can look complete while resting on inconsistent provenance.

``ingest`` merges a downloaded bundle into the execution directory; ``check`` re-verifies a
committed directory offline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/iter232_validated_exercise_instrument"
EVAL_SET = ROOT / "experiments/iter230_gold_free_detector_natural/proof/raw/eval_set.json"
EXERCISES = EXP / "proof/raw/exercises/exercises_summary.json"
EXECUTION = EXP / "proof/raw/execution"
RECEIPT = EXECUTION / "_iter232_execution_complete.receipt.json"

FROZEN_EVAL_SET_SHA256 = "10dc898c3cdc6026aaedc57d469e546b279a982df3772ba3388c1dfb515b8928"
SHARD_COUNT = 8
BENCHMARK_ROWS = 67
PROGRESS_RE = re.compile(r"^_shard-(\d+)-of-(\d+)\.progress\.json$")


def expected_stems() -> list[str]:
    """The ordered 67 stems, in the same order the executor assigns ordinals."""

    raw = EVAL_SET.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN_EVAL_SET_SHA256:
        raise SystemExit("frozen iter230 benchmark sha changed; collection may not proceed")
    data = json.loads(raw)
    items = data["positives"] + data["negatives"]
    if len(items) != BENCHMARK_ROWS:
        raise SystemExit(f"benchmark is not the frozen {BENCHMARK_ROWS} rows")
    return [f"{row['run']}__{row['instance_id'].replace('/', '__')}" for row in items]


def verify(directory: Path) -> tuple[list[str], dict]:
    """Return (errors, summary). The partition must be exact, disjoint, and single-attempt."""

    errors: list[str] = []
    stems = expected_stems()
    statuses = {
        (row["run"], row["instance_id"]): row["status"]
        for row in json.loads(EXERCISES.read_text())["manifest"]
    }
    status_by_stem = {
        f"{run}__{iid.replace('/', '__')}": status for (run, iid), status in statuses.items()
    }

    logs = {path.name[: -len(".oracle.log")] for path in directory.glob("*.oracle.log")}
    missing = [stem for stem in stems if stem not in logs]
    extra = sorted(logs - set(stems))
    if missing:
        errors.append(f"{len(missing)} benchmark row(s) have no oracle log: {missing[:5]}")
    if extra:
        errors.append(f"unexpected oracle log(s) not in the benchmark: {extra[:5]}")

    progress = sorted(directory.glob("_shard-*.progress.json"))
    seen_shards: set[int] = set()
    for path in progress:
        match = PROGRESS_RE.match(path.name)
        if not match or int(match.group(2)) != SHARD_COUNT:
            errors.append(f"malformed shard progress file: {path.name}")
            continue
        index = int(match.group(1))
        if index in seen_shards:
            errors.append(f"duplicate shard progress for shard {index}")
        seen_shards.add(index)
        payload = json.loads(path.read_text())
        if payload.get("schema_version") != "telos.iter232.shard_progress.v1":
            errors.append(f"shard {index} progress schema mismatch")
        if payload.get("phase") != "finished":
            errors.append(f"shard {index} did not reach the finished phase")
    if seen_shards != set(range(SHARD_COUNT)):
        errors.append(
            f"shard partition incomplete: have {sorted(seen_shards)}, need 0..{SHARD_COUNT - 1}"
        )

    executed = 0
    not_executed = 0
    for stem in stems:
        path = directory / f"{stem}.oracle.log"
        if not path.is_file():
            continue
        text = path.read_text(errors="replace")
        status = status_by_stem.get(stem)
        if status != "exercise":
            if f"NOT_EXECUTED status={status}" not in text:
                errors.append(f"{stem}: expected a NOT_EXECUTED marker for status {status}")
            not_executed += 1
            continue
        executed += 1
        if "APPLY_OK candidate" not in text:
            errors.append(f"{stem}: no candidate apply marker")
        if not re.search(r"^EXERCISE_EXIT=\d+$", text, re.MULTILINE):
            errors.append(f"{stem}: no explicit exercise exit code")
        if not re.search(r"^PREFLIGHT=", text, re.MULTILINE):
            errors.append(f"{stem}: no stage B preflight verdict")

    return errors, {
        "rows": len(stems),
        "executed": executed,
        "not_executed": not_executed,
        "shards": sorted(seen_shards),
    }


def ingest(bundle_dir: Path, run_id: str, run_attempt: str, head_sha: str) -> int:
    staging = EXECUTION.parent / "_execution_staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    # Shard artifacts download into per-artifact subdirectories; flatten, refusing any collision so
    # two shards cannot silently overwrite each other's evidence.
    for path in sorted(bundle_dir.rglob("*")):
        if not path.is_file():
            continue
        target = staging / path.name
        if target.exists():
            print(f"duplicate evidence file across shards: {path.name}", file=sys.stderr)
            return 2
        shutil.copy2(path, target)

    errors, summary = verify(staging)
    if errors:
        for error in errors:
            print(f"iter232 collection error: {error}", file=sys.stderr)
        return 1

    if EXECUTION.exists():
        shutil.rmtree(EXECUTION)
    staging.rename(EXECUTION)

    digest = hashlib.sha256()
    for path in sorted(EXECUTION.glob("*.oracle.log")):
        digest.update(f"{path.name}\0".encode())
        digest.update(path.read_bytes())
    RECEIPT.write_text(
        json.dumps(
            {
                "schema_version": "telos.iter232.execution_receipt.v1",
                "eval_set_sha256": FROZEN_EVAL_SET_SHA256,
                "github_run_id": run_id,
                "github_run_attempt": run_attempt,
                "github_sha": head_sha,
                "oracle_log_corpus_sha256": digest.hexdigest(),
                **summary,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(
        f"iter232 execution ingested: {summary['executed']} executed, "
        f"{summary['not_executed']} not executed, {summary['rows']} rows, shards {summary['shards']}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    ing = sub.add_parser("ingest")
    ing.add_argument("--bundle-dir", type=Path, required=True)
    ing.add_argument("--expected-run-id", required=True)
    ing.add_argument("--expected-run-attempt", required=True)
    ing.add_argument("--expected-github-sha", required=True)
    sub.add_parser("check")
    args = parser.parse_args()

    if args.command == "ingest":
        return ingest(
            args.bundle_dir,
            args.expected_run_id,
            args.expected_run_attempt,
            args.expected_github_sha,
        )

    if not EXECUTION.is_dir():
        print("iter232 execution directory is not committed", file=sys.stderr)
        return 1
    errors, summary = verify(EXECUTION)
    if not RECEIPT.is_file():
        errors.append("execution receipt is missing")
    else:
        receipt = json.loads(RECEIPT.read_text())
        digest = hashlib.sha256()
        for path in sorted(EXECUTION.glob("*.oracle.log")):
            digest.update(f"{path.name}\0".encode())
            digest.update(path.read_bytes())
        if receipt.get("oracle_log_corpus_sha256") != digest.hexdigest():
            errors.append("oracle log corpus hash does not match the receipt")
    if errors:
        for error in errors:
            print(f"iter232 collection error: {error}", file=sys.stderr)
        return 1
    print(
        f"iter232 execution evidence complete: {summary['executed']} executed, "
        f"{summary['not_executed']} not executed, shards {summary['shards']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
