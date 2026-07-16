#!/usr/bin/env python3
"""Build or verify the artifact-bound iter214 numeric-recovery receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
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


EXPERIMENT = "experiments/iter214_tcp1_cross_platform_numeric_recovery"
RECEIPT_PATH = ROOT / EXPERIMENT / "proof/receipt_v2.json"
PREDECESSOR_SEAL = "dbe008211022e0abdff5bc9e47e871b02b6d5501"
PRODUCER = "iter214-tcp1-cross-platform-numeric-recovery"
BINDINGS = {
    ".github/workflows/ci.yml": "build",
    "README.md": "artifact",
    "docs/MISSION_LOOP.md": "artifact",
    "docs/TELOS-ROADMAP-2026.md": "artifact",
    f"{EXPERIMENT}/HYPOTHESIS.md": "artifact",
    f"{EXPERIMENT}/RESULT.md": "artifact",
    f"{EXPERIMENT}/proof/analysis_amendment.json": "adversarial_review",
    f"{EXPERIMENT}/proof/ci_failure.json": "adversarial_review",
    "mission/loop.json": "artifact",
    "scripts/build_iter214_handoff.py": "build",
    "scripts/build_iter214_receipt.py": "build",
    "scripts/validate_current_paper.py": "adversarial_review",
    "scripts/validate_handoff.py": "adversarial_review",
    "scripts/validate_iter213_post_seal_validation_recovery.py": "adversarial_review",
    "scripts/validate_iter214_tcp1_cross_platform_numeric_recovery.py": "adversarial_review",
    "scripts/validate_mission_loop.py": "adversarial_review",
    "telos/tcp1.py": "build",
    "tests/test_iter214_tcp1_cross_platform_numeric_recovery.py": "test",
    "tests/test_make_handoff.py": "test",
    "tests/test_mission_loop_guard.py": "test",
    "tests/test_tcp1.py": "test",
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
        "receipt_id": "telos-iter214-tcp1-cross-platform-numeric-recovery-v2",
        "task_id": "iter214_tcp1_cross_platform_numeric_recovery",
        "agent_id": "codex-local-publication-auditor",
        "benchmark_id": "telos-tcp1-pre-data-numeric-recovery",
        "status": "pass",
        "stated_goal": (
            "Canonicalize exact Wilson boundaries and recover sealed descendant validation "
            "without changing TCP-1 data, interior analysis, or predecessor evidence."
        ),
        "acceptance_criteria": [
            "Wilson k=0 lower and k=n upper endpoints are exact across supported platforms.",
            "The interior Wilson formula and every other TCP-1 analysis rule remain unchanged.",
            "Iter211 through iter213 experiment bytes remain unchanged.",
            "The failed iter213 branch and pull request remain fixed and are not rerun.",
            "Every iter214 source artifact except this self-referential receipt is byte-bound.",
            "The complete provider-free suite and synthetic-merge simulation pass.",
            "No provider, accelerator, scientific, dispatch, payment, release, or deployment action occurs.",
        ],
        "evidence": evidence,
        "falsifiers": [
            "Any predecessor experiment byte changes.",
            "Any interior Wilson estimate or TCP-1 endpoint, cohort, control, or missingness rule changes.",
            "Any sealed predecessor validator treats additive descendant evidence as predecessor scope.",
            "Any failed iter213 branch mutation or workflow rerun occurs.",
            "Any iter214 source delta is absent from the receipt closure.",
            "Any scientific or provider action occurs.",
        ],
        "evidence_closure_sha256": evidence_closure_digest(evidence),
        "receipt_sha256": "",
    }
    receipt["receipt_sha256"] = receipt_v2_digest(receipt)
    return receipt


def rendered_receipt() -> str:
    return json.dumps(build_receipt(), indent=2, ensure_ascii=False) + "\n"


def git_bytes(*arguments: str) -> bytes:
    result = subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, check=False)
    if result.returncode != 0:
        diagnostic = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git command failed: {' '.join(arguments)}: {diagnostic}")
    return result.stdout


def sealed_source_commit() -> str | None:
    """Resolve iter214's source by parent topology, independent of the handoff."""

    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", PREDECESSOR_SEAL, "HEAD"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    rows = git_bytes(
        "rev-list", "--ancestry-path", "--parents", f"{PREDECESSOR_SEAL}..HEAD"
    ).decode().splitlines()
    candidates: list[str] = []
    relative = RECEIPT_PATH.relative_to(ROOT).as_posix()
    for line in rows:
        row = line.split()
        if len(row) != 2 or row[1] != PREDECESSOR_SEAL:
            continue
        exists = subprocess.run(
            ["git", "cat-file", "-e", f"{row[0]}:{relative}"],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        if exists.returncode == 0:
            candidates.append(row[0])
    if not candidates:
        return None
    if len(candidates) != 1:
        raise RuntimeError("cannot resolve exactly one iter214 source child")
    return candidates[0]


def verify_sealed_receipt(source: str) -> int:
    relative = RECEIPT_PATH.relative_to(ROOT).as_posix()
    payload = git_bytes("show", f"{source}:{relative}")
    if RECEIPT_PATH.read_bytes() != payload:
        raise RuntimeError("iter214 receipt differs from source Git blob")
    receipt = validate_receipt_v2(json.loads(payload.decode("utf-8")))
    for item in receipt.evidence:
        artifact = item["artifact"]
        artifact_payload = git_bytes("show", f"{source}:{artifact['path']}")
        if len(artifact_payload) != artifact["bytes"] or (
            hashlib.sha256(artifact_payload).hexdigest() != artifact["sha256"]
        ):
            raise RuntimeError(f"iter214 sealed artifact differs: {artifact['path']}")
    return len(receipt.evidence)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    source = sealed_source_commit()
    if args.check and source is not None:
        count = verify_sealed_receipt(source)
        print(f"iter214 receipt builder: clean sealed {count}-artifact closure")
        return 0
    if source is not None:
        print("iter214 receipt builder: refusing to rewrite sealed source")
        return 1
    rendered = rendered_receipt()
    if args.check:
        if not RECEIPT_PATH.is_file() or RECEIPT_PATH.read_text(encoding="utf-8") != rendered:
            print("iter214 receipt builder: committed receipt differs")
            return 1
        receipt = load_receipt_v2(RECEIPT_PATH, artifact_root=ROOT)
        if receipt.status != "pass":
            print("iter214 receipt builder: recovery receipt is not pass")
            return 1
        print(f"iter214 receipt builder: clean {len(BINDINGS)}-artifact closure")
        return 0
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(rendered, encoding="utf-8")
    print(f"iter214 receipt builder: wrote {len(BINDINGS)}-artifact closure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
