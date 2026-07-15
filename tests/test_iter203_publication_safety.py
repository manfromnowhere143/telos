from __future__ import annotations

from pathlib import Path

import pytest

from scripts import validate_iter203_publication_safety as guard


def test_uuid_tail_is_not_treated_as_a_numeric_account_identifier() -> None:
    secret_hits, claim_hits, uuid_count = guard.scan_text(
        'value = "12345678-1234-1234-1234-123456789012"\n'
    )
    assert secret_hits == []
    assert claim_hits == []
    assert uuid_count == 1


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Authorization: Bearer sensitive-token-value", "bearer_token"),
        ("contact someone@example.com", "private_email"),
        ("cache = /home/private-user/data", "local_home_path"),
    ],
)
def test_scan_reports_identifiers_without_returning_secret_values(
    text: str, expected: str
) -> None:
    secret_hits, _claim_hits, _uuid_count = guard.scan_text(text)
    assert expected in secret_hits
    assert "sensitive-token-value" not in repr(secret_hits)


def test_build_audit_rejects_a_hit_without_printing_its_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(guard, "ROOT", tmp_path)
    path = tmp_path / "evidence.txt"
    path.write_text("Authorization: Bearer sensitive-token-value\n", encoding="utf-8")
    with pytest.raises(guard.PublicationSafetyError) as exc_info:
        guard.build_audit([path])
    assert "sensitive-token-value" not in str(exc_info.value)
