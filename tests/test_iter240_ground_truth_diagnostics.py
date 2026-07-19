"""Adversarial tests for iter240's independent post-freeze diagnostic guard."""

from __future__ import annotations

import ast
from copy import deepcopy
from decimal import Decimal
import hashlib
from pathlib import Path
import subprocess
from typing import Any

import pytest

from scripts import validate_iter240_ground_truth_diagnostics as guard
from scripts import validate_iter240_role_view_policy as role_guard


ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = (
    ROOT
    / "experiments/iter240_ground_truth_admission_design/fixtures"
    / "ground_truth_diagnostics_known_bad.json"
)

EXPECTED_CASE_IDS = {
    "absence_converted_to_negative",
    "author_view_candidate_leak",
    "candidate_exception_as_valid",
    "changed_source_bytes",
    "common_probability_removed",
    "concentration_field_reintroduced",
    "current_population_model_promoted",
    "design_as_spending_authority",
    "diagnostic_boundary_flag_forged",
    "duplicate_result_as_valid",
    "duplicate_selected_task",
    "error_sentinel_as_valid",
    "excluded_row_changed_to_valid",
    "favourable_branch_selected",
    "forged_candidate_unit_id",
    "forged_artifact_digest",
    "forged_cross_stratum_unit",
    "forged_duplicate_member_count",
    "future_replacement_sampling_allowed",
    "iid_assumption_removed",
    "illustrative_grid_claimed_complete",
    "immutable_boundary_uses_seal",
    "integer_boolean",
    "invented_frame_row_id",
    "invented_label_provenance",
    "invalid_decimal_display",
    "legacy_v1_output_present",
    "legacy_preflight_reintroduced",
    "libm_bit_exact",
    "missing_duplicate_group",
    "missing_digest",
    "missing_image",
    "missing_log",
    "missing_patch",
    "missing_pointer",
    "missing_source",
    "missing_specification",
    "model_as_human_ground_truth",
    "mutable_latest_execution",
    "nonzero_exit_as_valid",
    "old_scenario_recovered_endpoint",
    "one_endpoint_inflated",
    "pooled_strata",
    "premature_acquisition_link",
    "relaxed_allowlist",
    "repeated_patches_independent",
    "required_solve_attempts_reintroduced",
    "result_candidate_rows_called_patches",
    "result_counts_guaranteed",
    "result_current_population_inference",
    "result_v1_authority",
    "result_would_require",
    "retrospective_attempt_duplicate",
    "retrospective_certified_unattempted",
    "retrospective_stable_estimate",
    "sealed_predecessor_mutation",
    "semantic_rows_retained_for_extra",
    "selected_count_12",
    "selected_count_14",
    "selection_commit_replaced",
    "selector_delegates_outcome_read",
    "selector_reads_scenario",
    "selector_reads_status",
    "silent_selected_row_removal",
    "single_arm_result_as_valid",
    "solved_denominator",
    "stale_image",
    "task_endpoint_promoted",
    "timeout_as_valid",
    "truncated_output_as_valid",
    "unregistered_source_path",
    "unsafe_execution",
    "zero_yield_attainable",
}


@pytest.fixture(scope="module")
def catalogue() -> dict[str, dict[str, Any]]:
    document = guard.parse_json(
        CATALOGUE.read_bytes(),
        source=CATALOGUE.relative_to(ROOT).as_posix(),
        canonical=True,
    )
    assert document["schema_version"] == ("telos.iter240.ground_truth_diagnostics_known_bad.v1")
    cases = document["cases"]
    indexed = {case["id"]: case for case in cases}
    assert len(indexed) == len(cases)
    assert set(indexed) == EXPECTED_CASE_IDS
    assert all(case["mutation"] and case["expected_fragment"] for case in cases)
    return indexed


def _candidate(**overrides: Any) -> dict[str, Any]:
    row = {
        "certified_resolved": True,
        "gold_equivalent_after_terminal_lf_normalization": False,
        "outcome_complete": False,
    }
    row.update(overrides)
    return row


def _log(
    *,
    arm: str = "variant",
    body: list[str] | None = None,
    before: list[str] | None = None,
    image_digest: str | None = None,
) -> str:
    digest = image_digest or ("registry.example/test@sha256:" + "b" * 64)
    lines = [
        "IMAGE_ID=sha256:" + "a" * 64,
        f"IMAGE_REPO_DIGEST={digest}",
        f"APPLY_OK {arm}",
        *(before or []),
        ">>>>> Scenario Start",
        *(body if body is not None else ["RESULT={}", "SCENARIO_EXIT=0"]),
        ">>>>> Scenario End",
    ]
    return "\n".join(lines) + "\n"


def test_known_bad_catalogue_is_complete(
    catalogue: dict[str, dict[str, Any]],
) -> None:
    assert len(catalogue) == 73


def test_frozen_commit_and_selector_reconstruct() -> None:
    authority = guard.validate_commit_authority()
    census, rows = guard.validate_selection_freeze(authority)
    assert census["selected_count"] == len(rows) == 13
    assert len({row["instance_id"] for row in rows}) == 13
    assert guard.expected_selection_authority(authority)["selection_commit"] == (
        guard.SELECTION_COMMIT
    )
    boundary = guard.expected_immutable_source_boundary()
    assert boundary["commits"]["selection"] == {
        "commit": guard.SELECTION_COMMIT,
        "parents": [guard.ACTIVATION],
        "tree": guard.SELECTION_TREE,
    }
    assert boundary["source_blob_count"] == 163


def test_diagnostic_builder_bypasses_legacy_mutable_control() -> None:
    source = (ROOT / guard.DIAGNOSTIC_BUILDER).read_text(encoding="utf-8")
    assert guard.validate_diagnostic_builder_source(source) == []
    bad = """
def build_all():
    authority = _verify_selection_authority()
    legacy = load()
    legacy.preflight()
    legacy.build_missingness()
    legacy.build_frame()
    legacy.build_decision_curves()
    return authority
"""
    assert guard.validate_diagnostic_builder_source(bad)


@pytest.mark.parametrize(
    ("field", "numeric"),
    [
        ("certified_resolved", 1),
        ("gold_equivalent_after_terminal_lf_normalization", 0),
        ("outcome_complete", 0),
    ],
)
def test_selector_rejects_integer_boolean(field: str, numeric: int) -> None:
    row = _candidate()
    assert guard.select_independently([row], source="fixture") == [(0, row)]
    bad = dict(row)
    bad[field] = numeric
    with pytest.raises(guard.ValidationError, match="exact boolean"):
        guard.select_independently([bad], source="fixture")


@pytest.mark.parametrize(
    "source",
    [
        """
def select_missing_candidates(document):
    return [row for row in document["candidates"] if row["status"]]
""",
        """
def select_missing_candidates(document):
    return [row for row in document["candidates"] if row["scenario"]]
""",
        """
def select_missing_candidates(document):
    return helper(document["candidates"])
""",
    ],
)
def test_selector_source_rejects_outcome_reads_and_delegation(source: str) -> None:
    assert guard.validate_frozen_selector_source(source)


def test_active_frozen_selector_has_no_forbidden_path() -> None:
    source = guard._git(
        "show",
        f"{guard.SELECTION_COMMIT}:{guard.FROZEN_BUILDER.as_posix()}",
    ).decode("utf-8")
    assert guard.validate_frozen_selector_source(source) == []


def test_valid_scenario_arm_retains_only_digest_metadata() -> None:
    result = guard.classify_scenario_arm(_log(), "variant", source="fixture")
    assert result["apply_ok"] is True
    assert result["exit_code"] == 0
    assert result["exit_marker_count"] == 1
    assert result["image_id"] == "sha256:" + "a" * 64
    assert result["image_repository_digest"] == ("registry.example/test@sha256:" + "b" * 64)
    assert result["result_byte_count"] == 2
    assert result["result_count"] == result["result_like_line_count"] == 1
    assert result["result_payload_sha256"] == hashlib.sha256(b"{}").hexdigest()
    assert result["section_contract_failures"] == []
    assert result["section_error_sentinels"] == []
    assert result["whole_file_failure_sentinels"] == []
    assert result["valid"] is True
    assert result["validity_state"] == "valid"
    assert "{}" not in result.values()


@pytest.mark.parametrize(
    ("body", "before"),
    [
        (["Traceback (most recent call last):", "ValueError: bad", "SCENARIO_EXIT=1"], []),
        (["RESULT=x", "SCENARIO_EXIT=7"], []),
        (["RESULT=x", "RESULT=y", "SCENARIO_EXIT=0"], []),
        (["SCENARIO_EXIT=0"], []),
        (["RESULT=x", "SCENARIO_EXIT=0"], ["SCENARIO_TIMEOUT"]),
        (["RESULT=x", "SCENARIO_EXIT=0"], ["LOG_TRUNCATED"]),
    ],
)
def test_invalid_arm_classes_never_become_valid(
    body: list[str],
    before: list[str],
) -> None:
    result = guard.classify_scenario_arm(
        _log(body=body, before=before), "variant", source="fixture"
    )
    assert result["valid"] is False
    assert result["validity_state"] == "invalid"


def test_result_payload_is_bounded() -> None:
    payload = "x" * (guard.MAX_RESULT_BYTES + 1)
    result = guard.classify_scenario_arm(
        _log(body=[f"RESULT={payload}", "SCENARIO_EXIT=0"]),
        "variant",
        source="fixture",
    )
    assert result["valid"] is False
    assert result["result_byte_count"] == guard.MAX_RESULT_BYTES + 1


def test_not_evaluated_is_null_not_negative() -> None:
    result = guard.not_evaluated_arm(
        {
            "image_id": "sha256:" + "a" * 64,
            "image_repository_digest": "repo@sha256:" + "b" * 64,
        },
        reason="source_status:no_scenario:no_committed_scenario",
    )
    assert result["valid"] is None
    assert result["validity_state"] == "not_evaluated"
    assert result["apply_ok"] is result["exit_code"] is result["result_count"] is None


def test_mutable_latest_image_digest_is_rejected() -> None:
    with pytest.raises(guard.ValidationError, match="latest"):
        guard.classify_scenario_arm(
            _log(image_digest="registry.example/test:latest@sha256:" + "b" * 64),
            "variant",
            source="fixture",
        )


class _FakeReader:
    def __init__(self, data: bytes) -> None:
        self.data = data

    def bytes(self, _path: Path) -> bytes:
        return self.data

    def record(self, path: Path) -> dict[str, Any]:
        return {
            "git_blob_oid": "a" * 40,
            "path": path.as_posix(),
        }


def test_forged_and_missing_artifact_digest_are_rejected() -> None:
    path = Path("fixture.patch")
    data = b"patch\n"
    baseline = {
        "byte_count": len(data),
        "git_blob_oid": "a" * 40,
        "legacy_sha256_one_terminal_lf_removed": hashlib.sha256(data[:-1]).hexdigest(),
        "path": path.as_posix(),
        "sha256_file_bytes": hashlib.sha256(data).hexdigest(),
    }
    guard.validate_artifact(
        baseline,
        _FakeReader(data),  # type: ignore[arg-type]
        expected_path=path,
        source="fixture",
        legacy_one_lf=True,
    )
    for mutation in ("missing", "forged"):
        bad = dict(baseline)
        if mutation == "missing":
            bad.pop("sha256_file_bytes")
        else:
            bad["sha256_file_bytes"] = "f" * 64
        with pytest.raises(guard.ValidationError, match="schema|forged"):
            guard.validate_artifact(
                bad,
                _FakeReader(data),  # type: ignore[arg-type]
                expected_path=path,
                source="fixture",
                legacy_one_lf=True,
            )


def test_fisher_grid_known_rationals() -> None:
    assert guard.fisher_lower_tail(0) == guard.Fraction(145, 10912)
    assert guard.fisher_lower_tail(13) > guard.fisher_lower_tail(0)
    for x in range(14):
        value = guard.fisher_lower_tail(x)
        assert value.denominator > 0


def test_zero_event_crossings_and_decimal_contract() -> None:
    expected = {"0.10": 29, "0.05": 59, "0.02": 149, "0.01": 299}
    for threshold_text, n in expected.items():
        threshold = Decimal(threshold_text)
        assert (Decimal(1) - threshold) ** (n - 1) > Decimal("0.05")
        assert (Decimal(1) - threshold) ** n <= Decimal("0.05")
        rendered = guard.canonical_decimal(guard.zero_event_bound(n))
        guard.assert_decimal_close(rendered, guard.zero_event_bound(n), source="fixture")
    for invalid in ("not-a-number", "NaN", "Infinity", "1e-3"):
        with pytest.raises(guard.ValidationError, match="decimal"):
            guard.assert_decimal_close(invalid, guard.zero_event_bound(29), source="fixture")


@pytest.mark.parametrize(
    ("target", "numerator", "denominator", "expected"),
    [
        (1, 1, 7, 7),
        (29, 37, 64, 51),
        (13, 2, 5, 33),
        (299, 4, 5, 374),
        (1, 0, 1, None),
    ],
)
def test_symbolic_expected_count_rule_is_exact_for_rational_yields(
    target: int,
    numerator: int,
    denominator: int,
    expected: int | None,
) -> None:
    assert guard.expected_count_threshold(target, numerator, denominator) == expected


def test_libm_bit_exact_scan_rejects_new_bug_class() -> None:
    bad = """
import math
computed = math.pow(0.05, 1 / 29)
if computed == 0.9018:
    pass
"""
    good = """
from decimal import Decimal
computed = Decimal("0.05") ** (Decimal(1) / Decimal(29))
if abs(computed - Decimal("0.9018")) < Decimal("1e-4"):
    pass
"""
    assert guard.find_bit_exact_libm_comparisons(bad)
    assert guard.find_bit_exact_libm_comparisons(good) == []
    active = (ROOT / "scripts/validate_iter240_ground_truth_diagnostics.py").read_text()
    assert guard.find_bit_exact_libm_comparisons(active) == []


def test_frame_row_id_binds_provenance_and_full_patch_digest() -> None:
    baseline = guard.frame_row_id("hard_control", "iter200", "django__django-1", "a" * 64)
    assert len(baseline) == 64
    assert baseline != guard.frame_row_id("hard_control", "iter200", "django__django-1", "b" * 64)
    assert baseline != guard.frame_row_id(
        "operational_positive", "iter200", "django__django-1", "a" * 64
    )
    unit = guard.future_candidate_unit_id("django__django-1", "a" * 64)
    assert len(unit) == 64
    assert unit != guard.future_candidate_unit_id("django__django-1", "b" * 64)


def test_legacy_v1_presence_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(guard, "ROOT", tmp_path)
    relative = Path("proof/missingness_manifest.json")
    (tmp_path / relative).parent.mkdir(parents=True)
    (tmp_path / relative).write_text("{}\n", encoding="utf-8")
    with pytest.raises(guard.ValidationError, match="V1"):
        guard.validate_legacy_v1_absence([relative])
    (tmp_path / relative).unlink()
    guard.validate_legacy_v1_absence([relative])


def test_selection_authority_mutation_is_rejected() -> None:
    frozen = guard.validate_commit_authority()
    document = {"selection_authority": guard.expected_selection_authority(frozen)}
    guard.validate_selection_authority_field(document, frozen, source="fixture")
    bad = deepcopy(document)
    bad["selection_authority"]["selection_commit"] = guard.ACTIVATION
    with pytest.raises(guard.ValidationError, match="selection authority"):
        guard.validate_selection_authority_field(bad, frozen, source="fixture")


def test_catalogue_ids_are_literal_and_unique() -> None:
    tree = ast.parse(CATALOGUE.read_text(encoding="utf-8"))
    # JSON parses as a Python expression; this also catches accidental comments.
    assert len(tree.body) == 1


@pytest.fixture(scope="module")
def retained() -> dict[str, Any]:
    frozen = guard.validate_commit_authority()
    _census, selected = guard.validate_selection_freeze(frozen)
    manifest, _ = guard.load_canonical_object(guard.MANIFEST)
    taxonomy, _ = guard.load_canonical_object(guard.TAXONOMY)
    frame, _ = guard.load_canonical_object(guard.FRAME)
    curves, _ = guard.load_canonical_object(guard.CURVES)
    receipt, _ = guard.load_canonical_object(guard.RECEIPT)
    policy, policy_bytes = guard.load_canonical_object(guard.ROLE_POLICY)
    reader = guard.SourceReader()
    guard.validate_missingness_and_taxonomy(manifest, taxonomy, selected, reader)
    guard.validate_frame(frame, selected, reader, policy, policy_bytes)
    guard.validate_decision_curves(curves, reader)
    return {
        "curves": curves,
        "frame": frame,
        "frozen": frozen,
        "manifest": manifest,
        "policy": policy,
        "policy_bytes": policy_bytes,
        "reader": reader,
        "receipt": receipt,
        "selected": selected,
        "taxonomy": taxonomy,
    }


def _first_taxonomy_row(
    taxonomy: dict[str, Any],
    *,
    state: str | None = None,
) -> dict[str, Any]:
    return next(
        row for row in taxonomy["rows"] if state is None or row["availability_state"] == state
    )


def _validate_missing(retained: dict[str, Any], manifest: Any, taxonomy: Any) -> None:
    guard.validate_missingness_and_taxonomy(
        manifest,
        taxonomy,
        retained["selected"],
        retained["reader"],
    )


def _validate_frame(retained: dict[str, Any], frame: Any, policy: Any | None = None) -> None:
    selected_policy = policy if policy is not None else retained["policy"]
    policy_bytes = guard._canonical_json_bytes(selected_policy)
    guard.validate_frame(
        frame,
        retained["selected"],
        retained["reader"],
        selected_policy,
        policy_bytes,
    )


def _raise_role_errors(policy: dict[str, Any]) -> None:
    errors = role_guard.policy_errors(policy)
    if not errors:
        raise AssertionError("role mutation was not rejected")
    raise guard.ValidationError("; ".join(errors))


def _require_paired_valid(candidate_log: str, accepted_log: str) -> None:
    candidate = guard.classify_scenario_arm(
        candidate_log, "variant", source="known-bad candidate arm"
    )
    accepted = guard.classify_scenario_arm(accepted_log, "gold", source="known-bad accepted arm")
    if not (candidate["valid"] and accepted["valid"]):
        raise guard.ValidationError(
            "arm pair rejected by exact RESULT/error/exit/truncation contract"
        )
    raise AssertionError("known-bad arm pair was admitted as paired-valid")


def _temp_git_source(tmp_path: Path) -> tuple[str, Path]:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.name", "iter240-test"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "iter240@example.invalid"],
        cwd=tmp_path,
        check=True,
    )
    relative = Path("evidence/source.json")
    (tmp_path / relative).parent.mkdir(parents=True)
    (tmp_path / relative).write_text('{"value":"sealed"}\n', encoding="utf-8")
    subprocess.run(["git", "add", relative.as_posix()], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "sealed source"],
        cwd=tmp_path,
        check=True,
    )
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return commit, relative


def _validate_mutated_result(
    tmp_path: Path,
    old: str,
    new: str,
) -> None:
    source = (ROOT / guard.RESULT).read_text(encoding="utf-8")
    assert source.count(old) == 1
    target = tmp_path / guard.RESULT
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.replace(old, new), encoding="utf-8")
    guard.validate_result_boundary(tmp_path)


def dispatch_known_bad(
    case_id: str,
    retained: dict[str, Any],
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Closed mutation dispatcher: every catalogue entry reaches a live guard."""

    manifest = deepcopy(retained["manifest"])
    taxonomy = deepcopy(retained["taxonomy"])
    frame = deepcopy(retained["frame"])
    curves = deepcopy(retained["curves"])
    receipt = deepcopy(retained["receipt"])
    policy = deepcopy(retained["policy"])

    if case_id == "selected_count_12":
        manifest["selected_rows"].pop()
        _validate_missing(retained, manifest, taxonomy)
    elif case_id == "selected_count_14":
        manifest["selected_rows"].append(deepcopy(manifest["selected_rows"][0]))
        _validate_missing(retained, manifest, taxonomy)
    elif case_id == "duplicate_selected_task":
        manifest["selected_rows"][-1] = deepcopy(manifest["selected_rows"][0])
        _validate_missing(retained, manifest, taxonomy)
    elif case_id == "silent_selected_row_removal":
        manifest["selected_rows"].pop()
        taxonomy["rows"].pop()
        manifest["selected_count"] = taxonomy["selected_count"] = 12
        manifest["unique_task_count"] = 12
        _validate_missing(retained, manifest, taxonomy)
    elif case_id == "integer_boolean":
        guard.select_independently(
            [_candidate(certified_resolved=1)], source="known-bad integer boolean"
        )
    elif case_id in {"selector_reads_status", "selector_reads_scenario"}:
        field = "status" if case_id.endswith("status") else "scenario"
        problems = guard.validate_frozen_selector_source(
            "def select_missing_candidates(document):\n"
            f"    return document['candidates'][0]['{field}']\n"
        )
        if problems:
            raise guard.ValidationError("; ".join(problems))
        raise AssertionError("outcome-reading selector was not rejected")
    elif case_id == "selector_delegates_outcome_read":
        problems = guard.validate_frozen_selector_source(
            "def select_missing_candidates(document):\n    return helper(document['candidates'])\n"
        )
        if problems:
            raise guard.ValidationError("; ".join(problems))
        raise AssertionError("delegating selector was not rejected")
    elif case_id == "immutable_boundary_uses_seal":
        manifest["immutable_source_boundary"]["historical_seal_id"] = (
            "mutable-seal-derived-authority"
        )
        guard.validate_common_v2_fields(
            manifest,
            retained["frozen"],
            source="known-bad immutable boundary",
        )
    elif case_id == "diagnostic_boundary_flag_forged":
        manifest["diagnostic_builder_boundary"]["legacy_preflight_invoked"] = True
        guard.validate_common_v2_fields(
            manifest,
            retained["frozen"],
            source="known-bad diagnostic builder boundary",
        )
    elif case_id == "legacy_preflight_reintroduced":
        problems = guard.validate_diagnostic_builder_source(
            "def build_all():\n"
            "    authority = _verify_selection_authority()\n"
            "    legacy = load()\n"
            "    legacy.preflight()\n"
            "    legacy.build_missingness()\n"
            "    legacy.build_frame()\n"
            "    legacy.build_decision_curves()\n"
            "    return authority\n"
        )
        if problems:
            raise guard.ValidationError("; ".join(problems))
        raise AssertionError("legacy mutable preflight was not rejected")
    elif case_id == "missing_source":
        retained["reader"].bytes(Path("experiments/does_not_exist.json"))
    elif case_id in {
        "missing_patch",
        "missing_specification",
        "missing_log",
    }:
        artifact_name = {
            "missing_patch": "candidate_patch",
            "missing_specification": "specification",
            "missing_log": "candidate_execution_log",
        }[case_id]
        manifest["selected_rows"][0]["artifacts"].pop(artifact_name)
        _validate_missing(retained, manifest, taxonomy)
    elif case_id == "missing_image":
        guard.classify_scenario_arm(
            _log().replace("IMAGE_ID=" + "sha256:" + "a" * 64 + "\n", ""),
            "variant",
            source="known-bad missing image",
        )
    elif case_id == "missing_pointer":
        manifest["selected_rows"][0]["pointers"].pop("candidate")
        _validate_missing(retained, manifest, taxonomy)
    elif case_id in {"missing_digest", "forged_artifact_digest"}:
        artifact = manifest["selected_rows"][0]["artifacts"]["candidate_patch"]
        if case_id == "missing_digest":
            artifact.pop("sha256_file_bytes")
        else:
            artifact["sha256_file_bytes"] = "f" * 64
        _validate_missing(retained, manifest, taxonomy)
    elif case_id in {"changed_source_bytes", "sealed_predecessor_mutation"}:
        commit, relative = _temp_git_source(tmp_path)
        monkeypatch.setattr(guard, "ROOT", tmp_path)
        monkeypatch.setattr(guard, "PREDECESSOR", commit)
        if case_id == "changed_source_bytes":
            (tmp_path / relative).write_text('{"value":"mutable-worktree"}\n', encoding="utf-8")
        else:
            (tmp_path / relative).write_text('{"value":"changed-at-head"}\n', encoding="utf-8")
            subprocess.run(["git", "add", relative.as_posix()], cwd=tmp_path, check=True)
            subprocess.run(
                ["git", "commit", "-q", "-m", "mutate sealed source"],
                cwd=tmp_path,
                check=True,
            )
        guard.SourceReader().bytes(relative)
    elif case_id == "unregistered_source_path":
        receipt["source_inputs"].append(
            {
                **receipt["source_inputs"][0],
                "path": "experiments/unregistered.json",
            }
        )
        receipt["source_count"] += 1
        guard.validate_source_ledger(receipt, retained["reader"])
    elif case_id == "old_scenario_recovered_endpoint":
        taxonomy["future_primary_endpoint_rows"] = 1
        _validate_missing(retained, manifest, taxonomy)
    elif case_id in {
        "candidate_exception_as_valid",
        "single_arm_result_as_valid",
        "timeout_as_valid",
        "error_sentinel_as_valid",
        "nonzero_exit_as_valid",
        "duplicate_result_as_valid",
        "truncated_output_as_valid",
    }:
        accepted = _log(arm="gold")
        candidate_by_case = {
            "candidate_exception_as_valid": _log(
                body=[
                    "Traceback (most recent call last):",
                    "ValueError: candidate failed",
                    "SCENARIO_EXIT=1",
                ]
            ),
            "single_arm_result_as_valid": _log(body=["SCENARIO_EXIT=0"]),
            "timeout_as_valid": _log(
                before=["SCENARIO_TIMEOUT"],
            ),
            "error_sentinel_as_valid": _log(
                body=[
                    "Traceback (most recent call last):",
                    "RuntimeError: failed",
                    "SCENARIO_EXIT=1",
                ]
            ),
            "nonzero_exit_as_valid": _log(body=["RESULT=x", "SCENARIO_EXIT=9"]),
            "duplicate_result_as_valid": _log(body=["RESULT=x", "RESULT=y", "SCENARIO_EXIT=0"]),
            "truncated_output_as_valid": _log(
                before=["LOG_TRUNCATED"],
            ),
        }
        _require_paired_valid(candidate_by_case[case_id], accepted)
    elif case_id in {
        "absence_converted_to_negative",
        "excluded_row_changed_to_valid",
    }:
        row = _first_taxonomy_row(taxonomy, state="excluded_unsafe")
        value = case_id == "excluded_row_changed_to_valid"
        row["arm_summaries"]["candidate"]["valid"] = value
        row["arm_summaries"]["candidate"]["validity_state"] = "valid" if value else "invalid"
        _validate_missing(retained, manifest, taxonomy)
    elif case_id == "unsafe_execution":
        row = next(
            item
            for item in manifest["selected_rows"]
            if (
                item["source_run"],
                item["instance_id"],
            )
            == (
                taxonomy["rows"][0]["source_run"],
                taxonomy["rows"][0]["instance_id"],
            )
        )
        row["artifacts"]["historical_scenario"] = deepcopy(row["artifacts"]["candidate_patch"])
        _validate_missing(retained, manifest, taxonomy)
    elif case_id == "relaxed_allowlist":
        policy["broker_constraints"]["safety_allowlist_relaxation_allowed"] = True
        _raise_role_errors(policy)
    elif case_id == "mutable_latest_execution":
        guard.classify_scenario_arm(
            _log(image_digest="registry/test:latest@sha256:" + "b" * 64),
            "variant",
            source="known-bad latest image",
        )
    elif case_id == "stale_image":
        taxonomy["rows"][0]["arm_summaries"]["candidate"]["image_id"] = "sha256:" + "f" * 64
        _validate_missing(retained, manifest, taxonomy)
    elif case_id == "repeated_patches_independent":
        frame["unique_task_count"] = 55
        _validate_frame(retained, frame)
    elif case_id == "pooled_strata":
        frame["rows"][0]["operational_stratum"] = "pooled"
        _validate_frame(retained, frame)
    elif case_id == "missing_duplicate_group":
        frame["duplicate_task_candidate_patch_groups"].pop()
        _validate_frame(retained, frame)
    elif case_id == "forged_duplicate_member_count":
        frame["duplicate_task_candidate_patch_groups"][0]["member_count"] = 3
        _validate_frame(retained, frame)
    elif case_id == "forged_cross_stratum_unit":
        frame["cross_stratum_exact_duplicate"]["future_candidate_unit_id"] = "f" * 64
        _validate_frame(retained, frame)
    elif case_id == "forged_candidate_unit_id":
        frame["rows"][0]["future_candidate_unit_id"] = "f" * 64
        _validate_frame(retained, frame)
    elif case_id == "semantic_rows_retained_for_extra":
        frame["future_semantic_adjudication"]["operational_rows_retained_for"].append(
            "independent_vote"
        )
        _validate_frame(retained, frame)
    elif case_id == "task_endpoint_promoted":
        frame["future_semantic_adjudication"]["task_level_endpoint_aggregation"]["status"] = (
            "supported"
        )
        _validate_frame(retained, frame)
    elif case_id == "solved_denominator":
        curves["acquisition_sensitivity"]["retrospective_fresh_point_observation"][
            "certification_yield_fraction"
        ]["denominator"] = 62
        guard.validate_decision_curves(curves, retained["reader"])
    elif case_id == "favourable_branch_selected":
        curves["missingness_branches"].pop()
        guard.validate_decision_curves(curves, retained["reader"])
    elif case_id == "concentration_field_reintroduced":
        curves["missingness_branches"][0]["registered_strict_concentration_holds"] = True
        guard.validate_decision_curves(curves, retained["reader"])
    elif case_id == "iid_assumption_removed":
        curves["binomial_model_sensitivity"]["assumptions"][
            "independent_bernoulli_task_endpoints"
        ] = False
        guard.validate_decision_curves(curves, retained["reader"])
    elif case_id == "common_probability_removed":
        curves["binomial_model_sensitivity"]["assumptions"][
            "common_event_probability_across_tasks"
        ] = False
        guard.validate_decision_curves(curves, retained["reader"])
    elif case_id == "one_endpoint_inflated":
        curves["binomial_model_sensitivity"]["assumptions"][
            "completed_independently_adjudicated_endpoint_per_unique_task"
        ] = 2
        guard.validate_decision_curves(curves, retained["reader"])
    elif case_id == "current_population_model_promoted":
        curves["binomial_model_sensitivity"]["assumptions"][
            "population_inference_for_current_convenience_cohorts"
        ] = True
        guard.validate_decision_curves(curves, retained["reader"])
    elif case_id == "premature_acquisition_link":
        curves["binomial_model_sensitivity"]["acquisition_connection"]["status"] = "supported"
        guard.validate_decision_curves(curves, retained["reader"])
    elif case_id == "required_solve_attempts_reintroduced":
        target = curves["acquisition_sensitivity"]["illustrative_post_hypothesis_grid"]["points"][
            0
        ]["targets"][0]
        target["required_solve_attempts"] = target["expected_count_threshold_solve_attempts"]
        guard.validate_decision_curves(curves, retained["reader"])
    elif case_id == "zero_yield_attainable":
        curves["acquisition_sensitivity"]["symbolic_expected_count_rule"]["yield_zero_boundary"][
            "disposition_for_positive_target"
        ] = "finite"
        guard.validate_decision_curves(curves, retained["reader"])
    elif case_id == "retrospective_attempt_duplicate":
        observation = curves["acquisition_sensitivity"]["retrospective_fresh_point_observation"]
        observation["attempted_task_ids"][-1] = observation["attempted_task_ids"][0]
        guard.validate_decision_curves(curves, retained["reader"])
    elif case_id == "retrospective_certified_unattempted":
        curves["acquisition_sensitivity"]["retrospective_fresh_point_observation"][
            "certified_task_ids"
        ][0] = "django__django-999999"
        guard.validate_decision_curves(curves, retained["reader"])
    elif case_id == "future_replacement_sampling_allowed":
        curves["acquisition_sensitivity"]["future_unique_task_acquisition_contract"][
            "attempted_task_id_sampling"
        ] = "with_replacement"
        guard.validate_decision_curves(curves, retained["reader"])
    elif case_id == "retrospective_stable_estimate":
        curves["acquisition_sensitivity"]["retrospective_fresh_point_observation"][
            "stable_estimate"
        ] = True
        guard.validate_decision_curves(curves, retained["reader"])
    elif case_id == "illustrative_grid_claimed_complete":
        curves["acquisition_sensitivity"]["illustrative_post_hypothesis_grid"][
            "completeness_claim"
        ] = True
        guard.validate_decision_curves(curves, retained["reader"])
    elif case_id == "libm_bit_exact":
        problems = guard.find_bit_exact_libm_comparisons(
            "import math\nx = math.pow(.05, .5)\nassert x == .2\n"
        )
        if problems:
            raise guard.ValidationError("; ".join(problems))
        raise AssertionError("bit-exact libm comparison was not rejected")
    elif case_id == "author_view_candidate_leak":
        profile = next(iter(frame["row_visibility_profiles"].values()))
        permission = next(
            item
            for item in profile["field_permissions"]
            if item["frame_field_pointer"] == "/patch/sha256_file_bytes"
        )
        permission["allowed_future_roles"] = sorted(
            set(permission["allowed_future_roles"]) | {"consequence_author"}
        )
        permission["any_future_role_permitted"] = True
        _validate_frame(retained, frame)
    elif case_id == "model_as_human_ground_truth":
        policy["roles"]["semantic_adjudicator_1"]["authority_class"] = "model_consensus"
        _raise_role_errors(policy)
    elif case_id == "design_as_spending_authority":
        receipt["external_actions"]["cohort_acquisitions"] = 1
        guard.validate_materialization_receipt(receipt, retained["reader"])
    elif case_id == "selection_commit_replaced":
        document = {"selection_authority": guard.expected_selection_authority(retained["frozen"])}
        document["selection_authority"]["selection_commit"] = guard.ACTIVATION
        guard.validate_selection_authority_field(
            document, retained["frozen"], source="known-bad selection"
        )
    elif case_id == "invented_label_provenance":
        frame["rows"][0]["label_provenance"] = "invented_independent_label"
        _validate_frame(retained, frame)
    elif case_id == "invented_frame_row_id":
        frame["rows"][0]["candidate_row_id"] = "f" * 64
        _validate_frame(retained, frame)
    elif case_id == "invalid_decimal_display":
        curves["missingness_branches"][0]["exploratory_fisher"]["decimal_display"] = "not-a-number"
        guard.validate_decision_curves(curves, retained["reader"])
    elif case_id == "result_would_require":
        _validate_mutated_result(
            tmp_path,
            ("the expectation thresholds\nare `51`, `103`, `258`, and `518` attempts."),
            "the grid would require `51`, `103`, `258`, and `518` attempts.",
        )
    elif case_id == "result_counts_guaranteed":
        _validate_mutated_result(
            tmp_path,
            (
                "They are not requirements,\nprobability guarantees, stable yield "
                "estimates, independent-label counts,"
            ),
            (
                "The attempt counts are probability guarantees, stable yield "
                "estimates, independent-label counts,"
            ),
        )
    elif case_id == "result_candidate_rows_called_patches":
        _validate_mutated_result(
            tmp_path,
            (
                "| Operational stratum | Candidate rows | Unique task-patch "
                "entities | Unique tasks |"
            ),
            ("| Operational stratum | Patches | Unique task-patch entities | Unique tasks |"),
        )
    elif case_id == "result_current_population_inference":
        _validate_mutated_result(
            tmp_path,
            (
                "The current convenience cohorts do not satisfy the prerequisites "
                "for\npopulation inference"
            ),
            ("The current convenience cohorts support current population inference"),
        )
    elif case_id == "result_v1_authority":
        _validate_mutated_result(
            tmp_path,
            ("The unversioned V1 diagnostic outputs are intentionally absent and rejected:"),
            "The unversioned V1 diagnostic outputs remain diagnostic authority.",
        )
    elif case_id == "legacy_v1_output_present":
        monkeypatch.setattr(guard, "ROOT", tmp_path)
        relative = Path("proof/missingness_manifest.json")
        (tmp_path / relative).parent.mkdir(parents=True)
        (tmp_path / relative).write_text("{}\n", encoding="utf-8")
        guard.validate_legacy_v1_absence([relative])
    else:  # pragma: no cover - catalogue/dispatcher closure test forbids this.
        raise AssertionError(f"unhandled known-bad case: {case_id}")


@pytest.mark.parametrize("case_id", sorted(EXPECTED_CASE_IDS))
def test_every_registered_known_bad_fixture_fires(
    case_id: str,
    catalogue: dict[str, dict[str, Any]],
    retained: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    with pytest.raises(guard.ValidationError) as captured:
        dispatch_known_bad(
            case_id,
            retained,
            monkeypatch=monkeypatch,
            tmp_path=tmp_path,
        )
    expected = catalogue[case_id]["expected_fragment"].casefold()
    assert expected in str(captured.value).casefold()
