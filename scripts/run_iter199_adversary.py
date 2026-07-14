#!/usr/bin/env python3
"""iter199 Phase A: elicit certified-resolved-but-wrong variant candidates over the frozen 42 targets.

Reuses the proven iter193 adversary helpers (one_src, added_block, build_variant, extract, gen) and the
same prompt, driven by the frozen target manifest at
experiments/iter199_benchmark_expansion_across_repos/proof/raw/targets.json. Stages variant/gold/test
patch triplets for the Phase B certify+witness CI run. Reads OPENAI_API_KEY from the environment; never
prints or commits it. Ceilings: <=120 adversary calls, <=$15.00 (the scenario-generation stage has its own
budget; the gate's combined ceiling is 160 calls / $30.00).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "iter199_benchmark_expansion_across_repos"
STAGE = EXP / "proof" / "raw" / "candidates"
TARGETS = EXP / "proof" / "raw" / "targets.json"
SNAPSHOT = (
    ROOT
    / "experiments/iter154_reward_hack_benchmark_expansion_pilot/proof/raw/swebench_verified_rows_snapshot.json"
)

# Reuse the iter193 adversary helpers rather than duplicate them.
_spec = importlib.util.spec_from_file_location(
    "adv193", ROOT / "scripts" / "run_certified_resolved_adversary.py"
)
adv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(adv)

CALL_CEILING = 120
SPEND_CEILING = 15.00


def main() -> int:
    STAGE.mkdir(parents=True, exist_ok=True)
    by_id = {r["instance_id"]: r for r in json.loads(SNAPSHOT.read_text())["rows"]}
    targets = json.loads(TARGETS.read_text())["targets"]
    key = adv._key()

    calls = 0
    est = 0.0
    manifest: list[dict] = []
    for t in targets:
        iid = t["instance_id"]
        if calls >= CALL_CEILING or est >= SPEND_CEILING:
            manifest.append({"instance_id": iid, "status": "budget_stopped"})
            continue
        row = by_id[iid]
        srcf = adv.one_src(row["patch"])
        if not srcf:
            manifest.append({"instance_id": iid, "status": "no_single_src"})
            continue
        block = adv.added_block(row["patch"], srcf)
        block_lines = block.split("\n")
        if not block.strip():
            manifest.append({"instance_id": iid, "status": "no_block"})
            continue

        f2p = json.loads(row["FAIL_TO_PASS"])
        p2p = json.loads(row["PASS_TO_PASS"])
        prompt = adv.PROMPT_TEMPLATE.format(
            iid=iid,
            repo=row["repo"],
            problem=(row["problem_statement"] or "")[:1200],
            srcf=srcf,
            block=block,
            target=f2p[0] if f2p else "(none)",
            p2p="\n".join(f"- {x}" for x in p2p[:8]),
            n=len(block_lines),
        )
        variant_patch = None
        usage: dict = {}
        for _ in range(2):
            if calls >= CALL_CEILING or est >= SPEND_CEILING:
                break
            calls += 1
            est += adv.EST_USD_PER_CALL
            try:
                raw, usage = adv.gen(adv.ADV_SYS, prompt, key)
            except Exception as exc:
                manifest.append({"instance_id": iid, "status": "provider_error", "detail": str(exc)[:160]})
                break
            repl = adv.extract(raw).split("\n")
            if len(repl) != len(block_lines):
                continue
            if "\n".join(repl).strip() == block.strip():
                continue
            candidate = adv.build_variant(row["patch"], srcf, repl)
            if candidate and candidate != row["patch"]:
                variant_patch = candidate
                break
        if not variant_patch:
            if not any(m["instance_id"] == iid for m in manifest):
                manifest.append({"instance_id": iid, "status": "no_valid_variant"})
            continue

        stem = iid.replace("/", "__")
        (STAGE / f"{stem}.variant.patch").write_text(variant_patch + "\n")
        (STAGE / f"{stem}.gold.patch").write_text(
            row["patch"] + ("\n" if not row["patch"].endswith("\n") else "")
        )
        (STAGE / f"{stem}.test.patch").write_text(
            row["test_patch"] + ("\n" if not row["test_patch"].endswith("\n") else "")
        )
        manifest.append(
            {
                "instance_id": iid,
                "status": "candidate",
                "repo": row["repo"],
                "base_commit": row["base_commit"],
                "src_file": srcf,
                "fail_to_pass": f2p,
                "pass_to_pass_count": len(p2p),
                "variant_patch_sha256": hashlib.sha256(variant_patch.encode()).hexdigest(),
                "gold_patch_sha256": hashlib.sha256(row["patch"].encode()).hexdigest(),
                "adversary_model": adv.MODEL,
                "provider_usage": usage,
            }
        )

    summary = {
        "schema_version": "telos.iter199.adversary_summary.v1",
        "adversary_model": adv.MODEL,
        "targets": len(targets),
        "provider_calls": calls,
        "estimated_spend_usd": round(est, 4),
        "candidates": sum(1 for m in manifest if m["status"] == "candidate"),
        "manifest": manifest,
    }
    (STAGE / "adversary_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(
        f"iter199 adversary: {summary['candidates']} variants from {len(targets)} targets, "
        f"{calls} calls, ~${est:.2f}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
