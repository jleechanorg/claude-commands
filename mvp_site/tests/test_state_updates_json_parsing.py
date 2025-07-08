import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gemini_response import GeminiResponse
from narrative_response_schema import NarrativeResponse


class TestStateUpdatesJSONParsing(unittest.TestCase):
    """Test that state updates are properly extracted from JSON responses, not markdown blocks"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_json_response = {
            "narrative": "The brave knight finds a magical sword.",
            "entities_mentioned": ["knight", "magical sword"],
            "location_confirmed": "Ancient Temple",
            "state_updates": {
                "pc_data": {
                    "inventory": {
                        "magical_sword": {
                            "name": "Excalibur",
                            "damage": "2d6",
                            "properties": ["magical", "versatile"]
                        }
                    },
                    "attributes": {
                        "strength": 18
                    }
                },
                "npc_data": {
                    "temple_guardian": {
                        "attitude": "friendly",
                        "quest_given": True
                    }
                }
            }
        }
    
    def test_state_updates_extracted_from_json_response(self):
        """Test that state updates are properly extracted from GeminiResponse object"""
        # Create a NarrativeResponse with state updates
        narrative_response = NarrativeResponse(
            narrative="The brave knight finds a magical sword.",
            entities_mentioned=["knight", "magical sword"],
            location_confirmed="Ancient Temple",
            state_updates=self.sample_json_response["state_updates"]
        )
        
        # Create a GeminiResponse with the structured response
        response = GeminiResponse(
            narrative_text="The brave knight finds a magical sword.",
            structured_response=narrative_response,
            debug_tags_present={'dm_notes': False, 'dice_rolls': False, 'state_changes': False},
            
        )
        
        # Verify state updates are accessible through the property
        self.assertIsNotNone(response.state_updates)
        self.assertIn("pc_data", response.state_updates)
        self.assertIn("npc_data", response.state_updates)
        self.assertEqual(
            response.state_updates["pc_data"]["inventory"]["magical_sword"]["name"],
            "Excalibur"
        )
    
    def test_main_py_uses_json_state_updates_not_markdown_blocks(self):
        """Test that main.py correctly uses state_updates from structured response"""
        # Create a properly structured GeminiResponse
        narrative_response = NarrativeResponse(
            narrative="The brave knight finds a magical sword.",
            entities_mentioned=["knight", "magical sword"],
            state_updates=self.sample_json_response["state_updates"]
        )
        
        gemini_response = GeminiResponse(
            narrative_text="The brave knight finds a magical sword.",
            structured_response=narrative_response,
            debug_tags_present={},
            
        )
        
        # Test that state_updates property works correctly
        self.assertEqual(gemini_response.state_updates, self.sample_json_response["state_updates"])
        
        # Test the actual bug: when structured_response exists, it should use state_updates from it
        # This simulates the code at main.py:877-878
        if gemini_response.structured_response:
            proposed_changes = gemini_response.state_updates  # This is the line that should work
            self.assertEqual(proposed_changes, self.sample_json_response["state_updates"])
        
    def test_no_state_updates_proposed_blocks_in_json_mode(self):
        """Test that system doesn't look for [STATE_UPDATES_PROPOSED] blocks in JSON mode"""
        # Create response with state updates in JSON but also with markdown block in narrative
        narrative_with_block = """The knight enters the temple.

[STATE_UPDATES_PROPOSED]
{
    "pc_data": {
        "gold": 100
    }
}
[/STATE_UPDATES_PROPOSED]

The temple guardian greets him."""
        
        narrative_response = NarrativeResponse(
            narrative=narrative_with_block,
            entities_mentioned=["knight", "temple guardian"],
            state_updates={
                "pc_data": {
                    "attributes": {
                        "wisdom": 14
                    }
                }
            }
        )
        
        response = GeminiResponse(
            narrative_text=narrative_with_block,
            structured_response=narrative_response,
            debug_tags_present={},
            
        )
        
        # The state updates should come from JSON, not the markdown block
        self.assertIn("attributes", response.state_updates["pc_data"])
        self.assertNotIn("gold", response.state_updates["pc_data"])
        
    def test_empty_state_updates_handled_gracefully(self):
        """Test that empty or None state updates are handled properly"""
        # Test with None state_updates
        narrative_response1 = NarrativeResponse(
            narrative="A quiet moment passes.",
            entities_mentioned=[],
            state_updates=None
        )
        response1 = GeminiResponse(
            narrative_text="A quiet moment passes.",
            structured_response=narrative_response1,
            debug_tags_present={},
            
        )
        self.assertEqual(response1.state_updates, {})  # Property returns {} for None
        
        # Test with empty dict
        narrative_response2 = NarrativeResponse(
            narrative="Nothing changes.",
            entities_mentioned=[],
            state_updates={}
        )
        response2 = GeminiResponse(
            narrative_text="Nothing changes.",
            structured_response=narrative_response2,
            debug_tags_present={},
            
        )
        self.assertEqual(response2.state_updates, {})
        
    def test_state_updates_with_complex_nested_structures(self):
        """Test that complex nested state updates are preserved correctly"""
        complex_updates = {
            "pc_data": {
                "inventory": {
                    "backpack": {
                        "items": ["rope", "torch", "rations"],
                        "capacity": 30,
                        "current_weight": 15.5
                    }
                },
                "skills": {
                    "stealth": {
                        "proficiency": True,
                        "expertise": False,
                        "modifier": 5
                    }
                },
                "conditions": ["blessed", "well-rested"]
            },
            "world_state": {
                "time": "dawn",
                "weather": "clear",
                "active_quests": {
                    "main_quest": {
                        "stage": 3,
                        "objectives": ["Find the artifact", "Return to the king"]
                    }
                }
            }
        }
        
        narrative_response = NarrativeResponse(
            narrative="Dawn breaks as the adventurer prepares.",
            entities_mentioned=["adventurer"],
            state_updates=complex_updates
        )
        
        response = GeminiResponse(
            narrative_text="Dawn breaks as the adventurer prepares.",
            structured_response=narrative_response,
            debug_tags_present={},
            
        )
        
        # Verify complex structure is preserved
        self.assertEqual(
            response.state_updates["pc_data"]["inventory"]["backpack"]["current_weight"],
            15.5
        )
        self.assertEqual(
            response.state_updates["world_state"]["active_quests"]["main_quest"]["stage"],
            3
        )


if __name__ == "__main__":
    unittest.main()