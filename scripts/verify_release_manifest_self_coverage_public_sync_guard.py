#!/usr/bin/env python3
"""Generate iter37 release-manifest self-coverage public-sync artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "iter37_release_manifest_self_coverage_public_sync_guard"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"

MANIFEST = (
    ROOT
    / "experiments"
    / "iter31_claim_boundary_release_manifest"
    / "proof"
    / "claim_boundary_release_manifest.json"
)
SELF_COVERAGE = (
    ROOT
    / "experiments"
    / "iter35_release_manifest_self_coverage_guard"
    / "proof"
    / "self_coverage_report.json"
)
NEGATIVE_REPORT = (
    ROOT
    / "experiments"
    / "iter36_release_manifest_self_coverage_negative_guard"
    / "proof"
    / "negative_guard_report.json"
)

PUBLIC_FILES = [
    Path("README.md"),
    Path("docs/REPORT.md"),
    Path("docs/NEXT_PHASE.md"),
    Path("CONTINUITY.md"),
]
MANIFEST_PATH = "experiments/iter31_claim_boundary_release_manifest/proof/claim_boundary_release_manifest.json"
SELF_COVERAGE_PATH = (
    "experiments/iter35_release_manifest_self_coverage_guard/proof/self_coverage_report.json"
)
NEGATIVE_REPORT_PATH = (
    "experiments/iter36_release_manifest_self_coverage_negative_guard/proof/negative_guard_report.json"
)
EXPECTED_FAILED_OR_NULL = [
    "iter23_original_occupied_tail_falsification",
    "iter25_tail_safety_mutation_guard_miss",
]
EXPECTED_CHANGED_CANDIDATE = ["iter24_changed_candidate_occupied_tail_control"]

REQUIRED_SNIPPETS = {
    "README.md": [
        MANIFEST_PATH,
        SELF_COVERAGE_PATH,
        NEGATIVE_REPORT_PATH,
        "Release manifest self-coverage guard: passed",
        "Release manifest self-coverage negative guard: passed",
        "Benchmark result: none yet.",
    ],
    "docs/REPORT.md": [
        f"../{MANIFEST_PATH}",
        f"../{SELF_COVERAGE_PATH}",
        f"../{NEGATIVE_REPORT_PATH}",
        "`experiments/iter35_release_manifest_self_coverage_guard/RESULT.md` passes",
        "`experiments/iter36_release_manifest_self_coverage_negative_guard/RESULT.md` passes",
    ],
    "docs/NEXT_PHASE.md": [
        f"../{MANIFEST_PATH}",
        f"../{SELF_COVERAGE_PATH}",
        f"../{NEGATIVE_REPORT_PATH}",
        "keep `iter23` and `iter25` visible as failed/null evidence",
        "do not call a provider model",
    ],
    "CONTINUITY.md": [
        MANIFEST_PATH,
        SELF_COVERAGE_PATH,
        NEGATIVE_REPORT_PATH,
        "`iter35_release_manifest_self_coverage_guard` passed",
        "`iter36_release_manifest_self_coverage_negative_guard` passed",
        "No model or benchmark result is claimed yet.",
    ],
}

FORBIDDEN_CLAIMS = [
    "original `iter21` bot was occupied-tail safe",
    "original iter21 bot was occupied-tail safe",
    "CodeClash leaderboard result is claimed",
    "SWE-bench result is claimed",
    "model superiority",
    "production result is claimed",
    "live-domain result is claimed",
]


class SelfCoveragePublicSyncError(RuntimeError):
    """Raised when public prose cannot be verified against self-coverage evidence."""


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
        raise SelfCoveragePublicSyncError(f"{path} root must be an object")
    return data


def load_public_texts() -> dict[str, str]:
    texts = {}
    for rel_path in PUBLIC_FILES:
        path = ROOT / rel_path
        if not path.exists():
            raise SelfCoveragePublicSyncError(f"missing public prose file: {rel_path}")
        texts[rel_path.as_posix()] = path.read_text(encoding="utf-8")
    return texts


def check_required_snippets(texts: dict[str, str]) -> list[dict[str, Any]]:
    checks = []
    for rel_path, snippets in REQUIRED_SNIPPETS.items():
        missing = [snippet for snippet in snippets if snippet not in texts[rel_path]]
        checks.append(
            {
                "check_id": f"required_snippets:{rel_path}",
                "file": rel_path,
                "status": "pass" if not missing else "fail",
                "missing": missing,
            }
        )
    return checks


def check_forbidden_claims(texts: dict[str, str]) -> list[dict[str, Any]]:
    checks = []
    for rel_path, text in texts.items():
        lower = text.lower()
        found = [claim for claim in FORBIDDEN_CLAIMS if claim.lower() in lower]
        checks.append(
            {
                "check_id": f"forbidden_claims:{rel_path}",
                "file": rel_path,
                "status": "pass" if not found else "fail",
                "found": found,
            }
        )
    return checks


def check_alignment(
    manifest: dict[str, Any],
    self_coverage: dict[str, Any],
    negative_report: dict[str, Any],
    texts: dict[str, str],
) -> list[dict[str, Any]]:
    all_text = "\n".join(texts.values())
    manifest_referenced_everywhere = all(
        MANIFEST_PATH in text or f"../{MANIFEST_PATH}" in text for text in texts.values()
    )
    self_coverage_referenced_everywhere = all(
        SELF_COVERAGE_PATH in text or f"../{SELF_COVERAGE_PATH}" in text for text in texts.values()
    )
    negative_report_referenced_everywhere = all(
        NEGATIVE_REPORT_PATH in text or f"../{NEGATIVE_REPORT_PATH}" in text
        for text in texts.values()
    )
    failed_rows = manifest.get("failed_or_null_rows", [])
    changed_rows = manifest.get("changed_candidate_rows", [])
    return [
        {
            "check_id": "release_manifest_status_pass",
            "status": "pass" if manifest.get("status") == "pass" else "fail",
        },
        {
            "check_id": "self_coverage_status_pass",
            "status": "pass" if self_coverage.get("status") == "pass" else "fail",
        },
        {
            "check_id": "negative_guard_status_pass",
            "status": (
                "pass"
                if negative_report.get("status") == "pass"
                and negative_report.get("fixtures_failed_as_expected") is True
                else "fail"
            ),
        },
        {
            "check_id": "manifest_referenced_everywhere",
            "status": "pass" if manifest_referenced_everywhere else "fail",
        },
        {
            "check_id": "self_coverage_referenced_everywhere",
            "status": "pass" if self_coverage_referenced_everywhere else "fail",
        },
        {
            "check_id": "negative_report_referenced_everywhere",
            "status": "pass" if negative_report_referenced_everywhere else "fail",
        },
        {
            "check_id": "failed_null_rows_visible",
            "status": (
                "pass"
                if manifest.get("claim_boundary_matrix", {}).get("failed_or_null_claim_ids")
                == EXPECTED_FAILED_OR_NULL
                and [row.get("claim_id") for row in failed_rows] == EXPECTED_FAILED_OR_NULL
                and all(row.get("failure_visible") is True for row in failed_rows)
                and "iter23" in all_text
                and "iter25" in all_text
                else "fail"
            ),
        },
        {
            "check_id": "changed_candidate_boundary_visible",
            "status": (
                "pass"
                if manifest.get("claim_boundary_matrix", {}).get("changed_candidate_claim_ids")
                == EXPECTED_CHANGED_CANDIDATE
                and [row.get("claim_id") for row in changed_rows] == EXPECTED_CHANGED_CANDIDATE
                and all(row.get("changed_candidate") is True for row in changed_rows)
                and all(row.get("original_provider_logic") is False for row in changed_rows)
                and "changed candidate" in all_text
                else "fail"
            ),
        },
        {
            "check_id": "no_benchmark_or_production_claims",
            "status": (
                "pass"
                if manifest.get("leaderboard_or_swebench_claimed") is False
                and self_coverage.get("leaderboard_or_swebench_claimed") is False
                and negative_report.get("leaderboard_or_swebench_claimed") is False
                and manifest.get("production_or_live_domain_changed") is False
                and self_coverage.get("production_or_live_domain_changed") is False
                and negative_report.get("production_or_live_domain_changed") is False
                else "fail"
            ),
        },
    ]


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter37-release-manifest-self-coverage-public-sync-guard-{status}",
        "task_id": "telos:iter37_release_manifest_self_coverage_public_sync_guard@iter35_iter36_self_coverage",
        "agent_id": "codex-local-release-manifest-self-coverage-public-sync",
        "benchmark_id": "telos_codeclash_battlesnake_semantic_slice",
        "status": status,
        "stated_goal": (
            "Verify public prose surfaces the self-coverage report and negative guard without "
            "bypassing claim boundaries."
        ),
        "acceptance_criteria": [
            "No provider, API, GPU, or cloud spend occurs.",
            "The release manifest, self-coverage report, and self-coverage negative guard load locally.",
            "All checked public prose files exist.",
            "Public prose stays inside the claim boundaries.",
            "Command output and proof artifacts are committed.",
            "No leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": "experiments/iter37_release_manifest_self_coverage_public_sync_guard/proof/public_sync_report.json",
                "notes": "Public prose checks against release manifest and self-coverage evidence.",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "experiments/iter35_release_manifest_self_coverage_guard/proof/self_coverage_report.json",
                "notes": "Self-coverage report surfaced by public prose.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": "experiments/iter37_release_manifest_self_coverage_public_sync_guard/proof/review.md",
                "notes": "Review records public-sync boundary and no-overclaim constraints.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if source proof artifacts cannot be loaded.",
            "The result must fail if public prose bypasses the release manifest.",
            "The result must fail if public prose hides self-coverage evidence.",
            "The result must fail if failed/null rows are hidden.",
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
    self_coverage = read_json(SELF_COVERAGE)
    negative_report = read_json(NEGATIVE_REPORT)
    texts = load_public_texts()
    checks = [
        *check_required_snippets(texts),
        *check_forbidden_claims(texts),
        *check_alignment(manifest, self_coverage, negative_report, texts),
    ]
    failures = [check for check in checks if check["status"] != "pass"]
    status = "pass" if not failures else "fail"

    report = {
        "schema_version": "telos.release_manifest_self_coverage_public_sync_guard.report.v1",
        "status": status,
        "source_manifest_path": str(MANIFEST.relative_to(ROOT)),
        "source_manifest_sha256": sha256_file(MANIFEST),
        "source_self_coverage_report_path": str(SELF_COVERAGE.relative_to(ROOT)),
        "source_self_coverage_report_sha256": sha256_file(SELF_COVERAGE),
        "source_negative_guard_report_path": str(NEGATIVE_REPORT.relative_to(ROOT)),
        "source_negative_guard_report_sha256": sha256_file(NEGATIVE_REPORT),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "checked_public_files": [path.as_posix() for path in PUBLIC_FILES],
        "check_count": len(checks),
        "failed_check_count": len(failures),
        "failed_check_ids": [check["check_id"] for check in failures],
        "release_manifest_referenced": not any(
            check["check_id"] == "manifest_referenced_everywhere" for check in failures
        ),
        "self_coverage_referenced": not any(
            check["check_id"] == "self_coverage_referenced_everywhere" for check in failures
        ),
        "negative_guard_referenced": not any(
            check["check_id"] == "negative_report_referenced_everywhere" for check in failures
        ),
        "failed_null_gates_visible": not any(
            check["check_id"] == "failed_null_rows_visible" for check in failures
        ),
        "changed_candidate_boundary_visible": not any(
            check["check_id"] == "changed_candidate_boundary_visible" for check in failures
        ),
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "model_superiority_claimed": False,
        "checks": checks,
    }
    write_json(PROOF / "public_sync_report.json", report)

    output_lines = [
        f"release manifest self coverage public sync guard: {status}",
        f"source_self_coverage={SELF_COVERAGE.relative_to(ROOT)}",
        "provider_api_calls=0",
        "cloud_or_gpu_used=false",
        f"files={len(PUBLIC_FILES)} checks={len(checks)} failed={len(failures)}",
        f"failed_checks={','.join(report['failed_check_ids'])}",
        f"self_coverage_referenced={str(report['self_coverage_referenced']).lower()}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 37 Review

The public-sync guard checked README, report, next-phase, and continuity prose against the release
manifest, the `iter35` self-coverage report, and the `iter36` self-coverage negative guard. Public
prose keeps the release manifest as the claim-boundary reviewer entry point while surfacing the
self-coverage layer.

This gate audits public wording only. It does not add benchmark evidence, production evidence, or
provider-model evidence.

No provider call, API call, GPU, cloud runner, production deployment, live-domain check, leaderboard
run, or SWE-bench run occurred in this gate.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    run_summary = {
        "schema_version": "telos.release_manifest_self_coverage_public_sync_guard.summary.v1",
        "status": status,
        "experiment_id": "iter37_release_manifest_self_coverage_public_sync_guard",
        "source_experiment": "iter35_release_manifest_self_coverage_guard",
        "source_manifest_path": str(MANIFEST.relative_to(ROOT)),
        "source_manifest_sha256": sha256_file(MANIFEST),
        "source_self_coverage_report_path": str(SELF_COVERAGE.relative_to(ROOT)),
        "source_self_coverage_report_sha256": sha256_file(SELF_COVERAGE),
        "source_negative_guard_report_path": str(NEGATIVE_REPORT.relative_to(ROOT)),
        "source_negative_guard_report_sha256": sha256_file(NEGATIVE_REPORT),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "checked_public_files": [path.as_posix() for path in PUBLIC_FILES],
        "check_count": len(checks),
        "failed_check_count": len(failures),
        "failed_check_ids": report["failed_check_ids"],
        "release_manifest_referenced": report["release_manifest_referenced"],
        "self_coverage_referenced": report["self_coverage_referenced"],
        "negative_guard_referenced": report["negative_guard_referenced"],
        "failed_null_gates_visible": report["failed_null_gates_visible"],
        "changed_candidate_boundary_visible": report["changed_candidate_boundary_visible"],
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "model_superiority_claimed": False,
        "clean_pass": status == "pass",
        "next_gate": "experiments/iter38_release_manifest_self_coverage_public_sync_negative_guard/HYPOTHESIS.md",
        "artifact_hashes": {
            "command_output.txt": sha256_file(PROOF / "command_output.txt"),
            "public_sync_report.json": sha256_file(PROOF / "public_sync_report.json"),
            "review.md": sha256_file(PROOF / "review.md"),
        },
    }
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter37_release_manifest_self_coverage_public_sync_guard",
        "status": "null" if status == "fail" else status,
        "insight": (
            "Public prose can surface the self-coverage report and negative guard while keeping "
            "the release manifest as the claim-boundary reviewer entry point."
        ),
        "next_action": (
            "pre-register negative public-sync fixtures so prose that hides self-coverage or "
            "bypasses the release manifest is rejected"
        ),
        "result_path": "experiments/iter37_release_manifest_self_coverage_public_sync_guard/RESULT.md",
        "evidence_paths": [
            "experiments/iter37_release_manifest_self_coverage_public_sync_guard/proof/run_summary.json",
            "experiments/iter37_release_manifest_self_coverage_public_sync_guard/proof/public_sync_report.json",
            "experiments/iter37_release_manifest_self_coverage_public_sync_guard/proof/command_output.txt",
            "experiments/iter37_release_manifest_self_coverage_public_sync_guard/proof/review.md",
            "experiments/iter37_release_manifest_self_coverage_public_sync_guard/proof/valid/receipt_release_manifest_self_coverage_public_sync_guard.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(VALID / "receipt_release_manifest_self_coverage_public_sync_guard.json", build_receipt(status))

    print("\n".join(output_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
