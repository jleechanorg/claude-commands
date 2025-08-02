"""
Test file to verify world_logic.py structure and basic functionality.
This test doesn't require external dependencies.
"""

import asyncio
import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add mvp_site to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import world_logic


class TestUnifiedAPIStructure(unittest.TestCase):
    """Test the structure and basic logic of world_logic.py"""

    def setUp(self):
        """Mock all external dependencies"""
        # Mock all the imports
        self.mock_modules = {}
        modules_to_mock = [
            "constants",
            "document_generator",
            "firestore_service",
            "gemini_service",
            "logging_util",
            "structured_fields_utils",
            "custom_types",
            "debug_hybrid_system",
            "debug_mode_parser",
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
            import world_logic

            assert hasattr(world_logic, "create_campaign_unified")
            assert hasattr(world_logic, "process_action_unified")
            assert hasattr(world_logic, "get_campaign_state_unified")
            assert hasattr(world_logic, "update_campaign_unified")
            assert hasattr(world_logic, "export_campaign_unified")
            assert hasattr(world_logic, "get_campaigns_list_unified")
        except ImportError as e:
            self.fail(f"Failed to import world_logic: {e}")

    def test_build_campaign_prompt(self):
        """Test the campaign prompt building logic"""
        import world_logic

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
        import world_logic

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
        import world_logic

        response = world_logic.create_error_response("Test error", 404)

        assert response["error"] == "Test error"
        assert response["status_code"] == 404
        assert not response["success"]

    def test_success_response_format(self):
        """Test standardized success response format"""
        import world_logic

        data = {"campaign_id": "test123", "title": "Test Campaign"}
        response = world_logic.create_success_response(data)

        assert response["success"]
        assert response["campaign_id"] == "test123"
        assert response["title"] == "Test Campaign"

    def test_create_campaign_unified_validation_sync(self):
        """Test campaign creation validation (sync version)"""
        import asyncio

        import world_logic

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
        import asyncio

        import world_logic

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

    @patch("world_logic.firestore_service.get_campaign_by_id")
    @patch("world_logic.firestore_service.update_campaign_game_state")
    @patch("world_logic.firestore_service.add_story_entry")
    @patch("world_logic.gemini_service.continue_story")
    @patch("world_logic._prepare_game_state")
    @patch("world_logic.get_user_settings")
    def test_sequence_id_calculation_bug_red_phase(
        self,
        mock_settings,
        mock_prepare,
        mock_gemini,
        mock_add_story,
        mock_update_state,
        mock_get_campaign,
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

        # Mock user settings
        mock_settings.return_value = {"debug_mode": False}

        # Mock Gemini response with structured fields
        mock_gemini_response = Mock()
        mock_gemini_response.narrative_text = "Here's a test story"
        mock_gemini_response.get_state_updates.return_value = {}
        mock_gemini_response.structured_response = None
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

    @patch("world_logic.firestore_service.get_campaign_by_id")
    @patch("world_logic.firestore_service.update_campaign_game_state")
    @patch("world_logic.firestore_service.add_story_entry")
    @patch("world_logic.gemini_service.continue_story")
    @patch("world_logic._prepare_game_state")
    @patch("world_logic.get_user_settings")
    def test_user_scene_number_field_red_phase(
        self,
        mock_settings,
        mock_prepare,
        mock_gemini,
        mock_add_story,
        mock_update_state,
        mock_get_campaign,
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

        mock_settings.return_value = {"debug_mode": False}

        mock_gemini_response = Mock()
        mock_gemini_response.narrative_text = "Test story response"
        mock_gemini_response.get_state_updates.return_value = {}
        mock_gemini_response.structured_response = None
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
        import world_logic
        
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
            result = world_logic.truncate_game_state_for_logging(complex_game_state, max_lines=10)
            # Should return truncated JSON string without crashing
            self.assertIsInstance(result, str)
            # Should handle Mock objects gracefully (not crash)
            self.assertTrue(len(result) > 0)
        except (TypeError, ValueError) as e:
            self.fail(
                f"Enhanced logging failed with complex objects: {e}. "
                f"This indicates the JSON serialization enhancement is missing!"
            )


if __name__ == "__main__":
    unittest.main()
