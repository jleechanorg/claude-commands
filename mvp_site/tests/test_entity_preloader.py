"""
Unit tests for Entity Pre-Loading System (Option 3)
Tests entity manifest generation and preload text creation.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from entity_preloader import (
    EntityPreloader,
    LocationEntityEnforcer,
    entity_preloader,
    location_enforcer,
)


class TestEntityPreloader(unittest.TestCase):
    def setUp(self):
        self.preloader = EntityPreloader()
        self.preloader.clear_cache()

        # Mock game state with minimal data to avoid timeouts
        self.sample_game_state = {
            "session_data": {
                "player_characters": [
                    {
                        "name": "Sariel",
                        "hp_current": 25,
                        "hp_max": 30,
                        "status": "normal",
                    }
                ],
                "npcs": [
                    {
                        "name": "Cassian",
                        "hp_current": 20,
                        "hp_max": 20,
                        "status": "normal",
                        "location": "Throne Room",
                    },
                    {"name": "Lady Cressida", "location": "Lady Cressida's Chambers"},
                ],
            }
        }

    @patch("entity_preloader.create_from_game_state")
    def test_generate_entity_manifest_caching(self, mock_create):
        """Test that entity manifest generation uses caching properly"""
        mock_manifest = Mock()
        mock_manifest.player_characters = [Mock(name="Sariel")]
        mock_manifest.npcs = [Mock(name="Cassian")]
        mock_create.return_value = mock_manifest

        # First call should create manifest
        result1 = self.preloader.generate_entity_manifest(self.sample_game_state, 1, 1)

        # Second call should use cache
        result2 = self.preloader.generate_entity_manifest(self.sample_game_state, 1, 1)

        # create_from_game_state should only be called once due to caching
        mock_create.assert_called_once()
        self.assertEqual(result1, result2)

    @patch("entity_preloader.create_from_game_state")
    def test_create_entity_preload_text_basic(self, mock_create):
        """Test basic entity preload text generation"""
        # Setup mock manifest
        mock_pc = Mock()
        mock_pc.display_name = "Sariel"
        mock_pc.name = "Sariel"
        mock_pc.hp_current = 25
        mock_pc.hp_max = 30
        mock_pc.status = "normal"

        mock_npc = Mock()
        mock_npc.display_name = "Cassian"
        mock_npc.name = "Cassian"
        mock_npc.hp_current = 20
        mock_npc.hp_max = 20
        mock_npc.status = "normal"
        mock_npc.location = "Throne Room"

        mock_manifest = Mock()
        mock_manifest.player_characters = [mock_pc]
        mock_manifest.npcs = [mock_npc]
        mock_create.return_value = mock_manifest

        result = self.preloader.create_entity_preload_text(self.sample_game_state, 1, 1)

        # Check structure
        self.assertIn("=== ENTITY MANIFEST ===", result)
        self.assertIn("PLAYER CHARACTERS PRESENT:", result)
        self.assertIn("NPCS PRESENT:", result)
        self.assertIn("Sariel", result)
        self.assertIn("Cassian", result)
        self.assertIn("HP: 25/30", result)
        self.assertIn("HP: 20/20", result)
        self.assertIn("Location: Throne Room", result)
        self.assertIn("Do not let any of these entities disappear", result)

    @patch("entity_preloader.create_from_game_state")
    def test_create_entity_preload_text_with_location(self, mock_create):
        """Test entity preload text with location-specific entities"""
        mock_npc = Mock()
        mock_npc.display_name = "Lady Cressida"
        mock_npc.name = "Lady Cressida"
        mock_npc.location = "Lady Cressida's Chambers"

        mock_manifest = Mock()
        mock_manifest.player_characters = []
        mock_manifest.npcs = [mock_npc]
        mock_create.return_value = mock_manifest

        result = self.preloader.create_entity_preload_text(
            self.sample_game_state, 1, 1, location="Lady Cressida's Chambers"
        )

        self.assertIn("ENTITIES IN LADY CRESSIDA'S CHAMBERS:", result)
        self.assertIn("Lady Cressida (resident)", result)
        self.assertIn("Personal furnishings", result)

    @patch("entity_preloader.create_from_game_state")
    def test_get_entity_count(self, mock_create):
        """Test entity counting functionality"""
        mock_manifest = Mock()
        mock_manifest.player_characters = [Mock(), Mock()]  # 2 PCs
        mock_manifest.npcs = [Mock(), Mock(), Mock()]  # 3 NPCs
        mock_create.return_value = mock_manifest

        result = self.preloader.get_entity_count(self.sample_game_state, 1, 1)

        expected = {"player_characters": 2, "npcs": 3, "total_entities": 5}
        self.assertEqual(result, expected)

    def test_get_location_entities_throne_room(self):
        """Test location entity detection for throne room"""
        mock_manifest = Mock()
        mock_manifest.npcs = []

        result = self.preloader._get_location_entities(mock_manifest, "Throne Room")

        self.assertIn("Court guards (background)", result)

    def test_clear_cache(self):
        """Test cache clearing functionality"""
        # Add something to cache
        self.preloader.manifest_cache["test"] = Mock()
        self.assertIn("test", self.preloader.manifest_cache)

        # Clear cache
        self.preloader.clear_cache()
        self.assertEqual(len(self.preloader.manifest_cache), 0)


class TestLocationEntityEnforcer(unittest.TestCase):
    def setUp(self):
        self.enforcer = LocationEntityEnforcer()

    def test_get_required_entities_valerius_study(self):
        """Test location rules for Valerius's study"""
        result = self.enforcer.get_required_entities_for_location("Valerius's Study")

        # No hardcoded rules anymore
        self.assertEqual(result, {})

    def test_get_required_entities_cressida_chambers(self):
        """Test location rules for Lady Cressida's chambers"""
        result = self.enforcer.get_required_entities_for_location(
            "Lady Cressida's Chambers"
        )

        # No hardcoded rules anymore
        self.assertEqual(result, {})

    def test_validate_location_entities_success(self):
        """Test successful location entity validation"""
        present_entities = ["Valerius", "Ancient scrolls"]
        result = self.enforcer.validate_location_entities(
            "Valerius's Study", present_entities
        )

        # No location rules, so validation always passes
        self.assertTrue(result["validation_passed"])
        self.assertEqual(len(result["missing_entities"]), 0)

    def test_validate_location_entities_failure(self):
        """Test location entity validation with no rules"""
        present_entities = ["Sariel"]
        result = self.enforcer.validate_location_entities(
            "Valerius's Study", present_entities
        )

        # No location rules, so validation always passes
        self.assertTrue(result["validation_passed"])
        self.assertEqual(result["missing_entities"], [])

    def test_generate_location_enforcement_text(self):
        """Test location enforcement text generation"""
        result = self.enforcer.generate_location_enforcement_text(
            "Lady Cressida's Chambers"
        )

        self.assertIn("LOCATION: Lady Cressida's Chambers", result)
        # No specific requirements anymore
        self.assertIn("no specific entity requirements", result)


class TestGlobalInstances(unittest.TestCase):
    def test_global_entity_preloader_exists(self):
        """Test that global entity preloader instance exists"""
        self.assertIsInstance(entity_preloader, EntityPreloader)

    def test_global_location_enforcer_exists(self):
        """Test that global location enforcer instance exists"""
        self.assertIsInstance(location_enforcer, LocationEntityEnforcer)


if __name__ == "__main__":
    unittest.main()
