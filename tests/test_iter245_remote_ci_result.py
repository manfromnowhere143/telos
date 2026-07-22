"""Known-good and known-bad controls for the Iter245 result consistency guard.

The guard under test is retrospective and same-operator.  These tests prove
fail-closed consistency behavior; they do not create independent attestation
of the hosted runs or their command execution.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import pytest

from scripts import validate_iter245_remote_ci_result as guard


ROOT = Path(__file__).resolve().parents[1]
OBSERVATION = (
    ROOT
    / "experiments/iter245_offline_verified_python_bootstrap/proof/remote_ci_observation.json"
)
WORKFLOW = ROOT / ".github/workflows/ci.yml"
COMMAND = "python3 scripts/validate_iter245_remote_ci_result.py"


def load_observation() -> dict[str, Any]:
    return json.loads(OBSERVATION.read_text(encoding="utf-8"))


def encode(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")


def mutated(path: tuple[str | int, ...], value: Any) -> bytes:
    document = deepcopy(load_observation())
    cursor: Any = document
    for component in path[:-1]:
        cursor = cursor[component]
    cursor[path[-1]] = value
    return encode(document)


def test_retained_observation_passes_retrospective_consistency_guard() -> None:
    assert guard.validation_errors(OBSERVATION.read_bytes()) == []


def test_ci_invokes_exactly_one_result_guard_after_bootstrap_guard() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    bootstrap_command = "python3 scripts/validate_iter245_python_bootstrap.py"

    assert workflow.count(f"        run: {COMMAND}\n") == 1
    assert workflow.index(bootstrap_command) < workflow.index(COMMAND)


@pytest.mark.parametrize(
    ("path", "value", "expected_fragment"),
    (
        (("candidate", "commit"), "0" * 40, "candidate.commit differs"),
        (("candidate", "tree"), "1" * 40, "candidate.tree differs"),
        (
            ("candidate", "pull_request", "synthetic_merge_parents"),
            [guard.CANDIDATE_COMMIT, guard.BASE_COMMIT],
            "synthetic_merge_parents differs",
        ),
        (
            ("candidate", "pull_request", "synthetic_merge_tree"),
            "2" * 40,
            "synthetic_merge_tree differs",
        ),
        (("runs", 0, "attempt"), 2, "runs.push.attempt differs"),
        (("runs", 1, "event"), "push", "run event census differs"),
        (
            ("runs", 1, "jobs", 0, "job_id"),
            88924522742,
            "runs.pull_request.jobs.3.11.job_id differs",
        ),
        (
            ("runs", 0, "jobs", 0, "selected_steps", "tests", "conclusion"),
            "failure",
            "runs.push.jobs.3.12.selected_steps.tests differs",
        ),
        (
            ("runs", 0, "jobs", 0, "runner", "id"),
            1000019999,
            "runs.push.jobs.3.12.runner differs",
        ),
        (
            ("runner_image", "image_version"),
            "rolling",
            "runner_image differs",
        ),
        (
            ("matrix_observations", 0, "archive_extraction", "archive_sha256"),
            "3" * 64,
            "archive_extraction.archive_sha256 differs",
        ),
        (
            ("matrix_observations", 1, "archive_extraction", "archive_member_count"),
            9340,
            "archive_extraction.archive_member_count differs",
        ),
        (
            ("matrix_observations", 0, "bootstrap_summary", "registered_asset_id"),
            449621340,
            "bootstrap_summary.registered_asset_id differs",
        ),
        (
            ("matrix_observations", 1, "observed_in_job_ids"),
            [88924514424, 88924522741],
            "observed_in_job_ids differs",
        ),
        (
            ("python_trust_observation", "bounded_observation", "decision"),
            "deny",
            "python_trust_observation differs",
        ),
        (
            ("python_trust_observation", "bounded_observation", "file_mode"),
            "0777",
            "python_trust_observation differs",
        ),
        (
            ("conclusion", "final_sealed_head_checks"),
            "success",
            "conclusion differs",
        ),
        (
            ("conclusion", "merged_master_verification"),
            "success",
            "conclusion differs",
        ),
        (
            ("external_security_check", "conclusion"),
            "success",
            "external_security_check differs",
        ),
        (
            ("external_security_check", "general_security_approval"),
            True,
            "external_security_check differs",
        ),
        (
            ("external_security_check", "required_by_default_branch_ruleset"),
            True,
            "external_security_check differs",
        ),
        (
            (
                "result_capture_contract",
                "semantic_validator_supplies_independent_attestation",
            ),
            True,
            "result_capture_contract differs",
        ),
        (
            ("workflow", "sha256"),
            "4" * 64,
            "workflow differs",
        ),
    ),
)
def test_semantic_known_bad_mutations_fail_closed(
    path: tuple[str | int, ...],
    value: Any,
    expected_fragment: str,
) -> None:
    errors = guard.validation_errors(mutated(path, value))

    assert errors
    assert any(expected_fragment in error for error in errors)


def test_missing_matrix_job_fails_closed() -> None:
    document = deepcopy(load_observation())
    del document["runs"][0]["jobs"][1]

    errors = guard.validation_errors(encode(document))

    assert "runs.push.jobs census differs" in errors


def test_duplicate_matrix_observation_fails_closed() -> None:
    document = deepcopy(load_observation())
    document["matrix_observations"].append(
        deepcopy(document["matrix_observations"][0])
    )

    errors = guard.validation_errors(encode(document))

    assert "matrix observation census differs" in errors


def test_duplicate_job_entry_fails_closed() -> None:
    document = deepcopy(load_observation())
    document["runs"][1]["jobs"].append(deepcopy(document["runs"][1]["jobs"][0]))

    errors = guard.validation_errors(encode(document))

    assert "runs.pull_request.jobs census differs" in errors


def test_absent_runner_identity_fails_exact_schema() -> None:
    document = deepcopy(load_observation())
    del document["runs"][0]["jobs"][0]["runner"]

    errors = guard.validation_errors(encode(document))

    assert any("runs[0].jobs[0]: exact fields differ" in error for error in errors)


def test_failed_run_cannot_coexist_with_supported_conclusion() -> None:
    document = deepcopy(load_observation())
    document["runs"][0]["conclusion"] = "failure"

    errors = guard.validation_errors(encode(document))

    assert "runs.push.conclusion differs" in errors


@pytest.mark.parametrize(
    "field",
    ("raw_logs", "environment", "secrets", "credential", "github_token"),
)
def test_forbidden_unbounded_or_sensitive_fields_fail_closed(field: str) -> None:
    document = deepcopy(load_observation())
    document[field] = {"value": "must-not-be-retained"}

    errors = guard.validation_errors(encode(document))

    assert any(f"observation.{field}: forbidden retained field" in error for error in errors)


def test_exact_schema_rejects_unregistered_field() -> None:
    document = deepcopy(load_observation())
    document["candidate"]["unregistered"] = False

    errors = guard.validation_errors(encode(document))

    assert "observation.candidate: exact fields differ" in errors


def test_exact_schema_rejects_missing_required_step() -> None:
    document = deepcopy(load_observation())
    del document["runs"][0]["jobs"][0]["selected_steps"]["bootstrap"]

    errors = guard.validation_errors(encode(document))

    assert any("selected_steps: exact fields differ" in error for error in errors)


def test_exact_schema_rejects_boolean_as_integer() -> None:
    document = deepcopy(load_observation())
    document["runs"][0]["attempt"] = True

    errors = guard.validation_errors(encode(document))

    assert any("attempt: exact scalar type differs" in error for error in errors)


def test_duplicate_json_key_is_rejected_before_semantics() -> None:
    raw = OBSERVATION.read_bytes()
    marker = b'  "schema_version": "telos.iter245.remote_ci_observation.v1",\n'
    assert raw.count(marker) == 1
    duplicate = raw.replace(marker, marker + marker, 1)

    errors = guard.validation_errors(duplicate)

    assert errors == ["observation JSON is not strict: DuplicateKeyError"]


def test_noncanonical_json_is_rejected() -> None:
    compact = json.dumps(load_observation(), sort_keys=True).encode("utf-8")

    errors = guard.validation_errors(compact)

    assert "observation JSON is not canonical" in errors


def test_guard_source_states_its_retrospective_authority_limit() -> None:
    source = (ROOT / "scripts/validate_iter245_remote_ci_result.py").read_text(
        encoding="utf-8"
    )

    assert "retrospective, same-operator consistency check" in source
    assert "not an independent attestation" in source
