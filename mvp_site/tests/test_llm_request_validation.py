"""
Test validation behavior of LLMRequest class

Tests for the new validation features added to ensure proper type safety,
field validation, and error handling.
"""

import os
import sys
import unittest

# Set TESTING_AUTH_BYPASS environment variable
os.environ["TESTING_AUTH_BYPASS"] = "true"
os.environ["GEMINI_API_KEY"] = "test-api-key"

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mvp_site.llm_request import (
    MAX_PAYLOAD_SIZE,
    MAX_STRING_LENGTH,
    LLMRequest,
    LLMRequestError,
    PayloadTooLargeError,
    ValidationError,
)


class TestLLMRequestValidation(unittest.TestCase):
    """Test validation behavior of LLMRequest class."""

    def test_empty_user_id_raises_validation_error(self):
        """Test that empty user_id raises ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            LLMRequest(
                user_action="test",
                game_mode="character",
                user_id="",  # Empty user_id
            )
        self.assertIn("user_id cannot be empty", str(cm.exception))

    def test_whitespace_user_id_raises_validation_error(self):
        """Test that whitespace-only user_id raises ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            LLMRequest(
                user_action="test",
                game_mode="character",
                user_id="   ",  # Whitespace-only user_id
            )
        self.assertIn("user_id cannot be empty", str(cm.exception))

    def test_empty_game_mode_raises_validation_error(self):
        """Test that empty game_mode raises ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            LLMRequest(
                user_action="test",
                game_mode="",  # Empty game_mode
                user_id="test-user",
            )
        self.assertIn("game_mode cannot be empty", str(cm.exception))

    def test_wrong_game_state_type_raises_validation_error(self):
        """Test that non-dict game_state raises ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            LLMRequest(
                user_action="test",
                game_mode="character",
                user_id="test-user",
                game_state="invalid",  # Should be dict
            )
        self.assertIn("game_state must be dict", str(cm.exception))

    def test_wrong_story_history_type_raises_validation_error(self):
        """Test that non-list story_history raises ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            LLMRequest(
                user_action="test",
                game_mode="character",
                user_id="test-user",
                story_history="invalid",  # Should be list
            )
        self.assertIn("story_history must be list", str(cm.exception))

    def test_wrong_core_memories_type_raises_validation_error(self):
        """Test that non-list core_memories raises ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            LLMRequest(
                user_action="test",
                game_mode="character",
                user_id="test-user",
                core_memories=123,  # Should be list
            )
        self.assertIn("core_memories must be list", str(cm.exception))

    def test_wrong_core_memories_item_type_raises_validation_error(self):
        """Test that non-string items in core_memories raise ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            LLMRequest(
                user_action="test",
                game_mode="character",
                user_id="test-user",
                core_memories=["valid", 123, "also valid"],  # 123 should be string
            )
        self.assertIn("core_memories[1] must be string", str(cm.exception))

    def test_too_long_user_action_raises_validation_error(self):
        """Test that overly long user_action raises ValidationError."""
        long_action = "x" * (MAX_STRING_LENGTH + 1)
        with self.assertRaises(ValidationError) as cm:
            LLMRequest(
                user_action=long_action, game_mode="character", user_id="test-user"
            )
        self.assertIn("User action is too long", str(cm.exception))

    def test_too_long_checkpoint_block_raises_validation_error(self):
        """Test that overly long checkpoint_block raises ValidationError."""
        long_checkpoint = "x" * (MAX_STRING_LENGTH + 1)
        with self.assertRaises(ValidationError) as cm:
            LLMRequest(
                user_action="test",
                game_mode="character",
                user_id="test-user",
                checkpoint_block=long_checkpoint,
            )
        self.assertIn("Checkpoint block is too long", str(cm.exception))

    def test_large_payload_raises_payload_too_large_error(self):
        """Test that oversized JSON payload raises PayloadTooLargeError."""
        # Create a large game_state that will exceed payload limits
        large_data = "x" * (MAX_PAYLOAD_SIZE // 2)
        request = LLMRequest(
            user_action="test",
            game_mode="character",
            user_id="test-user",
            game_state={"large_field": large_data, "another_large_field": large_data},
        )

        with self.assertRaises(PayloadTooLargeError) as cm:
            request.to_json()
        self.assertIn("JSON payload too large", str(cm.exception))

    def test_valid_request_passes_validation(self):
        """Test that valid LLMRequest passes all validation."""
        request = LLMRequest(
            user_action="I look around",
            game_mode="character",
            user_id="test-user-123",
            game_state={"player": {"name": "Hero"}},
            story_history=[{"text": "Once upon a time..."}],
            core_memories=["Important event"],
            selected_prompts=["narrative"],
            sequence_ids=["seq1", "seq2"],
        )

        # Should not raise any exceptions
        json_data = request.to_json()
        self.assertIsInstance(json_data, dict)
        self.assertEqual(json_data["user_action"], "I look around")

    def test_build_story_continuation_validates_parameters(self):
        """Test that build_story_continuation validates input parameters."""
        with self.assertRaises(ValidationError):
            LLMRequest.build_story_continuation(
                user_action="",  # Empty action
                user_id="test-user",
                game_mode="character",
                game_state="invalid",  # Wrong type
                story_history=[],
            )

    def test_build_initial_story_validates_parameters(self):
        """Test that build_initial_story validates input parameters."""
        with self.assertRaises(ValidationError):
            LLMRequest.build_initial_story(
                character_prompt="",  # Empty prompt
                user_id="test-user",
                selected_prompts=[],
            )

    def test_json_serialization_error_handling(self):
        """Test that JSON serialization errors are properly handled."""
        # Create a request with circular reference
        circular_ref = {}
        circular_ref["self"] = circular_ref

        request = LLMRequest(
            user_action="test",
            game_mode="character",
            user_id="test-user",
            game_state=circular_ref,
        )

        with self.assertRaises(LLMRequestError):
            request.to_json()


if __name__ == "__main__":
    unittest.main(verbosity=2)
