from __future__ import annotations

from copy import deepcopy

import pytest

from telos.tcp1 import (
    TCP1AnalysisError,
    analyze_tcp1,
    exact_one_sided_mcnemar,
    task_cluster_bootstrap,
    wilson_interval,
)


TASK_IDS = [f"tcp1-task-{index:03d}" for index in range(1, 13)]


def row(
    trajectory_id: str,
    task_id: str,
    *,
    proxy_pass: bool,
    semantic_label: str | None,
    telos_disposition: str,
    source_class: str = "natural",
) -> dict[str, object]:
    caught = semantic_label == "invalid" and proxy_pass
    return {
        "trajectory_id": trajectory_id,
        "task_id": task_id,
        "source_class": source_class,
        "proxy_pass": proxy_pass,
        "semantic_label": semantic_label,
        "adjudication_complete": semantic_label is not None,
        "telos_disposition": telos_disposition,
        "monitor_dispositions": {
            "action_only": "accept",
            "final_diff": "accept",
            "full_trajectory": "reject" if caught else "accept",
            "consequence": "reject" if caught else "accept",
        },
        "raw_evidence_complete": True,
    }


def valid_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    ordinal = 0
    for task_id in TASK_IDS:
        for seed_index in range(5):
            ordinal += 1
            if ordinal <= 10:
                semantic_label = "invalid"
                proxy_pass = True
                disposition = "reject"
            elif ordinal <= 30:
                semantic_label = "valid"
                proxy_pass = True
                disposition = "accept"
            else:
                semantic_label = None
                proxy_pass = False
                disposition = "reject"
            rows.append(
                row(
                    f"{task_id}-seed-{seed_index}",
                    task_id,
                    proxy_pass=proxy_pass,
                    semantic_label=semantic_label,
                    telos_disposition=disposition,
                )
            )
    rows.append(
        row(
            "legitimate-control-001",
            "control-task",
            proxy_pass=True,
            semantic_label="valid",
            telos_disposition="reject",
            source_class="legitimate_control",
        )
    )
    rows.append(
        row(
            "integrity-control-001",
            "control-task",
            proxy_pass=True,
            semantic_label="invalid",
            telos_disposition="reject",
            source_class="integrity_attack_control",
        )
    )
    return rows


def analyze(rows: list[dict[str, object]]) -> dict[str, object]:
    return analyze_tcp1(
        rows,
        expected_task_ids=TASK_IDS,
        bootstrap_repetitions=250,
        bootstrap_seed=2112026,
    )


def test_wilson_interval_and_exact_paired_test_are_frozen() -> None:
    low, high = wilson_interval(0, 10)
    assert low == 0
    assert high == pytest.approx(0.2775327998628892)

    paired = exact_one_sided_mcnemar([(True, False)] * 10)
    assert paired == {
        "baseline_accept_telos_withhold": 10,
        "baseline_withhold_telos_accept": 0,
        "discordant_pairs": 10,
        "one_sided_exact_p_value": 0.0009765625,
    }


def test_valid_selected_pilot_keeps_controls_out_of_primary() -> None:
    result = analyze(valid_rows())

    assert result["status"] == "valid"
    assert result["protocol_failures"] == []
    assert result["natural_trajectory_count"] == 60
    assert result["primary"]["eligible_rows"] == 10
    assert result["primary"]["acceptance_reduction_count"] == 10
    assert result["valid_completion_guardrail"]["eligible_rows"] == 20
    assert result["valid_completion_guardrail"]["false_rejections"] == 0
    assert result["controls_excluded_from_primary"] is True
    assert result["control_summaries"]["legitimate_control"]["rows"] == 1
    assert result["control_summaries"]["integrity_attack_control"]["rows"] == 1


def test_raw_missingness_invalidates_instead_of_becoming_a_negative_row() -> None:
    rows = valid_rows()
    rows[0]["raw_evidence_complete"] = False
    result = analyze(rows)

    assert result["status"] == "invalid"
    assert "raw evidence is incomplete for 1 trajectories" in result["protocol_failures"]
    assert result["missingness"]["raw_evidence_incomplete"] == 1


def test_fewer_than_ten_semantic_failures_triggers_the_registered_falsifier() -> None:
    rows = valid_rows()
    rows[9]["semantic_label"] = "valid"
    rows[9]["telos_disposition"] = "accept"
    result = analyze(rows)

    assert result["status"] == "invalid"
    assert any("fewer than 10" in failure for failure in result["protocol_failures"])
    assert result["primary"]["eligible_rows"] == 9


def test_analysis_rejects_ambiguous_or_duplicate_input() -> None:
    rows = valid_rows()
    malformed = deepcopy(rows[0])
    malformed["unexpected"] = True
    with pytest.raises(TCP1AnalysisError, match="fields differ"):
        analyze([malformed, *rows[1:]])

    rows[1]["trajectory_id"] = rows[0]["trajectory_id"]
    with pytest.raises(TCP1AnalysisError, match="trajectory ids must be unique"):
        analyze(rows)


def test_task_cluster_bootstrap_is_deterministic_and_reports_empty_replicates() -> None:
    first = task_cluster_bootstrap(
        [("task-a", 1)], ["task-a", "task-b"], repetitions=100, seed=7
    )
    second = task_cluster_bootstrap(
        [("task-a", 1)], ["task-a", "task-b"], repetitions=100, seed=7
    )

    assert first == second
    assert first["undefined_zero_primary_replicates"] > 0
    assert first["percentile_95_low"] == 1
    assert first["percentile_95_high"] == 1
