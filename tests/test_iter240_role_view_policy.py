"""Focused adversarial tests for iter240's prospective role-view policy."""

from __future__ import annotations

from copy import deepcopy

import pytest

from scripts import validate_iter240_role_view_policy as guard


def policy() -> dict:
    return guard.load_canonical_json(guard.POLICY)


def known_bad() -> dict:
    return guard.load_canonical_json(guard.KNOWN_BAD)


def assignment(
    principal: str,
    subject_id: str,
    *,
    authority_kind: str = "artifact_producer",
    conflicts_screened: bool = True,
    is_current_agent: bool = False,
    is_repository_owner: bool = False,
) -> dict:
    return {
        "authority_kind": authority_kind,
        "conflicts_screened": conflicts_screened,
        "is_current_agent": is_current_agent,
        "is_repository_owner": is_repository_owner,
        "principal": principal,
        "subject_id": subject_id,
    }


def test_committed_policy_is_canonical_and_exact() -> None:
    document = policy()
    assert guard.policy_errors(document) == []
    assert guard.POLICY.read_bytes() == guard.canonical_json_bytes(document)
    assert document["execution_authorized"] is False
    assert document["identity_assignments"] == []
    assert document["claim_boundary"] == guard.CLAIM_BOUNDARY


def test_future_ground_truth_admission_bars_are_exact_and_non_authorizing() -> None:
    document = policy()
    bars = document["future_ground_truth_admission_bars"]
    assert bars == guard.FUTURE_GROUND_TRUTH_ADMISSION_BARS
    assert bars["consequence_validity_minimum"] == {
        "denominator": 100,
        "numerator": 95,
    }
    assert bars["adjudication_completion_minimum"] == {
        "denominator": 100,
        "numerator": 90,
    }
    assert bars["critical_leakage_maximum"] == 0
    assert bars["supported_positive_unique_task_minimum"] == 10
    assert bars["self_approval_allowed"] is False
    assert document["execution_authorized"] is False


def test_consequence_requires_accepted_and_independent_validity_controls() -> None:
    controls = policy()["consequence_control_constraints"]
    assert controls == guard.CONSEQUENCE_CONTROL_CONSTRAINTS
    assert controls["accepted_implementation_alone_is_sufficient"] is False
    assert controls["accepted_implementation_must_satisfy_frozen_consequence"] is True
    assert controls["independent_implementation_must_satisfy_frozen_consequence"] is True
    assert (
        controls[
            "independent_producer_must_be_distinct_from_candidate_and_consequence_author"
        ]
        is True
    )


def test_broker_requires_immutable_image_identity_and_fixed_safety_policy() -> None:
    document = policy()
    constraints = document["broker_constraints"]
    assert constraints["immutable_image_id_and_repository_digest_required"] is True
    assert constraints["mutable_tag_sufficient"] is False
    assert constraints["safety_allowlist_relaxation_allowed"] is False
    assert constraints["stale_image_disposition"] == "invalid_attempt"

    view = guard.example_role_view("outcome_masking_broker")
    assert guard.role_view_errors(document, "outcome_masking_broker", view) == []
    view["image_digest"]["image_repository_digest"] = "example/repository:latest"
    errors = guard.role_view_errors(document, "outcome_masking_broker", view)
    assert any("immutable image provenance" in error for error in errors)


def test_role_partitions_are_exhaustive_disjoint_and_required() -> None:
    document = policy()
    catalog = set(document["field_catalog"])
    for role, record in document["roles"].items():
        allowed = record["allowed_view_fields"]
        forbidden = record["forbidden_view_fields"]
        required = record["required_view_fields"]
        assert len(allowed) == len(set(allowed)), role
        assert len(forbidden) == len(set(forbidden)), role
        assert set(allowed).isdisjoint(forbidden), role
        assert set(allowed) | set(forbidden) == catalog, role
        assert required == allowed, role


def test_every_synthetic_least_privilege_view_passes() -> None:
    document = policy()
    for role in sorted(guard.ROLE_ALLOWED):
        view = guard.example_role_view(role)
        assert set(view) == {pointer[1:] for pointer in guard.ROLE_ALLOWED[role]}
        assert guard.role_view_errors(document, role, view) == []


def test_author_and_valid_producer_never_receive_scientific_answers() -> None:
    document = policy()
    protected = {
        "/accepted_patch",
        "/candidate_operational_label",
        "/candidate_patch",
        "/frozen_consequence",
        "/historical_outcome",
        "/historical_scenario",
        "/independent_patch",
        "/instance_id",
        "/operational_stratum",
        "/prior_judge_output",
        "/prior_witness",
        "/private_slot_mapping",
        "/provider_identity",
        "/solver_identity",
    }
    for role in ("consequence_author", "valid_implementation_producer"):
        allowed = set(document["roles"][role]["allowed_view_fields"])
        assert allowed.isdisjoint(protected)
    assert "/frozen_consequence" not in document["roles"][
        "valid_implementation_producer"
    ]["allowed_view_fields"]


def test_primary_adjudicators_have_identical_blinded_views() -> None:
    document = policy()
    first = document["roles"]["semantic_adjudicator_1"]
    second = document["roles"]["semantic_adjudicator_2"]
    assert first["allowed_view_fields"] == second["allowed_view_fields"]
    forbidden = set(first["forbidden_view_fields"])
    assert {
        "/candidate_patch",
        "/accepted_patch",
        "/independent_patch",
        "/private_slot_mapping",
        "/prior_judge_output",
        "/prior_rationales_shuffled",
        "/candidate_operational_label",
    } <= forbidden


def test_nested_slot_identity_mapping_is_rejected_outside_broker() -> None:
    document = policy()
    view = guard.example_role_view("semantic_adjudicator_1")
    view["blinded_execution_records"][0]["origin"] = "candidate"
    errors = guard.role_view_errors(
        document,
        "semantic_adjudicator_1",
        view,
    )
    assert any("private slot identity leaked" in error for error in errors)

    broker = guard.example_role_view("outcome_masking_broker")
    assert guard.role_view_errors(document, "outcome_masking_broker", broker) == []


def test_disagreement_rationales_are_gated_by_own_lock() -> None:
    document = policy()
    view = guard.example_role_view("disagreement_adjudicator")
    assert "/prior_rationales_shuffled" in guard.ROLE_ALLOWED[
        "disagreement_adjudicator"
    ]
    del view["reviewer_lock_receipt"]
    errors = guard.role_view_errors(document, "disagreement_adjudicator", view)
    assert any("missing required fields" in error for error in errors)
    assert any("own first-pass lock required" in error for error in errors)


def test_deidentified_analyst_has_no_identity_patch_or_slot_mapping() -> None:
    document = policy()
    allowed = set(document["roles"]["deidentified_analyst"]["allowed_view_fields"])
    assert {
        "/accepted_patch",
        "/candidate_patch",
        "/independent_patch",
        "/person_id_opaque",
        "/private_slot_mapping",
        "/repository",
        "/source_path",
    }.isdisjoint(allowed)
    assert {
        "/adjudication_completion",
        "/conflict_or_abstention",
        "/consequence_validity",
        "/locked_semantic_labels",
        "/missingness_state",
        "/operational_stratum",
        "/task_cluster",
    } <= allowed


@pytest.mark.parametrize(
    "alias",
    [
        "candidatePatch",
        "candidate.patch",
        "candidate_patch",
        "\uff23\uff21\uff2e\uff24\uff29\uff24\uff21\uff34\uff25"
        "\uff0d\uff30\uff21\uff34\uff23\uff28",
    ],
)
def test_nested_key_aliases_are_rejected_after_normalization(alias: str) -> None:
    document = policy()
    view = guard.example_role_view("consequence_author")
    view["public_context"] = {"metadata": {alias: "concealed"}}
    errors = guard.role_view_errors(document, "consequence_author", view)
    assert any("forbidden key token" in error for error in errors)


def test_dynamic_diff_line_is_found_across_case_and_punctuation() -> None:
    document = policy()
    view = guard.example_role_view("consequence_author")
    view["public_context"] = "The implementation enables feature-flag-xyz."
    errors = guard.role_view_errors(
        document,
        "consequence_author",
        view,
        dynamic_forbidden_literals=["FEATURE_FLAG_XYZ"],
    )
    assert any("dynamic forbidden literal leaked" in error for error in errors)


def test_too_short_dynamic_literal_is_rejected_not_silently_scanned() -> None:
    document = policy()
    view = guard.example_role_view("consequence_author")
    errors = guard.role_view_errors(
        document,
        "consequence_author",
        view,
        dynamic_forbidden_literals=["x"],
    )
    assert any("dynamic forbidden literal is too short" in error for error in errors)


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        ("See https://example.invalid/private", "URL scheme contaminates"),
        ("Read retained/outcome.json first", "source-like filename contaminates"),
        ("RESULT=accepted-only", "fixed forbidden substring leaked"),
        ("source iter224 row", "fixed forbidden substring leaked"),
    ],
)
def test_author_source_contamination_is_fail_closed(value: str, reason: str) -> None:
    document = policy()
    view = guard.example_role_view("consequence_author")
    view["public_context"] = value
    errors = guard.role_view_errors(document, "consequence_author", view)
    assert any(reason in error for error in errors)


def test_integer_one_is_not_a_boolean() -> None:
    document = policy()
    view = guard.example_role_view("outcome_masking_broker")
    view["attempt_plan_frozen_before_outcomes"] = 1
    errors = guard.role_view_errors(document, "outcome_masking_broker", view)
    assert any("exact JSON type boolean" in error for error in errors)
    assert any("attempt plan must freeze before outcomes" in error for error in errors)


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        (
            "attempt_order",
            ["attempt-1", "attempt-2", "attempt-3", "attempt-4"],
            "attempt count must be between one and three",
        ),
        (
            "attempt_order",
            ["attempt-1", "attempt-1"],
            "attempt order contains duplicate IDs",
        ),
        (
            "attempt_selection_rule",
            "choose_first_different_result",
            "outcome-selected attempt rule is forbidden",
        ),
        (
            "unsafe_execution_allowed",
            True,
            "unsafe execution must remain forbidden",
        ),
    ],
)
def test_broker_cannot_relax_attempt_or_safety_contract(
    field: str,
    value: object,
    reason: str,
) -> None:
    document = policy()
    view = guard.example_role_view("outcome_masking_broker")
    view[field] = value
    errors = guard.role_view_errors(document, "outcome_masking_broker", view)
    assert any(reason in error for error in errors)


def test_excluded_unsafe_row_cannot_carry_execution_records() -> None:
    document = policy()
    view = guard.example_role_view("outcome_masking_broker")
    view["safety_disposition"] = "excluded_unsafe"
    errors = guard.role_view_errors(document, "outcome_masking_broker", view)
    assert any("unsafe row contains execution records" in error for error in errors)
    view["blinded_execution_records"] = []
    assert guard.role_view_errors(document, "outcome_masking_broker", view) == []


def test_candidate_and_accepted_producers_may_share_upstream_identity() -> None:
    document = policy()
    assignments = [
        assignment("candidate_patch_producer", "upstream-producer"),
        assignment("accepted_patch_producer", "upstream-producer"),
    ]
    assert guard.assignment_errors(document, assignments) == []


def test_artifact_producer_cannot_be_primary_adjudicator() -> None:
    document = policy()
    assignments = [
        assignment("candidate_patch_producer", "same-person"),
        assignment(
            "semantic_adjudicator_1",
            "same-person",
            authority_kind="independent_human",
        ),
    ]
    errors = guard.assignment_errors(document, assignments)
    assert any("incompatible principals share subject" in error for error in errors)


def test_artifact_producer_cannot_conflict_screen_itself() -> None:
    document = policy()
    assignments = [
        assignment("candidate_patch_producer", "same-person"),
        assignment(
            "independence_registrar",
            "same-person",
            authority_kind="conflict_screening_authority",
        ),
    ]
    errors = guard.assignment_errors(document, assignments)
    assert any("incompatible principals share subject" in error for error in errors)


@pytest.mark.parametrize(
    ("record", "reason"),
    [
        (
            assignment(
                "semantic_adjudicator_1",
                "model",
                authority_kind="model_sample",
            ),
            "independent human authority required",
        ),
        (
            assignment(
                "semantic_adjudicator_2",
                "owner",
                authority_kind="independent_human",
                is_repository_owner=True,
            ),
            "repository owner cannot supply independent authority",
        ),
        (
            assignment(
                "consequence_author",
                "agent",
                authority_kind="independent_human",
                is_current_agent=True,
            ),
            "current agent cannot supply human authority",
        ),
        (
            assignment(
                "disagreement_adjudicator",
                "unscreened",
                authority_kind="independent_human",
                conflicts_screened=False,
            ),
            "conflicts must be explicitly screened",
        ),
    ],
)
def test_authority_substitutes_and_unscreened_people_fail(
    record: dict,
    reason: str,
) -> None:
    errors = guard.assignment_errors(policy(), [record])
    assert any(reason in error for error in errors)


def test_known_bad_manifest_is_canonical_complete_and_executed() -> None:
    document = policy()
    manifest = known_bad()
    assert guard.KNOWN_BAD.read_bytes() == guard.canonical_json_bytes(manifest)
    assert {case["id"] for case in manifest["cases"]} == guard.REQUIRED_FIXTURE_IDS
    assert guard.fixture_manifest_errors(document, manifest) == []


def test_removing_one_known_bad_case_is_detected() -> None:
    manifest = deepcopy(known_bad())
    manifest["cases"].pop()
    errors = guard.fixture_manifest_errors(policy(), manifest)
    assert any("fixture inventory drift" in error for error in errors)


def test_strict_json_loader_rejects_duplicate_nonfinite_and_byte_drift() -> None:
    with pytest.raises(guard.PolicyError, match="duplicate JSON keys"):
        guard.load_canonical_json_bytes(
            b'{"schema_version":"x","schema_version":"y"}\n',
            label="duplicate",
        )
    with pytest.raises(guard.PolicyError, match="non-finite JSON value"):
        guard.load_canonical_json_bytes(b'{"value":NaN}\n', label="nonfinite")
    with pytest.raises(guard.PolicyError, match="not canonical"):
        guard.load_canonical_json_bytes(b'{"value": 1}\n', label="noncanonical")


def test_policy_mutations_cannot_authorize_execution_or_self_verification() -> None:
    document = policy()
    spend = deepcopy(document)
    spend["claim_boundary"]["spend_authorized_usd"] = 1
    assert any("claim_boundary" in error for error in guard.policy_errors(spend))

    consensus = deepcopy(document)
    consensus["claim_boundary"]["model_consensus_is_independent_authority"] = True
    assert any("claim_boundary" in error for error in guard.policy_errors(consensus))

    assigned = deepcopy(document)
    assigned["identity_assignments"] = [{"principal": "semantic_adjudicator_1"}]
    assert any("identity_assignments" in error for error in guard.policy_errors(assigned))


def test_repository_role_policy_guard_passes() -> None:
    assert guard.validate_current() == []
