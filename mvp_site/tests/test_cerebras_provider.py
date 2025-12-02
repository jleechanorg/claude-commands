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


def test_extracts_reasoning_field_for_qwen3_models(monkeypatch):
    """Qwen 3 reasoning models return content in 'reasoning' field, not 'content'."""
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        # Qwen 3 with reasoning returns the JSON in 'reasoning' field
        return DummyResponse({
            "id": "chatcmpl-test",
            "choices": [{
                "finish_reason": "stop",
                "index": 0,
                "message": {
                    "reasoning": '{"session_header": "test", "narrative": "Qwen 3 reasoning response"}'
                }
            }]
        })

    monkeypatch.setattr(
        cerebras_provider, "requests", types.SimpleNamespace(post=fake_post)
    )

    response = cerebras_provider.generate_content(
        prompt_contents=["test prompt"],
        model_name="qwen-3-32b",
        system_instruction_text="system",
        temperature=0.7,
        max_output_tokens=4096,
    )

    assert "Qwen 3 reasoning response" in response.text
    assert "session_header" in response.text


def test_prefers_content_over_reasoning_when_both_present(monkeypatch):
    """If both 'content' and 'reasoning' exist, prefer 'content'."""

    def fake_post(url, headers=None, json=None, timeout=None):
        return DummyResponse({
            "choices": [{
                "message": {
                    "content": '{"from_content": true}',
                    "reasoning": '{"from_reasoning": true}'
                }
            }]
        })

    monkeypatch.setattr(
        cerebras_provider, "requests", types.SimpleNamespace(post=fake_post)
    )

    response = cerebras_provider.generate_content(
        prompt_contents=["test"],
        model_name="test-model",
        system_instruction_text=None,
        temperature=0.5,
        max_output_tokens=100,
    )

    assert "from_content" in response.text
    assert "from_reasoning" not in response.text


def test_handles_empty_content_field(monkeypatch):
    """Empty content should be preserved, not fall back to reasoning."""

    def fake_post(url, headers=None, json=None, timeout=None):
        return DummyResponse({
            "choices": [{
                "message": {
                    "content": "",
                    "reasoning": '{"from_reasoning": true}'
                }
            }]
        })

    monkeypatch.setattr(
        cerebras_provider, "requests", types.SimpleNamespace(post=fake_post)
    )

    response = cerebras_provider.generate_content(
        prompt_contents=["test"],
        model_name="test-model",
        system_instruction_text=None,
        temperature=0.5,
        max_output_tokens=100,
    )

    # Empty content should be preserved, not fall back to reasoning
    assert response.text == ""
