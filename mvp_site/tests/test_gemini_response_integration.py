"""
Red/Green Test for GeminiResponse Integration Bug Fix

This test demonstrates the bug where campaign creation failed because
get_initial_story() returns a GeminiResponse object but create_campaign()
expected a string.

Test follows TDD red-green-refactor cycle:
1. RED: Write failing test that exposes the bug
2. GREEN: Fix the code to make test pass
3. REFACTOR: Clean up if needed
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock firebase_admin before importing main
mock_firebase_admin = MagicMock()
mock_firestore = MagicMock()
mock_auth = MagicMock()
mock_firebase_admin.firestore = mock_firestore
mock_firebase_admin.auth = mock_auth

sys.modules['firebase_admin'] = mock_firebase_admin
sys.modules['firebase_admin.firestore'] = mock_firestore
sys.modules['firebase_admin.auth'] = mock_auth

from main import create_app
from gemini_response_simplified import GeminiResponse
import gemini_service


class TestGeminiResponseIntegration(unittest.TestCase):
    """Red/Green test for GeminiResponse integration in campaign creation."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Test headers for authentication bypass
        self.test_headers = {
            'X-Test-Bypass-Auth': 'true',
            'X-Test-User-ID': 'test-user'
        }
    
    @patch('main.firestore_service')
    @patch('main.gemini_service')
    @patch('main.GameState')
    def test_campaign_creation_with_gemini_response_object(self, mock_game_state_class, mock_gemini_service, mock_firestore_service):
        """
        RED/GREEN TEST: Campaign creation should handle GeminiResponse objects properly.
        
        This test would have FAILED before the fix because:
        - get_initial_story() returns GeminiResponse object
        - create_campaign() tried to call .encode() on GeminiResponse
        - GeminiResponse doesn't have .encode() method
        
        After the fix, this test PASSES because:
        - We extract .narrative_text from GeminiResponse before passing to create_campaign()
        """
        # Arrange: Set up mocks
        mock_game_state = MagicMock()
        mock_game_state.to_dict.return_value = {'test': 'state'}
        mock_game_state_class.return_value = mock_game_state
        
        # Create a REAL GeminiResponse object (not a mock)
        # This simulates what get_initial_story() actually returns now
        narrative_text = "Your adventure begins in a bustling tavern..."
        mock_structured_response = MagicMock()
        raw_response = '{"narrative": "Your adventure begins..."}'
        
        # Create a raw JSON response that would come from Gemini API
        raw_json_response = '{"narrative": "Your adventure begins in a bustling tavern...", "entities_mentioned": [], "location_confirmed": "Tavern", "state_updates": {}, "debug_info": {}}'
        
        # Parse JSON and create GeminiResponse object
        import json
        from narrative_response_schema import NarrativeResponse
        parsed_json = json.loads(raw_json_response)
        structured_response = NarrativeResponse(**parsed_json)
        gemini_response_obj = GeminiResponse.create_from_structured_response(structured_response)
        
        # Mock get_initial_story to return actual GeminiResponse object
        mock_gemini_service.get_initial_story.return_value = gemini_response_obj
        
        # Mock firestore to capture what gets passed to create_campaign
        mock_firestore_service.create_campaign.return_value = 'test-campaign-123'
        
        campaign_data = {
            'prompt': 'Create a fantasy adventure',
            'title': 'Test Campaign',
            'selected_prompts': ['narrative'],
            'custom_options': []
        }
        
        # Act: Create campaign via API
        response = self.client.post(
            '/api/campaigns',
            json=campaign_data,
            headers=self.test_headers
        )
        
        # Assert: Campaign creation should succeed
        self.assertEqual(response.status_code, 201)
        
        # Verify the response
        data = response.get_json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('campaign_id'), 'test-campaign-123')
        
        # CRITICAL ASSERTION: Verify that create_campaign received a STRING, not GeminiResponse
        mock_firestore_service.create_campaign.assert_called_once()
        call_args = mock_firestore_service.create_campaign.call_args[0]
        
        # The 4th argument (index 3) should be the opening_story text
        opening_story_arg = call_args[3]
        
        # This assertion would FAIL before the fix (GeminiResponse object passed)
        # This assertion PASSES after the fix (narrative_text string passed)
        self.assertIsInstance(opening_story_arg, str, 
                            "create_campaign should receive narrative text as string, not GeminiResponse object")
        self.assertEqual(opening_story_arg, narrative_text,
                        "create_campaign should receive the narrative_text from GeminiResponse")
    
    def test_gemini_response_object_structure(self):
        """
        Verify that GeminiResponse object has the expected interface.
        
        This test documents the expected structure of GeminiResponse objects
        and ensures they provide the necessary methods for integration.
        """
        # Arrange: Create a GeminiResponse object
        narrative_text = "Test narrative"
        mock_structured_response = MagicMock()
        raw_response = '{"narrative": "Test narrative"}'
        
        # Act: Create GeminiResponse
        raw_json_response = '{"narrative": "Test narrative", "entities_mentioned": [], "location_confirmed": "Unknown", "state_updates": {}, "debug_info": {}}'
        # Parse JSON and create GeminiResponse object
        import json
        from narrative_response_schema import NarrativeResponse
        parsed_json = json.loads(raw_json_response)
        structured_response = NarrativeResponse(**parsed_json)
        gemini_response = GeminiResponse.create_from_structured_response(structured_response)
        
        # Assert: Verify required interface
        self.assertTrue(hasattr(gemini_response, 'narrative_text'), 
                       "GeminiResponse must have narrative_text property")
        self.assertTrue(hasattr(gemini_response, 'structured_response'), 
                       "GeminiResponse must have structured_response property")
        self.assertTrue(hasattr(gemini_response, 'debug_tags_present'), 
                       "GeminiResponse must have debug_tags_present property")
        
        # Verify that narrative_text is a string (what firestore expects)
        self.assertIsInstance(gemini_response.narrative_text, str,
                            "narrative_text must be a string for firestore compatibility")
        
        # Verify that GeminiResponse does NOT have encode method (this would cause the bug)
        self.assertFalse(hasattr(gemini_response, 'encode'),
                        "GeminiResponse should not have encode method - this would cause firestore errors")
    
    def test_get_initial_story_returns_gemini_response(self):
        """
        Integration test: Verify get_initial_story returns GeminiResponse object.
        
        This test ensures that the architecture change is properly implemented.
        """
        with patch('gemini_service._call_gemini_api') as mock_api, \
             patch('gemini_service._get_text_from_response') as mock_get_text:
            
            # Mock the API response
            mock_raw_response = '{"narrative": "Adventure begins...", "entities_mentioned": [], "location_confirmed": "Tavern", "state_updates": {}, "debug_info": {}}'
            mock_get_text.return_value = mock_raw_response
            mock_api.return_value = MagicMock()
            
            # Call get_initial_story
            result = gemini_service.get_initial_story("Test prompt", [])
            
            # Verify it returns GeminiResponse object
            self.assertIsInstance(result, GeminiResponse,
                                "get_initial_story must return GeminiResponse object")
            self.assertIsInstance(result.narrative_text, str,
                                "GeminiResponse.narrative_text must be string")


if __name__ == '__main__':
    # Run the tests to demonstrate red/green cycle
    print("=" * 60)
    print("RED/GREEN TEST DEMONSTRATION")
    print("=" * 60)
    print()
    print("This test demonstrates the GeminiResponse integration bug fix:")
    print("1. RED: Test would fail before fix (GeminiResponse passed to firestore)")
    print("2. GREEN: Test passes after fix (narrative_text extracted)")
    print()
    
    unittest.main(verbosity=2)