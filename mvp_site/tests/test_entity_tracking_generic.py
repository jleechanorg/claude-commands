"""
Tests to ensure entity tracking works for ANY campaign, not just Sariel.
Tests that the system is truly generic and doesn't have hardcoded campaign data.
"""

import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from entity_instructions import EntityInstructionGenerator
from entity_preloader import LocationEntityEnforcer
from entity_tracking import create_from_game_state
from game_state import GameState


class TestEntityTrackingGeneric(unittest.TestCase):
    """Test that entity tracking is generic and not campaign-specific"""

    def test_entity_instructions_not_hardcoded_sariel(self):
        """Test that entity instructions don't have hardcoded Sariel references"""
        generator = EntityInstructionGenerator()

        # Test with a completely different campaign
        non_sariel_entities = ["Bob the Merchant", "Alice the Warrior", "Dragon King"]
        player_references = ["Bob the Merchant"]
        location = "The Marketplace"

        instructions = generator.generate_entity_instructions(
            entities=non_sariel_entities,
            player_references=player_references,
            location=location,
        )

        # Should not contain any Sariel-specific references
        assert "sariel" not in instructions.lower()
        assert "cassian" not in instructions.lower()
        assert "valerius" not in instructions.lower()
        assert "cressida" not in instructions.lower()

        # Should contain our actual entities
        assert "Bob the Merchant" in instructions
        assert "Alice the Warrior" in instructions

    def test_player_character_detection_is_generic(self):
        """Test that PC detection isn't hardcoded to Sariel"""
        generator = EntityInstructionGenerator()

        # After fix, should return False for all (not hardcoded)
        assert not generator._is_player_character("Sariel")
        assert not generator._is_player_character("Gandalf")
        assert not generator._is_player_character("PlayerCharacter")

    def test_location_enforcer_not_hardcoded(self):
        """Test that location enforcer doesn't have hardcoded locations"""
        enforcer = LocationEntityEnforcer()

        # After fix, should return empty for all locations
        generic_location = "The Tavern"
        rules = enforcer.get_required_entities_for_location(generic_location)
        assert rules == {}

        # Even Sariel locations should now return empty
        sariel_rules = enforcer.get_required_entities_for_location("valerius's study")
        assert sariel_rules == {}

    def test_location_mappings_are_generic(self):
        """Test that location owner mappings are disabled (returns False for all)"""
        generator = EntityInstructionGenerator()

        # Location owner detection is now disabled to avoid hardcoded patterns
        # All entities are categorized based on story_critical or background logic instead
        assert not generator._is_location_owner("Valerius", "valerius's study")
        assert not generator._is_location_owner("Lady Cressida", "cressida's chamber")
        assert not generator._is_location_owner("Innkeeper John", "John's Tavern")
        assert not generator._is_location_owner("Wizard Merlin", "Merlin's Tower")

        # Test that random unrelated entities also return False
        assert not generator._is_location_owner("Random Person", "Different Place")
        assert not generator._is_location_owner(
            "Sariel", "Wizard Tower"
        )  # No hardcoded Sariel logic

    def test_entity_specific_instruction_is_generic(self):
        """Test that entity-specific methods are generic"""
        generator = EntityInstructionGenerator()

        # Old method should be gone
        assert not hasattr(generator, "create_cassian_specific_instruction")

        # Entity-specific instruction method was removed in favor of semantic understanding
        # (Part 8.B: Emotional Context and Character Response in system instructions)
        assert not hasattr(generator, "create_entity_specific_instruction")

    def test_entity_tracking_with_different_campaign(self):
        """Test full entity tracking with a non-Sariel campaign"""
        # Create a space opera campaign
        game_state = GameState(
            player_character_data={
                "name": "Captain Rex",
                "class": "Space Marine",
                "hp_current": 100,
                "hp_max": 100,
            },
            world_data={
                "current_location_name": "Bridge of the Starship Endeavor",
                "campaign_type": "Space Opera",
            },
            npc_data={
                "lieutenant_sarah": {
                    "name": "Lieutenant Sarah Chen",
                    "role": "Science Officer",
                    "location": "Bridge of the Starship Endeavor",
                },
                "ai_companion": {
                    "name": "ARIA",
                    "role": "Ship AI",
                    "location": "All ship systems",
                },
            },
            custom_campaign_state={"campaign_name": "Galactic Odyssey"},
        )

        # Create manifest
        manifest = create_from_game_state(
            game_state.to_dict(), session_number=1, turn_number=1
        )

        # Should work with any campaign
        assert len(manifest.player_characters) == 1
        assert manifest.player_characters[0].display_name == "Captain Rex"

        # Check NPCs by entity_id
        npc_names = [npc.display_name for npc in manifest.npcs]
        assert "Lieutenant Sarah Chen" in npc_names
        assert "ARIA" in npc_names

    def test_hardcoded_location_instructions(self):
        """Test that location instructions are hardcoded"""
        generator = EntityInstructionGenerator()

        # These are hardcoded in the method
        sariel_location = "throne room"
        instructions = generator.create_location_specific_instructions(
            sariel_location, ["Guard Captain", "Royal Advisor"]
        )

        assert "Court setting" in instructions
        assert "nobles, guards, or advisors" in instructions

        # But generic locations get generic instructions
        generic_location = "The Spaceship Bridge"
        generic_instructions = generator.create_location_specific_instructions(
            generic_location, ["Captain", "Navigator"]
        )

        # Only gets generic instruction
        assert "Ensure entities appropriate to this setting" in generic_instructions
        assert "Court setting" not in generic_instructions


class TestEntityTrackingGenericFixes(unittest.TestCase):
    """Test proposed fixes for making entity tracking generic"""

    def test_proposed_generic_player_character_detection(self):
        """Test how PC detection should work generically"""
        # This is how it SHOULD work - pass PC info to the generator
        GameState(
            player_character_data={"name": "Captain Rex"},
            world_data={},
            npc_data={},
            custom_campaign_state={},
        )

        # Generator should accept game state or PC name (future enhancement)

    def test_proposed_dynamic_location_rules(self):
        """Test how location rules should work dynamically"""
        # Location rules should come from the campaign data, not hardcoded

        # Future: Dynamic location rules from campaign data

    def test_proposed_no_character_specific_methods(self):
        """Test that generic system shouldn't have character-specific methods"""
        # The system should handle ALL character references generically
        # not have special methods for specific characters


if __name__ == "__main__":
    unittest.main()
