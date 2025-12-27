import json
import types

import pytest

from mvp_site.llm_providers import cerebras_provider
from mvp_site.llm_providers.provider_utils import ContextTooLargeError

# =============================================================================
# TDD MATRIX: json_schema with strict:false support
# =============================================================================
# | Test Case                | Model    | Expected Behavior                    |
# |--------------------------|----------|--------------------------------------|
# | json_schema in payload   | any      | Uses json_schema, not json_object    |
# | schema echo detection    | any      | Raises CerebrasSchemaEchoError       |
# | nested wrapper unwrap    | any      | Extracts content from {"json": {...}}|
# | valid json_schema resp   | qwen-3   | Returns valid structured JSON        |
# | valid json_schema resp   | glm-4.6  | Returns valid structured JSON        |
# | valid json_schema resp   | llama-3  | Returns valid structured JSON        |
# =============================================================================


class TestJsonSchemaSupport:
    """Tests for json_schema support with strict:false (allows dynamic choice keys)."""

    def test_uses_json_schema_format_in_payload(self, monkeypatch):
        """Verify request payload uses json_schema, not legacy json_object."""
        captured = {}

        def fake_post(url, headers=None, json=None, timeout=None):
            captured["json"] = json
            return DummyResponse(
                {"choices": [{"message": {"content": '{"narrative": "test"}'}}]}
            )

        monkeypatch.setattr(
            cerebras_provider, "requests", types.SimpleNamespace(post=fake_post)
        )

        cerebras_provider.generate_content(
            prompt_contents=["test prompt"],
            model_name="qwen-3-235b-a22b-instruct-2507",
            system_instruction_text="system",
            temperature=0.7,
            max_output_tokens=4096,
        )

        # Should use json_schema (not legacy json_object) with strict:false
        # strict:false allows dynamic choice keys in planning_block
        response_format = captured["json"]["response_format"]
        assert response_format["type"] == "json_schema", (
            f"Expected json_schema but got {response_format.get('type')}"
        )
        assert "json_schema" in response_format, "Missing json_schema field"
        assert response_format["json_schema"].get("strict") is False, (
            "json_schema must have strict:false to allow dynamic choice keys"
        )

    def test_json_schema_has_narrative_response_structure(self, monkeypatch):
        """Verify json_schema includes NarrativeResponse fields."""
        captured = {}

        def fake_post(url, headers=None, json=None, timeout=None):
            captured["json"] = json
            return DummyResponse(
                {"choices": [{"message": {"content": '{"narrative": "test"}'}}]}
            )

        monkeypatch.setattr(
            cerebras_provider, "requests", types.SimpleNamespace(post=fake_post)
        )

        cerebras_provider.generate_content(
            prompt_contents=["test"],
            model_name="llama-3.3-70b",
            system_instruction_text=None,
            temperature=0.5,
            max_output_tokens=100,
        )

        schema = captured["json"]["response_format"]["json_schema"]["schema"]
        properties = schema.get("properties", {})

        # Must have core NarrativeResponse fields
        assert "narrative" in properties, "Schema must include 'narrative' field"
        assert "planning_block" in properties, (
            "Schema must include 'planning_block' field"
        )
        assert properties["planning_block"].get("type") == "object"
        assert "entities_mentioned" in properties, (
            "Schema must include 'entities_mentioned' field"
        )
        assert "state_updates" in properties, (
            "Schema must include 'state_updates' field"
        )
        assert "turn_summary" in properties, "Schema must include 'turn_summary' field"
        assert "debug_info" in properties, "Schema must include 'debug_info' field"
        assert "god_mode_response" in properties, (
            "Schema must include 'god_mode_response' field"
        )

    def test_detects_schema_echo_response(self, monkeypatch):
        """Detect when API returns schema config instead of content."""
        from mvp_site.llm_providers.cerebras_provider import CerebrasSchemaEchoError

        def fake_post(url, headers=None, json=None, timeout=None):
            # API returns the response_format schema instead of content
            return DummyResponse(
                {"choices": [{"message": {"content": '{"type": "object"}'}}]}
            )

        monkeypatch.setattr(
            cerebras_provider, "requests", types.SimpleNamespace(post=fake_post)
        )

        with pytest.raises(CerebrasSchemaEchoError):
            cerebras_provider.generate_content(
                prompt_contents=["test"],
                model_name="zai-glm-4.6",
                system_instruction_text=None,
                temperature=0.5,
                max_output_tokens=100,
            )

    def test_unwraps_nested_json_wrapper(self, monkeypatch):
        """Extract content from nested {"type": "object", "json": {...}} wrapper."""

        def fake_post(url, headers=None, json=None, timeout=None):
            # API wraps content in nested structure
            return DummyResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": '{"type": "object", "json": {"narrative": "unwrapped content", "entities_mentioned": []}}'
                            }
                        }
                    ]
                }
            )

        monkeypatch.setattr(
            cerebras_provider, "requests", types.SimpleNamespace(post=fake_post)
        )

        response = cerebras_provider.generate_content(
            prompt_contents=["test"],
            model_name="qwen-3-235b-a22b-instruct-2507",
            system_instruction_text=None,
            temperature=0.5,
            max_output_tokens=100,
        )

        # Should extract the inner content
        parsed = json.loads(response.text)
        assert parsed == {
            "narrative": "unwrapped content",
            "entities_mentioned": [],
        }, f"Expected unwrapped structure but got {parsed}"
        assert "type" not in parsed, (
            "Unwrapped response should not contain 'type' field"
        )

    @pytest.mark.parametrize(
        "model_name",
        [
            "qwen-3-235b-a22b-instruct-2507",
            "zai-glm-4.6",
            "llama-3.3-70b",
        ],
    )
    def test_all_cerebras_models_use_json_schema(self, monkeypatch, model_name):
        """All supported Cerebras models should use json_schema format."""
        captured = {}

        def fake_post(url, headers=None, json=None, timeout=None):
            captured["json"] = json
            return DummyResponse(
                {"choices": [{"message": {"content": '{"narrative": "ok"}'}}]}
            )

        monkeypatch.setattr(
            cerebras_provider, "requests", types.SimpleNamespace(post=fake_post)
        )

        cerebras_provider.generate_content(
            prompt_contents=["test"],
            model_name=model_name,
            system_instruction_text=None,
            temperature=0.5,
            max_output_tokens=100,
        )

        response_format = captured["json"]["response_format"]
        assert response_format["type"] == "json_schema", (
            f"Model {model_name} should use json_schema"
        )


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
        return DummyResponse(
            {"choices": [{"message": {"content": '{"narrative": "ok"}'}}]}
        )

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

    def fake_post(url, headers=None, json=None, timeout=None):
        # Qwen 3 with reasoning returns the JSON in 'reasoning' field
        return DummyResponse(
            {
                "id": "chatcmpl-test",
                "choices": [
                    {
                        "finish_reason": "stop",
                        "index": 0,
                        "message": {
                            "reasoning": '{"session_header": "test", "narrative": "Qwen 3 reasoning response"}'
                        },
                    }
                ],
            }
        )

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

    assert "qwen 3 reasoning response" in response.text.lower()
    assert "session_header" in response.text


def test_prefers_content_over_reasoning_when_both_present(monkeypatch):
    """If both 'content' and 'reasoning' exist, prefer 'content'."""

    def fake_post(url, headers=None, json=None, timeout=None):
        return DummyResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": '{"from_content": true}',
                            "reasoning": '{"from_reasoning": true}',
                        }
                    }
                ]
            }
        )

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


def test_handles_mixed_case_keys(monkeypatch):
    """Case-insensitive lookup should handle mixed-case content/reasoning keys."""

    def fake_post(url, headers=None, json=None, timeout=None):
        return DummyResponse(
            {
                "choices": [
                    {
                        "message": {
                            "Content": '{"from_content": true}',
                            "REASONING": '{"from_reasoning": true}',
                        }
                    }
                ]
            }
        )

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
        return DummyResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": "",
                            "reasoning": '{"from_reasoning": true}',
                        }
                    }
                ]
            }
        )

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


def test_context_too_large_error_message(monkeypatch):
    """When finish_reason='length' and no content, raise clear context-too-large error."""

    def fake_post(url, headers=None, json=None, timeout=None):
        # Simulate the exact response from the GCP logs:
        # - finish_reason: 'length' (hit token limit)
        # - completion_tokens: 1 (couldn't generate meaningful output)
        # - message has only 'role', no 'content'
        return DummyResponse(
            {
                "id": "chatcmpl-test",
                "choices": [
                    {
                        "finish_reason": "length",
                        "index": 0,
                        "message": {"role": "assistant"},
                    }
                ],
                "usage": {
                    "total_tokens": 113038,
                    "completion_tokens": 1,
                    "prompt_tokens": 113037,
                },
            }
        )

    monkeypatch.setattr(
        cerebras_provider, "requests", types.SimpleNamespace(post=fake_post)
    )

    with pytest.raises(ContextTooLargeError) as exc_info:
        cerebras_provider.generate_content(
            prompt_contents=["test"],
            model_name="zai-glm-4.6",
            system_instruction_text=None,
            temperature=0.5,
            max_output_tokens=100,
        )

    error_msg = str(exc_info.value)
    assert "Context too large" in error_msg
    assert "113,037" in error_msg  # Should show prompt tokens with commas
    assert "prompt must be reduced" in error_msg.lower()

    # Verify exception attributes are set correctly
    assert exc_info.value.prompt_tokens == 113037
    assert exc_info.value.completion_tokens == 1
    assert exc_info.value.finish_reason == "length"
