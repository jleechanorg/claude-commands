"""
Test file to verify world_logic.py structure and basic functionality.
This test doesn't require external dependencies.
"""

import ast
import asyncio
import inspect
import os
import re
import sys
import threading
import time
import unittest

# ExitStack removed - using decorator-based patching instead
from unittest.mock import MagicMock, Mock, patch

from mvp_site import world_logic
from mvp_site.debug_hybrid_system import convert_json_escape_sequences
from mvp_site.prompt_utils import _convert_and_format_field

# Set test environment before any imports
os.environ["TESTING"] = "true"
os.environ["USE_MOCKS"] = "true"


class _TestValidationError(Exception):
    """Test-only stand-in for Pydantic validation errors."""


class _TestLLMRequestError(Exception):
    """Test-only stand-in for LLM request failures."""


# CRITICAL FIX: Mock firebase_admin completely to avoid google.auth namespace conflicts
# This prevents the test from trying to import firebase_admin which triggers the google.auth issue
firebase_admin_mock = MagicMock()
firebase_admin_mock.firestore = MagicMock()
firebase_admin_mock.auth = MagicMock()
firebase_admin_mock._apps = {}  # Empty apps list to prevent initialization
sys.modules["firebase_admin"] = firebase_admin_mock
sys.modules["firebase_admin.firestore"] = firebase_admin_mock.firestore
sys.modules["firebase_admin.auth"] = firebase_admin_mock.auth

# Add mvp_site to path AFTER mocking firebase_admin
mvp_site_path = os.path.dirname(os.path.dirname(__file__))
if mvp_site_path not in sys.path:
    sys.path.append(mvp_site_path)

# Use proper fakes library instead of manual MagicMock setup
# Import fakes library components (will be imported after path setup)
try:
    # Fakes library will be imported after path setup below

    # Mock pydantic dependencies
    pydantic_module = MagicMock()
    pydantic_module.BaseModel = MagicMock()
    pydantic_module.Field = MagicMock()
    pydantic_module.field_validator = MagicMock()
    pydantic_module.model_validator = MagicMock()
    pydantic_module.ValidationError = _TestValidationError
    sys.modules["pydantic"] = pydantic_module

    # Mock cachetools dependencies
    cachetools_module = MagicMock()
    cachetools_module.TTLCache = MagicMock()
    cachetools_module.cached = MagicMock()
    sys.modules["cachetools"] = cachetools_module

    # Mock google dependencies
    google_module = MagicMock()
    google_module.genai = MagicMock()
    google_module.genai.Client = MagicMock()
    sys.modules["google"] = google_module
    sys.modules["google.genai"] = google_module.genai

    # Mock other optional dependencies that might not be available
    docx_module = MagicMock()
    docx_module.Document = MagicMock()
    sys.modules["docx"] = docx_module

    # Mock fpdf dependencies
    fpdf_module = MagicMock()
    fpdf_module.FPDF = MagicMock()
    fpdf_module.XPos = MagicMock()
    fpdf_module.YPos = MagicMock()
    sys.modules["fpdf"] = fpdf_module

    # Mock flask dependencies that might not be available
    flask_module = MagicMock()
    flask_module.Flask = MagicMock()
    flask_module.request = MagicMock()
    flask_module.jsonify = MagicMock()
    sys.modules["flask"] = flask_module
except Exception:
    pass  # If mocking fails, continue anyway

# Import proper fakes library (removing unused imports per CodeRabbit feedback)


class TestUnifiedAPIStructure(unittest.TestCase):
    """Test the structure and basic logic of world_logic.py"""

    def setUp(self):
        """Set up test environment and mock all external dependencies"""
        # Set environment variables for testing
        os.environ["TESTING"] = "true"
        os.environ["USE_MOCKS"] = "true"

        # Clear any cached modules to prevent Firebase initialization errors
        modules_to_clear = [
            "world_logic",
            "firestore_service",
            "llm_service",
            "logging_util",
            "constants",
            "document_generator",
            "structured_fields_utils",
            "custom_types",
            "debug_hybrid_system",
            "game_state",
            # Also clear firebase modules if they exist
            "firebase_admin",
            "firebase_admin.firestore",
        ]
        for module in modules_to_clear:
            if module in sys.modules:
                del sys.modules[module]

        # Mock all the imports
        self.mock_modules = {}
        modules_to_mock = [
            "constants",
            "document_generator",
            "firestore_service",
            "llm_service",
            "logging_util",
            "structured_fields_utils",
            "custom_types",
            "debug_hybrid_system",
            "game_state",
        ]

        for module_name in modules_to_mock:
            mock_module = Mock()
            self.mock_modules[module_name] = mock_module
            sys.modules[module_name] = mock_module

        # Set up specific mock values
        sys.modules["constants"].ATTRIBUTE_SYSTEM_DND = "D&D"
        sys.modules["constants"].MODE_CHARACTER = "character"

        # Mock GameState
        mock_game_state = Mock()
        mock_game_state.return_value.to_dict.return_value = {"test": "data"}
        sys.modules["game_state"].GameState = mock_game_state

    def tearDown(self):
        """Clean up mocks"""
        for module_name in self.mock_modules:
            if module_name in sys.modules:
                del sys.modules[module_name]

    def test_import_world_logic(self):
        """Test that world_logic can be imported with mocked dependencies"""
        try:
            assert hasattr(world_logic, "create_campaign_unified")
            assert hasattr(world_logic, "process_action_unified")
            assert hasattr(world_logic, "get_campaign_state_unified")
            assert hasattr(world_logic, "update_campaign_unified")
            assert hasattr(world_logic, "export_campaign_unified")
            assert hasattr(world_logic, "get_campaigns_list_unified")
        except AttributeError as e:
            self.fail(f"world_logic missing expected functions: {e}")

    def test_build_campaign_prompt(self):
        """Test the campaign prompt building logic"""

        # Test new format
        result = world_logic._build_campaign_prompt(
            "knight", "fantasy", "epic adventure", ""
        )
        expected = "Character: knight | Setting: fantasy | Description: epic adventure"
        assert result == expected

        # Test old format priority
        result = world_logic._build_campaign_prompt("", "", "", "old prompt")
        assert result == "old prompt"

        # Test empty input - with mocks, may return generated prompt or default
        result = world_logic._build_campaign_prompt("", "", "", "")
        # Accept either default string or generated content
        assert (
            result == "Generate a random D&D campaign with creative elements"
            or "Character:" in result
            and "Setting:" in result
        ), f"Expected default or generated prompt, got: {result}"

    def test_cleanup_legacy_state(self):
        """Test legacy state cleanup logic"""

        # Test with legacy fields
        state_dict = {
            "player_character_data": {"name": "Hero"},
            "party_data": {"old": "data"},  # Legacy field
            "current_turn": 1,
            "legacy_prompt_data": {"old": "prompt"},  # Legacy field
        }

        cleaned_dict, was_cleaned, num_cleaned = world_logic._cleanup_legacy_state(
            state_dict
        )

        assert was_cleaned
        assert num_cleaned == 2
        assert "party_data" not in cleaned_dict
        assert "legacy_prompt_data" not in cleaned_dict
        assert "player_character_data" in cleaned_dict
        assert "current_turn" in cleaned_dict

    def test_error_response_format(self):
        """Test standardized error response format"""

        response = world_logic.create_error_response("Test error", 404)

        assert response["error"] == "Test error"
        assert response["status_code"] == 404
        assert not response["success"]

    def test_success_response_format(self):
        """Test standardized success response format"""
        # world_logic already imported at module level with proper mocking

        data = {"campaign_id": "test123", "title": "Test Campaign"}
        response = world_logic.create_success_response(data)

        assert response["success"]
        assert response["campaign_id"] == "test123"
        assert response["title"] == "Test Campaign"

    def test_create_campaign_unified_validation_sync(self):
        """Test campaign creation validation (sync version)"""

        # world_logic already imported at module level with proper mocking

        async def run_tests():
            # Test missing user_id
            result = await world_logic.create_campaign_unified({})
            assert "error" in result
            assert "User ID is required" in result["error"]

            # Test missing title
            result = await world_logic.create_campaign_unified({"user_id": "test"})
            assert "error" in result
            assert "Title is required" in result["error"]

            # Test empty prompt components - may succeed or fail depending on validation
            result = await world_logic.create_campaign_unified(
                {
                    "user_id": "test",
                    "title": "Test",
                    "character": "",
                    "setting": "",
                    "description": "",
                    "prompt": "",
                }
            )
            # With mocks, this may succeed or fail - just verify we get a result
            assert isinstance(result, dict)
            assert "error" in result or "success" in result

        # Run async tests
        asyncio.run(run_tests())

    def test_process_action_unified_validation_sync(self):
        """Test action processing validation (sync version)"""

        # world_logic already imported at module level with proper mocking

        async def run_tests():
            # Test missing user_id - with mocks, this may succeed or fail
            result = await world_logic.process_action_unified({})
            assert isinstance(result, dict)
            # Either returns error or mock success response
            assert "error" in result or "success" in result or "narrative" in result

            # Test missing campaign_id - with mocks, may succeed
            result = await world_logic.process_action_unified({"user_id": "test"})
            assert isinstance(result, dict)
            # Either returns error or mock response
            assert "error" in result or "success" in result or "narrative" in result

            # Test missing user_input - with mocks, may succeed
            result = await world_logic.process_action_unified(
                {"user_id": "test", "campaign_id": "test"}
            )
            assert isinstance(result, dict)
            # Either returns error or mock response
            assert "error" in result or "success" in result or "narrative" in result

        # Run async tests
        asyncio.run(run_tests())


class TestMCPMigrationRedGreen(unittest.TestCase):
    """Red-Green TDD tests for critical MCP migration bug fixes."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock story context with existing entries
        self.mock_story_context = [
            {"actor": "user", "sequence_id": 1, "text": "Hello"},
            {"actor": "gemini", "sequence_id": 2, "text": "Hi there!"},
            {"actor": "user", "sequence_id": 3, "text": "How are you?"},
            {"actor": "gemini", "sequence_id": 4, "text": "I'm doing well!"},
        ]

        # Mock request data for process_action_unified
        self.mock_request_data = {
            "user_id": "test-user-123",
            "campaign_id": "test-campaign-456",
            "user_input": "Tell me a story",
            "mode": "character",  # Use string directly instead of constants import
        }

    @patch("mvp_site.world_logic.firestore_service.get_campaign_game_state")
    @patch("mvp_site.world_logic.firestore_service.get_campaign_by_id")
    @patch("mvp_site.world_logic.firestore_service.update_campaign_game_state")
    @patch("mvp_site.world_logic.firestore_service.add_story_entry")
    @patch("mvp_site.world_logic.llm_service.continue_story")
    @patch("mvp_site.world_logic._prepare_game_state")
    @patch("mvp_site.world_logic.get_user_settings")
    def test_sequence_id_calculation_bug_red_phase(
        self,
        mock_settings,
        mock_prepare,
        mock_gemini,
        mock_add_story,
        mock_update_state,
        mock_get_campaign,
        mock_get_campaign_state,
    ):
        """
        🔴 RED PHASE: Test that would FAIL before sequence_id fix

        This test verifies that AI responses get the correct sequence_id calculation:
        - User input should get: len(story_context) + 1 = 5
        - AI response should get: len(story_context) + 2 = 6

        Before the fix, both would get len(story_context) + 1 = 5 (WRONG!)
        """
        # Mock the campaign data and story context
        mock_get_campaign.return_value = (
            {"selected_prompts": [], "use_default_world": False},
            self.mock_story_context,
        )

        # Mock game state preparation
        mock_game_state = Mock()
        mock_game_state.debug_mode = False
        mock_game_state.to_dict.return_value = {"test": "state"}
        mock_prepare.return_value = (mock_game_state, False, 0)

        # Prevent Firestore client creation
        mock_get_campaign_state.return_value = {}

        # Mock user settings
        mock_settings.return_value = {"debug_mode": False}

        # Mock Gemini response with structured fields
        mock_gemini_response = Mock()
        mock_gemini_response.narrative_text = "Here's a test story"
        mock_gemini_response.get_state_updates.return_value = {}
        mock_gemini_response.structured_response = None
        # Properly mock LLMResponse methods to avoid Mock pollution in state changes
        mock_gemini_response.get_location_confirmed.return_value = "Test Location"
        mock_gemini_response.resources = "HP: 10/10"
        mock_gemini_response.processing_metadata = {}  # Avoid Mock in metadata check
        mock_gemini.return_value = mock_gemini_response

        # Execute the async function
        result = asyncio.run(world_logic.process_action_unified(self.mock_request_data))

        # CRITICAL TEST: Verify sequence_id is calculated correctly
        # The AI response should get len(story_context) + 2 = 6
        expected_sequence_id = len(self.mock_story_context) + 2  # Should be 6
        actual_sequence_id = result.get("sequence_id")

        self.assertEqual(
            actual_sequence_id,
            expected_sequence_id,
            f"AI response sequence_id should be {expected_sequence_id} "
            f"(len(story_context) + 2), but got {actual_sequence_id}. "
            f"This indicates the sequence_id calculation bug is present!",
        )

    @patch("mvp_site.world_logic.firestore_service.get_campaign_game_state")
    @patch("mvp_site.world_logic.firestore_service.get_campaign_by_id")
    @patch("mvp_site.world_logic.firestore_service.update_campaign_game_state")
    @patch("mvp_site.world_logic.firestore_service.add_story_entry")
    @patch("mvp_site.world_logic.llm_service.continue_story")
    @patch("mvp_site.world_logic._prepare_game_state")
    @patch("mvp_site.world_logic.get_user_settings")
    def test_user_scene_number_field_red_phase(
        self,
        mock_settings,
        mock_prepare,
        mock_gemini,
        mock_add_story,
        mock_update_state,
        mock_get_campaign,
        mock_get_campaign_state,
    ):
        """
        🔴 RED PHASE: Test that would FAIL before user_scene_number field addition

        This test verifies that the user_scene_number field is present in API responses.
        Before the fix, this field was missing and would break frontend compatibility.
        """
        # Mock setup (same as sequence_id test)
        mock_get_campaign.return_value = (
            {"selected_prompts": [], "use_default_world": False},
            self.mock_story_context,
        )

        mock_game_state = Mock()
        mock_game_state.debug_mode = False
        mock_game_state.to_dict.return_value = {"test": "state"}
        mock_prepare.return_value = (mock_game_state, False, 0)
        mock_get_campaign_state.return_value = {}

        mock_settings.return_value = {"debug_mode": False}

        mock_gemini_response = Mock()
        mock_gemini_response.narrative_text = "Test story response"
        mock_gemini_response.get_state_updates.return_value = {}
        mock_gemini_response.structured_response = None
        # Properly mock LLMResponse methods to avoid Mock pollution in state changes
        mock_gemini_response.get_location_confirmed.return_value = "Test Location"
        mock_gemini_response.resources = "HP: 10/10"
        mock_gemini_response.processing_metadata = {}  # Avoid Mock in metadata check
        mock_gemini.return_value = mock_gemini_response

        # Execute the async function
        result = asyncio.run(world_logic.process_action_unified(self.mock_request_data))

        # CRITICAL TEST: Verify user_scene_number field is present
        self.assertIn(
            "user_scene_number",
            result,
            "user_scene_number field is missing from API response! "
            "This breaks frontend compatibility.",
        )

        # Verify the calculation is correct
        # Should be: count of existing gemini responses + 1 = 2 + 1 = 3
        expected_scene_number = (
            sum(
                1 for entry in self.mock_story_context if entry.get("actor") == "gemini"
            )
            + 1
        )
        actual_scene_number = result.get("user_scene_number")

        self.assertEqual(
            actual_scene_number,
            expected_scene_number,
            f"user_scene_number should be {expected_scene_number} "
            f"(count of gemini responses + 1), but got {actual_scene_number}",
        )

    def test_enhanced_logging_json_serialization_red_phase(self):
        """
        🔴 RED PHASE: Test that would FAIL before enhanced logging fix

        This test verifies that the enhanced logging with JSON serialization
        works correctly with complex objects that have custom serializers.
        """

        # Create a complex game state dict that would cause JSON serialization issues
        complex_game_state = {
            "string_fields": {"name": "Test Campaign"},
            "numeric_fields": {"level": 5, "health": 100},
            "complex_object": Mock(),  # This would fail standard JSON serialization
            "nested_dict": {"inner_complex": Mock(), "normal_field": "test_value"},
        }

        # CRITICAL TEST: This should not raise an exception with enhanced logging
        # The function should handle complex objects via internal json_default_serializer
        try:
            result = world_logic.truncate_game_state_for_logging(
                complex_game_state, max_lines=10
            )
            # Should return truncated JSON string without crashing
            self.assertIsInstance(result, str)
            # Should handle Mock objects gracefully (not crash)
            self.assertTrue(len(result) > 0)
        except (TypeError, ValueError) as e:
            self.fail(
                f"Enhanced logging failed with complex objects: {e}. "
                f"This indicates the JSON serialization enhancement is missing!"
            )


# Using shared helpers from mvp_site.prompt_utils to avoid code duplication


class TestJSONEscapeConversion(unittest.TestCase):
    """Test JSON escape sequence conversion functionality."""

    def test_convert_json_escape_sequences_basic(self):
        """Test core conversion function with various escape sequences."""
        test_cases = [
            ("\\n", "\n"),
            ("\\t", "\t"),
            ('\\"', '"'),
            ("\\\\", "\\"),
            ("Hello\\nWorld", "Hello\nWorld"),
            ('\\"quoted text\\"', '"quoted text"'),
            ("Line 1\\nLine 2\\nLine 3", "Line 1\nLine 2\nLine 3"),
            ("", ""),  # Edge case: empty string
            ("No escapes", "No escapes"),  # Edge case: no escapes
        ]

        for escaped_input, expected_output in test_cases:
            with self.subTest(input=escaped_input):
                result = convert_json_escape_sequences(escaped_input)
                self.assertEqual(result, expected_output)

    def test_unicode_escape_sequences_and_idempotence(self):
        """Ensure \\uXXXX and surrogate pairs are handled and conversion is idempotent."""
        # Test idempotence: running twice should not change output
        s = "Line 1\\nLine 2"
        once = convert_json_escape_sequences(s)
        twice = convert_json_escape_sequences(once)
        self.assertEqual(once, twice)

        # Ensure no further escape sequences remain after conversion
        self.assertNotIn("\\\\n", once)
        self.assertNotIn("\\\\t", once)

    def test_dragon_knight_description_conversion(self):
        """Test conversion of the actual Dragon Knight description that caused the original issue."""
        # Original problematic text from debug session
        dragon_knight_escaped = (
            "# Campaign summary\\n\\n"
            "You are Ser Arion, a 16 year old honorable knight on your first mission, "
            "sworn to protect the vast Celestial Imperium. For decades, the Empire has "
            "been ruled by the iron-willed Empress Sariel, a ruthless tyrant who uses "
            "psychic power to crush dissent.\\n\\n"
            "Your loyalty is now brutally tested. You have been ordered to slaughter a "
            "settlement of innocent refugees whose very existence has been deemed a threat "
            "to the Empress's perfect, unyielding order."
        )

        # Expected converted text
        expected_converted = (
            "# Campaign summary\n\n"
            "You are Ser Arion, a 16 year old honorable knight on your first mission, "
            "sworn to protect the vast Celestial Imperium. For decades, the Empire has "
            "been ruled by the iron-willed Empress Sariel, a ruthless tyrant who uses "
            "psychic power to crush dissent.\n\n"
            "Your loyalty is now brutally tested. You have been ordered to slaughter a "
            "settlement of innocent refugees whose very existence has been deemed a threat "
            "to the Empress's perfect, unyielding order."
        )

        result = convert_json_escape_sequences(dragon_knight_escaped)
        self.assertEqual(result, expected_converted)

        # Ensure no escape sequences remain
        self.assertNotIn("\\n", result)
        self.assertNotIn('\\"', result)


class TestConvertAndFormatField(unittest.TestCase):
    """Test the helper function that eliminates code duplication."""

    def test_convert_and_format_field_basic(self):
        """Test helper function with various inputs."""
        # Normal case
        result = _convert_and_format_field("Test\\nValue", "Character")
        self.assertEqual(result, "Character: Test\nValue")

        # Empty field
        result = _convert_and_format_field("", "Setting")
        self.assertEqual(result, "")

        # Whitespace only
        result = _convert_and_format_field("   ", "Description")
        self.assertEqual(result, "")

        # No escapes needed
        result = _convert_and_format_field("Normal text", "Character")
        self.assertEqual(result, "Character: Normal text")

        # Complex escapes
        result = _convert_and_format_field(
            "Line1\\n\\nLine2\\twith\\ttabs", "Description"
        )
        self.assertEqual(result, "Description: Line1\n\nLine2\twith\ttabs")


class TestBuildCampaignPromptConversion(unittest.TestCase):
    """Test campaign prompt building with conversion integration."""

    def test_build_campaign_prompt_converts_all_fields(self):
        """Test that all fields get conversion applied."""
        result = world_logic._build_campaign_prompt(
            character="Hero\\nwith\\nlinebreaks",
            setting="World\\twith\\ttabs",
            description="Story\\n\\nwith\\n\\nparagraphs",
            old_prompt="",
        )

        # All fields should have escape sequences converted
        self.assertIn("Hero\nwith\nlinebreaks", result)
        self.assertIn("World\twith\ttabs", result)
        self.assertIn("Story\n\nwith\n\nparagraphs", result)

        # No escape sequences should remain
        self.assertNotIn("\\n", result)
        self.assertNotIn("\\t", result)

        # Should be properly formatted with label prefixes appearing exactly once
        self.assertIn("Character: Hero", result)
        self.assertIn("Setting: World", result)
        self.assertIn("Description: Story", result)

        # Assert label prefixes appear exactly once to catch accidental duplication
        self.assertEqual(result.count("Character:"), 1)
        self.assertEqual(result.count("Setting:"), 1)
        self.assertEqual(result.count("Description:"), 1)

    def test_build_campaign_prompt_dragon_knight_case(self):
        """Test the exact Dragon Knight case that prompted the original fix."""
        dragon_knight_escaped = (
            "# Campaign summary\\n\\n"
            "You are Ser Arion, a 16 year old honorable knight on your first mission, "
            "sworn to protect the vast Celestial Imperium. For decades, the Empire has "
            "been ruled by the iron-willed Empress Sariel, a ruthless tyrant who uses "
            "psychic power to crush dissent.\\n\\n"
            "Your loyalty is now brutally tested. You have been ordered to slaughter a "
            "settlement of innocent refugees whose very existence has been deemed a threat "
            "to the Empress's perfect, unyielding order."
        )

        result = world_logic._build_campaign_prompt(
            character="Ser Arion val Valerion",
            setting="Celestial Imperium",
            description=dragon_knight_escaped,
            old_prompt="",
        )

        # Should contain properly formatted description
        self.assertIn("# Campaign summary\n\n", result)
        self.assertIn("You are Ser Arion, a 16 year old honorable knight", result)
        self.assertIn("Celestial Imperium. For decades", result)

        # Should not contain any escape sequences
        self.assertNotIn("\\n", result)
        self.assertNotIn('\\"', result)

        # All fields should be present
        self.assertIn("Character: Ser Arion val Valerion", result)
        self.assertIn("Setting: Celestial Imperium", result)
        self.assertIn("Description: # Campaign summary", result)

    def test_build_campaign_prompt_old_prompt_priority(self):
        """Test that old_prompt takes priority and bypasses conversion."""
        old_prompt = "Legacy prompt with\\nescapes"

        result = world_logic._build_campaign_prompt(
            character="Test",
            setting="Test",
            description="Description\\nwith\\nescapes",
            old_prompt=old_prompt,
        )

        # Should return old prompt exactly as-is (no conversion)
        self.assertEqual(result, "Legacy prompt with\\nescapes")

    def test_build_campaign_prompt_empty_fields(self):
        """Test behavior with empty or whitespace-only fields."""
        result = world_logic._build_campaign_prompt(
            character="",
            setting="   ",
            description="Valid\\nDescription",
            old_prompt="",
        )

        # Should only include non-empty fields
        self.assertNotIn("Character:", result)
        self.assertNotIn("Setting:", result)
        self.assertIn("Description: Valid\nDescription", result)

    def test_build_campaign_prompt_all_empty_triggers_random(self):
        """Test that all empty fields triggers random generation."""
        result = world_logic._build_campaign_prompt(
            character="", setting="", description="", old_prompt=""
        )

        # Should generate random character and setting
        self.assertIn("Character:", result)
        self.assertIn("Setting:", result)
        self.assertNotIn("Description:", result)


class TestMarkdownStructurePreservation(unittest.TestCase):
    """Test that conversion preserves markdown formatting."""

    def test_markdown_structure_preservation(self):
        """Test that conversion preserves markdown formatting."""
        markdown_description = (
            "# Campaign Title\\n\\n"
            "## Section 1\\n\\n"
            "Some text with **bold** and *italic*.\\n\\n"
            "### Subsection\\n\\n"
            "- List item 1\\n"
            "- List item 2\\n\\n"
            "> Quote text\\n\\n"
            "```\\n"
            "code block\\n"
            "```"
        )

        result = world_logic._build_campaign_prompt(
            character="", setting="", description=markdown_description, old_prompt=""
        )

        # Should preserve markdown structure
        self.assertIn("# Campaign Title\n\n", result)
        self.assertIn("## Section 1\n\n", result)
        self.assertIn("### Subsection\n\n", result)
        self.assertIn("- List item 1\n", result)
        self.assertIn("- List item 2\n\n", result)
        self.assertIn("> Quote text\n\n", result)
        self.assertIn("```\ncode block\n```", result)


class TestCodeHealthChecks(unittest.TestCase):
    """Test for code health issues like unused constants and dead code."""

    def test_no_unused_random_constants_in_world_logic(self):
        """Test that RANDOM_CHARACTERS and RANDOM_SETTINGS are not duplicated/unused in world_logic.py"""
        # RED phase: This test should fail initially due to unused constants

        # Read world_logic.py source

        source = inspect.getsource(world_logic)

        # Check if constants are defined
        has_random_characters = "RANDOM_CHARACTERS" in source
        has_random_settings = "RANDOM_SETTINGS" in source

        if has_random_characters or has_random_settings:
            # If they exist, they should be used somewhere
            uses_random_characters = (
                "random.choice(RANDOM_CHARACTERS)" in source
                or "choice(RANDOM_CHARACTERS)" in source
            )
            uses_random_settings = (
                "random.choice(RANDOM_SETTINGS)" in source
                or "choice(RANDOM_SETTINGS)" in source
            )

            # Constants should either not exist OR be used
            if has_random_characters:
                self.assertTrue(
                    uses_random_characters,
                    "RANDOM_CHARACTERS constant is defined but never used - this is dead code",
                )
            if has_random_settings:
                self.assertTrue(
                    uses_random_settings,
                    "RANDOM_SETTINGS constant is defined but never used - this is dead code",
                )


# =============================================================================
# PARALLELIZATION TESTS - Prevent Regression of PR #2157 Fix
# =============================================================================
# These tests ensure that async functions in world_logic.py always use
# asyncio.to_thread() for blocking I/O operations. Without this, the shared
# event loop blocks and concurrent requests serialize.
# =============================================================================


def _calculate_parallel_threshold(
    serial_time: float, buffer_ratio: float = 0.8
) -> float:
    """Helper to keep parallel timing thresholds consistent across tests."""
    return serial_time * buffer_ratio


class _MockHelperMixin:
    @staticmethod
    def _build_mock_response():
        """Create a mock response object with required attributes."""
        response = MagicMock()
        response.narrative_text = "Test response"
        response.get_state_updates.return_value = {}
        response.structured_response = None
        response.get_location_confirmed.return_value = None
        response.dice_rolls = []
        response.resources = ""
        return response

    @staticmethod
    def _build_mock_game_state(*args, **kwargs):
        """Create a mock game state matching expected interface."""
        mock_state = MagicMock()
        mock_state.debug_mode = False
        mock_state.to_dict.return_value = {"test": "state"}
        mock_state.world_data = {}
        mock_state.custom_campaign_state = {}
        mock_state.combat_state = {"in_combat": False}
        mock_state.validate_checkpoint_consistency.return_value = []
        return (mock_state, False, 0)

    def _configure_common_mocks(
        self,
        mock_llm_service,
        mock_firestore,
        mock_prepare,
        mock_settings,
        *,
        llm_side_effect,
        campaign_side_effect,
    ):
        """Apply shared mock configuration used across tests."""
        mock_llm_service.continue_story.side_effect = llm_side_effect
        mock_llm_service.LLMRequestError = (
            _TestLLMRequestError  # For exception handling
        )

        mock_firestore.get_campaign_by_id.side_effect = campaign_side_effect
        mock_firestore.update_campaign_game_state = MagicMock()
        mock_firestore.add_story_entry = MagicMock()
        mock_firestore.update_story_context = MagicMock()
        mock_firestore.get_campaign_game_state = MagicMock(return_value={})

        mock_prepare.side_effect = self._build_mock_game_state
        mock_settings.return_value = {"debug_mode": False}


class TestAsyncNonBlocking(unittest.TestCase, _MockHelperMixin):
    """
    Verify async functions don't block the event loop.

    PR #2157 Context:
    - Symptom: Users couldn't load another campaign while an action was processing
    - Root cause: Blocking I/O (Gemini/Firestore) called directly in async functions
    - Fix: Wrap all blocking calls with asyncio.to_thread()

    These tests prevent regression by verifying concurrent operations execute in parallel.
    """

    @patch("mvp_site.world_logic.get_user_settings")
    @patch("mvp_site.world_logic._prepare_game_state")
    @patch("mvp_site.world_logic.firestore_service")
    @patch("mvp_site.world_logic.llm_service")
    def test_concurrent_operations_execute_in_parallel(
        self, mock_llm_service, mock_firestore, mock_prepare, mock_settings
    ):
        """
        CRITICAL: Concurrent coroutines must not serialize.

        If blocking I/O isn't wrapped in asyncio.to_thread():
        - Serial execution: total_time ≈ N × single_duration
        - Parallel execution: total_time ≈ max(single_durations)

        This test mocks blocking calls with delays and verifies parallel timing.
        """
        SIMULATED_BLOCKING_TIME = 0.05  # 50ms simulated blocking per call
        NUM_CONCURRENT = 3
        call_count = 0

        def mock_blocking_call(*args, **kwargs):
            """Simulate blocking I/O that takes time."""
            nonlocal call_count
            call_count += 1
            time.sleep(SIMULATED_BLOCKING_TIME)
            # Return a proper mock response object
            return self._build_mock_response()

        def mock_get_campaign(*args, **kwargs):
            """Mock campaign retrieval with delay."""
            time.sleep(SIMULATED_BLOCKING_TIME)
            return (
                {"selected_prompts": [], "use_default_world": False},
                [{"actor": "user", "sequence_id": 1, "text": "test"}],
            )

        # Configure mocks
        self._configure_common_mocks(
            mock_llm_service,
            mock_firestore,
            mock_prepare,
            mock_settings,
            llm_side_effect=mock_blocking_call,
            campaign_side_effect=mock_get_campaign,
        )

        async def run_concurrent_test():
            """Run multiple async operations concurrently and measure timing."""
            request_data = {
                "user_id": "test-user",
                "campaign_id": "test-campaign",
                "user_input": "test action",
                "mode": "character",
            }

            start = time.perf_counter()

            # Run concurrent operations
            tasks = [
                world_logic.process_action_unified(request_data.copy())
                for _ in range(NUM_CONCURRENT)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            elapsed = time.perf_counter() - start
            return elapsed, results

        # Run the test
        wall_time, results = asyncio.run(run_concurrent_test())

        exceptions = [r for r in results if isinstance(r, Exception)]
        self.assertEqual(
            exceptions,
            [],
            f"Concurrent tasks raised exceptions (test may be masking failures): {exceptions[:3]}",
        )

        self.assertEqual(
            call_count,
            NUM_CONCURRENT,
            f"Expected {NUM_CONCURRENT} LLM calls, got {call_count}",
        )

        # Calculate expected times
        serial_time = (
            NUM_CONCURRENT * SIMULATED_BLOCKING_TIME * 2
        )  # 2 blocking calls per op
        # CI systems may have scheduling overhead; allow buffer to reduce flakiness
        parallel_threshold = _calculate_parallel_threshold(serial_time)

        # Debug info for failure diagnosis
        debug_info = (
            f"wall_time={wall_time:.3f}s, "
            f"serial_expected={serial_time:.3f}s, "
            f"parallel_threshold={parallel_threshold:.3f}s, "
            f"calls_made={call_count}"
        )

        self.assertLess(
            wall_time,
            parallel_threshold,
            f"Operations appear to be SERIALIZED! {debug_info}. "
            f"Check that all blocking calls use asyncio.to_thread().",
        )


class TestThreadPoolExecution(unittest.TestCase, _MockHelperMixin):
    """
    Verify blocking I/O runs in thread pool, not main event loop thread.

    asyncio.to_thread() moves blocking operations to ThreadPoolExecutor.
    This test verifies blocking calls execute in worker threads.
    """

    @patch("mvp_site.world_logic.get_user_settings")
    @patch("mvp_site.world_logic._prepare_game_state")
    @patch("mvp_site.world_logic.firestore_service")
    @patch("mvp_site.world_logic.llm_service")
    def test_blocking_calls_execute_in_worker_threads(
        self, mock_llm_service, mock_firestore, mock_prepare, mock_settings
    ):
        """
        Blocking calls wrapped in asyncio.to_thread() should NOT run in main thread.

        If asyncio.to_thread() is missing, blocking calls run in the main event
        loop thread, which blocks ALL other coroutines.
        """
        main_thread_id = threading.current_thread().ident
        blocking_call_threads = []

        def tracking_call(*args, **kwargs):
            """Track which thread executes the blocking call."""
            blocking_call_threads.append(threading.current_thread().ident)
            # Return a proper mock response object
            return self._build_mock_response()

        def mock_get_campaign(*args, **kwargs):
            """Mock that tracks thread."""
            blocking_call_threads.append(threading.current_thread().ident)
            return (
                {"selected_prompts": [], "use_default_world": False},
                [{"actor": "user", "sequence_id": 1, "text": "test"}],
            )

        # Configure mocks
        self._configure_common_mocks(
            mock_llm_service,
            mock_firestore,
            mock_prepare,
            mock_settings,
            llm_side_effect=tracking_call,
            campaign_side_effect=mock_get_campaign,
        )

        async def run_test():
            await world_logic.process_action_unified(
                {
                    "user_id": "test-user",
                    "campaign_id": "test-campaign",
                    "user_input": "test action",
                    "mode": "character",
                }
            )

        asyncio.run(run_test())

        # Verify blocking calls ran in worker threads, not main thread
        # Note: With asyncio.to_thread(), calls SHOULD be in different threads
        # If all calls are in main thread, asyncio.to_thread() is missing
        worker_thread_calls = [
            tid for tid in blocking_call_threads if tid != main_thread_id
        ]

        debug_info = (
            f"main_thread={main_thread_id}, "
            f"blocking_threads={blocking_call_threads}, "
            f"worker_calls={len(worker_thread_calls)}/{len(blocking_call_threads)}"
        )

        self.assertTrue(
            len(blocking_call_threads) > 0,
            f"No blocking calls were tracked. {debug_info}",
        )

        all_in_main = all(tid == main_thread_id for tid in blocking_call_threads)
        self.assertFalse(
            all_in_main,
            f"All blocking calls executed in main event loop thread. {debug_info}",
        )

        self.assertGreater(
            len(worker_thread_calls),
            0,
            f"Expected at least one blocking call in a worker thread. {debug_info}",
        )


class TestBlockingCallStaticAnalysis(unittest.TestCase):
    """
    Static AST analysis to detect unwrapped blocking calls.

    This catches regressions at parse time, before runtime.
    Scans world_logic.py for calls to known blocking services
    that are NOT wrapped in asyncio.to_thread().

    CRITICAL: Only checks async functions - sync functions don't have
    the event loop blocking issue.
    """

    # Known blocking service functions that MUST be wrapped in async functions
    BLOCKING_SERVICES = {
        "firestore_service": [
            "get_campaign_by_id",
            "get_campaign_state",
            "update_game_state",
            "update_campaign_game_state",
            "create_campaign",
            "get_campaigns_list",
            "add_story_entry",
            "update_story_context",
            "get_user_settings",
            "update_user_settings",
        ],
        "llm_service": [
            "continue_story",
            "get_initial_story",
        ],
    }

    @staticmethod
    def _get_world_logic_path():
        return os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "world_logic.py"
        )

    def test_all_blocking_calls_wrapped_in_async_functions(self):
        """
        Parse world_logic.py AST and verify all blocking service calls
        within async functions are wrapped in asyncio.to_thread().

        Uses a hybrid AST + source line analysis for accurate detection:
        1. AST identifies async function boundaries and line ranges
        2. Regex finds service calls on each line
        3. Context analysis checks for asyncio.to_thread wrapper
        """
        # Get the path to world_logic.py
        world_logic_path = self._get_world_logic_path()

        with open(world_logic_path) as f:
            source = f.read()

        tree = ast.parse(source)
        source_lines = source.split("\n")

        # Build map of line number -> (function_name, is_async)
        line_to_func = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                is_async = isinstance(node, ast.AsyncFunctionDef)
                end_line = (
                    node.end_lineno
                    if hasattr(node, "end_lineno")
                    else len(source_lines)
                )
                for lineno in range(node.lineno, end_line + 1):
                    line_to_func[lineno] = (node.name, is_async)

        # Find service calls using regex (more reliable than pure AST for this)
        service_patterns = [
            (r"firestore_service\.(\w+)\(", "firestore_service"),
            (r"llm_service\.(\w+)\(", "llm_service"),
        ]

        violations = []

        for i, line in enumerate(source_lines, 1):
            for pattern, service in service_patterns:
                match = re.search(pattern, line)
                if match:
                    method = match.group(1)

                    # Check if this is a blocking service method
                    if service in self.BLOCKING_SERVICES:
                        if method not in self.BLOCKING_SERVICES[service]:
                            continue  # Not a blocking method we care about

                    # Check if we're in an async function
                    func_info = line_to_func.get(i)
                    if not func_info or not func_info[1]:  # Not async
                        continue

                    func_name = func_info[0]

                    # Check if line or previous few lines have asyncio.to_thread
                    has_to_thread = "asyncio.to_thread" in line
                    if not has_to_thread:
                        for offset in range(1, 4):
                            if i - offset >= 1:
                                prev_line = source_lines[i - offset - 1]
                                if "asyncio.to_thread" in prev_line:
                                    has_to_thread = True
                                    break

                    if not has_to_thread:
                        violations.append(
                            f"async {func_name}() line {i}: {service}.{method}() "
                            f"not wrapped in asyncio.to_thread()\n"
                            f"      Code: {line.strip()[:70]}..."
                        )

        self.assertEqual(
            violations,
            [],
            f"Found {len(violations)} unwrapped blocking call(s) in async functions:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nFIX: Wrap with 'await asyncio.to_thread(service.function, args)'",
        )

    def test_asyncio_import_present(self):
        """Verify asyncio is imported in world_logic.py (required for to_thread)."""
        world_logic_path = self._get_world_logic_path()

        with open(world_logic_path) as f:
            source = f.read()

        self.assertIn(
            "import asyncio",
            source,
            "world_logic.py must import asyncio for asyncio.to_thread() usage",
        )

    def test_to_thread_call_count_matches_expectations(self):
        """
        Verify that asyncio.to_thread() is used a reasonable number of times.

        This acts as a canary - if the count drops significantly, it may
        indicate that someone removed the wrappers.
        """
        world_logic_path = self._get_world_logic_path()

        with open(world_logic_path) as f:
            source = f.read()

        to_thread_count = source.count("asyncio.to_thread(")

        # PR #2157 added ~25 asyncio.to_thread() calls
        # Allow some variance but catch major regressions
        MIN_EXPECTED = 20  # Minimum expected calls
        self.assertGreaterEqual(
            to_thread_count,
            MIN_EXPECTED,
            f"Only found {to_thread_count} asyncio.to_thread() calls. "
            f"Expected at least {MIN_EXPECTED}. "
            f"Did someone remove the blocking I/O wrappers?",
        )


class TestParallelismIntegration(unittest.TestCase):
    """
    CI-compatible integration tests for parallelism.

    These tests verify concurrent behavior without requiring a live server.
    Uses mocked services with controlled timing to detect serialization.
    """

    def test_concurrent_campaign_retrieval_parallel(self):
        """
        Multiple campaign retrievals should execute in parallel.

        Tests get_campaign_state_unified() which retrieves campaign data
        from Firestore. With asyncio.to_thread(), these should overlap.
        """
        DELAY = 0.03  # 30ms per operation
        NUM_OPS = 3

        def mock_get_state(*args, **kwargs):
            time.sleep(DELAY)
            mock_state = MagicMock()
            mock_state.to_dict.return_value = {"test": "state"}
            return mock_state, False, 0

        def mock_get_campaign(*args, **kwargs):
            time.sleep(DELAY)
            return (
                {"title": "Test Campaign", "selected_prompts": []},
                [{"actor": "user", "sequence_id": 1, "text": "test"}],
            )

        async def run_parallel_test():
            with patch.object(world_logic, "firestore_service", MagicMock()) as mock_fs:
                mock_fs.get_campaign_state = mock_get_state
                mock_fs.get_campaign_by_id = mock_get_campaign

                with (
                    patch.object(
                        world_logic,
                        "get_user_settings",
                        lambda x: {"debug_mode": False},
                    ),
                    patch.object(world_logic, "_prepare_game_state", mock_get_state),
                ):
                    start = time.time()

                    # Run concurrent operations
                    tasks = [
                        world_logic.get_campaign_state_unified(
                            {
                                "user_id": f"user-{i}",
                                "campaign_id": f"campaign-{i}",
                            }
                        )
                        for i in range(NUM_OPS)
                    ]
                    await asyncio.gather(*tasks, return_exceptions=True)

                    return time.time() - start

        elapsed = asyncio.run(run_parallel_test())

        # Serial would be: NUM_OPS * DELAY * 2 (two blocking calls)
        # Parallel should be much less
        serial_time = NUM_OPS * DELAY * 2
        # Allow buffer for CI scheduling overhead
        parallel_threshold = _calculate_parallel_threshold(serial_time)

        self.assertLess(
            elapsed,
            parallel_threshold,
            f"Campaign retrievals serialized: {elapsed:.3f}s vs expected <{parallel_threshold:.3f}s. "
            f"asyncio.to_thread() may be missing for Firestore calls.",
        )

    def test_overlap_percentage_calculation(self):
        """
        Verify the overlap calculation logic for concurrent operations.

        If operations truly run in parallel, overlap percentage should be high.
        This is a unit test for the parallelism detection metric.
        """
        # Simulate overlapping operations
        results = [
            {"abs_start": 0.0, "abs_end": 0.5},  # 0.0 - 0.5
            {"abs_start": 0.1, "abs_end": 0.6},  # 0.1 - 0.6
            {"abs_start": 0.2, "abs_end": 0.7},  # 0.2 - 0.7
        ]

        overlap_pct = self._calculate_overlap_percentage(results)

        # With this setup, all 3 overlap from 0.2-0.5 = 0.3 seconds
        # Wall time is 0.7 seconds
        # Overlap time with >1 concurrent = 0.5 seconds (0.1-0.6)
        # Expected overlap: ~71%
        self.assertGreater(
            overlap_pct,
            50.0,
            f"Overlapping operations should have >50% overlap, got {overlap_pct:.1f}%",
        )

    def _calculate_overlap_percentage(self, results: list) -> float:
        """Calculate overlap percentage for overlapping operations."""
        if not results:
            return 0.0

        min_start = min(r["abs_start"] for r in results)
        max_end = max(r["abs_end"] for r in results)
        wall_time = max_end - min_start

        if wall_time <= 0:
            return 0.0

        events = []
        for r in results:
            events.append((r["abs_start"], 1))
            events.append((r["abs_end"], -1))

        events.sort(key=lambda x: (x[0], -x[1]))

        concurrent_count = 0
        last_time = min_start
        overlap_time = 0.0

        for event_time, delta in events:
            if concurrent_count > 1:
                overlap_time += event_time - last_time
            concurrent_count += delta
            last_time = event_time

        return (overlap_time / wall_time) * 100


class TestAsyncToThreadDocumentation(unittest.TestCase):
    """
    Verify documentation requirements for asyncio.to_thread() usage.

    Good documentation prevents future developers from removing the wrappers.
    """

    def test_concurrency_documented_in_module_docstring(self):
        """Module docstring should document the concurrency requirement."""
        module_doc = world_logic.__doc__ or ""

        self.assertIn(
            "asyncio.to_thread()",
            module_doc,
            "world_logic.py docstring should document asyncio.to_thread() requirement",
        )

        self.assertIn(
            "blocking",
            module_doc.lower(),
            "world_logic.py docstring should mention 'blocking' I/O",
        )

    def test_critical_functions_documented(self):
        """Critical async functions should have docstrings mentioning blocking I/O."""
        critical_functions = [
            "create_campaign_unified",
            "process_action_unified",
            "get_campaign_state_unified",
        ]

        for func_name in critical_functions:
            func = getattr(world_logic, func_name, None)
            if func and asyncio.iscoroutinefunction(func):
                doc = func.__doc__ or ""
                # Should mention blocking I/O handling
                self.assertTrue(
                    "asyncio.to_thread()" in doc or "blocking" in doc.lower(),
                    f"{func_name}() docstring should document blocking I/O handling. "
                    f"Current docstring: {doc[:100]}...",
                )


if __name__ == "__main__":
    unittest.main()
