#!/usr/bin/env python3
"""
Test entity name sanitization in gemini_service.py
"""

import os
import sys
import unittest

# Add parent directory to path
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from gemini_service import sanitize_entity_name_for_id
from schemas.entities_pydantic import NPC, HealthStatus


class TestGeminiEntitySanitization(unittest.TestCase):
    """Test entity name sanitization function in gemini_service"""

    def test_sanitize_entity_name_for_id_basic(self):
        """Test basic sanitization cases"""
        test_cases = [
            # (input, expected_output)
            ("Cazador's Spawn", "cazadors_spawn"),
            ("Jean-Claude", "jean_claude"),
            ("Mind Flayer", "mind_flayer"),
            ("O'Brien", "obrien"),
            ("Dr. Strange", "dr_strange"),
            ("The-Dark-Knight", "the_dark_knight"),
        ]

        for input_name, expected in test_cases:
            result = sanitize_entity_name_for_id(input_name)
            assert result == expected, f"Failed for '{input_name}': got '{result}', expected '{expected}'"

    def test_multiple_apostrophes_and_quotes(self):
        """Test handling of multiple apostrophes and quotes"""
        test_cases = [
            ("Ma'at's Temple Guardian", "maats_temple_guardian"),
            ('"The Chosen One"', "the_chosen_one"),
            ("'Twas brillig", "twas_brillig"),
            ("Rock 'n' Roll", "rock_n_roll"),
        ]

        for input_name, expected in test_cases:
            result = sanitize_entity_name_for_id(input_name)
            assert result == expected

    def test_special_characters(self):
        """Test various special characters"""
        test_cases = [
            ("Name@Email.com", "name_email_com"),
            ("50% Health", "50_health"),
            ("A&B Company", "a_b_company"),
            ("Price: $100", "price_100"),
            ("Question?", "question"),
            ("Exclamation!", "exclamation"),
            ("Hash#Tag", "hash_tag"),
        ]

        for input_name, expected in test_cases:
            result = sanitize_entity_name_for_id(input_name)
            assert result == expected

    def test_unicode_and_accents(self):
        """Test unicode characters and accented letters"""
        test_cases = [
            ("Café", "caf"),
            ("Naïve", "na_ve"),
            ("Björk", "bj_rk"),
            ("Ñoño", "o_o"),
            ("Zürich", "z_rich"),
            ("Москва", ""),  # Cyrillic - removed entirely
            ("東京", ""),  # Japanese - removed entirely
            ("🔥Fire🔥", "fire"),  # Emojis removed
        ]

        for input_name, expected in test_cases:
            result = sanitize_entity_name_for_id(input_name)
            assert result == expected, f"Failed for '{input_name}': got '{result}', expected '{expected}'"

    def test_whitespace_handling(self):
        """Test various whitespace scenarios"""
        test_cases = [
            ("  Leading Spaces", "leading_spaces"),
            ("Trailing Spaces  ", "trailing_spaces"),
            ("Multiple   Spaces", "multiple_spaces"),
            ("Tab\tCharacter", "tab_character"),
            ("New\nLine", "new_line"),
            ("   ", ""),  # Only spaces
            ("\t\n", ""),  # Only whitespace
        ]

        for input_name, expected in test_cases:
            result = sanitize_entity_name_for_id(input_name)
            assert result == expected

    def test_consecutive_special_chars(self):
        """Test multiple consecutive special characters"""
        test_cases = [
            ("A---B", "a_b"),
            ("Name___With___Underscores", "name_with_underscores"),
            ("Multiple!!!Exclamations", "multiple_exclamations"),
            ("Dot...Dot...Dot", "dot_dot_dot"),
            ("Mix___---___Special", "mix_special"),
        ]

        for input_name, expected in test_cases:
            result = sanitize_entity_name_for_id(input_name)
            assert result == expected

    def test_edge_cases(self):
        """Test edge cases"""
        # Empty string
        assert sanitize_entity_name_for_id("") == ""

        # Only special characters
        assert sanitize_entity_name_for_id("!@#$%^&*()") == ""

        # Very long name
        long_name = "A" * 100 + " " + "B" * 100
        expected = "a" * 100 + "_" + "b" * 100
        assert sanitize_entity_name_for_id(long_name) == expected

        # Numbers and underscores (valid chars)
        assert sanitize_entity_name_for_id("Agent_007") == "agent_007"

        # Mixed case
        assert sanitize_entity_name_for_id("CamelCaseNAME") == "camelcasename"

    def test_real_world_npc_names(self):
        """Test with actual NPC names that might appear in games"""
        test_cases = [
            ("Strahd von Zarovich", "strahd_von_zarovich"),
            ("The Lich King", "the_lich_king"),
            ("Drizzt Do'Urden", "drizzt_dourden"),
            ("Lady Aribeth de Tylmarande", "lady_aribeth_de_tylmarande"),
            ("Minsc & Boo", "minsc_boo"),
            ("G'kar", "gkar"),
            ("7-of-9", "7_of_9"),
            ("GLaDOS", "glados"),
            ("HK-47", "hk_47"),
        ]

        for input_name, expected in test_cases:
            result = sanitize_entity_name_for_id(input_name)
            assert result == expected, f"Failed for '{input_name}': got '{result}', expected '{expected}'"

    def test_integration_with_entity_id_format(self):
        """Test that sanitized names work with the entity ID format"""

        # These should all create valid entity IDs
        test_names = [
            "Cazador's Spawn",
            "Jean-Baptiste",
            "Dr. Moreau",
            'The "Chosen" One',
            "50% Dead",
        ]

        for i, name in enumerate(test_names):
            sanitized = sanitize_entity_name_for_id(name)
            entity_id = f"npc_{sanitized}_{i + 1:03d}"

            # This should not raise validation error
            npc = NPC(
                entity_id=entity_id,
                display_name=name,
                health=HealthStatus(hp=10, hp_max=10),
                current_location="loc_test_001",
                gender="other",
            )

            assert npc.entity_id == entity_id
            assert npc.display_name == name


if __name__ == "__main__":
    unittest.main()
