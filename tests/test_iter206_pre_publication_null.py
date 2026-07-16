from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    path = ROOT / "scripts/validate_iter206_pre_publication_null.py"
    spec = importlib.util.spec_from_file_location("validate_iter206_pre_publication_null", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_iter206_pre_publication_null_validates() -> None:
    validator = load_validator()
    validator.validate()


def test_iter206_null_rejects_nonzero_publication(monkeypatch) -> None:
    validator = load_validator()
    original = validator._load_json

    def changed(path: Path):
        document = original(path)
        if path == validator.NULL:
            document["publication"]["remote_branch_push_count"] = 1
        return document

    monkeypatch.setattr(validator, "_load_json", changed)
    with pytest.raises(validator.PrePublicationNullError, match="publication boundary"):
        validator.validate()


def test_iter206_null_rejects_frozen_hash_drift(monkeypatch) -> None:
    validator = load_validator()
    path = next(iter(validator.FROZEN_HASHES))
    monkeypatch.setitem(validator.FROZEN_HASHES, path, "0" * 64)
    with pytest.raises(validator.PrePublicationNullError, match="frozen iter206 byte drift"):
        validator.validate()
