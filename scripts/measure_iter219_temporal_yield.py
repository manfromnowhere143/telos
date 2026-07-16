#!/usr/bin/env python3
"""Measure the iter219 temporal consequence-test yield.

Frozen gate: ``experiments/iter219_temporal_consequence_test_yield/HYPOTHESIS.md``.

The instrument answers one pre-registered question: for a task frozen at repository
commit ``T``, do test functions added within ``delta`` days after ``T`` statically
reference the source symbols that the task's gold patch modified, at a yield above a
matched permutation control?

It performs read-only public dataset retrieval, read-only repository clones pinned to
recorded head SHAs, and local deterministic static analysis.  It makes no provider or
model request, allocates no accelerator, builds no container, and never executes a
cloned repository's test suite.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
import time
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from telos.tcp1 import exact_one_sided_mcnemar, wilson_interval  # noqa: E402

DATASET = "princeton-nlp/SWE-bench_Verified"
DATASET_SPLIT = "test"
ROWS_ENDPOINT = "https://datasets-server.huggingface.co/rows"
PERMUTATION_SALT = "telos-iter219-permutation-v1:"
DELTAS_DAYS = (90, 180, 365, 730)
PRIMARY_DELTA = 365

IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@")


# --------------------------------------------------------------------------- #
# Frozen path convention
# --------------------------------------------------------------------------- #


def is_test_path(path: str) -> bool:
    """Frozen test-path convention, applied identically to every repository."""

    parts = path.split("/")
    name = parts[-1]
    if not name.endswith(".py"):
        return False
    if name == "conftest.py":
        return True
    if name.startswith("test_") or name.endswith("_test.py"):
        return True
    return any(part in {"test", "tests", "testing"} for part in parts[:-1])


def is_source_path(path: str) -> bool:
    return path.endswith(".py") and not is_test_path(path)


# --------------------------------------------------------------------------- #
# Git helpers (read-only)
# --------------------------------------------------------------------------- #


def git(repo_dir: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_dir), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()[:300]}")
    return result.stdout


def git_ok(repo_dir: Path, *args: str) -> bool:
    return (
        subprocess.run(
            ["git", "-C", str(repo_dir), *args],
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )


class BlobReader:
    """Persistent ``git cat-file --batch`` reader with an OID-keyed parse cache.

    Spawning one ``git show`` per blob costs more in process setup than in work, and the
    same test file blob is re-read by many instances in the same repository.  Reading over
    one long-lived pipe and caching parsed results by blob OID makes the full cohort
    tractable.  Neither changes any measured value.
    """

    def __init__(self, repo_dir: Path) -> None:
        self.repo_dir = repo_dir
        self.proc = subprocess.Popen(
            ["git", "-C", str(repo_dir), "cat-file", "--batch"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        self.parse_cache: dict[str, dict[str, set[str]]] = {}

    def read(self, commit: str, path: str) -> tuple[str, str] | None:
        """Return ``(blob_oid, text)`` for ``commit:path``, or None when absent."""

        assert self.proc.stdin is not None and self.proc.stdout is not None
        self.proc.stdin.write(f"{commit}:{path}\n".encode())
        self.proc.stdin.flush()
        header = self.proc.stdout.readline().decode("utf-8", errors="replace").strip()
        if not header or header.endswith(("missing", "ambiguous")):
            return None
        parts = header.split()
        if len(parts) != 3 or parts[1] != "blob":
            return None
        oid, size = parts[0], int(parts[2])
        payload = self.proc.stdout.read(size)
        self.proc.stdout.read(1)  # trailing newline
        return oid, payload.decode("utf-8", errors="replace")

    def test_identifiers(self, commit: str, path: str) -> dict[str, set[str]] | None:
        found = self.read(commit, path)
        if found is None:
            return None
        oid, text = found
        cached = self.parse_cache.get(oid)
        if cached is None:
            cached = extract_test_function_identifiers(text)
            self.parse_cache[oid] = cached
        return cached

    def close(self) -> None:
        if self.proc.stdin is not None:
            self.proc.stdin.close()
        self.proc.wait(timeout=10)


def blob_at(repo_dir: Path, commit: str, path: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo_dir), "show", f"{commit}:{path}"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", errors="replace")


def commit_datetime(repo_dir: Path, commit: str) -> datetime:
    raw = git(repo_dir, "show", "-s", "--format=%cI", commit).strip()
    return datetime.fromisoformat(raw)


# --------------------------------------------------------------------------- #
# Stage 1 — dataset retrieval
# --------------------------------------------------------------------------- #


def fetch_dataset(cache: Path) -> dict[str, Any]:
    if cache.exists():
        return json.loads(cache.read_text())
    rows: list[dict[str, Any]] = []
    offset = 0
    total = None
    while True:
        url = (
            f"{ROWS_ENDPOINT}?dataset={DATASET.replace('/', '%2F')}"
            f"&config=default&split={DATASET_SPLIT}&offset={offset}&length=100"
        )
        with urllib.request.urlopen(url, timeout=120) as response:
            payload = json.load(response)
        total = payload.get("num_rows_total")
        batch = payload.get("rows", [])
        if not batch:
            break
        for item in batch:
            row = item["row"]
            rows.append(
                {
                    "instance_id": row["instance_id"],
                    "repo": row["repo"],
                    "base_commit": row["base_commit"],
                    "created_at": row["created_at"],
                    "patch": row["patch"],
                    "test_patch": row["test_patch"],
                }
            )
        offset += len(batch)
        if total is not None and offset >= total:
            break
    rows.sort(key=lambda item: item["instance_id"])
    digest = hashlib.sha256(
        json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    record = {
        "dataset": DATASET,
        "split": DATASET_SPLIT,
        "num_rows_total": total,
        "retrieved_rows": len(rows),
        "rows_sha256": digest,
        "rows": rows,
    }
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(record, indent=1, sort_keys=True))
    return record


# --------------------------------------------------------------------------- #
# Stage 2 — repository clones
# --------------------------------------------------------------------------- #


def _clone_one(repo: str, work: Path, attempts: int = 4) -> None:
    target = work / repo.replace("/", "__")
    if target.exists():
        return
    url = f"https://github.com/{repo}.git"
    staging = work / f".{repo.replace('/', '__')}.partial"

    last_error = ""
    for attempt in range(1, attempts + 1):
        if staging.exists():
            subprocess.run(["rm", "-rf", str(staging)], check=False)
        print(f"  cloning {repo} (attempt {attempt}/{attempts}) ...", flush=True)
        # Full history with blobs, no working tree.  A blobless clone would refetch every
        # blob over the network, and this analysis reads thousands of them.  Clone into a
        # staging path and rename, so an interrupted clone is never a cache hit.
        result = subprocess.run(
            ["git", "clone", "--no-checkout", url, str(staging)],
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            staging.rename(target)
            return
        last_error = result.stderr.decode("utf-8", errors="replace").strip()[-400:]
        print(f"  clone failed for {repo}: {last_error}", flush=True)
        if attempt < attempts:
            time.sleep(5 * attempt)

    if staging.exists():
        subprocess.run(["rm", "-rf", str(staging)], check=False)
    raise RuntimeError(f"clone failed for {repo} after {attempts} attempts: {last_error}")


def clone_repos(repos: Iterable[str], work: Path) -> dict[str, dict[str, str]]:
    ordered = sorted(set(repos))
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda repo: _clone_one(repo, work), ordered))
    heads: dict[str, dict[str, str]] = {}
    for repo in ordered:
        target = work / repo.replace("/", "__")
        head = git(target, "rev-parse", "HEAD").strip()
        branch = git(target, "rev-parse", "--abbrev-ref", "HEAD").strip()
        heads[repo] = {
            "url": f"https://github.com/{repo}.git",
            "head_sha": head,
            "default_branch": branch,
        }
        print(f"  {repo} head={head[:12]} branch={branch}", flush=True)
    return heads


# --------------------------------------------------------------------------- #
# Stage 3 — symbol extraction
# --------------------------------------------------------------------------- #


def changed_old_lines(patch: str) -> dict[str, set[int]]:
    """Map each patched file to the original-side line numbers it disturbs."""

    touched: dict[str, set[int]] = defaultdict(set)
    current: str | None = None
    old_line = 0
    for line in patch.splitlines():
        if line.startswith("--- "):
            continue
        if line.startswith("+++ "):
            target = line[4:].strip()
            if target == "/dev/null":
                current = None
            else:
                current = target[2:] if target.startswith("b/") else target
            continue
        match = HUNK_RE.match(line)
        if match:
            start = int(match.group(1))
            length = int(match.group(2) or "1")
            # A pure-insertion hunk (``-N,0``) inserts after original line N.  Seat the
            # cursor at N+1 so the shared "+" rule below attributes it to N exactly, and
            # never to the untouched line N-1.
            old_line = start + 1 if length == 0 else start
            continue
        if current is None:
            continue
        if line.startswith("-"):
            touched[current].add(old_line)
            old_line += 1
        elif line.startswith("+"):
            touched[current].add(max(1, old_line - 1))
        elif line.startswith(" "):
            old_line += 1
    return {path: lines for path, lines in touched.items() if lines}


def enclosing_symbols(source: str, lines: set[int]) -> set[str]:
    """Names of the innermost definitions enclosing any of ``lines``."""

    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        raise
    spans: list[tuple[int, int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = node.lineno
            end = getattr(node, "end_lineno", None) or node.lineno
            spans.append((start, end, node.name))
    found: set[str] = set()
    for line in lines:
        best: tuple[int, str] | None = None
        for start, end, name in spans:
            if start <= line <= end:
                width = end - start
                if best is None or width < best[0]:
                    best = (width, name)
        if best is not None:
            found.add(best[1])
    return found


def extract_test_function_identifiers(source: str) -> dict[str, set[str]]:
    """Map each ``test_*`` function's qualified name to the identifiers in its text."""

    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return {}
    lines = source.splitlines()
    out: dict[str, set[str]] = {}

    def visit(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                visit(child, f"{prefix}{child.name}.")
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if child.name.startswith("test_"):
                    start = min(
                        [child.lineno] + [d.lineno for d in child.decorator_list]
                    ) - 1
                    end = getattr(child, "end_lineno", child.lineno)
                    text = "\n".join(lines[start:end])
                    out[f"{prefix}{child.name}"] = set(IDENTIFIER_RE.findall(text))

    visit(tree, "")
    return out


# --------------------------------------------------------------------------- #
# Stage 4 — later-added test identifiers
# --------------------------------------------------------------------------- #


def boundary_commit(repo_dir: Path, tip: str, cutoff: datetime) -> str | None:
    """Last first-parent commit at or before ``cutoff``, walking back from ``tip``."""

    out = git(
        repo_dir,
        "rev-list",
        "-1",
        "--first-parent",
        f"--before={cutoff.isoformat()}",
        tip,
    ).strip()
    return out or None


def window_commit(repo_dir: Path, head: str, base: str, cutoff: datetime) -> str | None:
    """Forward window end: must descend from ``base`` to define a ``base..window`` range."""

    out = boundary_commit(repo_dir, head, cutoff)
    if out is None:
        return None
    if not git_ok(repo_dir, "merge-base", "--is-ancestor", base, out):
        return None
    return out


def own_test_functions(test_patch: str) -> set[tuple[str, str]]:
    """(path, function) pairs for test functions added by the task's own fixing PR.

    Amendment A1.  ``base_commit`` is the parent of the pull request that fixes the task,
    so every forward window contains that pull request.  Its ``test_patch`` references the
    touched symbols by construction: those tests are the visible grader, never a hidden
    consequence test, and counting them would make the primary yield a tautology.
    """

    added: set[tuple[str, str]] = set()
    current: str | None = None
    for line in test_patch.splitlines():
        if line.startswith("+++ "):
            target = line[4:].strip()
            current = None if target == "/dev/null" else (
                target[2:] if target.startswith("b/") else target
            )
            continue
        if current is None or not line.startswith("+"):
            continue
        match = re.match(r"\+\s*(?:async\s+)?def\s+(test_[A-Za-z0-9_]*)", line)
        if match:
            added.add((current, match.group(1)))
    return added


def added_test_identifiers(
    repo_dir: Path,
    start: str,
    end: str,
    reader: BlobReader,
    excluded: set[tuple[str, str]] | None = None,
) -> tuple[set[str], int]:
    """Identifiers in test functions added in ``start..end``.

    Used for both directions: forward passes ``(base, window)``; the backward control of
    amendment A2 passes ``(backward_boundary, base)``.
    """

    names = git(
        repo_dir,
        "log",
        "--pretty=format:",
        "--name-only",
        "--diff-filter=AM",
        f"{start}..{end}",
    )
    touched = {p for p in {line.strip() for line in names.splitlines() if line.strip()} if is_test_path(p)}
    identifiers: set[str] = set()
    added_count = 0
    for path in sorted(touched):
        after_funcs = reader.test_identifiers(end, path)
        if after_funcs is None:
            continue
        before_funcs = reader.test_identifiers(start, path)
        before_names = set(before_funcs) if before_funcs else set()
        for qualname, ids in after_funcs.items():
            if qualname in before_names:
                continue
            if excluded and (path, qualname.split(".")[-1]) in excluded:
                continue
            added_count += 1
            identifiers |= ids
    return identifiers, added_count


# --------------------------------------------------------------------------- #
# Stage 5 — deterministic permutation control
# --------------------------------------------------------------------------- #


def _median(values: list[int]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[middle])
    return (ordered[middle - 1] + ordered[middle]) / 2


def exposure_diagnostic(rows: list[dict[str, Any]]) -> dict[str, float]:
    """How many tests each side of the comparison actually had to match against.

    The backward control is only a fair comparison if both windows expose a similar
    number of added tests.  Repositories mature, so the forward side may simply contain
    more tests.  This reports the imbalance instead of leaving it implicit.
    """

    forward = [row["forward_added_tests"] for row in rows]
    backward = [row["backward_added_tests"] for row in rows]
    forward_total = sum(forward)
    backward_total = sum(backward)
    return {
        "forward_added_tests_total": forward_total,
        "backward_added_tests_total": backward_total,
        "forward_added_tests_median": _median(forward),
        "backward_added_tests_median": _median(backward),
        "forward_over_backward_total_ratio": (
            forward_total / backward_total if backward_total else float("inf")
        ),
        "instances_with_zero_forward_tests": sum(1 for value in forward if value == 0),
        "instances_with_zero_backward_tests": sum(1 for value in backward if value == 0),
        "symbol_count_median": _median([row["symbol_count"] for row in rows]),
    }


def permutation_key(index: int) -> int:
    digest = hashlib.sha256(f"{PERMUTATION_SALT}{index}".encode()).digest()
    return int.from_bytes(digest[:4], "big")


def build_derangement(instance_ids: list[str], repo_of: dict[str, str]) -> dict[str, str]:
    """Deterministic fixed-point-free, different-repository pairing."""

    order = sorted(
        range(len(instance_ids)), key=lambda k: (permutation_key(k + 1), instance_ids[k])
    )
    shuffled = [instance_ids[k] for k in order]
    size = len(shuffled)
    target = {shuffled[m]: shuffled[(m + 1) % size] for m in range(size)}

    def bad(source: str) -> bool:
        dest = target[source]
        return dest == source or repo_of[dest] == repo_of[source]

    for m in range(size):
        source = shuffled[m]
        if not bad(source):
            continue
        for offset in range(1, size):
            other = shuffled[(m + offset) % size]
            if other == source:
                continue
            a, b = target[source], target[other]
            target[source], target[other] = b, a
            if not bad(source) and not bad(other):
                break
            target[source], target[other] = a, b
    return target


# --------------------------------------------------------------------------- #
# Measurement
# --------------------------------------------------------------------------- #


def measure(work: Path, out_path: Path, limit: int | None = None) -> dict[str, Any]:
    record = fetch_dataset(work / "swebench_verified.json")
    rows = record["rows"]
    if limit is not None:
        rows = rows[:limit]
    print(f"dataset rows: {len(rows)} (sha256={record['rows_sha256'][:16]})", flush=True)

    heads = clone_repos([r["repo"] for r in rows], work)

    excluded: dict[str, list[str]] = defaultdict(list)
    included: dict[str, dict[str, Any]] = {}
    readers: dict[str, BlobReader] = {}

    for position, row in enumerate(rows, start=1):
        iid = row["instance_id"]
        repo = row["repo"]
        repo_dir = work / repo.replace("/", "__")
        base = row["base_commit"]
        reader = readers.get(repo)
        if reader is None:
            reader = readers[repo] = BlobReader(repo_dir)

        if not git_ok(repo_dir, "cat-file", "-e", f"{base}^{{commit}}"):
            excluded["base_commit_unresolvable"].append(iid)
            continue

        touched = changed_old_lines(row["patch"])
        source_files = {p: lines for p, lines in touched.items() if is_source_path(p)}
        if not source_files:
            excluded["patch_touches_no_source_file"].append(iid)
            continue

        base_dt = commit_datetime(repo_dir, base)
        head = heads[repo]["head_sha"]
        head_dt = commit_datetime(repo_dir, head)
        if head_dt < base_dt + timedelta(days=max(DELTAS_DAYS)):
            excluded["insufficient_subsequent_history"].append(iid)
            continue

        symbols: set[str] = set()
        extraction_failed = False
        for path, lines in source_files.items():
            content = blob_at(repo_dir, base, path)
            if content is None:
                continue
            try:
                symbols |= enclosing_symbols(content, lines)
            except (SyntaxError, ValueError):
                extraction_failed = True
        if extraction_failed and not symbols:
            excluded["symbol_extraction_failed"].append(iid)
            continue
        if not symbols:
            excluded["no_enclosing_symbol"].append(iid)
            continue

        own_tests = own_test_functions(row["test_patch"])

        per_delta: dict[str, dict[str, Any]] = {}
        usable = True
        for delta in DELTAS_DAYS:
            window = window_commit(repo_dir, head, base, base_dt + timedelta(days=delta))
            if window is None:
                usable = False
                break
            # A1: the instance's own fixing-PR tests are the visible grader, not evidence.
            identifiers, added = added_test_identifiers(
                repo_dir, base, window, reader, excluded=own_tests
            )
            # A2: same repository, same window length, looking backward from base.
            back = boundary_commit(repo_dir, base, base_dt - timedelta(days=delta))
            if back is None:
                back_ids: set[str] = set()
                back_added = 0
            else:
                back_ids, back_added = added_test_identifiers(repo_dir, back, base, reader)
            per_delta[str(delta)] = {
                "window_commit": window,
                "added_test_functions": added,
                "identifiers": sorted(identifiers),
                "backward_boundary_commit": back,
                "backward_added_test_functions": back_added,
                "backward_identifiers": sorted(back_ids),
            }
        if not usable:
            excluded["window_commit_unresolvable"].append(iid)
            continue

        included[iid] = {
            "instance_id": iid,
            "repo": repo,
            "base_commit": base,
            "base_date": base_dt.isoformat(),
            "symbols": sorted(symbols),
            "own_test_functions_excluded": len(own_tests),
            "per_delta": per_delta,
        }
        if position % 25 == 0:
            print(f"  processed {position}/{len(rows)} (included={len(included)})", flush=True)

    for reader in readers.values():
        reader.close()

    ids = sorted(included)
    repo_of = {i: included[i]["repo"] for i in ids}
    pairing = build_derangement(ids, repo_of)

    results: dict[str, Any] = {}
    for delta in DELTAS_DAYS:
        key = str(delta)
        pairs: list[tuple[bool, bool]] = []
        backward_pairs: list[tuple[bool, bool]] = []
        real_hits = 0
        control_hits = 0
        backward_hits = 0
        per_repo_hits: dict[str, int] = defaultdict(int)
        rows_out = []
        for iid in ids:
            symbols = set(included[iid]["symbols"])
            own = set(included[iid]["per_delta"][key]["identifiers"])
            other = set(included[pairing[iid]]["per_delta"][key]["identifiers"])
            backward = set(included[iid]["per_delta"][key]["backward_identifiers"])
            real = bool(symbols & own)
            control = bool(symbols & other)
            back = bool(symbols & backward)
            pairs.append((real, control))
            backward_pairs.append((real, back))
            real_hits += int(real)
            control_hits += int(control)
            backward_hits += int(back)
            if real:
                per_repo_hits[included[iid]["repo"]] += 1
            rows_out.append(
                {
                    "instance_id": iid,
                    "repo": included[iid]["repo"],
                    "control_partner": pairing[iid],
                    "real": real,
                    "control": control,
                    "backward_control": back,
                    "symbol_count": len(symbols),
                    "forward_added_tests": included[iid]["per_delta"][key][
                        "added_test_functions"
                    ],
                    "backward_added_tests": included[iid]["per_delta"][key][
                        "backward_added_test_functions"
                    ],
                }
            )
        total = len(ids)
        mcnemar = exact_one_sided_mcnemar(pairs)
        backward_mcnemar = exact_one_sided_mcnemar(backward_pairs)
        dominant = max(per_repo_hits.values()) / real_hits if real_hits else 0.0
        results[key] = {
            "n": total,
            "real_hits": real_hits,
            "real_yield": real_hits / total if total else 0.0,
            "real_wilson_95": list(wilson_interval(real_hits, total)),
            "control_hits": control_hits,
            "control_yield": control_hits / total if total else 0.0,
            "control_wilson_95": list(wilson_interval(control_hits, total)),
            "yield_difference": (real_hits - control_hits) / total if total else 0.0,
            "mcnemar_real_gt_control": mcnemar,
            "backward_control_hits": backward_hits,
            "backward_control_yield": backward_hits / total if total else 0.0,
            "backward_control_wilson_95": list(wilson_interval(backward_hits, total)),
            "backward_yield_difference": (real_hits - backward_hits) / total if total else 0.0,
            "mcnemar_real_gt_backward": backward_mcnemar,
            "per_repo_real_hits": dict(sorted(per_repo_hits.items())),
            "max_single_repo_share_of_hits": dominant,
            # Exposure diagnostic.  A repository writes more tests as it matures, so the
            # forward window can beat the backward window purely because more tests were
            # added later.  Without these counts a reader cannot tell a real temporal
            # effect from repository growth, so they are reported, never hidden.
            "exposure": exposure_diagnostic(rows_out),
            "rows": rows_out,
        }

    total_seen = len(rows)
    total_excluded = sum(len(v) for v in excluded.values())
    report = {
        "schema_version": "telos.iter219.yield_report.v1",
        "gate": "experiments/iter219_temporal_consequence_test_yield/HYPOTHESIS.md",
        "dataset": {
            "name": DATASET,
            "split": DATASET_SPLIT,
            "num_rows_total": record["num_rows_total"],
            "rows_sha256": record["rows_sha256"],
        },
        "repositories": heads,
        "deltas_days": list(DELTAS_DAYS),
        "primary_delta_days": PRIMARY_DELTA,
        "permutation_salt": PERMUTATION_SALT,
        "instances_seen": total_seen,
        "instances_included": len(ids),
        "instances_excluded": total_excluded,
        "exclusions_by_reason": {k: sorted(v) for k, v in sorted(excluded.items())},
        "exclusion_counts": {k: len(v) for k, v in sorted(excluded.items())},
        "symbol_extraction_success_rate": (
            len(ids) / (len(ids) + len(excluded.get("symbol_extraction_failed", [])))
            if ids
            else 0.0
        ),
        "results_by_delta": results,
        "provider_calls": 0,
        "gpu_allocations": 0,
        "containers_built": 0,
        "repository_test_executions": 0,
        "scientific_result_claimed": False,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=1, sort_keys=True))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--work-dir",
        default="/private/tmp/telos-iter219-work",
        help="scratch directory for the dataset cache and read-only clones",
    )
    parser.add_argument(
        "--out",
        default=str(
            REPO_ROOT
            / "experiments/iter219_temporal_consequence_test_yield/proof/yield_report.json"
        ),
    )
    parser.add_argument("--limit", type=int, default=None, help="debug only; never used for the sealed run")
    args = parser.parse_args()

    work = Path(args.work_dir)
    work.mkdir(parents=True, exist_ok=True)
    report = measure(work, Path(args.out), args.limit)

    primary = report["results_by_delta"][str(PRIMARY_DELTA)]
    print()
    print(f"included={report['instances_included']} excluded={report['instances_excluded']}")
    for delta in DELTAS_DAYS:
        block = report["results_by_delta"][str(delta)]
        print(
            f"delta={delta:4d}d  real={block['real_yield']:.4f}  "
            f"xrepo={block['control_yield']:.4f}  back={block['backward_control_yield']:.4f}"
        )
    print()
    print(f"PRIMARY delta={PRIMARY_DELTA}d, n={primary['n']}")
    print(
        f"  real     = {primary['real_yield']:.4f} "
        f"CI[{primary['real_wilson_95'][0]:.4f}, {primary['real_wilson_95'][1]:.4f}]"
    )
    print(
        f"  xrepo    = {primary['control_yield']:.4f} "
        f"CI[{primary['control_wilson_95'][0]:.4f}, {primary['control_wilson_95'][1]:.4f}]  "
        f"diff={primary['yield_difference']:.4f}  "
        f"p={primary['mcnemar_real_gt_control']['one_sided_exact_p_value']:.6g}"
    )
    print(
        f"  backward = {primary['backward_control_yield']:.4f} "
        f"CI[{primary['backward_control_wilson_95'][0]:.4f}, "
        f"{primary['backward_control_wilson_95'][1]:.4f}]  "
        f"diff={primary['backward_yield_difference']:.4f}  "
        f"p={primary['mcnemar_real_gt_backward']['one_sided_exact_p_value']:.6g}"
    )
    print(f"  max single-repo share of hits={primary['max_single_repo_share_of_hits']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
