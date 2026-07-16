#!/usr/bin/env python3
"""Build or check the artifact-bound iter210 PR-topology recovery receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
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


RECEIPT_PATH = ROOT / "experiments/iter210_pr_synthetic_merge_recovery/proof/receipt_v2.json"
PRODUCER = "iter210-pr-synthetic-merge-recovery"
HANDOFF_SCHEMA = "telos.iter210.handoff.v1"
BINDINGS = {
    ".github/workflows/ci.yml": "build",
    "README.md": "artifact",
    "docs/MISSION_LOOP.md": "artifact",
    "experiments/iter210_pr_synthetic_merge_recovery/HYPOTHESIS.md": "artifact",
    "experiments/iter210_pr_synthetic_merge_recovery/RESULT.md": "artifact",
    "experiments/iter210_pr_synthetic_merge_recovery/proof/pr_synthetic_merge_failure.json": "adversarial_review",
    "mission/loop.json": "artifact",
    "scripts/build_iter209_receipt.py": "adversarial_review",
    "scripts/build_iter210_receipt.py": "build",
    "scripts/validate_handoff.py": "adversarial_review",
    "scripts/validate_iter209_publication_ci_recovery.py": "adversarial_review",
    "scripts/validate_iter210_pr_synthetic_merge_recovery.py": "adversarial_review",
    "scripts/validate_mission_loop.py": "adversarial_review",
    "tests/test_iter209_publication_ci_recovery.py": "test",
    "tests/test_iter210_pr_synthetic_merge_recovery.py": "test",
    "tests/test_make_handoff.py": "test",
    "tests/test_mission_loop_guard.py": "test",
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
        "receipt_id": "telos-iter210-pr-synthetic-merge-recovery-v2",
        "task_id": "iter210_pr_synthetic_merge_recovery",
        "agent_id": "codex-local-publication-auditor",
        "benchmark_id": "telos-pr-topology-recovery",
        "status": "pass",
        "stated_goal": "Recover PR synthetic-merge validation without rewriting the public iter209 seal.",
        "acceptance_criteria": [
            "The public iter209 branch remains unchanged and auditable.",
            "Push, PR synthetic merge, merged master, and descendant validation select exact sealed history.",
            "Sealed receipts verify source Git blobs and refuse descendant rewrites.",
            "Every iter210 source delta except this self-referential receipt is artifact-bound.",
            "No provider, GPU, scientific container, dispatch, release, or scientific action occurs.",
        ],
        "evidence": evidence,
        "falsifiers": [
            "Any historical experiment artifact changes.",
            "Synthetic-merge validation selects HEAD instead of the branch seal.",
            "The receipt omits an iter210 source delta.",
            "Any scientific or provider action occurs.",
            "Either fresh remote CI matrix fails at the exact sealed tip.",
        ],
        "evidence_closure_sha256": evidence_closure_digest(evidence),
        "receipt_sha256": "",
    }
    receipt["receipt_sha256"] = receipt_v2_digest(receipt)
    return receipt


def rendered_receipt() -> str:
    return json.dumps(build_receipt(), indent=2, ensure_ascii=False) + "\n"


def _git_bytes(*arguments: str) -> bytes:
    result = subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, check=False)
    if result.returncode != 0:
        diagnostic = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git command failed: {' '.join(arguments)}: {diagnostic}")
    return result.stdout


def sealed_source_commit() -> str | None:
    handoff = (ROOT / "HANDOFF.md").read_text(encoding="utf-8")
    if f"handoff_schema: {HANDOFF_SCHEMA}" not in handoff:
        return None
    match = re.search(r"^source_commit: ([0-9a-f]{40})$", handoff, re.MULTILINE)
    if match is None:
        raise RuntimeError("iter210 handoff lacks one exact source commit")
    source = match.group(1)
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", source, "HEAD"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("iter210 handoff source is not in current Git history")
    return source


def verify_sealed_receipt(source: str) -> int:
    relative = RECEIPT_PATH.relative_to(ROOT).as_posix()
    payload = _git_bytes("show", f"{source}:{relative}")
    if RECEIPT_PATH.read_bytes() != payload:
        raise RuntimeError("iter210 receipt differs from source Git blob")
    receipt = validate_receipt_v2(json.loads(payload.decode("utf-8")))
    for item in receipt.evidence:
        artifact = item["artifact"]
        artifact_payload = _git_bytes("show", f"{source}:{artifact['path']}")
        if len(artifact_payload) != artifact["bytes"] or (
            hashlib.sha256(artifact_payload).hexdigest() != artifact["sha256"]
        ):
            raise RuntimeError(f"iter210 sealed artifact differs: {artifact['path']}")
    return len(receipt.evidence)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    source = sealed_source_commit()
    if args.check and source is not None:
        count = verify_sealed_receipt(source)
        print(f"iter210 receipt builder: clean sealed {count}-artifact closure")
        return 0
    if source is not None:
        print("iter210 receipt builder: refusing to rewrite sealed source")
        return 1
    rendered = rendered_receipt()
    if args.check:
        if not RECEIPT_PATH.is_file() or RECEIPT_PATH.read_text(encoding="utf-8") != rendered:
            print("iter210 receipt builder: committed receipt differs")
            return 1
        load_receipt_v2(RECEIPT_PATH, artifact_root=ROOT)
        print(f"iter210 receipt builder: clean {len(BINDINGS)}-artifact closure")
        return 0
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(rendered, encoding="utf-8")
    print(f"iter210 receipt builder: wrote {len(BINDINGS)}-artifact closure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
