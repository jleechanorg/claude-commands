"""
TDD Tests for Hybrid Dice Roll System

UPDATE (2025-12): Gemini 2.0 and 3.0 models now support code_execution
WITH JSON response mode. This hybrid system supports:

1. Code Execution (Gemini 2.0/3.0): Native Python code execution for dice rolls
2. Tool Use (Cerebras, OpenRouter): Function calling with local execution
3. Pre-computed (fallback): Backend pre-rolls dice and provides values

See: https://ai.google.dev/gemini-api/docs/structured-output

These tests verify:
1. JSON mode is enabled (required for structured output)
2. Code execution is enabled for supported models (Gemini 2.0/3.0)
3. Tool schemas are defined for non-code-execution models
4. Prompt instructions cover all dice roll strategies
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


from mvp_site import constants, llm_service


class TestHybridDiceRollSystem(unittest.TestCase):
    """Test the hybrid dice roll system across different model types."""

    def test_code_execution_enabled_for_supported_models(self):
        """
        Verify code_execution IS enabled for Gemini 2.0/3.0 models.

        Gemini 2.0 and 3.0 support code_execution WITH JSON response mode.
        This allows true randomness for dice rolls via Python's random module.
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

            # Call the API function with Gemini 2.0 model (supports code execution)
            llm_service._call_llm_api(
                ["test prompt"],
                "gemini-2.0-flash",
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

            # CRITICAL: Verify code_execution IS present for supported models
            code_execution_found = False
            if config_obj.tools is not None:
                for tool in config_obj.tools:
                    if hasattr(tool, 'code_execution'):
                        code_execution_found = True
                        break

            self.assertTrue(
                code_execution_found,
                "FAIL: code_execution should be enabled for gemini-2.0-flash"
            )

    def test_model_capability_detection(self):
        """
        Verify the model capability detection function works correctly.
        """
        # Gemini models support code_execution
        self.assertEqual(
            constants.get_dice_roll_strategy("gemini-2.0-flash"),
            "code_execution"
        )
        self.assertEqual(
            constants.get_dice_roll_strategy("gemini-3-pro-preview"),
            "code_execution"
        )

        # Cerebras/OpenRouter models with 100k+ context use tool_use
        self.assertEqual(
            constants.get_dice_roll_strategy("qwen-3-235b-a22b-instruct-2507"),
            "tool_use"
        )
        self.assertEqual(
            constants.get_dice_roll_strategy("zai-glm-4.6"),
            "tool_use"
        )

        # llama-3.3-70b does NOT support multi-turn tool calling, falls back to precompute
        self.assertEqual(
            constants.get_dice_roll_strategy("llama-3.3-70b"),
            "precompute"
        )

        # Unknown models fall back to precompute
        self.assertEqual(
            constants.get_dice_roll_strategy("unknown-model"),
            "precompute"
        )

    def test_dice_roll_instructions_exist(self):
        """
        Verify prompt instructions for hybrid dice roll handling exist.
        """
        # Read the instruction file
        instruction_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts",
            "game_state_instruction.md"
        )

        with open(instruction_path) as f:
            instruction_content = f.read()

        # Check for hybrid dice roll section
        self.assertIn(
            "Dice Roll",
            instruction_content,
            "FAIL: Instruction file missing Dice Roll section"
        )

        # Check for code execution strategy mention
        self.assertIn(
            "Code Execution",
            instruction_content,
            "FAIL: Instruction file should mention Code Execution strategy"
        )

        # Check for tool use strategy mention
        self.assertIn(
            "Tool Use",
            instruction_content,
            "FAIL: Instruction file should mention Tool Use strategy"
        )

    def test_dice_tool_schemas_defined(self):
        """
        Verify dice roll tool schemas are defined for tool use models.
        """
        from mvp_site.game_state import DICE_ROLL_TOOLS

        # Verify tool schemas exist
        self.assertIsInstance(DICE_ROLL_TOOLS, list)
        self.assertGreater(len(DICE_ROLL_TOOLS), 0)

        # Verify required tools are present
        tool_names = [t["function"]["name"] for t in DICE_ROLL_TOOLS]
        self.assertIn("roll_dice", tool_names)
        self.assertIn("roll_attack", tool_names)
        self.assertIn("roll_skill_check", tool_names)
        self.assertIn("roll_saving_throw", tool_names)

    def test_execute_dice_tool_roll_dice(self):
        """
        Verify the execute_dice_tool function works for basic dice rolls.
        """
        from mvp_site.game_state import execute_dice_tool

        result = execute_dice_tool("roll_dice", {"notation": "1d20+5"})

        self.assertIn("total", result)
        self.assertIn("rolls", result)
        self.assertIn("modifier", result)
        self.assertEqual(result["modifier"], 5)
        self.assertTrue(6 <= result["total"] <= 25)  # 1+5 to 20+5

    def test_execute_dice_tool_roll_attack(self):
        """
        Verify the execute_dice_tool function works for attack rolls.
        """
        from mvp_site.game_state import execute_dice_tool

        result = execute_dice_tool("roll_attack", {
            "attack_modifier": 5,
            "damage_notation": "1d8+3",
            "target_ac": 15,
        })

        self.assertIn("attack_roll", result)
        self.assertIn("hit", result)
        self.assertIn("target_ac", result)
        self.assertEqual(result["target_ac"], 15)

        # If hit, damage should be present
        if result["hit"]:
            self.assertIsNotNone(result["damage"])
            self.assertIn("total", result["damage"])

    def test_api_call_has_required_config_params(self):
        """
        Verify API calls have all required configuration parameters.
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
                "gemini-2.0-flash",
                "test logging",
                provider_name=constants.LLM_PROVIDER_GEMINI
            )

            call_args = mock_client.models.generate_content.call_args
            config_obj = call_args[1]["config"]

            # Verify JSON mode is enabled
            self.assertEqual(
                config_obj.response_mime_type,
                "application/json",
                "FAIL: JSON mode not configured"
            )

            # Verify token limit is configured
            self.assertEqual(
                config_obj.max_output_tokens,
                llm_service.JSON_MODE_MAX_OUTPUT_TOKENS,
                "FAIL: Token limit not configured"
            )

            # Verify temperature is configured
            self.assertEqual(
                config_obj.temperature,
                llm_service.TEMPERATURE,
                "FAIL: Temperature not configured"
            )

            # Verify safety settings exist
            self.assertIsNotNone(
                config_obj.safety_settings,
                "FAIL: Safety settings not configured"
            )


class TestCerebrasToolUseIntegration(unittest.TestCase):
    """Test Cerebras provider tool use for dice rolling (two-stage inference)."""

    def test_cerebras_provider_accepts_tools_parameter(self):
        """
        Verify Cerebras provider can accept tools parameter.
        """
        # Check that generate_content accepts tools parameter
        import inspect

        from mvp_site.llm_providers import cerebras_provider
        sig = inspect.signature(cerebras_provider.generate_content)
        param_names = list(sig.parameters.keys())

        self.assertIn(
            "tools",
            param_names,
            "FAIL: cerebras_provider.generate_content should accept 'tools' parameter"
        )

    def test_cerebras_response_handles_tool_calls(self):
        """
        Verify CerebrasResponse can extract tool_calls from response.
        """
        from mvp_site.llm_providers.cerebras_provider import CerebrasResponse

        # Mock response with tool_calls
        mock_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "roll_dice",
                            "arguments": '{"notation": "1d20+5"}'
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }]
        }

        response = CerebrasResponse("", mock_response)

        # Verify tool_calls can be extracted
        self.assertTrue(
            hasattr(response, 'tool_calls') or hasattr(response, 'get_tool_calls'),
            "FAIL: CerebrasResponse should expose tool_calls"
        )

    def test_process_tool_calls_executes_dice_tools(self):
        """
        Verify process_tool_calls function executes dice roll tools.
        """
        from mvp_site.llm_providers.cerebras_provider import process_tool_calls

        # Mock tool call from LLM
        tool_calls = [{
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "roll_dice",
                "arguments": '{"notation": "1d20+5"}'
            }
        }]

        results = process_tool_calls(tool_calls)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["tool_call_id"], "call_123")
        self.assertIn("total", results[0]["result"])

    def test_generate_content_with_tool_loop(self):
        """
        Verify generate_content_with_tool_loop handles two-stage inference.
        """
        from mvp_site.llm_providers import cerebras_provider

        # Check function exists
        self.assertTrue(
            hasattr(cerebras_provider, 'generate_content_with_tool_loop'),
            "FAIL: cerebras_provider should have generate_content_with_tool_loop function"
        )

    def test_cerebras_tool_loop_requires_positive_iterations(self):
        """Guard against invalid iteration counts to avoid uninitialized responses."""
        from mvp_site.llm_providers import cerebras_provider

        with self.assertRaises(ValueError):
            cerebras_provider.generate_content_with_tool_loop(
                prompt_contents=["test"],
                model_name="qwen-3-235b-a22b-instruct-2507",
                system_instruction_text=None,
                temperature=0.2,
                max_output_tokens=128,
                tools=[],
                max_iterations=0,
            )


class TestOpenRouterToolUseIntegration(unittest.TestCase):
    """Test OpenRouter provider tool use for dice rolling."""

    def test_openrouter_provider_accepts_tools_parameter(self):
        """
        Verify OpenRouter provider can accept tools parameter.
        """
        import inspect

        from mvp_site.llm_providers import openrouter_provider
        sig = inspect.signature(openrouter_provider.generate_content)
        param_names = list(sig.parameters.keys())

        self.assertIn(
            "tools",
            param_names,
            "FAIL: openrouter_provider.generate_content should accept 'tools' parameter"
        )

    def test_openrouter_tool_loop_requires_positive_iterations(self):
        """Guard against invalid iteration counts to avoid None returns."""
        from mvp_site.llm_providers import openrouter_provider

        with self.assertRaises(ValueError):
            openrouter_provider.generate_content_with_tool_loop(
                prompt_contents=["test"],
                model_name="gpt-4o-mini",
                system_instruction_text=None,
                temperature=0.2,
                max_output_tokens=128,
                tools=[],
                max_iterations=0,
            )


class TestLLMServiceToolIntegration(unittest.TestCase):
    """Test llm_service integration with tool use providers."""

    def test_call_llm_api_passes_tools_to_cerebras(self):
        """
        Verify _call_llm_api passes dice tools to Cerebras provider.
        """
        with patch("mvp_site.llm_providers.cerebras_provider.generate_content_with_tool_loop") as mock_generate:
            mock_generate.return_value = Mock(
                text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
            )

            # This should pass tools to Cerebras
            llm_service._call_llm_api(
                ["test prompt"],
                "qwen-3-235b-a22b-instruct-2507",
                "test logging",
                provider_name=constants.LLM_PROVIDER_CEREBRAS
            )

            # Verify tools were passed
            self.assertTrue(
                mock_generate.called,
                "generate_content_with_tool_loop should be called",
            )
            call_kwargs = mock_generate.call_args[1] if mock_generate.call_args[1] else {}
            self.assertIn(
                "tools",
                call_kwargs,
                "FAIL: tools should be passed to Cerebras provider"
            )


if __name__ == "__main__":
    unittest.main()
