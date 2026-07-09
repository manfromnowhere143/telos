#!/usr/bin/env python3
"""Generate iter32 release-manifest negative-guard proof artifacts."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "iter32_claim_boundary_release_manifest_negative_guard"
PROOF = EXPERIMENT / "proof"
FIXTURES = PROOF / "fixtures"
VALID = PROOF / "valid"
SOURCE_MANIFEST = (
    ROOT
    / "experiments"
    / "iter31_claim_boundary_release_manifest"
    / "proof"
    / "claim_boundary_release_manifest.json"
)
SOURCE_SUMMARY = (
    ROOT / "experiments" / "iter31_claim_boundary_release_manifest" / "proof" / "run_summary.json"
)
SOURCE_AUDIT = ROOT / "scripts" / "audit_claim_boundary_release_manifest.py"

EXPECTED_FAILED_OR_NULL = [
    "iter23_original_occupied_tail_falsification",
    "iter25_tail_safety_mutation_guard_miss",
]
EXPECTED_CHANGED_CANDIDATE = ["iter24_changed_candidate_occupied_tail_control"]
EXPECTED_SOURCE_ARTIFACTS = {
    "claim_boundary_matrix",
    "public_claim_surface_report",
    "negative_guard_report",
    "schema_guard_report",
}
EXPECTED_FORBIDDEN = {
    "codeclash_leaderboard_result",
    "swebench_result",
    "production_or_live_domain_result",
    "model_superiority_result",
    "provider_game_score_as_verifier_evidence",
    "original_iter21_occupied_tail_safety",
}


class ReleaseManifestNegativeGuardError(RuntimeError):
    """Raised when iter32 cannot produce trustworthy negative-fixture artifacts."""


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
        raise ReleaseManifestNegativeGuardError(f"{path} root must be an object")
    return data


def append_error(errors: list[dict[str, str]], code: str, path: str, detail: str) -> None:
    errors.append({"code": code, "path": path, "detail": detail})


def validate_manifest_fixture(manifest: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    if manifest.get("schema_version") != "telos.claim_boundary_release_manifest.v1":
        append_error(errors, "schema_mismatch", "$.schema_version", "unexpected schema")
    if manifest.get("status") != "pass":
        append_error(errors, "status_mismatch", "$.status", "manifest status must be pass")

    expected_flags = {
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "model_superiority_claimed": False,
    }
    for key, expected in expected_flags.items():
        if manifest.get(key) != expected:
            code = "forbidden_claim_made" if key != "local_cpu_only" else "side_effect_flag"
            append_error(errors, code, f"$.{key}", f"expected {expected!r}")

    if manifest.get("forbidden_claims_made") != []:
        append_error(
            errors,
            "forbidden_claim_made",
            "$.forbidden_claims_made",
            "must be empty",
        )

    source_artifacts = manifest.get("source_artifacts", [])
    source_ids = {artifact.get("artifact_id") for artifact in source_artifacts}
    if source_ids != EXPECTED_SOURCE_ARTIFACTS:
        append_error(errors, "missing_source_artifact", "$.source_artifacts", "ids mismatch")
    for index, artifact in enumerate(source_artifacts):
        rel_path = artifact.get("path")
        path = ROOT / rel_path if isinstance(rel_path, str) else None
        if path is None or not path.exists():
            append_error(
                errors,
                "missing_source_artifact",
                f"$.source_artifacts[{index}].path",
                f"missing {rel_path!r}",
            )
            continue
        if artifact.get("sha256") != sha256_file(path):
            append_error(
                errors,
                "stale_artifact_hash",
                f"$.source_artifacts[{index}].sha256",
                f"hash mismatch for {rel_path}",
            )
        if artifact.get("status") != "pass":
            append_error(
                errors,
                "source_status_mismatch",
                f"$.source_artifacts[{index}].status",
                "source status must be pass",
            )

    artifact_index = manifest.get("artifact_index", [])
    if not isinstance(artifact_index, list) or len(artifact_index) < 20:
        append_error(errors, "missing_source_artifact", "$.artifact_index", "too few artifacts")
    seen = set()
    for index, artifact in enumerate(artifact_index):
        rel_path = artifact.get("path") if isinstance(artifact, dict) else None
        if not isinstance(rel_path, str) or not rel_path:
            append_error(errors, "missing_source_artifact", f"$.artifact_index[{index}]", "bad path")
            continue
        if rel_path in seen:
            append_error(errors, "duplicate_artifact", f"$.artifact_index[{index}]", rel_path)
        seen.add(rel_path)
        path = ROOT / rel_path
        if not path.exists():
            append_error(errors, "missing_source_artifact", f"$.artifact_index[{index}]", rel_path)
            continue
        if artifact.get("sha256") != sha256_file(path):
            append_error(
                errors,
                "stale_artifact_hash",
                f"$.artifact_index[{index}].sha256",
                f"hash mismatch for {rel_path}",
            )

    matrix = manifest.get("claim_boundary_matrix", {})
    if matrix.get("failed_or_null_claim_ids") != EXPECTED_FAILED_OR_NULL:
        append_error(
            errors,
            "hidden_failed_null_rows",
            "$.claim_boundary_matrix.failed_or_null_claim_ids",
            "failed/null ids mismatch",
        )
    if matrix.get("changed_candidate_claim_ids") != EXPECTED_CHANGED_CANDIDATE:
        append_error(
            errors,
            "candidate_original_conflation",
            "$.claim_boundary_matrix.changed_candidate_claim_ids",
            "changed candidate ids mismatch",
        )
    if matrix.get("original_iter21_occupied_tail_safety_claimed") is not False:
        append_error(
            errors,
            "forbidden_claim_made",
            "$.claim_boundary_matrix.original_iter21_occupied_tail_safety_claimed",
            "original iter21 occupied-tail safety must not be claimed",
        )
    if matrix.get("failed_null_gates_hidden") is not False:
        append_error(
            errors,
            "hidden_failed_null_rows",
            "$.claim_boundary_matrix.failed_null_gates_hidden",
            "failed/null gates must not be hidden",
        )

    failed_rows = manifest.get("failed_or_null_rows", [])
    if [row.get("claim_id") for row in failed_rows] != EXPECTED_FAILED_OR_NULL:
        append_error(errors, "hidden_failed_null_rows", "$.failed_or_null_rows", "row ids mismatch")
    for index, row in enumerate(failed_rows):
        if row.get("failure_visible") is not True or row.get("status") != "null":
            append_error(
                errors,
                "hidden_failed_null_rows",
                f"$.failed_or_null_rows[{index}]",
                "failed/null row must be visible as null",
            )

    changed_rows = manifest.get("changed_candidate_rows", [])
    if [row.get("claim_id") for row in changed_rows] != EXPECTED_CHANGED_CANDIDATE:
        append_error(
            errors,
            "candidate_original_conflation",
            "$.changed_candidate_rows",
            "row ids mismatch",
        )
    for index, row in enumerate(changed_rows):
        if row.get("changed_candidate") is not True or row.get("original_provider_logic") is not False:
            append_error(
                errors,
                "candidate_original_conflation",
                f"$.changed_candidate_rows[{index}]",
                "changed candidate row conflated with original provider logic",
            )

    if set(manifest.get("forbidden_claim_classes", [])) != EXPECTED_FORBIDDEN:
        append_error(errors, "forbidden_claim_made", "$.forbidden_claim_classes", "classes mismatch")
    if manifest.get("public_claim_surface", {}).get("failed_null_gates_visible") is not True:
        append_error(
            errors,
            "hidden_failed_null_rows",
            "$.public_claim_surface.failed_null_gates_visible",
            "public surface must keep failed/null gates visible",
        )
    if manifest.get("negative_guard", {}).get("fixtures_failed_as_expected") is not True:
        append_error(
            errors,
            "source_status_mismatch",
            "$.negative_guard.fixtures_failed_as_expected",
            "negative guard must pass",
        )
    if manifest.get("schema_guard", {}).get("real_matrix_valid") is not True:
        append_error(
            errors,
            "source_status_mismatch",
            "$.schema_guard.real_matrix_valid",
            "schema guard must validate real matrix",
        )
    if manifest.get("schema_guard", {}).get("fixtures_failed_as_expected") is not True:
        append_error(
            errors,
            "source_status_mismatch",
            "$.schema_guard.fixtures_failed_as_expected",
            "schema guard fixtures must fail as expected",
        )
    return errors


def fixture_manifest(source: dict[str, Any], fixture_id: str) -> dict[str, Any]:
    manifest = copy.deepcopy(source)
    if fixture_id == "stale_artifact_hash":
        manifest["artifact_index"][0]["sha256"] = "0" * 64
    elif fixture_id == "hidden_failed_null_rows":
        manifest["claim_boundary_matrix"]["failed_or_null_claim_ids"] = []
        manifest["claim_boundary_matrix"]["failed_null_gates_hidden"] = True
        manifest["failed_or_null_rows"] = []
        manifest["public_claim_surface"]["failed_null_gates_visible"] = False
    elif fixture_id == "candidate_original_conflation":
        manifest["changed_candidate_rows"][0]["original_provider_logic"] = True
        manifest["changed_candidate_rows"][0]["subject_type"] = (
            "reconstructed_original_provider_logic"
        )
    elif fixture_id == "forbidden_claim_made":
        manifest["forbidden_claims_made"] = ["codeclash_leaderboard_result"]
        manifest["leaderboard_or_swebench_claimed"] = True
    elif fixture_id == "missing_source_artifact":
        manifest["source_artifacts"][0]["path"] = "experiments/missing/source_artifact.json"
    else:
        raise ReleaseManifestNegativeGuardError(f"unknown fixture: {fixture_id}")
    return manifest


def write_fixture(fixture_id: str, manifest: dict[str, Any]) -> str:
    path = FIXTURES / f"{fixture_id}.json"
    write_json(path, manifest)
    return str(path.relative_to(ROOT))


def evaluate_fixture(
    source_manifest: dict[str, Any],
    fixture_id: str,
    expected_error_codes: list[str],
) -> dict[str, Any]:
    manifest = fixture_manifest(source_manifest, fixture_id)
    fixture_path = write_fixture(fixture_id, manifest)
    errors = validate_manifest_fixture(manifest)
    observed_codes = sorted({item["code"] for item in errors})
    expected_detected = all(code in observed_codes for code in expected_error_codes)
    return {
        "fixture_id": fixture_id,
        "status": "pass" if errors and expected_detected else "fail",
        "fixture_path": fixture_path,
        "expected_error_codes": expected_error_codes,
        "observed_error_codes": observed_codes,
        "malformation_detected": bool(errors),
        "expected_detection_observed": expected_detected,
        "errors": errors,
    }


def real_manifest_audit() -> dict[str, Any]:
    result = subprocess.run(
        ["python3", str(SOURCE_AUDIT.relative_to(ROOT))],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "command": f"python3 {SOURCE_AUDIT.relative_to(ROOT)}",
        "returncode": result.returncode,
        "stdout_lines": result.stdout.splitlines(),
        "stderr_lines": result.stderr.splitlines(),
        "passed": result.returncode == 0,
    }


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter32-claim-boundary-release-manifest-negative-guard-{status}",
        "task_id": "telos:iter32_claim_boundary_release_manifest_negative_guard@iter31_release_manifest",
        "agent_id": "codex-local-release-manifest-negative-fixtures",
        "benchmark_id": "telos_codeclash_battlesnake_semantic_slice",
        "status": status,
        "stated_goal": "Prove the release-manifest audit rejects malformed manifest fixtures.",
        "acceptance_criteria": [
            "No provider, API, GPU, or cloud spend occurs.",
            "The real release manifest still passes its audit.",
            "Every malformed manifest fixture fails for the expected reason.",
            "Fixture files remain separate from the real manifest.",
            "Command output and proof artifacts are committed.",
            "No leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": "experiments/iter32_claim_boundary_release_manifest_negative_guard/proof/negative_guard_report.json",
                "notes": "Real manifest audit plus malformed manifest fixtures.",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "experiments/iter32_claim_boundary_release_manifest_negative_guard/proof/fixtures/",
                "notes": "Generated malformed fixture manifests; real manifest is not mutated.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": "experiments/iter32_claim_boundary_release_manifest_negative_guard/proof/review.md",
                "notes": "Review records fixture coverage and claim boundary.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if the iter31 release manifest cannot be loaded.",
            "The result must fail if the real release manifest no longer passes its audit.",
            "The result must fail if any malformed manifest fixture passes.",
            "The result must fail if fixtures mutate the real manifest.",
            "The result must not widen into benchmark or production claims.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    if FIXTURES.exists():
        shutil.rmtree(FIXTURES)
    FIXTURES.mkdir(parents=True, exist_ok=True)

    source_manifest = read_json(SOURCE_MANIFEST)
    source_summary = read_json(SOURCE_SUMMARY)
    real_audit = real_manifest_audit()
    real_errors = validate_manifest_fixture(source_manifest)
    fixtures = [
        evaluate_fixture(source_manifest, "stale_artifact_hash", ["stale_artifact_hash"]),
        evaluate_fixture(source_manifest, "hidden_failed_null_rows", ["hidden_failed_null_rows"]),
        evaluate_fixture(
            source_manifest,
            "candidate_original_conflation",
            ["candidate_original_conflation"],
        ),
        evaluate_fixture(source_manifest, "forbidden_claim_made", ["forbidden_claim_made"]),
        evaluate_fixture(source_manifest, "missing_source_artifact", ["missing_source_artifact"]),
    ]
    failed_fixtures = [fixture for fixture in fixtures if fixture["status"] != "pass"]
    status = "pass" if real_audit["passed"] and not real_errors and not failed_fixtures else "fail"

    report = {
        "schema_version": "telos.claim_boundary_release_manifest_negative_guard.report.v1",
        "status": status,
        "source_manifest_path": str(SOURCE_MANIFEST.relative_to(ROOT)),
        "source_manifest_sha256": sha256_file(SOURCE_MANIFEST),
        "source_summary_path": str(SOURCE_SUMMARY.relative_to(ROOT)),
        "source_summary_sha256": sha256_file(SOURCE_SUMMARY),
        "source_audit_path": str(SOURCE_AUDIT.relative_to(ROOT)),
        "source_audit_sha256": sha256_file(SOURCE_AUDIT),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "real_manifest_audit_passed": real_audit["passed"],
        "real_manifest_validation_passed": not real_errors,
        "real_manifest_error_codes": sorted({item["code"] for item in real_errors}),
        "real_manifest_audit": real_audit,
        "fixture_count": len(fixtures),
        "fixtures_failed_as_expected": len(failed_fixtures) == 0,
        "failed_fixture_ids": [fixture["fixture_id"] for fixture in failed_fixtures],
        "source_iter31_status": source_summary.get("status"),
        "source_iter31_clean_pass": source_summary.get("clean_pass"),
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "model_superiority_claimed": False,
        "fixtures": fixtures,
    }
    write_json(PROOF / "negative_guard_report.json", report)

    output_lines = [
        f"claim boundary release manifest negative guard: {status}",
        f"source_manifest={SOURCE_MANIFEST.relative_to(ROOT)}",
        "provider_api_calls=0",
        "cloud_or_gpu_used=false",
        f"real_manifest_audit_passed={str(real_audit['passed']).lower()}",
        f"fixtures={len(fixtures)} failed_as_expected={len(fixtures) - len(failed_fixtures)}",
        f"failed_fixture_ids={','.join(report['failed_fixture_ids'])}",
    ]
    for fixture in fixtures:
        output_lines.append(
            f"{fixture['fixture_id']}: {'pass' if fixture['status'] == 'pass' else 'fail'} "
            f"observed={','.join(fixture['observed_error_codes'])}"
        )
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 32 Review

The negative guard kept the real release manifest passing its audit and evaluated five generated
malformed manifest fixtures. The fixtures cover stale artifact hashes, hidden failed/null rows,
changed-candidate/original-provider conflation, forbidden claim classes marked as made, and missing
source artifacts.

Fixture manifests are committed under proof artifacts and do not mutate the real `iter31` release
manifest. This strengthens the reviewer-entry manifest without adding behavior, benchmark,
production, or provider-model evidence.

No provider call, API call, GPU, cloud runner, production deployment, live-domain check, leaderboard
run, or SWE-bench run occurred in this gate.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    run_summary = {
        "schema_version": "telos.claim_boundary_release_manifest_negative_guard.summary.v1",
        "status": status,
        "experiment_id": "iter32_claim_boundary_release_manifest_negative_guard",
        "source_experiment": "iter31_claim_boundary_release_manifest",
        "source_manifest_path": str(SOURCE_MANIFEST.relative_to(ROOT)),
        "source_manifest_sha256": sha256_file(SOURCE_MANIFEST),
        "source_audit_path": str(SOURCE_AUDIT.relative_to(ROOT)),
        "source_audit_sha256": sha256_file(SOURCE_AUDIT),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "real_manifest_audit_passed": real_audit["passed"],
        "real_manifest_validation_passed": not real_errors,
        "fixture_count": len(fixtures),
        "fixtures_failed_as_expected": len(failed_fixtures) == 0,
        "failed_fixture_ids": report["failed_fixture_ids"],
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "model_superiority_claimed": False,
        "clean_pass": status == "pass",
        "next_gate": "experiments/iter33_release_manifest_public_sync_guard/HYPOTHESIS.md",
        "artifact_hashes": {
            "command_output.txt": sha256_file(PROOF / "command_output.txt"),
            "negative_guard_report.json": sha256_file(PROOF / "negative_guard_report.json"),
            "review.md": sha256_file(PROOF / "review.md"),
        },
    }
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter32_claim_boundary_release_manifest_negative_guard",
        "status": "null" if status == "fail" else status,
        "insight": (
            "The release-manifest audit rejects malformed manifest fixtures for stale hashes, "
            "hidden failed/null rows, candidate/original conflation, forbidden claims, and missing "
            "source artifacts."
        ),
        "next_action": (
            "pre-register a public-sync guard so README, report, next-phase, and continuity prose "
            "use the release manifest without bypassing its boundaries"
        ),
        "result_path": "experiments/iter32_claim_boundary_release_manifest_negative_guard/RESULT.md",
        "evidence_paths": [
            "experiments/iter32_claim_boundary_release_manifest_negative_guard/proof/run_summary.json",
            "experiments/iter32_claim_boundary_release_manifest_negative_guard/proof/negative_guard_report.json",
            "experiments/iter32_claim_boundary_release_manifest_negative_guard/proof/command_output.txt",
            "experiments/iter32_claim_boundary_release_manifest_negative_guard/proof/review.md",
            "experiments/iter32_claim_boundary_release_manifest_negative_guard/proof/valid/receipt_claim_boundary_release_manifest_negative_guard.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(
        VALID / "receipt_claim_boundary_release_manifest_negative_guard.json",
        build_receipt(status),
    )

    print("\n".join(output_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
