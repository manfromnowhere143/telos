from __future__ import annotations

import json

from scripts import build_iter209_receipt as iter209_receipt
from scripts import validate_iter209_publication_ci_recovery as iter209_guard
from scripts import validate_iter210_pr_synthetic_merge_recovery as iter210_guard


def test_iter209_descendant_target_is_exact_public_seal() -> None:
    assert iter209_guard.validation_target() == iter209_guard.ITER209_SEAL_COMMIT
    iter209_guard.validate_predecessor_and_experiment_delta()
    iter209_guard.validate_receipt_and_source_closure()


def test_iter209_sealed_receipt_is_git_blob_bound_and_not_rebuilt() -> None:
    assert iter209_receipt.sealed_descendant() is True
    assert iter209_receipt.verify_sealed_receipt() == 17


def test_iter210_preflight_is_clean() -> None:
    assert iter210_guard.source_and_seal() == (
        iter210_guard.ITER210_SOURCE_COMMIT,
        iter210_guard.ITER210_SEAL_COMMIT,
    )
    assert iter210_guard.validate(preflight=True) == []


def test_iter210_diagnosis_records_green_push_and_failed_pr_only() -> None:
    diagnosis = json.loads(iter210_guard.DIAGNOSIS.read_text(encoding="utf-8"))
    attempt = diagnosis["failed_publication_attempt"]
    assert attempt["push_ci"]["conclusion"] == "success"
    assert attempt["pull_request_ci"]["conclusion"] == "failure"
    assert set(diagnosis["actions_during_iter210_before_publication"].values()) == {0}
