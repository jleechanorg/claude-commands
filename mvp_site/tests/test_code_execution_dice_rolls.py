"""
Tests for code execution and dice rolling integrity.
"""

# ruff: noqa: PT009,N802,SIM117

import inspect
import json
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from mvp_site import constants, llm_service
from mvp_site.dice import DICE_ROLL_TOOLS, execute_dice_tool
from mvp_site.dice_integrity import (
    _extract_dice_audit_events_from_tool_results,
    _is_code_execution_fabrication,
)
from mvp_site.llm_providers import (
    cerebras_provider,
    gemini_code_execution,
    gemini_provider,
    openrouter_provider,
)
from mvp_site.llm_providers.cerebras_provider import (
    CerebrasResponse,
    execute_tool_requests,
)
from mvp_site.llm_providers.openrouter_provider import OpenRouterResponse

# Set TESTING environment variable
os.environ["TESTING"] = "true"

# Add parent directory to path for imports
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
)


class TestCerebrasToolUseIntegration(unittest.TestCase):
    """Test Cerebras provider tool use for dice rolling (two-stage inference)."""

    def test_cerebras_provider_accepts_tools_parameter(self):
        """
        Verify Cerebras provider can accept tools parameter.
        """
        # Check that generate_content accepts tools parameter
        sig = inspect.signature(cerebras_provider.generate_content)
        param_names = list(sig.parameters.keys())

        self.assertIn(
            "tools",
            param_names,
            "FAIL: cerebras_provider.generate_content should accept 'tools' parameter",
        )

    def test_cerebras_response_handles_tool_calls(self):
        """
        Verify CerebrasResponse can extract tool_calls from response.
        """
        # Mock response with tool_calls
        mock_response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_123",
                                "type": "function",
                                "function": {
                                    "name": "roll_dice",
                                    "arguments": '{"notation": "1d20+5"}',
                                },
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ]
        }

        response = CerebrasResponse("", mock_response)

        # Verify tool_calls can be extracted
        self.assertTrue(
            hasattr(response, "tool_calls") or hasattr(response, "get_tool_calls"),
            "FAIL: CerebrasResponse should expose tool_calls",
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
        result = execute_dice_tool(
            "roll_dice", {"notation": "2d6+3", "purpose": "damage"}
        )

        self.assertIn("notation", result)
        self.assertIn("total", result)
        self.assertIn("rolls", result)
        self.assertEqual(result["notation"], "2d6+3")
        self.assertEqual(result["purpose"], "damage")

    def test_execute_dice_tool_roll_attack(self):
        """
        Verify execute_dice_tool handles roll_attack correctly.
        """
        result = execute_dice_tool(
            "roll_attack",
            {"attack_modifier": 5, "damage_notation": "1d8+3", "target_ac": 15},
        )

        self.assertIn("attack_roll", result)
        self.assertIn("target_ac", result)
        self.assertIn("hit", result)
        self.assertEqual(result["target_ac"], 15)

    def test_execute_dice_tool_roll_skill_check(self):
        """
        Verify execute_dice_tool handles roll_skill_check correctly.
        """
        result = execute_dice_tool(
            "roll_skill_check",
            {
                "attribute_modifier": 3,
                "proficiency_bonus": 2,
                "proficient": True,
                "dc": 15,
                "dc_reasoning": "guard is distracted",
                "skill_name": "Stealth",
            },
        )

        self.assertIn("skill", result)
        self.assertIn("total", result)
        self.assertIn("success", result)
        self.assertEqual(result["skill"], "Stealth")

    def test_execute_dice_tool_skill_check_with_dc_reasoning(self):
        """
        Verify roll_skill_check includes dc_reasoning in the result.

        DC reasoning proves that the difficulty was determined BEFORE the roll,
        preventing "just in time" DC manipulation to fit narratives.
        """
        dc_reasoning = "FBI agent, professionally trained to resist manipulation"
        result = execute_dice_tool(
            "roll_skill_check",
            {
                "attribute_modifier": 4,
                "proficiency_bonus": 2,
                "proficient": True,
                "dc": 18,
                "dc_reasoning": dc_reasoning,
                "skill_name": "Persuasion",
            },
        )

        # DC reasoning must be preserved in the result for audit trail
        self.assertIn("dc_reasoning", result)
        self.assertEqual(result["dc_reasoning"], dc_reasoning)
        self.assertEqual(result["dc"], 18)
        # Formatted output must include DC and reasoning details
        self.assertIn("formatted", result)
        self.assertIn("vs DC 18", result["formatted"])
        self.assertIn("FBI agent", result["formatted"])

    def test_execute_dice_tool_saving_throw_with_dc_reasoning(self):
        """
        Verify roll_saving_throw includes dc_reasoning in the result.
        """
        dc_reasoning = "Fireball from 5th-level caster (8+3+3)"
        result = execute_dice_tool(
            "roll_saving_throw",
            {
                "attribute_modifier": 2,
                "proficiency_bonus": 2,
                "proficient": False,
                "dc": 14,
                "dc_reasoning": dc_reasoning,
                "save_type": "DEX",
            },
        )

        # DC reasoning must be preserved in the result for audit trail
        self.assertIn("dc_reasoning", result)
        self.assertEqual(result["dc_reasoning"], dc_reasoning)
        self.assertEqual(result["dc"], 14)
        # Formatted output must include DC and reasoning details
        self.assertIn("formatted", result)
        self.assertIn("vs DC 14", result["formatted"])
        self.assertIn("Fireball", result["formatted"])

    def test_skill_check_returns_error_without_dc_reasoning(self):
        """
        Verify roll_skill_check returns error dict when dc_reasoning is missing.
        """
        result = execute_dice_tool(
            "roll_skill_check",
            {
                "attribute_modifier": 3,
                "proficiency_bonus": 2,
                "dc": 15,
                "skill_name": "Stealth",
                # Missing dc_reasoning
            },
        )
        self.assertIn("error", result)
        self.assertIn("dc_reasoning is required", result["error"])

    def test_saving_throw_returns_error_without_dc_reasoning(self):
        """
        Verify roll_saving_throw returns error dict when dc_reasoning is missing.
        """
        result = execute_dice_tool(
            "roll_saving_throw",
            {
                "attribute_modifier": 2,
                "proficiency_bonus": 2,
                "dc": 14,
                "save_type": "DEX",
                # Missing dc_reasoning
            },
        )
        self.assertIn("error", result)
        self.assertIn("dc_reasoning is required", result["error"])


class TestLLMServiceToolIntegration(unittest.TestCase):
    """Test llm_service integration with tool use providers."""

    def test_call_llm_api_routes_to_tool_requests_for_cerebras(self):
        """
        Verify _call_llm_api routes to JSON-first tool_requests flow for Cerebras.

        ARCHITECTURE UPDATE (Dec 2024): All Cerebras models use JSON-first flow
        to avoid forced tool calls and match prompt documentation.
        Phase 1: JSON with optional tool_requests, Phase 2: JSON with results.
        """
        with patch(
            "mvp_site.llm_providers.cerebras_provider.generate_content_with_tool_requests"
        ) as mock_tool_requests:
            mock_tool_requests.return_value = Mock(
                text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
            )

            # All Cerebras models use JSON-first tool_requests flow
            llm_service._call_llm_api(
                ["test prompt"],
                "qwen-3-235b-a22b-instruct-2507",
                "test logging",
                provider_name=constants.LLM_PROVIDER_CEREBRAS,
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
        with patch(
            "mvp_site.llm_providers.openrouter_provider.generate_content_with_tool_requests"
        ) as mock_tool_requests:
            mock_tool_requests.return_value = Mock(
                text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
            )

            # All OpenRouter models use JSON-first tool_requests flow
            llm_service._call_llm_api(
                ["test prompt"],
                "meta-llama/llama-3.1-70b-instruct",
                "test logging",
                provider_name=constants.LLM_PROVIDER_OPENROUTER,
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
        with patch(
            "mvp_site.llm_providers.cerebras_provider.generate_content_with_tool_requests"
        ) as mock_tool_requests:
            mock_tool_requests.return_value = Mock(
                text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
            )

            # ALL Cerebras models now use JSON-first tool_requests (including llama-3.3-70b)
            llm_service._call_llm_api(
                ["test prompt"],
                "llama-3.3-70b",
                "test logging",
                provider_name=constants.LLM_PROVIDER_CEREBRAS,
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
        # Phase 1 response: No tool_requests
        phase1_json = json.dumps(
            {
                "narrative": "You look around the room.",
                "planning_block": {"thinking": "Observing surroundings"},
            }
        )

        with patch.object(cerebras_provider, "generate_content") as mock_gen:
            mock_gen.return_value = CerebrasResponse(
                text=phase1_json, raw_response=None
            )

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
        # Phase 1 response: Has tool_requests
        phase1_json = json.dumps(
            {
                "narrative": "You attack the goblin!",
                "tool_requests": [
                    {"tool": "roll_dice", "args": {"notation": "1d20+5"}}
                ],
            }
        )

        # Phase 2 response: Final narrative with results
        phase2_json = json.dumps(
            {
                "narrative": "You rolled a 17! The goblin is hit.",
                "planning_block": {"thinking": "Attack successful"},
                "dice_rolls": ["17"],
            }
        )

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
            self.assertTrue(
                len(messages) >= 3, "Phase 2 should have messages with tool results"
            )

            # Check that tool results message is included
            tool_results_msg = messages[-1]["content"]
            self.assertIn("Tool results", tool_results_msg)
            # The formatted output contains the calculation (e.g. "1d20+5 = 3+5 = 8")
            # but NOT necessarily the tool name "roll_dice"
            self.assertIn("1d20+5", tool_results_msg)

    def test_path3_invalid_json_returns_as_is(self):
        """Path 3: Non-JSON response returns as-is without Phase 2."""
        invalid_response = "This is not valid JSON"

        with patch.object(cerebras_provider, "generate_content") as mock_gen:
            mock_gen.return_value = CerebrasResponse(
                text=invalid_response, raw_response=None
            )

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
        tool_requests = [
            {"tool": "roll_dice", "args": {"notation": "2d6+3", "purpose": "damage"}},
            {"tool": "roll_attack", "args": {"attack_modifier": 5, "target_ac": 15}},
            {
                "tool": "roll_skill_check",
                "args": {
                    "skill_name": "Perception",
                    "attribute_modifier": 2,
                    "proficiency_bonus": 2,
                    "proficient": True,
                    "dc": 12,
                    "dc_reasoning": "Normal perception check in dim light",
                },
            },
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

        # Verify skill_check result succeeded
        self.assertNotIn(
            "error",
            results[2]["result"],
            f"Skill check failed: {results[2]['result']}",
        )
        self.assertIn("success", results[2]["result"])

    def test_openrouter_path1_no_tool_requests(self):
        """Test OpenRouter provider Path 1: No tool_requests."""

        phase1_json = json.dumps(
            {
                "narrative": "The forest is peaceful.",
                "planning_block": {"thinking": "Peaceful scene"},
            }
        )

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

        phase1_json = json.dumps(
            {
                "narrative": "You attempt a skill check.",
                "tool_requests": [
                    {
                        "tool": "roll_skill_check",
                        "args": {
                            "skill_name": "Stealth",
                            "attribute_modifier": 4,
                            "proficiency_bonus": 2,
                            "proficient": True,
                            "dc": 12,
                            "dc_reasoning": "Guard is distracted",
                        },
                    }
                ],
            }
        )

        phase2_json = json.dumps(
            {
                "narrative": "You rolled a 16! You move silently.",
                "planning_block": {"thinking": "Stealth success"},
                "dice_rolls": ["16"],
            }
        )

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

        # Mock get_client to return a fake client that captures config
        mock_client = Mock()
        mock_response = Mock(text='{"narrative": "test", "dice_rolls": []}')
        mock_client.models.generate_content.return_value = mock_response

        with patch.object(gemini_provider, "get_client", return_value=mock_client):
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
            "Should call Client.models.generate_content",
        )

        # Get the config from the call
        call_args = mock_client.models.generate_content.call_args
        if call_args is None:
            self.fail("generate_content was not called")

        config = call_args.kwargs.get("config")
        self.assertIsNotNone(config, "Should pass config")

        # Verify thinking_config is present
        self.assertIsNotNone(
            getattr(config, "thinking_config", None),
            "Config should have thinking_config attribute",
        )


class TestNativeToolsSystemInstruction(unittest.TestCase):
    """TDD tests for native two-phase system instruction retention."""

    def test_native_phase2_keeps_system_instruction_when_phase1_text_exists(self):
        mock_client = Mock()
        mock_response = Mock()
        mock_part = Mock()
        mock_part.text = "Phase 1 narrative response."
        mock_response.candidates = [Mock(content=Mock(parts=[mock_part]))]
        mock_client.models.generate_content.return_value = mock_response

        with patch.object(gemini_provider, "get_client", return_value=mock_client):
            with patch.object(
                gemini_provider, "generate_json_mode_content"
            ) as mock_json:
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

        # Mock response with executable_code_parts that has JSON stdout
        mock_response = Mock()
        mock_part = Mock()
        mock_part.executable_code = Mock(
            language="python",
            code='import random; print(\'{"notation":"1d20","rolls":[15],"total":15}\')',
        )
        mock_part.code_execution_result = Mock(
            outcome="OUTCOME_OK", output='{"notation":"1d20","rolls":[15],"total":15}'
        )
        mock_response.candidates = [Mock(content=Mock(parts=[mock_part]))]
        mock_response.text = (
            '{"narrative": "You rolled 15!", "dice_rolls": ["1d20 = 15"]}'
        )

        # Extract and validate code execution evidence
        evidence = gemini_provider.extract_code_execution_evidence(mock_response)

        # Should validate that stdout is valid JSON
        self.assertTrue(
            evidence.get("code_execution_used", False),
            "Should detect code execution was used",
        )

        # Should parse stdout as JSON
        stdout = evidence.get("stdout", "")
        self.assertIsNotNone(stdout, "Should extract stdout")

        # This will FAIL until we add JSON validation
        try:
            json_output = json.loads(stdout)
            self.assertIn("notation", json_output, "Should have notation field")
            self.assertIn("rolls", json_output, "Should have rolls field")
            self.assertIn("total", json_output, "Should have total field")
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
            language="python",
            code=code,
        )
        mock_part.code_execution_result = Mock(
            outcome="OUTCOME_OK",
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
            "Code execution WITHOUT random.randint() should be detected as FABRICATION",
        )

    def test_extract_evidence_includes_rng_verified_field(self):
        """
        extract_code_execution_evidence should return rng_verified field.
        """

        mock_response = Mock()
        mock_part = Mock()
        # Code that fabricates values without RNG
        mock_part.executable_code = Mock(
            language="python",
            code='import json; print(json.dumps({"rolls": [16], "total": 21}))',
        )
        mock_part.code_execution_result = Mock(
            outcome="OUTCOME_OK", output='{"rolls": [16], "total": 21}'
        )
        mock_response.candidates = [Mock(content=Mock(parts=[mock_part]))]

        evidence = gemini_provider.extract_code_execution_evidence(mock_response)

        self.assertIn(
            "rng_verified", evidence, "Evidence should include 'rng_verified' field"
        )
        self.assertFalse(
            evidence.get("rng_verified", True),
            "rng_verified should be False when code lacks random.randint()",
        )

    def test_valid_rng_passes_verification(self):
        """
        This tests the positive case - legitimate dice rolls with actual RNG.
        """

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
            "Code with random.randint() should NOT be flagged as fabrication",
        )

    def test_extract_evidence_detects_rng_in_code(self):
        """
        extract_code_execution_evidence should detect RNG in code.
        """

        # Code that actually uses random.randint
        mock_response = self._make_mock_response(
            "import random, json; roll = random.randint(1, 20); "
            'print(json.dumps({"rolls": [roll], "total": roll}))'
        )

        evidence = gemini_provider.extract_code_execution_evidence(mock_response)

        self.assertTrue(
            evidence.get("code_execution_used"), "Should detect code execution"
        )
        self.assertTrue(evidence.get("code_contains_rng"), "Should detect RNG in code")
        self.assertTrue(evidence.get("rng_verified"), "Should verify RNG usage")

    def test_extract_evidence_detects_rng_from_imported_randint(self):
        mock_response = self._make_mock_response(
            "from random import randint; import json; roll = randint(1, 20); "
            'print(json.dumps({"rolls": [roll], "total": roll}))'
        )
        evidence = gemini_provider.extract_code_execution_evidence(mock_response)
        self.assertTrue(
            evidence.get("code_contains_rng"),
            "Should detect RNG for from-import randint",
        )
        self.assertTrue(
            evidence.get("rng_verified"),
            "Should verify RNG usage for from-import randint",
        )

    def test_extract_evidence_detects_rng_for_numpy_alias(self):
        mock_response = self._make_mock_response(
            "import numpy as np, json; roll = np.random.randint(1, 21); "
            'print(json.dumps({"rolls": [int(roll)], "total": int(roll)}))'
        )
        evidence = gemini_provider.extract_code_execution_evidence(mock_response)
        self.assertTrue(
            evidence.get("code_contains_rng"), "Should detect RNG for numpy alias"
        )
        self.assertTrue(
            evidence.get("rng_verified"), "Should verify RNG usage for numpy alias"
        )

    def test_extract_evidence_detects_rng_for_default_rng_generator(self):
        mock_response = self._make_mock_response(
            "import numpy as np, json; rng = np.random.default_rng(); "
            "roll = rng.integers(1, 21); "
            'print(json.dumps({"rolls": [int(roll)], "total": int(roll)}))'
        )
        evidence = gemini_provider.extract_code_execution_evidence(mock_response)
        self.assertTrue(
            evidence.get("code_contains_rng"),
            "Should detect RNG for default_rng generator",
        )
        self.assertTrue(
            evidence.get("rng_verified"),
            "Should verify RNG usage for default_rng generator",
        )

    def test_extract_evidence_detects_rng_for_system_random_chain(self):
        mock_response = self._make_mock_response(
            "import random, json; roll = random.SystemRandom().randint(1, 20); "
            'print(json.dumps({"rolls": [roll], "total": roll}))'
        )
        evidence = gemini_provider.extract_code_execution_evidence(mock_response)
        self.assertTrue(
            evidence.get("code_contains_rng"),
            "Should detect RNG for SystemRandom chain",
        )
        self.assertTrue(
            evidence.get("rng_verified"),
            "Should verify RNG usage for SystemRandom chain",
        )


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

        captured_system_instruction = None

        def capture_system_instruction(**kwargs):
            nonlocal captured_system_instruction
            captured_system_instruction = kwargs.get("system_instruction_text", "")
            # Return a mock response
            return Mock(text='{"narrative": "test", "dice_rolls": []}')

        with patch.object(
            gemini_provider,
            "generate_json_mode_content",
            side_effect=capture_system_instruction,
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
            "RED: system_instruction_text should be captured",
        )
        self.assertIn(
            "ENFORCEMENT WARNING",
            captured_system_instruction,
            "RED: System prompt must include 'ENFORCEMENT WARNING' section",
        )
        self.assertIn(
            "IS INSPECTED",
            captured_system_instruction,
            "RED: System prompt must warn that code 'IS INSPECTED'",
        )
        self.assertIn(
            "WILL BE REJECTED",
            captured_system_instruction,
            "RED: System prompt must warn that fabrication 'WILL BE REJECTED'",
        )

    def test_RED_fabrication_example_is_documented(self):
        """
        RED: Verify system prompt documents the specific fabrication pattern.

        The PR added an explicit example of the fabrication pattern that was caught:
        - "print('{\"rolls\": [16]}') without RNG"

        This ensures LLMs know exactly what pattern is detected and rejected.
        """

        captured_system_instruction = None

        def capture_system_instruction(**kwargs):
            nonlocal captured_system_instruction
            captured_system_instruction = kwargs.get("system_instruction_text", "")
            return Mock(text='{"narrative": "test", "dice_rolls": []}')

        with patch.object(
            gemini_provider,
            "generate_json_mode_content",
            side_effect=capture_system_instruction,
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
            "RED: System prompt must warn about 'hardcoded' values",
        )
        self.assertIn(
            "without RNG",
            captured_system_instruction,
            "RED: System prompt must mention 'without RNG' pattern",
        )


class TestDCAuditTrail(unittest.TestCase):
    """Test that DC and dc_reasoning are properly captured in audit events."""

    def test_dice_audit_events_include_dc_for_skill_check(self):
        """
        Verify that dice_audit_events extraction includes DC and dc_reasoning.

        This is critical for proving mechanical fairness - users can see
        that the DC was determined BEFORE the roll result was known.
        """
        tool_results = [
            {
                "tool": "roll_skill_check",
                "args": {
                    "skill_name": "Persuasion",
                    "dc": 18,
                    "dc_reasoning": "FBI agent, trained to resist",
                },
                "result": {
                    "skill": "Persuasion",
                    "roll": 14,
                    "modifier": 6,
                    "total": 20,
                    "dc": 18,
                    "dc_reasoning": "FBI agent, trained to resist",
                    "success": True,
                },
            }
        ]

        events = _extract_dice_audit_events_from_tool_results(tool_results)

        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event["label"], "Persuasion")
        self.assertEqual(event["total"], 20)
        # Critical: DC and reasoning must be in the audit event
        self.assertEqual(event["dc"], 18)
        self.assertEqual(event["dc_reasoning"], "FBI agent, trained to resist")
        self.assertTrue(event["success"])

    def test_dice_audit_events_include_dc_for_saving_throw(self):
        """
        Verify that dice_audit_events extraction includes DC and dc_reasoning for saves.
        """
        tool_results = [
            {
                "tool": "roll_saving_throw",
                "args": {
                    "save_type": "DEX",
                    "dc": 14,
                    "dc_reasoning": "Fireball DC 14",
                },
                "result": {
                    "save_type": "DEX",
                    "roll": 8,
                    "modifier": 2,
                    "total": 10,
                    "dc": 14,
                    "dc_reasoning": "Fireball DC 14",
                    "success": False,
                },
            }
        ]

        events = _extract_dice_audit_events_from_tool_results(tool_results)

        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event["label"], "DEX Save")
        self.assertEqual(event["total"], 10)
        # Critical: DC and reasoning must be in the audit event
        self.assertEqual(event["dc"], 14)
        self.assertEqual(event["dc_reasoning"], "Fireball DC 14")
        self.assertFalse(event["success"])


class TestCodeExecutionIntegrity(unittest.TestCase):
    """Test cases for code execution integrity and safety."""

    def test_extract_code_execution_evidence_finds_usage(self):
        """Should detect when code execution was used in response."""
        mock_response = Mock()
        mock_part = Mock()
        mock_part.executable_code = Mock(language="python", code="print('hello')")
        mock_part.code_execution_result = Mock(outcome="OUTCOME_OK", output="hello")
        mock_response.candidates = [Mock(content=Mock(parts=[mock_part]))]

        evidence = gemini_code_execution.extract_code_execution_evidence(mock_response)

        self.assertTrue(evidence["code_execution_used"])
        self.assertEqual(evidence["executable_code_parts"], 1)
        self.assertEqual(evidence["code_execution_result_parts"], 1)
        self.assertEqual(evidence["stdout"], "hello")

    def test_extract_code_execution_evidence_no_usage(self):
        """Should handle responses without code execution."""
        mock_response = Mock()
        mock_part = Mock()
        # Ensure these attributes don't exist to simulate plain text response
        del mock_part.executable_code
        del mock_part.code_execution_result
        mock_part.text = "Just text"
        mock_response.candidates = [Mock(content=Mock(parts=[mock_part]))]

        evidence = gemini_code_execution.extract_code_execution_evidence(mock_response)

        self.assertFalse(evidence["code_execution_used"])
        self.assertEqual(evidence["executable_code_parts"], 0)
        self.assertEqual(evidence["code_execution_result_parts"], 0)

    def test_extract_code_execution_parts_summary(self):
        """Should generate readable summary of code execution."""
        mock_response = Mock()
        mock_part1 = Mock()
        mock_part1.executable_code = Mock(language="python", code="x = 1")
        mock_part2 = Mock()
        mock_part2.code_execution_result = Mock(outcome="OUTCOME_OK", output="")
        mock_response.candidates = [Mock(content=Mock(parts=[mock_part1, mock_part2]))]

        summary = gemini_code_execution.extract_code_execution_parts_summary(
            mock_response
        )

        self.assertTrue(summary["code_execution_used"])
        self.assertEqual(summary["parts"], 2)
        self.assertEqual(len(summary["executable_code_samples"]), 1)
        self.assertEqual(len(summary["code_execution_result_samples"]), 1)


class TestDiceToolExecution(unittest.TestCase):
    """Test cases for server-side dice tool execution."""

    def test_execute_dice_tool_roll_dice(self):
        """roll_dice tool should return correct structure."""
        with patch("mvp_site.dice.roll_dice_notation") as mock_roll:
            mock_roll.return_value = {
                "notation": "1d20",
                "total": 15,
                "rolls": [15],
                "type": "d20",
            }

            result = execute_dice_tool("roll_dice", {"notation": "1d20"})

            self.assertEqual(result["total"], 15)
            self.assertEqual(result["notation"], "1d20")
            self.assertIn("rolls", result)

    def test_execute_dice_tool_roll_attack(self):
        """roll_attack tool should return correct structure."""
        # roll_attack calls roll_dice_notation internally multiple times
        # We'll just verify it returns a dict with expected keys
        with patch("mvp_site.dice.roll_dice_notation") as mock_roll:
            mock_roll.return_value = {"total": 15, "rolls": [15]}

            result = execute_dice_tool("roll_attack", {"attack_modifier": 5})

            self.assertIn("attack_roll", result)
            self.assertIn("total", result["attack_roll"])

    def test_execute_dice_tool_unknown(self):
        """Unknown tool should return error."""
        result = execute_dice_tool("unknown_tool", {})
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
