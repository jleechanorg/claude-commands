"""
Test Pydantic validation functionality and performance.
"""

import os
import sys
import time
import unittest

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import entity_tracking


class TestPydanticValidation(unittest.TestCase):
    """Test Pydantic validation functionality and performance"""

    def setUp(self):
        """Setup test data"""
        self.sample_game_state = {
            "player_character_data": {
                "name": "Sariel",
                "hp": 25,
                "hp_max": 30,
                "level": 3,
            },
            "npc_data": {
                "Cassian": {"present": True, "hp": 20, "hp_max": 20},
                "Lady Cressida": {"present": True, "location": "Chambers"},
            },
            "location": "Throne Room",
        }

    def test_pydantic_validation_performance(self):
        """Test Pydantic validation performance"""
        # Performance test
        start_time = time.time()
        iterations = 100

        for i in range(iterations):
            manifest = entity_tracking.create_from_game_state(
                self.sample_game_state, session_number=1, turn_number=i + 1
            )
            assert manifest is not None

        duration = time.time() - start_time
        rate = iterations / duration

        print(
            f"Pydantic validation: {iterations} iterations in {duration:.3f}s ({rate:.0f} ops/sec)"
        )

        # Test functionality
        manifest = entity_tracking.create_from_game_state(
            self.sample_game_state, session_number=1, turn_number=1
        )

        assert entity_tracking.VALIDATION_TYPE == "Pydantic"
        assert len(manifest.player_characters) == 1
        assert manifest.player_characters[0].display_name == "Sariel"
        assert len(manifest.npcs) > 0

    def test_validation_info(self):
        """Test that validation info returns correct Pydantic settings"""
        info = entity_tracking.get_validation_info()

        assert info["validation_type"] == "Pydantic"
        assert info["pydantic_available"] == "true"

    def test_entity_creation_with_validation(self):
        """Test that entities are created with proper validation"""
        manifest = entity_tracking.create_from_game_state(
            self.sample_game_state, session_number=1, turn_number=1
        )

        # Test that SceneManifest has expected structure
        assert isinstance(manifest, entity_tracking.SceneManifest)
        assert isinstance(manifest.player_characters, list)
        assert isinstance(manifest.npcs, list)
        assert isinstance(
            manifest.current_location,
            entity_tracking.SceneManifest.__annotations__["current_location"],
        )

    def test_invalid_data_handling(self):
        """Test that Pydantic validation handles invalid data gracefully"""
        invalid_game_state = {
            "player_character_data": {
                "name": "Test",
                "hp": "unknown",  # Should be converted by DefensiveNumericConverter
                "hp_max": "unknown",
                "level": "invalid",  # Should be converted
            },
            "location": "Test Location",
        }

        # This should not crash due to Pydantic validation + defensive conversion
        try:
            manifest = entity_tracking.create_from_game_state(
                invalid_game_state, session_number=1, turn_number=1
            )
            assert manifest is not None
            print("Pydantic: Handled invalid data gracefully")
        except Exception as e:
            self.fail(f"Pydantic validation failed to handle invalid data: {e}")


if __name__ == "__main__":
    unittest.main()
