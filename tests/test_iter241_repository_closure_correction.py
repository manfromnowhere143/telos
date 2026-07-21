from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import sys
import tomllib


ROOT = Path(__file__).resolve().parents[1]
ADJUDICATOR_PATH = ROOT / "scripts/adjudicate_iter241_repository_closure_correction.py"


def load_adjudicator():
    spec = importlib.util.spec_from_file_location(
        "test_iter241_repository_closure_correction_adjudicator",
        ADJUDICATOR_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


adjudicator = load_adjudicator()


def test_merge_commit_sha_membership_is_distinct_from_value() -> None:
    assert adjudicator.merge_member_adjudication({}) == {
        "accepted": False,
        "classification": "omitted",
    }
    assert adjudicator.merge_member_adjudication({"merge_commit_sha": None}) == {
        "accepted": True,
        "classification": "explicit_null",
    }
    assert adjudicator.merge_member_adjudication({"merge_commit_sha": adjudicator.MERGE}) == {
        "accepted": True,
        "classification": "exact_sha",
    }
    assert adjudicator.merge_member_adjudication({"merge_commit_sha": "0" * 40}) == {
        "accepted": False,
        "classification": "conflicting_sha",
    }


def test_raw_header_bytes_are_distinct_from_canonicalized_pairs() -> None:
    assert adjudicator.raw_header_byte_adjudication(
        {
            "raw_header_section_bytes_retained": True,
            "serialization": "identity_bytes",
            "source_api": "raw_header_section_bytes",
        }
    ) == {
        "accepted": True,
        "classification": "raw_header_section_bytes_retained",
        "status": {"raw_header_byte_fidelity": "supported"},
    }
    assert adjudicator.raw_header_byte_adjudication(
        {
            "raw_header_section_bytes_retained": False,
            "serialization": "canonical_json_header_pairs",
            "source_api": "http.client.HTTPResponse.getheaders",
        }
    ) == {
        "accepted": False,
        "classification": "canonicalized_returned_pairs_only",
        "status": {
            "capture_completeness": "failed",
            "raw_header_byte_fidelity": "failed",
        },
    }


def test_intent_bound_safe_and_known_bad_fixtures() -> None:
    assert adjudicator.fixture_failures(ROOT) == []


def test_adjudicator_does_not_import_the_frozen_validator() -> None:
    tree = ast.parse(ADJUDICATOR_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
    assert imported_roots == {
        "__future__",
        "argparse",
        "datetime",
        "email",
        "hashlib",
        "json",
        "pathlib",
        "stat",
        "typing",
    }
    source = ADJUDICATOR_PATH.read_text(encoding="utf-8")
    assert "importlib" not in source
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "document_projection" not in called_attributes


def test_marker_bound_and_retained_evidence_bytes_remain_exact() -> None:
    assert adjudicator.source_failures(ROOT) == []
    receipt = adjudicator.read_json(
        adjudicator.ORIGINAL_RECEIPT,
        label="original receipt",
    )
    protected = adjudicator._expected_protected_records(ROOT, receipt)
    assert len(protected) == 36
    assert len({row["path"] for row in protected}) == 36


def test_correction_receipt_regenerates_and_fails_closure() -> None:
    assert adjudicator.validate(ROOT) == []
    receipt = adjudicator.read_json(
        adjudicator.CORRECTION_RECEIPT,
        label="correction receipt",
    )
    assert receipt["adjudication"] == adjudicator.EXPECTED_STATUS_VECTOR
    assert receipt["adjudication"]["capture_completeness"] == "failed"
    assert receipt["adjudication"]["raw_header_byte_fidelity"] == "failed"
    assert receipt["defect"]["retained_pull_request"] == {
        "contract_acceptance": False,
        "merge_commit_sha_classification": "omitted",
        "merge_commit_sha_member_present": False,
        "original_projection_value": None,
    }
    assert receipt["defect"]["retained_response_headers"] == {
        "capture_completeness": "failed",
        "contract_acceptance": False,
        "exact_header_section_bytes_reconstructible": False,
        "raw_header_byte_fidelity": "failed",
        "raw_header_section_bytes_retained": False,
        "retained_representation": "canonicalized_returned_header_pair_documents",
        "source_api": "http.client.HTTPResponse.getheaders",
    }
    assert receipt["retained_observations"]["header_representation"] == (
        "canonicalized_returned_header_pair_documents_not_raw_wire_bytes"
    )
    assert receipt["retained_observations"]["raw_header_section_bytes_retained"] is False
    assert receipt["retained_observations"]["raw_header_section_bytes_reconstructible"] is False


def test_frozen_f401_exception_is_exactly_one_file_and_one_rule() -> None:
    configuration = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert configuration["tool"]["ruff"]["lint"]["per-file-ignores"] == {
        "scripts/validate_iter240_repository_closure.py": ["F401"]
    }
    frozen = ROOT / "scripts/validate_iter240_repository_closure.py"
    assert adjudicator.sha256(frozen.read_bytes()) == (
        "9f54fdacca4ce334d97c60593c585873f07ec968fcffded7d82c19e649cd36ec"
    )
