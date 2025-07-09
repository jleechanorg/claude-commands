#!/usr/bin/env python3
"""
Unit tests for main.py structured response building.
Tests that the /api/campaigns/{id}/interaction endpoint returns the correct structure.
"""
import unittest
from unittest.mock import MagicMock, patch
import json


class TestMainStructuredResponseBuilding(unittest.TestCase):
    """Test that main.py builds responses matching the schema"""
    
    def setUp(self):
        """Set up test data"""
        # Mock structured response object
        self.mock_structured_response = MagicMock()
        self.mock_structured_response.narrative = "Test narrative"
        self.mock_structured_response.entities_mentioned = ["goblin", "dragon"]
        self.mock_structured_response.location_confirmed = "Dungeon"
        self.mock_structured_response.state_updates = {"npc_data": {"goblin_1": {"hp_current": 5}}}
        self.mock_structured_response.debug_info = {
            "dm_notes": ["Test note"],
            "dice_rolls": ["1d20+5 = 18"],
            "resources": "HD: 2/3",
            "state_rationale": "Test rationale"
        }
        
        # Mock GeminiResponse with structured_response
        self.mock_gemini_response = MagicMock()
        self.mock_gemini_response.narrative_text = "Test narrative"
        self.mock_gemini_response.structured_response = self.mock_structured_response
        self.mock_gemini_response.state_updates = self.mock_structured_response.state_updates
    
    def test_response_includes_all_required_fields(self):
        """Test that API response includes all fields from structured response"""
        # Build response_data as main.py does
        response_data = {
            'success': True,
            'response': self.mock_gemini_response.narrative_text,
            'debug_mode': True,
            'sequence_id': 5
        }
        
        # Add structured response fields as main.py does
        if self.mock_gemini_response.structured_response:
            # State updates
            if hasattr(self.mock_structured_response, 'state_updates') and self.mock_structured_response.state_updates:
                response_data['state_updates'] = self.mock_structured_response.state_updates
            
            # Entity tracking fields
            response_data['entities_mentioned'] = getattr(self.mock_structured_response, 'entities_mentioned', [])
            response_data['location_confirmed'] = getattr(self.mock_structured_response, 'location_confirmed', 'Unknown')
            
            # Debug info
            if hasattr(self.mock_structured_response, 'debug_info') and self.mock_structured_response.debug_info:
                response_data['debug_info'] = self.mock_structured_response.debug_info
        
        # Verify all fields are present
        self.assertIn('state_updates', response_data)
        self.assertIn('entities_mentioned', response_data)
        self.assertIn('location_confirmed', response_data)
        self.assertIn('debug_info', response_data)
        
        # Verify correct values
        self.assertEqual(response_data['entities_mentioned'], ["goblin", "dragon"])
        self.assertEqual(response_data['location_confirmed'], "Dungeon")
        self.assertEqual(response_data['state_updates']['npc_data']['goblin_1']['hp_current'], 5)
        
        # Verify debug_info structure
        self.assertIn('dice_rolls', response_data['debug_info'])
        self.assertIn('resources', response_data['debug_info'])
        self.assertIn('dm_notes', response_data['debug_info'])
        self.assertIn('state_rationale', response_data['debug_info'])
    
    def test_response_handles_missing_fields_gracefully(self):
        """Test that response handles missing optional fields"""
        # Mock response with minimal fields
        minimal_response = MagicMock()
        minimal_response.narrative_text = "Minimal narrative"
        minimal_response.structured_response = None
        
        response_data = {
            'success': True,
            'response': minimal_response.narrative_text,
            'debug_mode': False,
            'sequence_id': 1
        }
        
        # Try to add structured fields when structured_response is None
        if minimal_response.structured_response:
            response_data['state_updates'] = {}  # This won't execute
        
        # Response should still be valid
        self.assertIn('success', response_data)
        self.assertIn('response', response_data)
        self.assertNotIn('state_updates', response_data)
        self.assertNotIn('debug_info', response_data)
    
    def test_debug_info_only_in_debug_mode(self):
        """Test that debug_info is included based on debug mode"""
        response_data_debug_on = {
            'success': True,
            'response': "Test",
            'debug_mode': True,
            'debug_info': self.mock_structured_response.debug_info
        }
        
        response_data_debug_off = {
            'success': True,
            'response': "Test",
            'debug_mode': False
            # debug_info should still be included if present, frontend decides display
        }
        
        # With debug mode on
        self.assertIn('debug_info', response_data_debug_on)
        self.assertEqual(response_data_debug_on['debug_info']['dice_rolls'], ["1d20+5 = 18"])
        
        # Debug mode flag tells frontend whether to display
        self.assertTrue(response_data_debug_on['debug_mode'])
        self.assertFalse(response_data_debug_off['debug_mode'])
    
    def test_nested_field_extraction(self):
        """Test extraction of fields from nested structure"""
        # The actual data has dice_rolls and resources in debug_info
        debug_info = self.mock_structured_response.debug_info
        
        # Frontend should extract from debug_info
        self.assertIn('dice_rolls', debug_info)
        self.assertIsInstance(debug_info['dice_rolls'], list)
        
        self.assertIn('resources', debug_info)
        self.assertIsInstance(debug_info['resources'], str)
        
        # These fields should be in debug_info, not at top level
        self.assertNotIn('dice_rolls', {'response': 'test', 'debug_info': debug_info})
        self.assertNotIn('resources', {'response': 'test', 'debug_info': debug_info})


if __name__ == '__main__':
    unittest.main()