#!/usr/bin/env python3
"""Build or verify the artifact-bound iter222 admission-evidence receipt."""

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

EXPERIMENT = "experiments/iter222_tcp1_agent_solvable_admission_evidence"
RECEIPT_PATH = ROOT / EXPERIMENT / "proof/receipt_v2.json"
PREDECESSOR_SEAL = "b38d8921d30ca665692afc024b4f0e3706902f78"

PRODUCER = "iter222-tcp1-agent-solvable-admission-evidence"
BINDINGS = {
    f"{EXPERIMENT}/HYPOTHESIS.md": "artifact",
    f"{EXPERIMENT}/RESULT.md": "artifact",
    f"{EXPERIMENT}/proof/admission_view.json": "artifact",
    f"{EXPERIMENT}/proof/isolation_rehearsal.json": "adversarial_review",
    f"{EXPERIMENT}/proof/model_binding.json": "artifact",
    f"{EXPERIMENT}/proof/transparency_timestamp.json": "adversarial_review",
    f"{EXPERIMENT}/proof/timestamp_commitment.json": "artifact",
    "scripts/build_iter222_admission_view.py": "build",
    "scripts/build_iter222_model_binding.py": "build",
    "scripts/build_iter222_receipt.py": "build",
    "scripts/build_iter222_transparency_timestamp.py": "build",
    "scripts/run_iter222_isolation_rehearsal.py": "build",
    "scripts/validate_iter222_tcp1_agent_solvable_admission_evidence.py": "adversarial_review",
    "tests/test_iter222_admission_evidence.py": "test",
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
        "receipt_id": "telos-iter222-tcp1-agent-solvable-admission-evidence-v2",
        "task_id": "iter222_tcp1_agent_solvable_admission_evidence",
        "agent_id": "claude-local-publication-auditor",
        "benchmark_id": "telos-iter222-tcp1-admission-evidence",
        "status": "pass",
        "stated_goal": (
            "Fill the three agent-solvable TCP-1 admission gates with independently "
            "verifiable evidence at zero spend: a live-digest model binding, a real RFC "
            "3161 transparency timestamp, and a hostile isolation rehearsal with positive "
            "controls, moving admission from 2/11 to 5/11 without authorizing execution."
        ),
        "acceptance_criteria": [
            "At least three source-linked model candidates with a default bound to live license, cutoff, commit, and weight+tokenizer digests.",
            "A real RFC 3161 timestamp token that verifies against its authority chain and re-verifies offline.",
            "Five registered attacks denied by the real contract and not-denied under each weakened contract.",
            "An admission view of exactly 5 pass, 6 blocked, with execution unauthorized.",
            "No model or provider inference, no weight download, no accelerator, no container, and no scientific action occurs.",
        ],
        "evidence": evidence,
        "falsifiers": [
            "Any model digest, license, or cutoff is invented or does not match the live public record.",
            "A timestamp token is fabricated or a Git commit is described as the external timestamp.",
            "The isolation rehearsal passes the real contract without catching the attack under a weakened contract.",
            "Any admission gate beyond the three named is described as filled, or execution becomes authorized.",
            "A published digest is described as proving the model runs, or a denied rehearsal as proving runtime isolation.",
            "Any scientific, provider, accelerator, container, dispatch, payment, or release action occurs.",
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
            print("iter222 receipt missing")
            return 1
        committed = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        validate_receipt_v2(committed)
        # A sealed receipt validates its own source blobs, never a descendant's tree: a
        # later iteration legitimately edits shared files this receipt binds.
        if receipt_is_committed(ROOT, RECEIPT_PATH):
            try:
                source, count = verify_against_source(ROOT, RECEIPT_PATH)
            except ReceiptSealingError as error:
                print(f"iter222 receipt: {error}")
                return 1
            print(f"iter222 receipt verified at sealed source {source[:12]} (evidence={count})")
            return 0
        expected = build_receipt()
        if committed.get("evidence_closure_sha256") != expected["evidence_closure_sha256"]:
            print("iter222 receipt closure does not match the committed artifacts")
            return 1
        if committed.get("receipt_sha256") != expected["receipt_sha256"]:
            print("iter222 receipt digest does not match its contents")
            return 1
        print(f"iter222 receipt verified (evidence={len(expected['evidence'])})")
        return 0

    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(rendered_receipt(), encoding="utf-8")
    receipt = build_receipt()
    print(f"iter222 receipt written (evidence={len(receipt['evidence'])})")
    print(f"  closure sha256: {receipt['evidence_closure_sha256']}")
    print(f"  receipt sha256: {receipt['receipt_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
