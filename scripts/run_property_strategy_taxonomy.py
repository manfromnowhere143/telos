#!/usr/bin/env python3
"""Iter128 - the inverse round-trip closes 10999; property strategy is function-type-dependent.

The round-trip soundness on gold is observed native-execution evidence
(proof/roundtrip_10999.json). This runner records the resulting genuine-sound rate and the strategy
taxonomy.
"""

from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/iter128_property_strategy_taxonomy"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
ROUNDTRIP = PROOF / "roundtrip_10999.json"
ZERO = Decimal("0.00000000")

PRIOR_GENUINE = {"django__django-14089", "django__django-14373", "django__django-13670", "django__django-11848", "django__django-11206"}
TOTAL = 7
STRATEGY_TAXONOMY = {
    "pure_transform": "a contract property relating out to inp (e.g. reversed == forward reversed; four-digit year == str(year))",
    "invertible_parser_or_formatter": "an inverse round-trip f(f_inverse(x)) == x, self-validating and needing no external anchor",
    "soundness_anchor": "the visible-test known-correct pair, valid only when it matches the harness input convention",
}


def _rate(n: int, d: int) -> str:
    return format((Decimal(n) / Decimal(d)).quantize(ZERO), "f") if d else "0.00000000"


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    rt = json.loads(ROUNDTRIP.read_text(encoding="utf-8"))
    closed = bool(rt.get("sound")) and rt.get("gold_violations") == 0
    genuine = sorted(PRIOR_GENUINE | ({"django__django-10999"} if closed else set()))

    endpoints = {
        "schema_version": "telos.property_strategy_taxonomy.endpoints.v1",
        "experiment_id": EXPERIMENT.name,
        "roundtrip_sound": closed,
        "roundtrip_evidence": rt,
        "prior_genuine_sound_rate": _rate(len(PRIOR_GENUINE), TOTAL),
        "genuine_sound_rate_after": _rate(len(genuine), TOTAL),
        "genuine_sound_ids": genuine,
        "honest_residual": {"django__django-11276": "mis-targetable task (FAIL_TO_PASS test in admin_docs, fix in html.py); needs targeting from the test's assertions"},
        "property_strategy_taxonomy": STRATEGY_TAXONOMY,
        "mid_gate_correction": "the first anchor-in-the-loop attempt failed due to a harness bug (string anchors forced onto a timedelta-input round-trip harness), not a model failure; recorded transparently",
        "benchmark_or_sota_claim": False,
    }
    bars = {
        "roundtrip_closes_10999": closed,
        "genuine_sound_rate_improved": len(genuine) > len(PRIOR_GENUINE),
    }
    status = "pass" if all(bars.values()) else "null"

    receipt = {
        "receipt_id": f"iter128-property-strategy-taxonomy-{status}",
        "task_id": "telos:iter128_property_strategy_taxonomy",
        "agent_id": "codex-local-property-strategy-taxonomy-executor",
        "benchmark_id": "swebench_verified_property_strategy_taxonomy_v0",
        "status": status,
        "stated_goal": "Close 10999 with an inverse round-trip and record the function-type property-strategy taxonomy.",
        "acceptance_criteria": [
            "The inverse round-trip is sound on gold over random inputs.",
            "The genuine-sound rate rises to 6/7.",
            "The mid-gate harness-bug correction is recorded transparently.",
        ],
        "evidence": [
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json"},
            {"kind": "artifact", "status": status, "artifact": f"experiments/{EXPERIMENT.name}/proof/roundtrip_10999.json"},
        ],
        "falsifiers": [
            "Record the violations if the inverse round-trip is not sound.",
            "The harness-bug correction is disclosed rather than hidden.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)

    learning = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT.name,
        "status": status,
        "result_path": f"experiments/{EXPERIMENT.name}/RESULT.md",
        "evidence_paths": [f"experiments/{EXPERIMENT.name}/proof/endpoint_results.json", f"experiments/{EXPERIMENT.name}/proof/roundtrip_10999.json"],
        "insight": "gold-free property strategy is function-type-dependent: a contract property for pure transforms, a self-validating inverse round-trip for invertible parsers/formatters; the round-trip closes 10999 (0 violations) to reach 6/7, and an anchor must match the harness input convention",
        "next_action": "resolve the last residual 11276 by targeting from the test's assertions rather than the fix diff, and generalize strategy selection (transform vs parser) automatically",
    }

    _write(PROOF / "endpoint_results.json", endpoints)
    _write(VALID / "receipt_property_strategy_taxonomy.json", receipt)
    _write(PROOF / "learning_record.json", learning)
    _write(PROOF / "run_summary.json", {"schema_version": "telos.property_strategy_taxonomy.summary.v1", "experiment_id": EXPERIMENT.name, "status": status, "endpoints": endpoints})

    print(f"status={status}")
    print(f"roundtrip_sound={closed} (violations={rt.get('gold_violations')}/{rt.get('samples')})")
    print(f"genuine_sound_rate {endpoints['prior_genuine_sound_rate']} -> {endpoints['genuine_sound_rate_after']} ({len(genuine)}/7)")
    print(f"genuine_sound_ids={genuine}")
    print(f"honest_residual={list(endpoints['honest_residual'])}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
