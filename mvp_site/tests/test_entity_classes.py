#!/usr/bin/env python3
"""Unit tests for entity schema classes"""

import os
import sys
import unittest

from pydantic import ValidationError

# Add the mvp_site directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from schemas.entities_pydantic import (
    Character,
    EntityStatus,
    EntityType,
    HealthStatus,
    Location,
    Stats,
    Visibility,
)


class TestPydanticValidation(unittest.TestCase):
    """Test Pydantic validation functionality"""

    def test_entity_id_validation(self):
        """Test entity ID validation in Pydantic models"""

        # Valid entity IDs should work
        location = Location(entity_id="loc_tavern_001", display_name="The Tavern")
        self.assertEqual(location.entity_id, "loc_tavern_001")

        # Invalid entity IDs should be rejected
        with self.assertRaises(ValidationError):
            Location(entity_id="invalid_format", display_name="Test")

    def test_pydantic_field_validation(self):
        """Test Pydantic field validation with defensive conversion"""

        # Test Stats field validation (should be between 1-30)
        stats = Stats(strength=15, dexterity=10)
        self.assertEqual(stats.strength, 15)

        # Invalid values get converted to safe defaults
        stats = Stats(strength=0)  # Below minimum -> converted to 1
        self.assertEqual(stats.strength, 1)

        # Very high values also get converted to field maximum
        stats = Stats(strength=100)  # Above maximum -> clamped to 30
        self.assertEqual(stats.strength, 30)  # Field maximum


class TestStats(unittest.TestCase):
    """Test Stats class functionality"""

    def test_stats_default_values(self):
        """Test Stats with default values"""
        stats = Stats()
        self.assertEqual(stats.strength, 10)
        self.assertEqual(stats.dexterity, 10)
        self.assertEqual(stats.constitution, 10)
        self.assertEqual(stats.intelligence, 10)
        self.assertEqual(stats.wisdom, 10)
        self.assertEqual(stats.charisma, 10)

    def test_stats_custom_values(self):
        """Test Stats with custom values"""
        stats = Stats(
            strength=18,
            dexterity=14,
            constitution=16,
            intelligence=12,
            wisdom=13,
            charisma=8,
        )
        self.assertEqual(stats.strength, 18)
        self.assertEqual(stats.dexterity, 14)
        self.assertEqual(stats.constitution, 16)
        self.assertEqual(stats.intelligence, 12)
        self.assertEqual(stats.wisdom, 13)
        self.assertEqual(stats.charisma, 8)

    def test_stats_with_string_values(self):
        """Test Stats with string numeric values"""
        stats = Stats(strength="15", dexterity="12", constitution="14")
        self.assertEqual(stats.strength, 15)
        self.assertEqual(stats.dexterity, 12)
        self.assertEqual(stats.constitution, 14)

    def test_stats_with_unknown_values(self):
        """Test Stats handles unknown values gracefully"""
        stats = Stats(strength="unknown", dexterity=None, constitution="invalid")
        self.assertEqual(stats.strength, 10)  # Default value
        self.assertEqual(stats.dexterity, 10)  # Default value
        self.assertEqual(stats.constitution, 10)  # Default value

    def test_stats_range_clamping(self):
        """Test Stats clamps values to valid range"""
        stats = Stats(strength=0, dexterity=35, constitution=-5)
        self.assertEqual(stats.strength, 1)  # Clamped to minimum
        self.assertEqual(stats.dexterity, 30)  # Clamped to maximum
        self.assertEqual(stats.constitution, 1)  # Clamped to minimum


class TestHealthStatus(unittest.TestCase):
    """Test HealthStatus class functionality"""

    def test_health_status_basic(self):
        """Test basic HealthStatus creation"""
        health = HealthStatus(hp=10, hp_max=15, temp_hp=5)
        self.assertEqual(health.hp, 10)
        self.assertEqual(health.hp_max, 15)
        self.assertEqual(health.temp_hp, 5)
        self.assertEqual(health.conditions, [])
        self.assertEqual(health.death_saves, {"successes": 0, "failures": 0})

    def test_health_status_with_conditions(self):
        """Test HealthStatus with conditions"""
        conditions = ["poisoned", "blinded"]
        health = HealthStatus(hp=5, hp_max=10, conditions=conditions)
        self.assertEqual(health.conditions, conditions)

    def test_health_status_hp_validation(self):
        """Test HP validation - should reject hp > hp_max"""

        # Pydantic should reject hp > hp_max rather than clamping
        with self.assertRaises(ValidationError) as context:
            HealthStatus(hp=20, hp_max=10)

        self.assertIn("cannot exceed max HP", str(context.exception))

        # Valid HP should work
        health = HealthStatus(hp=10, hp_max=10)
        self.assertEqual(health.hp, 10)
        self.assertEqual(health.hp_max, 10)

    def test_health_status_with_unknown_values(self):
        """Test HealthStatus with unknown values"""
        health = HealthStatus(hp="unknown", hp_max=None, temp_hp="invalid")
        self.assertEqual(health.hp, 1)  # Default HP
        self.assertEqual(health.hp_max, 1)  # Default HP_MAX
        self.assertEqual(health.temp_hp, 0)  # Default temp_hp

    def test_health_status_negative_temp_hp(self):
        """Test negative temp_hp gets converted to 0"""
        health = HealthStatus(hp=10, hp_max=10, temp_hp=-5)
        self.assertEqual(health.temp_hp, 0)


class TestLocation(unittest.TestCase):
    """Test Location class functionality"""

    def test_location_basic(self):
        """Test basic Location creation"""
        location = Location(
            entity_id="loc_tavern_001",
            display_name="The Prancing Pony",
            description="A cozy tavern",
        )
        self.assertEqual(location.entity_id, "loc_tavern_001")
        self.assertEqual(location.entity_type, EntityType.LOCATION)
        self.assertEqual(location.display_name, "The Prancing Pony")
        self.assertEqual(location.description, "A cozy tavern")
        self.assertEqual(location.aliases, [])
        self.assertEqual(location.connected_locations, [])
        self.assertEqual(location.entities_present, [])
        self.assertEqual(location.environmental_effects, [])

    def test_location_with_all_fields(self):
        """Test Location with all optional fields"""
        location = Location(
            entity_id="loc_tavern_001",
            display_name="The Prancing Pony",
            aliases=["The Pony", "Local Tavern"],
            description="A cozy tavern",
            connected_locations=["loc_street_001", "loc_stable_001"],
            entities_present=["pc_frodo_001", "npc_barkeep_001"],
            environmental_effects=["warm", "noisy"],
        )
        self.assertEqual(location.aliases, ["The Pony", "Local Tavern"])
        self.assertEqual(
            location.connected_locations, ["loc_street_001", "loc_stable_001"]
        )
        self.assertEqual(location.entities_present, ["pc_frodo_001", "npc_barkeep_001"])
        self.assertEqual(location.environmental_effects, ["warm", "noisy"])

    def test_location_invalid_id(self):
        """Test Location with invalid entity ID"""
        with self.assertRaises(ValueError):
            Location(entity_id="invalid_id", display_name="Test Location")


class TestCharacter(unittest.TestCase):
    """Test Character class functionality"""

    def setUp(self):
        """Set up test data"""
        self.health = HealthStatus(hp=10, hp_max=15)
        self.stats = Stats(strength=15, dexterity=12)

    def test_character_basic_pc(self):
        """Test basic Player Character creation"""
        character = Character(
            entity_id="pc_aragorn_001",
            entity_type=EntityType.PLAYER_CHARACTER,
            display_name="Aragorn",
            health=self.health,
            current_location="loc_tavern_001",
        )
        self.assertEqual(character.entity_id, "pc_aragorn_001")
        self.assertEqual(character.entity_type, EntityType.PLAYER_CHARACTER)
        self.assertEqual(character.display_name, "Aragorn")
        self.assertEqual(character.level, 1)  # Default level
        self.assertEqual(character.current_location, "loc_tavern_001")
        self.assertEqual(
            character.status, [EntityStatus.CONSCIOUS]
        )  # Default is enum object
        self.assertEqual(
            character.visibility, Visibility.VISIBLE
        )  # Default is enum object

    def test_character_basic_npc(self):
        """Test basic NPC creation"""
        character = Character(
            entity_id="npc_gandalf_001",
            entity_type=EntityType.NPC,
            display_name="Gandalf",
            health=self.health,
            current_location="loc_tavern_001",
            level=5,
            gender="male",  # Required for NPCs
        )
        self.assertEqual(character.entity_type, EntityType.NPC)
        self.assertEqual(character.level, 5)

    def test_character_with_all_fields(self):
        """Test Character with all optional fields"""
        character = Character(
            entity_id="pc_legolas_001",
            entity_type=EntityType.PLAYER_CHARACTER,
            display_name="Legolas",
            aliases=["Greenleaf", "Elf Prince"],
            health=self.health,
            current_location="loc_forest_001",
            level=3,
            stats=self.stats,
            status=[EntityStatus.CONSCIOUS, EntityStatus.HIDDEN],
            visibility=Visibility.HIDDEN,
            equipped_items=["item_bow_001", "item_arrows_001"],
            inventory=["item_rope_001", "item_bread_001"],
            resources={"gold": 50, "arrows": 30},
            knowledge=["Forest Lore", "Archery Mastery"],
            core_memories=["Childhood in Mirkwood", "First battle"],
            recent_decisions=["Joined the Fellowship", "Tracked the Uruk-hai"],
            relationships={"Gimli": "friend", "Aragorn": "ally"},
        )
        self.assertEqual(character.aliases, ["Greenleaf", "Elf Prince"])
        self.assertEqual(character.level, 3)
        self.assertEqual(character.stats, self.stats)
        self.assertEqual(
            character.status, ["conscious", "hidden"]
        )  # Explicit values become strings
        self.assertEqual(
            character.visibility, "hidden"
        )  # Explicit values become strings
        self.assertEqual(character.equipped_items, ["item_bow_001", "item_arrows_001"])
        self.assertEqual(character.inventory, ["item_rope_001", "item_bread_001"])
        self.assertEqual(character.resources, {"gold": 50, "arrows": 30})
        self.assertEqual(character.knowledge, ["Forest Lore", "Archery Mastery"])
        self.assertEqual(
            character.core_memories, ["Childhood in Mirkwood", "First battle"]
        )
        self.assertEqual(
            character.recent_decisions,
            ["Joined the Fellowship", "Tracked the Uruk-hai"],
        )
        self.assertEqual(
            character.relationships, {"Gimli": "friend", "Aragorn": "ally"}
        )

    def test_character_invalid_entity_id(self):
        """Test Character with invalid entity ID"""
        with self.assertRaises(ValueError):
            Character(
                entity_id="invalid_id",
                entity_type=EntityType.PLAYER_CHARACTER,
                display_name="Test",
                health=self.health,
                current_location="loc_test_001",
            )

    def test_character_invalid_location_id(self):
        """Test Character with invalid location ID"""
        with self.assertRaises(ValueError):
            Character(
                entity_id="pc_test_001",
                entity_type=EntityType.PLAYER_CHARACTER,
                display_name="Test",
                health=self.health,
                current_location="invalid_location",
            )

    def test_character_with_unknown_level(self):
        """Test Character handles unknown level gracefully"""
        character = Character(
            entity_id="pc_test_001",
            entity_type=EntityType.PLAYER_CHARACTER,
            display_name="Test",
            health=self.health,
            current_location="loc_test_001",
            level="unknown",
        )
        self.assertEqual(character.level, 1)  # Should default to 1

    def test_character_default_stats(self):
        """Test Character creates default Stats when none provided"""
        character = Character(
            entity_id="pc_test_001",
            entity_type=EntityType.PLAYER_CHARACTER,
            display_name="Test",
            health=self.health,
            current_location="loc_test_001",
        )
        self.assertIsInstance(character.stats, Stats)
        self.assertEqual(character.stats.strength, 10)  # Default stat value


if __name__ == "__main__":
    unittest.main()
