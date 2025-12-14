"""
End-to-end tests for Gemini tool loop internal logic.

These tests verify the internal behavior of generate_content_with_tool_loop,
specifically that conversation history is properly passed between Phase 1 and Phase 2.

Following the testing philosophy from CLAUDE.md:
- Mock the LOWEST-LEVEL API call (generate_json_mode_content), NOT the function under test
- This ensures internal logic (building history, passing to Phase 2) is exercised
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, call

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.genai import types


class FakeGeminiFunctionCall:
    """Fake function call object for Gemini responses."""

    def __init__(self, name: str, args: dict):
        self.name = name
        self.args = args


class FakeGeminiPart:
    """Fake part object for Gemini responses."""

    def __init__(self, text: str = "", function_call: FakeGeminiFunctionCall | None = None):
        self.text = text
        self.function_call = function_call


class FakeGeminiContent:
    """Fake content object for Gemini responses."""

    def __init__(self, parts: list):
        self.parts = parts
        self.role = "model"


class FakeGeminiCandidate:
    """Fake candidate object for Gemini responses."""

    def __init__(self, content: FakeGeminiContent):
        self.content = content


class FakeGeminiResponse:
    """Fake Gemini API response."""

    def __init__(self, text: str = "", parts: list | None = None):
        self.text = text
        if parts is None:
            parts = [FakeGeminiPart(text=text)]
        content = FakeGeminiContent(parts=parts)
        self.candidates = [FakeGeminiCandidate(content)]


def create_phase1_response_with_tool_call(tool_name: str, tool_args: dict) -> FakeGeminiResponse:
    """Create a Phase 1 response that contains a tool call."""
    function_call = FakeGeminiFunctionCall(name=tool_name, args=tool_args)
    part = FakeGeminiPart(function_call=function_call)
    return FakeGeminiResponse(parts=[part])


def create_phase2_json_response(json_text: str) -> FakeGeminiResponse:
    """Create a Phase 2 response with final JSON output."""
    return FakeGeminiResponse(text=json_text)


class TestGeminiToolLoopHistoryPassing(unittest.TestCase):
    """
    Test that generate_content_with_tool_loop properly passes conversation
    history from Phase 1 to Phase 2.

    BUG BEING TESTED: In gemini_provider.py:268-278, the `history` list
    is built but NOT passed to generate_json_mode_content in Phase 2.
    Instead, prompt_contents=[] and messages=None are passed, causing
    an empty context to be sent to the LLM.
    """

    @patch('mvp_site.llm_providers.gemini_provider.get_client')
    @patch('mvp_site.game_state.execute_dice_tool')
    def test_phase2_receives_history_not_empty_prompt(self, mock_execute_tool, mock_get_client):
        """
        CRITICAL TEST: Verify Phase 2 API call receives conversation history.

        The bug: Phase 2 is called with prompt_contents=[] instead of the
        built history containing:
        1. User prompt
        2. Model's tool call response
        3. Tool execution results

        This test will FAIL until the bug is fixed.
        """
        from mvp_site.llm_providers import gemini_provider

        # Setup mock client
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Phase 1 response: Model requests a dice roll
        phase1_response = create_phase1_response_with_tool_call(
            tool_name="roll_dice",
            tool_args={"notation": "1d20", "label": "attack"}
        )

        # Phase 2 response: Final JSON output
        phase2_response = create_phase2_json_response(
            '{"narrative": "You rolled a 15!", "dice_rolls": ["Attack: 1d20 = 15"], "entities_mentioned": []}'
        )

        # Mock generate_content to return Phase 1 then Phase 2 responses
        mock_client.models.generate_content.side_effect = [phase1_response, phase2_response]

        # Mock tool execution
        mock_execute_tool.return_value = {"roll": 15, "total": 15, "notation": "1d20"}

        # Call the function under test
        result = gemini_provider.generate_content_with_tool_loop(
            prompt_contents=["Test prompt: roll for attack"],
            model_name="gemini-2.0-flash",
            system_instruction_text="You are a DM",
            temperature=0.7,
            safety_settings=[],
            json_mode_max_output_tokens=8000,
            tools=[{
                "function": {
                    "name": "roll_dice",
                    "description": "Roll dice",
                    "parameters": {"type": "object", "properties": {"notation": {"type": "string"}}}
                }
            }],
        )

        # ASSERTION: Verify generate_content was called twice (Phase 1 and Phase 2)
        self.assertEqual(
            mock_client.models.generate_content.call_count, 2,
            "Should have called API twice: Phase 1 (tools) and Phase 2 (JSON)"
        )

        # CRITICAL ASSERTION: Phase 2 should NOT receive empty contents
        phase2_call_args = mock_client.models.generate_content.call_args_list[1]
        phase2_contents = phase2_call_args.kwargs.get('contents', phase2_call_args.args[1] if len(phase2_call_args.args) > 1 else [])

        # The bug: contents is [] because history is built but not passed
        # After fix: contents should have 3 items (user prompt, model tool call, tool result)
        self.assertIsNotNone(phase2_contents, "Phase 2 contents should not be None")
        self.assertGreater(
            len(phase2_contents), 0,
            "BUG DETECTED: Phase 2 received empty contents! "
            "The 'history' list is built but not passed to generate_json_mode_content. "
            "Fix: Pass history as the contents parameter in Phase 2 call."
        )

        # Verify the history structure contains expected parts
        # Should have: user prompt, model response (tool call), user response (tool result)
        self.assertGreaterEqual(
            len(phase2_contents), 3,
            f"Phase 2 should receive full history (user + model + tool_result), got {len(phase2_contents)} items"
        )

    @patch('mvp_site.llm_providers.gemini_provider.get_client')
    def test_no_tool_calls_returns_phase1_response(self, mock_get_client):
        """
        Verify that when Phase 1 returns no tool calls,
        the response is returned directly without Phase 2.
        """
        from mvp_site.llm_providers import gemini_provider

        # Setup mock client
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Phase 1 response: No tool calls, just text
        phase1_response = FakeGeminiResponse(
            text='{"narrative": "No dice needed", "dice_rolls": [], "entities_mentioned": []}'
        )

        mock_client.models.generate_content.return_value = phase1_response

        # Call the function
        result = gemini_provider.generate_content_with_tool_loop(
            prompt_contents=["Test prompt without dice"],
            model_name="gemini-2.0-flash",
            system_instruction_text="You are a DM",
            temperature=0.7,
            safety_settings=[],
            json_mode_max_output_tokens=8000,
            tools=[],
        )

        # Should only call API once (no Phase 2 needed)
        self.assertEqual(
            mock_client.models.generate_content.call_count, 1,
            "Should only call API once when no tool calls in Phase 1"
        )

        # Result should be the Phase 1 response
        self.assertEqual(result, phase1_response)


class TestGeminiToolLoopToolExecution(unittest.TestCase):
    """Test that tool calls are properly executed between phases."""

    @patch('mvp_site.llm_providers.gemini_provider.get_client')
    @patch('mvp_site.llm_providers.gemini_provider.execute_dice_tool')
    def test_tool_results_included_in_history(self, mock_execute_tool, mock_get_client):
        """
        Verify that tool execution results are included in the history
        passed to Phase 2.
        """
        from mvp_site.llm_providers import gemini_provider

        # Setup
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        phase1_response = create_phase1_response_with_tool_call(
            tool_name="roll_attack",
            tool_args={"attack_modifier": 5, "target_ac": 15}
        )
        phase2_response = create_phase2_json_response('{"narrative": "Hit!", "dice_rolls": [], "entities_mentioned": []}')

        mock_client.models.generate_content.side_effect = [phase1_response, phase2_response]
        mock_execute_tool.return_value = {"roll": 18, "total": 23, "hit": True}

        # Execute
        gemini_provider.generate_content_with_tool_loop(
            prompt_contents=["Attack the goblin"],
            model_name="gemini-2.0-flash",
            system_instruction_text=None,
            temperature=0.7,
            safety_settings=[],
            json_mode_max_output_tokens=8000,
            tools=[{"function": {"name": "roll_attack", "description": "Roll attack", "parameters": {}}}],
        )

        # Verify tool was executed
        mock_execute_tool.assert_called_once_with(
            "roll_attack",
            {"attack_modifier": 5, "target_ac": 15}
        )


if __name__ == "__main__":
    unittest.main()
