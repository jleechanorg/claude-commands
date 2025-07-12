#!/usr/bin/env python3
"""
Unit tests for new JSON-based planning block format.
Tests the transition from string-based to structured JSON planning blocks.

RED PHASE: These tests will FAIL initially and drive the implementation.
"""
import unittest
import sys
import os
import json
from unittest.mock import Mock, patch

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gemini_response import GeminiResponse
from narrative_response_schema import NarrativeResponse
import constants


class TestPlanningBlockJsonFormat(unittest.TestCase):
    """Test new JSON-based planning block format"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_narrative = "You approach a mysterious door..."
        
        # New JSON format for planning blocks
        self.new_planning_block_json = {
            "thinking": "The player needs to decide how to approach this door. Multiple options available.",
            "context": "The door appears ancient and might be trapped.",
            "choices": {
                "examine_door": {
                    "text": "Examine Door",
                    "description": "Look carefully for traps or mechanisms",
                    "risk_level": "low"
                },
                "open_directly": {
                    "text": "Open Directly",
                    "description": "Push the door open immediately",
                    "risk_level": "medium"
                },
                "search_for_key": {
                    "text": "Search for Key",
                    "description": "Look around for a key or alternative entrance",
                    "risk_level": "safe"
                },
                "cast_unlock_spell": {
                    "text": "Cast Unlock Spell",
                    "description": "Use magic to bypass the lock",
                    "risk_level": "high"
                }
            }
        }
    
    def test_planning_block_json_structure_validation(self):
        """Test that planning block JSON structure is properly validated"""
        # This test will FAIL initially - drives implementation
        
        raw_response = json.dumps({
            "narrative": self.sample_narrative,
            "planning_block": self.new_planning_block_json,
            "user_scene_number": 1,
            "session_header": "Session 1, Turn 1 | Ancient Ruins | Lvl 1 | HP: 10/10"
        })
        
        response = GeminiResponse.create(raw_response)
        narrative_resp = response.structured_response
        
        # Should parse planning block as structured JSON, not string
        self.assertIsInstance(narrative_resp.planning_block, dict)
        self.assertIn("thinking", narrative_resp.planning_block)
        self.assertIn("choices", narrative_resp.planning_block)
        
        # Validate choices structure
        choices = narrative_resp.planning_block["choices"]
        self.assertIsInstance(choices, dict)
        
        # Check specific choice structure
        examine_choice = choices["examine_door"]
        self.assertEqual(examine_choice["text"], "Examine Door")
        self.assertEqual(examine_choice["description"], "Look carefully for traps or mechanisms")
        self.assertEqual(examine_choice["risk_level"], "low")
    
    def test_planning_block_choice_keys_are_valid_identifiers(self):
        """Test that choice keys are valid JavaScript identifiers"""
        # This test will FAIL initially - drives validation logic
        
        raw_response = json.dumps({
            "narrative": self.sample_narrative,
            "planning_block": self.new_planning_block_json,
            "user_scene_number": 1,
            "session_header": "Session 1, Turn 1"
        })
        
        response = GeminiResponse.create(raw_response)
        narrative_resp = response.structured_response
        
        choices = narrative_resp.planning_block["choices"]
        
        # All choice keys should be valid identifiers (no spaces, special chars except underscore)
        for choice_key in choices.keys():
            # Valid identifier: alphanumeric + underscore, not starting with digit
            self.assertRegex(choice_key, r'^[a-zA-Z_][a-zA-Z0-9_]*$', 
                           f"Choice key '{choice_key}' is not a valid identifier")
    
    def test_planning_block_empty_choices_handled(self):
        """Test that planning blocks with no choices are handled gracefully"""
        # This test will FAIL initially - drives edge case handling
        
        empty_planning_block = {
            "thinking": "The player rests and considers their options.",
            "context": "This is a narrative moment with no immediate choices.",
            "choices": {}
        }
        
        raw_response = json.dumps({
            "narrative": self.sample_narrative,
            "planning_block": empty_planning_block,
            "user_scene_number": 1,
            "session_header": "Session 1, Turn 1"
        })
        
        response = GeminiResponse.create(raw_response)
        narrative_resp = response.structured_response
        
        # Should handle empty choices gracefully
        self.assertIsInstance(narrative_resp.planning_block, dict)
        self.assertEqual(len(narrative_resp.planning_block["choices"]), 0)
        self.assertIn("thinking", narrative_resp.planning_block)
    
    def test_planning_block_malformed_json_fallback(self):
        """Test fallback behavior for malformed planning block JSON"""
        # This test will FAIL initially - drives error handling
        
        # Invalid JSON structure (missing required fields)
        malformed_planning_block = {
            "choices": {
                "invalid_choice": {
                    "text": "Missing description field"
                    # description field missing - should be handled gracefully
                }
            }
            # thinking field missing - should be handled gracefully
        }
        
        raw_response = json.dumps({
            "narrative": self.sample_narrative,
            "planning_block": malformed_planning_block,
            "user_scene_number": 1,
            "session_header": "Session 1, Turn 1"
        })
        
        response = GeminiResponse.create(raw_response)
        narrative_resp = response.structured_response
        
        # Should either fix the structure or fall back gracefully
        # Implementation will determine exact behavior
        self.assertIsNotNone(narrative_resp.planning_block)
    
    def test_planning_block_choice_text_sanitization(self):
        """Test that choice text is properly sanitized for XSS prevention"""
        # This test will FAIL initially - drives security implementation
        
        xss_planning_block = {
            "thinking": "Testing XSS prevention in choice text",
            "choices": {
                "xss_test": {
                    "text": "<script>alert('xss')</script>Examine Door",
                    "description": "Look for traps & mechanisms < > \" '",
                    "risk_level": "low"
                }
            }
        }
        
        raw_response = json.dumps({
            "narrative": self.sample_narrative,
            "planning_block": xss_planning_block,
            "user_scene_number": 1,
            "session_header": "Session 1, Turn 1"
        })
        
        response = GeminiResponse.create(raw_response)
        narrative_resp = response.structured_response
        
        # Should sanitize dangerous content by removing script tags completely
        choice = narrative_resp.planning_block["choices"]["xss_test"]
        # Script tags and their content should be completely removed
        self.assertNotIn("<script>", choice["text"])
        self.assertNotIn("</script>", choice["text"])
        self.assertNotIn("alert", choice["text"])  # Entire script content removed
        # Only the safe content should remain
        self.assertEqual(choice["text"], "Examine Door")  # Just the safe part
        
        # Description should preserve normal characters but without dangerous HTML
        description = choice["description"]
        self.assertIn("&", description)  # Normal ampersand preserved
        self.assertIn("<", description)  # Normal brackets preserved
        self.assertIn('"', description)  # Normal quotes preserved
        self.assertIn("'", description)  # Normal apostrophes preserved
    
    def test_planning_block_unicode_support(self):
        """Test that planning blocks support unicode characters properly"""
        # This test will FAIL initially - drives unicode handling
        
        unicode_planning_block = {
            "thinking": "Testing unicode support 🧙‍♂️✨",
            "choices": {
                "magic_spell": {
                    "text": "Cast Spell 🔮",
                    "description": "Use magical powers ✨ to open the door 🚪",
                    "risk_level": "medium"
                },
                "chinese_option": {
                    "text": "检查门",  # "Examine door" in Chinese
                    "description": "仔细查看是否有陷阱",  # "Look carefully for traps"
                    "risk_level": "low"
                }
            }
        }
        
        raw_response = json.dumps({
            "narrative": self.sample_narrative,
            "planning_block": unicode_planning_block,
            "user_scene_number": 1,
            "session_header": "Session 1, Turn 1"
        }, ensure_ascii=False)
        
        response = GeminiResponse.create(raw_response)
        narrative_resp = response.structured_response
        
        # Should preserve unicode characters
        magic_choice = narrative_resp.planning_block["choices"]["magic_spell"]
        self.assertIn("🔮", magic_choice["text"])
        self.assertIn("✨", magic_choice["description"])
        
        chinese_choice = narrative_resp.planning_block["choices"]["chinese_option"]
        self.assertEqual(chinese_choice["text"], "检查门")
    
    def test_planning_block_backwards_compatibility_string_format(self):
        """Test that old string format is still supported during transition"""
        # This test ensures we don't break existing functionality
        # Should PASS initially, then be removed after full migration
        
        old_string_planning_block = """The player must choose their approach:

1. **Examine Door** - Look carefully for traps or mechanisms
2. **Open Directly** - Push the door open immediately
3. **Search for Key** - Look around for a key or alternative entrance"""
        
        raw_response = json.dumps({
            "narrative": self.sample_narrative,
            "planning_block": old_string_planning_block,
            "user_scene_number": 1,
            "session_header": "Session 1, Turn 1"
        })
        
        response = GeminiResponse.create(raw_response)
        narrative_resp = response.structured_response
        
        # During transition, should still handle string format
        # (This behavior will be removed in Phase 4)
        self.assertIsNotNone(narrative_resp.planning_block)


if __name__ == '__main__':
    unittest.main()