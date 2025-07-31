#!/usr/bin/env python3
"""
Test structured generation implementation
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import json
import unittest

from entity_tracking import create_from_game_state
from narrative_response_schema import (
    EntityTrackingInstruction,
    NarrativeResponse,
    create_structured_prompt_injection,
    parse_structured_response,
    validate_entity_coverage,
)


class TestStructuredGeneration(unittest.TestCase):
    """Test structured generation components"""

    def setUp(self):
        """Set up test data"""
        self.test_entities = ["Gideon", "Sariel", "Rowan"]
        self.test_manifest = """=== SCENE MANIFEST ===
Location: The Silver Stag Tavern
Session: 1, Turn: 5

PRESENT CHARACTERS:
- Gideon (PC): HP 45/60, Status: conscious, Visibility: visible
- Sariel (NPC): HP 38/50, Status: conscious, Visibility: visible
- Rowan (NPC): HP 22/40, Status: conscious, Visibility: visible
=== END MANIFEST ==="""

    def test_narrative_response_schema(self):
        """Test NarrativeResponse model"""
        # Valid response
        narrative = "Gideon stands in the tavern, looking at Sariel and Rowan as they discuss their next move."
        entities = ["Gideon", "Sariel", "Rowan"]
        location = "The Silver Stag Tavern"

        response = NarrativeResponse(
            narrative=narrative,
            entities_mentioned=entities,
            location_confirmed=location,
        )

        assert response.narrative == narrative
        assert response.entities_mentioned == entities
        assert response.location_confirmed == location

    def test_entity_tracking_instruction(self):
        """Test EntityTrackingInstruction creation"""
        instruction = EntityTrackingInstruction.create_from_manifest(
            self.test_manifest, self.test_entities
        )

        assert instruction.expected_entities == self.test_entities
        assert "Gideon" in instruction.response_format
        assert "Sariel" in instruction.response_format
        assert "Rowan" in instruction.response_format

    def test_structured_prompt_injection(self):
        """Test prompt injection creation"""
        injection = create_structured_prompt_injection(
            self.test_manifest, self.test_entities
        )

        # Should contain manifest
        assert "=== SCENE MANIFEST ===" in injection
        assert "The Silver Stag Tavern" in injection

        # Should contain entity requirements
        assert "You MUST mention ALL characters" in injection
        assert "Gideon, Sariel, Rowan" in injection

        # JSON format is now handled automatically by always-JSON mode
        # Should contain entity tracking instructions
        assert "entities_mentioned array" in injection
        assert "location_confirmed" in injection

    def test_parse_structured_response_valid_json(self):
        """Test parsing valid JSON response"""
        json_response = {
            "narrative": "Gideon looked around the tavern. Sariel nodded to Rowan as they prepared for the next phase of their mission.",
            "entities_mentioned": ["Gideon", "Sariel", "Rowan"],
            "location_confirmed": "The Silver Stag Tavern",
        }

        response_text = json.dumps(json_response)
        narrative, parsed = parse_structured_response(response_text)

        assert narrative == json_response["narrative"]
        assert isinstance(parsed, NarrativeResponse)
        assert parsed.entities_mentioned == json_response["entities_mentioned"]

    def test_parse_structured_response_with_extra_text(self):
        """Test parsing JSON with extra text around it"""
        json_response = {
            "narrative": "The heroes gathered in the tavern. Gideon spoke to Sariel while Rowan listened.",
            "entities_mentioned": ["Gideon", "Sariel", "Rowan"],
            "location_confirmed": "The Silver Stag Tavern",
        }

        response_text = (
            f"Here's my response:\n{json.dumps(json_response)}\n\nThat's the story!"
        )
        narrative, parsed = parse_structured_response(response_text)

        assert narrative == json_response["narrative"]
        assert isinstance(parsed, NarrativeResponse)

    def test_parse_structured_response_fallback(self):
        """Test fallback for invalid JSON"""
        plain_text = "This is just plain text that mentions Gideon, Sariel, and Rowan in the tavern."
        narrative, parsed = parse_structured_response(plain_text)

        assert narrative == plain_text
        assert isinstance(parsed, NarrativeResponse)
        assert parsed.narrative == plain_text
        assert parsed.entities_mentioned == []  # Should be empty for fallback

    def test_validate_entity_coverage_perfect(self):
        """Test entity coverage validation with perfect coverage"""
        response = NarrativeResponse(
            narrative="Gideon, Sariel, and Rowan stood in the tavern discussing their plans.",
            entities_mentioned=["Gideon", "Sariel", "Rowan"],
            location_confirmed="The Silver Stag Tavern",
        )

        validation = validate_entity_coverage(response, self.test_entities)

        assert validation["schema_valid"]
        assert validation["narrative_valid"]
        assert validation["coverage_rate"] == 1.0
        assert len(validation["missing_from_schema"]) == 0
        assert len(validation["missing_from_narrative"]) == 0

    def test_validate_entity_coverage_missing(self):
        """Test entity coverage validation with missing entities"""
        response = NarrativeResponse(
            narrative="Gideon stood alone in the tavern, waiting for his companions.",
            entities_mentioned=["Gideon"],
            location_confirmed="The Silver Stag Tavern",
        )

        validation = validate_entity_coverage(response, self.test_entities)

        assert not validation["schema_valid"]
        assert not validation["narrative_valid"]
        assert validation["coverage_rate"] < 1.0
        assert "sariel" in validation["missing_from_schema"]
        assert "rowan" in validation["missing_from_schema"]

    def test_integration_with_entity_tracking(self):
        """Test integration with existing entity tracking system"""
        game_state = {
            "player_character_data": {"name": "TestPlayer", "hp": 100, "hp_max": 100},
            "npc_data": {
                "NPC1": {
                    "name": "NPC1",
                    "hp": 50,
                    "hp_max": 50,
                    "present": True,
                    "conscious": True,
                    "hidden": False,
                },
                "NPC2": {
                    "name": "NPC2",
                    "hp": 50,
                    "hp_max": 50,
                    "present": True,
                    "conscious": True,
                    "hidden": False,
                },
            },
            "world_data": {"current_location_name": "Test Location"},
        }

        # Create manifest
        manifest = create_from_game_state(game_state, session_number=1, turn_number=1)
        expected_entities = manifest.get_expected_entities()
        manifest_text = manifest.to_prompt_format()

        # Create structured prompt
        prompt_injection = create_structured_prompt_injection(
            manifest_text, expected_entities
        )

        # Should contain all expected components
        assert "=== SCENE MANIFEST ===" in prompt_injection
        assert "TestPlayer" in prompt_injection
        assert "NPC1" in prompt_injection
        assert "NPC2" in prompt_injection
        # JSON format is now handled automatically by always-JSON mode
        assert "CRITICAL ENTITY TRACKING REQUIREMENT" in prompt_injection

        print("✅ Integration test: Structured generation works with entity tracking")


if __name__ == "__main__":
    print("🧪 Testing Structured Generation Implementation")
    print("=" * 60)

    unittest.main(verbosity=2)
