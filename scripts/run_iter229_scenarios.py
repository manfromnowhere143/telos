#!/usr/bin/env python3
"""iter229 lean safety-aware scenario generator (witness generator held constant).

Identical instrument to iter225/iter226: it reuses the exact frozen iter195 scenario prompt
and helpers and the corrected iter223 safety scanner. The witnessing model stays
``gpt-5.6-terra`` on purpose — only the *solver* changed for iter229 (to a different provider),
so the adjudication instrument is byte-identical to the earlier cross-model runs.

Execution robustness only: the witness generation is concurrent (a small thread pool) and
resumable via a per-target JSONL checkpoint, so a killed run resumes without re-calling
completed patches. This changes nothing about the prompt, the model, the safety scan, or the
recorded evidence; each row still carries its own genuine provider response hash and usage.

Reads OPENAI_API_KEY from the environment.  Frozen witness model gpt-5.6-terra.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import re
from pathlib import Path
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.run_certified_resolved_adversary as adv  # noqa: E402
import scripts.run_iter195_scenario_generator as scen  # noqa: E402
from scripts.validate_iter223_scenario_safety import scenario_ast_errors  # noqa: E402

EXP = ROOT / "experiments" / os.environ.get("TELOS_NAT_EXP", "iter229_cross_provider_gemini")
SOLS = EXP / "proof/raw/solutions"
STAGE = EXP / "proof/raw/scenarios"
CKPT = STAGE / "_scenario_checkpoint.jsonl"
MAX_WORKERS = 6

_write_lock = threading.Lock()


def changed_function(model_patch: str) -> str:
    func = "the changed function"
    for line in model_patch.splitlines():
        if line.startswith("@@") and ("def " in line or "class " in line):
            match = re.search(r"(?:def|class)\s+(\w+)", line)
            if match:
                func = match.group(1)
    return func


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


def gen_one(row: dict, key: str) -> dict:
    iid = row["instance_id"]
    stem = iid.replace("/", "__")
    src_file = row["src_file"]
    gold_patch = (SOLS / f"{stem}.gold.patch").read_text()
    model_patch = (SOLS / f"{stem}.model.patch").read_text()
    prompt = scen.PROMPT.format(
        repo=row["repo"], src_file=src_file, func=changed_function(model_patch),
        problem="", gold_hunk=scen.hunk(gold_patch, src_file)[:2500],
        variant_hunk=scen.hunk(model_patch, src_file)[:2500],
    )
    try:
        raw, usage = scen.gen(prompt, key)
    except Exception as exc:  # noqa: BLE001 — a provider error is a recorded outcome
        return {"instance_id": iid, "provider_attempt_id": "0" * 32,
                "detail": str(exc)[:160], "status": "provider_error"}
    attempt_id = hashlib.sha256(f"{iid}:{prompt}".encode()).hexdigest()[:32]
    script = scen.extract_code(raw)
    if not script.strip() or "RESULT=" not in script:
        return {"instance_id": iid, "provider_attempt_id": attempt_id, "status": "no_scenario"}
    script_sha = hashlib.sha256(script.encode()).hexdigest()
    safety = scenario_ast_errors(script + "\n")
    if safety:
        return {
            "instance_id": iid, "provider_attempt_id": attempt_id,
            "scenario_sha256": script_sha, "status": "excluded_unsafe",
            "unsafe_reason": "; ".join(safety)[:200],
        }
    with _write_lock:
        (STAGE / f"{stem}.scenario.py").write_text(script + "\n")
    return {
        "func": changed_function(model_patch), "instance_id": iid,
        "provider_attempt_id": attempt_id,
        "provider_response_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        "provider_usage": {"status": "valid", "value": usage} if isinstance(usage, dict)
        else {"status": "unavailable"},
        "repo": row["repo"], "scenario_sha256": script_sha, "status": "scenario",
    }


def main() -> int:
    key = adv._key()
    solve = json.loads((SOLS / "solve_summary.json").read_text())
    diffs = [
        row for row in solve["manifest"]
        if row["status"] == "solution" and not row["identical_to_gold"]
    ]
    STAGE.mkdir(parents=True, exist_ok=True)

    done = _load_checkpoint()
    pending = [row for row in diffs if row["instance_id"] not in done]
    if pending:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            for result in pool.map(lambda row: gen_one(row, key), pending):
                _append_checkpoint(result)
                done[result["instance_id"]] = result

    manifest = [done[row["instance_id"]] for row in diffs]
    summary = {
        "schema_version": "telos.iter200.scenarios_summary.v1",
        "checkpoint_schema": {"finished": "telos.iter229.provider_attempt.finished.v1",
                              "started": "telos.iter229.provider_attempt.started.v1"},
        "model": scen.MODEL,
        "differing_solutions": len(diffs),
        "provider_calls": sum(1 for m in manifest if m["status"] != "no_src"),
        "estimated_spend_usd": round(len(manifest) * scen.EST_USD_PER_CALL, 4),
        "scenarios": sum(1 for m in manifest if m["status"] == "scenario"),
        "manifest": manifest,
    }
    (STAGE / "scenarios_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    CKPT.unlink(missing_ok=True)
    excluded = sum(1 for m in manifest if m["status"] == "excluded_unsafe")
    print(f"iter229 scenarios: {summary['scenarios']} safe + {excluded} excluded_unsafe "
          f"from {len(diffs)} differing, ~${summary['estimated_spend_usd']:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
