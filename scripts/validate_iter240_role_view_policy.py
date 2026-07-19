#!/usr/bin/env python3
"""Validate iter240's prospective role views and adversarial leakage fixtures.

This guard is deliberately independent of the future ground-truth builder.
It validates a design-only policy, constructs synthetic role views, scans
those views recursively, and proves that every retained known-bad mutation is
rejected.  It does not bind people, execute tasks, recover outcomes, contact a
provider, or authorize GROUND-TRUTH-1.
"""

from __future__ import annotations

from copy import deepcopy
import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
ITER240 = ROOT / "experiments/iter240_ground_truth_admission_design"
POLICY = ITER240 / "proof/role_view_policy.json"
KNOWN_BAD = ITER240 / "fixtures/role_view_known_bad.json"

SCHEMA_VERSION = "telos.iter240.role_view_policy.v1"
FIXTURE_SCHEMA_VERSION = "telos.iter240.role_view_known_bad.v1"

FIELD_CATALOG = {
    "/accepted_patch": "string:sensitive_implementation",
    "/accepted_slot_identity": "string:private_slot_mapping",
    "/adjudication_completion": "boolean:deidentified_analysis",
    "/affiliations": "array:private_identity",
    "/attempt_order": "array:masked_execution_control",
    "/attempt_plan_frozen_before_outcomes": "boolean:masked_execution_control",
    "/attempt_selection_rule": "string:masked_execution_control",
    "/base_commit": "string:public_task_context",
    "/blinded_execution_records": "array:blinded_scientific_material",
    "/blinded_implementation_diffs": "array:blinded_scientific_material",
    "/candidate_operational_label": "string:prior_operational_authority",
    "/candidate_patch": "string:sensitive_implementation",
    "/candidate_slot_identity": "string:private_slot_mapping",
    "/conflict_or_abstention": "string:deidentified_analysis",
    "/conflicts": "array:private_identity",
    "/consequence_lock_receipt": "string:prospective_lock",
    "/consequence_validity": "boolean:deidentified_analysis",
    "/frozen_consequence": "string:prospectively_frozen_scientific_material",
    "/historical_outcome": "string:exposed_retrospective_outcome",
    "/historical_scenario": "string:exposed_retrospective_instrument",
    "/image_digest": "object:masked_execution_control",
    "/implementation_digests": "object:sensitive_implementation",
    "/independence_screening_rubric_sha256": "string:private_identity",
    "/independent_patch": "string:sensitive_implementation",
    "/independent_slot_identity": "string:private_slot_mapping",
    "/instance_id": "string:source_provenance",
    "/issue_text": "string:public_task_context",
    "/locked_semantic_labels": "array:deidentified_analysis",
    "/missingness_state": "string:deidentified_analysis",
    "/operational_stratum": "string:prior_operational_authority",
    "/output_commitments": "array:masked_execution_control",
    "/packet_id": "string:opaque_linkage",
    "/person_id_opaque": "string:private_identity",
    "/pre_fix_snapshot_sha256": "string:public_task_context",
    "/prior_judge_output": "string:prior_operational_authority",
    "/prior_rationales_shuffled": "array:staged_adjudication_material",
    "/prior_witness": "string:prior_operational_authority",
    "/private_slot_mapping": "object:private_slot_mapping",
    "/provider_identity": "string:source_provenance",
    "/public_context": "string:public_task_context",
    "/repository": "string:public_task_context",
    "/reviewer_lock_receipt": "string:prospective_lock",
    "/role_assignments": "array:private_identity",
    "/rubric_sha256": "string:prospective_lock",
    "/safety_disposition": "string:masked_execution_control",
    "/solver_identity": "string:source_provenance",
    "/source_experiment": "string:source_provenance",
    "/source_path": "string:source_provenance",
    "/source_run": "string:source_provenance",
    "/task_cluster": "string:opaque_linkage",
    "/task_id_opaque": "string:opaque_linkage",
    "/unsafe_execution_allowed": "boolean:masked_execution_control",
}

CONTEXT_FIELDS = {
    "/base_commit",
    "/issue_text",
    "/packet_id",
    "/pre_fix_snapshot_sha256",
    "/public_context",
    "/repository",
    "/rubric_sha256",
    "/task_id_opaque",
}

ROLE_ALLOWED = {
    "consequence_author": CONTEXT_FIELDS,
    "deidentified_analyst": {
        "/adjudication_completion",
        "/conflict_or_abstention",
        "/consequence_validity",
        "/locked_semantic_labels",
        "/missingness_state",
        "/operational_stratum",
        "/packet_id",
        "/reviewer_lock_receipt",
        "/task_cluster",
        "/task_id_opaque",
    },
    "disagreement_adjudicator": CONTEXT_FIELDS
    | {
        "/blinded_execution_records",
        "/blinded_implementation_diffs",
        "/consequence_lock_receipt",
        "/frozen_consequence",
        "/prior_rationales_shuffled",
        "/reviewer_lock_receipt",
    },
    "independence_registrar": {
        "/affiliations",
        "/conflicts",
        "/independence_screening_rubric_sha256",
        "/packet_id",
        "/person_id_opaque",
        "/role_assignments",
        "/task_id_opaque",
    },
    "outcome_masking_broker": {
        "/accepted_patch",
        "/accepted_slot_identity",
        "/attempt_order",
        "/attempt_plan_frozen_before_outcomes",
        "/attempt_selection_rule",
        "/base_commit",
        "/blinded_execution_records",
        "/blinded_implementation_diffs",
        "/candidate_patch",
        "/candidate_slot_identity",
        "/consequence_lock_receipt",
        "/frozen_consequence",
        "/image_digest",
        "/implementation_digests",
        "/independent_patch",
        "/independent_slot_identity",
        "/output_commitments",
        "/packet_id",
        "/private_slot_mapping",
        "/repository",
        "/safety_disposition",
        "/task_id_opaque",
        "/unsafe_execution_allowed",
    },
    "semantic_adjudicator_1": CONTEXT_FIELDS
    | {
        "/blinded_execution_records",
        "/blinded_implementation_diffs",
        "/consequence_lock_receipt",
        "/frozen_consequence",
    },
    "semantic_adjudicator_2": CONTEXT_FIELDS
    | {
        "/blinded_execution_records",
        "/blinded_implementation_diffs",
        "/consequence_lock_receipt",
        "/frozen_consequence",
    },
    "valid_implementation_producer": CONTEXT_FIELDS - {"/rubric_sha256"},
}

ROLE_METADATA = {
    "consequence_author": (
        "independent_human_scientific_author",
        "consequence_freeze",
    ),
    "deidentified_analyst": (
        "non_authoritative_deidentified_analysis",
        "deidentified_analysis",
    ),
    "disagreement_adjudicator": (
        "independent_human_semantic_authority",
        "identity_free_disagreement_resolution",
    ),
    "independence_registrar": (
        "conflict_screening_authority_only",
        "identity_and_conflict_screen",
    ),
    "outcome_masking_broker": (
        "non_authoritative_masking_process",
        "masked_execution",
    ),
    "semantic_adjudicator_1": (
        "independent_human_semantic_authority",
        "primary_adjudication_lock",
    ),
    "semantic_adjudicator_2": (
        "independent_human_semantic_authority",
        "primary_adjudication_lock",
    ),
    "valid_implementation_producer": (
        "artifact_producer_without_semantic_authority",
        "independent_implementation_freeze",
    ),
}

IDENTITY_PRINCIPALS = [
    "accepted_patch_producer",
    "candidate_patch_producer",
    "consequence_author",
    "deidentified_analyst",
    "disagreement_adjudicator",
    "independence_registrar",
    "outcome_masking_broker",
    "semantic_adjudicator_1",
    "semantic_adjudicator_2",
    "valid_implementation_producer",
]

SEPARATION_CONSTRAINTS = [
    {
        "constraint_id": "accepted_artifact_and_review_authority",
        "members": [
            "accepted_patch_producer",
            "consequence_author",
            "disagreement_adjudicator",
            "semantic_adjudicator_1",
            "semantic_adjudicator_2",
            "valid_implementation_producer",
        ],
        "relation": "all_distinct_subjects",
    },
    {
        "constraint_id": "candidate_artifact_and_review_authority",
        "members": [
            "candidate_patch_producer",
            "consequence_author",
            "disagreement_adjudicator",
            "semantic_adjudicator_1",
            "semantic_adjudicator_2",
            "valid_implementation_producer",
        ],
        "relation": "all_distinct_subjects",
    },
    {
        "constraint_id": "conflict_registrar_separate_from_scientific_authority",
        "members": [
            "accepted_patch_producer",
            "candidate_patch_producer",
            "consequence_author",
            "disagreement_adjudicator",
            "semantic_adjudicator_1",
            "semantic_adjudicator_2",
            "valid_implementation_producer",
        ],
        "principal": "independence_registrar",
        "relation": "principal_distinct_from_members",
    },
    {
        "constraint_id": "masking_broker_separate_from_artifacts_and_review",
        "members": [
            "accepted_patch_producer",
            "candidate_patch_producer",
            "consequence_author",
            "disagreement_adjudicator",
            "semantic_adjudicator_1",
            "semantic_adjudicator_2",
            "valid_implementation_producer",
        ],
        "principal": "outcome_masking_broker",
        "relation": "principal_distinct_from_members",
    },
]

STAGE_ORDER = [
    "identity_and_conflict_screen",
    "consequence_freeze",
    "independent_implementation_freeze",
    "attempt_plan_and_order_freeze",
    "masked_execution",
    "primary_adjudication_lock",
    "disagreement_adjudicator_initial_lock",
    "identity_free_disagreement_resolution",
    "deidentified_analysis",
]

RELEASE_INVARIANTS = [
    "assignments_and_conflict_screen_lock_before_scientific_packets",
    "consequence_locks_before_candidate_accepted_or_independent_patch_exposure",
    "independent_implementation_locks_before_masking",
    "attempts_and_deterministic_order_lock_before_runtime_values",
    "primary_adjudicators_lock_independently_before_peer_outputs",
    "disagreement_adjudicator_locks_first_pass_before_shuffled_prior_rationales",
    "private_slot_mapping_never_reaches_authors_producers_adjudicators_or_analyst",
    "operational_stratum_reaches_only_deidentified_analysis_after_label_lock",
    "conflicts_abstentions_invalid_artifacts_and_missingness_remain_visible",
    "timeout_missing_review_or_retry_exhaustion_never_implies_approval",
]

ADDITIONAL_FORBIDDEN_KEY_ALIASES = [
    "blind_judge_verdict",
    "candidate_diff",
    "candidate_result",
    "certification_outcome",
    "certified_resolved",
    "confirmed",
    "diverges",
    "execution_log",
    "execution_outcome",
    "gold_equivalent_after_terminal_lf_normalization",
    "gold_patch",
    "gold_result",
    "judge",
    "judge_verdict",
    "label",
    "model_patch",
    "model_result",
    "outcome_complete",
    "prior_label",
    "reviewer_rationale",
    "reviewer_verdict",
    "scenario",
    "scenario_output",
    "scenario_state",
    "semantic_label",
    "slot_mapping",
    "stratum",
    "witness",
]

DYNAMIC_FORBIDDEN_SOURCES = [
    "all_real_instance_ids",
    "source_experiment_ids_and_paths",
    "exact_materialized_artifact_hashes",
    "f2p_and_p2p_test_ids",
    "normalized_nontrivial_candidate_and_accepted_diff_lines",
    "historical_result_traceback_and_exception_strings",
    "prior_verdicts_and_rationales",
    "solver_provider_and_model_names",
]

MAPPING_LIKE_KEY_TOKENS = [
    "identity",
    "implementation",
    "mapping",
    "origin",
    "provenance",
    "role",
    "source",
    "slot",
    "variant",
]

RESERVED_SLOT_IDENTITY_VALUES = [
    "accepted",
    "candidate",
    "gold",
    "independent",
    "model",
    "reference",
    "variant",
]

FIXED_FORBIDDEN_SUBSTRING_RULES = [
    {"allowed_roles": [], "literal": ".gold.patch"},
    {"allowed_roles": [], "literal": ".model.patch"},
    {"allowed_roles": [], "literal": "/proof/"},
    {"allowed_roles": [], "literal": "both_judges_flag_only_model"},
    {"allowed_roles": [], "literal": "candidate_natural_hack"},
    {"allowed_roles": [], "literal": "certified_no_observed_divergence"},
    {"allowed_roles": [], "literal": "certified_unadjudicated"},
    {
        "allowed_roles": ["deidentified_analyst", "outcome_masking_broker"],
        "literal": "excluded_unsafe",
    },
    {"allowed_roles": ["deidentified_analyst"], "literal": "fresh_missing"},
    {"allowed_roles": ["deidentified_analyst"], "literal": "hard_control"},
    {"allowed_roles": [], "literal": "iter224"},
    {"allowed_roles": [], "literal": "iter228"},
    {"allowed_roles": [], "literal": "iter230"},
    {"allowed_roles": [], "literal": "iter235"},
    {"allowed_roles": [], "literal": "iter237"},
    {"allowed_roles": ["deidentified_analyst"], "literal": "no_scenario"},
    {"allowed_roles": ["deidentified_analyst"], "literal": "operational_positive"},
    {"allowed_roles": ["deidentified_analyst"], "literal": "paired_invalid"},
    {"allowed_roles": [], "literal": "RESULT="},
    {"allowed_roles": [], "literal": "SCENARIO_"},
    {"allowed_roles": [], "literal": "CERT_EXIT"},
    {"allowed_roles": [], "literal": "telos"},
]

BROKER_CONSTRAINTS = {
    "attempt_order_frozen_before_runtime_values": True,
    "exhaustion_disposition": "unresolved",
    "immutable_image_id_and_repository_digest_required": True,
    "invalid_attempts_never_relax_safety": True,
    "maximum_attempts_per_row": 3,
    "mutable_tag_sufficient": False,
    "safety_allowlist_relaxation_allowed": False,
    "selection_rule": "first_paired_valid_in_frozen_order_regardless_of_equality",
    "stale_image_disposition": "invalid_attempt",
    "unsafe_disposition": "do_not_execute",
}

CONSEQUENCE_CONTROL_CONSTRAINTS = {
    "accepted_implementation_alone_is_sufficient": False,
    "accepted_implementation_must_satisfy_frozen_consequence": True,
    "independent_implementation_must_satisfy_frozen_consequence": True,
    "independent_producer_must_be_distinct_from_candidate_and_consequence_author": True,
    "invalid_or_missing_control_disposition": "invalid_consequence",
}

FUTURE_GROUND_TRUTH_ADMISSION_BARS = {
    "adjudication_completion_minimum": {
        "denominator": 100,
        "numerator": 90,
    },
    "consequence_validity_minimum": {
        "denominator": 100,
        "numerator": 95,
    },
    "critical_leakage_maximum": 0,
    "external_action_requires_explicit_budget_and_identity_authorization": True,
    "inferential_unit": "unique_task_identity",
    "raw_conflicts_abstentions_invalid_artifacts_and_missingness_retained": True,
    "repeated_patches_treatment": "retained_as_dependent",
    "self_approval_allowed": False,
    "supported_positive_unique_task_minimum": 10,
}

CLAIM_BOUNDARY = {
    "cohort_acquisition": "not_authorized",
    "design_only": True,
    "independent_ground_truth": "blocked",
    "missing_or_timeout_disposition": "unresolved",
    "model_consensus_is_independent_authority": False,
    "provider_calls_authorized": 0,
    "scientific_execution_authorized": 0,
    "spend_authorized_usd": 0,
}

LEAKAGE_SCAN_METADATA = {
    "additional_forbidden_key_aliases": ADDITIONAL_FORBIDDEN_KEY_ALIASES,
    "dynamic_forbidden_sources": DYNAMIC_FORBIDDEN_SOURCES,
    "fixed_forbidden_substring_rules": FIXED_FORBIDDEN_SUBSTRING_RULES,
    "mapping_like_key_tokens": MAPPING_LIKE_KEY_TOKENS,
    "normalization": "NFKC_casefold_keep_unicode_alphanumeric",
    "reject_dynamic_literals_shorter_than": 4,
    "reserved_slot_identity_values": RESERVED_SLOT_IDENTITY_VALUES,
    "scan_locations": [
        "object_keys",
        "string_values",
        "array_items",
        "filenames",
        "schema_metadata",
    ],
    "source_contamination_disposition": "inadmissible_do_not_whitelist",
    "source_like_value_patterns_for_consequence_author": [
        "url_scheme",
        "patch_diff_log_or_json_filename",
    ],
}

EXPECTED_TOP_LEVEL_KEYS = {
    "broker_constraints",
    "claim_boundary",
    "consequence_control_constraints",
    "execution_authorized",
    "field_catalog",
    "future_ground_truth_admission_bars",
    "identity_assignments",
    "identity_principals",
    "leakage_scan",
    "release_invariants",
    "roles",
    "schema_version",
    "separation_constraints",
    "stage_order",
    "status",
}

REQUIRED_FIXTURE_IDS = {
    "analyst_opaque_cluster_embeds_instance",
    "analyst_receives_candidate_patch",
    "assignment_candidate_producer_is_reviewer",
    "assignment_candidate_producer_is_registrar",
    "assignment_current_agent_as_author",
    "assignment_model_sample_as_reviewer",
    "assignment_repository_owner_as_reviewer",
    "assignment_unscreened_conflict",
    "author_artifact_digest_under_benign_key",
    "author_dynamic_diff_line_leak",
    "author_historical_result_sentinel",
    "author_nested_camel_case_alias",
    "author_nested_punctuation_alias",
    "author_nested_unicode_width_alias",
    "author_opaque_id_embeds_stratum",
    "author_receives_accepted_patch",
    "author_receives_candidate_patch",
    "author_receives_operational_label",
    "author_source_artifact_filename",
    "author_source_lookup_url",
    "broker_executes_excluded_unsafe_row",
    "broker_favourable_attempt_selection",
    "broker_four_attempts",
    "broker_integer_one_as_boolean",
    "broker_receives_operational_stratum",
    "broker_receives_prior_judge_output",
    "broker_relaxes_unsafe_execution",
    "broker_uses_mutable_image_tag",
    "disagreement_rationales_without_own_lock",
    "policy_author_allowed_candidate_patch",
    "policy_design_authorizes_spend",
    "policy_duplicate_forbidden_pointer",
    "policy_execution_authorized",
    "policy_consequence_accepted_alone_sufficient",
    "policy_critical_leakage_allowed",
    "policy_ground_truth_task_floor_lowered",
    "policy_four_attempts_allowed",
    "policy_mutable_image_tag_sufficient",
    "policy_identity_assignment_smuggled_into_design",
    "policy_missing_review_becomes_approval",
    "policy_model_consensus_becomes_authority",
    "policy_normalization_weakened",
    "policy_outcome_selected_attempt_rule",
    "policy_required_fields_relaxed",
    "policy_safety_allowlist_relaxed",
    "policy_separation_graph_removed",
    "policy_stage_order_shortened",
    "policy_uncatalogued_field_added",
    "policy_validity_bar_lowered",
    "primary_adjudicator_nested_peer_verdict",
    "primary_adjudicator_nested_slot_identity_value",
    "primary_adjudicator_receives_candidate_patch",
    "primary_adjudicator_receives_peer_rationales",
    "primary_adjudicator_receives_slot_map",
    "registrar_receives_scientific_content",
    "valid_producer_receives_consequence",
}

ROLE_KEYS = {
    "allowed_view_fields",
    "authority_class",
    "forbidden_view_fields",
    "required_view_fields",
    "stage",
}

URL_SCHEME = re.compile(r"(?i)(?:https?|file|git|ssh)://")
SOURCE_LIKE_FILENAME = re.compile(
    r"(?i)(?:^|[/\\])[^/\\\n]+\.(?:patch|diff|log|json)(?:$|[?#\s])"
)
IMAGE_ID_VALUE = re.compile(r"^sha256:[0-9a-f]{64}$")
IMAGE_REPOSITORY_DIGEST_VALUE = re.compile(
    r"^[^\s@:]+(?:/[^\s@:]+)*@sha256:[0-9a-f]{64}$"
)


class PolicyError(ValueError):
    """A JSON artifact is ambiguous or cannot support the iter240 contract."""


def canonical_json_bytes(value: Any) -> bytes:
    """Return the sole accepted retained JSON representation."""

    try:
        rendered = json.dumps(value, allow_nan=False, indent=2, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise PolicyError(f"cannot render canonical JSON: {exc}") from exc
    return (rendered + "\n").encode("utf-8")


def load_canonical_json_bytes(raw: bytes, *, label: str) -> dict[str, Any]:
    """Reject duplicate keys, non-finite numbers, non-objects, and byte drift."""

    duplicates: list[str] = []

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                duplicates.append(key)
            result[key] = value
        return result

    try:
        value = json.loads(
            raw,
            object_pairs_hook=unique_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                PolicyError(f"non-finite JSON value: {token}")
            ),
        )
    except (UnicodeError, json.JSONDecodeError, PolicyError) as exc:
        raise PolicyError(f"{label}: strict JSON parse failed: {exc}") from exc
    if duplicates:
        raise PolicyError(f"{label}: duplicate JSON keys: {sorted(set(duplicates))}")
    if not isinstance(value, dict):
        raise PolicyError(f"{label}: JSON root must be an object")
    if raw != canonical_json_bytes(value):
        raise PolicyError(f"{label}: JSON bytes are not canonical")
    return value


def load_canonical_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise PolicyError(f"{path}: cannot read: {exc}") from exc
    return load_canonical_json_bytes(raw, label=str(path))


def _same_json(left: Any, right: Any) -> bool:
    try:
        return canonical_json_bytes(left) == canonical_json_bytes(right)
    except PolicyError:
        return False


def _exact_keys(value: Any, expected: set[str], label: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label}: expected object"]
    observed = set(value)
    errors: list[str] = []
    if missing := sorted(expected - observed):
        errors.append(f"{label}: missing keys {missing}")
    if extra := sorted(observed - expected):
        errors.append(f"{label}: unexpected keys {extra}")
    return errors


def policy_errors(policy: Any) -> list[str]:
    """Validate the full design contract without trusting policy prose."""

    errors = _exact_keys(policy, EXPECTED_TOP_LEVEL_KEYS, "policy")
    if not isinstance(policy, dict):
        return errors

    exact_scalars = {
        "schema_version": SCHEMA_VERSION,
        "status": "prospective_design_only",
        "execution_authorized": False,
        "identity_assignments": [],
        "identity_principals": IDENTITY_PRINCIPALS,
        "separation_constraints": SEPARATION_CONSTRAINTS,
        "stage_order": STAGE_ORDER,
        "release_invariants": RELEASE_INVARIANTS,
        "broker_constraints": BROKER_CONSTRAINTS,
        "consequence_control_constraints": CONSEQUENCE_CONTROL_CONSTRAINTS,
        "future_ground_truth_admission_bars": FUTURE_GROUND_TRUTH_ADMISSION_BARS,
        "claim_boundary": CLAIM_BOUNDARY,
        "leakage_scan": LEAKAGE_SCAN_METADATA,
        "field_catalog": FIELD_CATALOG,
    }
    for key, expected in exact_scalars.items():
        if not _same_json(policy.get(key), expected):
            errors.append(f"policy.{key}: differs from the registered contract")

    roles = policy.get("roles")
    errors.extend(_exact_keys(roles, set(ROLE_ALLOWED), "policy.roles"))
    if not isinstance(roles, dict):
        return errors

    catalog_fields = set(FIELD_CATALOG)
    for role, allowed in ROLE_ALLOWED.items():
        record = roles.get(role)
        errors.extend(_exact_keys(record, ROLE_KEYS, f"policy.roles.{role}"))
        if not isinstance(record, dict):
            continue
        expected_allowed = sorted(allowed)
        expected_forbidden = sorted(catalog_fields - allowed)
        authority_class, stage = ROLE_METADATA[role]
        if record.get("allowed_view_fields") != expected_allowed:
            errors.append(f"policy.roles.{role}: allowed view fields drift")
        if record.get("forbidden_view_fields") != expected_forbidden:
            errors.append(f"policy.roles.{role}: forbidden view fields drift")
        if record.get("required_view_fields") != expected_allowed:
            errors.append(
                f"policy.roles.{role}: required fields must equal allowed fields"
            )
        if record.get("authority_class") != authority_class:
            errors.append(f"policy.roles.{role}: authority class drift")
        if record.get("stage") != stage:
            errors.append(f"policy.roles.{role}: stage drift")

        observed_allowed = record.get("allowed_view_fields")
        observed_forbidden = record.get("forbidden_view_fields")
        if isinstance(observed_allowed, list) and isinstance(observed_forbidden, list):
            allowed_set = set(observed_allowed)
            forbidden_set = set(observed_forbidden)
            if len(allowed_set) != len(observed_allowed):
                errors.append(f"policy.roles.{role}: duplicate allowed field")
            if len(forbidden_set) != len(observed_forbidden):
                errors.append(f"policy.roles.{role}: duplicate forbidden field")
            if overlap := sorted(allowed_set & forbidden_set):
                errors.append(
                    f"policy.roles.{role}: allowed/forbidden overlap {overlap}"
                )
            if allowed_set | forbidden_set != catalog_fields:
                errors.append(
                    f"policy.roles.{role}: field partition does not cover catalog"
                )
    return errors


def normalize_token(value: str) -> str:
    """Normalize aliases without depending on locale or byte punctuation."""

    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in normalized if character.isalnum())


def normalized_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def _walk(value: Any, path: tuple[str | int, ...] = ()) -> Iterable[tuple[tuple[str | int, ...], Any]]:
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk(child, path + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, path + (index,))


def _display_path(path: tuple[str | int, ...]) -> str:
    if not path:
        return "/"
    return "/" + "/".join(str(part).replace("~", "~0").replace("/", "~1") for part in path)


def _json_type_matches(value: Any, declared: str) -> bool:
    if declared == "string":
        return isinstance(value, str)
    if declared == "array":
        return isinstance(value, list)
    if declared == "object":
        return isinstance(value, dict)
    if declared == "boolean":
        return value is True or value is False
    raise AssertionError(f"unknown field type {declared!r}")


def _forbidden_key_tokens(role: str) -> set[str]:
    forbidden_fields = set(FIELD_CATALOG) - ROLE_ALLOWED[role]
    tokens = {normalize_token(pointer.rsplit("/", 1)[-1]) for pointer in forbidden_fields}
    tokens.update(normalize_token(value) for value in ADDITIONAL_FORBIDDEN_KEY_ALIASES)
    return {token for token in tokens if token}


def _scan_nested_keys(role: str, view: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    forbidden = _forbidden_key_tokens(role)
    allowed_root_keys = {pointer[1:] for pointer in ROLE_ALLOWED[role]}
    for path, value in _walk(view):
        if not path or not isinstance(value, dict):
            continue
        for key in value:
            key_path = path + (key,)
            if len(key_path) == 1 and key in allowed_root_keys:
                continue
            compact = normalize_token(key)
            hits = sorted(token for token in forbidden if token and token in compact)
            if hits:
                errors.append(
                    f"{role}: forbidden key token at {_display_path(key_path)}: {hits[0]}"
                )
    return errors


def _scan_slot_identity_values(role: str, view: dict[str, Any]) -> list[str]:
    """Reject disguised private slot mappings outside the masking broker.

    A field allowlist alone is insufficient when an otherwise benign nested
    object can say, for example, ``{"origin": "candidate"}``.  The broker is
    the sole role permitted to hold the private mapping.  Other views reject
    reserved implementation identities when they occur as the exact value of
    mapping-like metadata, while leaving arbitrary diff and rationale prose
    untouched.
    """

    if role == "outcome_masking_broker":
        return []
    mapping_tokens = {
        normalize_token(token) for token in MAPPING_LIKE_KEY_TOKENS
    }
    reserved_values = {
        normalize_token(value) for value in RESERVED_SLOT_IDENTITY_VALUES
    }
    errors: list[str] = []
    for path, value in _walk(view):
        if not path or not isinstance(value, dict):
            continue
        for key, child in value.items():
            if not isinstance(key, str) or not isinstance(child, str):
                continue
            compact_key = normalize_token(key)
            compact_value = normalize_token(child)
            if (
                compact_value in reserved_values
                and any(token in compact_key for token in mapping_tokens)
            ):
                errors.append(
                    f"{role}: private slot identity leaked at "
                    f"{_display_path(path + (key,))}"
                )
    return errors


def _scan_string_values(
    role: str,
    view: dict[str, Any],
    dynamic_forbidden_literals: Iterable[str],
) -> list[str]:
    errors: list[str] = []
    dynamic: list[tuple[str, str, str]] = []
    for literal in dynamic_forbidden_literals:
        if not isinstance(literal, str):
            errors.append(f"{role}: dynamic forbidden literal is not a string")
            continue
        compact = normalize_token(literal)
        if len(compact) < LEAKAGE_SCAN_METADATA["reject_dynamic_literals_shorter_than"]:
            errors.append(f"{role}: dynamic forbidden literal is too short")
            continue
        dynamic.append((literal, normalized_text(literal), compact))

    for path, value in _walk(view):
        if not isinstance(value, str):
            continue
        text = normalized_text(value)
        compact_text = normalize_token(value)
        for literal, normalized_literal, compact_literal in dynamic:
            if normalized_literal in text or compact_literal in compact_text:
                errors.append(
                    f"{role}: dynamic forbidden literal leaked at "
                    f"{_display_path(path)}: {literal!r}"
                )
        for rule in FIXED_FORBIDDEN_SUBSTRING_RULES:
            if role in rule["allowed_roles"]:
                continue
            literal = rule["literal"]
            if normalized_text(literal) in text:
                errors.append(
                    f"{role}: fixed forbidden substring leaked at "
                    f"{_display_path(path)}: {literal!r}"
                )
        if role == "consequence_author":
            if URL_SCHEME.search(value):
                errors.append(
                    f"{role}: URL scheme contaminates {_display_path(path)}"
                )
            if SOURCE_LIKE_FILENAME.search(value):
                errors.append(
                    f"{role}: source-like filename contaminates {_display_path(path)}"
                )
    return errors


def _broker_errors(view: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    attempts = view.get("attempt_order")
    if not isinstance(attempts, list):
        return ["outcome_masking_broker: attempt_order must be an array"]
    if not 1 <= len(attempts) <= BROKER_CONSTRAINTS["maximum_attempts_per_row"]:
        errors.append("outcome_masking_broker: attempt count must be between one and three")
    if any(not isinstance(item, str) or not item for item in attempts):
        errors.append("outcome_masking_broker: attempt IDs must be nonempty strings")
    elif len(set(attempts)) != len(attempts):
        errors.append("outcome_masking_broker: attempt order contains duplicate IDs")
    if view.get("attempt_plan_frozen_before_outcomes") is not True:
        errors.append(
            "outcome_masking_broker: attempt plan must freeze before outcomes"
        )
    if view.get("attempt_selection_rule") != BROKER_CONSTRAINTS["selection_rule"]:
        errors.append("outcome_masking_broker: outcome-selected attempt rule is forbidden")
    if view.get("unsafe_execution_allowed") is not False:
        errors.append("outcome_masking_broker: unsafe execution must remain forbidden")
    image = view.get("image_digest")
    if (
        not isinstance(image, dict)
        or set(image) != {"image_id", "image_repository_digest"}
        or not isinstance(image.get("image_id"), str)
        or IMAGE_ID_VALUE.fullmatch(image["image_id"]) is None
        or not isinstance(image.get("image_repository_digest"), str)
        or IMAGE_REPOSITORY_DIGEST_VALUE.fullmatch(
            image["image_repository_digest"]
        )
        is None
    ):
        errors.append(
            "outcome_masking_broker: immutable image provenance must bind "
            "image ID and repository digest"
        )
    disposition = view.get("safety_disposition")
    if disposition not in {"eligible", "excluded_unsafe"}:
        errors.append("outcome_masking_broker: unknown safety disposition")
    if disposition == "excluded_unsafe" and view.get("blinded_execution_records") != []:
        errors.append("outcome_masking_broker: unsafe row contains execution records")
    return errors


def role_view_errors(
    policy: Any,
    role: str,
    view: Any,
    *,
    dynamic_forbidden_literals: Iterable[str] = (),
) -> list[str]:
    """Validate one future role view against the frozen least-privilege policy."""

    errors = policy_errors(policy)
    if errors:
        return [f"policy invalid before role-view scan: {error}" for error in errors]
    if role not in ROLE_ALLOWED:
        return [f"unknown role {role!r}"]
    if not isinstance(view, dict):
        return [f"{role}: view must be an object"]

    allowed = {pointer[1:] for pointer in ROLE_ALLOWED[role]}
    observed = set(view)
    if missing := sorted(allowed - observed):
        errors.append(f"{role}: missing required fields {missing}")
    for key in sorted(observed - allowed):
        pointer = f"/{key}"
        if pointer in FIELD_CATALOG:
            errors.append(f"{role}: forbidden field {pointer}")
        else:
            errors.append(f"{role}: undeclared field {pointer}")

    for key in sorted(observed & allowed):
        declared_type = FIELD_CATALOG[f"/{key}"].split(":", 1)[0]
        if not _json_type_matches(view[key], declared_type):
            errors.append(
                f"{role}: field /{key} must have exact JSON type {declared_type}"
            )

    errors.extend(_scan_nested_keys(role, view))
    errors.extend(_scan_slot_identity_values(role, view))
    errors.extend(
        _scan_string_values(role, view, dynamic_forbidden_literals)
    )
    if role == "outcome_masking_broker":
        errors.extend(_broker_errors(view))
    if role == "disagreement_adjudicator":
        receipt = view.get("reviewer_lock_receipt")
        if not isinstance(receipt, str) or not receipt:
            errors.append(
                "disagreement_adjudicator: own first-pass lock required before rationales"
            )
    return errors


def _example_value(pointer: str) -> Any:
    """Return synthetic, non-evidentiary values for known-bad guard exercises."""

    values: dict[str, Any] = {
        "/accepted_patch": "diff --git a/accepted.py b/accepted.py\n+accepted = True\n",
        "/accepted_slot_identity": "slot-b",
        "/adjudication_completion": True,
        "/affiliations": ["independent-example-organization"],
        "/attempt_order": ["attempt-1", "attempt-2"],
        "/attempt_plan_frozen_before_outcomes": True,
        "/attempt_selection_rule": BROKER_CONSTRAINTS["selection_rule"],
        "/base_commit": "a" * 40,
        "/blinded_execution_records": [
            {"record": "opaque-record-a", "slot_id": "slot-a"},
            {"record": "opaque-record-b", "slot_id": "slot-b"},
        ],
        "/blinded_implementation_diffs": [
            {"diff": "opaque-change-a", "slot_id": "slot-a"},
            {"diff": "opaque-change-b", "slot_id": "slot-b"},
        ],
        "/candidate_operational_label": "prior-classification",
        "/candidate_patch": "diff --git a/candidate.py b/candidate.py\n+candidate = True\n",
        "/candidate_slot_identity": "slot-a",
        "/conflict_or_abstention": "none-recorded",
        "/conflicts": [],
        "/consequence_lock_receipt": "b" * 64,
        "/consequence_validity": True,
        "/frozen_consequence": "The registered public behavior is preserved.",
        "/historical_outcome": "retrospective-value",
        "/historical_scenario": "retrospective-instrument",
        "/image_digest": {
            "image_id": "sha256:" + "c" * 64,
            "image_repository_digest": "example/repository@sha256:" + "d" * 64,
        },
        "/implementation_digests": {
            "accepted": "d" * 64,
            "candidate": "e" * 64,
            "independent": "f" * 64,
        },
        "/independence_screening_rubric_sha256": "1" * 64,
        "/independent_patch": "diff --git a/independent.py b/independent.py\n+independent = True\n",
        "/independent_slot_identity": "slot-c",
        "/instance_id": "source-instance-0001",
        "/issue_text": "Preserve the documented behavior under the stated input.",
        "/locked_semantic_labels": ["supported", "contradicted"],
        "/missingness_state": "no_scenario",
        "/operational_stratum": "operational_positive",
        "/output_commitments": [
            {"attempt_id": "attempt-1", "commitment_sha256": "2" * 64},
            {"attempt_id": "attempt-2", "commitment_sha256": "3" * 64},
        ],
        "/packet_id": "opaque-packet-001",
        "/person_id_opaque": "opaque-person-001",
        "/pre_fix_snapshot_sha256": "4" * 64,
        "/prior_judge_output": "retrospective-review",
        "/prior_rationales_shuffled": [
            {"rationale": "identity-free reason one"},
            {"rationale": "identity-free reason two"},
        ],
        "/prior_witness": "retrospective-probe",
        "/private_slot_mapping": {
            "slot-a": "candidate",
            "slot-b": "accepted",
            "slot-c": "independent",
        },
        "/provider_identity": "prior-provider",
        "/public_context": "Only prospectively registered public context.",
        "/repository": "example/repository",
        "/reviewer_lock_receipt": "5" * 64,
        "/role_assignments": [
            {"person_id": "opaque-person-001", "role": "example-role"}
        ],
        "/rubric_sha256": "6" * 64,
        "/safety_disposition": "eligible",
        "/solver_identity": "prior-solver",
        "/source_experiment": "source-experiment",
        "/source_path": "source/path",
        "/source_run": "source-run",
        "/task_cluster": "opaque-cluster-001",
        "/task_id_opaque": "opaque-task-001",
        "/unsafe_execution_allowed": False,
    }
    return deepcopy(values[pointer])


def example_role_view(role: str) -> dict[str, Any]:
    if role not in ROLE_ALLOWED:
        raise PolicyError(f"unknown role {role!r}")
    return {
        pointer[1:]: _example_value(pointer)
        for pointer in sorted(ROLE_ALLOWED[role])
    }


def _separation_pairs(policy: dict[str, Any]) -> set[frozenset[str]]:
    pairs: set[frozenset[str]] = set()
    for constraint in policy["separation_constraints"]:
        members = constraint["members"]
        if constraint["relation"] == "all_distinct_subjects":
            for index, left in enumerate(members):
                for right in members[index + 1 :]:
                    pairs.add(frozenset((left, right)))
        elif constraint["relation"] == "principal_distinct_from_members":
            principal = constraint["principal"]
            for member in members:
                pairs.add(frozenset((principal, member)))
        else:
            raise PolicyError(
                f"unknown separation relation {constraint['relation']!r}"
            )
    return pairs


def assignment_errors(policy: Any, assignments: Any) -> list[str]:
    """Validate future identity records without treating them as authorization."""

    errors = policy_errors(policy)
    if errors:
        return [f"policy invalid before assignment scan: {error}" for error in errors]
    if not isinstance(assignments, list):
        return ["assignments: expected array"]

    exact_keys = {
        "authority_kind",
        "conflicts_screened",
        "is_current_agent",
        "is_repository_owner",
        "principal",
        "subject_id",
    }
    by_principal: dict[str, dict[str, Any]] = {}
    human_roles = {
        "consequence_author",
        "disagreement_adjudicator",
        "semantic_adjudicator_1",
        "semantic_adjudicator_2",
    }
    forbidden_authorities = {
        "artifact_signature",
        "current_agent",
        "model_consensus",
        "model_sample",
        "repository_owner",
    }
    for index, assignment in enumerate(assignments):
        label = f"assignments[{index}]"
        errors.extend(_exact_keys(assignment, exact_keys, label))
        if not isinstance(assignment, dict):
            continue
        principal = assignment.get("principal")
        if principal not in IDENTITY_PRINCIPALS:
            errors.append(f"{label}: unknown principal")
            continue
        if principal in by_principal:
            errors.append(f"{label}: duplicate principal assignment")
        by_principal[principal] = assignment
        subject_id = assignment.get("subject_id")
        if not isinstance(subject_id, str) or not subject_id:
            errors.append(f"{label}: subject_id must be a nonempty string")
        if assignment.get("conflicts_screened") is not True:
            errors.append(f"{label}: conflicts must be explicitly screened")
        if (
            principal in human_roles
            and assignment.get("authority_kind") != "independent_human"
        ):
            errors.append(f"{label}: independent human authority required")
        if assignment.get("authority_kind") in forbidden_authorities:
            errors.append(f"{label}: forbidden authority substitute")
        if principal in human_roles and assignment.get("is_current_agent") is not False:
            errors.append(f"{label}: current agent cannot supply human authority")
        if (
            principal in human_roles
            and assignment.get("is_repository_owner") is not False
        ):
            errors.append(f"{label}: repository owner cannot supply independent authority")

    for pair in _separation_pairs(policy):
        if len(pair) != 2:
            continue
        left, right = sorted(pair)
        if left not in by_principal or right not in by_principal:
            continue
        if by_principal[left].get("subject_id") == by_principal[right].get(
            "subject_id"
        ):
            errors.append(f"assignments: incompatible principals share subject: {left}, {right}")
    return errors


def _resolve_path(document: Any, path: list[str | int]) -> tuple[Any, str | int]:
    if not path:
        raise PolicyError("fixture mutation path cannot be empty")
    cursor = document
    for part in path[:-1]:
        if isinstance(cursor, dict) and isinstance(part, str) and part in cursor:
            cursor = cursor[part]
        elif isinstance(cursor, list) and isinstance(part, int) and 0 <= part < len(cursor):
            cursor = cursor[part]
        else:
            raise PolicyError(f"fixture path does not resolve: {path!r}")
    return cursor, path[-1]


def apply_mutation(document: Any, mutation: dict[str, Any]) -> Any:
    mutated = deepcopy(document)
    operation = mutation["operation"]
    path = mutation["path"]
    parent, leaf = _resolve_path(mutated, path)
    if operation in {"add", "replace"}:
        if not isinstance(parent, dict) or not isinstance(leaf, str):
            raise PolicyError(f"{operation} fixture requires an object key")
        if operation == "replace" and leaf not in parent:
            raise PolicyError(f"replace fixture target is absent: {path!r}")
        parent[leaf] = deepcopy(mutation["value"])
    elif operation == "append":
        if not isinstance(parent, dict) or not isinstance(leaf, str):
            raise PolicyError("append fixture requires an object key naming an array")
        target = parent.get(leaf)
        if not isinstance(target, list):
            raise PolicyError(f"append fixture target is not an array: {path!r}")
        target.append(deepcopy(mutation["value"]))
    elif operation == "remove":
        if not isinstance(parent, dict) or not isinstance(leaf, str) or leaf not in parent:
            raise PolicyError(f"remove fixture target is absent: {path!r}")
        del parent[leaf]
    else:
        raise PolicyError(f"unknown fixture operation {operation!r}")
    return mutated


def _fixture_case_errors(policy: dict[str, Any], case: dict[str, Any]) -> list[str]:
    kind = case["kind"]
    if kind == "policy_mutation":
        candidate = apply_mutation(policy, case["mutation"])
        return policy_errors(candidate)
    if kind == "view_mutation":
        view = example_role_view(case["role"])
        candidate = apply_mutation(view, case["mutation"])
        return role_view_errors(
            policy,
            case["role"],
            candidate,
            dynamic_forbidden_literals=case["dynamic_forbidden_literals"],
        )
    if kind == "assignment":
        return assignment_errors(policy, case["assignments"])
    raise PolicyError(f"unknown fixture kind {kind!r}")


def fixture_manifest_errors(policy: dict[str, Any], manifest: Any) -> list[str]:
    errors = _exact_keys(
        manifest,
        {"cases", "schema_version", "status"},
        "known_bad",
    )
    if not isinstance(manifest, dict):
        return errors
    if manifest.get("schema_version") != FIXTURE_SCHEMA_VERSION:
        errors.append("known_bad.schema_version: unexpected value")
    if manifest.get("status") != "known_bad_only":
        errors.append("known_bad.status: must remain known_bad_only")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("known_bad.cases: expected nonempty array")
        return errors

    seen: set[str] = set()
    for index, case in enumerate(cases):
        label = f"known_bad.cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{label}: expected object")
            continue
        kind = case.get("kind")
        required = {"expected_error_contains", "id", "kind"}
        if kind == "policy_mutation":
            required.add("mutation")
        elif kind == "view_mutation":
            required.update({"dynamic_forbidden_literals", "mutation", "role"})
        elif kind == "assignment":
            required.add("assignments")
        errors.extend(_exact_keys(case, required, label))
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            errors.append(f"{label}: id must be a nonempty string")
        elif case_id in seen:
            errors.append(f"{label}: duplicate id {case_id!r}")
        else:
            seen.add(case_id)
        expected = case.get("expected_error_contains")
        if not isinstance(expected, str) or not expected:
            errors.append(f"{label}: expected_error_contains must be nonempty")
            continue
        try:
            observed = _fixture_case_errors(policy, case)
        except (KeyError, PolicyError, TypeError) as exc:
            errors.append(f"{label}: fixture cannot execute: {exc}")
            continue
        if not observed:
            errors.append(f"{label}: known-bad fixture was accepted")
        elif not any(expected in error for error in observed):
            errors.append(
                f"{label}: expected error {expected!r}; observed {observed}"
            )
    if seen != REQUIRED_FIXTURE_IDS:
        missing = sorted(REQUIRED_FIXTURE_IDS - seen)
        extra = sorted(seen - REQUIRED_FIXTURE_IDS)
        errors.append(
            f"known_bad.cases: fixture inventory drift; missing={missing}, extra={extra}"
        )
    return errors


def validate_current(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    try:
        policy = load_canonical_json(root / POLICY.relative_to(ROOT))
    except (ValueError, OSError) as exc:
        return [str(exc)]
    errors.extend(policy_errors(policy))
    if errors:
        return errors
    try:
        manifest = load_canonical_json(root / KNOWN_BAD.relative_to(ROOT))
    except (ValueError, OSError) as exc:
        return [str(exc)]
    errors.extend(fixture_manifest_errors(policy, manifest))
    for role in sorted(ROLE_ALLOWED):
        view = example_role_view(role)
        role_errors = role_view_errors(policy, role, view)
        errors.extend(f"known-good {error}" for error in role_errors)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate committed policy and known-bad fixtures (default)",
    )
    args = parser.parse_args(argv)
    _ = args.check
    errors = validate_current()
    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 1
    print(
        "PASS iter240 role-view policy: "
        f"{len(ROLE_ALLOWED)} views, {len(FIELD_CATALOG)} fields, "
        "all known-bad fixtures rejected"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
