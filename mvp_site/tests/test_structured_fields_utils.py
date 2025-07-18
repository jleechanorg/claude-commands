#!/usr/bin/env python3
"""
Unit tests for structured_fields_utils.py
Tests the extraction function with various GeminiResponse objects.
"""

import os
import sys
import unittest
from unittest.mock import Mock

# Add the parent directory to the path so we can import from the mvp_site package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import constants
import structured_fields_utils
from gemini_response import GeminiResponse
from narrative_response_schema import NarrativeResponse


class TestStructuredFieldsUtils(unittest.TestCase):
    """Test cases for structured_fields_utils.extract_structured_fields function."""

    def setUp(self):
        """Set up test fixtures for each test."""
        # Sample structured response data
        self.sample_structured_data = {
            "session_header": "Turn 3 - Combat Phase\nHP: 25/30 | AC: 16 | Status: Engaged",
            "planning_block": "What would you like to do next?\n1. Attack with sword\n2. Cast spell\n3. Use item\n4. Retreat",
            "dice_rolls": [
                "Initiative: d20+2 = 15",
                "Attack roll: d20+5 = 18",
                "Damage: 1d8+3 = 7",
            ],
            "resources": "HP: 25/30, SP: 8/12, Gold: 150, Arrows: 24",
            "debug_info": {
                "turn_number": 3,
                "combat_active": True,
                "dm_notes": "Player chose aggressive approach",
                "dice_rolls": ["d20+5", "1d8+3"],
                "enemy_hp": 12,
            },
        }

        # Create a mock structured response object
        self.mock_structured_response = Mock(spec=NarrativeResponse)
        self.mock_structured_response.session_header = self.sample_structured_data[
            "session_header"
        ]
        self.mock_structured_response.planning_block = self.sample_structured_data[
            "planning_block"
        ]
        self.mock_structured_response.dice_rolls = self.sample_structured_data[
            "dice_rolls"
        ]
        self.mock_structured_response.resources = self.sample_structured_data[
            "resources"
        ]
        self.mock_structured_response.debug_info = self.sample_structured_data[
            "debug_info"
        ]

    def test_extract_structured_fields_with_full_data(self):
        """Test extraction with complete structured response data."""
        # Create a mock GeminiResponse with structured_response
        mock_gemini_response = Mock(spec=GeminiResponse)
        mock_gemini_response.structured_response = self.mock_structured_response

        # Extract structured fields
        result = structured_fields_utils.extract_structured_fields(mock_gemini_response)

        # Verify all fields are extracted correctly
        self.assertEqual(
            result[constants.FIELD_SESSION_HEADER],
            self.sample_structured_data["session_header"],
        )
        self.assertEqual(
            result[constants.FIELD_PLANNING_BLOCK],
            self.sample_structured_data["planning_block"],
        )
        self.assertEqual(
            result[constants.FIELD_DICE_ROLLS],
            self.sample_structured_data["dice_rolls"],
        )
        self.assertEqual(
            result[constants.FIELD_RESOURCES], self.sample_structured_data["resources"]
        )
        self.assertEqual(
            result[constants.FIELD_DEBUG_INFO],
            self.sample_structured_data["debug_info"],
        )

    def test_extract_structured_fields_with_empty_fields(self):
        """Test extraction with empty structured response fields."""
        # Create a mock structured response with empty fields
        mock_structured_response = Mock(spec=NarrativeResponse)
        mock_structured_response.session_header = ""
        mock_structured_response.planning_block = ""
        mock_structured_response.dice_rolls = []
        mock_structured_response.resources = ""
        mock_structured_response.debug_info = {}

        mock_gemini_response = Mock(spec=GeminiResponse)
        mock_gemini_response.structured_response = mock_structured_response

        # Extract structured fields
        result = structured_fields_utils.extract_structured_fields(mock_gemini_response)

        # Verify all fields are empty but present
        self.assertEqual(result[constants.FIELD_SESSION_HEADER], "")
        self.assertEqual(result[constants.FIELD_PLANNING_BLOCK], "")
        self.assertEqual(result[constants.FIELD_DICE_ROLLS], [])
        self.assertEqual(result[constants.FIELD_RESOURCES], "")
        self.assertEqual(result[constants.FIELD_DEBUG_INFO], {})

    def test_extract_structured_fields_with_missing_attributes(self):
        """Test extraction when structured response lacks some attributes."""
        # Create a mock structured response with missing attributes
        mock_structured_response = Mock(spec=NarrativeResponse)
        mock_structured_response.session_header = "Available header"
        mock_structured_response.planning_block = "Available planning"
        # dice_rolls, resources, debug_info are missing (will use getattr default)

        mock_gemini_response = Mock(spec=GeminiResponse)
        mock_gemini_response.structured_response = mock_structured_response

        # Extract structured fields
        result = structured_fields_utils.extract_structured_fields(mock_gemini_response)

        # Verify available fields are extracted, missing ones default to empty
        self.assertEqual(result[constants.FIELD_SESSION_HEADER], "Available header")
        self.assertEqual(result[constants.FIELD_PLANNING_BLOCK], "Available planning")
        self.assertEqual(result[constants.FIELD_DICE_ROLLS], [])  # Default empty list
        self.assertEqual(result[constants.FIELD_RESOURCES], "")  # Default empty string
        self.assertEqual(result[constants.FIELD_DEBUG_INFO], {})  # Default empty dict

    def test_extract_structured_fields_with_no_structured_response(self):
        """Test extraction when GeminiResponse has no structured_response."""
        # Create a mock GeminiResponse without structured_response
        mock_gemini_response = Mock(spec=GeminiResponse)
        mock_gemini_response.structured_response = None

        # Extract structured fields
        result = structured_fields_utils.extract_structured_fields(mock_gemini_response)

        # Verify result is empty dict
        self.assertEqual(result, {})

    def test_extract_structured_fields_with_none_values(self):
        """Test extraction when structured response has None values."""
        # Create a mock structured response with None values
        mock_structured_response = Mock(spec=NarrativeResponse)
        mock_structured_response.session_header = None
        mock_structured_response.planning_block = None
        mock_structured_response.dice_rolls = None
        mock_structured_response.resources = None
        mock_structured_response.debug_info = None

        mock_gemini_response = Mock(spec=GeminiResponse)
        mock_gemini_response.structured_response = mock_structured_response

        # Extract structured fields
        result = structured_fields_utils.extract_structured_fields(mock_gemini_response)

        # Verify all fields use defaults when None
        self.assertEqual(result[constants.FIELD_SESSION_HEADER], "")
        self.assertEqual(result[constants.FIELD_PLANNING_BLOCK], "")
        self.assertEqual(result[constants.FIELD_DICE_ROLLS], [])
        self.assertEqual(result[constants.FIELD_RESOURCES], "")
        self.assertEqual(result[constants.FIELD_DEBUG_INFO], {})

    def test_extract_structured_fields_constants_mapping(self):
        """Test that function uses correct constants for field names."""
        # Create a mock response with data
        mock_structured_response = Mock(spec=NarrativeResponse)
        mock_structured_response.session_header = "Test session"
        mock_structured_response.planning_block = "Test planning"
        mock_structured_response.dice_rolls = ["Test roll"]
        mock_structured_response.resources = "Test resources"
        mock_structured_response.debug_info = {"test": "data"}

        mock_gemini_response = Mock(spec=GeminiResponse)
        mock_gemini_response.structured_response = mock_structured_response

        # Extract structured fields
        result = structured_fields_utils.extract_structured_fields(mock_gemini_response)

        # Verify all constants are used as keys
        expected_keys = {
            constants.FIELD_SESSION_HEADER,
            constants.FIELD_PLANNING_BLOCK,
            constants.FIELD_DICE_ROLLS,
            constants.FIELD_RESOURCES,
            constants.FIELD_DEBUG_INFO,
            constants.FIELD_GOD_MODE_RESPONSE,
        }
        self.assertEqual(set(result.keys()), expected_keys)

    def test_extract_structured_fields_with_complex_debug_info(self):
        """Test extraction with complex debug info structure."""
        complex_debug_info = {
            "turn_number": 5,
            "combat_active": True,
            "dm_notes": "Player used clever strategy",
            "dice_rolls": ["d20+3", "2d6+2"],
            "enemy_status": {
                "goblin_1": {"hp": 8, "status": "wounded"},
                "goblin_2": {"hp": 12, "status": "healthy"},
            },
            "environmental_factors": ["heavy_rain", "difficult_terrain"],
        }

        mock_structured_response = Mock(spec=NarrativeResponse)
        mock_structured_response.session_header = "Complex Combat Turn"
        mock_structured_response.planning_block = "Multiple options available"
        mock_structured_response.dice_rolls = [
            "Attack: d20+3 = 16",
            "Damage: 2d6+2 = 8",
        ]
        mock_structured_response.resources = "HP: 30/30, SP: 15/20"
        mock_structured_response.debug_info = complex_debug_info

        mock_gemini_response = Mock(spec=GeminiResponse)
        mock_gemini_response.structured_response = mock_structured_response

        # Extract structured fields
        result = structured_fields_utils.extract_structured_fields(mock_gemini_response)

        # Verify complex debug info is preserved
        self.assertEqual(result[constants.FIELD_DEBUG_INFO], complex_debug_info)
        self.assertEqual(
            result[constants.FIELD_DEBUG_INFO]["enemy_status"]["goblin_1"]["hp"], 8
        )
        self.assertEqual(
            result[constants.FIELD_DEBUG_INFO]["environmental_factors"],
            ["heavy_rain", "difficult_terrain"],
        )

    def test_extract_structured_fields_with_long_text_fields(self):
        """Test extraction with longer text content."""
        long_session_header = """Turn 7 - Dungeon Exploration
=====================================
Current Location: Ancient Temple - Main Chamber
Party Status: All members healthy
Light Sources: 2 torches remaining (30 minutes)
Detected Threats: None visible
Recent Actions: Successfully disarmed pressure plate trap
Next Objective: Investigate the glowing altar"""

        long_planning_block = """The ancient chamber holds many secrets. What would you like to do?

1. Approach the glowing altar carefully
2. Search the walls for hidden passages
3. Cast Detect Magic on the altar
4. Have the rogue check for additional traps
5. Examine the hieroglyphs on the walls
6. Rest and tend to wounds before proceeding
7. Retreat to the previous chamber
8. Use a different approach (describe your action)"""

        mock_structured_response = Mock(spec=NarrativeResponse)
        mock_structured_response.session_header = long_session_header
        mock_structured_response.planning_block = long_planning_block
        mock_structured_response.dice_rolls = [
            "Perception: d20+4 = 18",
            "Investigation: d20+2 = 14",
        ]
        mock_structured_response.resources = "HP: 28/30, SP: 12/15, Torch time: 30 min"
        mock_structured_response.debug_info = {
            "location": "temple_chamber",
            "trap_disarmed": True,
        }

        mock_gemini_response = Mock(spec=GeminiResponse)
        mock_gemini_response.structured_response = mock_structured_response

        # Extract structured fields
        result = structured_fields_utils.extract_structured_fields(mock_gemini_response)

        # Verify long text fields are preserved
        self.assertEqual(result[constants.FIELD_SESSION_HEADER], long_session_header)
        self.assertEqual(result[constants.FIELD_PLANNING_BLOCK], long_planning_block)
        self.assertIn(
            "Ancient Temple - Main Chamber", result[constants.FIELD_SESSION_HEADER]
        )
        self.assertIn("different approach", result[constants.FIELD_PLANNING_BLOCK])


def run_tests():
    """Run all tests and display results."""
    print("Running Structured Fields Utils Tests")
    print("=" * 50)

    # Create a test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStructuredFieldsUtils)

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    if result.wasSuccessful():
        print(f"\n✅ All {result.testsRun} tests passed!")
    else:
        print(
            f"\n❌ {len(result.failures)} failures, {len(result.errors)} errors out of {result.testsRun} tests"
        )
        for test, error in result.failures:
            print(f"FAILED: {test}")
            print(f"  {error}")
        for test, error in result.errors:
            print(f"ERROR: {test}")
            print(f"  {error}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
