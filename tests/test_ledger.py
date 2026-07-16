from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from telos.ledger import (
    LedgerValidationError,
    discover_learning_record_paths,
    latest_next_action,
    load_learning_record,
    select_active_learning_record,
    validate_learning_record,
)


ROOT = Path(__file__).resolve().parents[1]


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


def test_discovery_includes_additive_adjudication_records(tmp_path) -> None:
    proof = tmp_path / "experiments/iter204_example/proof"
    proof.mkdir(parents=True)
    canonical = proof / "learning_record.json"
    terminal = proof / "learning_record.pre_dispatch_null.json"
    admission = proof / "learning_record.pre_dispatch_admission_null.json"
    ignored = proof / "other.json"
    canonical.write_text("{}\n", encoding="utf-8")
    terminal.write_text("{}\n", encoding="utf-8")
    admission.write_text("{}\n", encoding="utf-8")
    ignored.write_text("{}\n", encoding="utf-8")

    assert discover_learning_record_paths(tmp_path) == [
        canonical,
        admission,
        terminal,
    ]


def test_additive_terminal_record_supersedes_pending_next_action() -> None:
    pending_data = record("iter204_recovery")
    pending_data["status"] = "pending"
    pending_data["next_action"] = "dispatch iter204"
    terminal_data = record("iter204_recovery_pre_dispatch_null")
    terminal_data["status"] = "null"
    terminal_data["next_action"] = "do not dispatch iter204; advance to iter205"

    assert latest_next_action(
        [validate_learning_record(pending_data), validate_learning_record(terminal_data)]
    ) == "do not dispatch iter204; advance to iter205"


def test_active_gate_selects_iter206_instead_of_closed_iter205() -> None:
    iter205 = record("iter205_recovery_pre_dispatch_null")
    iter205["status"] = "null"
    iter205["result_path"] = "experiments/iter205_recovery/RESULT.md"
    iter205["next_action"] = "do not dispatch iter205"
    iter206 = record("iter206_recovery")
    iter206["status"] = "pending"
    iter206["result_path"] = "experiments/iter206_recovery/HYPOTHESIS.md"
    iter206["next_action"] = "validate and dispatch iter206 once"
    active = select_active_learning_record(
        [validate_learning_record(iter205), validate_learning_record(iter206)],
        "experiments/iter206_recovery/HYPOTHESIS.md",
    )

    assert active.experiment_id == "iter206_recovery"
    assert active.next_action == "validate and dispatch iter206 once"


@pytest.mark.parametrize("failure", ["missing", "duplicate", "completed", "mismatch"])
def test_active_gate_binding_fails_closed(failure: str) -> None:
    gate = "experiments/iter206_recovery/HYPOTHESIS.md"
    data = record("iter206_recovery")
    data["status"] = "pending"
    data["result_path"] = gate
    rows = [validate_learning_record(data)]
    if failure == "missing":
        rows = []
    elif failure == "duplicate":
        rows.append(validate_learning_record(data))
    elif failure == "completed":
        data["status"] = "null"
        rows = [validate_learning_record(data)]
    elif failure == "mismatch":
        data["experiment_id"] = "iter206_other"
        rows = [validate_learning_record(data)]

    with pytest.raises(LedgerValidationError):
        select_active_learning_record(rows, gate)


def test_committed_active_learning_record_is_iter206() -> None:
    contract = json.loads((ROOT / "mission/loop.json").read_text(encoding="utf-8"))
    records = [
        load_learning_record(path, root=ROOT)
        for path in discover_learning_record_paths(ROOT)
    ]

    active = select_active_learning_record(records, contract["active_gate"])

    assert active.experiment_id == "iter206_iter205_admission_history_recovery"
    assert active.status == "pending"


def test_validator_prints_active_iter206_action_not_obsolete_iter205_dispatch() -> None:
    completed = subprocess.run(
        ["python3", "scripts/validate_learning_ledger.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "active=iter206_iter205_admission_history_recovery" in completed.stdout
    assert "active_next=Finalize and adversarially validate all iter206 source" in completed.stdout
    assert "dispatch iter205" not in completed.stdout
