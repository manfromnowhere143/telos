"""Offline tests for the LLM-judge output parser (no network).

The first iter111 run had 18% unparseable outputs because extended-thinking tokens truncated the
JSON mid-``reason``. These tests lock the recovery path.
"""

from __future__ import annotations

import pytest

from telos.tamper.llm_judge import _parse_verdict, vertex_endpoint


def test_parses_clean_json() -> None:
    assert _parse_verdict('{"verdict":"legitimate","reason":"general fix"}')[0] == "legitimate"


def test_parses_fenced_json() -> None:
    assert _parse_verdict('```json\n{"verdict":"reward_hack","reason":"skips test"}\n```')[0] == "reward_hack"


def test_recovers_truncated_json_via_verdict_regex() -> None:
    # Token cap cut the reason mid-string: no closing brace, but the verdict is present.
    truncated = '```json\n{\n  "verdict": "legitimate",\n  "reason": "The patch correctly modifies inter'
    assert _parse_verdict(truncated)[0] == "legitimate"


def test_truly_empty_output_is_unparseable() -> None:
    assert _parse_verdict("")[0] == "unparseable"


def test_unknown_verdict_is_unparseable() -> None:
    assert _parse_verdict('{"verdict":"maybe"}')[0] == "unparseable"


def test_vertex_endpoint_requires_explicit_project_configuration(monkeypatch) -> None:
    monkeypatch.delenv("TELOS_VERTEX_PROJECT", raising=False)
    with pytest.raises(RuntimeError, match="TELOS_VERTEX_PROJECT"):
        vertex_endpoint()


def test_vertex_endpoint_uses_environment_without_repository_identity(monkeypatch) -> None:
    monkeypatch.setenv("TELOS_VERTEX_PROJECT", "example-project-123")
    assert vertex_endpoint() == (
        "https://us-central1-aiplatform.googleapis.com/v1/projects/example-project-123/"
        "locations/us-central1/publishers/google/models/gemini-2.5-flash:generateContent"
    )


@pytest.mark.parametrize("component", ("project/name", "project?query", "project#fragment"))
def test_vertex_endpoint_rejects_path_or_url_metacharacters(component) -> None:
    with pytest.raises(ValueError, match="invalid Vertex project"):
        vertex_endpoint(project=component)
