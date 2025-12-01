"""
TDD Tests for Code Execution - Dice Roll Randomness Fix

Problem: Dice rolls showed bias (avg 16.19 vs expected 10.5) because Gemini
was inferring results instead of executing actual random code.

Solution: Enable code_execution tool in Gemini API and require code execution
for all dice rolls via prompt instructions.

RED -> GREEN -> REFACTOR:
1. RED: Tests fail without code_execution tool configured
2. GREEN: Implementation enables code execution in API calls
3. REFACTOR: Ensure prompt instructions enforce code execution usage
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

from mvp_site import llm_service
from google.genai import types


class TestCodeExecutionForDiceRolls(unittest.TestCase):
    """Test that code execution is properly enabled for dice rolls"""

    def test_code_execution_tool_enabled_in_api_config(self):
        """
        RED PHASE TEST: Verify code_execution tool is included in API configuration

        This test ensures that when we call the Gemini API, the configuration
        includes the code_execution tool which allows Gemini to run actual
        Python code (random.randint) instead of inferring dice results.
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

            # Call the API function
            llm_service._call_llm_api_with_model_cycling(
                ["test prompt"], "gemini-3-pro-preview", "test logging"
            )

            # Verify the API was called
            self.assertTrue(mock_client.models.generate_content.called)

            # Get the configuration object passed to the API
            call_args = mock_client.models.generate_content.call_args
            config_obj = call_args[1]["config"]

            # CRITICAL ASSERTION: Verify tools parameter includes code_execution
            self.assertIsNotNone(
                config_obj.tools,
                "FAIL: tools parameter is None - code_execution tool not configured"
            )

            self.assertIsInstance(
                config_obj.tools,
                list,
                "FAIL: tools must be a list"
            )

            self.assertGreater(
                len(config_obj.tools),
                0,
                "FAIL: tools list is empty - code_execution tool not configured"
            )

            # Verify the first tool is a Tool object with code_execution
            first_tool = config_obj.tools[0]
            self.assertIsInstance(
                first_tool,
                types.Tool,
                f"FAIL: Expected types.Tool, got {type(first_tool)}"
            )

            # Verify code_execution is configured
            self.assertIsNotNone(
                first_tool.code_execution,
                "FAIL: code_execution not configured in Tool object"
            )

            self.assertIsInstance(
                first_tool.code_execution,
                types.ToolCodeExecution,
                f"FAIL: Expected types.ToolCodeExecution, got {type(first_tool.code_execution)}"
            )

    def test_dice_roll_instructions_require_code_execution(self):
        """
        RED PHASE TEST: Verify prompt instructions mandate code execution for dice rolls

        This test checks that the game_state_instruction.md file contains
        explicit instructions to use code execution for dice rolls.
        """
        # Read the instruction file
        instruction_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts",
            "game_state_instruction.md"
        )

        with open(instruction_path, "r") as f:
            instruction_content = f.read()

        # CRITICAL ASSERTIONS: Verify code execution instructions are present

        # Check for code execution mandate in dice_rolls field description
        self.assertIn(
            "code execution",
            instruction_content.lower(),
            "FAIL: Instruction file does not mention 'code execution'"
        )

        # Check for random.randint instruction
        self.assertIn(
            "random.randint",
            instruction_content,
            "FAIL: Instruction file does not specify random.randint for dice rolls"
        )

        # Check for import random instruction
        self.assertIn(
            "import random",
            instruction_content,
            "FAIL: Instruction file does not show 'import random' for dice rolls"
        )

        # Check for critical/mandatory language
        critical_keywords = ["CRITICAL", "MUST", "NEVER generate"]
        found_critical = any(keyword in instruction_content for keyword in critical_keywords)
        self.assertTrue(
            found_critical,
            f"FAIL: Instruction file lacks critical language ({critical_keywords}) "
            f"to enforce code execution usage"
        )

        # Check for dice roll section with code execution protocol
        self.assertIn(
            "Dice Roll",
            instruction_content,
            "FAIL: Instruction file missing dedicated Dice Roll section"
        )

    def test_api_call_preserves_other_config_params(self):
        """
        REGRESSION TEST: Ensure adding code_execution doesn't break existing config

        Verify that enabling code_execution tool doesn't interfere with:
        - JSON mode (response_mime_type)
        - Token limits (max_output_tokens)
        - Temperature settings
        - Safety settings
        """
        with patch("mvp_site.llm_providers.gemini_provider.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            mock_client.models.generate_content = Mock(
                return_value=Mock(
                    text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
                )
            )

            llm_service._call_llm_api_with_model_cycling(
                ["test prompt"], "gemini-3-pro-preview", "test logging"
            )

            call_args = mock_client.models.generate_content.call_args
            config_obj = call_args[1]["config"]

            # Verify existing configurations are still present
            self.assertEqual(
                config_obj.response_mime_type,
                "application/json",
                "FAIL: JSON mode not preserved after adding code_execution"
            )

            self.assertEqual(
                config_obj.max_output_tokens,
                llm_service.JSON_MODE_MAX_OUTPUT_TOKENS,
                "FAIL: Token limit not preserved after adding code_execution"
            )

            self.assertEqual(
                config_obj.temperature,
                llm_service.TEMPERATURE,
                "FAIL: Temperature not preserved after adding code_execution"
            )

            self.assertIsNotNone(
                config_obj.safety_settings,
                "FAIL: Safety settings not preserved after adding code_execution"
            )

            # AND verify code_execution is ALSO present
            self.assertIsNotNone(
                config_obj.tools,
                "FAIL: code_execution tool missing"
            )


if __name__ == "__main__":
    unittest.main()
