#!/usr/bin/env python3
"""Build or verify the artifact-bound iter221 cross-platform tolerance receipt."""

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

from scripts.receipt_sealing import (  # noqa: E402
    ReceiptSealingError,
    receipt_is_committed,
    verify_against_source,
)

EXPERIMENT = "experiments/iter221_cross_platform_guard_tolerance"
RECEIPT_PATH = ROOT / EXPERIMENT / "proof/receipt_v2.json"
PREDECESSOR_SEAL = "3cee092420c2d13227005c8d78e584ec69da832f"

PRODUCER = "iter221-cross-platform-guard-tolerance"
BINDINGS = {
    ".github/workflows/ci.yml": "build",
    f"{EXPERIMENT}/HYPOTHESIS.md": "artifact",
    f"{EXPERIMENT}/RESULT.md": "artifact",
    f"{EXPERIMENT}/proof/ci_failure.json": "adversarial_review",
    "README.md": "artifact",
    "scripts/build_iter221_receipt.py": "build",
    "scripts/run_ci_closure.py": "build",
    "scripts/validate_iter219_temporal_consequence_test_yield.py": "adversarial_review",
    "scripts/validate_iter221_cross_platform_guard_tolerance.py": "adversarial_review",
    "telos/tcp1.py": "build",
    "tests/test_iter221_cross_platform_guard_tolerance.py": "test",
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
        "receipt_id": "telos-iter221-cross-platform-guard-tolerance-v2",
        "task_id": "iter221_cross_platform_guard_tolerance",
        "agent_id": "claude-local-publication-auditor",
        "benchmark_id": "telos-iter221-cross-platform-tolerance",
        "status": "pass",
        "stated_goal": (
            "Stop a guard from asserting bit-exact floating-point equality across machines, "
            "so that sqrt-derived Wilson intervals compare within a bounded tolerance while "
            "every exactly reproducible value stays exact, without changing any iter219 "
            "number or evidence byte."
        ),
        "acceptance_criteria": [
            "The guard passes at one ULP of platform drift and fails at 1e-9 relative tampering.",
            "No libm-derived value is compared bit-exactly anywhere in the guard set.",
            "The closure runner reports its interpreter and platform and accepts --python.",
            "Every guard command CI declares passes locally at this seal.",
            "Iter219 evidence and iter220 corrections are byte-identical to their seals.",
            "The failed iter219 and iter220 branches and pull requests remain unmutated and unmerged.",
            "No provider, accelerator, container, dispatch, payment, release, or scientific action occurs.",
        ],
        "evidence": evidence,
        "falsifiers": [
            "Any iter219 experiment byte changes.",
            "Any iter219 yield, control, interval, paired test, bar verdict, or claim boundary changes.",
            "The tolerance is loose enough to admit a tampered interval at 1e-9 relative.",
            "A libm-dependent value is compared bit-exactly anywhere in the guard set.",
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
            print("iter221 receipt missing")
            return 1
        committed = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        validate_receipt_v2(committed)
        # A sealed receipt validates its own source blobs, never a descendant's tree: a
        # later iteration legitimately edits shared files this receipt binds.
        if receipt_is_committed(ROOT, RECEIPT_PATH):
            try:
                source, count = verify_against_source(ROOT, RECEIPT_PATH)
            except ReceiptSealingError as error:
                print(f"iter221 receipt: {error}")
                return 1
            print(f"iter221 receipt verified at sealed source {source[:12]} (evidence={count})")
            return 0
        expected = build_receipt()
        if committed.get("evidence_closure_sha256") != expected["evidence_closure_sha256"]:
            print("iter221 receipt closure does not match the committed artifacts")
            return 1
        if committed.get("receipt_sha256") != expected["receipt_sha256"]:
            print("iter221 receipt digest does not match its contents")
            return 1
        print(f"iter221 receipt verified (evidence={len(expected['evidence'])})")
        return 0

    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(rendered_receipt(), encoding="utf-8")
    receipt = build_receipt()
    print(f"iter221 receipt written (evidence={len(receipt['evidence'])})")
    print(f"  closure sha256: {receipt['evidence_closure_sha256']}")
    print(f"  receipt sha256: {receipt['receipt_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
