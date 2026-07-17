#!/usr/bin/env python3
"""iter227 lean cross-PROVIDER solver: the iter225/iter226 harness with an Anthropic solver.

Iter227 is a single-variable replication of iter223/iter225/iter226 on the identical frozen
53-target cohort, changing only the solver to ``claude-sonnet-5`` (Anthropic). It imports the
exact same frozen solve helpers as iter200 — the neutral prompt, the gold-region reconstruction,
and the patch builder — so every solve is byte-for-byte the frozen procedure; only the provider
endpoint and model differ. The scenario/witness generator stays ``gpt-5.6-terra`` and both blind
judges stay ``gpt-5.6-terra`` + ``claude-opus-4-8``, so the adjudication instrument is identical
to the earlier cross-model runs.

Disclosed limitation (recorded in the pre-registration): one of the two fixed blind judges
(``claude-opus-4-8``) shares the solver's provider. This is conservative for confirmation, not
inflationary — a provider-loyal judge would suppress rather than manufacture confirmations, and
``gpt-5.6-terra`` remains a fully independent cross-provider judge.

Execution robustness only: concurrent (a small thread pool) and resumable via a per-target JSONL
checkpoint. Reads ANTHROPIC_API_KEY from the environment.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.run_certified_resolved_adversary as adv  # noqa: E402
from scripts.run_iter200_solver import (  # noqa: E402
    PROMPT,
    SOLVE_SYS,
    build_solve_patch,
    equivalent_after_terminal_lf_normalization,
    prefix_region,
    source_hunk,
)

EXP = ROOT / "experiments" / os.environ.get("TELOS_NAT_EXP", "iter227_cross_provider_generalization")
TARGETS = EXP / "proof/raw/solve_targets.json"
STAGE = EXP / "proof/raw/solutions"
CKPT = STAGE / "_solve_checkpoint.jsonl"
SNAPSHOT = ROOT / (
    "experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/"
    "swebench_verified_rows_snapshot.json"
)
SPEND_CEILING = 15.0
SOLVER_MODEL = "claude-sonnet-5"
ANTHROPIC_ENDPOINT = "https://api.anthropic.com/v1/messages"
ANTHROPIC_API_VERSION = "2023-06-01"
MAX_TOKENS = 4000
MAX_WORKERS = 6

_write_lock = threading.Lock()


def _anthropic_key() -> str:
    val = os.environ.get("ANTHROPIC_API_KEY")
    if not val:
        raise SystemExit("ANTHROPIC_API_KEY not in environment")
    return val


def anthropic_gen(system: str, prompt: str, key: str) -> tuple[str, dict]:
    body = json.dumps(
        {
            "model": SOLVER_MODEL,
            "max_tokens": MAX_TOKENS,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode()
    req = urllib.request.Request(
        ANTHROPIC_ENDPOINT,
        data=body,
        headers={
            "x-api-key": key,
            "anthropic-version": ANTHROPIC_API_VERSION,
            "content-type": "application/json",
        },
        method="POST",
    )
    doc = json.load(urllib.request.urlopen(req, timeout=180))
    text = "".join(p.get("text", "") for p in doc.get("content", []) if p.get("type") == "text")
    usage = doc.get("usage", {})
    return text, usage


def _load_checkpoint() -> dict[str, dict]:
    rows: dict[str, dict] = {}
    if CKPT.exists():
        for line in CKPT.read_text().splitlines():
            line = line.strip()
            if line:
                row = json.loads(line)
                rows[row["instance_id"]] = row
    return rows


def _append_checkpoint(row: dict) -> None:
    with _write_lock:
        with CKPT.open("a") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def solve_one(entry: dict, by_id: dict, key: str) -> dict:
    iid = entry["instance_id"]
    row = by_id[iid]
    patch = row["patch"]
    srcf = adv.one_src(patch)
    region = prefix_region(source_hunk(patch, srcf))
    prompt = PROMPT.format(
        repo=row["repo"], srcf=srcf, problem=(row["problem_statement"] or "")[:1500],
        region=region[:2500],
    )
    try:
        raw, usage = anthropic_gen(SOLVE_SYS, prompt, key)
    except Exception as exc:  # noqa: BLE001 — a provider error is a recorded outcome
        return {"instance_id": iid, "status": "provider_error", "detail": str(exc)[:160]}
    fix = adv.extract(raw).split("\n")
    if not [line for line in fix if line.strip()]:
        return {"instance_id": iid, "status": "empty_fix"}
    model_patch = build_solve_patch(patch, srcf, fix)
    if not model_patch:
        return {"instance_id": iid, "status": "no_patch"}
    stem = iid.replace("/", "__")
    with _write_lock:
        (STAGE / f"{stem}.model.patch").write_text(model_patch + "\n")
        (STAGE / f"{stem}.gold.patch").write_text(
            patch + ("\n" if not patch.endswith("\n") else "")
        )
    return {
        "base_commit": row["base_commit"],
        "fail_to_pass": json.loads(row["FAIL_TO_PASS"]),
        "identical_to_gold": equivalent_after_terminal_lf_normalization(
            (model_patch + "\n").encode(), row["patch"].encode()
        ),
        "instance_id": iid,
        "model_patch_sha256": hashlib.sha256(model_patch.encode()).hexdigest(),
        "pass_to_pass_count": len(json.loads(row["PASS_TO_PASS"])),
        "provider_attempt_id": hashlib.sha256(f"{iid}:{prompt}".encode()).hexdigest()[:32],
        "provider_response_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        "provider_usage": {"status": "valid", "value": usage} if isinstance(usage, dict)
        else {"status": "unavailable"},
        "repo": row["repo"],
        "solver_model": SOLVER_MODEL,
        "src_file": srcf,
        "status": "solution",
    }


def main() -> int:
    key = _anthropic_key()
    targets = json.loads(TARGETS.read_text())["targets"]
    by_id = {r["instance_id"]: r for r in json.loads(SNAPSHOT.read_text())["rows"]}
    STAGE.mkdir(parents=True, exist_ok=True)

    done = _load_checkpoint()
    pending = [t for t in targets if t["instance_id"] not in done]
    budget_calls = int(SPEND_CEILING / adv.EST_USD_PER_CALL)
    remaining_budget = budget_calls - sum(
        1 for r in done.values()
        if r["status"] in ("solution", "provider_error", "empty_fix", "no_patch")
    )
    to_run = pending[:max(0, remaining_budget)]
    budget_stopped = pending[max(0, remaining_budget):]

    if to_run:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            for result in pool.map(lambda entry: solve_one(entry, by_id, key), to_run):
                _append_checkpoint(result)
                done[result["instance_id"]] = result
    for entry in budget_stopped:
        row = {"instance_id": entry["instance_id"], "status": "budget_stopped"}
        _append_checkpoint(row)
        done[entry["instance_id"]] = row

    manifest = [done[t["instance_id"]] for t in targets]
    spend = round(
        sum(
            adv.EST_USD_PER_CALL for r in manifest
            if r["status"] in ("solution", "provider_error", "empty_fix", "no_patch")
        ),
        4,
    )
    summary = {
        "schema_version": "telos.iter200.solve_summary.v1",
        "checkpoint_schema": {"finished": "telos.iter227.provider_attempt.finished.v1",
                              "started": "telos.iter227.provider_attempt.started.v1"},
        "solver_model": SOLVER_MODEL,
        "targets": len(targets),
        "provider_calls": sum(
            1 for r in manifest
            if r["status"] in ("solution", "provider_error", "empty_fix", "no_patch")
        ),
        "solutions": sum(1 for r in manifest if r["status"] == "solution"),
        "estimated_spend_usd": spend,
        "manifest": manifest,
    }
    (STAGE / "solve_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    CKPT.unlink(missing_ok=True)
    print(
        f"iter227 solver [{SOLVER_MODEL}]: {summary['solutions']} solutions from {len(targets)} targets, "
        f"~${spend:.2f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
