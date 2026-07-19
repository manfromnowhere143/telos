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


def test_current_paper_guard_preserves_claim_authority_role_and_report_link(
    monkeypatch,
) -> None:
    validator = load_validator()
    original = validator.normalized_prose
    role = (
        "The claim registry is the canonical reviewed resolution authority; "
        "the active-gate coverage report is retained evidence that the "
        "declared surfaces resolve against it"
    )

    def tampered(path: Path) -> str:
        text = original(path)
        if path == validator.ROOT / "paper/README.md":
            active_gate, report_path = validator.active_claim_authority_paths()
            return (
                text.replace(role, "The claim registry is one useful file")
                .replace(f"(../{active_gate})", "")
                .replace(f"(../{report_path})", "")
            )
        return text

    monkeypatch.setattr(validator, "normalized_prose", tampered)

    failures = validator.validate()

    assert any(role in failure for failure in failures)
    assert any("exact active engineering gate" in failure for failure in failures)
    assert any("exact active-gate claim coverage report" in failure for failure in failures)
