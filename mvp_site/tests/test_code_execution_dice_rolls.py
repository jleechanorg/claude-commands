"""
TDD Tests for Hybrid Dice Roll System

Gemini 2.0 and 3.0 models support BOTH code_execution AND JSON mode together.
Gemini 2.5 does NOT support this combination - it uses precompute fallback.

The hybrid dice roll system:
1. Code Execution (Gemini 2.0/3.0): Native Python code execution + JSON mode
2. Tool Use (Cerebras, OpenRouter): Function calling with local execution
3. Pre-computed (fallback): Backend pre-rolls dice and provides values

See: https://ai.google.dev/gemini-api/docs/structured-output

These tests verify:
1. JSON mode is enabled (required for structured output)
2. Code execution IS enabled for Gemini 2.0/3.0 models (they support both)
3. Code execution is NOT enabled for Gemini 2.5 models
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
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


from mvp_site import constants, llm_service


class TestHybridDiceRollSystem(unittest.TestCase):
    """Test the hybrid dice roll system across different model types."""

    def test_gemini_uses_tool_loop_for_dice(self):
        """
        Verify Gemini models use tool loop for dice rolling.

        ARCHITECTURE UPDATE (Dec 2024): All Gemini models now use two-phase
        tool loop. Phase 1 has tools (no JSON), Phase 2 has JSON (no tools).
        """
        # Gemini 2.x now uses JSON-first tool_requests flow (not old tool_loop)
        with patch('mvp_site.llm_providers.gemini_provider.generate_content_with_tool_requests') as mock_tool_requests:
            mock_tool_requests.return_value = Mock(
                text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
            )

            # Call the API function with Gemini 2.0 model
            llm_service._call_llm_api(
                ['test prompt'],
                'gemini-2.0-flash',
                'test logging',
                provider_name=constants.LLM_PROVIDER_GEMINI
            )

            # Verify tool_requests was called
            self.assertTrue(
                mock_tool_requests.called,
                "generate_content_with_tool_requests should be called for Gemini 2.x models"
            )

            # JSON-first flow doesn't pass tools param (model requests via JSON schema)
            call_kwargs = mock_tool_requests.call_args[1] if mock_tool_requests.call_args[1] else {}
            self.assertNotIn(
                "tools",
                call_kwargs,
                "tools should NOT be passed to JSON-first flow (model uses tool_requests in JSON)"
            )

    def test_model_capability_detection(self):
        """
        Verify the model capability detection function works correctly.

        ARCHITECTURE UPDATE (Dec 2024): Strategy now varies by provider:
        - Gemini 3.x: code_execution (single-phase)
        - Gemini 2.x: tool_use_phased (two-phase)
        - Cerebras/OpenRouter with tool support: tool_use (two-phase)
        - Fallback: precompute (pre-rolled dice in prompt)
        """
        # Gemini 3.x models: code_execution (single-phase)
        self.assertEqual(
            constants.get_dice_roll_strategy("gemini-3-pro-preview", "gemini"),
            "code_execution"
        )

        # Gemini 2.x models: tool_use_phased (two-phase)
        self.assertEqual(
            constants.get_dice_roll_strategy("gemini-2.0-flash", "gemini"),
            "tool_use_phased"
        )
        self.assertEqual(
            constants.get_dice_roll_strategy("gemini-2.5-flash", "gemini"),
            "tool_use_phased"
        )

        # Cerebras models with tool support: tool_use
        self.assertEqual(
            constants.get_dice_roll_strategy("qwen-3-235b-a22b-instruct-2507", "cerebras"),
            "tool_use"
        )
        self.assertEqual(
            constants.get_dice_roll_strategy("zai-glm-4.6", "cerebras"),
            "tool_use"
        )

        # OpenRouter models with tool support: tool_use
        self.assertEqual(
            constants.get_dice_roll_strategy("meta-llama/llama-3.1-70b-instruct", "openrouter"),
            "tool_use"
        )

        # Models without tool support: precompute
        self.assertEqual(
            constants.get_dice_roll_strategy("llama-3.3-70b", "cerebras"),
            "precompute"
        )

        # Unknown models: precompute
        self.assertEqual(
            constants.get_dice_roll_strategy("unknown-model", ""),
            "precompute"
        )

        # No provider specified: precompute (backwards compatibility)
        self.assertEqual(
            constants.get_dice_roll_strategy("gemini-2.0-flash"),
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

    def test_api_call_passes_required_params_to_tool_requests(self):
        """
        Verify API calls pass required parameters to JSON-first tool_requests flow.

        ARCHITECTURE UPDATE (Dec 2024): Gemini 2.x now uses JSON-first tool_requests
        flow instead of old tool_loop. Tools are NOT passed as API param - model
        requests tools via tool_requests array in JSON schema.
        """
        with patch("mvp_site.llm_providers.gemini_provider.generate_content_with_tool_requests") as mock_tool_requests:
            mock_tool_requests.return_value = Mock(
                text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
            )

            llm_service._call_llm_api(
                ["test prompt"],
                "gemini-2.0-flash",
                "test logging",
                provider_name=constants.LLM_PROVIDER_GEMINI
            )

            # Verify tool_requests was called with expected params
            self.assertTrue(mock_tool_requests.called)
            call_kwargs = mock_tool_requests.call_args[1]

            # Verify model name is passed
            self.assertEqual(
                call_kwargs.get("model_name"),
                "gemini-2.0-flash",
                "FAIL: model_name not passed to tool_requests"
            )

            # Verify temperature is passed
            self.assertEqual(
                call_kwargs.get("temperature"),
                llm_service.TEMPERATURE,
                "FAIL: Temperature not passed to tool_requests"
            )

            # JSON-first flow does NOT pass tools param (model uses JSON schema)
            self.assertIsNone(
                call_kwargs.get("tools"),
                "tools should NOT be passed to JSON-first tool_requests flow"
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
        from mvp_site.game_state import DICE_ROLL_TOOLS

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

        ARCHITECTURE UPDATE (Dec 2024): All Cerebras models use
        generate_content_with_tool_requests for JSON-first two-phase inference.
        This keeps JSON schema enforcement throughout (vs old tool_loop which couldn't).
        """
        with patch("mvp_site.llm_providers.cerebras_provider.generate_content_with_tool_requests") as mock_tool_requests:
            mock_tool_requests.return_value = Mock(
                text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
            )

            # All Cerebras models use tool_requests flow
            llm_service._call_llm_api(
                ["test prompt"],
                "qwen-3-235b-a22b-instruct-2507",
                "test logging",
                provider_name=constants.LLM_PROVIDER_CEREBRAS
            )

            # Verify tool_requests flow was called
            self.assertTrue(
                mock_tool_requests.called,
                "generate_content_with_tool_requests should be called for Cerebras",
            )
            # No tools parameter - JSON-first flow uses tool_requests in schema
            call_kwargs = mock_tool_requests.call_args[1] if mock_tool_requests.call_args[1] else {}
            self.assertNotIn(
                "tools",
                call_kwargs,
                "tools should NOT be passed to tool_requests flow (uses schema instead)"
            )

    def test_call_llm_api_routes_to_tool_requests_for_openrouter(self):
        """
        Verify _call_llm_api routes to JSON-first tool_requests flow for OpenRouter.

        ARCHITECTURE UPDATE (Dec 2024): All OpenRouter models use
        generate_content_with_tool_requests for JSON-first two-phase inference.
        This keeps JSON schema enforcement throughout (vs old tool_loop which couldn't).
        """
        with patch("mvp_site.llm_providers.openrouter_provider.generate_content_with_tool_requests") as mock_tool_requests:
            mock_tool_requests.return_value = Mock(
                text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
            )

            # All OpenRouter models use tool_requests flow
            llm_service._call_llm_api(
                ["test prompt"],
                "meta-llama/llama-3.1-70b-instruct",
                "test logging",
                provider_name=constants.LLM_PROVIDER_OPENROUTER
            )

            # Verify tool_requests flow was called
            self.assertTrue(
                mock_tool_requests.called,
                "generate_content_with_tool_requests should be called for OpenRouter",
            )
            # No tools parameter - JSON-first flow uses tool_requests in schema
            call_kwargs = mock_tool_requests.call_args[1] if mock_tool_requests.call_args[1] else {}
            self.assertNotIn(
                "tools",
                call_kwargs,
                "tools should NOT be passed to tool_requests flow (uses schema instead)"
            )

    def test_call_llm_api_falls_back_to_direct_call_for_unsupported_models(self):
        """
        Verify _call_llm_api falls back to direct call for models NOT in MODELS_WITH_TOOL_USE.

        Models like llama-3.3-70b don't reliably support multi-turn tool calling,
        so they should use direct call without tools.
        """
        with patch("mvp_site.llm_providers.cerebras_provider.generate_content") as mock_direct:
            mock_direct.return_value = Mock(
                text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
            )

            # llama-3.3-70b is NOT in MODELS_WITH_TOOL_USE - should use direct call
            llm_service._call_llm_api(
                ["test prompt"],
                "llama-3.3-70b",
                "test logging",
                provider_name=constants.LLM_PROVIDER_CEREBRAS
            )

            # Verify direct call was used (not tool loop)
            self.assertTrue(
                mock_direct.called,
                "generate_content should be called for models NOT in MODELS_WITH_TOOL_USE",
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
            "tool_requests": [{"tool": "roll_dice", "args": {"dice_notation": "1d20+5"}}],
        })

        # Phase 2 response: Final narrative with results
        phase2_json = json.dumps({
            "narrative": "You rolled a 17! The goblin is hit.",
            "planning_block": {"thinking": "Attack successful"},
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
            self.assertIn("roll_dice", tool_results_msg)

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
            {"tool": "roll_dice", "args": {"dice_notation": "1d20"}},
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
            {"tool": "roll_dice", "args": {"dice_notation": "2d6+3", "purpose": "damage"}},
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


if __name__ == "__main__":
    unittest.main()
