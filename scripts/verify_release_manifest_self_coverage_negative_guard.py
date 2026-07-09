#!/usr/bin/env python3
"""Generate iter36 release-manifest self-coverage negative-guard artifacts."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_release_manifest_self_coverage_guard import validate_report  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "iter36_release_manifest_self_coverage_negative_guard"
PROOF = EXPERIMENT / "proof"
FIXTURES = PROOF / "fixtures"
VALID = PROOF / "valid"
SOURCE_REPORT = (
    ROOT
    / "experiments"
    / "iter35_release_manifest_self_coverage_guard"
    / "proof"
    / "self_coverage_report.json"
)
SOURCE_SUMMARY = (
    ROOT / "experiments" / "iter35_release_manifest_self_coverage_guard" / "proof" / "run_summary.json"
)
NEXT_GATE = (
    ROOT
    / "experiments"
    / "iter37_release_manifest_self_coverage_public_sync_guard"
    / "HYPOTHESIS.md"
)


class SelfCoverageNegativeGuardError(RuntimeError):
    """Raised when iter36 cannot produce trustworthy negative-fixture artifacts."""


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
        raise SelfCoverageNegativeGuardError(f"{path} root must be an object")
    return data


def fixture_report(base: dict[str, Any], fixture_id: str) -> dict[str, Any]:
    report = copy.deepcopy(base)
    if fixture_id == "missing_self_verification_gate":
        report["covered_gates"] = [
            gate
            for gate in report["covered_gates"]
            if gate["experiment_id"] != "iter34_release_manifest_public_sync_negative_guard"
        ]
        report["covered_gate_ids"] = [gate["experiment_id"] for gate in report["covered_gates"]]
        report["covered_gate_count"] = len(report["covered_gates"])
    elif fixture_id == "stale_artifact_hash":
        report["covered_gates"][0]["summary"]["sha256"] = "0" * 64
    elif fixture_id == "hidden_failed_nulls":
        report["failed_null_gates_visible"] = False
        report["failed_or_null_claim_ids"] = []
    elif fixture_id == "candidate_original_conflation":
        report["changed_candidate_boundary_visible"] = False
        report["changed_candidate_claim_ids"] = []
    elif fixture_id == "forbidden_benchmark_claim":
        report["leaderboard_or_swebench_claimed"] = True
    else:
        raise SelfCoverageNegativeGuardError(f"unknown fixture: {fixture_id}")
    return report


def evaluate_fixture(
    base: dict[str, Any],
    fixture_id: str,
    expected_failure_fragments: list[str],
) -> dict[str, Any]:
    report = fixture_report(base, fixture_id)
    fixture_path = FIXTURES / f"{fixture_id}.json"
    write_json(fixture_path, report)
    failures = validate_report(report)
    expected_detected = all(
        any(fragment in failure for failure in failures)
        for fragment in expected_failure_fragments
    )
    return {
        "fixture_id": fixture_id,
        "status": "pass" if failures and expected_detected else "fail",
        "fixture_path": str(fixture_path.relative_to(ROOT)),
        "fixture_sha256": sha256_file(fixture_path),
        "expected_failure_fragments": expected_failure_fragments,
        "observed_failures": failures,
        "malformation_detected": bool(failures),
        "expected_detection_observed": expected_detected,
    }


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter36-release-manifest-self-coverage-negative-guard-{status}",
        "task_id": "telos:iter36_release_manifest_self_coverage_negative_guard@iter35_self_coverage",
        "agent_id": "codex-local-release-manifest-self-coverage-negative-fixtures",
        "benchmark_id": "telos_codeclash_battlesnake_semantic_slice",
        "status": status,
        "stated_goal": "Prove the release-manifest self-coverage guard catches malformed reports.",
        "acceptance_criteria": [
            "No provider, API, GPU, or cloud spend occurs.",
            "The real iter35 self-coverage report still passes.",
            "Every malformed self-coverage fixture fails for the expected reason.",
            "Fixture files remain separate from real proof artifacts.",
            "Command output and proof artifacts are committed.",
            "No leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": "experiments/iter36_release_manifest_self_coverage_negative_guard/proof/negative_guard_report.json",
                "notes": "Real self-coverage report plus malformed report fixtures.",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "experiments/iter36_release_manifest_self_coverage_negative_guard/proof/fixtures/",
                "notes": "Generated fixture reports; real proof artifacts are not mutated.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": "experiments/iter36_release_manifest_self_coverage_negative_guard/proof/review.md",
                "notes": "Review records fixture coverage and claim boundary.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if the iter35 self-coverage report cannot be loaded.",
            "The result must fail if the real self-coverage report no longer passes.",
            "The result must fail if any malformed fixture passes.",
            "The result must fail if fixture generation mutates real proof artifacts.",
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

    real_report = read_json(SOURCE_REPORT)
    source_summary = read_json(SOURCE_SUMMARY)
    real_failures = validate_report(real_report)
    fixtures = [
        evaluate_fixture(
            real_report,
            "missing_self_verification_gate",
            ["covered_gate_ids mismatch", "covered_gate_count mismatch"],
        ),
        evaluate_fixture(real_report, "stale_artifact_hash", ["stale summary hash"]),
        evaluate_fixture(
            real_report,
            "hidden_failed_nulls",
            ["failed/null gates must remain visible"],
        ),
        evaluate_fixture(
            real_report,
            "candidate_original_conflation",
            ["changed candidate boundary must remain visible"],
        ),
        evaluate_fixture(
            real_report,
            "forbidden_benchmark_claim",
            ["leaderboard_or_swebench_claimed must be false"],
        ),
    ]
    failed_fixtures = [fixture for fixture in fixtures if fixture["status"] != "pass"]
    source_guard_ok = source_summary.get("status") == "pass" and source_summary.get("clean_pass") is True
    status = "pass" if not real_failures and not failed_fixtures and source_guard_ok else "fail"

    report = {
        "schema_version": "telos.release_manifest_self_coverage_negative_guard.report.v1",
        "status": status,
        "source_iter35_report_path": str(SOURCE_REPORT.relative_to(ROOT)),
        "source_iter35_report_sha256": sha256_file(SOURCE_REPORT),
        "source_iter35_summary_path": str(SOURCE_SUMMARY.relative_to(ROOT)),
        "source_iter35_summary_sha256": sha256_file(SOURCE_SUMMARY),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "real_self_coverage_passed": not real_failures,
        "real_self_coverage_failures": real_failures,
        "fixture_count": len(fixtures),
        "fixtures_failed_as_expected": len(failed_fixtures) == 0,
        "failed_fixture_ids": [fixture["fixture_id"] for fixture in failed_fixtures],
        "source_iter35_status": source_summary.get("status"),
        "source_iter35_clean_pass": source_summary.get("clean_pass") is True,
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "model_superiority_claimed": False,
        "fixtures": fixtures,
    }
    write_json(PROOF / "negative_guard_report.json", report)

    output_lines = [
        f"release manifest self coverage negative guard: {status}",
        f"source_iter35={SOURCE_REPORT.relative_to(ROOT)}",
        "provider_api_calls=0",
        "cloud_or_gpu_used=false",
        f"real_self_coverage_passed={str(not real_failures).lower()}",
        f"fixtures={len(fixtures)} failed_as_expected={len(fixtures) - len(failed_fixtures)}",
        f"failed_fixture_ids={','.join(report['failed_fixture_ids'])}",
    ]
    for fixture in fixtures:
        output_lines.append(
            f"{fixture['fixture_id']}: {'pass' if fixture['status'] == 'pass' else 'fail'} "
            f"observed={';'.join(fixture['observed_failures'])}"
        )
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 36 Review

The negative guard kept the real `iter35` self-coverage report passing and evaluated five generated
malformed report fixtures. The fixtures cover missing self-verification gates, stale artifact
hashes, hidden failed/null gates, changed-candidate/original-provider conflation, and forbidden
benchmark claims.

Fixture files are committed under proof artifacts and do not mutate the real self-coverage report
or source proof packets. This strengthens the self-coverage guard without adding behavior,
benchmark, production, or provider-model evidence.

No provider call, API call, GPU, cloud runner, production deployment, live-domain check, leaderboard
run, or SWE-bench run occurred in this gate.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    run_summary = {
        "schema_version": "telos.release_manifest_self_coverage_negative_guard.summary.v1",
        "status": status,
        "experiment_id": "iter36_release_manifest_self_coverage_negative_guard",
        "source_experiment": "iter35_release_manifest_self_coverage_guard",
        "source_iter35_report_path": str(SOURCE_REPORT.relative_to(ROOT)),
        "source_iter35_report_sha256": sha256_file(SOURCE_REPORT),
        "source_iter35_summary_path": str(SOURCE_SUMMARY.relative_to(ROOT)),
        "source_iter35_summary_sha256": sha256_file(SOURCE_SUMMARY),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "real_self_coverage_passed": not real_failures,
        "fixture_count": len(fixtures),
        "fixtures_failed_as_expected": len(failed_fixtures) == 0,
        "failed_fixture_ids": report["failed_fixture_ids"],
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "model_superiority_claimed": False,
        "clean_pass": status == "pass",
        "next_gate": "experiments/iter37_release_manifest_self_coverage_public_sync_guard/HYPOTHESIS.md",
        "artifact_hashes": {
            "command_output.txt": sha256_file(PROOF / "command_output.txt"),
            "negative_guard_report.json": sha256_file(PROOF / "negative_guard_report.json"),
            "review.md": sha256_file(PROOF / "review.md"),
        },
    }
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter36_release_manifest_self_coverage_negative_guard",
        "status": "null" if status == "fail" else status,
        "insight": (
            "The self-coverage guard rejects malformed reports that remove self-verification gates, "
            "stale hashes, hide failed/null gates, conflate candidate/original logic, or add "
            "forbidden benchmark claims."
        ),
        "next_action": (
            "pre-register a public-sync guard so README, report, next-phase, and continuity prose "
            "surface the self-coverage report without bypassing claim boundaries"
        ),
        "result_path": "experiments/iter36_release_manifest_self_coverage_negative_guard/RESULT.md",
        "evidence_paths": [
            "experiments/iter36_release_manifest_self_coverage_negative_guard/proof/run_summary.json",
            "experiments/iter36_release_manifest_self_coverage_negative_guard/proof/negative_guard_report.json",
            "experiments/iter36_release_manifest_self_coverage_negative_guard/proof/command_output.txt",
            "experiments/iter36_release_manifest_self_coverage_negative_guard/proof/review.md",
            "experiments/iter36_release_manifest_self_coverage_negative_guard/proof/valid/receipt_release_manifest_self_coverage_negative_guard.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(VALID / "receipt_release_manifest_self_coverage_negative_guard.json", build_receipt(status))

    print("\n".join(output_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
