from __future__ import annotations

import json
import subprocess

from scripts import build_iter213_receipt as receipt_builder
from scripts import validate_iter213_post_seal_validation_recovery as guard
from telos.proof import validate_receipt_v2


def test_iter213_preflight_preserves_predecessors_and_recovers_descendants() -> None:
    assert guard.validate(preflight=True) == []
    assert guard.iter210_guard.source_and_seal() == (
        guard.ITER210_SOURCE_COMMIT,
        guard.ITER210_SEAL_COMMIT,
    )
    assert guard.iter211_guard.source_and_seal() == (
        guard.ITER211_SOURCE_COMMIT,
        guard.ITER211_SEAL_COMMIT,
    )


def test_iter213_failure_record_is_exact_and_non_scientific() -> None:
    failure = json.loads(guard.FAILURE.read_text(encoding="utf-8"))

    assert failure["command"] == "pytest -q"
    assert (failure["passed"], failure["failed"]) == (648, 3)
    assert len(failure["failures"]) == 3
    assert set(failure["pre_recovery_actions"].values()) == {0}
    assert failure["iter211_mutated"] is False
    assert failure["iter212_mutated"] is False
    assert failure["scientific_result_changed"] is False


def test_iter213_receipt_is_artifact_bound_and_source_resolution_is_topological() -> None:
    receipt = validate_receipt_v2(receipt_builder.build_receipt())

    assert receipt.status == "pass"
    assert len(receipt.evidence) == len(receipt_builder.BINDINGS)
    source = receipt_builder.sealed_source_commit()
    if source is not None:
        row = subprocess.run(
            ["git", "rev-list", "--parents", "-n", "1", source],
            cwd=receipt_builder.ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.split()
        assert row == [source, receipt_builder.PREDECESSOR_SEAL]
