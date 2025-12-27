import types

import pytest

from mvp_site.llm_providers import openrouter_provider


class DummyResponse:
    def __init__(self, payload: dict):
        self._payload = payload
        self.status_code = 200

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")


def test_builds_openrouter_payload(monkeypatch):
    captured = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return DummyResponse(
            {"choices": [{"message": {"content": '{"narrative": "ok"}'}}]}
        )

    monkeypatch.setattr(
        openrouter_provider, "requests", types.SimpleNamespace(post=fake_post)
    )

    response = openrouter_provider.generate_content(
        prompt_contents=["first", "second"],
        model_name="meta-llama/llama-3.1-70b-instruct",
        system_instruction_text="system rules",
        temperature=0.4,
        max_output_tokens=400,
    )

    assert captured["url"] == openrouter_provider.OPENROUTER_URL
    assert captured["json"]["model"] == "meta-llama/llama-3.1-70b-instruct"
    assert captured["json"]["messages"][0]["role"] == "system"
    assert "first\n\nsecond" in captured["json"]["messages"][1]["content"]
    assert captured["json"]["response_format"]["type"] == "json_object"
    assert response.text == '{"narrative": "ok"}'
