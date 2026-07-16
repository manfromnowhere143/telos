from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import validate_iter204_pre_dispatch_null as guard


ROOT = Path(__file__).resolve().parents[1]


def canonical(value: dict[str, object]) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def test_iter204_pre_dispatch_null_is_exact_and_science_free() -> None:
    assert guard.validate() == {
        "provider_calls": 0,
        "push_validation_runs": 2,
        "scientific_executions": 0,
        "workflow_dispatch_runs": 0,
    }


def test_local_422_claim_is_a_lower_bound_not_an_exact_request_count() -> None:
    document = json.loads(guard.NULL.read_text(encoding="utf-8"))
    rejection = document["dispatch_api_rejection"]

    assert rejection["request_count_exact"] is None
    assert rejection["request_count_lower_bound"] == 1
    assert rejection["locally_observed"] is True
    assert rejection["raw_response_committed"] is False
    assert rejection["error_message"] == guard.ERROR_MESSAGE


def test_guard_rejects_overstating_the_api_request_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    document = json.loads(guard.NULL.read_text(encoding="utf-8"))
    document["dispatch_api_rejection"]["request_count_exact"] = 1
    candidate = tmp_path / "null.json"
    candidate.write_text(canonical(document), encoding="utf-8")
    monkeypatch.setattr(guard, "NULL", candidate)

    with pytest.raises(
        guard.PreDispatchNullError,
        match="bounded local dispatch-rejection claim differs",
    ):
        guard.validate_normalized_null()


def test_push_parse_failures_are_preserved_separately_from_dispatch_count() -> None:
    push = json.loads(
        (guard.PUBLIC / "push_validation_runs.json").read_text(encoding="utf-8")
    )
    dispatch = json.loads(
        (guard.PUBLIC / "dispatch_runs.json").read_text(encoding="utf-8")
    )

    assert dispatch == {"total_count": 0, "workflow_runs": []}
    assert push["total_count"] == 2
    assert {row["id"] for row in push["runs"]} == set(guard.PUSH_RUN_IDS)
    assert {row["event"] for row in push["runs"]} == {"push"}
    assert {row["conclusion"] for row in push["runs"]} == {"failure"}
    assert {row["jobs_response"]["total_count"] for row in push["runs"]} == {0}
    assert {row["artifacts_response"]["total_count"] for row in push["runs"]} == {0}
    assert {
        row["logs_download_response"]["http_status"] for row in push["runs"]
    } == {404}


def test_reported_parse_location_binds_the_frozen_workflow() -> None:
    lines = guard.WORKFLOW.read_text(encoding="utf-8").splitlines()
    line = lines[317]

    assert line.index("${{ runner.temp }}") + 1 == 36
    assert "TELOS_ITER204_SMOKE_RECEIPT" in line
    assert guard.sha256(guard.WORKFLOW.read_bytes()) == guard.WORKFLOW_SHA256
    assert guard.sha256(guard.HYPOTHESIS.read_bytes()) == guard.HYPOTHESIS_SHA256
    assert (
        guard.sha256(guard.RUNTIME_MANIFEST.read_bytes())
        == guard.RUNTIME_MANIFEST_SHA256
    )


def test_result_never_collapses_push_records_into_zero_workflow_runs() -> None:
    result = guard.RESULT.read_text(encoding="utf-8")

    assert "zero workflow runs" not in result
    assert "no workflow run exists" not in result
    assert "zero iter204 `workflow_dispatch` runs" in result
    assert "two failed `push` workflow" in result
    assert "at least one locally observed" in result
