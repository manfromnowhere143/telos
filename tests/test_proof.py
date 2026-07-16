from __future__ import annotations

import json

import pytest

from telos.proof import (
    RECEIPT_V2_SCHEMA,
    ProofValidationError,
    build_artifact_binding,
    evidence_closure_digest,
    load_receipt_v2,
    receipt_digest,
    receipt_v2_digest,
    validate_receipt,
    validate_receipt_v2,
    verify_receipt_v2_artifacts,
)


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


def valid_v2_receipt(tmp_path) -> dict:
    proof = tmp_path / "proof"
    proof.mkdir()
    (proof / "test.log").write_text("596 passed\n", encoding="utf-8")
    (proof / "scope.txt").write_text("paper and active API only\n", encoding="utf-8")
    evidence = [
        {
            "kind": "test",
            "status": "pass",
            "artifact": build_artifact_binding(
                tmp_path,
                "proof/test.log",
                media_type="text/plain",
                producer="pytest",
            ),
        },
        {
            "kind": "diff_scope",
            "status": "pass",
            "artifact": build_artifact_binding(
                tmp_path,
                "proof/scope.txt",
                media_type="text/plain",
                producer="git-diff-audit",
            ),
        },
    ]
    data = {
        "schema_version": RECEIPT_V2_SCHEMA,
        "receipt_id": "r-demo-v2",
        "task_id": "task-demo",
        "agent_id": "agent-under-test",
        "benchmark_id": "telos-demo",
        "status": "pass",
        "stated_goal": "Bind claims to exact evidence bytes.",
        "acceptance_criteria": ["every evidence file is hash-bound"],
        "evidence": evidence,
        "falsifiers": ["an evidence file is missing or differs"],
        "evidence_closure_sha256": evidence_closure_digest(evidence),
    }
    data["receipt_sha256"] = receipt_v2_digest(data)
    return data


def test_v2_receipt_validates_and_verifies_artifact_bytes(tmp_path) -> None:
    data = valid_v2_receipt(tmp_path)
    assert validate_receipt_v2(data).receipt_id == "r-demo-v2"
    assert verify_receipt_v2_artifacts(data, tmp_path).status == "pass"


def test_v2_artifact_tampering_fails(tmp_path) -> None:
    data = valid_v2_receipt(tmp_path)
    (tmp_path / "proof/test.log").write_text("595 passed, 1 failed\n", encoding="utf-8")
    with pytest.raises(ProofValidationError, match="artifact (byte count|sha256) mismatch"):
        verify_receipt_v2_artifacts(data, tmp_path)


def test_v2_closure_tampering_fails(tmp_path) -> None:
    data = valid_v2_receipt(tmp_path)
    data["evidence_closure_sha256"] = "0" * 64
    data["receipt_sha256"] = receipt_v2_digest(data)
    with pytest.raises(ProofValidationError, match="evidence closure mismatch"):
        validate_receipt_v2(data)


def test_v2_receipt_field_tampering_fails(tmp_path) -> None:
    data = valid_v2_receipt(tmp_path)
    data["stated_goal"] = "A different unbound goal."
    with pytest.raises(ProofValidationError, match="receipt_sha256 mismatch"):
        validate_receipt_v2(data)


def test_v2_rejects_duplicate_artifact_paths(tmp_path) -> None:
    data = valid_v2_receipt(tmp_path)
    duplicate = {
        "kind": "artifact",
        "status": "pass",
        "artifact": dict(data["evidence"][0]["artifact"]),
    }
    data["evidence"].append(duplicate)
    data["evidence_closure_sha256"] = evidence_closure_digest(data["evidence"])
    data["receipt_sha256"] = receipt_v2_digest(data)
    with pytest.raises(ProofValidationError, match="duplicate artifact path"):
        validate_receipt_v2(data)


def test_v2_rejects_symlink_and_parent_traversal(tmp_path) -> None:
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    proof = tmp_path / "proof"
    proof.mkdir()
    (proof / "linked.txt").symlink_to(outside)
    with pytest.raises(ProofValidationError, match="cannot read artifact safely"):
        build_artifact_binding(
            tmp_path,
            "proof/linked.txt",
            media_type="text/plain",
            producer="test",
        )
    with pytest.raises(ProofValidationError, match="not canonical"):
        build_artifact_binding(
            tmp_path,
            "../outside.txt",
            media_type="text/plain",
            producer="test",
        )


def test_v2_rejects_intermediate_directory_symlink(tmp_path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    (real / "artifact.txt").write_text("evidence\n", encoding="utf-8")
    (tmp_path / "linked-directory").symlink_to(real, target_is_directory=True)
    with pytest.raises(ProofValidationError, match="cannot read artifact safely"):
        build_artifact_binding(
            tmp_path,
            "linked-directory/artifact.txt",
            media_type="text/plain",
            producer="test",
        )


@pytest.mark.parametrize(
    "relative_path",
    (
        "/absolute.txt",
        "proof//test.log",
        "proof/./test.log",
        "proof\\test.log",
        "proof/control\x00.txt",
        "proof/control\n.txt",
    ),
)
def test_v2_rejects_noncanonical_or_control_character_paths(tmp_path, relative_path) -> None:
    with pytest.raises(ProofValidationError, match="artifact.path"):
        build_artifact_binding(
            tmp_path,
            relative_path,
            media_type="text/plain",
            producer="test",
        )


def test_load_v2_can_require_artifact_verification(tmp_path) -> None:
    data = valid_v2_receipt(tmp_path)
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps(data), encoding="utf-8")
    assert load_receipt_v2(receipt_path, artifact_root=tmp_path).receipt_id == "r-demo-v2"
