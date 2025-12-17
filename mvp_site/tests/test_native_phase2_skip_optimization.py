"""Tests for native two-phase Phase 2 skip optimization.

This test module verifies the performance optimization where Phase 2 is skipped
when Phase 1 returns no tool_calls AND the response text is valid JSON.

OPTIMIZATION: When LLM returns valid JSON without requesting tools, we skip
the redundant Phase 2 call, reducing API calls and token usage.
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from mvp_site.llm_providers import cerebras_provider, gemini_provider, openrouter_provider


class TestGeminiPhase2SkipOptimization:
    """Test Phase 2 skip optimization in Gemini provider."""

    def test_skips_phase2_when_phase1_returns_valid_json_no_tools(self, monkeypatch):
        """When Phase 1 returns valid JSON and no function_calls, skip Phase 2."""
        # Mock client.models.generate_content to return valid JSON without function_calls
        valid_json_response = {"narrative": "The hero stands ready.", "planning_block": {}}

        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [
            MagicMock(text=json.dumps(valid_json_response), function_call=None)
        ]

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        monkeypatch.setattr(gemini_provider, 'get_client', lambda: mock_client)

        # Call generate_content_with_native_tools
        result = gemini_provider.generate_content_with_native_tools(
            prompt_contents=["test prompt"],
            model_name="gemini-2.5-flash-latest",
            system_instruction_text="system",
            temperature=0.7,
            safety_settings=[],
            json_mode_max_output_tokens=4096,
        )

        # Verify: Only ONE API call (Phase 1), Phase 2 was skipped
        assert mock_client.models.generate_content.call_count == 1, (
            "Expected only Phase 1 call when Phase 1 returns valid JSON"
        )

        # Verify: Returned Phase 1 response directly
        assert result == mock_response

    def test_proceeds_to_phase2_when_phase1_returns_invalid_json(self, monkeypatch):
        """When Phase 1 returns invalid JSON and no function_calls, proceed to Phase 2."""
        # Mock Phase 1 response with invalid JSON
        mock_phase1_response = MagicMock()
        mock_phase1_response.candidates = [MagicMock()]
        mock_phase1_response.candidates[0].content.parts = [
            MagicMock(text="The hero stands ready.", function_call=None)  # Not JSON
        ]

        # Mock Phase 2 response with valid JSON
        valid_json_response = {"narrative": "The hero stands ready.", "planning_block": {}}
        mock_phase2_response = MagicMock()
        mock_phase2_response.candidates = [MagicMock()]
        mock_phase2_response.candidates[0].content.parts = [
            MagicMock(text=json.dumps(valid_json_response))
        ]

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = [mock_phase1_response, mock_phase2_response]

        monkeypatch.setattr(gemini_provider, 'get_client', lambda: mock_client)

        # Call generate_content_with_native_tools
        result = gemini_provider.generate_content_with_native_tools(
            prompt_contents=["test prompt"],
            model_name="gemini-2.5-flash-latest",
            system_instruction_text="system",
            temperature=0.7,
            safety_settings=[],
            json_mode_max_output_tokens=4096,
        )

        # Verify: TWO API calls (Phase 1 + Phase 2) because Phase 1 returned invalid JSON
        assert mock_client.models.generate_content.call_count == 2, (
            "Expected Phase 1 + Phase 2 calls when Phase 1 returns invalid JSON"
        )

        # Verify: Returned Phase 2 response
        assert result == mock_phase2_response


class TestOpenRouterPhase2SkipOptimization:
    """Test Phase 2 skip optimization in OpenRouter provider."""

    def test_skips_phase2_when_phase1_returns_valid_json_no_tools(self, monkeypatch):
        """When Phase 1 returns valid JSON and no tool_calls, skip Phase 2."""
        valid_json_response = {"narrative": "The warrior prepares.", "planning_block": {}}

        mock_response = MagicMock()
        mock_response.text = json.dumps(valid_json_response)
        mock_response.tool_calls = None  # No tools requested

        def mock_generate_content(*args, **kwargs):
            return mock_response

        monkeypatch.setattr(openrouter_provider, 'generate_content', mock_generate_content)

        # Track calls
        call_count = 0
        original_func = openrouter_provider.generate_content

        def counting_generate_content(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return mock_response

        monkeypatch.setattr(openrouter_provider, 'generate_content', counting_generate_content)

        result = openrouter_provider.generate_content_with_native_tools(
            prompt_contents=["test prompt"],
            model_name="anthropic/claude-3.5-sonnet",
            system_instruction_text="system",
            temperature=0.7,
            max_output_tokens=4096,
        )

        # Verify: Only ONE API call (Phase 1), Phase 2 was skipped
        assert call_count == 1, "Expected only Phase 1 call when Phase 1 returns valid JSON"
        assert result == mock_response

    def test_proceeds_to_phase2_when_phase1_returns_invalid_json(self, monkeypatch):
        """When Phase 1 returns invalid JSON and no tool_calls, proceed to Phase 2."""
        # Phase 1: Invalid JSON
        mock_phase1_response = MagicMock()
        mock_phase1_response.text = "The warrior prepares."  # Not JSON
        mock_phase1_response.tool_calls = None

        # Phase 2: Valid JSON
        valid_json_response = {"narrative": "The warrior prepares.", "planning_block": {}}
        mock_phase2_response = MagicMock()
        mock_phase2_response.text = json.dumps(valid_json_response)
        mock_phase2_response.tool_calls = None

        call_count = 0

        def mock_generate_content(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_phase1_response
            return mock_phase2_response

        monkeypatch.setattr(openrouter_provider, 'generate_content', mock_generate_content)

        result = openrouter_provider.generate_content_with_native_tools(
            prompt_contents=["test prompt"],
            model_name="anthropic/claude-3.5-sonnet",
            system_instruction_text="system",
            temperature=0.7,
            max_output_tokens=4096,
        )

        # Verify: TWO API calls (Phase 1 + Phase 2)
        assert call_count == 2, "Expected Phase 1 + Phase 2 calls when Phase 1 returns invalid JSON"
        assert result == mock_phase2_response


class TestCerebrasPhase2SkipOptimization:
    """Test Phase 2 skip optimization in Cerebras provider."""

    def test_skips_phase2_when_phase1_returns_valid_json_no_tools(self, monkeypatch):
        """When Phase 1 returns valid JSON and no tool_calls, skip Phase 2."""
        valid_json_response = {"narrative": "The mage focuses.", "planning_block": {}}

        mock_response = MagicMock()
        mock_response.text = json.dumps(valid_json_response)
        mock_response.tool_calls = None  # No tools requested

        call_count = 0

        def mock_generate_content(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return mock_response

        monkeypatch.setattr(cerebras_provider, 'generate_content', mock_generate_content)

        result = cerebras_provider.generate_content_with_native_tools(
            prompt_contents=["test prompt"],
            model_name="qwen-3-235b-a22b-instruct-2507",
            system_instruction_text="system",
            temperature=0.7,
            max_output_tokens=4096,
        )

        # Verify: Only ONE API call (Phase 1), Phase 2 was skipped
        assert call_count == 1, "Expected only Phase 1 call when Phase 1 returns valid JSON"
        assert result == mock_response

    def test_proceeds_to_phase2_when_phase1_returns_invalid_json(self, monkeypatch):
        """When Phase 1 returns invalid JSON and no tool_calls, proceed to Phase 2."""
        # Phase 1: Invalid JSON
        mock_phase1_response = MagicMock()
        mock_phase1_response.text = "The mage focuses."  # Not JSON
        mock_phase1_response.tool_calls = None

        # Phase 2: Valid JSON
        valid_json_response = {"narrative": "The mage focuses.", "planning_block": {}}
        mock_phase2_response = MagicMock()
        mock_phase2_response.text = json.dumps(valid_json_response)
        mock_phase2_response.tool_calls = None

        call_count = 0

        def mock_generate_content(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_phase1_response
            return mock_phase2_response

        monkeypatch.setattr(cerebras_provider, 'generate_content', mock_generate_content)

        result = cerebras_provider.generate_content_with_native_tools(
            prompt_contents=["test prompt"],
            model_name="qwen-3-235b-a22b-instruct-2507",
            system_instruction_text="system",
            temperature=0.7,
            max_output_tokens=4096,
        )

        # Verify: TWO API calls (Phase 1 + Phase 2)
        assert call_count == 2, "Expected Phase 1 + Phase 2 calls when Phase 1 returns invalid JSON"
        assert result == mock_phase2_response
