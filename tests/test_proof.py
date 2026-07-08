from __future__ import annotations

import pytest

from telos.proof import ProofValidationError, receipt_digest, validate_receipt


def valid_receipt() -> dict:
    data = {
        "receipt_id": "r-demo-001",
        "task_id": "task-demo",
        "agent_id": "agent-under-test",
        "benchmark_id": "telos-demo",
        "status": "pass",
        "stated_goal": "Change one behavior and verify it against the acceptance criteria.",
        "acceptance_criteria": ["targeted test passes", "diff scope is limited"],
        "evidence": [
            {"kind": "test", "status": "pass", "artifact": "proof/test.log"},
            {"kind": "diff_scope", "status": "pass", "artifact": "proof/diff.txt"},
        ],
        "falsifiers": ["test fails", "unrelated files changed"],
    }
    data["sha256"] = receipt_digest(data)
    return data


def test_valid_receipt_passes() -> None:
    receipt = validate_receipt(valid_receipt())
    assert receipt.receipt_id == "r-demo-001"
    assert receipt.status == "pass"


def test_receipt_digest_excludes_sha_field() -> None:
    data = valid_receipt()
    original = receipt_digest(data)
    data["sha256"] = "wrong"
    assert receipt_digest(data) == original


def test_invalid_digest_fails() -> None:
    data = valid_receipt()
    data["sha256"] = "0" * 64
    with pytest.raises(ProofValidationError, match="sha256 mismatch"):
        validate_receipt(data)


def test_empty_evidence_fails() -> None:
    data = valid_receipt()
    data["evidence"] = []
    data["sha256"] = receipt_digest(data)
    with pytest.raises(ProofValidationError, match="evidence"):
        validate_receipt(data)
