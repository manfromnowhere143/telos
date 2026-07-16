#!/usr/bin/env python3
"""Build or check the artifact-bound iter209 publication-recovery receipt."""

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
)


RECEIPT_PATH = (
    ROOT / "experiments/iter209_publication_ci_recovery/proof/receipt_v2.json"
)
PRODUCER = "iter209-publication-ci-recovery"
BINDINGS = {
    ".github/workflows/ci.yml": "build",
    "README.md": "artifact",
    "docs/MISSION_LOOP.md": "artifact",
    "experiments/iter209_publication_ci_recovery/HYPOTHESIS.md": "artifact",
    "experiments/iter209_publication_ci_recovery/RESULT.md": "artifact",
    "experiments/iter209_publication_ci_recovery/proof/ci_failure_diagnosis.json": "adversarial_review",
    "mission/loop.json": "artifact",
    "scripts/audit_receipt_schema_prompt_alignment.py": "adversarial_review",
    "scripts/build_iter209_receipt.py": "build",
    "scripts/validate_current_paper.py": "adversarial_review",
    "scripts/validate_handoff.py": "adversarial_review",
    "scripts/validate_iter208_post_seal_forensic_correction.py": "adversarial_review",
    "scripts/validate_iter209_publication_ci_recovery.py": "adversarial_review",
    "scripts/validate_mission_loop.py": "adversarial_review",
    "tests/test_iter209_publication_ci_recovery.py": "test",
    "tests/test_make_handoff.py": "test",
    "tests/test_mission_loop_guard.py": "test",
}


def media_type(path: str) -> str:
    suffix = Path(path).suffix
    return {
        ".json": "application/json",
        ".md": "text/markdown; charset=utf-8",
        ".py": "text/x-python; charset=utf-8",
        ".yml": "application/yaml",
        ".yaml": "application/yaml",
    }.get(suffix, "application/octet-stream")


def build_receipt() -> dict[str, object]:
    evidence = [
        {
            "kind": BINDINGS[path],
            "status": "pass",
            "artifact": build_artifact_binding(
                ROOT,
                path,
                media_type=media_type(path),
                producer=PRODUCER,
            ),
        }
        for path in sorted(BINDINGS)
    ]
    receipt: dict[str, object] = {
        "schema_version": RECEIPT_V2_SCHEMA,
        "receipt_id": "telos-iter209-publication-ci-recovery-v2",
        "task_id": "iter209_publication_ci_recovery",
        "agent_id": "codex-local-publication-auditor",
        "benchmark_id": "telos-publication-ci-recovery",
        "status": "pass",
        "stated_goal": (
            "Recover from the failed iter208 publication CI without rewriting its "
            "public seal or changing scientific evidence."
        ),
        "acceptance_criteria": [
            "The failed iter208 publication branch remains unchanged and auditable.",
            "Historical source hashes resolve from their exact sealed Git tree.",
            "GitHub pull-request environment is isolated in publication-lineage tests.",
            "Iter208 receipt validation remains correct on descendants.",
            "Every iter209 source delta except this self-referential receipt is artifact-bound.",
            "No provider, GPU, scientific container, dispatch, release, or scientific action occurs.",
        ],
        "evidence": evidence,
        "falsifiers": [
            "Any historical experiment artifact changes.",
            "Either original CI failure still reproduces.",
            "The receipt omits an iter209 source delta.",
            "Any scientific or provider action occurs.",
            "Either fresh branch or pull-request CI matrix fails at the sealed tip.",
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
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = rendered_receipt()
    if args.check:
        if not RECEIPT_PATH.is_file() or RECEIPT_PATH.read_text(encoding="utf-8") != rendered:
            print("iter209 receipt builder: committed receipt differs")
            return 1
        load_receipt_v2(RECEIPT_PATH, artifact_root=ROOT)
        print(f"iter209 receipt builder: clean {len(BINDINGS)}-artifact closure")
        return 0
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(rendered, encoding="utf-8")
    print(f"iter209 receipt builder: wrote {len(BINDINGS)}-artifact closure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
