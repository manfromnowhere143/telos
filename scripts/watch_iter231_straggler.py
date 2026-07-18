#!/usr/bin/env python3
"""Wall-clock straggler monitor for the iter231 sharded oracle run.

The lesson this encodes: on an earlier sharded run, ``sympy-19040`` hit a reproducible container
hang and burned roughly four hours before anyone noticed, because the run *looked* healthy --
shards were still "in progress" and the completed-shard count kept rising. Shard count is not a
liveness signal. Wall-clock elapsed against each job's ``startedAt`` is.

This polls the GitHub run and reports any in-progress shard whose elapsed wall clock exceeds the
threshold *while other shards have already finished* -- the exact signature of a hang rather than
of an ordinarily slow shard. It only observes: it never cancels, reruns, or mutates the run.

Usage:
    python3 scripts/watch_iter231_straggler.py --run-id 12345678
    python3 scripts/watch_iter231_straggler.py --run-id 12345678 --watch
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import subprocess
import time

WORKFLOW = "iter231-execute.yml"
# A shard past this while siblings have finished is the hang signature, not slowness. The executor's
# own per-row ceiling is 1200s, so a healthy shard's rows are individually bounded well under this.
DEFAULT_THRESHOLD_SECONDS = 20 * 60
DEFAULT_POLL_SECONDS = 120


def _gh_json(args: list[str]) -> object:
    try:
        out = subprocess.run(
            ["gh", *args], capture_output=True, text=True, check=True, timeout=120
        ).stdout
    except FileNotFoundError:
        raise SystemExit("gh CLI is required to observe the run")
    except subprocess.TimeoutExpired:
        raise SystemExit("gh call timed out")
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"gh call failed: {(exc.stderr or '').strip()[:300]}")
    try:
        return json.loads(out)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"gh returned unparseable JSON: {exc}")


def _github_now() -> datetime:
    """GitHub's clock, not this host's.

    ``startedAt`` is stamped in GitHub's clock domain, so elapsed must be measured against the same
    clock. Measured live on this host: GitHub ran ~65s ahead, which made every just-started job look
    like it began in the future and understated every elapsed time by that offset. Comparing
    timestamps across two clock domains is wrong even when the error is small enough not to matter
    against a 20-minute threshold. Falls back to local UTC if the header is unavailable.
    """

    try:
        out = subprocess.run(
            ["gh", "api", "rate_limit", "--include"],
            capture_output=True, text=True, check=True, timeout=60,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return datetime.now(timezone.utc)
    for line in out.splitlines():
        if line.lower().startswith("date:"):
            try:
                return parsedate_to_datetime(line.split(":", 1)[1].strip())
            except (TypeError, ValueError):
                break
        if not line.strip():
            break
    return datetime.now(timezone.utc)


def _elapsed_seconds(started_at: str, now: datetime) -> float | None:
    try:
        started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None
    return (now - started).total_seconds()


def poll_once(run_id: str, threshold: int) -> tuple[int, list[str]]:
    """Return (exit-worthy straggler count, human-readable report lines)."""

    data = _gh_json(
        ["run", "view", run_id, "--json", "jobs,status,conclusion"]
    )
    if not isinstance(data, dict):
        raise SystemExit("unexpected gh run payload")
    jobs = [job for job in data.get("jobs") or [] if isinstance(job, dict)]
    if not jobs:
        return 0, [f"run {run_id}: no jobs visible yet"]

    now = _github_now()
    running: list[tuple[str, float]] = []
    finished = 0
    unknown: list[str] = []
    skewed: list[str] = []
    for job in jobs:
        name = str(job.get("name", "?"))
        if job.get("status") == "completed":
            finished += 1
            continue
        elapsed = _elapsed_seconds(str(job.get("startedAt") or ""), now)
        # A queued job carries no start stamp, and GitHub may report a start stamp slightly in the
        # future relative to this host's clock. Observed live: not-yet-started shards reported
        # elapsed ~= -48s. Negative elapsed is not a measurement, so such a job is counted as not
        # started rather than silently entering the running set with a nonsense age.
        if elapsed is None:
            unknown.append(name)
            continue
        if elapsed < 0:
            # Counted separately, not merged into "not started". A shard that stays skewed poll
            # after poll means this host's clock is behind GitHub's, and a monitor that silently
            # buckets those can never flag a straggler -- the exact failure it exists to prevent.
            skewed.append(name)
            continue
        running.append((name, elapsed))

    lines = [
        f"run {run_id} [{data.get('status')}]: {finished} finished, {len(running)} running, "
        f"{len(unknown)} not started"
        + (f", {len(skewed)} clock-skewed" if skewed else "")
    ]
    stragglers = []
    for name, elapsed in sorted(running, key=lambda row: -row[1]):
        minutes = elapsed / 60
        # The hang signature requires a finished sibling: without one, every shard is simply young.
        flag = finished > 0 and elapsed > threshold
        lines.append(f"  {'STRAGGLER' if flag else 'ok       '} {minutes:6.1f}m  {name}")
        if flag:
            stragglers.append(name)
    if stragglers:
        lines.append(
            f"  {len(stragglers)} shard(s) past {threshold // 60}m while siblings finished: "
            "inspect for a reproducible container hang before trusting the run."
        )
    return len(stragglers), lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", help="run id; defaults to the latest dispatched run")
    parser.add_argument("--threshold-seconds", type=int, default=DEFAULT_THRESHOLD_SECONDS)
    parser.add_argument("--poll-seconds", type=int, default=DEFAULT_POLL_SECONDS)
    parser.add_argument(
        "--watch", action="store_true", help="poll until the run completes instead of once"
    )
    args = parser.parse_args()

    run_id = args.run_id
    if not run_id:
        rows = _gh_json(
            ["run", "list", "--workflow", WORKFLOW, "--event", "workflow_dispatch",
             "--limit", "1", "--json", "databaseId"]
        )
        if not isinstance(rows, list) or not rows:
            raise SystemExit(f"no dispatched {WORKFLOW} run found")
        run_id = str(rows[0]["databaseId"])

    while True:
        count, lines = poll_once(run_id, args.threshold_seconds)
        print("\n".join(lines), flush=True)
        if not args.watch:
            return 1 if count else 0
        status = _gh_json(["run", "view", run_id, "--json", "status"])
        if isinstance(status, dict) and status.get("status") == "completed":
            print(f"run {run_id} completed", flush=True)
            return 1 if count else 0
        time.sleep(max(30, args.poll_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
