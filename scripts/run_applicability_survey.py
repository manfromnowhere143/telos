#!/usr/bin/env python3
"""Iter138 - dataset-wide applicability survey of the property-based layer, by repo.

Reproducible in CI: reads the committed frozen survey (proof/applicability_survey.json), computed over
all 500 SWE-bench Verified instances, and reports the structural applicability rate with the honest
upper-bound framing.
"""

from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter138_applicability_survey"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
SURVEY = PROOF / "applicability_survey.json"
ZERO = Decimal("0.00000000")


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    s = json.loads(SURVEY.read_text(encoding="utf-8"))
    by_repo = s["by_repo"]
    high = [k for k, v in by_repo.items() if v["applicability_rate"] >= 0.8]
    low = [k for k, v in by_repo.items() if v["applicability_rate"] < 0.6]

    endpoints = {
        "schema_version": "telos.applicability_survey.endpoints.v1",
        "experiment_id": EXPERIMENT.name,
        "dataset": s["dataset"],
        "total_instances": s["total_instances"],
        "criterion": s["criterion"],
        "overall_applicable": s["overall_applicable"],
        "overall_applicability_rate": s["overall_applicability_rate"],
        "per_repo": by_repo,
        "high_applicability_repos": sorted(high),
        "low_applicability_repos": sorted(low),
        "upper_bound_note": "structural applicability (single source file, narrow FAIL_TO_PASS) is necessary but not sufficient: an applicable instance still needs a function with a derivable gold-free property, abundant in mathematical libraries and rarer in application libraries; this rate is an upper bound on the property layer's reach, not the property genuine-sound rate",
        "benchmark_or_sota_claim": False,
    }
    bars = {
        "survey_covers_full_dataset": s["total_instances"] == 500,
        "overall_rate_recorded": 0.0 <= s["overall_applicability_rate"] <= 1.0,
        "upper_bound_stated": "upper bound" in endpoints["upper_bound_note"],
    }
    status = "pass" if all(bars.values()) else "null"

    receipt = {
        "receipt_id": f"iter138-applicability-survey-{status}",
        "task_id": "telos:iter138_applicability_survey",
        "agent_id": "codex-local-applicability-survey-analyst",
        "benchmark_id": "swebench_verified_applicability_survey_v0",
        "status": status,
        "stated_goal": "Measure the property-layer structural applicability across the full dataset by repo, as an upper bound on its reach.",
        "acceptance_criteria": [
            "The survey covers all 500 instances.",
            "The overall and per-repo applicability rates are recorded.",
            "The rate is framed as an upper bound, not the property genuine-sound rate.",
        ],
        "evidence": [
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json"},
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/applicability_survey.json"},
        ],
        "falsifiers": [
            "Do not present the structural criterion as the property genuine-sound rate.",
            "Report low-applicability repos as-is.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)

    learning = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT.name,
        "status": status,
        "result_path": f"experiments/{EXPERIMENT.name}/RESULT.md",
        "evidence_paths": [f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json", f"experiments/{EXPERIMENT.name}/proof/applicability_survey.json"],
        "insight": f"the property layer's single-testable-function criterion is met by {s['overall_applicable']}/500 = {s['overall_applicability_rate']} of SWE-bench Verified (scikit-learn 0.94, sympy 0.89 high; pylint 0.40, requests/seaborn 0.50 low) - a broad structural reach, but an upper bound because property-derivability within it is function-dependent (high for math, lower for application libraries)",
        "next_action": "within the high-applicability repos, measure the fraction of applicable instances that admit a derivable gold-free property, to turn the upper bound into a property-derivability rate",
    }

    _write(PROOF / "endpoint_results.json", endpoints)
    _write(VALID / "receipt_applicability_survey.json", receipt)
    _write(PROOF / "learning_record.json", learning)
    _write(PROOF / "run_summary.json", {"schema_version": "telos.applicability_survey.summary.v1", "experiment_id": EXPERIMENT.name, "status": status, "endpoints": endpoints})

    print(f"status={status}")
    print(f"overall_applicability={s['overall_applicable']}/500 = {s['overall_applicability_rate']} (upper bound on Layer 3 reach)")
    print(f"high (>=0.8): {sorted(high)}")
    print(f"low (<0.6): {sorted(low)}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
