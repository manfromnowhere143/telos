#!/usr/bin/env python3
"""Deterministically assemble the iter230 frozen natural certified-yet-wrong detector eval set.

For the first time the natural-rate arc gives a set of *naturally occurring* certified-yet-wrong
patches, rather than the constructed ones of iter193--iter199. This builds a frozen detector
benchmark from committed evidence: the confirmed hacks are positives (a certified patch both blind
judges named wrong), and the certified-and-believed-correct patches are negatives (certified and
either normalized-identical to gold or witness-executed with no divergence). Each entry binds to the
committed model patch by SHA-256; the patch bytes live in each run's committed solutions directory.

Selection is fully deterministic (sorted by (run, instance_id)); the manifest regenerates byte-for-byte.
Run: python3 scripts/build_iter230_eval_set.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/iter230_gold_free_detector_natural/proof/raw/eval_set.json"

# The six natural-rate runs, each with its committed solver model.
RUNS = {
    "iter200_natural_certified_yet_wrong_rate": "gpt-5.6-terra",
    "iter223_natural_rate_safety_aware": "gpt-5.6-terra",
    "iter225_cross_model_generalization": "gpt-5.5",
    "iter226_cross_model_generalization_gpt54": "gpt-5.4",
    "iter227_cross_provider_generalization": "claude-sonnet-5",
    "iter229_cross_provider_gemini": "gemini-3.1-pro-preview",
}
NEG_STATUSES = {"certified_gold_equivalent_normalized", "certified_no_observed_divergence"}


def _model_patch_sha(run: str, iid: str) -> str | None:
    stem = iid.replace("/", "__")
    p = ROOT / f"experiments/{run}/proof/raw/solutions/{stem}.model.patch"
    if not p.is_file():
        return None
    raw = p.read_bytes()
    return hashlib.sha256(raw[:-1] if raw.endswith(b"\n") else raw).hexdigest()


def main() -> int:
    positives: list[dict] = []
    negatives: list[dict] = []
    for run, model in RUNS.items():
        base = ROOT / f"experiments/{run}"
        pc = base / "proof/iter200_per_candidate.json"
        verd = base / "proof/blind_judge_verdicts.json"
        if not pc.is_file() or not verd.is_file():
            continue
        rows = json.loads(pc.read_text())
        rows = rows if isinstance(rows, list) else rows.get("candidates", rows.get("per_candidate", []))
        confirmed = {
            r["instance_id"]
            for r in json.loads(verd.read_text())["verdicts"]
            if r.get("both_judges_flag_only_model")
        }
        for r in sorted(rows, key=lambda x: x.get("instance_id", "")):
            iid = r.get("instance_id")
            status = r.get("status")
            sha = _model_patch_sha(run, iid)
            if sha is None:
                continue
            entry = {
                "run": run,
                "solver_model": model,
                "instance_id": iid,
                "model_patch_sha256": sha,
                "model_patch_path": f"experiments/{run}/proof/raw/solutions/{iid.replace('/', '__')}.model.patch",
            }
            if iid in confirmed:
                positives.append({**entry, "label": "certified_yet_wrong"})
            elif status in NEG_STATUSES:
                negatives.append({**entry, "label": "certified_correct", "reason": status})

    positives.sort(key=lambda e: (e["run"], e["instance_id"]))
    negatives.sort(key=lambda e: (e["run"], e["instance_id"]))
    manifest = {
        "schema_version": "telos.iter230.natural_detector_eval.v1",
        "description": (
            "Frozen natural certified-yet-wrong detector benchmark assembled from the committed "
            "natural-rate arc (iter200/223/225/226/227/229). Positives are confirmed certified-yet-wrong "
            "patches (both blind judges named the model); negatives are certified-and-believed-correct "
            "patches (normalized-identical to gold, or witness-executed with no divergence). Patch bytes "
            "live in each run's committed solutions directory, bound here by SHA-256."
        ),
        "positive_count": len(positives),
        "negative_count": len(negatives),
        "positives": positives,
        "negatives": negatives,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"iter230 eval set: {len(positives)} positives + {len(negatives)} negatives -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
