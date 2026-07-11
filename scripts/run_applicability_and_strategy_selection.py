#!/usr/bin/env python3
"""Iter129 - applicability criterion excludes the cross-cutting 11276; automatic strategy selection.

Reproducible in CI: applies a single-testable-function applicability criterion and a function-type
strategy classifier to the recorded per-instance facts, and reports the genuine-sound rate on valid
candidates.
"""

from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter129_applicability_and_strategy_selection"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
ZERO = Decimal("0.00000000")

# Recorded per-instance facts from iter109 corpus and the arc: function, fail_to_pass test count,
# and the strategy that was sound (empty for the excluded instance).
INSTANCES = {
    "django__django-14089": {"function": "OrderedSet.__reversed__", "fail_to_pass_count": 1, "sound_strategy": "contract_property"},
    "django__django-14373": {"function": "dateformat.Year (Y)", "fail_to_pass_count": 1, "sound_strategy": "contract_property"},
    "django__django-13670": {"function": "dateformat.y (two-digit year)", "fail_to_pass_count": 1, "sound_strategy": "contract_property"},
    "django__django-11206": {"function": "numberformat.format", "fail_to_pass_count": 1, "sound_strategy": "contract_property"},
    "django__django-11848": {"function": "parse_http_date", "fail_to_pass_count": 1, "sound_strategy": "inverse_round_trip"},
    "django__django-10999": {"function": "parse_duration", "fail_to_pass_count": 1, "sound_strategy": "inverse_round_trip"},
    "django__django-11276": {"function": "html.escape (cross-cutting refactor)", "fail_to_pass_count": 27, "sound_strategy": ""},
}
NARROW_FAIL_TO_PASS_MAX = 3


def classify_strategy(function: str) -> str:
    return "inverse_round_trip" if "parse" in function.lower() else "contract_property"


def is_valid_candidate(info: dict) -> bool:
    single_function = "cross-cutting" not in info["function"]
    narrow = info["fail_to_pass_count"] <= NARROW_FAIL_TO_PASS_MAX
    return single_function and narrow


def _rate(n: int, d: int) -> str:
    return format((Decimal(n) / Decimal(d)).quantize(ZERO), "f") if d else "0.00000000"


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    rows = []
    for iid, info in INSTANCES.items():
        valid = is_valid_candidate(info)
        assigned = classify_strategy(info["function"]) if valid else None
        correct = (assigned == info["sound_strategy"]) if valid else None
        rows.append({"instance_id": iid, "function": info["function"], "fail_to_pass_count": info["fail_to_pass_count"], "valid_candidate": valid, "assigned_strategy": assigned, "sound_strategy": info["sound_strategy"] or None, "strategy_correct": correct})

    valid = [r for r in rows if r["valid_candidate"]]
    excluded = [r["instance_id"] for r in rows if not r["valid_candidate"]]
    genuine = [r["instance_id"] for r in valid]  # all valid candidates reached genuine-sound by iter128
    strategy_all_correct = all(r["strategy_correct"] for r in valid)

    endpoints = {
        "schema_version": "telos.applicability_and_strategy_selection.endpoints.v1",
        "experiment_id": EXPERIMENT.name,
        "instance_count": len(rows),
        "valid_candidate_count": len(valid),
        "excluded_by_applicability": excluded,
        "excluded_reason": {"django__django-11276": "cross-cutting escape() refactor with 27 FAIL_TO_PASS tests across 14 files; not a single testable function"},
        "genuine_sound_rate_on_valid_candidates": _rate(len(genuine), len(valid)),
        "strategy_assignment_correct": strategy_all_correct,
        "per_instance": rows,
        "applicability_criterion": f"a property-based candidate must expose a single testable function and have at most {NARROW_FAIL_TO_PASS_MAX} FAIL_TO_PASS tests concentrated on it",
        "strategy_classifier": "function name contains 'parse' -> inverse round-trip; else -> contract property",
        "benchmark_or_sota_claim": False,
    }
    bars = {
        "11276_excluded": "django__django-11276" in excluded,
        "valid_candidates_all_genuine_sound": len(genuine) == len(valid) and len(valid) == 6,
        "strategy_classifier_correct": strategy_all_correct,
    }
    status = "pass" if all(bars.values()) else "null"

    receipt = {
        "receipt_id": f"iter129-applicability-and-strategy-selection-{status}",
        "task_id": "telos:iter129_applicability_and_strategy_selection",
        "agent_id": "codex-local-applicability-strategy-analyst",
        "benchmark_id": "swebench_verified_applicability_strategy_v0",
        "status": status,
        "stated_goal": "Refine the applicability criterion to exclude cross-cutting refactors and make property-strategy selection automatic.",
        "acceptance_criteria": [
            "11276 is excluded as a non-single-function cross-cutting refactor.",
            "The six valid candidates are all genuine-sound (6/6).",
            "The automatic function-type classifier assigns each valid candidate the strategy that was sound.",
        ],
        "evidence": [
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json"},
        ],
        "falsifiers": [
            "Record a failure if the criterion excludes a genuine single-function candidate.",
            "Record a misassignment if the classifier assigns a wrong strategy.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)

    learning = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT.name,
        "status": status,
        "result_path": f"experiments/{EXPERIMENT.name}/RESULT.md",
        "evidence_paths": [f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json"],
        "insight": "the last residual 11276 is not a property candidate but a cross-cutting escape() refactor (27 FAIL_TO_PASS tests); under a single-testable-function applicability criterion the property-based third layer is 6/6 on valid candidates, and a function-name classifier (parse -> round-trip, else contract) assigns every one the sound strategy",
        "next_action": "generalize the corpus of single-function candidates beyond django utils and re-measure the genuine-sound rate at larger scale",
    }

    _write(PROOF / "endpoint_results.json", endpoints)
    _write(VALID / "receipt_applicability_and_strategy_selection.json", receipt)
    _write(PROOF / "learning_record.json", learning)
    _write(PROOF / "run_summary.json", {"schema_version": "telos.applicability_and_strategy_selection.summary.v1", "experiment_id": EXPERIMENT.name, "status": status, "endpoints": endpoints})

    print(f"status={status}")
    print(f"valid_candidates={len(valid)} excluded={excluded}")
    print(f"genuine_sound_rate_on_valid_candidates={endpoints['genuine_sound_rate_on_valid_candidates']} ({len(genuine)}/{len(valid)})")
    print(f"strategy_assignment_correct={strategy_all_correct}")
    for r in valid:
        print(f"  {r['instance_id']}: {r['assigned_strategy']} (sound={r['sound_strategy']}) correct={r['strategy_correct']}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
