from __future__ import annotations

import json

from scripts import build_iter211_receipt as receipt_builder
from scripts import build_iter211_tcp1_packet as packet_builder
from scripts import validate_iter211_tcp1_materialization_preflight as guard
from telos.proof import validate_receipt_v2


def test_iter211_deterministic_packet_and_blocked_admission_are_clean() -> None:
    assert len(packet_builder.documents()) == 17
    assert len(packet_builder.fixed_seeds()) == 5
    assert len(set(packet_builder.fixed_seeds())) == 5
    assert guard.validate(preflight=True) == []
    assert receipt_builder.sealed_source_commit() == receipt_builder.ITER211_SOURCE_COMMIT
    assert guard.source_and_seal() == (
        receipt_builder.ITER211_SOURCE_COMMIT,
        receipt_builder.ITER211_SEAL_COMMIT,
    )

    admission = json.loads((packet_builder.PROOF / "admission_report.json").read_text())
    assert admission["materialization_preflight_status"] == "pass"
    assert admission["scientific_execution_admission"] == "blocked"
    assert admission["passed_gate_count"] == 2
    assert admission["blocked_gate_count"] == 9
    assert admission["execution_authorized"] is False


def test_iter211_receipt_semantics_are_blocked_even_when_artifacts_pass() -> None:
    receipt = validate_receipt_v2(receipt_builder.build_receipt())

    assert receipt.status == "blocked"
    assert len(receipt.evidence) == len(receipt_builder.BINDINGS)
    assert all(item["status"] == "pass" for item in receipt.evidence)
    assert "Admit TCP-1 scientific execution only after" in receipt.stated_goal


def test_iter211_has_no_task_reviewer_or_execution_identity_invention() -> None:
    tasks = json.loads((packet_builder.PROOF / "task_candidate_ledger.json").read_text())
    reviewers = json.loads((packet_builder.PROOF / "reviewer_ledger.json").read_text())
    bindings = json.loads((packet_builder.PROOF / "execution_binding_ledger.json").read_text())

    assert tasks["admitted_tasks"] == 0
    assert tasks["candidates"] == []
    assert all(slot["reviewer_id"] is None for slot in reviewers["slots"])
    assert all(
        value is None
        for section in ("model", "runtime", "environment", "hardware")
        for value in bindings[section].values()
    )
    assert bindings["execution_authorized"] is False
