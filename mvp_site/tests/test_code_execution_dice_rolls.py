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
        with patch('mvp_site.llm_providers.gemini_provider.generate_content_with_tool_loop') as mock_tool_loop:
            mock_tool_loop.return_value = Mock(
                text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
            )

            # Call the API function with Gemini 2.0 model
            llm_service._call_llm_api(
                ['test prompt'],
                'gemini-2.0-flash',
                'test logging',
                provider_name=constants.LLM_PROVIDER_GEMINI
            )

            # Verify tool loop was called
            self.assertTrue(
                mock_tool_loop.called,
                "generate_content_with_tool_loop should be called for Gemini models"
            )

            # Verify tools were passed
            call_kwargs = mock_tool_loop.call_args[1] if mock_tool_loop.call_args[1] else {}
            self.assertIn(
                "tools",
                call_kwargs,
                "tools should be passed to Gemini tool loop"
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

        # Check for hybrid dice roll section
        self.assertIn(
            "Dice Roll",
            instruction_content,
            "FAIL: Instruction file missing Dice Roll section"
        )

        # Check for pre-rolled dice strategy (new architecture Dec 2024)
        self.assertIn(
            "pre_rolled_dice",
            instruction_content,
            "FAIL: Instruction file should mention pre_rolled_dice system"
        )

        # Check for usage instructions
        self.assertIn(
            "IN ORDER",
            instruction_content,
            "FAIL: Instruction file should mention using dice values IN ORDER"
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

    def test_api_call_passes_required_params_to_tool_loop(self):
        """
        Verify API calls pass required parameters to tool loop.
        """
        with patch("mvp_site.llm_providers.gemini_provider.generate_content_with_tool_loop") as mock_tool_loop:
            mock_tool_loop.return_value = Mock(
                text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
            )

            llm_service._call_llm_api(
                ["test prompt"],
                "gemini-2.0-flash",
                "test logging",
                provider_name=constants.LLM_PROVIDER_GEMINI
            )

            # Verify tool loop was called with expected params
            self.assertTrue(mock_tool_loop.called)
            call_kwargs = mock_tool_loop.call_args[1]

            # Verify model name is passed
            self.assertEqual(
                call_kwargs.get("model_name"),
                "gemini-2.0-flash",
                "FAIL: model_name not passed to tool loop"
            )

            # Verify temperature is passed
            self.assertEqual(
                call_kwargs.get("temperature"),
                llm_service.TEMPERATURE,
                "FAIL: Temperature not passed to tool loop"
            )

            # Verify tools are passed
            self.assertIsNotNone(
                call_kwargs.get("tools"),
                "FAIL: Tools not passed to tool loop"
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


class TestToolLoopAllCodePaths(unittest.TestCase):
    """
    Comprehensive TDD tests for tool loop - ALL code paths.

    Bug discovered 2025-12-10 (Scene #302, #307):
    When tool loop hits max iterations and the model STILL wants to call
    another tool, we returned CerebrasResponse(text_length=0, tool_calls=1).
    This caused "non-text response" errors.

    Fix: When max iterations reached with empty text + pending tool_calls,
    make one final API call WITHOUT tools to force text generation.

    Code Paths Tested:
    1. Happy path: Model generates text on first call (no tools)
    2. Happy path: Model calls tool once, then generates text
    3. Happy path: Model calls tools multiple times, generates text within limit
    4. Edge case: Max iterations with text (no forced call needed)
    5. Edge case: Max iterations with empty text + tool_calls (forced call)
    """

    def test_path_1_immediate_text_response_no_tools(self):
        """Path 1: Model generates text immediately without calling any tools."""
        text_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": '{"narrative": "Direct text response"}',
                    "tool_calls": None
                },
                "finish_reason": "stop"
            }]
        }

        def mock_post(*args, **kwargs):
            mock_resp = Mock()
            mock_resp.ok = True
            mock_resp.raise_for_status = Mock()
            mock_resp.json.return_value = text_response
            return mock_resp

        with patch("requests.post", side_effect=mock_post):
            with patch.dict(os.environ, {"CEREBRAS_API_KEY": "test-key"}):
                from mvp_site.llm_providers import cerebras_provider

                result = cerebras_provider.generate_content_with_tool_loop(
                    prompt_contents=["Generate narrative"],
                    model_name="zai-glm-4.6",
                    system_instruction_text=None,
                    temperature=0.7,
                    max_output_tokens=8000,
                    tools=[{"type": "function", "function": {"name": "roll_dice"}}],
                    max_iterations=5,
                )

                self.assertIn("narrative", result.text)
                self.assertEqual(result.text, '{"narrative": "Direct text response"}')

    def test_path_2_single_tool_call_then_text(self):
        """Path 2: Model calls one tool, then generates text."""
        call_count = [0]

        tool_call_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "roll_dice",
                            "arguments": '{"notation": "1d20"}'
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }]
        }

        text_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": '{"narrative": "After the dice roll..."}',
                    "tool_calls": None
                },
                "finish_reason": "stop"
            }]
        }

        def mock_post(*args, **kwargs):
            call_count[0] += 1
            mock_resp = Mock()
            mock_resp.ok = True
            mock_resp.raise_for_status = Mock()
            mock_resp.json.return_value = tool_call_response if call_count[0] == 1 else text_response
            return mock_resp

        with patch("requests.post", side_effect=mock_post):
            with patch.dict(os.environ, {"CEREBRAS_API_KEY": "test-key"}):
                from mvp_site.llm_providers import cerebras_provider

                result = cerebras_provider.generate_content_with_tool_loop(
                    prompt_contents=["Generate narrative"],
                    model_name="zai-glm-4.6",
                    system_instruction_text=None,
                    temperature=0.7,
                    max_output_tokens=8000,
                    tools=[{"type": "function", "function": {"name": "roll_dice"}}],
                    max_iterations=5,
                )

                self.assertEqual(call_count[0], 2, "Should make 2 API calls")
                self.assertIn("After the dice roll", result.text)

    def test_path_3_multiple_tool_calls_within_limit(self):
        """Path 3: Model calls tools 3 times, then generates text (within limit)."""
        call_count = [0]

        tool_call_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_x",
                        "type": "function",
                        "function": {"name": "roll_dice", "arguments": '{"notation": "1d20"}'}
                    }]
                },
                "finish_reason": "tool_calls"
            }]
        }

        text_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": '{"narrative": "Three rolls complete"}',
                    "tool_calls": None
                },
                "finish_reason": "stop"
            }]
        }

        def mock_post(*args, **kwargs):
            call_count[0] += 1
            mock_resp = Mock()
            mock_resp.ok = True
            mock_resp.raise_for_status = Mock()
            # First 3 calls return tool_calls, 4th returns text
            mock_resp.json.return_value = tool_call_response if call_count[0] <= 3 else text_response
            return mock_resp

        with patch("requests.post", side_effect=mock_post):
            with patch.dict(os.environ, {"CEREBRAS_API_KEY": "test-key"}):
                from mvp_site.llm_providers import cerebras_provider

                result = cerebras_provider.generate_content_with_tool_loop(
                    prompt_contents=["Generate narrative"],
                    model_name="zai-glm-4.6",
                    system_instruction_text=None,
                    temperature=0.7,
                    max_output_tokens=8000,
                    tools=[{"type": "function", "function": {"name": "roll_dice"}}],
                    max_iterations=5,
                )

                self.assertEqual(call_count[0], 4, "Should make 4 API calls (3 tools + 1 text)")
                self.assertIn("Three rolls complete", result.text)

    def test_path_4_max_iterations_with_text_already_present(self):
        """Path 4: Max iterations reached but last response HAS text (no forced call)."""
        call_count = [0]

        # Response with BOTH tool_calls AND text (some models do this)
        mixed_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": '{"narrative": "Partial response with text"}',
                    "tool_calls": [{
                        "id": "call_x",
                        "type": "function",
                        "function": {"name": "roll_dice", "arguments": '{"notation": "1d20"}'}
                    }]
                },
                "finish_reason": "tool_calls"
            }]
        }

        def mock_post(*args, **kwargs):
            call_count[0] += 1
            mock_resp = Mock()
            mock_resp.ok = True
            mock_resp.raise_for_status = Mock()
            mock_resp.json.return_value = mixed_response
            return mock_resp

        with patch("requests.post", side_effect=mock_post):
            with patch.dict(os.environ, {"CEREBRAS_API_KEY": "test-key"}):
                from mvp_site.llm_providers import cerebras_provider

                result = cerebras_provider.generate_content_with_tool_loop(
                    prompt_contents=["Generate narrative"],
                    model_name="zai-glm-4.6",
                    system_instruction_text=None,
                    temperature=0.7,
                    max_output_tokens=8000,
                    tools=[{"type": "function", "function": {"name": "roll_dice"}}],
                    max_iterations=5,
                )

                # Text already present, no extra call needed
                self.assertEqual(call_count[0], 5, "Should make exactly 5 API calls")
                self.assertIn("Partial response with text", result.text)

    def test_path_5_max_iterations_empty_text_forces_final_call(self):
        """
        RED-GREEN test: Tool loop should NEVER return empty text.

        When max iterations reached and response has empty text with pending
        tool_calls, the loop should make one final call without tools to
        force text generation.
        """
        from mvp_site.llm_providers.cerebras_provider import CerebrasResponse

        # Simulate: Model keeps calling tools 5 times, never generates text
        tool_call_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,  # Empty text!
                    "tool_calls": [{
                        "id": "call_infinite",
                        "type": "function",
                        "function": {
                            "name": "roll_dice",
                            "arguments": '{"notation": "1d20", "purpose": "endless loop"}'
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }]
        }

        # Final response with actual text (after tools disabled)
        text_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": '{"narrative": "The dice roll resulted in success."}',
                    "tool_calls": None
                },
                "finish_reason": "stop"
            }]
        }

        call_count = [0]

        def mock_post(*args, **kwargs):
            call_count[0] += 1
            mock_resp = Mock()
            mock_resp.ok = True
            mock_resp.raise_for_status = Mock()

            # First 5 calls: return tool_calls with no text
            # 6th call (final, no tools): return text
            if call_count[0] <= 5:
                mock_resp.json.return_value = tool_call_response
            else:
                mock_resp.json.return_value = text_response

            return mock_resp

        with patch("requests.post", side_effect=mock_post):
            with patch.dict(os.environ, {"CEREBRAS_API_KEY": "test-key"}):
                from mvp_site.llm_providers import cerebras_provider

                result = cerebras_provider.generate_content_with_tool_loop(
                    prompt_contents=["Generate a narrative"],
                    model_name="zai-glm-4.6",
                    system_instruction_text="You are a DM",
                    temperature=0.7,
                    max_output_tokens=8000,
                    tools=[{"type": "function", "function": {"name": "roll_dice"}}],
                    max_iterations=5,
                )

                # CRITICAL ASSERTION: We should NEVER get empty text
                self.assertIsNotNone(result.text, "Tool loop should never return None text")
                self.assertNotEqual(result.text, "", "Tool loop should never return empty text")
                self.assertIn("narrative", result.text, "Final response should be valid JSON")

                # Should have made 6 calls: 5 with tools + 1 final without tools
                self.assertEqual(
                    call_count[0], 6,
                    f"Expected 6 API calls (5 with tools + 1 final), got {call_count[0]}"
                )


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

    def test_call_llm_api_routes_to_tool_loop_for_tool_use_models(self):
        """
        Verify _call_llm_api routes to tool loop for models with tool_use capability.

        ARCHITECTURE UPDATE (Dec 2024): Models in MODELS_WITH_TOOL_USE use
        generate_content_with_tool_loop for two-phase inference.
        """
        with patch("mvp_site.llm_providers.cerebras_provider.generate_content_with_tool_loop") as mock_tool_loop:
            mock_tool_loop.return_value = Mock(
                text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
            )

            # This model is in MODELS_WITH_TOOL_USE, so should use tool loop
            llm_service._call_llm_api(
                ["test prompt"],
                "qwen-3-235b-a22b-instruct-2507",
                "test logging",
                provider_name=constants.LLM_PROVIDER_CEREBRAS
            )

            # Verify tool loop was called
            self.assertTrue(
                mock_tool_loop.called,
                "generate_content_with_tool_loop should be called for tool_use models",
            )
            # Verify tools were passed (DICE_ROLL_TOOLS)
            call_kwargs = mock_tool_loop.call_args[1] if mock_tool_loop.call_args[1] else {}
            self.assertIn(
                "tools",
                call_kwargs,
                "tools should be passed to tool loop"
            )

    def test_call_llm_api_routes_to_tool_loop_for_all_cerebras_models(self):
        """
        Verify _call_llm_api routes ALL Cerebras models to tool loop.

        ARCHITECTURE UPDATE (Dec 2024): All Cerebras models use tool loop.
        The model decides what dice to roll, server executes with true randomness.
        """
        with patch("mvp_site.llm_providers.cerebras_provider.generate_content_with_tool_loop") as mock_tool_loop:
            mock_tool_loop.return_value = Mock(
                text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
            )

            # Even llama-3.3-70b now uses tool loop
            llm_service._call_llm_api(
                ["test prompt"],
                "llama-3.3-70b",
                "test logging",
                provider_name=constants.LLM_PROVIDER_CEREBRAS
            )

            # Verify tool loop was called
            self.assertTrue(
                mock_tool_loop.called,
                "generate_content_with_tool_loop should be called for ALL Cerebras models",
            )
            # Verify tools were passed (DICE_ROLL_TOOLS)
            call_kwargs = mock_tool_loop.call_args[1] if mock_tool_loop.call_args[1] else {}
            self.assertIn(
                "tools",
                call_kwargs,
                "tools should be passed to tool loop"
            )


if __name__ == "__main__":
    unittest.main()
