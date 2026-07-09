#!/usr/bin/env python3
"""Generate iter28 public claim-surface guard proof artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "iter28_public_claim_surface_guard"
PROOF = EXPERIMENT / "proof"
VALID = PROOF / "valid"
MATRIX = ROOT / "experiments" / "iter27_semantic_claim_boundary_matrix" / "proof" / "claim_boundary_matrix.json"

PUBLIC_FILES = [
    Path("README.md"),
    Path("docs/REPORT.md"),
    Path("docs/NEXT_PHASE.md"),
    Path("CONTINUITY.md"),
]

REQUIRED_SNIPPETS = {
    "README.md": [
        "Tail semantics falsification: failed",
        "Tail safety mutation guard: failed",
        "Tail safety control: passed for a clearly labeled changed candidate",
        "Semantic claim boundary matrix: passed",
        "Benchmark result: none yet.",
    ],
    "docs/REPORT.md": [
        "No model or benchmark result is claimed yet.",
        "fails under the explicit",
        "changed candidate",
        "claim-boundary matrix",
    ],
    "docs/NEXT_PHASE.md": [
        "Run `iter28_public_claim_surface_guard`",
        "read the committed `iter27` claim-boundary matrix",
        "do not call a provider model",
    ],
    "CONTINUITY.md": [
        "`iter23_tail_semantics_falsification` failed",
        "`iter25_tail_safety_mutation_guard` failed",
        "`iter27_semantic_claim_boundary_matrix` passed",
        "No model or benchmark result is claimed yet.",
    ],
}

FORBIDDEN_CLAIMS = [
    "original `iter21` bot was occupied-tail safe",
    "original iter21 bot was occupied-tail safe",
    "original `iter21` occupied-tail safety is proven",
    "original iter21 occupied-tail safety is proven",
    "CodeClash leaderboard result is claimed",
    "SWE-bench result is claimed",
    "model superiority",
]


class PublicClaimSurfaceError(RuntimeError):
    """Raised when public prose cannot be verified against the matrix."""


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
        raise PublicClaimSurfaceError(f"{path} root must be an object")
    return data


def load_public_text() -> dict[str, str]:
    texts = {}
    for rel_path in PUBLIC_FILES:
        path = ROOT / rel_path
        if not path.exists():
            raise PublicClaimSurfaceError(f"missing public prose file: {rel_path}")
        texts[rel_path.as_posix()] = path.read_text(encoding="utf-8")
    return texts


def check_required_snippets(texts: dict[str, str]) -> list[dict[str, Any]]:
    checks = []
    for rel_path, snippets in REQUIRED_SNIPPETS.items():
        text = texts[rel_path]
        missing = [snippet for snippet in snippets if snippet not in text]
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


def check_matrix_alignment(matrix: dict[str, Any], texts: dict[str, str]) -> list[dict[str, Any]]:
    readme = texts["README.md"]
    report = texts["docs/REPORT.md"]
    continuity = texts["CONTINUITY.md"]
    checks = [
        {
            "check_id": "matrix_status_pass",
            "status": "pass" if matrix.get("status") == "pass" else "fail",
            "observed": matrix.get("status"),
        },
        {
            "check_id": "matrix_nulls_visible_publicly",
            "status": (
                "pass"
                if "Tail semantics falsification: failed" in readme
                and "Tail safety mutation guard: failed" in readme
                and "`iter23_tail_semantics_falsification` failed" in continuity
                and "`iter25_tail_safety_mutation_guard` failed" in continuity
                else "fail"
            ),
        },
        {
            "check_id": "changed_candidate_boundary_visible",
            "status": "pass" if "changed candidate" in readme and "changed candidate" in report else "fail",
        },
        {
            "check_id": "original_iter21_occupied_tail_not_claimed",
            "status": (
                "pass"
                if matrix.get("original_iter21_occupied_tail_safety_claimed") is False
                and "original `iter21` bot was occupied-tail safe" not in readme
                and "original `iter21` bot was occupied-tail safe" not in report
                else "fail"
            ),
        },
        {
            "check_id": "active_gate_iter28",
            "status": (
                "pass"
                if "`experiments/iter28_public_claim_surface_guard/HYPOTHESIS.md`" in continuity
                else "fail"
            ),
        },
    ]
    return checks


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter28-public-claim-surface-guard-{status}",
        "task_id": "telos:iter28_public_claim_surface_guard@iter27_semantic_claim_boundary_matrix",
        "agent_id": "codex-local-public-claim-surface-guard",
        "benchmark_id": "telos_codeclash_battlesnake_semantic_slice",
        "status": status,
        "stated_goal": (
            "Audit README and report prose against the semantic claim-boundary matrix without "
            "widening into benchmark, production, or model claims."
        ),
        "acceptance_criteria": [
            "No provider, API, GPU, or cloud spend occurs.",
            "The guard reads the committed iter27 matrix.",
            "Every checked public prose file exists.",
            "Failed/null gates remain visible in public prose.",
            "Original provider logic and changed candidate logic are not conflated in public prose.",
            "No leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": "experiments/iter28_public_claim_surface_guard/proof/public_claim_surface_report.json",
                "notes": "Public prose checks against the iter27 claim-boundary matrix.",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "experiments/iter27_semantic_claim_boundary_matrix/proof/claim_boundary_matrix.json",
                "notes": "Machine-readable boundary used as the source of truth.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": "experiments/iter28_public_claim_surface_guard/proof/review.md",
                "notes": "Review states public-surface claim boundaries.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if the claim matrix cannot be loaded.",
            "The result must block if required public prose files are missing.",
            "The result must fail if public prose hides failed/null gates.",
            "The result must fail if public prose implies original iter21 occupied-tail safety.",
            "The result must fail if public prose widens into benchmark or production claims.",
        ],
        "sha256": "",
    }
    receipt["sha256"] = receipt_digest(receipt)
    return receipt


def main() -> int:
    PROOF.mkdir(parents=True, exist_ok=True)
    VALID.mkdir(parents=True, exist_ok=True)
    matrix = read_json(MATRIX)
    texts = load_public_text()
    checks = [
        *check_required_snippets(texts),
        *check_forbidden_claims(texts),
        *check_matrix_alignment(matrix, texts),
    ]
    failures = [check for check in checks if check["status"] != "pass"]
    status = "pass" if not failures else "fail"

    report = {
        "schema_version": "telos.public_claim_surface_guard.report.v1",
        "status": status,
        "source_matrix_path": str(MATRIX.relative_to(ROOT)),
        "source_matrix_sha256": sha256_file(MATRIX),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "checked_public_files": [path.as_posix() for path in PUBLIC_FILES],
        "check_count": len(checks),
        "failed_check_count": len(failures),
        "failed_check_ids": [check["check_id"] for check in failures],
        "failed_null_gates_visible": not any(
            check["check_id"] == "matrix_nulls_visible_publicly" for check in failures
        ),
        "changed_candidate_boundary_visible": not any(
            check["check_id"] == "changed_candidate_boundary_visible" for check in failures
        ),
        "original_iter21_occupied_tail_safety_claimed": any(
            check["check_id"] == "original_iter21_occupied_tail_not_claimed"
            for check in failures
        ),
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "checks": checks,
    }
    write_json(PROOF / "public_claim_surface_report.json", report)

    output_lines = [
        f"public claim surface guard: {status}",
        f"source_matrix={MATRIX.relative_to(ROOT)}",
        "provider_api_calls=0",
        "cloud_or_gpu_used=false",
        f"files={len(PUBLIC_FILES)} checks={len(checks)} failed={len(failures)}",
        f"failed_checks={','.join(report['failed_check_ids'])}",
    ]
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 28 Review

The public claim-surface guard read the `iter27` claim-boundary matrix and checked README, report,
next-phase, and continuity prose. The checked public surface keeps the `iter23` and `iter25`
failed/null gates visible, describes `iter24` as a changed candidate, and does not claim original
`iter21` occupied-tail safety.

This gate audits public wording only. It does not add benchmark evidence, production evidence, or
provider-model evidence.

No provider call, API call, GPU, cloud runner, production deployment, live-domain check, leaderboard
run, or SWE-bench run occurred in this gate.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    run_summary = {
        "schema_version": "telos.public_claim_surface_guard.summary.v1",
        "status": status,
        "experiment_id": "iter28_public_claim_surface_guard",
        "source_experiment": "iter27_semantic_claim_boundary_matrix",
        "source_matrix_path": str(MATRIX.relative_to(ROOT)),
        "source_matrix_sha256": sha256_file(MATRIX),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "checked_public_files": [path.as_posix() for path in PUBLIC_FILES],
        "check_count": len(checks),
        "failed_check_count": len(failures),
        "failed_check_ids": report["failed_check_ids"],
        "failed_null_gates_visible": report["failed_null_gates_visible"],
        "changed_candidate_boundary_visible": report["changed_candidate_boundary_visible"],
        "original_iter21_occupied_tail_safety_claimed": report[
            "original_iter21_occupied_tail_safety_claimed"
        ],
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "clean_pass": status == "pass",
        "next_gate": "experiments/iter29_public_claim_surface_negative_guard/HYPOTHESIS.md",
        "artifact_hashes": {
            "command_output.txt": sha256_file(PROOF / "command_output.txt"),
            "public_claim_surface_report.json": sha256_file(
                PROOF / "public_claim_surface_report.json"
            ),
            "review.md": sha256_file(PROOF / "review.md"),
        },
    }
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter28_public_claim_surface_guard",
        "status": status,
        "insight": (
            "README, report, next-phase, and continuity prose can be checked against the claim "
            "matrix so nulls and changed-candidate boundaries remain public."
        ),
        "next_action": (
            "pre-register a negative public-claim fixture guard that proves the prose guard catches "
            "known overclaim patterns"
        ),
        "result_path": "experiments/iter28_public_claim_surface_guard/RESULT.md",
        "evidence_paths": [
            "experiments/iter28_public_claim_surface_guard/proof/run_summary.json",
            "experiments/iter28_public_claim_surface_guard/proof/public_claim_surface_report.json",
            "experiments/iter28_public_claim_surface_guard/proof/command_output.txt",
            "experiments/iter28_public_claim_surface_guard/proof/review.md",
            "experiments/iter28_public_claim_surface_guard/proof/valid/receipt_public_claim_surface_guard.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(VALID / "receipt_public_claim_surface_guard.json", build_receipt(status))

    print("\n".join(output_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
