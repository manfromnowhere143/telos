#!/usr/bin/env python3
"""Build or verify the artifact-bound iter219 temporal-yield receipt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from telos.proof import (  # noqa: E402
    RECEIPT_V2_SCHEMA,
    build_artifact_binding,
    evidence_closure_digest,
    load_receipt_v2,
    receipt_v2_digest,
    validate_receipt_v2,
)

EXPERIMENT = "experiments/iter219_temporal_consequence_test_yield"
RECEIPT_PATH = ROOT / EXPERIMENT / "proof/receipt_v2.json"
PREDECESSOR_MERGE = "470ca3627b7635d9a315cf2811ceb2eed6575fb9"
SEALED_HYPOTHESIS = "79311824e2732d09e69742ea7b566fc91e0e04ab"
PRODUCER = "iter219-temporal-consequence-test-yield"
BINDINGS = {
    f"{EXPERIMENT}/HYPOTHESIS.md": "artifact",
    f"{EXPERIMENT}/RESULT.md": "artifact",
    f"{EXPERIMENT}/proof/analysis_amendment.json": "adversarial_review",
    f"{EXPERIMENT}/proof/yield_report.json": "artifact",
    "scripts/build_iter219_receipt.py": "build",
    "scripts/measure_iter219_temporal_yield.py": "build",
    "scripts/validate_iter219_temporal_consequence_test_yield.py": "adversarial_review",
    "telos/tcp1.py": "build",
    "tests/test_iter219_temporal_yield.py": "test",
}


def media_type(path: str) -> str:
    return {
        ".json": "application/json",
        ".md": "text/markdown; charset=utf-8",
        ".py": "text/x-python; charset=utf-8",
        ".yml": "application/yaml",
    }.get(Path(path).suffix, "application/octet-stream")


def build_receipt() -> dict[str, object]:
    evidence = [
        {
            "kind": BINDINGS[path],
            "status": "pass",
            "artifact": build_artifact_binding(
                ROOT, path, media_type=media_type(path), producer=PRODUCER
            ),
        }
        for path in sorted(BINDINGS)
    ]
    receipt: dict[str, object] = {
        "schema_version": RECEIPT_V2_SCHEMA,
        "receipt_id": "telos-iter219-temporal-consequence-test-yield-v2",
        "task_id": "iter219_temporal_consequence_test_yield",
        "agent_id": "claude-local-measurement-auditor",
        "benchmark_id": "telos-iter219-temporal-yield-screen",
        "status": "pass",
        "stated_goal": (
            "Measure whether test functions added after a task's base commit statically "
            "reference the task's touched symbols above two matched controls, without any "
            "provider call, accelerator, container, or repository test execution."
        ),
        "acceptance_criteria": [
            "The hypothesis was sealed before any instance was scored.",
            "Amendments A1, A2, and A3 were recorded before any overlap or control count existed.",
            "The instrument's frozen constants equal the sealed hypothesis rules.",
            "Every reported number recomputes from the report's own rows.",
            "Every excluded instance is reported with an exact machine-readable reason.",
            "Static token overlap is reported as a screen, never as executed coverage.",
            "No provider call, GPU allocation, container, or repository test execution occurs.",
        ],
        "evidence": evidence,
        "falsifiers": [
            "Any outcome was observed before the hypothesis was sealed.",
            "Any sample rule, qualification rule, window, seed, or bar changed after observation.",
            "A test function added by the task's own test_patch is counted as hidden evidence.",
            "Either control's interval overlaps the primary's at the primary window.",
            "Static token overlap is described as proving executed coverage.",
            "The screen is described as establishing TCP-1 feasibility or any model behavior.",
            "Any provider, accelerator, container, payment, dispatch, or release action occurs.",
        ],
        "evidence_closure_sha256": evidence_closure_digest(evidence),
        "receipt_sha256": "",
    }
    receipt["receipt_sha256"] = receipt_v2_digest(receipt)
    return receipt


def rendered_receipt() -> str:
    return json.dumps(build_receipt(), indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="verify the committed receipt instead of writing it"
    )
    args = parser.parse_args()

    if args.check:
        if not RECEIPT_PATH.exists():
            print("iter219 receipt missing")
            return 1
        committed = load_receipt_v2(RECEIPT_PATH)
        validate_receipt_v2(committed)
        expected = build_receipt()
        if committed.get("evidence_closure_sha256") != expected["evidence_closure_sha256"]:
            print("iter219 receipt closure does not match the committed artifacts")
            return 1
        if committed.get("receipt_sha256") != expected["receipt_sha256"]:
            print("iter219 receipt digest does not match its contents")
            return 1
        print(f"iter219 receipt verified (evidence={len(expected['evidence'])})")
        return 0

    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(rendered_receipt(), encoding="utf-8")
    receipt = build_receipt()
    print(f"iter219 receipt written (evidence={len(receipt['evidence'])})")
    print(f"  closure sha256: {receipt['evidence_closure_sha256']}")
    print(f"  receipt sha256: {receipt['receipt_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
