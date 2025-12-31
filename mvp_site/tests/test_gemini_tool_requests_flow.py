"""Tests for Gemini native function calling flow.

Tests generate_content_with_native_tools which uses Gemini's native
function_call API (not JSON-first tool_requests parsing).
"""

from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


class TestGeminiNativeToolsFlow(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["TESTING"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test")

    def test_native_tools_runs_phase2_when_function_calls_present(self):
        """Phase 2 runs when model returns function calls."""
        from mvp_site.llm_providers import gemini_provider

        # Mock Phase 1 response with function calls
        mock_function_call = MagicMock()
        mock_function_call.name = "roll_dice"
        mock_function_call.args = {"notation": "1d20"}

        mock_part = MagicMock()
        mock_part.function_call = mock_function_call

        mock_content = MagicMock()
        mock_content.parts = [mock_part]

        mock_candidate = MagicMock()
        mock_candidate.content = mock_content

        phase1_response = MagicMock()
        phase1_response.candidates = [mock_candidate]

        phase2_response = SimpleNamespace(text='{"narrative":"Rolled a 15!"}')

        with (
            patch.object(gemini_provider, "get_client") as mock_get_client,
            patch.object(
                gemini_provider, "execute_tool_requests"
            ) as mock_exec,
            patch.object(
                gemini_provider, "generate_json_mode_content"
            ) as mock_json,
        ):
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = phase1_response
            mock_get_client.return_value = mock_client

            mock_exec.return_value = [
                {"tool": "roll_dice", "args": {"notation": "1d20"}, "result": 15}
            ]
            mock_json.return_value = phase2_response

            out = gemini_provider.generate_content_with_native_tools(
                prompt_contents=["Roll for initiative"],
                model_name="gemini-2.0-flash",
                system_instruction_text="sys",
                temperature=0.0,
                safety_settings=[],
                json_mode_max_output_tokens=256,
            )

        assert out.text == '{"narrative":"Rolled a 15!"}'
        assert mock_exec.called
        assert mock_json.called

    def test_native_tools_skips_phase2_when_no_function_calls(self):
        """No Phase 2 when model doesn't call functions."""
        from mvp_site.llm_providers import gemini_provider

        # Mock Phase 1 response without function calls (just text)
        mock_part = MagicMock()
        mock_part.function_call = None

        mock_content = MagicMock()
        mock_content.parts = [mock_part]

        mock_candidate = MagicMock()
        mock_candidate.content = mock_content

        phase1_response = MagicMock()
        phase1_response.candidates = [mock_candidate]

        phase2_response = SimpleNamespace(text='{"narrative":"No dice needed"}')

        with (
            patch.object(gemini_provider, "get_client") as mock_get_client,
            patch.object(
                gemini_provider, "execute_tool_requests"
            ) as mock_exec,
            patch.object(
                gemini_provider, "generate_json_mode_content"
            ) as mock_json,
        ):
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = phase1_response
            mock_get_client.return_value = mock_client

            mock_json.return_value = phase2_response

            out = gemini_provider.generate_content_with_native_tools(
                prompt_contents=["Hello"],
                model_name="gemini-2.0-flash",
                system_instruction_text="sys",
                temperature=0.0,
                safety_settings=[],
                json_mode_max_output_tokens=256,
            )

        assert out.text == '{"narrative":"No dice needed"}'
        # execute_tool_requests should NOT be called when no function calls
        assert not mock_exec.called
        # Phase 2 still runs to get final JSON output
        assert mock_json.called
