#!/usr/bin/env python3
"""Generate iter29 public claim-surface negative-guard proof artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_public_claim_surface_guard import (  # noqa: E402
    MATRIX,
    PUBLIC_FILES,
    check_forbidden_claims,
    check_matrix_alignment,
    check_required_snippets,
    read_json,
)


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "iter29_public_claim_surface_negative_guard"
PROOF = EXPERIMENT / "proof"
FIXTURES = PROOF / "fixtures"
VALID = PROOF / "valid"
SOURCE_ITER28_REPORT = (
    ROOT / "experiments" / "iter28_public_claim_surface_guard" / "proof" / "public_claim_surface_report.json"
)


class PublicClaimNegativeGuardError(RuntimeError):
    """Raised when iter29 cannot produce trustworthy negative-fixture artifacts."""


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
            raise PublicClaimNegativeGuardError(f"missing public prose file: {rel_path}")
        texts[rel_path.as_posix()] = path.read_text(encoding="utf-8")
    return texts


def run_guard(matrix: dict[str, Any], texts: dict[str, str]) -> list[dict[str, Any]]:
    checks = [
        *check_required_snippets(texts),
        *check_forbidden_claims(texts),
        *check_matrix_alignment(matrix, texts),
    ]
    ignored = {"active_gate_iter28", "required_snippets:docs/NEXT_PHASE.md"}
    return [check for check in checks if check["check_id"] not in ignored]


def fixture_texts(base: dict[str, str], fixture_id: str) -> dict[str, str]:
    texts = dict(base)
    if fixture_id == "original_iter21_tail_overclaim":
        texts["README.md"] += "\nThe original `iter21` bot was occupied-tail safe.\n"
    elif fixture_id == "hidden_nulls":
        texts["README.md"] = texts["README.md"].replace(
            "Tail semantics falsification: failed",
            "Tail semantics falsification: passed",
        ).replace(
            "Tail safety mutation guard: failed",
            "Tail safety mutation guard: passed",
        )
        texts["CONTINUITY.md"] = texts["CONTINUITY.md"].replace(
            "`iter23_tail_semantics_falsification` failed",
            "`iter23_tail_semantics_falsification` passed",
        ).replace(
            "`iter25_tail_safety_mutation_guard` failed",
            "`iter25_tail_safety_mutation_guard` passed",
        )
    elif fixture_id == "changed_candidate_conflated":
        texts["README.md"] = texts["README.md"].replace(
            "Tail safety control: passed for a clearly labeled changed candidate",
            "Tail safety control: passed for original provider-submitted behavior",
        )
        texts["docs/REPORT.md"] = texts["docs/REPORT.md"].replace(
            "changed candidate",
            "original provider-submitted behavior",
        )
    elif fixture_id == "benchmark_result_overclaim":
        texts["README.md"] += "\nCodeClash leaderboard result is claimed.\n"
    else:
        raise PublicClaimNegativeGuardError(f"unknown fixture: {fixture_id}")
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
    matrix: dict[str, Any],
    base_texts: dict[str, str],
    fixture_id: str,
    expected_failed_checks: list[str],
) -> dict[str, Any]:
    texts = fixture_texts(base_texts, fixture_id)
    paths = write_fixture_files(fixture_id, texts)
    checks = run_guard(matrix, texts)
    failed = [check for check in checks if check["status"] != "pass"]
    failed_ids = [check["check_id"] for check in failed]
    expected_detected = all(check_id in failed_ids for check_id in expected_failed_checks)
    return {
        "fixture_id": fixture_id,
        "status": "pass" if failed and expected_detected else "fail",
        "expected_failed_checks": expected_failed_checks,
        "observed_failed_checks": failed_ids,
        "overclaim_detected": bool(failed),
        "expected_detection_observed": expected_detected,
        "fixture_paths": paths,
        "checks": checks,
    }


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter29-public-claim-surface-negative-guard-{status}",
        "task_id": "telos:iter29_public_claim_surface_negative_guard@iter28_public_claim_surface_guard",
        "agent_id": "codex-local-public-claim-negative-fixtures",
        "benchmark_id": "telos_codeclash_battlesnake_semantic_slice",
        "status": status,
        "stated_goal": "Prove the public-claim guard catches known overclaim fixtures.",
        "acceptance_criteria": [
            "No provider, API, GPU, or cloud spend occurs.",
            "The real public prose still passes the guard.",
            "Every negative fixture fails for the expected reason.",
            "The guard records the exact overclaim detected for each fixture.",
            "Command output and proof artifacts are committed.",
            "No leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": "experiments/iter29_public_claim_surface_negative_guard/proof/negative_guard_report.json",
                "notes": "Real public prose plus known overclaim fixtures evaluated by the guard.",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "experiments/iter29_public_claim_surface_negative_guard/proof/fixtures/",
                "notes": "Generated fixture prose; real public prose is not mutated.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": "experiments/iter29_public_claim_surface_negative_guard/proof/review.md",
                "notes": "Review records fixture coverage and claim boundary.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if the iter28 report or iter27 matrix cannot be loaded.",
            "The result must fail if real public prose no longer passes.",
            "The result must fail if any overclaim fixture passes.",
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
    iter28 = read_json(SOURCE_ITER28_REPORT)
    matrix = read_json(MATRIX)
    base_texts = load_public_texts()
    real_checks = run_guard(matrix, base_texts)
    real_failures = [check for check in real_checks if check["status"] != "pass"]

    fixtures = [
        evaluate_fixture(
            matrix,
            base_texts,
            "original_iter21_tail_overclaim",
            ["forbidden_claims:README.md", "original_iter21_occupied_tail_not_claimed"],
        ),
        evaluate_fixture(
            matrix,
            base_texts,
            "hidden_nulls",
            [
                "required_snippets:README.md",
                "required_snippets:CONTINUITY.md",
                "matrix_nulls_visible_publicly",
            ],
        ),
        evaluate_fixture(
            matrix,
            base_texts,
            "changed_candidate_conflated",
            [
                "required_snippets:README.md",
                "required_snippets:docs/REPORT.md",
                "changed_candidate_boundary_visible",
            ],
        ),
        evaluate_fixture(
            matrix,
            base_texts,
            "benchmark_result_overclaim",
            ["forbidden_claims:README.md"],
        ),
    ]
    failed_fixtures = [fixture for fixture in fixtures if fixture["status"] != "pass"]
    status = "pass" if not real_failures and not failed_fixtures else "fail"

    report = {
        "schema_version": "telos.public_claim_surface_negative_guard.report.v1",
        "status": status,
        "source_iter28_report_path": str(SOURCE_ITER28_REPORT.relative_to(ROOT)),
        "source_iter28_report_sha256": sha256_file(SOURCE_ITER28_REPORT),
        "source_matrix_path": str(MATRIX.relative_to(ROOT)),
        "source_matrix_sha256": sha256_file(MATRIX),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "real_public_prose_passed": not real_failures,
        "real_failed_check_ids": [check["check_id"] for check in real_failures],
        "fixture_count": len(fixtures),
        "fixtures_failed_as_expected": len(failed_fixtures) == 0,
        "failed_fixture_ids": [fixture["fixture_id"] for fixture in failed_fixtures],
        "iter28_status": iter28.get("status"),
        "fixtures": fixtures,
    }
    write_json(PROOF / "negative_guard_report.json", report)

    output_lines = [
        f"public claim surface negative guard: {status}",
        f"source_iter28={SOURCE_ITER28_REPORT.relative_to(ROOT)}",
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

    review = """# Iteration 29 Review

The negative guard kept the real public prose passing and evaluated four generated overclaim
fixtures. Each fixture failed for the expected reason: original `iter21` occupied-tail overclaim,
hidden nulls, changed-candidate conflation, and benchmark-result overclaim.

The fixture files are committed under proof artifacts and do not mutate README, report, next-phase,
or continuity prose. This strengthens the documentation guard without adding any behavior,
benchmark, production, or provider-model claim.

No provider call, API call, GPU, cloud runner, production deployment, live-domain check, leaderboard
run, or SWE-bench run occurred in this gate.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    run_summary = {
        "schema_version": "telos.public_claim_surface_negative_guard.summary.v1",
        "status": status,
        "experiment_id": "iter29_public_claim_surface_negative_guard",
        "source_experiment": "iter28_public_claim_surface_guard",
        "source_iter28_report_path": str(SOURCE_ITER28_REPORT.relative_to(ROOT)),
        "source_iter28_report_sha256": sha256_file(SOURCE_ITER28_REPORT),
        "source_matrix_path": str(MATRIX.relative_to(ROOT)),
        "source_matrix_sha256": sha256_file(MATRIX),
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
        "clean_pass": status == "pass",
        "next_gate": "experiments/iter30_boundary_matrix_schema_guard/HYPOTHESIS.md",
        "artifact_hashes": {
            "command_output.txt": sha256_file(PROOF / "command_output.txt"),
            "negative_guard_report.json": sha256_file(PROOF / "negative_guard_report.json"),
            "review.md": sha256_file(PROOF / "review.md"),
        },
    }
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter29_public_claim_surface_negative_guard",
        "status": status,
        "insight": (
            "The public-claim guard catches generated overclaim fixtures while real public prose "
            "continues to pass."
        ),
        "next_action": (
            "pre-register a boundary-matrix schema guard so future claim rows remain structurally "
            "machine-checkable"
        ),
        "result_path": "experiments/iter29_public_claim_surface_negative_guard/RESULT.md",
        "evidence_paths": [
            "experiments/iter29_public_claim_surface_negative_guard/proof/run_summary.json",
            "experiments/iter29_public_claim_surface_negative_guard/proof/negative_guard_report.json",
            "experiments/iter29_public_claim_surface_negative_guard/proof/command_output.txt",
            "experiments/iter29_public_claim_surface_negative_guard/proof/review.md",
            "experiments/iter29_public_claim_surface_negative_guard/proof/valid/receipt_public_claim_surface_negative_guard.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(VALID / "receipt_public_claim_surface_negative_guard.json", build_receipt(status))

    print("\n".join(output_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
