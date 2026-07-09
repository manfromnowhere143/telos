#!/usr/bin/env python3
"""Generate iter35 release-manifest self-coverage proof artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "iter35_release_manifest_self_coverage_guard"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
MANIFEST = (
    ROOT
    / "experiments"
    / "iter31_claim_boundary_release_manifest"
    / "proof"
    / "claim_boundary_release_manifest.json"
)
NEXT_GATE = ROOT / "experiments" / "iter36_release_manifest_self_coverage_negative_guard" / "HYPOTHESIS.md"

EXPECTED_FAILED_OR_NULL = [
    "iter23_original_occupied_tail_falsification",
    "iter25_tail_safety_mutation_guard_miss",
]
EXPECTED_CHANGED_CANDIDATE = ["iter24_changed_candidate_occupied_tail_control"]
FORBIDDEN_BOOLEAN_FIELDS = [
    "leaderboard_or_swebench_claimed",
    "production_or_live_domain_changed",
    "provider_game_score_used_as_verifier_evidence",
    "model_superiority_claimed",
]

SELF_GATES = [
    {
        "experiment_id": "iter31_claim_boundary_release_manifest",
        "summary": "proof/run_summary.json",
        "primary": "proof/claim_boundary_release_manifest.json",
        "receipt": "proof/valid/receipt_claim_boundary_release_manifest.json",
        "role": "release_manifest",
    },
    {
        "experiment_id": "iter32_claim_boundary_release_manifest_negative_guard",
        "summary": "proof/run_summary.json",
        "primary": "proof/negative_guard_report.json",
        "receipt": "proof/valid/receipt_claim_boundary_release_manifest_negative_guard.json",
        "role": "release_manifest_negative_guard",
    },
    {
        "experiment_id": "iter33_release_manifest_public_sync_guard",
        "summary": "proof/run_summary.json",
        "primary": "proof/public_sync_report.json",
        "receipt": "proof/valid/receipt_release_manifest_public_sync_guard.json",
        "role": "public_sync_guard",
    },
    {
        "experiment_id": "iter34_release_manifest_public_sync_negative_guard",
        "summary": "proof/run_summary.json",
        "primary": "proof/negative_guard_report.json",
        "receipt": "proof/valid/receipt_release_manifest_public_sync_negative_guard.json",
        "role": "public_sync_negative_guard",
    },
]


class SelfCoverageError(RuntimeError):
    """Raised when iter35 cannot build a trustworthy self-coverage report."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SelfCoverageError(f"{path} root must be an object")
    return data


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def artifact(path: Path, *, kind: str) -> dict[str, str]:
    if not path.exists():
        raise SelfCoverageError(f"missing artifact: {rel(path)}")
    return {"path": rel(path), "kind": kind, "sha256": sha256_file(path)}


def proof_artifacts(experiment_id: str) -> list[dict[str, str]]:
    proof = ROOT / "experiments" / experiment_id / "proof"
    if not proof.exists():
        raise SelfCoverageError(f"missing proof directory: {rel(proof)}")
    return [
        artifact(path, kind="proof_artifact")
        for path in sorted(proof.rglob("*"))
        if path.is_file()
    ]


def no_forbidden_claims(data: dict[str, Any]) -> bool:
    return all(data.get(field) is False for field in FORBIDDEN_BOOLEAN_FIELDS)


def gate_record(spec: dict[str, str]) -> dict[str, Any]:
    base = ROOT / "experiments" / spec["experiment_id"]
    hypothesis = base / "HYPOTHESIS.md"
    result = base / "RESULT.md"
    summary_path = base / spec["summary"]
    primary_path = base / spec["primary"]
    receipt_path = base / spec["receipt"]
    summary = read_json(summary_path)
    primary = read_json(primary_path)
    artifacts = proof_artifacts(spec["experiment_id"])
    clean_local_pass = (
        summary.get("status") == "pass"
        and summary.get("clean_pass") is True
        and summary.get("provider_api_calls") == 0
        and summary.get("provider_spend_usd") == 0.0
        and summary.get("cloud_or_gpu_used") is False
        and summary.get("local_cpu_only") is True
        and no_forbidden_claims(summary)
        and primary.get("status") == "pass"
        and primary.get("provider_api_calls") == 0
        and primary.get("provider_spend_usd") == 0.0
        and primary.get("cloud_or_gpu_used") is False
        and primary.get("local_cpu_only") is True
        and no_forbidden_claims(primary)
    )
    return {
        "experiment_id": spec["experiment_id"],
        "role": spec["role"],
        "status": summary.get("status"),
        "clean_local_pass": clean_local_pass,
        "hypothesis": artifact(hypothesis, kind="hypothesis"),
        "result": artifact(result, kind="result"),
        "summary": artifact(summary_path, kind="run_summary"),
        "primary_report": artifact(primary_path, kind=spec["role"]),
        "receipt": artifact(receipt_path, kind="receipt"),
        "proof_artifact_count": len(artifacts),
        "proof_artifacts": artifacts,
        "claim_boundary": {
            "provider_api_calls": summary.get("provider_api_calls"),
            "provider_spend_usd": summary.get("provider_spend_usd"),
            "cloud_or_gpu_used": summary.get("cloud_or_gpu_used"),
            "local_cpu_only": summary.get("local_cpu_only"),
            "leaderboard_or_swebench_claimed": summary.get("leaderboard_or_swebench_claimed"),
            "production_or_live_domain_changed": summary.get("production_or_live_domain_changed"),
            "provider_game_score_used_as_verifier_evidence": summary.get(
                "provider_game_score_used_as_verifier_evidence"
            ),
            "model_superiority_claimed": summary.get("model_superiority_claimed"),
        },
    }


def validate_report(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if report.get("schema_version") != "telos.release_manifest_self_coverage_guard.report.v1":
        failures.append("schema_version mismatch")
    if report.get("covered_gate_ids") != [spec["experiment_id"] for spec in SELF_GATES]:
        failures.append("covered_gate_ids mismatch")
    if report.get("covered_gate_count") != len(SELF_GATES):
        failures.append("covered_gate_count mismatch")
    if report.get("self_verification_gates_clean") is not True:
        failures.append("self-verification gates must be clean local passes")
    if report.get("failed_null_gates_visible") is not True:
        failures.append("failed/null gates must remain visible")
    if report.get("changed_candidate_boundary_visible") is not True:
        failures.append("changed candidate boundary must remain visible")
    for field in FORBIDDEN_BOOLEAN_FIELDS:
        if report.get(field) is not False:
            failures.append(f"{field} must be false")
    for gate in report.get("covered_gates", []):
        if gate.get("clean_local_pass") is not True:
            failures.append(f"{gate.get('experiment_id')}: clean_local_pass must be true")
        for item_key in ["hypothesis", "result", "summary", "primary_report", "receipt"]:
            item = gate.get(item_key, {})
            path = ROOT / item.get("path", "")
            if not path.exists():
                failures.append(f"{gate.get('experiment_id')}: missing {item_key}")
                continue
            if item.get("sha256") != sha256_file(path):
                failures.append(f"{gate.get('experiment_id')}: stale {item_key} hash")
        for item in gate.get("proof_artifacts", []):
            path = ROOT / item.get("path", "")
            if not path.exists():
                failures.append(f"{gate.get('experiment_id')}: missing proof artifact")
                continue
            if item.get("sha256") != sha256_file(path):
                failures.append(f"{gate.get('experiment_id')}: stale proof artifact hash")
    return failures


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter35-release-manifest-self-coverage-guard-{status}",
        "task_id": "telos:iter35_release_manifest_self_coverage_guard@iter31_iter34_release_manifest",
        "agent_id": "codex-local-release-manifest-self-coverage",
        "benchmark_id": "telos_codeclash_battlesnake_semantic_slice",
        "status": status,
        "stated_goal": (
            "Verify the release-manifest reviewer packet accounts for its own manifest, negative, "
            "public-sync, and public-sync-negative proof gates."
        ),
        "acceptance_criteria": [
            "No provider, API, GPU, or cloud spend occurs.",
            "The self-coverage report validates against committed proof artifacts.",
            "Iter31 through iter34 are represented with matching hashes.",
            "Original failed/null gates remain visible.",
            "Command output and proof artifacts are committed.",
            "No leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": "experiments/iter35_release_manifest_self_coverage_guard/proof/self_coverage_report.json",
                "notes": "Self-coverage report over iter31 through iter34 proof artifacts.",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "experiments/iter31_claim_boundary_release_manifest/proof/claim_boundary_release_manifest.json",
                "notes": "Unmodified release-manifest reviewer entry point.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": "experiments/iter35_release_manifest_self_coverage_guard/proof/review.md",
                "notes": "Review records the self-coverage boundary and no-overclaim constraints.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if required source proof artifacts cannot be loaded.",
            "The result must fail if any self-coverage hash is stale.",
            "The result must fail if any self-verification gate is hidden.",
            "The result must fail if failed/null gates are hidden.",
            "The result must not widen into benchmark, production, live-domain, or model-superiority claims.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    manifest = read_json(MANIFEST)
    gates = [gate_record(spec) for spec in SELF_GATES]
    failed_rows = manifest.get("failed_or_null_rows", [])
    changed_rows = manifest.get("changed_candidate_rows", [])
    failed_null_visible = (
        manifest.get("claim_boundary_matrix", {}).get("failed_or_null_claim_ids")
        == EXPECTED_FAILED_OR_NULL
        and [row.get("claim_id") for row in failed_rows] == EXPECTED_FAILED_OR_NULL
        and all(row.get("failure_visible") is True for row in failed_rows)
    )
    changed_candidate_visible = (
        manifest.get("claim_boundary_matrix", {}).get("changed_candidate_claim_ids")
        == EXPECTED_CHANGED_CANDIDATE
        and [row.get("claim_id") for row in changed_rows] == EXPECTED_CHANGED_CANDIDATE
        and all(row.get("changed_candidate") is True for row in changed_rows)
        and all(row.get("original_provider_logic") is False for row in changed_rows)
    )

    report = {
        "schema_version": "telos.release_manifest_self_coverage_guard.report.v1",
        "status": "pass",
        "source_manifest_path": rel(MANIFEST),
        "source_manifest_sha256": sha256_file(MANIFEST),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "covered_gate_ids": [gate["experiment_id"] for gate in gates],
        "covered_gate_count": len(gates),
        "proof_artifact_count": sum(gate["proof_artifact_count"] for gate in gates),
        "self_verification_gates_clean": all(gate["clean_local_pass"] for gate in gates),
        "failed_or_null_claim_ids": EXPECTED_FAILED_OR_NULL,
        "failed_null_gates_visible": failed_null_visible,
        "changed_candidate_claim_ids": EXPECTED_CHANGED_CANDIDATE,
        "changed_candidate_boundary_visible": changed_candidate_visible,
        "covered_gates": gates,
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "model_superiority_claimed": False,
    }
    failures = validate_report(report)
    status = "pass" if not failures else "fail"
    report["status"] = status
    write_json(PROOF / "self_coverage_report.json", report)

    output_lines = [
        f"release manifest self coverage guard: {status}",
        f"source_manifest={MANIFEST.relative_to(ROOT)}",
        "provider_api_calls=0",
        "cloud_or_gpu_used=false",
        f"covered_gates={','.join(report['covered_gate_ids'])}",
        f"proof_artifact_count={report['proof_artifact_count']}",
        f"self_verification_gates_clean={str(report['self_verification_gates_clean']).lower()}",
        f"failed_null_gates_visible={str(report['failed_null_gates_visible']).lower()}",
        f"self_coverage_failures={','.join(failures)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 35 Review

The self-coverage guard indexes the release-manifest reviewer packet's own `iter31` through
`iter34` proof gates. It records hashes for the manifest gate, manifest negative guard, public-sync
guard, and public-sync negative guard without rewriting prior proof artifacts.

The original `iter23` and `iter25` failed/null gates remain visible, and the changed `iter24`
candidate remains separate from original `iter21` provider logic.

This is reviewer-packet coverage evidence. It is not behavior evidence, not a benchmark result, and
not a provider-model result.

No provider call, API call, GPU, cloud runner, production deployment, live-domain check, leaderboard
run, or SWE-bench run occurred in this gate.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    run_summary = {
        "schema_version": "telos.release_manifest_self_coverage_guard.summary.v1",
        "status": status,
        "experiment_id": "iter35_release_manifest_self_coverage_guard",
        "source_experiment": "iter31_claim_boundary_release_manifest",
        "source_manifest_path": rel(MANIFEST),
        "source_manifest_sha256": sha256_file(MANIFEST),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "covered_gate_count": report["covered_gate_count"],
        "covered_gate_ids": report["covered_gate_ids"],
        "proof_artifact_count": report["proof_artifact_count"],
        "self_coverage_valid": not failures,
        "self_coverage_failure_count": len(failures),
        "self_coverage_failures": failures,
        "self_verification_gates_clean": report["self_verification_gates_clean"],
        "failed_or_null_claim_ids": EXPECTED_FAILED_OR_NULL,
        "failed_null_gates_visible": failed_null_visible,
        "changed_candidate_claim_ids": EXPECTED_CHANGED_CANDIDATE,
        "changed_candidate_boundary_visible": changed_candidate_visible,
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "model_superiority_claimed": False,
        "clean_pass": status == "pass",
        "next_gate": "experiments/iter36_release_manifest_self_coverage_negative_guard/HYPOTHESIS.md",
        "artifact_hashes": {
            "command_output.txt": sha256_file(PROOF / "command_output.txt"),
            "review.md": sha256_file(PROOF / "review.md"),
            "self_coverage_report.json": sha256_file(PROOF / "self_coverage_report.json"),
        },
    }
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter35_release_manifest_self_coverage_guard",
        "status": "null" if status == "fail" else status,
        "insight": (
            "A self-coverage report can account for the release-manifest reviewer packet's own "
            "manifest, negative, public-sync, and public-sync-negative proof gates without "
            "rewriting prior evidence."
        ),
        "next_action": (
            "pre-register negative self-coverage fixtures so missing, stale, or hidden "
            "self-verification artifacts are rejected"
        ),
        "result_path": "experiments/iter35_release_manifest_self_coverage_guard/RESULT.md",
        "evidence_paths": [
            "experiments/iter35_release_manifest_self_coverage_guard/proof/run_summary.json",
            "experiments/iter35_release_manifest_self_coverage_guard/proof/self_coverage_report.json",
            "experiments/iter35_release_manifest_self_coverage_guard/proof/command_output.txt",
            "experiments/iter35_release_manifest_self_coverage_guard/proof/review.md",
            "experiments/iter35_release_manifest_self_coverage_guard/proof/valid/receipt_release_manifest_self_coverage_guard.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(VALID / "receipt_release_manifest_self_coverage_guard.json", build_receipt(status))

    print("\n".join(output_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
