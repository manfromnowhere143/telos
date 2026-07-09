#!/usr/bin/env python3
"""Generate iter30 boundary-matrix schema-guard proof artifacts."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "iter30_boundary_matrix_schema_guard"
PROOF = EXPERIMENT / "proof"
FIXTURES = PROOF / "fixtures"
VALID = PROOF / "valid"
SOURCE_MATRIX = (
    ROOT
    / "experiments"
    / "iter27_semantic_claim_boundary_matrix"
    / "proof"
    / "claim_boundary_matrix.json"
)
SOURCE_NEGATIVE_REPORT = (
    ROOT
    / "experiments"
    / "iter29_public_claim_surface_negative_guard"
    / "proof"
    / "negative_guard_report.json"
)

EXPECTED_EXPERIMENTS = [
    "iter20_behavior_semantic_verification",
    "iter21_opponent_collision_control",
    "iter22_semantic_mutation_guard",
    "iter23_tail_semantics_falsification",
    "iter24_tail_safety_control",
    "iter25_tail_safety_mutation_guard",
    "iter26_own_tail_redundancy_mutation_guard",
]
EXPECTED_FAILED_OR_NULL = [
    "iter23_original_occupied_tail_falsification",
    "iter25_tail_safety_mutation_guard_miss",
]
REQUIRED_EXCLUSIONS = {
    "no_codeclash_leaderboard_claim",
    "no_swebench_claim",
    "no_production_or_live_domain_claim",
    "no_model_superiority_claim",
    "no_provider_game_score_as_verifier_evidence",
}
ROOT_REQUIRED_FIELDS = {
    "schema_version",
    "status",
    "experiment_id",
    "provider_api_calls",
    "provider_spend_usd",
    "cloud_or_gpu_used",
    "local_cpu_only",
    "included_experiments",
    "row_count",
    "failed_or_null_claim_ids",
    "changed_candidate_claim_ids",
    "original_provider_logic_claim_ids",
    "verifier_strength_claim_ids",
    "original_iter21_occupied_tail_safety_claimed",
    "failed_null_gates_hidden",
    "provider_game_score_used_as_verifier_evidence",
    "leaderboard_or_swebench_claimed",
    "production_or_live_domain_changed",
    "rows",
}
ROW_REQUIRED_FIELDS = {
    "claim_id",
    "experiment_id",
    "subject_type",
    "subject_id",
    "status",
    "source_summary_status",
    "source_summary_clean_pass",
    "claim",
    "boundary",
    "failure_visible",
    "changed_candidate",
    "original_provider_logic",
    "verifier_strength_evidence",
    "evidence_paths",
    "does_not_claim",
}
VALID_ROOT_STATUSES = {"pass", "fail", "blocked"}
VALID_ROW_STATUSES = {"pass", "null", "blocked", "pending"}
BOOLEAN_ROOT_FIELDS = {
    "cloud_or_gpu_used",
    "local_cpu_only",
    "original_iter21_occupied_tail_safety_claimed",
    "failed_null_gates_hidden",
    "provider_game_score_used_as_verifier_evidence",
    "leaderboard_or_swebench_claimed",
    "production_or_live_domain_changed",
}
BOOLEAN_ROW_FIELDS = {
    "source_summary_clean_pass",
    "failure_visible",
    "changed_candidate",
    "original_provider_logic",
    "verifier_strength_evidence",
}


class BoundarySchemaGuardError(RuntimeError):
    """Raised when iter30 cannot produce trustworthy proof artifacts."""


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
        raise BoundarySchemaGuardError(f"{path} root must be an object")
    return data


def error(code: str, path: str, detail: str) -> dict[str, str]:
    return {"code": code, "path": path, "detail": detail}


def list_value(data: dict[str, Any], field: str, errors: list[dict[str, str]]) -> list[Any]:
    value = data.get(field)
    if not isinstance(value, list):
        errors.append(error("invalid_type", field, "expected list"))
        return []
    return value


def non_empty_strings(
    values: list[Any],
    *,
    field: str,
    errors: list[dict[str, str]],
    code: str = "invalid_type",
) -> list[str]:
    strings: list[str] = []
    for index, value in enumerate(values):
        if not isinstance(value, str) or not value:
            errors.append(error(code, f"{field}[{index}]", "expected non-empty string"))
            continue
        strings.append(value)
    return strings


def append_missing_fields(
    *,
    present: set[str],
    required: set[str],
    path: str,
    errors: list[dict[str, str]],
) -> None:
    for field in sorted(required - present):
        errors.append(error("missing_required_field", f"{path}.{field}", "field is required"))


def validate_matrix(matrix: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    append_missing_fields(
        present=set(matrix),
        required=ROOT_REQUIRED_FIELDS,
        path="$",
        errors=errors,
    )
    if errors:
        return errors

    if matrix.get("schema_version") != "telos.semantic_claim_boundary_matrix.v1":
        errors.append(
            error(
                "invalid_schema_version",
                "$.schema_version",
                "expected telos.semantic_claim_boundary_matrix.v1",
            )
        )
    if matrix.get("status") not in VALID_ROOT_STATUSES:
        errors.append(error("invalid_status", "$.status", f"invalid status {matrix.get('status')!r}"))
    if matrix.get("experiment_id") != "iter27_semantic_claim_boundary_matrix":
        errors.append(
            error(
                "invalid_experiment_id",
                "$.experiment_id",
                "expected iter27_semantic_claim_boundary_matrix",
            )
        )
    if matrix.get("provider_api_calls") != 0:
        errors.append(error("provider_side_effect", "$.provider_api_calls", "expected 0"))
    if matrix.get("provider_spend_usd") != 0.0:
        errors.append(error("provider_side_effect", "$.provider_spend_usd", "expected 0.0"))
    for field in BOOLEAN_ROOT_FIELDS:
        if not isinstance(matrix.get(field), bool):
            errors.append(error("invalid_type", f"$.{field}", "expected bool"))

    for field in [
        "cloud_or_gpu_used",
        "original_iter21_occupied_tail_safety_claimed",
        "failed_null_gates_hidden",
        "provider_game_score_used_as_verifier_evidence",
        "leaderboard_or_swebench_claimed",
        "production_or_live_domain_changed",
    ]:
        if matrix.get(field) is not False:
            code = "hidden_failed_null_rows" if field == "failed_null_gates_hidden" else "overclaim"
            errors.append(error(code, f"$.{field}", "expected false"))
    if matrix.get("local_cpu_only") is not True:
        errors.append(error("provider_side_effect", "$.local_cpu_only", "expected true"))

    included = non_empty_strings(
        list_value(matrix, "included_experiments", errors),
        field="included_experiments",
        errors=errors,
    )
    if included != EXPECTED_EXPERIMENTS:
        errors.append(
            error(
                "experiment_coverage_mismatch",
                "$.included_experiments",
                f"expected {EXPECTED_EXPERIMENTS!r}",
            )
        )

    rows_raw = list_value(matrix, "rows", errors)
    if matrix.get("row_count") != len(rows_raw):
        errors.append(error("row_count_mismatch", "$.row_count", "does not match rows length"))
    if not rows_raw:
        errors.append(error("missing_rows", "$.rows", "matrix must contain rows"))
        return errors

    row_ids: list[str] = []
    row_experiments: list[str] = []
    failed_or_null: list[str] = []
    changed_candidate: list[str] = []
    original_provider_logic: list[str] = []
    verifier_strength: list[str] = []

    for row_index, row in enumerate(rows_raw):
        row_path = f"$.rows[{row_index}]"
        if not isinstance(row, dict):
            errors.append(error("invalid_type", row_path, "expected object"))
            continue
        append_missing_fields(
            present=set(row),
            required=ROW_REQUIRED_FIELDS,
            path=row_path,
            errors=errors,
        )
        if ROW_REQUIRED_FIELDS - set(row):
            continue

        claim_id = row.get("claim_id")
        if not isinstance(claim_id, str) or not claim_id:
            errors.append(error("invalid_type", f"{row_path}.claim_id", "expected string"))
            claim_id = f"<invalid:{row_index}>"
        else:
            row_ids.append(claim_id)

        for field in ["experiment_id", "subject_type", "subject_id", "claim", "boundary"]:
            if not isinstance(row.get(field), str) or not row.get(field):
                errors.append(error("invalid_type", f"{row_path}.{field}", "expected string"))
        if isinstance(row.get("experiment_id"), str):
            row_experiments.append(row["experiment_id"])

        if row.get("status") not in VALID_ROW_STATUSES:
            errors.append(
                error("invalid_status", f"{row_path}.status", f"invalid status {row.get('status')!r}")
            )
        for field in BOOLEAN_ROW_FIELDS:
            if not isinstance(row.get(field), bool):
                errors.append(error("invalid_type", f"{row_path}.{field}", "expected bool"))

        paths = non_empty_strings(
            list_value(row, "evidence_paths", errors),
            field=f"rows[{row_index}].evidence_paths",
            errors=errors,
        )
        if not paths:
            errors.append(error("missing_evidence_path", f"{row_path}.evidence_paths", "empty list"))
        for evidence_path in paths:
            if not (ROOT / evidence_path).exists():
                errors.append(
                    error(
                        "missing_evidence_path",
                        f"{row_path}.evidence_paths",
                        f"missing {evidence_path}",
                    )
                )

        exclusions = set(
            non_empty_strings(
                list_value(row, "does_not_claim", errors),
                field=f"rows[{row_index}].does_not_claim",
                errors=errors,
            )
        )
        missing_exclusions = REQUIRED_EXCLUSIONS - exclusions
        if missing_exclusions:
            errors.append(
                error(
                    "missing_required_exclusion",
                    f"{row_path}.does_not_claim",
                    f"missing {sorted(missing_exclusions)}",
                )
            )

        if row.get("original_provider_logic") is True and row.get("changed_candidate") is True:
            errors.append(
                error(
                    "original_candidate_conflation",
                    row_path,
                    "row cannot be both original provider logic and changed candidate",
                )
            )
        if row.get("changed_candidate") is True:
            changed_candidate.append(str(claim_id))
            if row.get("subject_type") != "changed_candidate":
                errors.append(
                    error(
                        "original_candidate_conflation",
                        f"{row_path}.subject_type",
                        "changed candidate row must be labeled changed_candidate",
                    )
                )
        if row.get("original_provider_logic") is True:
            original_provider_logic.append(str(claim_id))
            if row.get("subject_type") != "reconstructed_original_provider_logic":
                errors.append(
                    error(
                        "original_candidate_conflation",
                        f"{row_path}.subject_type",
                        "original row must be labeled reconstructed_original_provider_logic",
                    )
                )
        if row.get("verifier_strength_evidence") is True:
            verifier_strength.append(str(claim_id))
        if row.get("status") in {"null", "blocked"}:
            failed_or_null.append(str(claim_id))
            if row.get("failure_visible") is not True:
                errors.append(
                    error(
                        "hidden_failed_null_rows",
                        f"{row_path}.failure_visible",
                        "failed/null row must remain visible",
                    )
                )

    duplicates = sorted({claim_id for claim_id in row_ids if row_ids.count(claim_id) > 1})
    if duplicates:
        errors.append(error("duplicate_claim_id", "$.rows", f"duplicates {duplicates}"))
    if sorted(row_experiments) != sorted(EXPECTED_EXPERIMENTS):
        errors.append(
            error(
                "experiment_coverage_mismatch",
                "$.rows[*].experiment_id",
                "rows do not cover expected experiments exactly",
            )
        )

    expected_lists = {
        "failed_or_null_claim_ids": failed_or_null,
        "changed_candidate_claim_ids": changed_candidate,
        "original_provider_logic_claim_ids": original_provider_logic,
        "verifier_strength_claim_ids": verifier_strength,
    }
    for field, expected in expected_lists.items():
        observed = non_empty_strings(list_value(matrix, field, errors), field=field, errors=errors)
        if observed != expected:
            code = "hidden_failed_null_rows" if field == "failed_or_null_claim_ids" else "index_mismatch"
            errors.append(
                error(
                    code,
                    f"$.{field}",
                    f"expected row-derived list {expected!r}, got {observed!r}",
                )
            )

    for claim_id in EXPECTED_FAILED_OR_NULL:
        if claim_id not in failed_or_null:
            errors.append(
                error(
                    "hidden_failed_null_rows",
                    "$.rows",
                    f"required failed/null row not visible: {claim_id}",
                )
            )
    return errors


def schema_manifest() -> dict[str, Any]:
    return {
        "schema_version": "telos.boundary_matrix_schema_guard.schema.v1",
        "validated_schema": "telos.semantic_claim_boundary_matrix.v1",
        "validator": "scripts/verify_boundary_matrix_schema_guard.py",
        "root_required_fields": sorted(ROOT_REQUIRED_FIELDS),
        "row_required_fields": sorted(ROW_REQUIRED_FIELDS),
        "valid_root_statuses": sorted(VALID_ROOT_STATUSES),
        "valid_row_statuses": sorted(VALID_ROW_STATUSES),
        "required_exclusions": sorted(REQUIRED_EXCLUSIONS),
        "required_invariants": [
            "row_count_equals_rows_length",
            "included_experiments_exactly_iter20_through_iter26",
            "evidence_paths_exist",
            "original_provider_logic_and_changed_candidate_are_disjoint",
            "failed_or_null_rows_are_listed_and_failure_visible",
            "original_iter21_occupied_tail_safety_claimed_is_false",
            "failed_null_gates_hidden_is_false",
            "no_leaderboard_swebench_production_live_domain_model_superiority_claim",
            "no_provider_game_score_used_as_verifier_evidence",
        ],
    }


def write_fixture(fixture_id: str, matrix: dict[str, Any]) -> str:
    path = FIXTURES / f"{fixture_id}.json"
    write_json(path, matrix)
    return str(path.relative_to(ROOT))


def fixture_matrix(source: dict[str, Any], fixture_id: str) -> dict[str, Any]:
    matrix = copy.deepcopy(source)
    rows = matrix["rows"]
    if fixture_id == "missing_evidence_path":
        rows[0]["evidence_paths"][0] = "experiments/missing/proof/run_summary.json"
    elif fixture_id == "invalid_status":
        rows[0]["status"] = "clean_win"
    elif fixture_id == "original_candidate_conflation":
        rows[4]["original_provider_logic"] = True
    elif fixture_id == "missing_required_exclusion":
        rows[0]["does_not_claim"] = [
            item
            for item in rows[0]["does_not_claim"]
            if item != "no_model_superiority_claim"
        ]
    elif fixture_id == "hidden_failed_null_rows":
        matrix["failed_or_null_claim_ids"] = []
        matrix["failed_null_gates_hidden"] = True
        for row in rows:
            if row["claim_id"] in EXPECTED_FAILED_OR_NULL:
                row["failure_visible"] = False
    else:
        raise BoundarySchemaGuardError(f"unknown fixture: {fixture_id}")
    return matrix


def evaluate_fixture(
    source_matrix: dict[str, Any],
    fixture_id: str,
    expected_error_codes: list[str],
) -> dict[str, Any]:
    matrix = fixture_matrix(source_matrix, fixture_id)
    fixture_path = write_fixture(fixture_id, matrix)
    errors = validate_matrix(matrix)
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


def receipt_digest(data: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in data.items() if key != "sha256"}
    return sha256_bytes(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def build_receipt(status: str) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"iter30-boundary-matrix-schema-guard-{status}",
        "task_id": "telos:iter30_boundary_matrix_schema_guard@iter27_claim_boundary_matrix",
        "agent_id": "codex-local-boundary-matrix-schema-guard",
        "benchmark_id": "telos_codeclash_battlesnake_semantic_slice",
        "status": status,
        "stated_goal": (
            "Validate the claim-boundary matrix shape and prove malformed matrix fixtures fail."
        ),
        "acceptance_criteria": [
            "No provider, API, GPU, or cloud spend occurs.",
            "The current claim-boundary matrix validates.",
            "Every malformed matrix fixture fails for the expected reason.",
            "The schema or validator artifact is committed.",
            "Command output and proof artifacts are committed.",
            "No leaderboard, SWE-bench, production, live-domain, or model-superiority claim is made.",
        ],
        "evidence": [
            {
                "kind": "test",
                "status": status,
                "artifact": "experiments/iter30_boundary_matrix_schema_guard/proof/schema_guard_report.json",
                "notes": "Real matrix validation plus intentionally malformed matrix fixtures.",
            },
            {
                "kind": "artifact",
                "status": "pass",
                "artifact": "experiments/iter30_boundary_matrix_schema_guard/proof/claim_boundary_matrix.schema.json",
                "notes": "Machine-readable manifest of required matrix fields and invariants.",
            },
            {
                "kind": "adversarial_review",
                "status": status,
                "artifact": "experiments/iter30_boundary_matrix_schema_guard/proof/review.md",
                "notes": "Review records schema coverage and claim boundary.",
            },
            {
                "kind": "live_check",
                "status": "not_applicable",
                "notes": "No production or live-domain behavior changed.",
            },
        ],
        "falsifiers": [
            "The result must block if the current matrix cannot be loaded.",
            "The result must fail if the current matrix fails validation.",
            "The result must fail if any malformed matrix fixture passes.",
            "The result must fail if original provider logic and changed candidate logic can be conflated.",
            "The result must fail if failed/null rows can be hidden.",
            "The result must not widen into benchmark, production, live-domain, or model-superiority claims.",
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

    matrix = read_json(SOURCE_MATRIX)
    negative_report = read_json(SOURCE_NEGATIVE_REPORT)
    schema = schema_manifest()
    write_json(PROOF / "claim_boundary_matrix.schema.json", schema)

    real_errors = validate_matrix(matrix)
    fixtures = [
        evaluate_fixture(matrix, "missing_evidence_path", ["missing_evidence_path"]),
        evaluate_fixture(matrix, "invalid_status", ["invalid_status"]),
        evaluate_fixture(
            matrix,
            "original_candidate_conflation",
            ["original_candidate_conflation"],
        ),
        evaluate_fixture(matrix, "missing_required_exclusion", ["missing_required_exclusion"]),
        evaluate_fixture(matrix, "hidden_failed_null_rows", ["hidden_failed_null_rows"]),
    ]
    failed_fixtures = [fixture for fixture in fixtures if fixture["status"] != "pass"]
    source_guard_ok = (
        negative_report.get("status") == "pass"
        and negative_report.get("fixtures_failed_as_expected") is True
    )
    status = "pass" if not real_errors and not failed_fixtures and source_guard_ok else "fail"

    report = {
        "schema_version": "telos.boundary_matrix_schema_guard.report.v1",
        "status": status,
        "source_matrix_path": str(SOURCE_MATRIX.relative_to(ROOT)),
        "source_matrix_sha256": sha256_file(SOURCE_MATRIX),
        "source_negative_guard_report_path": str(SOURCE_NEGATIVE_REPORT.relative_to(ROOT)),
        "source_negative_guard_report_sha256": sha256_file(SOURCE_NEGATIVE_REPORT),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "schema_path": "experiments/iter30_boundary_matrix_schema_guard/proof/claim_boundary_matrix.schema.json",
        "validator_path": "scripts/verify_boundary_matrix_schema_guard.py",
        "real_matrix_valid": not real_errors,
        "real_matrix_error_codes": sorted({item["code"] for item in real_errors}),
        "real_matrix_errors": real_errors,
        "fixture_count": len(fixtures),
        "fixtures_failed_as_expected": len(failed_fixtures) == 0,
        "failed_fixture_ids": [fixture["fixture_id"] for fixture in failed_fixtures],
        "source_negative_guard_status": negative_report.get("status"),
        "source_negative_guard_fixtures_failed_as_expected": negative_report.get(
            "fixtures_failed_as_expected"
        ),
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "fixtures": fixtures,
    }
    write_json(PROOF / "schema_guard_report.json", report)

    output_lines = [
        f"boundary matrix schema guard: {status}",
        f"source_matrix={SOURCE_MATRIX.relative_to(ROOT)}",
        "provider_api_calls=0",
        "cloud_or_gpu_used=false",
        f"real_matrix_valid={str(not real_errors).lower()}",
        f"fixtures={len(fixtures)} failed_as_expected={len(fixtures) - len(failed_fixtures)}",
        f"failed_fixture_ids={','.join(report['failed_fixture_ids'])}",
    ]
    for fixture in fixtures:
        output_lines.append(
            f"{fixture['fixture_id']}: {'pass' if fixture['status'] == 'pass' else 'fail'} "
            f"observed={','.join(fixture['observed_error_codes'])}"
        )
    (PROOF / "command_output.txt").write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    review = """# Iteration 30 Review

The boundary-matrix schema guard validated the current `iter27` claim-boundary matrix and evaluated
five generated malformed matrix fixtures. The validator rejects missing evidence paths, invalid row
status values, original/candidate conflation, missing no-claim exclusions, and hidden failed/null
rows.

This gate strengthens the matrix contract. It does not add behavior evidence, mutate the real
matrix, or claim a benchmark result. The fixture files are separate proof artifacts under
`experiments/iter30_boundary_matrix_schema_guard/proof/fixtures/`.

No provider call, API call, GPU, cloud runner, production deployment, live-domain check, leaderboard
run, or SWE-bench run occurred in this gate.
"""
    (PROOF / "review.md").write_text(review, encoding="utf-8")

    run_summary = {
        "schema_version": "telos.boundary_matrix_schema_guard.summary.v1",
        "status": status,
        "experiment_id": "iter30_boundary_matrix_schema_guard",
        "source_experiment": "iter27_semantic_claim_boundary_matrix",
        "source_matrix_path": str(SOURCE_MATRIX.relative_to(ROOT)),
        "source_matrix_sha256": sha256_file(SOURCE_MATRIX),
        "source_negative_guard_report_path": str(SOURCE_NEGATIVE_REPORT.relative_to(ROOT)),
        "source_negative_guard_report_sha256": sha256_file(SOURCE_NEGATIVE_REPORT),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "real_matrix_valid": not real_errors,
        "fixture_count": len(fixtures),
        "fixtures_failed_as_expected": len(failed_fixtures) == 0,
        "failed_fixture_ids": report["failed_fixture_ids"],
        "leaderboard_or_swebench_claimed": False,
        "production_or_live_domain_changed": False,
        "provider_game_score_used_as_verifier_evidence": False,
        "clean_pass": status == "pass",
        "next_gate": "experiments/iter31_claim_boundary_release_manifest/HYPOTHESIS.md",
        "artifact_hashes": {
            "claim_boundary_matrix.schema.json": sha256_file(
                PROOF / "claim_boundary_matrix.schema.json"
            ),
            "command_output.txt": sha256_file(PROOF / "command_output.txt"),
            "review.md": sha256_file(PROOF / "review.md"),
            "schema_guard_report.json": sha256_file(PROOF / "schema_guard_report.json"),
        },
    }
    write_json(PROOF / "run_summary.json", run_summary)

    learning_record = {
        "schema_version": "telos.learning_record.v1",
        "experiment_id": "iter30_boundary_matrix_schema_guard",
        "status": "null" if status == "fail" else status,
        "insight": (
            "The claim-boundary matrix can be guarded by an explicit local schema validator that "
            "rejects malformed rows and hidden failed/null gates."
        ),
        "next_action": (
            "pre-register a release manifest for the claim-boundary evidence chain so reviewers "
            "can verify the result packet without guessing artifact scope"
        ),
        "result_path": "experiments/iter30_boundary_matrix_schema_guard/RESULT.md",
        "evidence_paths": [
            "experiments/iter30_boundary_matrix_schema_guard/proof/run_summary.json",
            "experiments/iter30_boundary_matrix_schema_guard/proof/schema_guard_report.json",
            "experiments/iter30_boundary_matrix_schema_guard/proof/claim_boundary_matrix.schema.json",
            "experiments/iter30_boundary_matrix_schema_guard/proof/command_output.txt",
            "experiments/iter30_boundary_matrix_schema_guard/proof/review.md",
            "experiments/iter30_boundary_matrix_schema_guard/proof/valid/receipt_boundary_matrix_schema_guard.json",
        ],
    }
    write_json(PROOF / "learning_record.json", learning_record)
    write_json(VALID / "receipt_boundary_matrix_schema_guard.json", build_receipt(status))

    print("\n".join(output_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
