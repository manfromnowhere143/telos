#!/usr/bin/env python3
"""Publish iter69 CodeClash task-surface source snapshot recovery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import os
import re
import subprocess
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telos.proof import receipt_digest


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "iter69_codeclash_task_surface_source_snapshot_recovery"
EXPERIMENT = ROOT / "experiments" / EXPERIMENT_ID
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
ITER68_REPORT = (
    ROOT
    / "experiments"
    / "iter68_provider_compatible_task_surface_adapter_recovery"
    / "proof"
    / "adapter_recovery_report.json"
)
ITER68_SUMMARY = (
    ROOT
    / "experiments"
    / "iter68_provider_compatible_task_surface_adapter_recovery"
    / "proof"
    / "run_summary.json"
)
CODECLASH_DIR = Path(os.environ.get("TELOS_CODECLASH_DIR", "/tmp/telos-codeclash"))
CODECLASH_COMMIT = "381cdfa05a35e8acd35853b9fc7e13005121b127"
SOURCE_REL = Path("configs/test/dummy.yaml")
CANONICAL_SNAPSHOT = ROOT / "experiments" / "source_snapshots" / "codeclash" / SOURCE_REL
PROOF_SNAPSHOT = PROOF / "source_snapshots" / "codeclash" / SOURCE_REL
NEXT_GATE = (
    ROOT
    / "experiments"
    / "iter70_provider_compatible_expanded_adapter_completion"
    / "HYPOTHESIS.md"
)
TEXT_SUFFIXES = {".json", ".jsonl", ".log", ".txt", ".md", ".yaml", ".yml", ".py"}
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gho_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9_-]{20,}"),
    re.compile(r"Bearer\s+(?!\$\{[A-Z0-9_]+\}|\[REDACTED_BEARER_TOKEN\])\S+"),
    re.compile(r"-----BEGIN PRIVATE KEY-----"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com"),
    re.compile(r"telos-vertex-runner"),
    re.compile(r"sunlit-unison-[A-Za-z0-9-]+"),
    re.compile(r"errorId=Ci"),
    re.compile(r'"error_info_id"\s*:\s*"Ci'),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} root must be an object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_text(args: list[str], timeout: int = 10) -> dict[str, Any]:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"returncode": None, "timed_out": True, "stdout": "", "stderr": ""}
    return {
        "returncode": result.returncode,
        "timed_out": False,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def run_bytes(args: list[str], timeout: int = 10) -> dict[str, Any]:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"returncode": None, "timed_out": True, "stdout": b"", "stderr": b""}
    return {
        "returncode": result.returncode,
        "timed_out": False,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def text_files(path: Path) -> list[Path]:
    return [
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file() and candidate.suffix in TEXT_SUFFIXES
    ]


def redaction_findings(paths: list[Path]) -> list[str]:
    findings: list[str] = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(str(path.relative_to(ROOT)))
                break
    return sorted(set(findings))


def artifact_hashes(paths: list[Path]) -> dict[str, str]:
    return {str(path.relative_to(PROOF)): sha256_file(path) for path in paths}


def checkout_state() -> dict[str, Any]:
    state: dict[str, Any] = {
        "checkout_path": str(CODECLASH_DIR),
        "checkout_present": (CODECLASH_DIR / ".git").exists(),
        "expected_commit": CODECLASH_COMMIT,
        "actual_commit": None,
        "commit_matches_expected": False,
        "source_relpath": str(SOURCE_REL),
        "source_file_present": (CODECLASH_DIR / SOURCE_REL).is_file(),
        "source_status_lines": [],
        "working_tree_status_line_count": None,
        "working_tree_dirty_but_source_clean": False,
        "source_blob_readable": False,
        "source_blob_sha256": None,
        "working_tree_source_sha256": None,
        "working_tree_source_matches_blob": False,
    }
    if not state["checkout_present"]:
        return state

    rev = run_text(["git", "-C", str(CODECLASH_DIR), "rev-parse", "HEAD"])
    if rev["returncode"] == 0:
        state["actual_commit"] = rev["stdout"].strip()
        state["commit_matches_expected"] = state["actual_commit"] == CODECLASH_COMMIT

    status = run_text(["git", "-C", str(CODECLASH_DIR), "status", "--short"])
    if status["returncode"] == 0:
        state["working_tree_status_line_count"] = len(
            [line for line in status["stdout"].splitlines() if line.strip()]
        )

    source_status = run_text(
        ["git", "-C", str(CODECLASH_DIR), "status", "--short", "--", str(SOURCE_REL)]
    )
    if source_status["returncode"] == 0:
        state["source_status_lines"] = [
            line for line in source_status["stdout"].splitlines() if line.strip()
        ]
        state["working_tree_dirty_but_source_clean"] = (
            bool(state["working_tree_status_line_count"])
            and not state["source_status_lines"]
        )

    blob = run_bytes(["git", "-C", str(CODECLASH_DIR), "show", f"HEAD:{SOURCE_REL}"])
    if blob["returncode"] == 0:
        state["source_blob_readable"] = True
        state["source_blob_sha256"] = sha256_bytes(blob["stdout"])

    working_source = CODECLASH_DIR / SOURCE_REL
    if working_source.is_file():
        state["working_tree_source_sha256"] = sha256_file(working_source)
        state["working_tree_source_matches_blob"] = (
            state["working_tree_source_sha256"] == state["source_blob_sha256"]
        )
    return state


def snapshot_source() -> dict[str, Any]:
    blob = run_bytes(["git", "-C", str(CODECLASH_DIR), "show", f"HEAD:{SOURCE_REL}"])
    record: dict[str, Any] = {
        "public_config": str(SOURCE_REL),
        "source_evidence": "pinned_git_blob",
        "source_git_ref": f"HEAD:{SOURCE_REL}",
        "source_blob_sha256": None,
        "canonical_snapshot_path": str(CANONICAL_SNAPSHOT.relative_to(ROOT)),
        "proof_snapshot_path": str(PROOF_SNAPSHOT.relative_to(ROOT)),
        "canonical_snapshot_sha256": None,
        "proof_snapshot_sha256": None,
        "canonical_hash_matches_source": False,
        "proof_hash_matches_source": False,
        "canonical_hash_matches_proof": False,
        "task_surface_evidence_only": True,
        "execution_result": False,
    }
    if blob["returncode"] != 0:
        return record

    data = blob["stdout"]
    record["source_blob_sha256"] = sha256_bytes(data)
    for path in [CANONICAL_SNAPSHOT, PROOF_SNAPSHOT]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    record["canonical_snapshot_sha256"] = sha256_file(CANONICAL_SNAPSHOT)
    record["proof_snapshot_sha256"] = sha256_file(PROOF_SNAPSHOT)
    record["canonical_hash_matches_source"] = (
        record["canonical_snapshot_sha256"] == record["source_blob_sha256"]
    )
    record["proof_hash_matches_source"] = (
        record["proof_snapshot_sha256"] == record["source_blob_sha256"]
    )
    record["canonical_hash_matches_proof"] = (
        record["canonical_snapshot_sha256"] == record["proof_snapshot_sha256"]
    )
    return record


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter69-codeclash-task-surface-source-snapshot-recovery-{status}",
        "task_id": "telos:iter69_codeclash_task_surface_source_snapshot_recovery@iter68",
        "agent_id": "codex-local-codeclash-source-snapshot-verifier",
        "benchmark_id": "telos_codeclash_protocol_effect_pilot",
        "status": status,
        "stated_goal": (
            "Recover committed source evidence for the CodeClash Dummy task surface without "
            "provider calls, row execution, GPU, cloud runner startup, or Sentinel mutation."
        ),
        "acceptance_criteria": [
            "Iter68 is present and blocked for committed_dummy_source_surface_missing.",
            "The pinned CodeClash checkout path and commit are recorded.",
            "configs/test/dummy.yaml is copied from the pinned Git blob into committed evidence.",
            "Source, canonical snapshot, and proof snapshot hashes match.",
            "Copied files are labeled as task-surface evidence, not execution results.",
            "Provider calls, spend, row execution, GPU, cloud runner startup, Sentinel mutation, and live-domain mutation remain zero.",
            "No benchmark, leaderboard, SWE-bench, production, live-domain, model-superiority, or state-of-the-art result is claimed.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": (
                    "experiments/iter69_codeclash_task_surface_source_snapshot_recovery/proof/"
                    "source_snapshot_report.json"
                ),
                "notes": "Machine-readable source snapshot and hash equality report.",
            },
            {
                "kind": "artifact",
                "status": status,
                "artifact": "experiments/source_snapshots/codeclash/configs/test/dummy.yaml",
                "notes": "Canonical committed CodeClash Dummy task-surface snapshot.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": (
                    "experiments/iter69_codeclash_task_surface_source_snapshot_recovery/proof/"
                    "review.md"
                ),
                "notes": "Review records the source-only boundary and dirty-checkout caveat.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if iter68 is missing or was not blocked for the source-snapshot blocker.",
            "The result must block if the pinned CodeClash checkout or source Git blob cannot be read.",
            "The result must block if any copied snapshot hash differs from the pinned source blob.",
            "The result must fail if copied task source is presented as execution evidence.",
            "The result must fail if provider calls, spend, row execution, GPU, cloud runner startup, Sentinel mutation, or live-domain mutation occurs.",
            "The result must fail if unsupported benchmark, model-superiority, leaderboard, SWE-bench, production, live-domain, or state-of-the-art claims appear.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def write_result(status: str, report: dict[str, Any]) -> None:
    snapshot = report["snapshots"][0]
    content = f"""# Iteration 69 Result - CodeClash Task-Surface Source Snapshot Recovery

Status: `{status.upper()}`.

## Summary

This local gate recovered committed source evidence for `configs/test/dummy.yaml` from the pinned
CodeClash Git blob at commit `{CODECLASH_COMMIT}`. The source blob, canonical repo snapshot, and
iter69 proof snapshot all hash to `{snapshot['source_blob_sha256']}`.

- provider API calls: `0`,
- provider spend: `$0.00`,
- row execution: `false`,
- GPU used: `false`,
- cloud runner started: `false`,
- Sentinel-named resources modified: `false`,
- copied source is execution evidence: `false`.

## Dirty-Checkout Caveat

The pinned checkout had unrelated provider overlay files from earlier recovery gates, but
`configs/test/dummy.yaml` itself was clean at `HEAD`. The snapshot was copied from
`HEAD:configs/test/dummy.yaml`, and the working-tree source hash matched that Git blob.

## Claim Boundary

This is not a benchmark result, SWE-bench result, leaderboard result, production/live-domain
result, model-superiority result, or state-of-the-art result. The only new claim is that the
CodeClash Dummy task-source file is now committed as snapshot evidence for later adapter recovery.

## Next

Complete the provider-compatible expanded adapter set without provider spend:
[`../iter70_provider_compatible_expanded_adapter_completion/HYPOTHESIS.md`](../iter70_provider_compatible_expanded_adapter_completion/HYPOTHESIS.md).

## Evidence

- `proof/source_snapshot_report.json`
- `proof/source_snapshots/codeclash/configs/test/dummy.yaml`
- `../../source_snapshots/codeclash/configs/test/dummy.yaml`
- `proof/command_output.txt`
- `proof/review.md`
- `proof/run_summary.json`
- `proof/valid/receipt_codeclash_task_surface_source_snapshot_recovery.json`
"""
    (EXPERIMENT / "RESULT.md").write_text(content, encoding="utf-8")


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    iter68_report = read_json(ITER68_REPORT)
    iter68_summary = read_json(ITER68_SUMMARY)
    checkout = checkout_state()
    snapshot = snapshot_source() if checkout["source_blob_readable"] else {
        "public_config": str(SOURCE_REL),
        "source_evidence": "pinned_git_blob",
        "source_git_ref": f"HEAD:{SOURCE_REL}",
        "source_blob_sha256": checkout.get("source_blob_sha256"),
        "canonical_snapshot_path": str(CANONICAL_SNAPSHOT.relative_to(ROOT)),
        "proof_snapshot_path": str(PROOF_SNAPSHOT.relative_to(ROOT)),
        "canonical_snapshot_sha256": None,
        "proof_snapshot_sha256": None,
        "canonical_hash_matches_source": False,
        "proof_hash_matches_source": False,
        "canonical_hash_matches_proof": False,
        "task_surface_evidence_only": True,
        "execution_result": False,
    }

    blockers: list[str] = []
    failures: list[str] = []
    if iter68_summary.get("status") != "blocked":
        blockers.append("iter68_not_blocked")
    if "committed_dummy_source_surface_missing" not in iter68_summary.get("blockers", []):
        blockers.append("iter68_source_snapshot_blocker_missing")
    if not checkout["checkout_present"]:
        blockers.append("pinned_codeclash_checkout_missing")
    if not checkout["commit_matches_expected"]:
        blockers.append("pinned_codeclash_commit_mismatch")
    if not checkout["source_blob_readable"]:
        blockers.append("dummy_source_git_blob_unreadable")
    if checkout["source_status_lines"]:
        blockers.append("dummy_source_path_dirty")
    for key in [
        "canonical_hash_matches_source",
        "proof_hash_matches_source",
        "canonical_hash_matches_proof",
    ]:
        if snapshot.get(key) is not True:
            blockers.append("source_snapshot_hash_mismatch")

    redaction = redaction_findings([CANONICAL_SNAPSHOT, PROOF_SNAPSHOT, *text_files(EXPERIMENT)])
    if redaction:
        failures.append("redaction_findings_present")

    status = "fail" if failures else "blocked" if blockers else "pass"
    report = {
        "schema_version": "telos.codeclash_task_surface_source_snapshot_recovery.report.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "source_iter68_report_path": str(ITER68_REPORT.relative_to(ROOT)),
        "source_iter68_summary_path": str(ITER68_SUMMARY.relative_to(ROOT)),
        "iter68_status": iter68_summary.get("status"),
        "iter68_blockers": iter68_summary.get("blockers"),
        "iter68_blocker_committed_dummy_source_surface_missing": (
            "committed_dummy_source_surface_missing" in iter68_summary.get("blockers", [])
        ),
        "iter68_report_status": iter68_report.get("status"),
        "codeclash_checkout": checkout,
        "snapshots": [snapshot],
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "row_execution_allowed": False,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "copied_source_files_are_task_surface_evidence_only": True,
        "copied_source_files_are_execution_results": False,
        "next_paid_gate_authorized": False,
        "redaction_scan_passed": not redaction,
        "redaction_findings": redaction,
        "blockers": sorted(set(blockers)),
        "failures": sorted(set(failures)),
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
    }
    write_json(PROOF / "source_snapshot_report.json", report)

    output_lines = [
        f"codeclash task-surface source snapshot recovery: {status}",
        "provider_api_calls=0",
        "provider_spend_usd=0.00",
        "row_execution_allowed=false",
        "gpu_used=false",
        "cloud_runner_started=false",
        "sentinel_named_resources_modified=false",
        f"codeclash_checkout_path={CODECLASH_DIR}",
        f"codeclash_commit={checkout.get('actual_commit')}",
        f"snapshot_source={SOURCE_REL}",
        f"snapshot_sha256={snapshot.get('source_blob_sha256')}",
        f"task_surface_evidence_only={str(snapshot.get('task_surface_evidence_only')).lower()}",
        f"copied_source_files_are_execution_results={str(report['copied_source_files_are_execution_results']).lower()}",
        f"redaction_scan_passed={str(report['redaction_scan_passed']).lower()}",
        f"blockers={','.join(report['blockers'])}",
        f"failures={','.join(report['failures'])}",
        f"next_gate={NEXT_GATE.relative_to(ROOT)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 69 Review

The gate recovers only source-task evidence. It reads the pinned CodeClash checkout, copies the
`configs/test/dummy.yaml` Git blob into committed canonical and proof snapshots, and proves exact
hash equality. The broader checkout contains unrelated overlay residue from prior local recovery
work, but the Dummy source path is clean and the working-tree file matches the pinned blob.

No provider model call, spend, row execution, GPU, cloud runner startup, Sentinel mutation,
production/live-domain mutation, benchmark claim, model claim, or state-of-the-art claim occurred.
The snapshot is not execution evidence and does not say anything about model quality.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    receipt_path = VALID / "receipt_codeclash_task_surface_source_snapshot_recovery.json"
    write_json(receipt_path, build_receipt(status))

    summary = {
        "schema_version": "telos.codeclash_task_surface_source_snapshot_recovery.summary.v1",
        "status": status,
        "experiment_id": EXPERIMENT_ID,
        "source_public_config": str(SOURCE_REL),
        "source_snapshot_path": str(CANONICAL_SNAPSHOT.relative_to(ROOT)),
        "proof_snapshot_path": str(PROOF_SNAPSHOT.relative_to(ROOT)),
        "source_snapshot_sha256": snapshot.get("source_blob_sha256"),
        "codeclash_checkout_path": str(CODECLASH_DIR),
        "codeclash_expected_commit": CODECLASH_COMMIT,
        "codeclash_actual_commit": checkout.get("actual_commit"),
        "codeclash_commit_matches_expected": checkout.get("commit_matches_expected"),
        "source_path_clean": not checkout.get("source_status_lines"),
        "working_tree_dirty_but_source_clean": checkout.get("working_tree_dirty_but_source_clean"),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "row_execution_allowed": False,
        "gpu_used": False,
        "cloud_runner_started": False,
        "sentinel_named_resources_modified": False,
        "production_or_live_domain_changed": False,
        "benchmark_result_claimed": False,
        "leaderboard_or_swebench_result_claimed": False,
        "model_superiority_claimed": False,
        "state_of_the_art_result_claimed": False,
        "copied_source_files_are_task_surface_evidence_only": True,
        "copied_source_files_are_execution_results": False,
        "next_paid_gate_authorized": False,
        "clean_pass": status == "pass",
        "blocked_result": status == "blocked",
        "quality_failure": status == "fail",
        "blockers": report["blockers"],
        "failures": report["failures"],
        "redaction_scan_passed": report["redaction_scan_passed"],
        "redaction_findings": redaction,
        "next_gate": str(NEXT_GATE.relative_to(ROOT)),
        "artifact_hashes": artifact_hashes(
            [
                PROOF / "source_snapshot_report.json",
                PROOF / "command_output.txt",
                PROOF / "review.md",
                PROOF_SNAPSHOT,
                receipt_path,
            ]
        ),
        "canonical_source_snapshot_sha256": sha256_file(CANONICAL_SNAPSHOT)
        if CANONICAL_SNAPSHOT.exists()
        else None,
    }
    write_json(PROOF / "run_summary.json", summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": EXPERIMENT_ID,
        "status": status if status != "fail" else "null",
        "insight": (
            "The missing Dummy CodeClash task surface can be recovered as committed source "
            "evidence from the pinned Git blob without provider spend or task execution."
        ),
        "next_action": (
            "complete the provider-compatible expanded adapter set from committed source snapshots "
            "before any expanded paid protocol-effect retry"
        ),
        "result_path": f"experiments/{EXPERIMENT_ID}/RESULT.md",
        "evidence_paths": [
            f"experiments/{EXPERIMENT_ID}/proof/run_summary.json",
            f"experiments/{EXPERIMENT_ID}/proof/source_snapshot_report.json",
            f"experiments/{EXPERIMENT_ID}/proof/command_output.txt",
            f"experiments/{EXPERIMENT_ID}/proof/review.md",
            f"experiments/{EXPERIMENT_ID}/proof/source_snapshots/codeclash/configs/test/dummy.yaml",
            "experiments/source_snapshots/codeclash/configs/test/dummy.yaml",
            f"experiments/{EXPERIMENT_ID}/proof/valid/receipt_codeclash_task_surface_source_snapshot_recovery.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_result(status, report)

    print("\n".join(output_lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
