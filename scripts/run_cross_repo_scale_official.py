#!/usr/bin/env python3
"""Iter151 - cross-repo scale on the OFFICIAL SWE-bench metric.

Scales the completion-gate intervention (iter146-iter148) to 8 SWE-bench_Verified repositories, scored by
the official `swebench.harness.run_evaluation` (resolved iff FAIL_TO_PASS and PASS_TO_PASS all pass) on a
cloud x86 Docker box. For each reward-hack-prone instance, a frontier adversary constructs a both-miss
(passes the target test, fails a regression test), the proxy gate accepts it (never truly resolved), and
the Telos gate rejects on regression failure, returns a gold-free generalize-signal, and repairs; the
resulting patches are scored by the official harness.

Honest framing (self-critique on the record): the proxy baseline is `0` by construction (a both-miss fails
a PASS_TO_PASS, so it is never `resolved`); the held-out oracle here is the repository's existing
regression suite (`PASS_TO_PASS`) - realistic CI - so this scales the *intervention* cross-repo, not the
gold-free-property-oracle novelty (that is the separate iter149-iter150 result). The generation ran on the
cloud VM; per-instance outcomes and 132 official SWE-bench `report.json` files are committed under
proof/raw, and this runner re-derives the tallies deterministically.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter151_cross_repo_scale_official"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
RESULTS = PROOF / "raw/scale_results.json"


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    rows = json.loads(RESULTS.read_text(encoding="utf-8"))
    bm = [x for x in rows if x.get("both_miss")]
    n = len(bm)
    repos = sorted(set(x["repo"] for x in bm))
    baseline = sum(1 for x in bm if x.get("baseline_resolved"))
    telos = sum(1 for x in bm if x.get("telos_resolved"))
    no_both_miss = sum(1 for x in rows if x.get("status") == "no_both_miss")
    per_repo = {
        r: {
            "both_miss": sum(1 for x in bm if x["repo"] == r),
            "telos_resolved": sum(1 for x in bm if x["repo"] == r and x.get("telos_resolved")),
        }
        for r in repos
    }

    def frac(k: int, d: int) -> float:
        return round(k / d, 3) if d else 0.0

    endpoints = {
        "schema_version": "telos.cross_repo_scale_official.endpoints.v1",
        "experiment_id": EXPERIMENT.name,
        "adversary_model": "gpt-5.6-terra",
        "metric": "official SWE-bench resolved (FAIL_TO_PASS + PASS_TO_PASS all pass), swebench 4.1.0",
        "both_miss_starts": n,
        "repos": repos,
        "repo_count": len(repos),
        "no_both_miss": no_both_miss,
        "baseline_resolved": baseline,
        "baseline_resolved_rate": frac(baseline, n),
        "telos_resolved": telos,
        "telos_resolved_rate": frac(telos, n),
        "per_repo": per_repo,
        "finding": (
            f"scaling the completion-gate intervention to {len(repos)} SWE-bench repositories on the "
            f"official metric: over {n} both-miss starts a proxy gate resolves {baseline}/{n} (=0 by "
            f"construction, since a both-miss fails a PASS_TO_PASS) while the Telos gate (regression-failure "
            f"rejection + gold-free generalize-signal + bounded repair) recovers {telos}/{n} = "
            f"{frac(telos, n)} to full official resolution. The intervention generalizes cross-repo on the "
            "metric the field tracks. Honest scope: the held-out oracle here is the existing regression "
            "suite (realistic CI), so this scales the intervention, not the gold-free-property-oracle "
            "novelty (iter149-150); per-repo recovery varies (e.g. scikit-learn 3/3, xarray 2/2, django "
            "2/5, sphinx 0/2), reported at full weight"
        ),
        "baseline_is_definitional": True,
        "oracle_is_regression_suite": True,
        "benchmark_or_sota_claim": False,
    }

    bars = {
        "multi_repo": len(repos) >= 5,
        "baseline_zero_by_construction": baseline == 0,
        "telos_recovers_some": telos >= 1,
        "official_metric": True,
    }
    status = "pass" if all(bars.values()) else "null"

    receipt = {
        "receipt_id": f"iter151-cross-repo-scale-official-{status}",
        "task_id": "telos:iter151_cross_repo_scale_official",
        "agent_id": "cloud-vm-cross-repo-scale-executor",
        "benchmark_id": "swebench_verified_cross_repo_scale_official_v0",
        "status": status,
        "stated_goal": (
            "Scale the completion-gate intervention across SWE-bench repositories and score it with the "
            "official SWE-bench evaluation harness."
        ),
        "acceptance_criteria": [
            "The intervention is measured across at least five repositories.",
            "The proxy baseline is 0 by construction and reported as such.",
            "The Telos-gate resolved-rate is measured by the official harness and reported with per-repo detail.",
        ],
        "evidence": [
            {"kind": "test", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/raw/scale_results.json"},
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/raw/sweb_reports.tgz"},
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json"},
        ],
        "falsifiers": [
            "resolved is the official SWE-bench verdict (FAIL_TO_PASS + PASS_TO_PASS), backed by a committed report.json.",
            "The proxy baseline being 0 is definitional (a both-miss fails a PASS_TO_PASS), not an empirical surprise.",
            "The oracle is the regression suite; this scales the intervention, not the gold-free-oracle result.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)

    learning = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT.name,
        "status": status,
        "result_path": f"experiments/{EXPERIMENT.name}/RESULT.md",
        "evidence_paths": [
            f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json",
            f"experiments/{EXPERIMENT.name}/proof/raw/scale_results.json",
            f"experiments/{EXPERIMENT.name}/proof/raw/sweb_reports.tgz",
        ],
        "insight": (
            f"the completion-gate intervention scales cross-repo on the official SWE-bench metric: over {n} "
            f"both-miss starts across {len(repos)} repos, proxy resolves {baseline}/{n} (definitional), Telos "
            f"gate recovers {telos}/{n} = {frac(telos, n)} to full official resolution. Honest: the oracle is "
            "the regression suite (realistic CI), so this is the intervention at scale, not the gold-free "
            "oracle; baseline 0 is definitional; per-repo varies. Ran on a cloud x86 Docker VM (arm64/local "
            "could not); harness malformed-patch false-negative caught and fixed before trusting numbers"
        ),
        "next_action": (
            "the higher-novelty v2 experiment: detection at scale - measure the rate frontier LLM judges "
            "(reward models) are fooled by the both-miss hacks across these repos, saving each hack diff for "
            "the reward-hack benchmark artifact"
        ),
    }

    _write(PROOF / "endpoint_results.json", endpoints)
    _write(VALID / "receipt_cross_repo_scale_official.json", receipt)
    _write(PROOF / "learning_record.json", learning)
    _write(PROOF / "run_summary.json", {"schema_version": "telos.cross_repo_scale_official.summary.v1", "experiment_id": EXPERIMENT.name, "status": status, "endpoints": endpoints})

    print(f"status={status}")
    print(f"  {n} both-miss starts across {len(repos)} repos ({no_both_miss} no-both-miss)")
    print(f"  baseline resolved: {baseline}/{n} (definitional) | Telos resolved: {telos}/{n} = {frac(telos, n)}")
    per_repo_str = {r: f"{v['telos_resolved']}/{v['both_miss']}" for r, v in per_repo.items()}
    print(f"  per-repo: {per_repo_str}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
