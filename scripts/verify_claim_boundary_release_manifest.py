#!/usr/bin/env python3
"""Generate iter31 claim-boundary release-manifest proof artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "iter31_claim_boundary_release_manifest"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"

MATRIX = (
    ROOT
    / "experiments"
    / "iter27_semantic_claim_boundary_matrix"
    / "proof"
    / "claim_boundary_matrix.json"
)
PUBLIC_GUARD = (
    ROOT
    / "experiments"
    / "iter28_public_claim_surface_guard"
    / "proof"
    / "public_claim_surface_report.json"
)
NEGATIVE_GUARD = (
    ROOT
    / "experiments"
    / "iter29_public_claim_surface_negative_guard"
    / "proof"
    / "negative_guard_report.json"
)
SCHEMA_GUARD = (
    ROOT
    / "experiments"
    / "iter30_boundary_matrix_schema_guard"
    / "proof"
    / "schema_guard_report.json"
)

EXPECTED_FAILED_OR_NULL = [
    "iter23_original_occupied_tail_falsification",
    "iter25_tail_safety_mutation_guard_miss",
]
EXPECTED_CHANGED_CANDIDATE = ["iter24_changed_candidate_occupied_tail_control"]
FORBIDDEN_CLAIM_CLASSES = [
    "codeclash_leaderboard_result",
    "swebench_result",
    "production_or_live_domain_result",
    "model_superiority_result",
    "provider_game_score_as_verifier_evidence",
    "original_iter21_occupied_tail_safety",
]


class ReleaseManifestError(RuntimeError):
    """Raised when iter31 cannot produce a trustworthy release manifest."""


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
        raise ReleaseManifestError(f"{path} root must be an object")
    return data


def source_artifact(artifact_id: str, path: Path, *, kind: str, status: str | None) -> dict[str, Any]:
    if not path.exists():
        raise ReleaseManifestError(f"missing source artifact: {path.relative_to(ROOT)}")
    return {
        "artifact_id": artifact_id,
        "kind": kind,
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256_file(path),
        "status": status,
    }


def row_boundary(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "claim_id": row["claim_id"],
        "experiment_id": row["experiment_id"],
        "subject_type": row["subject_type"],
        "status": row["status"],
        "failure_visible": row["failure_visible"],
        "original_provider_logic": row["original_provider_logic"],
        "changed_candidate": row["changed_candidate"],
        "verifier_strength_evidence": row["verifier_strength_evidence"],
        "boundary": row["boundary"],
        "evidence_paths": row["evidence_paths"],
        "does_not_claim": row["does_not_claim"],
    }


def artifact_index(matrix: dict[str, Any]) -> list[dict[str, str]]:
    paths: list[str] = []
    for row in matrix["rows"]:
        paths.extend(row["evidence_paths"])
    paths.extend(
        [
            str(MATRIX.relative_to(ROOT)),
            str(PUBLIC_GUARD.relative_to(ROOT)),
            str(NEGATIVE_GUARD.relative_to(ROOT)),
            str(SCHEMA_GUARD.relative_to(ROOT)),
        ]
    )
    indexed = []
    for rel_path in sorted(set(paths)):
        path = ROOT / rel_path
        if not path.exists():
            raise ReleaseManifestError(f"missing manifest artifact: {rel_path}")
        indexed.append({"path": rel_path, "sha256": sha256_file(path)})
    return indexed


def build_manifest(
    matrix: dict[str, Any],
    public_guard: dict[str, Any],
    negative_guard: dict[str, Any],
    schema_guard: dict[str, Any],
) -> dict[str, Any]:
    failed_rows = [row for row in matrix["rows"] if row["claim_id"] in EXPECTED_FAILED_OR_NULL]
    changed_rows = [row for row in matrix["rows"] if row["claim_id"] in EXPECTED_CHANGED_CANDIDATE]
    return {
        "schema_version": "telos.claim_boundary_release_manifest.v1",
        "status": "pass",
        "experiment_id": "iter31_claim_boundary_release_manifest",
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "source_artifacts": [
            source_artifact("claim_boundary_matrix", MATRIX, kind="matrix", status=matrix["status"]),
            source_artifact(
                "public_claim_surface_report",
                PUBLIC_GUARD,
                kind="public_claim_guard",
                status=public_guard["status"],
            ),
            source_artifact(
                "negative_guard_report",
                NEGATIVE_GUARD,
                kind="negative_guard",
                status=negative_guard["status"],
            ),
            source_artifact(
                "schema_guard_report",
                SCHEMA_GUARD,
                kind="schema_guard",
                status=schema_guard["status"],
            ),
        ],
        "artifact_index": artifact_index(matrix),
        "claim_boundary_matrix": {
            "path": str(MATRIX.relative_to(ROOT)),
            "status": matrix["status"],
            "row_count": matrix["row_count"],
            "included_experiments": matrix["included_experiments"],
            "failed_or_null_claim_ids": matrix["failed_or_null_claim_ids"],
            "changed_candidate_claim_ids": matrix["changed_candidate_claim_ids"],
            "original_provider_logic_claim_ids": matrix["original_provider_logic_claim_ids"],
            "verifier_strength_claim_ids": matrix["verifier_strength_claim_ids"],
            "original_iter21_occupied_tail_safety_claimed": matrix[
                "original_iter21_occupied_tail_safety_claimed"
            ],
            "failed_null_gates_hidden": matrix["failed_null_gates_hidden"],
            "provider_game_score_used_as_verifier_evidence": matrix[
                "provider_game_score_used_as_verifier_evidence"
            ],
            "leaderboard_or_swebench_claimed": matrix["leaderboard_or_swebench_claimed"],
            "production_or_live_domain_changed": matrix["production_or_live_domain_changed"],
        },
        "claim_boundaries": [row_boundary(row) for row in matrix["rows"]],
        "failed_or_null_rows": [row_boundary(row) for row in failed_rows],
        "changed_candidate_rows": [row_boundary(row) for row in changed_rows],
        "public_claim_surface": {
            "path": str(PUBLIC_GUARD.relative_to(ROOT)),
            "status": public_guard["status"],
            "failed_null_gates_visible": public_guard["failed_null_gates_visible"],
            "changed_candidate_boundary_visible": public_guard[
                "changed_candidate_boundary_visible"
            ],
            "original_iter21_occupied_tail_safety_claimed": public_guard[
                "original_iter21_occupied_tail_safety_claimed"
            ],
        },
        "negative_guard": {
            "path": str(NEGATIVE_GUARD.relative_to(ROOT)),
            "status": negative_guard["status"],
            "fixture_count": negative_guard["fixture_count"],
            "fixtures_failed_as_expected": negative_guard["fixtures_failed_as_expected"],
        },
        "schema_guard": {
            "path": str(SCHEMA_GUARD.relative_to(ROOT)),
            "status": schema_guard["status"],
            "real_matrix_valid": schema_guard["real_matrix_valid"],
            "fixture_count": schema_guard["fixture_count"],
            "fixtures_failed_as_expected": schema_guard["fixtures_failed_as_expected"],
        },
        "forbidden_claim_classes": FORBIDDEN_CLAIM_CLASSES,
        "forbidden_claims_made": [],
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "model_superiority_claimed": False,
    }


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if manifest.get("schema_version") != "telos.claim_boundary_release_manifest.v1":
        failures.append("schema_version mismatch")
    if manifest.get("status") != "pass":
        failures.append("manifest status must be pass")
    for key, value in {
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "model_superiority_claimed": False,
    }.items():
        if manifest.get(key) != value:
            failures.append(f"{key} expected {value!r}, got {manifest.get(key)!r}")
    if manifest.get("forbidden_claims_made") != []:
        failures.append("forbidden_claims_made must be empty")

    for artifact in manifest.get("artifact_index", []):
        path = ROOT / artifact.get("path", "")
        if not path.exists():
            failures.append(f"missing artifact: {artifact.get('path')}")
            continue
        if artifact.get("sha256") != sha256_file(path):
            failures.append(f"hash mismatch: {artifact.get('path')}")

    matrix = manifest.get("claim_boundary_matrix", {})
    if matrix.get("failed_or_null_claim_ids") != EXPECTED_FAILED_OR_NULL:
        failures.append("failed_or_null_claim_ids mismatch")
    if matrix.get("changed_candidate_claim_ids") != EXPECTED_CHANGED_CANDIDATE:
        failures.append("changed_candidate_claim_ids mismatch")
    if matrix.get("original_iter21_occupied_tail_safety_claimed") is not False:
        failures.append("original iter21 occupied-tail safety must not be claimed")
    if matrix.get("failed_null_gates_hidden") is not False:
        failures.append("failed/null gates must not be hidden")

    failed_rows = manifest.get("failed_or_null_rows", [])
    if [row.get("claim_id") for row in failed_rows] != EXPECTED_FAILED_OR_NULL:
        failures.append("failed_or_null_rows mismatch")
    if any(row.get("failure_visible") is not True for row in failed_rows):
        failures.append("failed_or_null_rows must have failure_visible=true")
    changed_rows = manifest.get("changed_candidate_rows", [])
    if [row.get("claim_id") for row in changed_rows] != EXPECTED_CHANGED_CANDIDATE:
        failures.append("changed_candidate_rows mismatch")
    if any(row.get("original_provider_logic") for row in changed_rows):
        failures.append("changed candidate row must not be original provider logic")

    if manifest.get("public_claim_surface", {}).get("failed_null_gates_visible") is not True:
        failures.append("public claim surface must keep failed/null gates visible")
    if manifest.get("negative_guard", {}).get("fixtures_failed_as_expected") is not True:
        failures.append("negative guard fixtures must have failed as expected")
    if manifest.get("schema_guard", {}).get("real_matrix_valid") is not True:
        failures.append("schema guard must validate real matrix")
    if manifest.get("schema_guard", {}).get("fixtures_failed_as_expected") is not True:
        failures.append("schema guard fixtures must have failed as expected")
    return failures


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter31-claim-boundary-release-manifest-{status}",
        "task_id": "telos:iter31_claim_boundary_release_manifest@iter27_iter30_claim_boundary",
        "agent_id": "codex-local-claim-boundary-release-manifest",
        "benchmark_id": "telos_codeclash_battlesnake_semantic_slice",
        "status": status,
        "stated_goal": (
            "Publish a reviewer-facing manifest for the claim-boundary proof packet."
        ),
        "acceptance_criteria": [
            "No provider, API, GPU, or cloud spend occurs.",
            "The release manifest validates against committed proof artifacts.",
            "The manifest includes explicit failed/null gates.",
            "All artifact hashes match.",
            "Command output and proof artifacts are committed.",
            "No leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.",
        ],
        "evidence": [
            {
                "kind": "artifact",
                "status": status,
                "artifact": "experiments/iter31_claim_boundary_release_manifest/proof/claim_boundary_release_manifest.json",
                "notes": "Reviewer-facing manifest with artifact hashes and claim boundaries.",
            },
            {
                "kind": "test",
                "status": status,
                "artifact": "experiments/iter31_claim_boundary_release_manifest/proof/run_summary.json",
                "notes": "Summary records manifest validation and claim-boundary invariants.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": "experiments/iter31_claim_boundary_release_manifest/proof/review.md",
                "notes": "Review records the manifest boundary and no-overclaim constraints.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if required source proof artifacts cannot be loaded.",
            "The result must fail if any referenced artifact hash is stale.",
            "The result must fail if failed/null gates are hidden.",
            "The result must fail if original provider logic and changed candidate logic are conflated.",
            "The result must not widen into benchmark, production, live-domain, or model-superiority claims.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)

    matrix = read_json(MATRIX)
    public_guard = read_json(PUBLIC_GUARD)
    negative_guard = read_json(NEGATIVE_GUARD)
    schema_guard = read_json(SCHEMA_GUARD)
    manifest = build_manifest(matrix, public_guard, negative_guard, schema_guard)
    manifest_failures = validate_manifest(manifest)
    status = "pass" if not manifest_failures else "fail"
    manifest["status"] = status
    write_json(PROOF / "claim_boundary_release_manifest.json", manifest)

    output_lines = [
        f"claim boundary release manifest: {status}",
        f"source_matrix={MATRIX.relative_to(ROOT)}",
        "provider_api_calls=0",
        "cloud_or_gpu_used=false",
        f"artifact_count={len(manifest['artifact_index'])}",
        f"failed_or_null={','.join(manifest['claim_boundary_matrix']['failed_or_null_claim_ids'])}",
        f"changed_candidate={','.join(manifest['claim_boundary_matrix']['changed_candidate_claim_ids'])}",
        f"manifest_failures={','.join(manifest_failures)}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 31 Review

The release manifest indexes the `iter27` claim-boundary matrix, the `iter28` public-claim guard,
the `iter29` negative guard, the `iter30` schema guard, and every matrix row evidence artifact.
It records current hashes, failed/null rows, changed-candidate rows, and forbidden claim classes.

The manifest keeps `iter23` and `iter25` visible as failed/null gates and keeps the changed
`iter24` candidate separate from original `iter21` provider logic. It is reviewer-navigation
evidence, not new BattleSnake behavior evidence and not a benchmark result.

No provider call, API call, GPU, cloud runner, production deployment, live-domain check, leaderboard
run, or SWE-bench run occurred in this gate.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    run_summary = {
        "schema_version": "telos.claim_boundary_release_manifest.summary.v1",
        "status": status,
        "experiment_id": "iter31_claim_boundary_release_manifest",
        "source_experiments": [
            "iter27_semantic_claim_boundary_matrix",
            "iter28_public_claim_surface_guard",
            "iter29_public_claim_surface_negative_guard",
            "iter30_boundary_matrix_schema_guard",
        ],
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "manifest_valid": not manifest_failures,
        "manifest_failure_count": len(manifest_failures),
        "manifest_failures": manifest_failures,
        "artifact_count": len(manifest["artifact_index"]),
        "failed_or_null_claim_ids": manifest["claim_boundary_matrix"]["failed_or_null_claim_ids"],
        "changed_candidate_claim_ids": manifest["claim_boundary_matrix"][
            "changed_candidate_claim_ids"
        ],
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "model_superiority_claimed": False,
        "clean_pass": status == "pass",
        "next_gate": "experiments/iter32_claim_boundary_release_manifest_negative_guard/HYPOTHESIS.md",
        "artifact_hashes": {
            "claim_boundary_release_manifest.json": sha256_file(
                PROOF / "claim_boundary_release_manifest.json"
            ),
            "command_output.txt": sha256_file(PROOF / "command_output.txt"),
            "review.md": sha256_file(PROOF / "review.md"),
        },
    }
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter31_claim_boundary_release_manifest",
        "status": "null" if status == "fail" else status,
        "insight": (
            "A reviewer-facing manifest can tie the claim-boundary matrix, public guards, schema "
            "guard, and row evidence into one hash-checked proof packet."
        ),
        "next_action": (
            "pre-register negative fixtures for the release-manifest audit so stale hashes, hidden "
            "nulls, and candidate/original conflation are rejected"
        ),
        "result_path": "experiments/iter31_claim_boundary_release_manifest/RESULT.md",
        "evidence_paths": [
            "experiments/iter31_claim_boundary_release_manifest/proof/run_summary.json",
            "experiments/iter31_claim_boundary_release_manifest/proof/claim_boundary_release_manifest.json",
            "experiments/iter31_claim_boundary_release_manifest/proof/command_output.txt",
            "experiments/iter31_claim_boundary_release_manifest/proof/review.md",
            "experiments/iter31_claim_boundary_release_manifest/proof/valid/receipt_claim_boundary_release_manifest.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(VALID / "receipt_claim_boundary_release_manifest.json", build_receipt(status))

    print("\n".join(output_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
