"""
TDD Tests for Pre-Rolled Dice System

ARCHITECTURE (Dec 2024): All models now use pre-rolled dice injected into prompts.
This eliminates tool loops (two-stage inference) and code_execution.

The pre-rolled dice system:
1. Before each LLM call, generate fresh random dice values
2. Inject pre_rolled_dice arrays into the prompt
3. LLM uses these values IN ORDER for any dice rolls needed
4. Single-inference architecture (1 API call instead of 2+)

Benefits:
- Reduced latency (1 API call vs 2+)
- True randomness (server-side random.randint)
- Simplified code (~200 lines deleted)
- Works with ALL models (no capability requirements)
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


class TestPreRolledDiceSystem(unittest.TestCase):
    """Test the pre-rolled dice system."""

    def test_json_mode_enabled_without_code_execution(self):
        """
        Verify JSON mode is enabled and code_execution is NOT used.

        ARCHITECTURE (Dec 2024): Gemini API does NOT support combining
        response_mime_type="application/json" with code_execution tools.
        All models now use pre-rolled dice instead.
        """
        with patch('mvp_site.llm_providers.gemini_provider.get_client') as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            mock_client.models.generate_content = Mock(
                return_value=Mock(
                    text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
                )
            )

            llm_service._call_llm_api(
                ['test prompt'],
                'gemini-2.0-flash',
                'test logging',
                provider_name=constants.LLM_PROVIDER_GEMINI
            )

            self.assertTrue(mock_client.models.generate_content.called)

            call_args = mock_client.models.generate_content.call_args
            config_obj = call_args[1]['config']

            # JSON mode must be enabled
            self.assertEqual(
                config_obj.response_mime_type,
                'application/json',
                'JSON mode must be enabled for structured responses'
            )

            # code_execution must NOT be used (incompatible with JSON mode)
            self.assertIsNone(
                config_obj.tools,
                'code_execution tools must NOT be set with JSON mode'
            )

    def test_dice_roll_instructions_exist(self):
        """
        Verify prompt instructions for pre-rolled dice handling exist.
        """
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
            "Instruction file missing Dice Roll section"
        )

        # Check for pre-rolled dice instructions
        self.assertIn(
            "pre_rolled_dice",
            instruction_content,
            "Instruction file should mention pre_rolled_dice system"
        )

        # Check for usage instructions
        self.assertIn(
            "IN ORDER",
            instruction_content,
            "Instruction file should mention using dice values IN ORDER"
        )

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

            # JSON mode
            self.assertEqual(
                config_obj.response_mime_type,
                "application/json",
            )

            # Token limit
            self.assertEqual(
                config_obj.max_output_tokens,
                llm_service.JSON_MODE_MAX_OUTPUT_TOKENS,
            )

            # Temperature
            self.assertEqual(
                config_obj.temperature,
                llm_service.TEMPERATURE,
            )

            # Safety settings
            self.assertIsNotNone(config_obj.safety_settings)


class TestCerebrasProvider(unittest.TestCase):
    """Test Cerebras provider (no tool loops, direct generation only)."""

    def test_cerebras_provider_has_generate_content(self):
        """
        Verify Cerebras provider has generate_content function.
        """
        from mvp_site.llm_providers import cerebras_provider

        self.assertTrue(
            hasattr(cerebras_provider, 'generate_content'),
            "cerebras_provider should have generate_content function"
        )

    def test_cerebras_response_class_exists(self):
        """
        Verify CerebrasResponse class exists for response parsing.
        """
        from mvp_site.llm_providers.cerebras_provider import CerebrasResponse

        response = CerebrasResponse("test text", {"choices": []})
        self.assertEqual(response.text, "test text")


class TestOpenRouterProvider(unittest.TestCase):
    """Test OpenRouter provider (no tool loops, direct generation only)."""

    def test_openrouter_provider_has_generate_content(self):
        """
        Verify OpenRouter provider has generate_content function.
        """
        from mvp_site.llm_providers import openrouter_provider

        self.assertTrue(
            hasattr(openrouter_provider, 'generate_content'),
            "openrouter_provider should have generate_content function"
        )

    def test_openrouter_response_class_exists(self):
        """
        Verify OpenRouterResponse class exists for response parsing.
        """
        from mvp_site.llm_providers.openrouter_provider import OpenRouterResponse

        response = OpenRouterResponse("test text", {"choices": []})
        self.assertEqual(response.text, "test text")


class TestPreRolledDiceGeneration(unittest.TestCase):
    """Test the pre-rolled dice generation function."""

    def test_generate_pre_rolled_dice_returns_all_die_types(self):
        """
        Verify generate_pre_rolled_dice returns arrays for all standard dice.
        """
        from mvp_site.game_state import generate_pre_rolled_dice

        dice = generate_pre_rolled_dice()

        # Verify all die types are present
        self.assertIn("d20", dice)
        self.assertIn("d12", dice)
        self.assertIn("d10", dice)
        self.assertIn("d8", dice)
        self.assertIn("d6", dice)
        self.assertIn("d4", dice)
        self.assertIn("d100", dice)

    def test_generate_pre_rolled_dice_default_counts(self):
        """
        Verify default dice counts are sufficient for typical combat.
        """
        from mvp_site.game_state import generate_pre_rolled_dice

        dice = generate_pre_rolled_dice()

        # Default counts from function
        self.assertEqual(len(dice["d20"]), 100)  # 100 d20s by default
        self.assertEqual(len(dice["d6"]), 40)    # 40 d6s
        self.assertEqual(len(dice["d8"]), 30)    # 30 d8s

    def test_generate_pre_rolled_dice_values_in_range(self):
        """
        Verify all generated dice values are within valid ranges.
        """
        from mvp_site.game_state import generate_pre_rolled_dice

        dice = generate_pre_rolled_dice()

        # Check d20 values (1-20)
        for val in dice["d20"]:
            self.assertGreaterEqual(val, 1)
            self.assertLessEqual(val, 20)

        # Check d6 values (1-6)
        for val in dice["d6"]:
            self.assertGreaterEqual(val, 1)
            self.assertLessEqual(val, 6)

        # Check d100 values (1-100)
        for val in dice["d100"]:
            self.assertGreaterEqual(val, 1)
            self.assertLessEqual(val, 100)

    def test_generate_pre_rolled_dice_custom_counts(self):
        """
        Verify custom dice counts work correctly.
        """
        from mvp_site.game_state import generate_pre_rolled_dice

        dice = generate_pre_rolled_dice(num_d20=50, num_d6=10)

        self.assertEqual(len(dice["d20"]), 50)
        self.assertEqual(len(dice["d6"]), 10)


class TestLLMServicePreRolledDice(unittest.TestCase):
    """Test llm_service integration with pre-rolled dice."""

    def test_call_llm_api_uses_direct_call(self):
        """
        Verify _call_llm_api uses direct generate_content for all providers.

        ARCHITECTURE (Dec 2024): All models now use pre-rolled dice
        injected into the prompt. No tool loops needed.
        """
        with patch("mvp_site.llm_providers.cerebras_provider.generate_content") as mock_generate:
            mock_generate.return_value = Mock(
                text='{"narrative": "test", "entities_mentioned": [], "dice_rolls": []}'
            )

            llm_service._call_llm_api(
                ["test prompt"],
                "qwen-3-235b-a22b-instruct-2507",
                "test logging",
                provider_name=constants.LLM_PROVIDER_CEREBRAS
            )

            # Verify direct call was made
            self.assertTrue(mock_generate.called)


if __name__ == "__main__":
    unittest.main()
