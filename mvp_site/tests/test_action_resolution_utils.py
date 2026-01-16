"""Tests for action_resolution_utils helper functions."""

import unittest

from mvp_site.action_resolution_utils import (
    extract_dice_rolls_from_action_resolution,
    extract_dice_audit_events_from_action_resolution,
    get_action_resolution,
    get_outcome_resolution,
    add_action_resolution_to_response,
)


class TestExtractDiceRollsFromActionResolution(unittest.TestCase):
    """Test extract_dice_rolls_from_action_resolution function"""

    def test_extract_single_roll(self):
        """Test extraction of single dice roll"""
        action_resolution = {
            "mechanics": {
                "rolls": [
                    {
                        "purpose": "Attack",
                        "notation": "1d20+5",
                        "result": 17,
                        "dc": None,
                        "success": None,
                    }
                ]
            }
        }
        result = extract_dice_rolls_from_action_resolution(action_resolution)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "1d20+5 = 17 (Attack)")

    def test_extract_roll_with_dc_and_success(self):
        """Test extraction of roll with DC and success"""
        action_resolution = {
            "mechanics": {
                "rolls": [
                    {
                        "purpose": "Stealth (Soul Siphon Deception)",
                        "notation": "1d20+149",
                        "result": 164,
                        "dc": 45,
                        "success": True,
                    }
                ]
            }
        }
        result = extract_dice_rolls_from_action_resolution(action_resolution)
        self.assertEqual(len(result), 1)
        self.assertEqual(
            result[0], "1d20+149 = 164 vs DC 45 - Success (Stealth (Soul Siphon Deception))"
        )

    def test_extract_roll_with_dc_and_failure(self):
        """Test extraction of roll with DC and failure"""
        action_resolution = {
            "mechanics": {
                "rolls": [
                    {
                        "purpose": "Persuasion",
                        "notation": "1d20+5",
                        "result": 12,
                        "dc": 18,
                        "success": False,
                    }
                ]
            }
        }
        result = extract_dice_rolls_from_action_resolution(action_resolution)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "1d20+5 = 12 vs DC 18 - Failure (Persuasion)")

    def test_extract_multiple_rolls(self):
        """Test extraction of multiple dice rolls"""
        action_resolution = {
            "mechanics": {
                "rolls": [
                    {
                        "purpose": "Parallel Logic Coordination",
                        "notation": "1d20+42",
                        "result": 56,
                        "dc": 25,
                        "success": True,
                    },
                    {
                        "purpose": "Stealth (Soul Siphon Deception)",
                        "notation": "1d20+149",
                        "result": 164,
                        "dc": 45,
                        "success": True,
                    },
                ]
            }
        }
        result = extract_dice_rolls_from_action_resolution(action_resolution)
        self.assertEqual(len(result), 2)
        self.assertEqual(
            result[0], "1d20+42 = 56 vs DC 25 - Success (Parallel Logic Coordination)"
        )
        self.assertEqual(
            result[1], "1d20+149 = 164 vs DC 45 - Success (Stealth (Soul Siphon Deception))"
        )

    def test_extract_empty_rolls(self):
        """Test extraction with empty rolls array"""
        action_resolution = {"mechanics": {"rolls": []}}
        result = extract_dice_rolls_from_action_resolution(action_resolution)
        self.assertEqual(result, [])

    def test_extract_no_mechanics(self):
        """Test extraction with no mechanics field"""
        action_resolution = {}
        result = extract_dice_rolls_from_action_resolution(action_resolution)
        self.assertEqual(result, [])

    def test_extract_no_rolls_field(self):
        """Test extraction with no rolls field"""
        action_resolution = {"mechanics": {}}
        result = extract_dice_rolls_from_action_resolution(action_resolution)
        self.assertEqual(result, [])

    def test_extract_invalid_roll_format(self):
        """Test extraction handles invalid roll format gracefully"""
        action_resolution = {
            "mechanics": {
                "rolls": [
                    {"purpose": "Attack"},  # Missing notation and result
                    "not a dict",  # Invalid type
                ]
            }
        }
        result = extract_dice_rolls_from_action_resolution(action_resolution)
        self.assertEqual(result, [])

    def test_extract_roll_without_purpose(self):
        """Test extraction of roll without purpose"""
        action_resolution = {
            "mechanics": {
                "rolls": [
                    {
                        "notation": "1d20+5",
                        "result": 17,
                        "dc": None,
                        "success": None,
                    }
                ]
            }
        }
        result = extract_dice_rolls_from_action_resolution(action_resolution)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "1d20+5 = 17")


class TestExtractDiceAuditEventsFromActionResolution(unittest.TestCase):
    """Test extract_dice_audit_events_from_action_resolution function"""

    def test_extract_string_audit_events(self):
        """Test extraction of string audit events"""
        action_resolution = {
            "mechanics": {
                "audit_events": [
                    "Rolled 1d20+5 = 17",
                    "Rolled 1d8+3 = 8",
                ]
            }
        }
        result = extract_dice_audit_events_from_action_resolution(action_resolution)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "Rolled 1d20+5 = 17")
        self.assertEqual(result[1], "Rolled 1d8+3 = 8")

    def test_extract_dict_audit_events(self):
        """Test extraction of dict audit events (converted to string)"""
        action_resolution = {
            "mechanics": {
                "audit_events": [
                    {"type": "attack_roll", "result": 17},
                    {"type": "damage_roll", "result": 8},
                ]
            }
        }
        result = extract_dice_audit_events_from_action_resolution(action_resolution)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], str)
        self.assertIsInstance(result[1], str)

    def test_extract_empty_audit_events(self):
        """Test extraction with empty audit_events array"""
        action_resolution = {"mechanics": {"audit_events": []}}
        result = extract_dice_audit_events_from_action_resolution(action_resolution)
        self.assertEqual(result, [])

    def test_extract_no_mechanics(self):
        """Test extraction with no mechanics field"""
        action_resolution = {}
        result = extract_dice_audit_events_from_action_resolution(action_resolution)
        self.assertEqual(result, [])


class TestAddActionResolutionToResponse(unittest.TestCase):
    """Test add_action_resolution_to_response function"""

    def test_extracts_dice_rolls_from_action_resolution(self):
        """Test that dice_rolls are extracted from action_resolution"""
        class MockResponse:
            def __init__(self):
                self.action_resolution = {
                    "mechanics": {
                        "rolls": [
                            {
                                "purpose": "Attack",
                                "notation": "1d20+5",
                                "result": 17,
                                "dc": 18,
                                "success": False,
                            }
                        ]
                    }
                }

        mock_response = MockResponse()
        unified_response = {}
        
        add_action_resolution_to_response(mock_response, unified_response)
        
        # Should have extracted dice_rolls
        self.assertIn("dice_rolls", unified_response)
        self.assertEqual(len(unified_response["dice_rolls"]), 1)
        self.assertEqual(
            unified_response["dice_rolls"][0], "1d20+5 = 17 vs DC 18 - Failure (Attack)"
        )

    def test_overrides_existing_dice_rolls_with_extracted_rolls(self):
        """Test that extracted dice_rolls override existing ones when extraction yields data"""
        class MockResponse:
            def __init__(self):
                self.action_resolution = {
                    "mechanics": {
                        "rolls": [
                            {
                                "purpose": "Attack",
                                "notation": "1d20+5",
                                "result": 17,
                            }
                        ]
                    }
                }
                self.dice_rolls = ["Existing roll"]

        mock_response = MockResponse()
        unified_response = {"dice_rolls": ["Existing roll"]}
        
        add_action_resolution_to_response(mock_response, unified_response)
        
        # Should prefer extracted rolls (single source of truth)
        self.assertIn("dice_rolls", unified_response)
        # Extracted rolls should override existing ones
        self.assertEqual(
            unified_response["dice_rolls"][0], "1d20+5 = 17 (Attack)"
        )

    def test_extracts_dice_audit_events(self):
        """Test that dice_audit_events are extracted from action_resolution"""
        class MockResponse:
            def __init__(self):
                self.action_resolution = {
                    "mechanics": {
                        "audit_events": ["Event 1", "Event 2"]
                    }
                }

        mock_response = MockResponse()
        unified_response = {}
        
        add_action_resolution_to_response(mock_response, unified_response)
        
        # Should have extracted dice_audit_events
        self.assertIn("dice_audit_events", unified_response)
        self.assertEqual(len(unified_response["dice_audit_events"]), 2)
        self.assertEqual(unified_response["dice_audit_events"][0], "Event 1")

    def test_no_action_resolution_no_extraction(self):
        """Test that nothing is extracted if action_resolution is missing"""
        class MockResponse:
            pass

        mock_response = MockResponse()
        unified_response = {}
        
        add_action_resolution_to_response(mock_response, unified_response)
        
        # Should not have dice_rolls or dice_audit_events
        self.assertNotIn("dice_rolls", unified_response)
        self.assertNotIn("dice_audit_events", unified_response)

    def test_bug_fix_missing_dice_rolls_extracted_from_action_resolution(self):
        """Test bug fix: Dice rolls in action_resolution.mechanics.rolls are extracted to dice_rolls
        
        This test verifies the fix for the bug where dice rolls existed in 
        action_resolution.mechanics.rolls but were missing from dice_rolls field,
        causing dice rolls to not display in the UI.
        
        Scenario: LLM populated action_resolution.mechanics.rolls correctly but
        forgot to populate dice_rolls directly. The backend should automatically
        extract and populate dice_rolls for UI display.
        """
        class MockResponse:
            def __init__(self):
                # LLM correctly populated action_resolution.mechanics.rolls
                self.action_resolution = {
                    "mechanics": {
                        "rolls": [
                            {
                                "purpose": "Stealth (Soul Siphon Deception)",
                                "notation": "1d20+149",
                                "result": 164,
                                "dc": 45,
                                "success": True,
                            },
                            {
                                "purpose": "Attack",
                                "notation": "1d20+5",
                                "result": 17,
                                "dc": None,
                                "success": None,
                            }
                        ]
                    }
                }
                # But forgot to populate dice_rolls (the bug scenario)

        mock_response = MockResponse()
        unified_response = {}  # dice_rolls is missing
        
        add_action_resolution_to_response(mock_response, unified_response)
        
        # Bug fix: Should automatically extract dice_rolls from action_resolution.mechanics.rolls
        self.assertIn("dice_rolls", unified_response, 
                     "dice_rolls should be extracted from action_resolution.mechanics.rolls")
        self.assertEqual(len(unified_response["dice_rolls"]), 2,
                        "Should extract both dice rolls")
        self.assertEqual(
            unified_response["dice_rolls"][0], 
            "1d20+149 = 164 vs DC 45 - Success (Stealth (Soul Siphon Deception))",
            "First roll should be extracted correctly"
        )
        self.assertEqual(
            unified_response["dice_rolls"][1],
            "1d20+5 = 17 (Attack)",
            "Second roll should be extracted correctly"
        )

    def test_bug_fix_empty_dice_rolls_overridden_by_extraction(self):
        """Test bug fix: Empty dice_rolls is overridden when action_resolution has rolls
        
        Scenario: dice_rolls exists but is empty [], while action_resolution.mechanics.rolls
        has actual rolls. The extraction should populate dice_rolls with the extracted rolls.
        """
        class MockResponse:
            def __init__(self):
                self.action_resolution = {
                    "mechanics": {
                        "rolls": [
                            {
                                "purpose": "Persuasion",
                                "notation": "1d20+5",
                                "result": 12,
                                "dc": 18,
                                "success": False,
                            }
                        ]
                    }
                }

        mock_response = MockResponse()
        unified_response = {"dice_rolls": []}  # Empty dice_rolls (bug scenario)
        
        add_action_resolution_to_response(mock_response, unified_response)
        
        # Should extract and populate dice_rolls even though it was empty
        self.assertIn("dice_rolls", unified_response)
        self.assertEqual(len(unified_response["dice_rolls"]), 1)
        self.assertEqual(
            unified_response["dice_rolls"][0],
            "1d20+5 = 12 vs DC 18 - Failure (Persuasion)"
        )
