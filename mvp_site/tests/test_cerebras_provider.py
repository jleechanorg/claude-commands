import types

import pytest

from mvp_site.llm_providers import cerebras_provider


class DummyResponse:
    def __init__(self, payload: dict):
        self._payload = payload
        self.status_code = 200
        self.ok = True  # Mimic requests.Response.ok property

    def json(self):
        return self._payload

    def raise_for_status(self):  # pragma: no cover - mimic requests interface
        return None


@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    monkeypatch.setenv("CEREBRAS_API_KEY", "test-cerebras-key")


def test_builds_cerebras_payload(monkeypatch):
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return DummyResponse({"choices": [{"message": {"content": '{"narrative": "ok"}'}}]})

    monkeypatch.setattr(
        cerebras_provider, "requests", types.SimpleNamespace(post=fake_post)
    )

    response = cerebras_provider.generate_content(
        prompt_contents=["hello", {"key": "value"}],
        model_name="llama-3.3-70b",  # Updated: 3.1-70b retired from Cerebras
        system_instruction_text="system guidance",
        temperature=0.3,
        max_output_tokens=256,
    )

    assert captured["url"] == cerebras_provider.CEREBRAS_URL
    assert captured["headers"]["Authorization"].startswith("Bearer test-cerebras-key")
    assert captured["json"]["model"] == "llama-3.3-70b"
    assert captured["json"]["messages"][0]["role"] == "system"
    assert "hello" in captured["json"]["messages"][1]["content"]
    assert response.text == '{"narrative": "ok"}'
