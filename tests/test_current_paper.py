from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    path = ROOT / "scripts/validate_current_paper.py"
    spec = importlib.util.spec_from_file_location("validate_current_paper", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_current_paper_source_and_pdf_are_bound() -> None:
    validator = load_validator()

    assert validator.validate() == []


def test_current_paper_guard_detects_source_or_pdf_drift(monkeypatch) -> None:
    validator = load_validator()

    monkeypatch.setattr(validator, "EXPECTED_SOURCE_SHA256", "0" * 64)
    monkeypatch.setattr(validator, "EXPECTED_PDF_SHA256", "1" * 64)
    failures = validator.validate()
    assert "paper/telos.tex changed without refreshing the current-paper binding" in failures
    assert (
        "paper/telos.pdf changed without a deterministic rebuild/binding refresh"
        in failures
    )
