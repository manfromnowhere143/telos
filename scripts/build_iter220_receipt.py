#!/usr/bin/env python3
"""Build or verify the artifact-bound iter220 publication-recovery receipt."""

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
    receipt_v2_digest,
    validate_receipt_v2,
)

EXPERIMENT = "experiments/iter220_iter219_publication_ci_recovery"
RECEIPT_PATH = ROOT / EXPERIMENT / "proof/receipt_v2.json"
PREDECESSOR_SEAL = "11e335e82100319a4f5f47d86eaea0c8e81edbbc"

PRODUCER = "iter220-iter219-publication-ci-recovery"
BINDINGS = {
    ".github/workflows/ci.yml": "build",
    f"{EXPERIMENT}/HYPOTHESIS.md": "artifact",
    f"{EXPERIMENT}/RESULT.md": "artifact",
    f"{EXPERIMENT}/proof/ci_failure.json": "adversarial_review",
    "README.md": "artifact",
    "scripts/build_iter220_receipt.py": "build",
    "scripts/run_ci_closure.py": "build",
    "scripts/validate_detector_methodology_correction.py": "adversarial_review",
    "scripts/validate_iter220_iter219_publication_ci_recovery.py": "adversarial_review",
    "tests/test_iter220_publication_ci_recovery.py": "test",
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
        "receipt_id": "telos-iter220-iter219-publication-ci-recovery-v2",
        "task_id": "iter220_iter220_publication_ci_recovery",
        "agent_id": "claude-local-publication-auditor",
        "benchmark_id": "telos-iter220-publication-recovery",
        "status": "pass",
        "stated_goal": (
            "Recover iter219's publication CI by root-causing a required-phrase scanner that "
            "a markdown line wrap defeats, and by replacing hand-listed local verification "
            "with a closure runner derived from the CI workflow, without changing any "
            "iter219 number or evidence byte."
        ),
        "acceptance_criteria": [
            "The required-phrase scanner reads a wrapped sentence and still fails on genuine absence.",
            "Local closure is derived from .github/workflows/ci.yml, never hand-listed.",
            "Every guard command CI declares passes locally at this seal.",
            "Iter219 HYPOTHESIS, RESULT, yield report, and amendment are byte-identical to their seal.",
            "The failed iter219 branch and pull request remain unmutated, unrerun, and unmerged.",
            "No provider, accelerator, container, dispatch, payment, release, or scientific action occurs.",
        ],
        "evidence": evidence,
        "falsifiers": [
            "Any iter219 experiment byte changes.",
            "Any iter219 yield, control, interval, paired test, bar verdict, or claim boundary changes.",
            "The normalizer lets a required-phrase scan pass while the required meaning is absent.",
            "The closure runner omits a guard command that the CI workflow runs.",
            "The failed iter219 branch or pull request is mutated, extended, or rerun.",
            "Any scientific, provider, accelerator, dispatch, payment, or release action occurs.",
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
            print("iter220 receipt missing")
            return 1
        committed = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        validate_receipt_v2(committed)
        expected = build_receipt()
        if committed.get("evidence_closure_sha256") != expected["evidence_closure_sha256"]:
            print("iter220 receipt closure does not match the committed artifacts")
            return 1
        if committed.get("receipt_sha256") != expected["receipt_sha256"]:
            print("iter220 receipt digest does not match its contents")
            return 1
        print(f"iter220 receipt verified (evidence={len(expected['evidence'])})")
        return 0

    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(rendered_receipt(), encoding="utf-8")
    receipt = build_receipt()
    print(f"iter220 receipt written (evidence={len(receipt['evidence'])})")
    print(f"  closure sha256: {receipt['evidence_closure_sha256']}")
    print(f"  receipt sha256: {receipt['receipt_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
