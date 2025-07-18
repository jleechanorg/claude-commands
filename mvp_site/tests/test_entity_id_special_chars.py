#!/usr/bin/env python3
"""
Test entity ID validation with special characters - verifies fix for apostrophe bug
"""

import os
import sys
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pydantic import ValidationError
from schemas.entities_pydantic import (
    NPC,
    EntityType,
    HealthStatus,
    create_from_game_state,
    sanitize_entity_name_for_id,
)


class TestEntityIDSpecialCharacters(unittest.TestCase):
    """Test that entity IDs handle special characters properly"""

    def test_sanitize_entity_name_for_id(self):
        """Test the sanitization function handles all special characters"""
        test_cases = [
            # (input, expected_output)
            ("Cazador's Spawn", "cazadors_spawn"),
            ("Jean-Luc Picard", "jean_luc_picard"),
            ("Dr. Strange", "dr_strange"),
            ("The 'Chosen' One", "the_chosen_one"),
            ("Multi  Space  Name", "multi_space_name"),
            ("Name-With-Hyphens", "name_with_hyphens"),
            ("Name@#$%Special", "name_special"),
            ("Ñoño García", "o_o_garc_a"),  # Non-ASCII chars
            ("A!B@C#D$E%F", "a_b_c_d_e_f"),
            ("Under_Score_Name", "under_score_name"),
            ("", ""),
            ("___", ""),  # All underscores
        ]

        for input_name, expected in test_cases:
            result = sanitize_entity_name_for_id(input_name)
            self.assertEqual(
                result,
                expected,
                f"Failed for '{input_name}': got '{result}', expected '{expected}'",
            )

    def test_npc_with_apostrophe_name(self):
        """Test creating NPC with apostrophe in name (the original bug case)"""
        # This should NOT raise a validation error
        npc = NPC(
            entity_id="npc_cazadors_spawn_001",  # Sanitized version
            display_name="Cazador's Spawn",  # Original name with apostrophe
            health=HealthStatus(hp=15, hp_max=15),
            current_location="loc_castle_001",
            gender="male",
        )

        self.assertEqual(npc.entity_id, "npc_cazadors_spawn_001")
        self.assertEqual(npc.display_name, "Cazador's Spawn")
        self.assertEqual(npc.entity_type, EntityType.NPC)

    def test_entity_id_validation_patterns(self):
        """Test that entity ID patterns reject invalid IDs"""
        # Valid IDs should work
        valid_npc = NPC(
            entity_id="npc_valid_name_123",
            display_name="Valid Name",
            health=HealthStatus(hp=10, hp_max=10),
            current_location="loc_test_001",
            gender="female",
        )
        self.assertEqual(valid_npc.entity_id, "npc_valid_name_123")

        # Invalid IDs should raise ValidationError
        with self.assertRaises(ValidationError) as cm:
            NPC(
                entity_id="npc_cazador's_spawn_001",  # Apostrophe not allowed
                display_name="Cazador's Spawn",
                health=HealthStatus(hp=10, hp_max=10),
                current_location="loc_test_001",
                gender="male",
            )

        # Check the error mentions pattern matching
        error_dict = cm.exception.errors()[0]
        self.assertIn("String should match pattern", error_dict["msg"])
        self.assertIn("entity_id", str(error_dict["loc"]))

    def test_create_from_game_state_with_special_chars(self):
        """Test the full pipeline with create_from_game_state"""
        game_state = {
            "player_character_data": {
                "name": "D'Artagnan",
                "hp": 20,
                "hp_max": 20,
                "level": 5,
            },
            "npc_data": {
                "Cazador's Spawn": {
                    "name": "Cazador's Spawn",
                    "hp": 15,
                    "hp_max": 15,
                    "present": True,
                    "gender": "male",
                },
                "Jean-Baptiste Maunier": {
                    "name": "Jean-Baptiste Maunier",
                    "hp": 25,
                    "hp_max": 25,
                    "present": True,
                    "gender": "male",
                },
                "Dr. Moreau": {
                    "name": "Dr. Moreau",
                    "hp": 12,
                    "hp_max": 12,
                    "present": True,
                    "gender": "other",
                },
            },
        }

        # This should work without validation errors
        manifest = create_from_game_state(game_state, session_number=2, turn_number=5)

        # Verify PC
        self.assertEqual(len(manifest.player_characters), 1)
        pc = manifest.player_characters[0]
        self.assertEqual(pc.display_name, "D'Artagnan")
        self.assertEqual(pc.entity_id, "pc_dartagnan_001")

        # Verify NPCs
        self.assertEqual(len(manifest.npcs), 3)

        # Find each NPC and verify
        npc_map = {npc.display_name: npc for npc in manifest.npcs}

        # Cazador's Spawn
        cazador_spawn = npc_map.get("Cazador's Spawn")
        self.assertIsNotNone(cazador_spawn)
        self.assertEqual(cazador_spawn.entity_id, "npc_cazadors_spawn_001")

        # Jean-Baptiste
        jean_baptiste = npc_map.get("Jean-Baptiste Maunier")
        self.assertIsNotNone(jean_baptiste)
        self.assertEqual(jean_baptiste.entity_id, "npc_jean_baptiste_maunier_002")

        # Dr. Moreau
        dr_moreau = npc_map.get("Dr. Moreau")
        self.assertIsNotNone(dr_moreau)
        self.assertEqual(dr_moreau.entity_id, "npc_dr_moreau_003")

    def test_edge_cases(self):
        """Test edge cases for entity ID generation"""
        # All special characters
        self.assertEqual(sanitize_entity_name_for_id("!@#$%^&*()"), "")

        # Mixed case and numbers
        self.assertEqual(sanitize_entity_name_for_id("Agent007"), "agent007")

        # Unicode characters
        self.assertEqual(sanitize_entity_name_for_id("Björk"), "bj_rk")

        # Multiple consecutive spaces/special chars
        self.assertEqual(sanitize_entity_name_for_id("A    B----C"), "a_b_c")


if __name__ == "__main__":
    unittest.main()
