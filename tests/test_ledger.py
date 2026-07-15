from __future__ import annotations

import pytest

from telos.ledger import LedgerValidationError, latest_next_action, validate_learning_record


def record(experiment_id: str = "iter01") -> dict:
    return {
        "experiment_id": experiment_id,
        "status": "pass",
        "result_path": "experiments/iter01/RESULT.md",
        "evidence_paths": ["experiments/iter01/proof/receipt.json"],
        "insight": "receipt validation is independently checkable",
        "next_action": "freeze first public-task slice",
    }


def test_learning_record_validates() -> None:
    validated = validate_learning_record(record())
    assert validated.experiment_id == "iter01"
    assert validated.next_action == "freeze first public-task slice"


def test_learning_record_accepts_honest_protocol_failure() -> None:
    data = record("iter197_protocol_failure")
    data["status"] = "fail"

    validated = validate_learning_record(data)

    assert validated.status == "fail"


def test_learning_record_requires_evidence() -> None:
    data = record()
    data["evidence_paths"] = []
    with pytest.raises(LedgerValidationError, match="evidence_paths"):
        validate_learning_record(data)


def test_latest_next_action_uses_newest_completed_record() -> None:
    first = validate_learning_record(record("iter01"))
    second_data = record("iter02")
    second_data["next_action"] = "run public task smoke"
    second = validate_learning_record(second_data)

    assert latest_next_action([second, first]) == "run public task smoke"


def test_latest_next_action_orders_iteration_numbers_numerically() -> None:
    older_data = record("iter99_external_verifier_telos_differential_fixture_materialization_after_design")
    older_data["next_action"] = "execute zero-provider deterministic strategies"
    older = validate_learning_record(older_data)
    newer_data = record("iter100_deterministic_strategy_execution_on_differential_fixtures_after_materialization")
    newer_data["next_action"] = "run deferred provider-backed LLM judge"
    newer = validate_learning_record(newer_data)

    assert latest_next_action([newer, older]) == "run deferred provider-backed LLM judge"
