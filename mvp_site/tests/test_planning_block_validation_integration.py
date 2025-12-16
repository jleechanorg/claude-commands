"""
Integration tests for planning block validation and logging.
Tests the complete flow of _validate_and_enforce_planning_block with all logging paths.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the parent directory to the path to import modules
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

try:
    from mvp_site.game_state import GameState
    from mvp_site.llm_service import (
        NarrativeResponse,
        _validate_and_enforce_planning_block,
    )

    MODULES_AVAILABLE = True
except ImportError:
    GameState = None
    NarrativeResponse = None
    _validate_and_enforce_planning_block = None
    MODULES_AVAILABLE = False


class TestPlanningBlockValidationIntegration(unittest.TestCase):
    """Integration tests for planning block validation with comprehensive logging coverage."""

    def setUp(self):
        """Set up test fixtures."""
        self.game_state = GameState()
        self.game_state.player_character_data = {"name": "Test Hero"}
        self.game_state.current_location = {"name": "Test Location"}

        # Create mock structured response
        self.structured_response = MagicMock(spec=NarrativeResponse)
        self.structured_response.planning_block = None

    @patch("mvp_site.llm_service.logging_util", autospec=True)
    def test_missing_planning_block_logs_warning_and_returns_response(
        self, mock_logging
    ):
        """When no planning block is present, return response unchanged and log warning."""
        response_text = "Normal story response without planning block"

        result = _validate_and_enforce_planning_block(
            response_text,
            "test input",
            self.game_state,
            "test-model",
            "test instruction",
            self.structured_response,
        )

        mock_logging.warning.assert_any_call(
            "⚠️ PLANNING_BLOCK_MISSING: Story mode response missing required planning block. "
            "The LLM should have generated this - no fallback will be used."
        )
        assert result == response_text

    @patch("mvp_site.llm_service.logging_util", autospec=True)
    def test_empty_planning_block_logs_warning_and_returns_response(self, mock_logging):
        """Existing but empty planning block logs and returns original response."""
        self.structured_response.planning_block = {"thinking": "", "choices": {}}
        response_text = "Story response with empty planning block"

        result = _validate_and_enforce_planning_block(
            response_text,
            "test input",
            self.game_state,
            "test-model",
            "test instruction",
            self.structured_response,
        )

        mock_logging.warning.assert_any_call(
            "⚠️ PLANNING_BLOCK_EMPTY: Planning block exists but has no content"
        )
        assert result == response_text

    @patch("mvp_site.llm_service.logging_util", autospec=True)
    def test_string_planning_block_logs_error_and_returns_response(self, mock_logging):
        """String planning blocks are rejected with error log and unchanged response."""
        self.structured_response.planning_block = "invalid"
        response_text = "Story response with string planning block"

        result = _validate_and_enforce_planning_block(
            response_text,
            "test input",
            self.game_state,
            "test-model",
            "test instruction",
            self.structured_response,
        )

        mock_logging.error.assert_any_call(
            "❌ STRING PLANNING BLOCKS NO LONGER SUPPORTED: Found str planning block, only JSON format is allowed"
        )
        assert result == response_text

    @patch("mvp_site.llm_service.logging_util", autospec=True)
    def test_valid_planning_block_passes_without_additional_logging(self, mock_logging):
        """Valid planning block returns early without warnings or errors."""
        self.structured_response.planning_block = {
            "thinking": "Plan",
            "choices": {"Continue": "Do thing"},
        }
        response_text = "Story response with planning block"

        result = _validate_and_enforce_planning_block(
            response_text,
            "test input",
            self.game_state,
            "test-model",
            "test instruction",
            self.structured_response,
        )

        mock_logging.info.assert_any_call(
            "✅ Planning block found in JSON structured response"
        )
        mock_logging.warning.assert_not_called()
        mock_logging.error.assert_not_called()
        assert result == response_text

    def test_crash_safety_with_malformed_inputs(self):
        """Test that the function doesn't crash with malformed inputs."""
        # Test with None inputs
        try:
            result = _validate_and_enforce_planning_block(
                None,
                "test input",
                self.game_state,
                "test-model",
                "test instruction",
                self.structured_response,
            )
            # Should handle gracefully and return None or empty string
            assert result in [None, "", "None"]
        except Exception as e:
            self.fail(f"Function crashed with None response_text: {e}")

        # Test with malformed game state
        try:
            malformed_game_state = MagicMock()
            malformed_game_state.player_character_data = None
            malformed_game_state.current_location = None

            result = _validate_and_enforce_planning_block(
                "test response",
                "test input",
                malformed_game_state,
                "test-model",
                "test instruction",
                self.structured_response,
            )
            # Should handle gracefully
            assert result is not None
        except Exception as e:
            self.fail(f"Function crashed with malformed game state: {e}")


class TestPlanningBlockSchemaStructure(unittest.TestCase):
    """TDD tests for planning_block schema enforcement.

    These tests verify NARRATIVE_RESPONSE_SCHEMA defines planning_block with
    required nested structure: thinking (string), context (string), choices (object).
    """

    def test_planning_block_schema_has_properties_defined(self):
        """NARRATIVE_RESPONSE_SCHEMA.planning_block must define nested properties."""
        from mvp_site.llm_providers.provider_utils import NARRATIVE_RESPONSE_SCHEMA

        planning_block_schema = NARRATIVE_RESPONSE_SCHEMA["properties"]["planning_block"]

        # Must have properties, not just additionalProperties
        self.assertIn(
            "properties",
            planning_block_schema,
            "planning_block schema must define 'properties' for nested structure",
        )

    def test_planning_block_schema_requires_thinking_field(self):
        """planning_block.properties must include 'thinking' as string."""
        from mvp_site.llm_providers.provider_utils import NARRATIVE_RESPONSE_SCHEMA

        planning_block_schema = NARRATIVE_RESPONSE_SCHEMA["properties"]["planning_block"]
        properties = planning_block_schema.get("properties", {})

        self.assertIn("thinking", properties, "planning_block must define 'thinking' property")
        self.assertEqual(
            properties["thinking"]["type"],
            "string",
            "thinking must be type string",
        )

    def test_planning_block_schema_requires_choices_field(self):
        """planning_block.properties must include 'choices' as object."""
        from mvp_site.llm_providers.provider_utils import NARRATIVE_RESPONSE_SCHEMA

        planning_block_schema = NARRATIVE_RESPONSE_SCHEMA["properties"]["planning_block"]
        properties = planning_block_schema.get("properties", {})

        self.assertIn("choices", properties, "planning_block must define 'choices' property")
        self.assertEqual(
            properties["choices"]["type"],
            "object",
            "choices must be type object",
        )

    def test_planning_block_schema_has_required_fields(self):
        """planning_block schema must list thinking and choices as required."""
        from mvp_site.llm_providers.provider_utils import NARRATIVE_RESPONSE_SCHEMA

        planning_block_schema = NARRATIVE_RESPONSE_SCHEMA["properties"]["planning_block"]

        self.assertIn(
            "required",
            planning_block_schema,
            "planning_block must have 'required' field",
        )
        required = planning_block_schema["required"]
        self.assertIn("thinking", required, "'thinking' must be required")
        self.assertIn("choices", required, "'choices' must be required")

    def test_planning_block_choices_has_additionalProperties_for_dynamic_keys(self):
        """choices.additionalProperties must define structure for dynamic choice keys."""
        from mvp_site.llm_providers.provider_utils import NARRATIVE_RESPONSE_SCHEMA

        planning_block_schema = NARRATIVE_RESPONSE_SCHEMA["properties"]["planning_block"]
        choices_schema = planning_block_schema.get("properties", {}).get("choices", {})

        self.assertIn(
            "additionalProperties",
            choices_schema,
            "choices must have additionalProperties for dynamic keys",
        )
        # Each choice should have text, description, risk_level
        choice_schema = choices_schema["additionalProperties"]
        self.assertEqual(choice_schema["type"], "object", "Each choice must be an object")
        self.assertIn("properties", choice_schema, "Choice schema must define properties")
        choice_props = choice_schema["properties"]
        self.assertIn("text", choice_props, "Choice must have 'text' property")
        self.assertIn("description", choice_props, "Choice must have 'description' property")


if __name__ == "__main__":
    unittest.main()
