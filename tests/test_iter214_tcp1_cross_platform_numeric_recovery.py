from __future__ import annotations

import json
import subprocess

import pytest

from scripts import build_iter214_receipt as receipt_builder
from scripts import validate_iter214_tcp1_cross_platform_numeric_recovery as guard
from telos.proof import validate_receipt_v2
from telos.tcp1 import wilson_interval


def test_iter214_preflight_is_pre_data_and_preserves_predecessors() -> None:
    assert guard.validate(preflight=True) == []
    assert guard.iter213_guard.source_and_seal() == (
        guard.ITER213_SOURCE,
        guard.ITER213_SEAL,
    )


def test_iter214_failure_record_binds_exact_remote_outcomes() -> None:
    failure = json.loads(guard.FAILURE.read_text(encoding="utf-8"))

    assert failure["draft_pull_request"] == 11
    assert failure["push_ci"]["run_id"] == 29505707609
    assert failure["pull_request_ci"]["run_id"] == 29505789397
    assert failure["linux_lower_endpoint"] == 2.7755575615628914e-17
    assert failure["other_tests_passed_per_job"] == 656
    assert failure["iter213_branch_mutated_after_observation"] is False
    assert failure["workflow_rerun_requested"] is False
    assert failure["scientific_result_changed"] is False


def test_iter214_wilson_amendment_is_exact_only_at_boundaries() -> None:
    zero_lower, zero_upper = wilson_interval(0, 10)
    full_lower, full_upper = wilson_interval(10, 10)
    interior_lower, interior_upper = wilson_interval(4, 10)

    assert zero_lower == 0.0
    assert zero_upper == pytest.approx(0.2775327998628892)
    assert full_lower == pytest.approx(1.0 - zero_upper)
    assert full_upper == 1.0
    assert interior_lower == pytest.approx(0.16818032970623614)
    assert interior_upper == pytest.approx(0.6873262302663417)


def test_iter214_receipt_is_artifact_bound_and_source_resolution_is_topological() -> None:
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
