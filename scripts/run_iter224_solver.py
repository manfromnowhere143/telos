#!/usr/bin/env python3
"""iter224 lean neutral solver: reuses the exact frozen solve logic without the iter202 freeze.

The frozen ``run_iter200_solver`` is hard-bound to iter202's runtime manifest and 53-target
cohort, so a fresh disjoint cohort cannot use it directly.  This driver imports the exact
same helpers — the neutral prompt, the gold-region reconstruction, and the patch builder —
so every solve is byte-for-byte the frozen procedure and the results pool validly with
iter200 and iter223.  It omits only the cryptographic checkpoint/freeze layer, which binds
evidence to the iter202 pipeline and is unnecessary for a fresh experiment.

Reads OPENAI_API_KEY from the environment.  Frozen model gpt-5.6-terra.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys

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

EXP = ROOT / "experiments" / os.environ.get("TELOS_NAT_EXP", "iter224_natural_rate_scale_n")
TARGETS = EXP / "proof/raw/solve_targets.json"
STAGE = EXP / "proof/raw/solutions"
SNAPSHOT = ROOT / (
    "experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/"
    "swebench_verified_rows_snapshot.json"
)
SPEND_CEILING = 15.0


def main() -> int:
    key = adv._key()
    targets = json.loads(TARGETS.read_text())["targets"]
    by_id = {r["instance_id"]: r for r in json.loads(SNAPSHOT.read_text())["rows"]}
    STAGE.mkdir(parents=True, exist_ok=True)

    manifest: list[dict] = []
    spend = 0.0
    for entry in targets:
        iid = entry["instance_id"]
        row = by_id[iid]
        patch = row["patch"]
        srcf = adv.one_src(patch)
        region = prefix_region(source_hunk(patch, srcf))
        prompt = PROMPT.format(
            repo=row["repo"], srcf=srcf, problem=(row["problem_statement"] or "")[:1500],
            region=region[:2500],
        )
        if spend + adv.EST_USD_PER_CALL > SPEND_CEILING:
            manifest.append({"instance_id": iid, "status": "budget_stopped"})
            continue
        try:
            raw, usage = adv.gen(SOLVE_SYS, prompt, key)
        except Exception as exc:  # noqa: BLE001 — a provider error is a recorded outcome
            manifest.append({"instance_id": iid, "status": "provider_error", "detail": str(exc)[:160]})
            continue
        spend += adv.EST_USD_PER_CALL
        fix = adv.extract(raw).split("\n")
        if not [line for line in fix if line.strip()]:
            manifest.append({"instance_id": iid, "status": "empty_fix"})
            continue
        model_patch = build_solve_patch(patch, srcf, fix)
        if not model_patch:
            manifest.append({"instance_id": iid, "status": "no_patch"})
            continue
        stem = iid.replace("/", "__")
        (STAGE / f"{stem}.model.patch").write_text(model_patch + "\n")
        (STAGE / f"{stem}.gold.patch").write_text(
            patch + ("\n" if not patch.endswith("\n") else "")
        )
        manifest.append(
            {
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
                "solver_model": adv.MODEL,
                "src_file": srcf,
                "status": "solution",
            }
        )

    summary = {
        "schema_version": "telos.iter200.solve_summary.v1",
        "checkpoint_schema": {"finished": "telos.iter224.provider_attempt.finished.v1",
                              "started": "telos.iter224.provider_attempt.started.v1"},
        "solver_model": adv.MODEL,
        "targets": len(targets),
        "provider_calls": sum(1 for m in manifest if m["status"] in ("solution","provider_error","empty_fix","no_patch")),
        "solutions": sum(1 for m in manifest if m["status"] == "solution"),
        "estimated_spend_usd": round(spend, 4),
        "manifest": manifest,
    }
    (STAGE / "solve_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(
        f"iter224 solver: {summary['solutions']} solutions from {len(targets)} targets, "
        f"~${spend:.2f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
