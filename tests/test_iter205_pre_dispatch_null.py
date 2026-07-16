from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import validate_iter205_pre_dispatch_null as guard


def canonical(value: dict[str, object]) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def test_iter205_pre_dispatch_null_is_exact_and_science_free() -> None:
    assert guard.validate() == {
        "dispatch_requests": 0,
        "iter204_push_parse_failures": 4,
        "iter205_workflow_runs": 0,
        "provider_calls": 0,
        "scientific_executions": 0,
    }


def test_iter205_histories_are_empty_but_iter204_history_is_not() -> None:
    all_runs = json.loads((guard.PUBLIC / "all_runs.json").read_text())
    dispatch_runs = json.loads((guard.PUBLIC / "dispatch_runs.json").read_text())
    iter204 = json.loads((guard.PUBLIC / "iter204_history.json").read_text())

    assert all_runs == {"total_count": 0, "workflow_runs": []}
    assert dispatch_runs == {"total_count": 0, "workflow_runs": []}
    assert iter204["total_count"] == 4
    assert {row["id"] for row in iter204["runs"]} == set(guard.ITER204_RUN_IDS)
    assert {row["event"] for row in iter204["runs"]} == {"push"}
    assert {row["jobs_response"]["total_count"] for row in iter204["runs"]} == {0}
    assert {
        row["artifacts_response"]["total_count"] for row in iter204["runs"]
    } == {0}
    assert {
        row["logs_download_response"]["http_status"] for row in iter204["runs"]
    } == {404}


def test_terminal_learning_closes_iter205_without_mutating_pending_record() -> None:
    terminal = json.loads(guard.TERMINAL_LEARNING.read_text())

    assert terminal["status"] == "null"
    assert terminal["supersedes"].endswith("/proof/learning_record.json")
    assert terminal["next_action"] == guard.TERMINAL_NEXT_ACTION
    assert terminal["next_action"].startswith("Do not dispatch or rerun iter205")
    assert guard.sha256(guard.PENDING_LEARNING.read_bytes()) == (
        guard.PENDING_LEARNING_SHA256
    )


def test_later_learning_records_cannot_reopen_iter205(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[str] = []
    real_latest = guard.latest_next_action

    def bounded_latest(records):
        observed.extend(record.experiment_id for record in records)
        return real_latest(records)

    monkeypatch.setattr(guard, "latest_next_action", bounded_latest)
    guard.validate_terminal_learning_record()

    assert observed == [
        "iter205_iter204_workflow_context_recovery",
        "iter205_iter204_workflow_context_recovery_pre_dispatch_admission_null",
    ]


def test_guard_rejects_nonempty_iter205_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    public = tmp_path / "public"
    public.mkdir()
    for source in guard.PUBLIC.iterdir():
        if source.is_file():
            (public / source.name).write_bytes(source.read_bytes())
    mutated = {"total_count": 1, "workflow_runs": [{"id": 1}]}
    (public / "all_runs.json").write_text(canonical(mutated))
    monkeypatch.setattr(guard, "PUBLIC", public)
    monkeypatch.setattr(guard, "MANIFEST", public / "manifest.json")
    monkeypatch.setattr(
        guard,
        "PUBLIC_MANIFEST_SHA256",
        guard.sha256((public / "manifest.json").read_bytes()),
    )

    with pytest.raises(guard.PreDispatchNullError):
        guard.validate_public_metadata()


def test_guard_rejects_scientific_denominator_or_outcome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    document = json.loads(guard.NULL.read_text())
    document["scientific_evidence"]["n"] = 0
    candidate = tmp_path / "null.json"
    candidate.write_text(canonical(document))
    monkeypatch.setattr(guard, "NULL", candidate)

    with pytest.raises(
        guard.PreDispatchNullError,
        match="scientific-null boundary differs",
    ):
        guard.validate_normalized_null()


def test_guard_rejects_request_or_api_rejection_claims(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    document = json.loads(guard.NULL.read_text())
    document["dispatch_request"]["attempted"] = True
    candidate = tmp_path / "null.json"
    candidate.write_text(canonical(document))
    monkeypatch.setattr(guard, "NULL", candidate)

    with pytest.raises(
        guard.PreDispatchNullError,
        match="admission-null identity differs",
    ):
        guard.validate_normalized_null()


def test_result_distinguishes_no_iter205_dispatch_from_iter204_push_rows() -> None:
    result = " ".join(guard.RESULT.read_text().split())

    assert "No iter205 dispatch request was issued" in result
    assert "no dispatch API response or rejection exists" in result
    assert "There was no iter205 API request" not in result
    assert "zero workflow runs" not in result
    assert "current iter204 history has four records" in result
    assert "contributes no `N`, `k`, or `u`; those quantities are absent, not zero" in result
