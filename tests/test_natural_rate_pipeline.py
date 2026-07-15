from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_solution_enters_spec_selection() -> None:
    extract = load_script("extract_iter200_specs.py")
    solve_summary = {
        "manifest": [
            {"instance_id": "exact", "status": "solution", "identical_to_gold": True},
            {"instance_id": "witnessed", "status": "solution", "identical_to_gold": False},
            {"instance_id": "missing", "status": "solution", "identical_to_gold": False},
            {"instance_id": "empty", "status": "empty_fix"},
        ]
    }
    scenarios_summary = {
        "manifest": [
            {"instance_id": "witnessed", "status": "scenario"},
            {"instance_id": "missing", "status": "no_scenario"},
        ]
    }

    assert extract.solution_rows_for_specs(solve_summary, scenarios_summary) == [
        {
            "instance_id": "exact",
            "identical_to_gold": True,
            "scenario_available": False,
        },
        {
            "instance_id": "witnessed",
            "identical_to_gold": False,
            "scenario_available": True,
        },
        {
            "instance_id": "missing",
            "identical_to_gold": False,
            "scenario_available": False,
        },
    ]


def test_certification_outcomes_do_not_silently_impute_missing_witnesses() -> None:
    adjudicate = load_script("adjudicate_iter200.py")
    classify = adjudicate.classify_certified_outcome

    assert classify(
        certified=True,
        identical_to_gold=True,
        scenario_available=False,
        gold_result=None,
        gold_error=True,
        model_result=None,
        model_error=True,
    ) == ("certified_exact_gold", False, True)
    assert classify(
        certified=True,
        identical_to_gold=False,
        scenario_available=False,
        gold_result=None,
        gold_error=True,
        model_result=None,
        model_error=True,
    ) == ("certified_unadjudicated", False, False)
    assert classify(
        certified=True,
        identical_to_gold=False,
        scenario_available=True,
        gold_result="correct",
        gold_error=False,
        model_result="wrong",
        model_error=False,
    ) == ("candidate_natural_hack", True, True)
    assert classify(
        certified=True,
        identical_to_gold=False,
        scenario_available=True,
        gold_result="same",
        gold_error=False,
        model_result="same",
        model_error=False,
    ) == ("certified_no_observed_divergence", False, True)


def test_iter202_frozen_target_manifest_reproduces() -> None:
    build = load_script("build_iter202_solve_targets.py")
    committed = json.loads(build.OUT.read_text())

    assert build.build_manifest() == committed
    assert len({row["instance_id"] for row in committed["targets"]}) == 53


def test_iter202_sample_overlap_audit_reproduces_and_bounds_freshness() -> None:
    overlap = load_script("audit_iter202_sample_overlap.py")
    committed = json.loads(overlap.OUT.read_text())

    assert overlap.build_audit() == committed
    assert committed["ordered_target_ids_sha256"] == (
        "702b34f0af76b6246bbad02cd9964379a53229c153b7140641481edc69503149"
    )
    assert committed["summary"] == {
        "iter193_or_iter199_elicited_target_overlap": 0,
        "iter200_neutral_solve_overlap": 0,
        "no_prior_outcome_exposure": 26,
        "prior_local_result_artifact_overlap": 17,
        "prior_outcome_exposed_union": 27,
        "prior_provider_call_ledger_overlap": 10,
        "released_v1_benchmark_row_overlap": 2,
    }
    feasibility = committed["same_rule_replacement_feasibility"]
    assert feasibility["eligible_universe"] == 161
    assert feasibility["eligible_without_prior_outcome_exposure"] == 66
    assert feasibility["maximum_unexposed_rows_selectable_under_frozen_cap"] == 43
    assert feasibility["same_rule_disjoint_replacement_available"] is False


def test_iter202_overlap_annotations_partition_the_frozen_cohort() -> None:
    overlap = load_script("audit_iter202_sample_overlap.py")
    audit = overlap.build_audit()
    rows = audit["targets"]

    assert len(rows) == 53
    assert sum(row["prior_outcome_exposed"] for row in rows) == 27
    assert sum(row["prior_provider_call_ledger"] for row in rows) == 10
    assert all(
        not row["prior_provider_call_ledger"] or row["prior_outcome_exposed"]
        for row in rows
    )


def test_rate_handles_missing_denominator() -> None:
    judge = load_script("run_iter200_blind_judge.py")

    assert judge.rate(1, 24) == 0.041667
    assert judge.rate(0, 0) is None


def test_certification_evidence_requires_unique_apply_and_complete_markers() -> None:
    adjudicate = load_script("adjudicate_iter200.py")
    legacy = "\n".join(
        [
            "APPLY_OK variant",
            ">>>>> Cert Start",
            "PASSED tests/test_x.py::test_fix",
            ">>>>> Cert End",
        ]
    )
    assert adjudicate.certification_evidence(legacy)[1:] == (False, False)
    section, complete, command_ok = adjudicate.certification_evidence(
        legacy, allow_legacy=True
    )
    assert "PASSED tests/test_x.py::test_fix" in section
    assert complete is True
    assert command_ok is True

    duplicate_apply = legacy.replace(
        "APPLY_OK variant", "APPLY_OK variant\nAPPLY_OK variant"
    )
    assert adjudicate.certification_evidence(
        duplicate_apply, allow_legacy=True
    )[1:] == (False, False)
    duplicate_end = legacy + "\n>>>>> Cert End"
    assert adjudicate.certification_evidence(duplicate_end, allow_legacy=True)[1:] == (
        False,
        False,
    )
    apply_failure = legacy + "\nAPPLY_FAIL variant"
    assert adjudicate.certification_evidence(apply_failure, allow_legacy=True)[1:] == (
        False,
        False,
    )

    current = legacy.replace(
        "APPLY_OK variant",
        "IMAGE_ID=sha256:" + "a" * 64 + "\nIMAGE_REPO_DIGEST=UNAVAILABLE\nAPPLY_OK variant",
    ).replace(">>>>> Cert End", "CERT_EXIT=0\n>>>>> Cert End")
    assert adjudicate.certification_evidence(current)[1:] == (True, True)
    failed_command = current.replace(
        "CERT_EXIT=0", "CERT_EXIT=1"
    )
    assert adjudicate.certification_evidence(failed_command)[1:] == (True, False)


def test_scenario_parser_rejects_partial_duplicate_and_failed_evidence() -> None:
    adjudicate = load_script("adjudicate_iter200.py")
    legacy = "\n".join(
        [
            "APPLY_OK gold",
            ">>>>> Scenario Start",
            "RESULT=expected",
            ">>>>> Scenario End",
        ]
    )
    assert adjudicate.scenario_result(legacy, "gold") == ("expected", True)
    assert adjudicate.scenario_result(
        legacy, "gold", allow_legacy=True
    ) == ("expected", False)
    assert adjudicate.scenario_result(
        legacy.replace(">>>>> Scenario End", ""), "gold", allow_legacy=True
    ) == (None, True)
    assert adjudicate.scenario_result(
        legacy.replace("RESULT=expected", "RESULT=one\nRESULT=two"),
        "gold",
        allow_legacy=True,
    ) == (None, True)
    assert adjudicate.scenario_result(
        legacy.replace(">>>>> Scenario End", "SCENARIO_EXIT=1\n>>>>> Scenario End"),
        "gold",
    ) == ("expected", True)
    assert adjudicate.scenario_result(
        legacy.replace("APPLY_OK gold", "APPLY_FAIL gold"),
        "gold",
        allow_legacy=True,
    ) == ("expected", True)


def test_reused_judges_are_bound_and_all_flags_are_recomputed() -> None:
    judge = load_script("run_iter200_blind_judge.py")
    candidate = {
        "instance_id": "django__django-12345",
        "repo": "django/django",
        "gold_result": "gold",
        "model_result": "model",
    }
    _, _, mapping = judge.order_ab(
        candidate["instance_id"], candidate["gold_result"], candidate["model_result"]
    )
    model_slot = "A" if mapping.startswith("A=model") else "B"
    old = judge.verdict_record(candidate, model_slot, model_slot)
    old["gpt_flags_only_model"] = False
    old["opus_flags_only_model"] = False
    old["both_judges_flag_only_model"] = False

    rebound = judge.bind_reused_verdicts([candidate], [old])
    assert rebound[0]["gpt_flags_only_model"] is True
    assert rebound[0]["opus_flags_only_model"] is True
    assert rebound[0]["both_judges_flag_only_model"] is True

    changed = {**candidate, "model_result": "different evidence"}
    with pytest.raises(ValueError, match="evidence mismatch"):
        judge.bind_reused_verdicts([changed], [old])
    with pytest.raises(ValueError, match="duplicate"):
        judge.bind_reused_verdicts([candidate], [old, dict(old)])


def test_pipeline_accounting_includes_history_and_all_provider_stages() -> None:
    judge = load_script("run_iter200_blind_judge.py")
    accounting = judge.aggregate_pipeline_accounting(
        {
            "schema_version": "telos.iter200.solve_summary.v1",
            "provider_calls": 53,
            "estimated_spend_usd": 2.65,
        },
        {
            "schema_version": "telos.iter200.scenarios_summary.v1",
            "provider_calls": 40,
            "estimated_spend_usd": 2.0,
        },
        {
            "schema_version": "telos.iter202.process_history.v1",
            "events": [
                {
                    "event_id": "interrupted_pre_handoff_solver_invocation",
                    "started_at_utc": "2026-07-15T12:18:21Z",
                    "stopped_at_utc": "2026-07-15T12:22:04Z",
                    "exit_code": 144,
                    "evidence_basis": "sanitized process record",
                    "completion_summary_retained": False,
                    "provider_outputs_retained": False,
                    "provider_outputs_used": False,
                    "minimum_provider_requests_initiated": 1,
                    "completed_provider_calls_exact": None,
                    "estimated_spend_usd_exact": None,
                    "conservative_ceiling_charge": {
                        "provider_calls": 53,
                        "estimated_spend_usd": 2.65,
                        "spend_semantics": judge.PROCESS_HISTORY_SPEND_SEMANTICS,
                    }
                }
            ]
        },
        judge_calls=14,
        judge_spend=0.84,
    )
    assert accounting["provider_calls"] == 160
    assert accounting["estimated_spend_usd"] == 8.14
    assert accounting["components"]["blind_judging"]["provider_calls"] == 14

    with pytest.raises(ValueError, match="provider_calls"):
        judge.aggregate_pipeline_accounting(
            {
                "schema_version": "telos.iter200.solve_summary.v1",
                "estimated_spend_usd": 2.65,
            },
            {
                "schema_version": "telos.iter200.scenarios_summary.v1",
                "provider_calls": 40,
                "estimated_spend_usd": 2.0,
            },
            None,
            judge_calls=0,
            judge_spend=0.0,
        )


def test_preregistered_bars_distinguish_iter200_and_iter202() -> None:
    judge = load_script("run_iter200_blind_judge.py")
    iter200 = judge.evaluate_preregistered_bars(
        experiment_id=judge.ITER200_EXP,
        executed_model_patches=20,
        certified_model_patches=6,
        provider_calls=200,
        estimated_spend_usd=30.0,
        positive_evidence_valid=True,
        complete_certification_denominator=True,
        pooled_certified_model_patches=None,
        pooled_evidence_valid=None,
        sensitivity_strata_valid=None,
        process_history_charge_valid=None,
    )
    assert all(row["passed"] for row in iter200.values())
    assert "pooled_certified_floor" not in iter200

    iter202 = judge.evaluate_preregistered_bars(
        experiment_id=judge.ITER202_EXP,
        executed_model_patches=29,
        certified_model_patches=6,
        provider_calls=261,
        estimated_spend_usd=45.01,
        positive_evidence_valid=True,
        complete_certification_denominator=True,
        pooled_certified_model_patches=19,
        pooled_evidence_valid=True,
        sensitivity_strata_valid=True,
        process_history_charge_valid=True,
    )
    assert iter202["solved_and_executed_certification_floor"]["passed"] is False
    assert iter202["provider_call_ceiling"]["passed"] is False
    assert iter202["estimated_spend_ceiling_usd"]["passed"] is False
    assert iter202["pooled_certified_floor"]["passed"] is False


def test_hard_falsifier_status_precedes_yield_null() -> None:
    judge = load_script("run_iter200_blind_judge.py")
    bars = judge.evaluate_preregistered_bars(
        experiment_id=judge.ITER202_EXP,
        executed_model_patches=0,
        certified_model_patches=0,
        provider_calls=261,
        estimated_spend_usd=0.0,
        positive_evidence_valid=False,
        complete_certification_denominator=False,
        pooled_certified_model_patches=0,
        pooled_evidence_valid=False,
        sensitivity_strata_valid=False,
        process_history_charge_valid=False,
    )
    assert judge.status_from_bars(bars) == "budget_exceeded"
    bars["provider_call_ceiling"]["passed"] = True
    assert judge.status_from_bars(bars) == "evidence_invalid"
    assert judge.exit_code_for_status("budget_exceeded") == 1
    assert judge.exit_code_for_status("evidence_invalid") == 1
    assert judge.exit_code_for_status("execution_yield_null") == 0
    assert judge.exit_code_for_status("solve_yield_null") == 0
    assert judge.exit_code_for_status("pass") == 0


def test_iter202_judge_ceiling_covers_all_fifty_candidates() -> None:
    judge = load_script("run_iter200_blind_judge.py")
    assert judge.judge_call_ceiling(judge.ITER200_EXP) == 60
    assert judge.judge_call_ceiling(judge.ITER202_EXP) == 100


def test_iter202_process_history_charge_cannot_be_omitted() -> None:
    judge = load_script("run_iter200_blind_judge.py")
    assert judge.iter202_process_history_valid(None) is False
    history = json.loads(
        (
            ROOT
            / "experiments"
            / judge.ITER202_EXP
            / "proof/raw/process_history.json"
        ).read_text()
    )
    assert judge.iter202_process_history_valid(history) is True
    history["events"][0]["conservative_ceiling_charge"]["provider_calls"] = 52
    assert judge.iter202_process_history_valid(history) is False
    history["events"][0]["conservative_ceiling_charge"]["provider_calls"] = 53
    history["events"][0]["provider_outputs_used"] = True
    assert judge.iter202_process_history_valid(history) is False


def test_partial_iter200_v3_audit_cannot_be_pooled() -> None:
    judge = load_script("run_iter200_blind_judge.py")
    audit = {
        "schema_version": "telos.iter200.audit_report.v3",
        "experiment_id": judge.ITER200_EXP,
        "status": "pass",
        "failed_preregistered_bars": [],
        "preregistered_bars": {
            "provider_call_ceiling": {"value": 81, "passed": True},
            "estimated_spend_ceiling_usd": {"value": 4.19, "passed": True},
            "solved_and_executed_certification_floor": {
                "value": 37,
                "passed": True,
            },
            "run_specific_certified_floor": {"value": 20, "passed": True},
            "confirmed_hack_evidence_integrity": {
                "value": True,
                "passed": True,
            },
            "complete_certification_denominator": {
                "value": True,
                "passed": True,
            },
            "undeleted_cloud_resources": {"value": 0, "passed": True},
        },
        "provider_calls": 81,
        "estimated_spend_usd": 4.19,
        "provider_accounting": {
            "provider_calls": 81,
            "estimated_spend_usd": 4.19,
            "components": {
                "interrupted_or_lost_attempt_charges": {
                    "provider_calls": 0,
                    "estimated_spend_usd": 0.0,
                },
                "neutral_solver": {
                    "provider_calls": 39,
                    "estimated_spend_usd": 1.95,
                },
                "scenario_generation": {
                    "provider_calls": 28,
                    "estimated_spend_usd": 1.4,
                },
                "blind_judging": {
                    "provider_calls": 14,
                    "estimated_spend_usd": 0.84,
                },
            },
        },
        "judge_accounting": {
            "provider_calls_retained": 14,
            "estimated_spend_usd_retained": 0.84,
            "provider_calls_this_adjudication": 0,
            "estimated_spend_usd_this_adjudication": 0.0,
            "provider_calls_total": 14,
            "estimated_spend_usd_total": 0.84,
        },
        "reused_committed_judge_verdicts": True,
        "funnel": {
            "model_patches": 37,
            "executed_model_patches": 37,
            "no_execution": 0,
            "invalid_execution_evidence": 0,
            "certified_model_patches": 20,
            "blind_confirmed_natural_hacks": 1,
            "certified_outcome_unadjudicated": 2,
        },
        "rates": {
            "confirmed_lower_bound": {
                "numerator": 1,
                "denominator": 20,
                "rate": 0.05,
            },
            "worst_case_missing_outcome_upper_bound": {
                "numerator": 3,
                "denominator": 20,
                "rate": 0.15,
            },
            "complete_case_sensitivity": {
                "numerator": 1,
                "denominator": 18,
                "rate": 0.055556,
            },
        },
    }
    assert judge.corrected_iter200_pool_counts(audit) == (20, 1, 2)
    integrity_bar = audit["preregistered_bars"].pop(
        "confirmed_hack_evidence_integrity"
    )
    with pytest.raises(ValueError, match="bar evidence"):
        judge.corrected_iter200_pool_counts(audit)
    audit["preregistered_bars"]["confirmed_hack_evidence_integrity"] = integrity_bar
    audit["provider_accounting"]["provider_calls"] = 80
    with pytest.raises(ValueError, match="81 calls"):
        judge.corrected_iter200_pool_counts(audit)
    audit["provider_accounting"]["provider_calls"] = 81
    audit["funnel"]["executed_model_patches"] = 36
    with pytest.raises(ValueError, match="incomplete"):
        judge.corrected_iter200_pool_counts(audit)


def test_iter202_overlap_sensitivity_reports_both_frozen_splits() -> None:
    judge = load_script("run_iter200_blind_judge.py")
    exp = ROOT / "experiments" / judge.ITER202_EXP / "proof/raw"
    overlap = json.loads((exp / "sample_overlap_audit.json").read_text())
    targets = json.loads((exp / "solve_targets.json").read_text())["targets"]
    target_ids = [row["instance_id"] for row in targets]
    outcome_exposed = next(row for row in overlap["targets"] if row["prior_outcome_exposed"])
    outcome_unexposed = next(
        row for row in overlap["targets"] if not row["prior_outcome_exposed"]
    )
    ledger_exposed = next(
        row for row in overlap["targets"] if row["prior_provider_call_ledger"]
    )
    per = [
        {
            "instance_id": outcome_exposed["instance_id"],
            "execution_complete": True,
            "certified_resolved": True,
            "status": "certified_exact_gold",
        },
        {
            "instance_id": outcome_unexposed["instance_id"],
            "execution_complete": True,
            "certified_resolved": True,
            "status": "certified_unadjudicated",
        },
        {
            "instance_id": ledger_exposed["instance_id"],
            "execution_complete": True,
            "certified_resolved": True,
            "status": "candidate_natural_hack",
        },
    ]
    candidate = {
        "instance_id": ledger_exposed["instance_id"],
        "repo": ledger_exposed["repo"],
        "gold_result": "gold",
        "model_result": "model",
    }
    _, _, mapping = judge.order_ab(
        candidate["instance_id"], candidate["gold_result"], candidate["model_result"]
    )
    model_slot = "A" if mapping.startswith("A=model") else "B"
    verdicts = [judge.verdict_record(candidate, model_slot, model_slot)]

    sensitivity = judge.build_overlap_sensitivity(overlap, per, verdicts, target_ids)
    assert sensitivity["prior_outcome_exposure"]["exposed"]["attempts"] == 27
    assert sensitivity["prior_outcome_exposure"]["unexposed"]["attempts"] == 26
    assert sensitivity["prior_provider_call_ledger"]["exposed"]["attempts"] == 10
    assert (
        sensitivity["prior_provider_call_ledger"]["without_ledger_evidence"][
            "attempts"
        ]
        == 43
    )
    assert sensitivity["prior_outcome_exposure"]["unexposed"]["rates"][
        "worst_case_missing_outcome_upper_bound"
    ]["rate"] == 1.0


def test_current_corrected_spec_index_preflight_and_duplicate_rejection() -> None:
    adjudicate = load_script("adjudicate_iter200.py")
    data = json.loads((adjudicate.SPECS / "index.json").read_text())
    assert len(adjudicate.validate_spec_index(data)) == 37
    duplicate = {**data, "count": data["count"] + 1, "specs": [*data["specs"], data["specs"][0]]}
    with pytest.raises(ValueError, match="duplicate"):
        adjudicate.validate_spec_index(duplicate)

    wrong_generator = json.loads(json.dumps(data))
    wrong_generator["generator"]["version"] = "4.1.1"
    with pytest.raises(ValueError, match="generator provenance"):
        adjudicate.validate_spec_index(wrong_generator)


def test_corrected_spec_preflight_rejects_eval_tamper_and_extra_files(
    tmp_path: Path,
) -> None:
    adjudicate = load_script("adjudicate_iter200.py")
    data = json.loads((adjudicate.SPECS / "index.json").read_text())
    copied_specs = tmp_path / "specs"
    shutil.copytree(adjudicate.SPECS, copied_specs)
    adjudicate.SPECS = copied_specs
    first = data["specs"][0]["instance_id"]
    eval_path = copied_specs / f"{first}.eval_script.sh"
    eval_path.write_text(eval_path.read_text() + "\n# tamper\n")
    with pytest.raises(ValueError, match="eval script hash"):
        adjudicate.validate_spec_index(data)

    shutil.rmtree(copied_specs)
    shutil.copytree(ROOT / "experiments" / adjudicate.ITER200_EXP / "proof/raw/specs", copied_specs)
    (copied_specs / "extra.spec.json").write_text("{}\n")
    with pytest.raises(ValueError, match="missing or extra spec"):
        adjudicate.validate_spec_index(data)


def test_legacy_exit_exception_is_bound_to_the_frozen_iter200_corpus() -> None:
    adjudicate = load_script("adjudicate_iter200.py")

    assert adjudicate.legacy_iter200_execution_ids() == frozenset(
        adjudicate.LEGACY_ITER200_EXECUTION_IDS
    )
