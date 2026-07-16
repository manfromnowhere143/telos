from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

from scripts import audit_iter207_claim_integrity as audit


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def outputs() -> dict[Path, dict]:
    return audit.build_outputs()


def test_correction_artifacts_reproduce_exactly(outputs: dict[Path, dict]) -> None:
    assert audit.check_outputs(outputs) == []
    assert set(outputs) == set(audit.OUTPUTS.values())


def test_strict_subreceipt_hashes_are_bound_by_ledger(outputs: dict[Path, dict]) -> None:
    ledger = outputs[audit.OUTPUTS["ledger"]]
    by_path = {row["path"]: row for row in ledger["strict_protocol_subreceipts"]}
    path = audit.OUTPUTS["iter195"]
    relative = path.relative_to(ROOT).as_posix()
    assert by_path[relative]["status"] == "fail"
    assert by_path[relative]["sha256"] == hashlib.sha256(
        audit._canonical(outputs[path])
    ).hexdigest()


def test_interpretive_correction_hash_is_bound_by_ledger(outputs: dict[Path, dict]) -> None:
    ledger = outputs[audit.OUTPUTS["ledger"]]
    rows = ledger["interpretive_correction_subreceipts"]
    assert len(rows) == 1
    path = audit.OUTPUTS["iter192"]
    assert rows[0]["path"] == path.relative_to(ROOT).as_posix()
    assert rows[0]["status"] == "conservative_novelty_fail"
    assert rows[0]["literal_trigger_status"] == "indeterminate"
    assert rows[0]["sha256"] == hashlib.sha256(audit._canonical(outputs[path])).hexdigest()


def test_custody_boundary_hash_binds_exact_public_relabels(outputs: dict[Path, dict]) -> None:
    ledger = outputs[audit.OUTPUTS["ledger"]]
    bindings = ledger["historical_public_surface_relabels"]
    expected_paths = {
        path.relative_to(ROOT).as_posix() for path in audit.HISTORICAL_RELABEL_PATHS
    }
    assert {row["path"] for row in bindings} == expected_paths
    assert all(row["iter206_seal_commit"] == audit.ITER206_SEAL_COMMIT for row in bindings)
    assert all(row["iter206_seal_sha256"] != row["current_sha256"] for row in bindings)
    guard = ledger["experiment_delta_guard"]
    assert set(guard["authorized_historical_relabels"]) == expected_paths
    assert set(guard["authorized_additive_iter206_terminal_nulls"]) == set(
        audit.ADDITIVE_ITER206_PATHS
    )
    assert guard["authorized_iter207_prefix"] == audit.ITER207_PREFIX


def test_custody_boundary_rejects_any_other_historical_experiment_delta() -> None:
    observed = audit._experiment_delta_statuses()
    assert audit._validate_experiment_delta(observed) == observed
    post_seal = dict(observed)
    post_seal[
        audit.ITER207_PREFIX + "proof/pre_execution_publication_safety.json"
    ] = "A"
    post_seal[audit.ITER207_PREFIX + "proof/raw/runtime_manifest.json"] = "A"
    assert audit._validate_experiment_delta(post_seal) == post_seal
    contaminated = dict(observed)
    contaminated["experiments/iter201_detectors_on_full_benchmark/proof/raw/tampered.json"] = "A"
    with pytest.raises(audit.ClaimIntegrityError, match="unauthorized historical experiment delta"):
        audit._validate_experiment_delta(contaminated)


def test_iter192_conservative_novelty_fail_preserves_literal_indeterminacy_and_recount(
    outputs: dict[Path, dict],
) -> None:
    receipt = outputs[audit.OUTPUTS["iter192"]]
    assert receipt["historical_recorded_status"] == "pass"
    assert receipt["standing_adjudication_status"] == "conservative_novelty_fail"
    assert receipt["literal_falsifier_5_status"] == "indeterminate"
    assert receipt["correction_id"] == "overbroad_conceptual_novelty"
    correction = receipt["correction"]
    assert correction["prior_semantic_baseline"] == [0, 20]
    assert correction["prior_baseline_and_v1_shared_instance_count"] == 19
    assert correction["iter151_rows_with_retained_patch_identity"] == 0
    assert correction["iter151_archived_report_count"] == 132
    assert correction["iter151_archived_reports_with_retained_patch_identity"] == 0
    assert correction["exact_v1_row_identity_in_iter151_established"] is None
    assert correction["literal_v1_specific_falsifier_triggered"] is None
    assert receipt["retained_findings"]["v1_rows_official_resolved_false"] == 40
    assert receipt["retained_findings"]["v1_rows_with_p2p_failure"] == 40
    findings = receipt["retained_findings"]
    assert findings["harness_resolved_hack_tagged_evaluations"] == 139
    assert findings["harness_resolved_unique_instance_ids"] == 65
    assert findings["iter152_generator_discarded_instance_ids"] == 23
    assert findings["iter152_discarded_and_harness_resolved_instance_ids"] == 17
    assert not findings["all_139_evaluations_bound_to_generator_discard_decisions"]


def test_iter195_has_exactly_three_failures_and_narrow_retained_result(
    outputs: dict[Path, dict],
) -> None:
    receipt = outputs[audit.OUTPUTS["iter195"]]
    assert receipt["strict_protocol_status"] == "fail"
    assert [failure["id"] for failure in receipt["protocol_failures"]] == [
        "gold_and_variant_hunks_entered_synthesis_prompt",
        "twenty_input_generator_validation_replaced",
        "raw_prompt_and_leakage_scan_custody_missing",
    ]
    assert receipt["retained_counts"] == {
        "certified_candidates_entering_phase_a": 16,
        "certified_equivalent_single_scenarios": 2,
        "clean_differing_single_scenarios": 10,
        "dedicated_raw_prompt_or_response_artifacts": 0,
        "estimated_spend_usd": 0.8,
        "gold_clean_single_scenarios": 13,
        "paired_execution_logs": 30,
        "provider_calls": 16,
        "scenario_failed": 2,
        "single_scenario_scripts": 15,
        "variant_errored": 1,
    }
    interpretation = receipt["retained_exploratory_interpretation"]
    assert "both hunks" in interpretation
    assert "not a passed synthesized-input oracle" in interpretation
    assert "does not establish global semantic inequivalence" in interpretation


def test_iter195_guard_fails_closed_if_historical_gold_prompt_evidence_disappears(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_git_blob = audit._git_blob
    runner = ROOT / "scripts/run_iter195_scenario_generator.py"

    def changed_blob(commit: str, path: Path) -> bytes:
        payload = real_git_blob(commit, path)
        if commit == "80f0c51fe145b6fe322d760e12508a58ea9ea502" and path == runner:
            return payload.replace(b"GOLD hunk:", b"REFERENCE hunk:")
        return payload

    monkeypatch.setattr(audit, "_git_blob", changed_blob)
    with pytest.raises(audit.ClaimIntegrityError, match="GOLD hunk"):
        audit.audit_iter195()


def test_iter199_method_and_chronology_are_not_overclaimed(outputs: dict[Path, dict]) -> None:
    correction = outputs[audit.OUTPUTS["ledger"]]["corrections"]["iter199"]
    assert correction["protocol_status"] == "registration_timing_not_independently_established"
    commits = {row["commit"] for row in correction["chronology"].values()}
    assert commits == {"03d199f49b69bcbe7948e223e26bdcd3ff2a32c9"}
    assert "gold and variant hunks" in correction["method"]
    assert correction["retained_counts"]["clean_reference_differentials"] == 12


def test_partial_attribution_and_disclosure_boundaries_are_explicit(
    outputs: dict[Path, dict],
) -> None:
    corrections = outputs[audit.OUTPUTS["ledger"]]["corrections"]
    assert corrections["iter196"]["gate_status"] == "partial_and_blocked"
    assert not corrections["iter196"]["both_detector_bar_met"]
    assert corrections["iter201"]["row_count"] == 4
    assert corrections["iter201"]["disposition"] == "disclosure_only_not_invalidation"
    assert corrections["iter200"]["original_logs"]["count"] == 54
    assert corrections["iter200"]["original_logs"]["embedded_claimed_run_id_count"] == 0
    assert corrections["iter200"]["backfill_attribution"]["run_id"] == 29422735843


def test_iter179_score_cost_excludes_diagnostic_guards(outputs: dict[Path, dict]) -> None:
    correction = outputs[audit.OUTPUTS["ledger"]]["corrections"]["iter179_cost_attribution"]
    assert correction["unrepaired_primary_result"] == {"majority_catch": [17, 40]}
    assert correction["score_producing_calls"] == {
        "count": 240,
        "estimated_spend_guard_usd": "13.128090",
        "components_usd": {
            "iter175_primary": "6.312690",
            "iter178_primary": "6.815400",
        },
    }
    assert correction["excluded_iter178_diagnostic_calls"] == {
        "count": 3,
        "estimated_spend_guard_usd": "0.189750",
    }
    assert correction["source_run_estimated_spend_guards_usd"]["sum"] == "13.317840"
    assert correction["later_repair_estimated_spend_guard_usd"] == "0.271800"
    assert correction["total_estimated_spend_guard_through_repair_usd"] == "13.589640"
    assert correction["diagnostic_recovery_excluded_from_primary_score"] is True
    assert "not provider invoices" in correction["cost_semantics"]


def test_iter202_unknown_usage_and_ceiling_charge_are_not_conflated(
    outputs: dict[Path, dict],
) -> None:
    correction = outputs[audit.OUTPUTS["ledger"]]["corrections"]["iter202"]
    interrupted = correction["interrupted_invocation"]
    assert interrupted["minimum_requests_initiated"] == 1
    assert interrupted["exact_completed_calls"] is None
    assert interrupted["exact_spend_usd"] is None
    assert interrupted["ceiling_charge"]["provider_calls"] == 53
    assert interrupted["ceiling_charge"]["estimated_spend_usd"] == 2.65
    assert correction["retained_later_run"]["total_calls"] == 92
    assert correction["conservative_ledger_total"] == {
        "charged_calls": 145,
        "estimated_or_charged_spend_usd": 7.25,
        "not_actual_usage_claim": True,
    }
    assert correction["N_k_u"] == {"N": None, "k": None, "u": None}


def test_audit_is_offline_only_and_active_gate_has_no_result() -> None:
    source = (ROOT / "scripts/audit_iter207_claim_integrity.py").read_text(encoding="utf-8")
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert not imported & {"urllib", "requests", "http.client", "socket"}
    assert "os.environ" not in source
    assert not (audit.EXP / "RESULT.md").exists()
    ledger = json.loads(audit.OUTPUTS["ledger"].read_text(encoding="utf-8"))
    assert ledger["generator_mode"] == "deterministic_offline_retrospective"
    assert ledger["investigation_side_effect_accounting"] == {
        "containers_or_scientific_executions": 0,
        "credential_reads_or_probes": 0,
        "network_call_scope": (
            "authenticated_read_only_github_metadata_gets_for_ci_projection_verification"
        ),
        "network_calls": 2,
        "provider_calls": 0,
        "remote_mutations": 0,
    }
