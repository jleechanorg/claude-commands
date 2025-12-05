"""
TDD Tests for Code Execution - Dice Roll Randomness Fix

IMPORTANT: Gemini API LIMITATION (discovered 2025-12-05):
The Gemini API does NOT support using code_execution tool WITH
response_mime_type (JSON mode/controlled generation). These features
are mutually exclusive. See:
https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/gemini

Since this application requires JSON mode for structured responses,
code execution for dice rolls is NOT available. Dice roll randomness
must be handled through prompt engineering instead.

These tests verify:
1. JSON mode is enabled (required for structured output)
2. Prompt instructions for dice roll randomness exist
3. Code execution is NOT enabled (would break JSON mode)
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Set TESTING environment variable
os.environ["TESTING"] = "true"

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from google.genai import types

from mvp_site import constants, llm_service


class TestCodeExecutionForDiceRolls(unittest.TestCase):
    """Test that JSON mode is properly configured (code execution is incompatible)"""

    def test_json_mode_enabled_without_code_execution(self):
        """
        Verify JSON mode is enabled and code_execution is NOT present.

        Gemini API does not support controlled generation (response_mime_type)
        with code_execution tool. We prioritize JSON mode for structured output.
        """
        with patch("mvp_site.llm_providers.gemini_provider.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            # Mock successful API response
            mock_client.models.generate_content = Mock(
                return_value=Mock(
                    text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
                )
            )

            # Call the API function with explicit Gemini provider
            llm_service._call_llm_api(
                ["test prompt"],
                "gemini-3-pro-preview",
                "test logging",
                provider_name=constants.LLM_PROVIDER_GEMINI
            )

            # Verify the API was called
            self.assertTrue(mock_client.models.generate_content.called)

            # Get the configuration object passed to the API
            call_args = mock_client.models.generate_content.call_args
            config_obj = call_args[1]["config"]

            # CRITICAL: Verify JSON mode is enabled
            self.assertEqual(
                config_obj.response_mime_type,
                "application/json",
                "FAIL: JSON mode must be enabled for structured responses"
            )

            # CRITICAL: Verify code_execution is NOT present (incompatible with JSON mode)
            # Code execution and response_mime_type cannot coexist in Gemini API
            if config_obj.tools is not None:
                for tool in config_obj.tools:
                    if hasattr(tool, 'code_execution'):
                        self.fail(
                            "FAIL: code_execution tool is present but incompatible with JSON mode. "
                            "Gemini API does not support controlled generation with code execution."
                        )

    def test_dice_roll_instructions_exist(self):
        """
        Verify prompt instructions for dice roll handling exist.

        Since code execution cannot be used with JSON mode, dice roll
        randomness must be handled through careful prompt engineering.
        """
        # Read the instruction file
        instruction_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts",
            "game_state_instruction.md"
        )

        with open(instruction_path) as f:
            instruction_content = f.read()

        # Check for dice roll section
        self.assertIn(
            "Dice Roll",
            instruction_content,
            "FAIL: Instruction file missing dedicated Dice Roll section"
        )

        # Check for randomness instructions
        self.assertTrue(
            "random" in instruction_content.lower() or "dice" in instruction_content.lower(),
            "FAIL: Instruction file should mention dice/random handling"
        )

    def test_api_call_has_required_config_params(self):
        """
        Verify API calls have all required configuration parameters.

        This test ensures JSON mode is properly configured without
        code execution (which would break the API call).
        """
        with patch("mvp_site.llm_providers.gemini_provider.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            mock_client.models.generate_content = Mock(
                return_value=Mock(
                    text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
                )
            )

            llm_service._call_llm_api(
                ["test prompt"],
                "gemini-3-pro-preview",
                "test logging",
                provider_name=constants.LLM_PROVIDER_GEMINI
            )

            call_args = mock_client.models.generate_content.call_args
            config_obj = call_args[1]["config"]

            # Verify existing configurations are present
            self.assertEqual(
                config_obj.response_mime_type,
                "application/json",
                "FAIL: JSON mode not configured"
            )

            self.assertEqual(
                config_obj.max_output_tokens,
                llm_service.JSON_MODE_MAX_OUTPUT_TOKENS,
                "FAIL: Token limit not configured"
            )

            self.assertEqual(
                config_obj.temperature,
                llm_service.TEMPERATURE,
                "FAIL: Temperature not configured"
            )

            self.assertIsNotNone(
                config_obj.safety_settings,
                "FAIL: Safety settings not configured"
            )


if __name__ == "__main__":
    unittest.main()
