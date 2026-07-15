from __future__ import annotations

import io
import json

import pytest

from scripts import run_iter200_blind_judge as judge


def test_openai_judge_request_matches_frozen_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return io.BytesIO(b'{"choices":[{"message":{"content":"ok"}}]}')

    monkeypatch.setattr(judge.urllib.request, "urlopen", fake_urlopen)
    assert judge.call_openai("prompt", "secret") == "ok"

    request = captured["request"]
    body = json.loads(request.data)
    assert request.full_url == "https://api.openai.com/v1/chat/completions"
    assert body == {
        "model": "gpt-5.6-terra",
        "messages": [{"role": "user", "content": "prompt"}],
        "max_completion_tokens": 1536,
    }
    assert "temperature" not in body
    assert captured["timeout"] == 120


def test_anthropic_judge_request_matches_frozen_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return io.BytesIO(b'{"content":[{"type":"text","text":"ok"}]}')

    monkeypatch.setattr(judge.urllib.request, "urlopen", fake_urlopen)
    assert judge.call_anthropic("prompt", "secret") == "ok"

    request = captured["request"]
    body = json.loads(request.data)
    headers = {name.lower(): value for name, value in request.header_items()}
    assert request.full_url == "https://api.anthropic.com/v1/messages"
    assert body == {
        "model": "claude-opus-4-8",
        "max_tokens": 400,
        "messages": [{"role": "user", "content": "prompt"}],
    }
    assert "temperature" not in body
    assert headers["anthropic-version"] == "2023-06-01"
    assert captured["timeout"] == 120


def test_judge_configuration_override_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELOS_NAT_OPENAI_JUDGE_MODEL", "different-model")
    with pytest.raises(SystemExit, match="does not accept environment overrides"):
        judge.reject_judge_configuration_overrides()
