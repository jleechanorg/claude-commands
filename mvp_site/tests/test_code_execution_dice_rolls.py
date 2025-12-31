"""
Tests for code execution and dice rolling integrity.
"""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from google.genai import types

from mvp_site import constants
from mvp_site.dice import execute_dice_tool
from mvp_site.dice_integrity import _is_code_execution_fabrication
from mvp_site.llm_providers import gemini_code_execution, gemini_provider, openrouter_provider
from mvp_site.llm_providers.openrouter_provider import OpenRouterResponse


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

            result = execute_dice_tool("roll_attack", {"modifier": 5})

            self.assertIn("attack_roll", result)
            self.assertIn("total", result["attack_roll"])

    def test_execute_dice_tool_unknown(self):
        """Unknown tool should return error."""
        result = execute_dice_tool("unknown_tool", {})
        self.assertIn("error", result)


class TestOpenRouterToolRequests(unittest.TestCase):
    """Test cases for OpenRouter tool request flow."""

    def test_phase1_detection_no_tools(self):
        """Should detect when no tools are requested in Phase 1."""
        json_response = json.dumps({"narrative": "Just a story.", "dice_rolls": []})

        with patch.object(openrouter_provider, "generate_content") as mock_gen:
            mock_gen.return_value = OpenRouterResponse(text=json_response)

            result = openrouter_provider.generate_content_with_tool_requests(
                prompt_contents=["Hello"],
                model_name="test-model",
                system_instruction_text="You are a GM",
                temperature=0.7,
                max_output_tokens=1000,
            )

            # Should return result immediately without Phase 2
            self.assertEqual(mock_gen.call_count, 1)
            self.assertEqual(result.text, json_response)

    def test_phase1_detection_with_tools(self):
        """Should detect tool requests and trigger Phase 2."""
        phase1_json = json.dumps(
            {
                "narrative": "You attempt a skill check.",
                "tool_requests": [
                    {
                        "tool": "roll_skill_check",
                        "args": {"skill": "stealth", "modifier": 4},
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
            code='import random; print(\'{\"notation\":\"1d20\",\"rolls\":[15],\"total\":15}\' )',
        )
        mock_part.code_execution_result = Mock(
            outcome="OUTCOME_OK", output='{"notation":"1d20","rolls":[15],"total":15}'
        )
        mock_response.candidates = [Mock(content=Mock(parts=[mock_part]))]
        mock_response.text = '{"narrative": "You rolled 15!", "dice_rolls": ["1d20 = 15"]}'

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


if __name__ == "__main__":
    unittest.main()
