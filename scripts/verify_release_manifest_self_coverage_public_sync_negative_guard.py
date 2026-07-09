#!/usr/bin/env python3
"""Generate iter38 self-coverage public-sync negative-guard artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_release_manifest_self_coverage_public_sync_guard import (  # noqa: E402
    MANIFEST,
    MANIFEST_PATH,
    NEGATIVE_REPORT,
    NEGATIVE_REPORT_PATH,
    PUBLIC_FILES,
    SELF_COVERAGE,
    SELF_COVERAGE_PATH,
    check_alignment,
    check_forbidden_claims,
    check_required_snippets,
    read_json,
)


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "iter38_release_manifest_self_coverage_public_sync_negative_guard"
PROOF = EXPERIMENT / "proof"
FIXTURES = PROOF / "fixtures"
VALID = PROOF / "valid"
SOURCE_ITER37_REPORT = (
    ROOT
    / "experiments"
    / "iter37_release_manifest_self_coverage_public_sync_guard"
    / "proof"
    / "public_sync_report.json"
)


class SelfCoveragePublicSyncNegativeGuardError(RuntimeError):
    """Raised when iter38 cannot produce trustworthy negative-fixture artifacts."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_public_texts() -> dict[str, str]:
    texts = {}
    for rel_path in PUBLIC_FILES:
        path = ROOT / rel_path
        if not path.exists():
            raise SelfCoveragePublicSyncNegativeGuardError(
                f"missing public prose file: {rel_path}"
            )
        texts[rel_path.as_posix()] = path.read_text(encoding="utf-8")
    return texts


def run_guard(
    manifest: dict[str, Any],
    self_coverage: dict[str, Any],
    negative_report: dict[str, Any],
    texts: dict[str, str],
) -> list[dict[str, Any]]:
    return [
        *check_required_snippets(texts),
        *check_forbidden_claims(texts),
        *check_alignment(manifest, self_coverage, negative_report, texts),
    ]


def replace_all(text: str, replacements: list[tuple[str, str]]) -> str:
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def remove_path_forms(text: str, rel_path: str) -> str:
    return text.replace(f"../{rel_path}", "").replace(rel_path, "")


def fixture_texts(base: dict[str, str], fixture_id: str) -> dict[str, str]:
    texts = dict(base)
    if fixture_id == "missing_release_manifest_reference":
        texts = {rel_path: remove_path_forms(text, MANIFEST_PATH) for rel_path, text in texts.items()}
    elif fixture_id == "missing_self_coverage_report_reference":
        texts = {
            rel_path: remove_path_forms(text, SELF_COVERAGE_PATH)
            for rel_path, text in texts.items()
        }
    elif fixture_id == "missing_self_coverage_negative_guard_reference":
        texts = {
            rel_path: remove_path_forms(text, NEGATIVE_REPORT_PATH)
            for rel_path, text in texts.items()
        }
    elif fixture_id == "hidden_failed_nulls":
        replacements = [
            ("Tail semantics falsification: failed", "Tail semantics falsification: passed"),
            ("Tail safety mutation guard: failed", "Tail safety mutation guard: passed"),
            ("`iter23` and `iter25` visible as failed/null evidence", "prior gates visible"),
            ("iter23", "iteration twenty-three"),
            ("iter25", "iteration twenty-five"),
        ]
        texts = {rel_path: replace_all(text, replacements) for rel_path, text in texts.items()}
    elif fixture_id == "candidate_original_conflation":
        replacements = [
            ("changed `iter24` candidate", "original `iter24` provider logic"),
            ("clearly labeled changed candidate", "original provider logic"),
            ("changed candidates", "original provider rows"),
            ("changed candidate", "original provider logic"),
            ("changed-candidate", "original-provider"),
        ]
        texts = {rel_path: replace_all(text, replacements) for rel_path, text in texts.items()}
    elif fixture_id == "forbidden_benchmark_or_runtime_claim":
        texts["README.md"] += "\nCodeClash leaderboard result is claimed.\n"
        texts["docs/REPORT.md"] += "\nSWE-bench result is claimed.\n"
        texts["docs/NEXT_PHASE.md"] += "\nProduction result is claimed.\n"
        texts["CONTINUITY.md"] += "\nLive-domain result is claimed.\n"
    else:
        raise SelfCoveragePublicSyncNegativeGuardError(f"unknown fixture: {fixture_id}")
    return texts


def write_fixture_files(fixture_id: str, texts: dict[str, str]) -> dict[str, str]:
    paths = {}
    for rel_path, text in texts.items():
        fixture_path = FIXTURES / fixture_id / f"{rel_path.replace('/', '__')}.txt"
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        fixture_path.write_text(text, encoding="utf-8")
        paths[rel_path] = str(fixture_path.relative_to(ROOT))
    return paths


def evaluate_fixture(
    manifest: dict[str, Any],
    self_coverage: dict[str, Any],
    negative_report: dict[str, Any],
    base_texts: dict[str, str],
    fixture_id: str,
    expected_failed_checks: list[str],
) -> dict[str, Any]:
    texts = fixture_texts(base_texts, fixture_id)
    paths = write_fixture_files(fixture_id, texts)
    checks = run_guard(manifest, self_coverage, negative_report, texts)
    failed = [check for check in checks if check["status"] != "pass"]
    failed_ids = [check["check_id"] for check in failed]
    expected_detected = all(check_id in failed_ids for check_id in expected_failed_checks)
    return {
        "fixture_id": fixture_id,
        "status": "pass" if failed and expected_detected else "fail",
        "expected_failed_checks": expected_failed_checks,
        "observed_failed_checks": failed_ids,
        "malformation_detected": bool(failed),
        "expected_detection_observed": expected_detected,
        "fixture_paths": paths,
        "checks": checks,
    }


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter38-release-manifest-self-coverage-public-sync-negative-guard-{status}",
        "task_id": "telos:iter38_release_manifest_self_coverage_public_sync_negative_guard@iter37_public_sync",
        "agent_id": "codex-local-release-manifest-self-coverage-public-sync-negative-fixtures",
        "benchmark_id": "telos_codeclash_battlesnake_semantic_slice",
        "status": status,
        "stated_goal": (
            "Prove the self-coverage public-sync guard catches malformed public prose."
        ),
        "acceptance_criteria": [
            "No provider, API, GPU, or cloud spend occurs.",
            "The real public prose still passes the self-coverage public-sync guard.",
            "Every malformed public-prose fixture fails for the expected reason.",
            "Fixture files remain separate from real public prose.",
            "Command output and proof artifacts are committed.",
            "No leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": (
                    "experiments/iter38_release_manifest_self_coverage_public_sync_negative_guard"
                    "/proof/negative_guard_report.json"
                ),
                "notes": "Real public prose plus malformed self-coverage public-prose fixtures.",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": (
                    "experiments/iter38_release_manifest_self_coverage_public_sync_negative_guard"
                    "/proof/fixtures/"
                ),
                "notes": "Generated fixture prose; real public prose is not mutated.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": (
                    "experiments/iter38_release_manifest_self_coverage_public_sync_negative_guard"
                    "/proof/review.md"
                ),
                "notes": "Review records fixture coverage and claim boundary.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if the iter37 public-sync report cannot be loaded.",
            "The result must fail if real public prose no longer passes.",
            "The result must fail if any malformed public-prose fixture passes.",
            "The result must fail if fixture prose mutates real public prose.",
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

    manifest = read_json(MANIFEST)
    self_coverage = read_json(SELF_COVERAGE)
    negative_report = read_json(NEGATIVE_REPORT)
    iter37_report = read_json(SOURCE_ITER37_REPORT)
    base_texts = load_public_texts()
    real_checks = run_guard(manifest, self_coverage, negative_report, base_texts)
    real_failures = [check for check in real_checks if check["status"] != "pass"]
    fixtures = [
        evaluate_fixture(
            manifest,
            self_coverage,
            negative_report,
            base_texts,
            "missing_release_manifest_reference",
            [
                "required_snippets:README.md",
                "required_snippets:docs/REPORT.md",
                "required_snippets:docs/NEXT_PHASE.md",
                "required_snippets:CONTINUITY.md",
                "manifest_referenced_everywhere",
            ],
        ),
        evaluate_fixture(
            manifest,
            self_coverage,
            negative_report,
            base_texts,
            "missing_self_coverage_report_reference",
            [
                "required_snippets:README.md",
                "required_snippets:docs/REPORT.md",
                "required_snippets:docs/NEXT_PHASE.md",
                "required_snippets:CONTINUITY.md",
                "self_coverage_referenced_everywhere",
            ],
        ),
        evaluate_fixture(
            manifest,
            self_coverage,
            negative_report,
            base_texts,
            "missing_self_coverage_negative_guard_reference",
            [
                "required_snippets:README.md",
                "required_snippets:docs/REPORT.md",
                "required_snippets:docs/NEXT_PHASE.md",
                "required_snippets:CONTINUITY.md",
                "negative_report_referenced_everywhere",
            ],
        ),
        evaluate_fixture(
            manifest,
            self_coverage,
            negative_report,
            base_texts,
            "hidden_failed_nulls",
            ["required_snippets:docs/NEXT_PHASE.md", "failed_null_rows_visible"],
        ),
        evaluate_fixture(
            manifest,
            self_coverage,
            negative_report,
            base_texts,
            "candidate_original_conflation",
            ["changed_candidate_boundary_visible"],
        ),
        evaluate_fixture(
            manifest,
            self_coverage,
            negative_report,
            base_texts,
            "forbidden_benchmark_or_runtime_claim",
            [
                "forbidden_claims:README.md",
                "forbidden_claims:docs/REPORT.md",
                "forbidden_claims:docs/NEXT_PHASE.md",
                "forbidden_claims:CONTINUITY.md",
            ],
        ),
    ]
    failed_fixtures = [fixture for fixture in fixtures if fixture["status"] != "pass"]
    source_guard_ok = (
        iter37_report.get("status") == "pass"
        and iter37_report.get("failed_check_count") == 0
        and iter37_report.get("self_coverage_referenced") is True
        and iter37_report.get("negative_guard_referenced") is True
    )
    status = "pass" if not real_failures and not failed_fixtures and source_guard_ok else "fail"

    report = {
        "schema_version": "telos.release_manifest_self_coverage_public_sync_negative_guard.report.v1",
        "status": status,
        "source_iter37_report_path": str(SOURCE_ITER37_REPORT.relative_to(ROOT)),
        "source_iter37_report_sha256": sha256_file(SOURCE_ITER37_REPORT),
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
        "real_public_prose_passed": not real_failures,
        "real_failed_check_ids": [check["check_id"] for check in real_failures],
        "fixture_count": len(fixtures),
        "fixtures_failed_as_expected": len(failed_fixtures) == 0,
        "failed_fixture_ids": [fixture["fixture_id"] for fixture in failed_fixtures],
        "source_iter37_status": iter37_report.get("status"),
        "source_iter37_clean_pass": iter37_report.get("failed_check_count") == 0,
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "model_superiority_claimed": False,
        "fixtures": fixtures,
    }
    write_json(PROOF / "negative_guard_report.json", report)

    output_lines = [
        f"release manifest self coverage public sync negative guard: {status}",
        f"source_iter37={SOURCE_ITER37_REPORT.relative_to(ROOT)}",
        "provider_api_calls=0",
        "cloud_or_gpu_used=false",
        f"real_public_prose_passed={str(not real_failures).lower()}",
        f"fixtures={len(fixtures)} failed_as_expected={len(fixtures) - len(failed_fixtures)}",
        f"failed_fixture_ids={','.join(report['failed_fixture_ids'])}",
    ]
    for fixture in fixtures:
        output_lines.append(
            f"{fixture['fixture_id']}: {'pass' if fixture['status'] == 'pass' else 'fail'} "
            f"observed={','.join(fixture['observed_failed_checks'])}"
        )
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 38 Review

The negative guard kept the real public prose passing and evaluated six generated malformed
self-coverage public-prose fixtures. The fixtures cover missing release-manifest references,
missing self-coverage report references, missing self-coverage negative-guard references, hidden
failed/null gates, changed-candidate/original-provider conflation, and forbidden benchmark/runtime
claims.

Fixture files are committed under proof artifacts and do not mutate README, report, next-phase, or
continuity prose. This strengthens the self-coverage public-sync guard without adding behavior,
benchmark, production, or provider-model evidence.

No provider call, API call, GPU, cloud runner, production deployment, live-domain check, leaderboard
run, or SWE-bench run occurred in this gate.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    run_summary = {
        "schema_version": "telos.release_manifest_self_coverage_public_sync_negative_guard.summary.v1",
        "status": status,
        "experiment_id": "iter38_release_manifest_self_coverage_public_sync_negative_guard",
        "source_experiment": "iter37_release_manifest_self_coverage_public_sync_guard",
        "source_iter37_report_path": str(SOURCE_ITER37_REPORT.relative_to(ROOT)),
        "source_iter37_report_sha256": sha256_file(SOURCE_ITER37_REPORT),
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
        "real_public_prose_passed": not real_failures,
        "fixture_count": len(fixtures),
        "fixtures_failed_as_expected": len(failed_fixtures) == 0,
        "failed_fixture_ids": report["failed_fixture_ids"],
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "model_superiority_claimed": False,
        "clean_pass": status == "pass",
        "next_gate": "experiments/iter39_public_task_protocol_effect_slice/HYPOTHESIS.md",
        "artifact_hashes": {
            "command_output.txt": sha256_file(PROOF / "command_output.txt"),
            "negative_guard_report.json": sha256_file(PROOF / "negative_guard_report.json"),
            "review.md": sha256_file(PROOF / "review.md"),
        },
    }
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter38_release_manifest_self_coverage_public_sync_negative_guard",
        "status": "null" if status == "fail" else status,
        "insight": (
            "The self-coverage public-sync guard catches malformed prose that hides the release "
            "manifest, hides self-coverage evidence, hides failed/null gates, conflates changed "
            "candidate logic with original provider logic, or adds forbidden claims."
        ),
        "next_action": (
            "pre-register a public-task protocol-effect slice so baseline and Telos-enforced "
            "completion evidence can be compared on frozen external tasks"
        ),
        "result_path": (
            "experiments/iter38_release_manifest_self_coverage_public_sync_negative_guard/RESULT.md"
        ),
        "evidence_paths": [
            "experiments/iter38_release_manifest_self_coverage_public_sync_negative_guard/proof/run_summary.json",
            "experiments/iter38_release_manifest_self_coverage_public_sync_negative_guard/proof/negative_guard_report.json",
            "experiments/iter38_release_manifest_self_coverage_public_sync_negative_guard/proof/command_output.txt",
            "experiments/iter38_release_manifest_self_coverage_public_sync_negative_guard/proof/review.md",
            "experiments/iter38_release_manifest_self_coverage_public_sync_negative_guard/proof/valid/receipt_release_manifest_self_coverage_public_sync_negative_guard.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(
        VALID / "receipt_release_manifest_self_coverage_public_sync_negative_guard.json",
        build_receipt(status),
    )

    print("\n".join(output_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
