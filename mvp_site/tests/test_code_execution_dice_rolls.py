"""
TDD Tests for Hybrid Dice Roll System

Gemini 3.x models support BOTH code_execution AND JSON mode together.
Gemini 2.x models do NOT support this combination - they use the native two-phase tool flow.

The hybrid dice roll system:
1. Code Execution (Gemini 3.x): Native Python code execution + JSON mode (single inference)
2. Tool Use (Gemini 2.x, Cerebras, OpenRouter): Function calling with local execution (two-phase)
3. Pre-computed (fallback): Backend pre-rolls dice and provides values

See: https://ai.google.dev/gemini-api/docs/structured-output

These tests verify:
1. JSON mode is enabled (required for structured output)
2. Code execution IS enabled for Gemini 3.x models (they support both)
3. Code execution is NOT enabled for Gemini 2.x models
4. Tool schemas are defined for non-code-execution models
5. Prompt instructions cover all dice roll strategies
"""

import json
import os
import sys
import unittest
from unittest.mock import Mock, patch

# Set TESTING environment variable
os.environ["TESTING"] = "true"

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)


from mvp_site import constants, dice_strategy, llm_service


class TestHybridDiceRollSystem(unittest.TestCase):
    """Test the hybrid dice roll system across different model types."""

    def test_gemini_2x_uses_tool_requests_flow_for_dice(self):
        """
        Verify Gemini 2.x models use JSON-first tool_requests flow for dice rolling.
        """
        with patch('mvp_site.llm_providers.gemini_provider.generate_content_with_tool_requests') as mock_tool_requests:
            mock_tool_requests.return_value = Mock(
                text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
            )

            # Call the API function with a Gemini 2.x model (not remapped to Gemini 3)
            llm_service._call_llm_api(
                ['test prompt'],
                'gemini-2.0-flash',
                'test logging',
                provider_name=constants.LLM_PROVIDER_GEMINI
            )

            self.assertTrue(
                mock_tool_requests.called,
                "generate_content_with_tool_requests should be called for Gemini 2.x models"
            )

    def test_gemini_3_code_execution_is_single_call(self):
        """Verify Gemini 3 code_execution path does not do Phase 2 calls."""
        from mvp_site.llm_providers import gemini_provider

        with patch("mvp_site.llm_providers.gemini_provider.generate_json_mode_content") as mock_json_mode:
            mock_json_mode.return_value = Mock(
                text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
            )

            with patch("mvp_site.llm_providers.gemini_provider.generate_content_with_tool_requests") as mock_tool_flow:
                gemini_provider.generate_content_with_code_execution(
                    prompt_contents=["test prompt"],
                    model_name="gemini-3-flash-preview",
                    system_instruction_text="test system",
                    temperature=0.7,
                    safety_settings=[],
                    json_mode_max_output_tokens=256,
                )

                self.assertEqual(
                    mock_json_mode.call_count,
                    1,
                    "Gemini 3 code_execution should make exactly one JSON-mode call",
                )
                self.assertFalse(
                    mock_tool_flow.called,
                    "Gemini 3 code_execution should not use tool_requests two-phase flow",
                )

    def test_model_capability_detection(self):
        """
        Verify the model capability detection function works correctly.

        VERIFIED Dec 2024 via real API tests:
        - Gemini 3.x: code_execution (single-phase, verified working)
        - Gemini 2.0: native_two_phase (code_execution + JSON disabled)
        - Gemini 2.5: native_two_phase (tools + JSON mime unsupported)
        - Cerebras/OpenRouter: native_two_phase
        """
        # Gemini 3 supports code_execution + JSON together
        self.assertEqual(
            dice_strategy.get_dice_roll_strategy("gemini-3-pro-preview", "gemini"),
            dice_strategy.DICE_STRATEGY_CODE_EXECUTION,
        )

        # Gemini 2.0 uses native_two_phase (code_execution + JSON unsupported)
        self.assertEqual(
            dice_strategy.get_dice_roll_strategy("gemini-2.0-flash", "gemini"),
            dice_strategy.DICE_STRATEGY_NATIVE_TWO_PHASE,
        )

        # Gemini 2.5 does NOT support tools + JSON mime
        self.assertEqual(
            dice_strategy.get_dice_roll_strategy("gemini-2.5-flash", "gemini"),
            dice_strategy.DICE_STRATEGY_NATIVE_TWO_PHASE,
        )

        # Cerebras models: native_two_phase (Phase 1: native tools, Phase 2: JSON)
        self.assertEqual(
            dice_strategy.get_dice_roll_strategy(
                "qwen-3-235b-a22b-instruct-2507", "cerebras"
            ),
            dice_strategy.DICE_STRATEGY_NATIVE_TWO_PHASE,
        )
        self.assertEqual(
            dice_strategy.get_dice_roll_strategy("zai-glm-4.6", "cerebras"),
            dice_strategy.DICE_STRATEGY_NATIVE_TWO_PHASE,
        )

        # OpenRouter models: native_two_phase
        self.assertEqual(
            dice_strategy.get_dice_roll_strategy(
                "meta-llama/llama-3.1-70b-instruct", "openrouter"
            ),
            dice_strategy.DICE_STRATEGY_NATIVE_TWO_PHASE,
        )

        # All models use native_two_phase
        self.assertEqual(
            dice_strategy.get_dice_roll_strategy("llama-3.3-70b", "cerebras"),
            dice_strategy.DICE_STRATEGY_NATIVE_TWO_PHASE,
        )

        # Unknown models: native_two_phase
        self.assertEqual(
            dice_strategy.get_dice_roll_strategy("unknown-model", ""),
            dice_strategy.DICE_STRATEGY_NATIVE_TWO_PHASE,
        )

        # Default provider path follows same routing
        self.assertEqual(
            dice_strategy.get_dice_roll_strategy("gemini-2.0-flash"),
            dice_strategy.DICE_STRATEGY_NATIVE_TWO_PHASE,
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

        # Check for dice roll section (tool-based architecture)
        self.assertIn(
            "Dice Roll",
            instruction_content,
            "FAIL: Instruction file missing Dice Roll section"
        )

    def test_dice_tool_schemas_defined(self):
        """
        Verify dice roll tool schemas are defined for tool use models.
        """
        from mvp_site.dice import DICE_ROLL_TOOLS

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

    def test_api_call_passes_required_params_to_tool_requests_flow(self):
        """
        Verify API calls pass required parameters to JSON-first tool_requests flow.
        """
        with patch("mvp_site.llm_providers.gemini_provider.generate_content_with_tool_requests") as mock_tool_requests:
            mock_tool_requests.return_value = Mock(
                text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
            )

            llm_service._call_llm_api(
                ["test prompt"],
                "gemini-2.0-flash",
                "test logging",
                provider_name=constants.LLM_PROVIDER_GEMINI,
            )

            self.assertTrue(mock_tool_requests.called)
            call_kwargs = mock_tool_requests.call_args[1]
            self.assertEqual(call_kwargs.get("model_name"), "gemini-2.0-flash")
            self.assertEqual(call_kwargs.get("temperature"), llm_service.TEMPERATURE)

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


# NOTE: Old TestOpenRouterToolUseIntegration and TestToolLoopAllCodePaths classes
# were deleted - they tested the old generate_content_with_tool_loop() which has
# been replaced by generate_content_with_tool_requests() (JSON-first architecture).
# See TestToolRequestsE2EFlow class at end of file for the new tests.


class TestDiceRollTools(unittest.TestCase):
    """Test the dice roll tool definitions."""

    def test_dice_roll_tools_exist(self):
        """
        Verify DICE_ROLL_TOOLS array contains all required tools.
        """
        from mvp_site.dice import DICE_ROLL_TOOLS

        # Get tool names
        tool_names = [t["function"]["name"] for t in DICE_ROLL_TOOLS]

        # Verify all required tools exist
        self.assertIn("roll_dice", tool_names)
        self.assertIn("roll_attack", tool_names)
        self.assertIn("roll_skill_check", tool_names)
        self.assertIn("roll_saving_throw", tool_names)

    def test_execute_dice_tool_roll_dice(self):
        """
        Verify execute_dice_tool handles roll_dice correctly.
        """
        from mvp_site.game_state import execute_dice_tool

        result = execute_dice_tool("roll_dice", {"notation": "2d6+3", "purpose": "damage"})

        self.assertIn("notation", result)
        self.assertIn("total", result)
        self.assertIn("rolls", result)
        self.assertEqual(result["notation"], "2d6+3")
        self.assertEqual(result["purpose"], "damage")

    def test_execute_dice_tool_roll_attack(self):
        """
        Verify execute_dice_tool handles roll_attack correctly.
        """
        from mvp_site.game_state import execute_dice_tool

        result = execute_dice_tool("roll_attack", {
            "attack_modifier": 5,
            "damage_notation": "1d8+3",
            "target_ac": 15
        })

        self.assertIn("attack_roll", result)
        self.assertIn("target_ac", result)
        self.assertIn("hit", result)
        self.assertEqual(result["target_ac"], 15)

    def test_execute_dice_tool_roll_skill_check(self):
        """
        Verify execute_dice_tool handles roll_skill_check correctly.
        """
        from mvp_site.game_state import execute_dice_tool

        result = execute_dice_tool("roll_skill_check", {
            "attribute_modifier": 3,
            "proficiency_bonus": 2,
            "proficient": True,
            "dc": 15,
            "skill_name": "Stealth"
        })

        self.assertIn("skill", result)
        self.assertIn("total", result)
        self.assertIn("success", result)
        self.assertEqual(result["skill"], "Stealth")


class TestLLMServiceToolIntegration(unittest.TestCase):
    """Test llm_service integration with tool use providers."""

    def test_call_llm_api_routes_to_tool_requests_for_cerebras(self):
        """
        Verify _call_llm_api routes to JSON-first tool_requests flow for Cerebras.

        ARCHITECTURE UPDATE (Dec 2024): All Cerebras models use JSON-first flow
        to avoid forced tool calls and match prompt documentation.
        Phase 1: JSON with optional tool_requests, Phase 2: JSON with results.
        """
        with patch("mvp_site.llm_providers.cerebras_provider.generate_content_with_tool_requests") as mock_tool_requests:
            mock_tool_requests.return_value = Mock(
                text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
            )

            # All Cerebras models use JSON-first tool_requests flow
            llm_service._call_llm_api(
                ["test prompt"],
                "qwen-3-235b-a22b-instruct-2507",
                "test logging",
                provider_name=constants.LLM_PROVIDER_CEREBRAS
            )

            # Verify JSON-first tool_requests flow was called
            self.assertTrue(
                mock_tool_requests.called,
                "generate_content_with_tool_requests should be called for Cerebras",
            )

    def test_call_llm_api_routes_to_tool_requests_for_openrouter(self):
        """
        Verify _call_llm_api routes to JSON-first tool_requests flow for OpenRouter.

        ARCHITECTURE UPDATE (Dec 2024): All OpenRouter models use JSON-first flow
        to avoid forced tool calls and match prompt documentation.
        Phase 1: JSON with optional tool_requests, Phase 2: JSON with results.
        """
        with patch("mvp_site.llm_providers.openrouter_provider.generate_content_with_tool_requests") as mock_tool_requests:
            mock_tool_requests.return_value = Mock(
                text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
            )

            # All OpenRouter models use JSON-first tool_requests flow
            llm_service._call_llm_api(
                ["test prompt"],
                "meta-llama/llama-3.1-70b-instruct",
                "test logging",
                provider_name=constants.LLM_PROVIDER_OPENROUTER
            )

            # Verify JSON-first tool_requests flow was called
            self.assertTrue(
                mock_tool_requests.called,
                "generate_content_with_tool_requests should be called for OpenRouter",
            )

    def test_call_llm_api_uses_tool_requests_for_all_cerebras_models(self):
        """
        Verify _call_llm_api uses JSON-first tool_requests for ALL Cerebras models.

        ARCHITECTURE UPDATE (Dec 2024): All Cerebras models use JSON-first flow
        to avoid forced tool calls. The old MODELS_WITH_TOOL_USE distinction
        is removed - all models now use optional tool_requests in JSON.
        """
        with patch("mvp_site.llm_providers.cerebras_provider.generate_content_with_tool_requests") as mock_tool_requests:
            mock_tool_requests.return_value = Mock(
                text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
            )

            # ALL Cerebras models now use JSON-first tool_requests (including llama-3.3-70b)
            llm_service._call_llm_api(
                ["test prompt"],
                "llama-3.3-70b",
                "test logging",
                provider_name=constants.LLM_PROVIDER_CEREBRAS
            )

            # Verify JSON-first tool_requests flow was called
            self.assertTrue(
                mock_tool_requests.called,
                "generate_content_with_tool_requests should be called for all Cerebras models",
            )


class TestToolRequestsE2EFlow(unittest.TestCase):
    """E2E tests for generate_content_with_tool_requests() internal logic.

    These tests mock the low-level generate_content() function to test the
    multi-phase flow, NOT the high-level generate_content_with_tool_requests().

    Test paths:
    1. No tool_requests → returns Phase 1 directly
    2. tool_requests present → executes tools, makes Phase 2 call
    3. Invalid JSON → returns response as-is
    4. Tool execution errors → captured in results
    5. execute_tool_requests() helper function
    """

    def test_path1_no_tool_requests_returns_phase1(self):
        """Path 1: Response without tool_requests returns Phase 1 directly."""
        from mvp_site.llm_providers import cerebras_provider
        from mvp_site.llm_providers.cerebras_provider import CerebrasResponse

        # Phase 1 response: No tool_requests
        phase1_json = json.dumps({
            "narrative": "You look around the room.",
            "planning_block": {"thinking": "Observing surroundings"},
        })

        with patch.object(cerebras_provider, "generate_content") as mock_gen:
            mock_gen.return_value = CerebrasResponse(text=phase1_json, raw_response=None)

            result = cerebras_provider.generate_content_with_tool_requests(
                prompt_contents=["Look around"],
                model_name="test-model",
                system_instruction_text="You are a GM",
                temperature=0.7,
                max_output_tokens=1000,
            )

            # Should only call generate_content once (Phase 1 only)
            self.assertEqual(mock_gen.call_count, 1)
            self.assertEqual(result.text, phase1_json)

    def test_path2_tool_requests_triggers_phase2(self):
        """Path 2: Response with tool_requests executes tools and makes Phase 2 call."""
        from mvp_site.llm_providers import cerebras_provider
        from mvp_site.llm_providers.cerebras_provider import CerebrasResponse

        # Phase 1 response: Has tool_requests
        phase1_json = json.dumps({
            "narrative": "You attack the goblin!",
            "tool_requests": [{"tool": "roll_dice", "args": {"notation": "1d20+5"}}],
        })

        # Phase 2 response: Final narrative with results
        phase2_json = json.dumps({
            "narrative": "You rolled a 17! The goblin is hit.",
            "planning_block": {"thinking": "Attack successful"},
            "dice_rolls": ["17"],
        })

        with patch.object(cerebras_provider, "generate_content") as mock_gen:
            mock_gen.side_effect = [
                CerebrasResponse(text=phase1_json, raw_response=None),
                CerebrasResponse(text=phase2_json, raw_response=None),
            ]

            result = cerebras_provider.generate_content_with_tool_requests(
                prompt_contents=["I attack the goblin"],
                model_name="test-model",
                system_instruction_text="You are a GM",
                temperature=0.7,
                max_output_tokens=1000,
            )

            # Should call generate_content twice (Phase 1 + Phase 2)
            self.assertEqual(mock_gen.call_count, 2)
            self.assertEqual(result.text, phase2_json)

            # Verify Phase 2 call includes tool results in messages
            phase2_call_args = mock_gen.call_args_list[1]
            messages = phase2_call_args.kwargs.get("messages", [])
            self.assertTrue(len(messages) >= 3, "Phase 2 should have messages with tool results")

            # Check that tool results message is included
            tool_results_msg = messages[-1]["content"]
            self.assertIn("Tool results", tool_results_msg)
            # The formatted output contains the calculation (e.g. "1d20+5 = 3+5 = 8")
            # but NOT necessarily the tool name "roll_dice"
            self.assertIn("1d20+5", tool_results_msg)

    def test_path3_invalid_json_returns_as_is(self):
        """Path 3: Non-JSON response returns as-is without Phase 2."""
        from mvp_site.llm_providers import cerebras_provider
        from mvp_site.llm_providers.cerebras_provider import CerebrasResponse

        invalid_response = "This is not valid JSON"

        with patch.object(cerebras_provider, "generate_content") as mock_gen:
            mock_gen.return_value = CerebrasResponse(text=invalid_response, raw_response=None)

            result = cerebras_provider.generate_content_with_tool_requests(
                prompt_contents=["Test"],
                model_name="test-model",
                system_instruction_text=None,
                temperature=0.7,
                max_output_tokens=1000,
            )

            # Should only call once and return as-is
            self.assertEqual(mock_gen.call_count, 1)
            self.assertEqual(result.text, invalid_response)

    def test_path4_tool_execution_errors_captured(self):
        """Path 4: Tool execution errors are captured in results."""
        from mvp_site.llm_providers.cerebras_provider import execute_tool_requests

        # Invalid tool request
        tool_requests = [
            {"tool": "invalid_tool", "args": {}},
            {"tool": "roll_dice", "args": {"notation": "1d20"}},
        ]

        results = execute_tool_requests(tool_requests)

        # First result should have error
        self.assertEqual(len(results), 2)
        self.assertIn("error", results[0]["result"])

        # Second result should succeed
        self.assertIn("total", results[1]["result"])

    def test_path5_execute_tool_requests_helper(self):
        """Path 5: Test execute_tool_requests helper function directly."""
        from mvp_site.llm_providers.cerebras_provider import execute_tool_requests

        tool_requests = [
            {"tool": "roll_dice", "args": {"notation": "2d6+3", "purpose": "damage"}},
            {"tool": "roll_attack", "args": {"modifier": 5, "target_ac": 15}},
            {"tool": "roll_skill_check", "args": {"skill": "perception", "modifier": 2}},
        ]

        results = execute_tool_requests(tool_requests)

        self.assertEqual(len(results), 3)

        # Verify structure of each result
        for i, result in enumerate(results):
            self.assertIn("tool", result)
            self.assertIn("args", result)
            self.assertIn("result", result)
            self.assertEqual(result["tool"], tool_requests[i]["tool"])

        # Verify roll_dice result has expected fields
        self.assertIn("total", results[0]["result"])
        self.assertIn("rolls", results[0]["result"])

    def test_openrouter_path1_no_tool_requests(self):
        """Test OpenRouter provider Path 1: No tool_requests."""
        from mvp_site.llm_providers import openrouter_provider
        from mvp_site.llm_providers.openrouter_provider import OpenRouterResponse

        phase1_json = json.dumps({
            "narrative": "The forest is peaceful.",
            "planning_block": {"thinking": "Peaceful scene"},
        })

        with patch.object(openrouter_provider, "generate_content") as mock_gen:
            mock_gen.return_value = OpenRouterResponse(text=phase1_json)

            result = openrouter_provider.generate_content_with_tool_requests(
                prompt_contents=["Describe the forest"],
                model_name="test-model",
                system_instruction_text="You are a GM",
                temperature=0.7,
                max_output_tokens=1000,
            )

            self.assertEqual(mock_gen.call_count, 1)
            self.assertEqual(result.text, phase1_json)

    def test_openrouter_path2_with_tool_requests(self):
        """Test OpenRouter provider Path 2: With tool_requests."""
        from mvp_site.llm_providers import openrouter_provider
        from mvp_site.llm_providers.openrouter_provider import OpenRouterResponse

        phase1_json = json.dumps({
            "narrative": "You attempt a skill check.",
            "tool_requests": [{"tool": "roll_skill_check", "args": {"skill": "stealth", "modifier": 4}}],
        })

        phase2_json = json.dumps({
            "narrative": "You rolled a 16! You move silently.",
            "planning_block": {"thinking": "Stealth success"},
            "dice_rolls": ["16"],
        })

        with patch.object(openrouter_provider, "generate_content") as mock_gen:
            mock_gen.side_effect = [
                OpenRouterResponse(text=phase1_json),
                OpenRouterResponse(text=phase2_json),
            ]

            result = openrouter_provider.generate_content_with_tool_requests(
                prompt_contents=["I try to sneak past"],
                model_name="test-model",
                system_instruction_text="You are a GM",
                temperature=0.7,
                max_output_tokens=1000,
            )

            self.assertEqual(mock_gen.call_count, 2)
            self.assertEqual(result.text, phase2_json)


class TestThinkingConfigEnforcement(unittest.TestCase):
    """TDD tests for thinkingConfig parameter to improve code_execution compliance."""

    def test_gemini_3_enables_thinking_config_for_code_execution(self):
        """
        Verify that Gemini 3 code_execution includes thinkingConfig.

        Per Consensus ML synthesis:
        - thinkingConfig with thinking_budget increases code_execution compliance
        - Forces model to deliberate before skipping tool use
        """
        from mvp_site.llm_providers import gemini_provider
        from google.genai import types

        # Mock get_client to return a fake client that captures config
        mock_client = Mock()
        mock_response = Mock(text='{"narrative": "test", "dice_rolls": []}')
        mock_client.models.generate_content.return_value = mock_response

        with patch.object(gemini_provider, 'get_client', return_value=mock_client):
            gemini_provider.generate_content_with_code_execution(
                prompt_contents=["test prompt"],
                model_name="gemini-3-flash-preview",
                system_instruction_text="test system",
                temperature=0.7,
                safety_settings=[],
                json_mode_max_output_tokens=256,
            )

        # Verify generate_content was called
        self.assertTrue(
            mock_client.models.generate_content.called,
            "Should call Client.models.generate_content"
        )

        # Get the config from the call
        call_args = mock_client.models.generate_content.call_args
        if call_args is None:
            self.fail("generate_content was not called")

        config = call_args.kwargs.get('config')
        self.assertIsNotNone(config, "Should pass config")

        # Verify thinking_config is present
        self.assertIsNotNone(
            getattr(config, 'thinking_config', None),
            "Config should have thinking_config attribute"
        )


class TestNativeToolsSystemInstruction(unittest.TestCase):
    """TDD tests for native two-phase system instruction retention."""

    def test_native_phase2_keeps_system_instruction_when_phase1_text_exists(self):
        from mvp_site.llm_providers import gemini_provider

        mock_client = Mock()
        mock_response = Mock()
        mock_part = Mock()
        mock_part.text = "Phase 1 narrative response."
        mock_response.candidates = [Mock(content=Mock(parts=[mock_part]))]
        mock_client.models.generate_content.return_value = mock_response

        with patch.object(gemini_provider, "get_client", return_value=mock_client):
            with patch.object(gemini_provider, "generate_json_mode_content") as mock_json:
                gemini_provider.generate_content_with_native_tools(
                    prompt_contents=["prompt"],
                    model_name="gemini-2.5-flash",
                    system_instruction_text="SYSTEM_INSTRUCTION",
                    temperature=0.7,
                    safety_settings=[],
                    json_mode_max_output_tokens=256,
                )

                _, kwargs = mock_json.call_args
                assert kwargs.get("system_instruction_text") == "SYSTEM_INSTRUCTION"


class TestCodeExecutionFabricationDetection(unittest.TestCase):
    """TDD tests for code_execution fabrication detection edge cases."""

    def test_empty_evidence_dict_flags_fabrication_when_dice_present(self):
        """Empty evidence dict should still evaluate fabrication when dice are present."""
        from types import SimpleNamespace
        from mvp_site.dice_integrity import _is_code_execution_fabrication

        structured = SimpleNamespace(dice_rolls=["1d20 = 12"])
        evidence = {}

        self.assertTrue(
            _is_code_execution_fabrication(structured, evidence),
            "Empty evidence dict should not bypass fabrication detection",
        )


class TestJSONStdoutValidation(unittest.TestCase):
    """TDD tests for JSON stdout validation from code_execution results."""

    def test_code_execution_result_validates_json_format(self):
        """
        Verify that code_execution stdout is validated as JSON.

        Per Consensus ML synthesis:
        - Code should print JSON to stdout: {"notation":"1d20","rolls":[15],"total":15}
        - Eliminates post-processing errors from model reformatting
        """
        from mvp_site.llm_providers import gemini_provider

        # Mock response with executable_code_parts that has JSON stdout
        mock_response = Mock()
        mock_part = Mock()
        mock_part.executable_code = Mock(
            language='python',
            code='import random; print(\'{"notation":"1d20","rolls":[15],"total":15}\')'
        )
        mock_part.code_execution_result = Mock(
            outcome='OUTCOME_OK',
            output='{"notation":"1d20","rolls":[15],"total":15}'
        )
        mock_response.candidates = [Mock(content=Mock(parts=[mock_part]))]
        mock_response.text = '{"narrative": "You rolled 15!", "dice_rolls": ["1d20 = 15"]}'

        # Extract and validate code execution evidence
        evidence = gemini_provider.extract_code_execution_evidence(mock_response)

        # Should validate that stdout is valid JSON
        self.assertTrue(
            evidence.get('code_execution_used', False),
            "Should detect code execution was used"
        )

        # Should parse stdout as JSON
        stdout = evidence.get('stdout', '')
        self.assertIsNotNone(stdout, "Should extract stdout")

        # This will FAIL until we add JSON validation
        try:
            json_output = json.loads(stdout)
            self.assertIn('notation', json_output, "Should have notation field")
            self.assertIn('rolls', json_output, "Should have rolls field")
            self.assertIn('total', json_output, "Should have total field")
        except json.JSONDecodeError:
            self.fail("Code execution stdout should be valid JSON")


class TestRNGVerification(unittest.TestCase):
    """Tests for RNG verification in code execution dice rolls.

    ISSUE: Chi-square 411.81 (vs expected 19-30) shows dice distribution is
    "statistically impossible" from true RNG. LLM fabricates via:
        print('{"rolls": [16], "total": 21}')  # No random.randint()!

    These tests verify that:
    1. Code execution WITHOUT random.randint() is detected as fabrication
    2. Code execution WITH random.randint() passes verification
    3. The rng_verified field is present in evidence
    """

    @staticmethod
    def _make_mock_response(code: str, output: str = '{"rolls": [15], "total": 15}'):
        mock_response = Mock()
        mock_part = Mock()
        mock_part.executable_code = Mock(
            language='python',
            code=code,
        )
        mock_part.code_execution_result = Mock(
            outcome='OUTCOME_OK',
            output=output,
        )
        mock_response.candidates = [Mock(content=Mock(parts=[mock_part]))]
        return mock_response

    def test_fabrication_detected_when_code_lacks_rng(self):
        """
        Code that prints JSON without random.randint() should be FABRICATION.

        When rng_verified=False (code executed but no RNG detected),
        _is_code_execution_fabrication should return True.
        """
        from types import SimpleNamespace
        from mvp_site.dice_integrity import _is_code_execution_fabrication

        structured = SimpleNamespace(dice_rolls=["1d20 = 16"], dice_audit_events=None)

        # Code executed but NO random.randint() - this is fabrication!
        evidence_no_rng = {
            "code_execution_used": True,
            "executable_code_parts": 1,
            "code_execution_result_parts": 1,
            "stdout": '{"rolls": [16], "total": 21}',
            "stdout_is_valid_json": True,
            "code_contains_rng": False,
            "rng_verified": False,
        }

        # This SHOULD be True (fabrication detected) but currently returns False
        # because existing code only checks code_execution_used
        self.assertTrue(
            _is_code_execution_fabrication(structured, evidence_no_rng),
            "Code execution WITHOUT random.randint() should be detected as FABRICATION"
        )

    def test_extract_evidence_includes_rng_verified_field(self):
        """
        extract_code_execution_evidence should return rng_verified field.
        """
        from mvp_site.llm_providers import gemini_provider

        mock_response = Mock()
        mock_part = Mock()
        # Code that fabricates values without RNG
        mock_part.executable_code = Mock(
            language='python',
            code='import json; print(json.dumps({"rolls": [16], "total": 21}))'
        )
        mock_part.code_execution_result = Mock(
            outcome='OUTCOME_OK',
            output='{"rolls": [16], "total": 21}'
        )
        mock_response.candidates = [Mock(content=Mock(parts=[mock_part]))]

        evidence = gemini_provider.extract_code_execution_evidence(mock_response)

        self.assertIn(
            'rng_verified', evidence,
            "Evidence should include 'rng_verified' field"
        )
        self.assertFalse(
            evidence.get('rng_verified', True),
            "rng_verified should be False when code lacks random.randint()"
        )

    def test_valid_rng_passes_verification(self):
        """
        This tests the positive case - legitimate dice rolls with actual RNG.
        """
        from types import SimpleNamespace
        from mvp_site.dice_integrity import _is_code_execution_fabrication

        structured = SimpleNamespace(dice_rolls=["1d20 = 15"], dice_audit_events=None)

        # Code executed WITH random.randint() - this is LEGITIMATE
        evidence_with_rng = {
            "code_execution_used": True,
            "executable_code_parts": 1,
            "code_execution_result_parts": 1,
            "stdout": '{"rolls": [15], "total": 20}',
            "stdout_is_valid_json": True,
            "code_contains_rng": True,
            "rng_verified": True,
        }

        # This should be False (NOT fabrication) - dice came from real RNG
        self.assertFalse(
            _is_code_execution_fabrication(structured, evidence_with_rng),
            "Code with random.randint() should NOT be flagged as fabrication"
        )

    def test_extract_evidence_detects_rng_in_code(self):
        """
        extract_code_execution_evidence should detect RNG in code.
        """
        from mvp_site.llm_providers import gemini_provider

        # Code that actually uses random.randint
        mock_response = self._make_mock_response(
            'import random, json; roll = random.randint(1, 20); '
            'print(json.dumps({"rolls": [roll], "total": roll}))'
        )

        evidence = gemini_provider.extract_code_execution_evidence(mock_response)

        self.assertTrue(evidence.get('code_execution_used'), "Should detect code execution")
        self.assertTrue(evidence.get('code_contains_rng'), "Should detect RNG in code")
        self.assertTrue(evidence.get('rng_verified'), "Should verify RNG usage")

    def test_extract_evidence_detects_rng_from_imported_randint(self):
        from mvp_site.llm_providers import gemini_provider

        mock_response = self._make_mock_response(
            'from random import randint; import json; roll = randint(1, 20); '
            'print(json.dumps({"rolls": [roll], "total": roll}))'
        )
        evidence = gemini_provider.extract_code_execution_evidence(mock_response)
        self.assertTrue(evidence.get('code_contains_rng'), "Should detect RNG for from-import randint")
        self.assertTrue(evidence.get('rng_verified'), "Should verify RNG usage for from-import randint")

    def test_extract_evidence_detects_rng_for_numpy_alias(self):
        from mvp_site.llm_providers import gemini_provider

        mock_response = self._make_mock_response(
            'import numpy as np, json; roll = np.random.randint(1, 21); '
            'print(json.dumps({"rolls": [int(roll)], "total": int(roll)}))'
        )
        evidence = gemini_provider.extract_code_execution_evidence(mock_response)
        self.assertTrue(evidence.get('code_contains_rng'), "Should detect RNG for numpy alias")
        self.assertTrue(evidence.get('rng_verified'), "Should verify RNG usage for numpy alias")

    def test_extract_evidence_detects_rng_for_default_rng_generator(self):
        from mvp_site.llm_providers import gemini_provider

        mock_response = self._make_mock_response(
            'import numpy as np, json; rng = np.random.default_rng(); '
            'roll = rng.integers(1, 21); '
            'print(json.dumps({"rolls": [int(roll)], "total": int(roll)}))'
        )
        evidence = gemini_provider.extract_code_execution_evidence(mock_response)
        self.assertTrue(evidence.get('code_contains_rng'), "Should detect RNG for default_rng generator")
        self.assertTrue(evidence.get('rng_verified'), "Should verify RNG usage for default_rng generator")

    def test_extract_evidence_detects_rng_for_system_random_chain(self):
        from mvp_site.llm_providers import gemini_provider

        mock_response = self._make_mock_response(
            'import random, json; roll = random.SystemRandom().randint(1, 20); '
            'print(json.dumps({"rolls": [roll], "total": roll}))'
        )
        evidence = gemini_provider.extract_code_execution_evidence(mock_response)
        self.assertTrue(evidence.get('code_contains_rng'), "Should detect RNG for SystemRandom chain")
        self.assertTrue(evidence.get('rng_verified'), "Should verify RNG usage for SystemRandom chain")


class TestSystemPromptEnforcementWarning(unittest.TestCase):
    """TDD tests for system prompt enforcement warning in code_execution mode.

    RED test: Verify that the enforcement warning text is actually passed to
    generate_json_mode_content when using code_execution mode.

    This test would FAIL if the warning text was removed from gemini_provider.py.
    """

    def test_RED_enforcement_warning_is_passed_to_llm(self):
        """
        RED: Verify system prompt includes enforcement warning text.

        The PR added these critical phrases to prevent fabrication:
        - "ENFORCEMENT WARNING"
        - "IS INSPECTED"
        - "WILL BE REJECTED"

        This test captures the system_instruction_text passed to generate_json_mode_content
        and verifies these phrases are present.
        """
        from mvp_site.llm_providers import gemini_provider

        captured_system_instruction = None

        def capture_system_instruction(**kwargs):
            nonlocal captured_system_instruction
            captured_system_instruction = kwargs.get("system_instruction_text", "")
            # Return a mock response
            return Mock(text='{"narrative": "test", "dice_rolls": []}')

        with patch.object(
            gemini_provider, "generate_json_mode_content", side_effect=capture_system_instruction
        ):
            gemini_provider.generate_content_with_code_execution(
                prompt_contents=["Test prompt"],
                model_name="gemini-3-flash-preview",
                system_instruction_text="Base system instruction",
                temperature=0.7,
                safety_settings=[],
                json_mode_max_output_tokens=256,
            )

        # Assert enforcement warning phrases are present
        self.assertIsNotNone(
            captured_system_instruction,
            "RED: system_instruction_text should be captured"
        )
        self.assertIn(
            "ENFORCEMENT WARNING",
            captured_system_instruction,
            "RED: System prompt must include 'ENFORCEMENT WARNING' section"
        )
        self.assertIn(
            "IS INSPECTED",
            captured_system_instruction,
            "RED: System prompt must warn that code 'IS INSPECTED'"
        )
        self.assertIn(
            "WILL BE REJECTED",
            captured_system_instruction,
            "RED: System prompt must warn that fabrication 'WILL BE REJECTED'"
        )

    def test_RED_fabrication_example_is_documented(self):
        """
        RED: Verify system prompt documents the specific fabrication pattern.

        The PR added an explicit example of the fabrication pattern that was caught:
        - "print('{\"rolls\": [16]}') without RNG"

        This ensures LLMs know exactly what pattern is detected and rejected.
        """
        from mvp_site.llm_providers import gemini_provider

        captured_system_instruction = None

        def capture_system_instruction(**kwargs):
            nonlocal captured_system_instruction
            captured_system_instruction = kwargs.get("system_instruction_text", "")
            return Mock(text='{"narrative": "test", "dice_rolls": []}')

        with patch.object(
            gemini_provider, "generate_json_mode_content", side_effect=capture_system_instruction
        ):
            gemini_provider.generate_content_with_code_execution(
                prompt_contents=["Test prompt"],
                model_name="gemini-3-flash-preview",
                system_instruction_text=None,
                temperature=0.7,
                safety_settings=[],
                json_mode_max_output_tokens=256,
            )

        # Assert fabrication example is documented
        self.assertIn(
            "hardcoded",
            captured_system_instruction.lower(),
            "RED: System prompt must warn about 'hardcoded' values"
        )
        self.assertIn(
            "without RNG",
            captured_system_instruction,
            "RED: System prompt must mention 'without RNG' pattern"
        )


if __name__ == "__main__":
    unittest.main()
