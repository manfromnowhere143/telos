#!/usr/bin/env python3
"""Build or verify the artifact-bound iter211 TCP-1 preflight receipt."""

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


EXPERIMENT = "experiments/iter211_tcp1_materialization_preflight"
RECEIPT_PATH = ROOT / EXPERIMENT / "proof/receipt_v2.json"
PRODUCER = "iter211-tcp1-materialization-preflight"
HANDOFF_SCHEMA = "telos.iter211.handoff.v1"
ITER211_SOURCE_COMMIT = "1c99c9bf798fc2aadd1718a3ce77e2b55e9b0021"
ITER211_SEAL_COMMIT = "dc19e6f27f5a001632b5183ff798a6eacae6de33"
BINDINGS = {
    ".github/workflows/ci.yml": "build",
    "README.md": "artifact",
    "docs/MISSION_LOOP.md": "artifact",
    "docs/TELOS-ROADMAP-2026.md": "artifact",
    f"{EXPERIMENT}/HYPOTHESIS.md": "artifact",
    f"{EXPERIMENT}/RESULT.md": "artifact",
    f"{EXPERIMENT}/proof/action_ledger.json": "artifact",
    f"{EXPERIMENT}/proof/admission_report.json": "adversarial_review",
    f"{EXPERIMENT}/proof/analysis_plan.json": "artifact",
    f"{EXPERIMENT}/proof/control_plan.json": "artifact",
    f"{EXPERIMENT}/proof/execution_binding_ledger.json": "artifact",
    f"{EXPERIMENT}/proof/isolation_contract.json": "adversarial_review",
    f"{EXPERIMENT}/proof/merged_baseline.json": "artifact",
    f"{EXPERIMENT}/proof/protocol.json": "artifact",
    f"{EXPERIMENT}/proof/resource_budget.json": "artifact",
    f"{EXPERIMENT}/proof/review.md": "adversarial_review",
    f"{EXPERIMENT}/proof/reviewer_ledger.json": "artifact",
    f"{EXPERIMENT}/proof/schemas/aggregate.schema.json": "artifact",
    f"{EXPERIMENT}/proof/schemas/analysis-input.schema.json": "artifact",
    f"{EXPERIMENT}/proof/schemas/semantic-label.schema.json": "artifact",
    f"{EXPERIMENT}/proof/schemas/task.schema.json": "artifact",
    f"{EXPERIMENT}/proof/schemas/trace-event.schema.json": "artifact",
    f"{EXPERIMENT}/proof/schemas/trajectory.schema.json": "artifact",
    f"{EXPERIMENT}/proof/task_candidate_ledger.json": "artifact",
    "experiments/iter212_tcp1_independent_cohort_and_custody_freeze/HYPOTHESIS.md": "artifact",
    "mission/loop.json": "artifact",
    "scripts/build_iter211_handoff.py": "build",
    "scripts/build_iter211_receipt.py": "build",
    "scripts/build_iter211_tcp1_packet.py": "build",
    "scripts/validate_current_paper.py": "adversarial_review",
    "scripts/validate_handoff.py": "adversarial_review",
    "scripts/validate_iter211_tcp1_materialization_preflight.py": "adversarial_review",
    "scripts/validate_mission_loop.py": "adversarial_review",
    "telos/tcp1.py": "artifact",
    "tests/test_iter211_tcp1_materialization_preflight.py": "test",
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
        "receipt_id": "telos-iter211-tcp1-materialization-preflight-v2",
        "task_id": "iter211_tcp1_scientific_execution_admission",
        "agent_id": "codex-local-protocol-auditor",
        "benchmark_id": "telos-trace-consequence-pilot-1",
        "status": "blocked",
        "stated_goal": (
            "Admit TCP-1 scientific execution only after independent reviewers, a fresh task cohort, "
            "hidden tests, exact execution bindings, isolation, timestamp, throughput, and budget all pass."
        ),
        "acceptance_criteria": [
            "The zero-execution protocol, custody schemas, and analysis implementation are deterministic.",
            "Every absent external prerequisite is explicit machine-readable missingness.",
            "Execution remains unauthorized while any admission gate is blocked.",
            "Controls remain separate and LLM judges cannot define semantic ground truth.",
            "Every iter211 source artifact except this self-referential receipt is byte-bound.",
            "No provider, GPU, scientific container, trajectory, dispatch, payment, or release occurs.",
        ],
        "evidence": evidence,
        "falsifiers": [
            "Any prerequisite is invented or inferred from an empty field.",
            "Any blocked gate is interpreted as execution-ready.",
            "Any historical experiment byte changes.",
            "Any iter211 source delta is absent from the receipt closure.",
            "Any scientific result or broad performance claim is made.",
            "Any provider, accelerator, scientific, dispatch, payment, or release action occurs.",
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
    source_is_ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ITER211_SOURCE_COMMIT, "HEAD"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    seal_is_ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ITER211_SEAL_COMMIT, "HEAD"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if seal_is_ancestor.returncode == 0:
        parents = _git_bytes("rev-list", "--parents", "-n", "1", ITER211_SEAL_COMMIT)
        if parents.decode().split() != [
            ITER211_SEAL_COMMIT,
            ITER211_SOURCE_COMMIT,
        ]:
            raise RuntimeError("iter211 public seal parent topology differs")
        return ITER211_SOURCE_COMMIT
    if source_is_ancestor.returncode == 0 and _git_bytes("rev-parse", "HEAD").decode().strip() != (
        ITER211_SOURCE_COMMIT
    ):
        raise RuntimeError("iter211 source is in history without its exact seal")

    handoff = (ROOT / "HANDOFF.md").read_text(encoding="utf-8")
    if f"handoff_schema: {HANDOFF_SCHEMA}" not in handoff:
        return None
    match = re.search(r"^source_commit: ([0-9a-f]{40})$", handoff, re.MULTILINE)
    if match is None:
        raise RuntimeError("iter211 handoff lacks one exact source commit")
    source = match.group(1)
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", source, "HEAD"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("iter211 handoff source is not in current Git history")
    if source != ITER211_SOURCE_COMMIT:
        raise RuntimeError("iter211 handoff source differs from the sealed source")
    return ITER211_SOURCE_COMMIT


def verify_sealed_receipt(source: str) -> int:
    relative = RECEIPT_PATH.relative_to(ROOT).as_posix()
    payload = _git_bytes("show", f"{source}:{relative}")
    if RECEIPT_PATH.read_bytes() != payload:
        raise RuntimeError("iter211 receipt differs from source Git blob")
    receipt = validate_receipt_v2(json.loads(payload.decode("utf-8")))
    for item in receipt.evidence:
        artifact = item["artifact"]
        artifact_payload = _git_bytes("show", f"{source}:{artifact['path']}")
        if len(artifact_payload) != artifact["bytes"] or (
            hashlib.sha256(artifact_payload).hexdigest() != artifact["sha256"]
        ):
            raise RuntimeError(f"iter211 sealed artifact differs: {artifact['path']}")
    return len(receipt.evidence)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    source = sealed_source_commit()
    if args.check and source is not None:
        count = verify_sealed_receipt(source)
        print(f"iter211 receipt builder: clean sealed {count}-artifact blocked closure")
        return 0
    if source is not None:
        print("iter211 receipt builder: refusing to rewrite sealed source")
        return 1
    rendered = rendered_receipt()
    if args.check:
        if not RECEIPT_PATH.is_file() or RECEIPT_PATH.read_text(encoding="utf-8") != rendered:
            print("iter211 receipt builder: committed receipt differs")
            return 1
        receipt = load_receipt_v2(RECEIPT_PATH, artifact_root=ROOT)
        if receipt.status != "blocked":
            print("iter211 receipt builder: execution admission must remain blocked")
            return 1
        print(f"iter211 receipt builder: clean {len(BINDINGS)}-artifact blocked closure")
        return 0
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(rendered, encoding="utf-8")
    print(f"iter211 receipt builder: wrote {len(BINDINGS)}-artifact blocked closure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
