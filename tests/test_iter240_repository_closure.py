from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts/validate_iter240_repository_closure.py"
CAPTURE_PATH = ROOT / "scripts/capture_iter240_repository_closure.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


validator = load_module(VALIDATOR_PATH, "test_iter240_repository_closure_validator")
capture = load_module(CAPTURE_PATH, "test_iter240_repository_closure_capture")


def test_exact_get_only_plan_agrees_across_instruments() -> None:
    assert tuple(validator.ENDPOINTS) == tuple(capture.ENDPOINTS)
    assert len(validator.ENDPOINTS) == 13
    assert all(row[1].startswith("/repos/manfromnowhere143/telos/") for row in validator.ENDPOINTS)
    assert validator.request_plan() == capture.request_plan()
    assert validator.expected_counts() == {
        "GET": 13,
        "POST": 0,
        "PUT": 0,
        "PATCH": 0,
        "DELETE": 0,
    }


def test_safe_fixture_and_every_known_bad_case() -> None:
    assert validator.fixture_failures(ROOT) == []


def test_safe_fixture_allows_only_null_or_exact_rest_merge_sha() -> None:
    safe = validator.read_json(validator.SAFE_FIXTURE, label="safe fixture")
    exact = deepcopy(safe)
    exact["pull_request"]["rest_merge_commit_sha"] = validator.MERGE
    assert validator.projection_failures(exact, expected=safe) == []
    wrong = deepcopy(safe)
    wrong["pull_request"]["rest_merge_commit_sha"] = "0" * 40
    assert any("REST merge" in item for item in validator.projection_failures(wrong, expected=safe))


def test_local_authorization_and_sealed_iter240_bytes() -> None:
    assert validator.repository_failures(ROOT) == []


def test_attempt_marker_freezes_required_instruments() -> None:
    assert capture.INSTRUMENT_PATHS == (
        "experiments/iter241_iter240_repository_closure/HYPOTHESIS.md",
        "experiments/iter241_iter240_repository_closure/fixtures/repository_closure_safe.json",
        "experiments/iter241_iter240_repository_closure/fixtures/repository_closure_known_bad.json",
        "scripts/capture_iter240_repository_closure.py",
        "scripts/validate_iter240_repository_closure.py",
        "scripts/validate_seal_registry.py",
        "tests/test_iter240_repository_closure.py",
    )


def _retained_or_skip() -> tuple[dict, Path]:
    if not validator.RECEIPT.is_file() or not validator.ATTEMPT.is_file():
        pytest.skip("one-shot repository-closure evidence is not captured yet")
    return validator.read_json(validator.RECEIPT, label="receipt"), validator.RAW_ROOT


def _stage_retained(tmp_path: Path) -> tuple[dict, Path, Path]:
    receipt, raw = _retained_or_skip()
    staged_raw = tmp_path / "raw"
    shutil.copytree(raw, staged_raw)
    staged_receipt = tmp_path / "receipt.json"
    staged_receipt.write_bytes(validator.canonical_json(receipt))
    staged_receipt.chmod(0o644)
    return receipt, staged_raw, staged_receipt


def test_retained_capture_validates_when_present() -> None:
    _retained_or_skip()
    assert validator.validate() == []


def test_raw_body_hash_drift_fires_when_evidence_present(tmp_path: Path) -> None:
    _receipt, raw, receipt_path = _stage_retained(tmp_path)
    body = raw / validator.ENDPOINTS[0][2]
    body.write_bytes(body.read_bytes() + b" ")
    body.chmod(0o644)
    failures = validator.validate(
        root=ROOT,
        receipt_path=receipt_path,
        raw_root=raw,
        check_repository=False,
    )
    assert any("raw body hash" in item for item in failures)


def test_duplicate_request_id_fires_when_evidence_present(tmp_path: Path) -> None:
    receipt, raw, receipt_path = _stage_retained(tmp_path)
    first_id = receipt["capture"]["response_inventory"][0]["github_request_id"]
    second_filename = validator.ENDPOINTS[1][2].removesuffix(".json") + ".headers.json"
    second_headers_path = raw / second_filename
    second_headers = json.loads(second_headers_path.read_text(encoding="utf-8"))
    for row in second_headers["headers"]:
        if row["name"].lower() == "x-github-request-id":
            row["value"] = first_id
    header_raw = validator.canonical_json(second_headers)
    second_headers_path.write_bytes(header_raw)
    second_headers_path.chmod(0o644)
    inventory = receipt["capture"]["response_inventory"][1]
    inventory["github_request_id"] = first_id
    inventory["raw_headers_byte_count"] = len(header_raw)
    inventory["raw_headers_sha256"] = hashlib.sha256(header_raw).hexdigest()
    receipt_path.write_bytes(validator.canonical_json(receipt))
    receipt_path.chmod(0o644)
    failures = validator.validate(
        root=ROOT,
        receipt_path=receipt_path,
        raw_root=raw,
        check_repository=False,
    )
    assert "GitHub request IDs are not unique" in failures


def test_write_count_fabrication_fires_when_evidence_present(tmp_path: Path) -> None:
    receipt, raw, receipt_path = _stage_retained(tmp_path)
    receipt["request_counts"]["POST"] = 1
    receipt_path.write_bytes(validator.canonical_json(receipt))
    receipt_path.chmod(0o644)
    failures = validator.validate(
        root=ROOT,
        receipt_path=receipt_path,
        raw_root=raw,
        check_repository=False,
    )
    assert "receipt write count differs" in failures
