#!/usr/bin/env python3
"""
Test-Driven Development for Backend Character and Setting Parameters
Phase 2: Backend Testing

Red-Green-Refactor cycle for backend API changes
"""
import os
import sys
import json
import pytest
import tempfile
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set testing environment
os.environ['TESTING'] = 'true'

import main
from main import create_app

class TestCharacterSettingBackend:
    """Test backend handling of character and setting parameters"""
    
    def setup_method(self):
        """Setup test client"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
    def test_api_accepts_character_setting_params(self):
        """Test that /api/campaigns accepts character and setting parameters"""
        
        print("🧪 TEST 1: API accepts character and setting parameters")
        
        # Mock the dependencies
        with patch('main.gemini_service') as mock_gemini, \
             patch('main.firestore_service') as mock_firestore, \
             patch('main.firebase_admin.auth') as mock_auth:
            
            # Setup mocks
            mock_auth.verify_id_token.return_value = {'uid': 'test-user-123'}
            mock_response = MagicMock()
            mock_response.narrative_text = "Test story"
            mock_gemini.get_initial_story.return_value = mock_response
            mock_firestore.create_campaign.return_value = 'test-campaign-id'
            
            # Test data with character and setting
            test_data = {
                'character': 'Astarion who ascended in BG3',
                'setting': 'Baldur\'s Gate',
                'title': 'Test Campaign',
                'selected_prompts': ['mechanics'],
                'custom_options': []
            }
            
            # Make the API call
            response = self.client.post('/api/campaigns', 
                                      data=json.dumps(test_data),
                                      content_type='application/json',
                                      headers={'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': 'test-user-123'})
            
            # Check that the request was accepted (not a 400 error)
            assert response.status_code != 400, f"API should accept character/setting params, got {response.status_code}: {response.data}"
            print("✅ API accepts character and setting parameters")
            
    def test_empty_character_setting_handling(self):
        """Test that empty character and setting are handled as 'random'"""
        
        print("🧪 TEST 2: Empty character and setting handled as random")
        
        with patch('main.gemini_service') as mock_gemini, \
             patch('main.firestore_service') as mock_firestore, \
             patch('main.firebase_admin.auth') as mock_auth:
            
            # Setup mocks
            mock_auth.verify_id_token.return_value = {'uid': 'test-user-123'}
            mock_response = MagicMock()
            mock_response.narrative_text = "Test story"
            mock_gemini.get_initial_story.return_value = mock_response
            mock_firestore.create_campaign.return_value = 'test-campaign-id'
            
            # Test data with empty character and setting
            test_data = {
                'character': '',
                'setting': '',
                'title': 'Test Campaign',
                'selected_prompts': ['mechanics'],
                'custom_options': []
            }
            
            # Make the API call
            response = self.client.post('/api/campaigns', 
                                      data=json.dumps(test_data),
                                      content_type='application/json',
                                      headers={'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': 'test-user-123'})
            
            # Debug: print response details
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
            
            # Should not fail
            assert response.status_code != 400, f"Empty character/setting should be handled gracefully, got {response.status_code}"
            
            # Check that gemini_service was called with proper parameters
            mock_gemini.get_initial_story.assert_called_once()
            call_args = mock_gemini.get_initial_story.call_args
            
            # The prompt should be constructed properly for empty inputs
            prompt_arg = call_args[0][0]  # First positional argument
            assert prompt_arg is not None, "Prompt should be constructed even with empty inputs"
            print("✅ Empty character and setting handled properly")
            
    def test_character_setting_prompt_construction(self):
        """Test that character and setting are properly used in prompt construction"""
        
        print("🧪 TEST 3: Character and setting used in prompt construction")
        
        with patch('main.gemini_service') as mock_gemini, \
             patch('main.firestore_service') as mock_firestore, \
             patch('main.firebase_admin.auth') as mock_auth:
            
            # Setup mocks
            mock_auth.verify_id_token.return_value = {'uid': 'test-user-123'}
            mock_response = MagicMock()
            mock_response.narrative_text = "Test story"
            mock_gemini.get_initial_story.return_value = mock_response
            mock_firestore.create_campaign.return_value = 'test-campaign-id'
            
            # Test data with specific character and setting
            test_data = {
                'character': 'Astarion who ascended in BG3',
                'setting': 'Baldur\'s Gate',
                'title': 'Test Campaign',
                'selected_prompts': ['mechanics'],
                'custom_options': []
            }
            
            # Make the API call
            response = self.client.post('/api/campaigns', 
                                      data=json.dumps(test_data),
                                      content_type='application/json',
                                      headers={'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': 'test-user-123'})
            
            # Check that gemini_service was called with the constructed prompt
            mock_gemini.get_initial_story.assert_called_once()
            call_args = mock_gemini.get_initial_story.call_args
            
            # The first argument should be the constructed prompt
            prompt_arg = call_args[0][0]
            
            # Check that the prompt contains the character and setting
            assert 'Astarion who ascended in BG3' in prompt_arg, f"Character should be in prompt: {prompt_arg}"
            assert 'Baldur\'s Gate' in prompt_arg, f"Setting should be in prompt: {prompt_arg}"
            
            print("✅ Character and setting properly used in prompt construction")
            
    def test_backward_compatibility_with_old_prompt(self):
        """Test that the API still works if 'prompt' parameter is sent (backward compatibility)"""
        
        print("🧪 TEST 4: Backward compatibility with old prompt parameter")
        
        with patch('main.gemini_service') as mock_gemini, \
             patch('main.firestore_service') as mock_firestore, \
             patch('main.firebase_admin.auth') as mock_auth:
            
            # Setup mocks
            mock_auth.verify_id_token.return_value = {'uid': 'test-user-123'}
            mock_response = MagicMock()
            mock_response.narrative_text = "Test story"
            mock_gemini.get_initial_story.return_value = mock_response
            mock_firestore.create_campaign.return_value = 'test-campaign-id'
            
            # Test data with old prompt parameter (for backward compatibility)
            test_data = {
                'prompt': 'Play as Astarion in Baldur\'s Gate',
                'title': 'Test Campaign',
                'selected_prompts': ['mechanics'],
                'custom_options': []
            }
            
            # Make the API call
            response = self.client.post('/api/campaigns', 
                                      data=json.dumps(test_data),
                                      content_type='application/json',
                                      headers={'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': 'test-user-123'})
            
            # Should still work for backward compatibility
            assert response.status_code != 400, f"Old prompt parameter should still work, got {response.status_code}"
            
            print("✅ Backward compatibility maintained")

if __name__ == "__main__":
    # Run the tests
    test_instance = TestCharacterSettingBackend()
    test_instance.setup_method()
    
    try:
        print("🔴 RED PHASE: Running backend tests (should fail initially)")
        test_instance.test_api_accepts_character_setting_params()
        test_instance.test_empty_character_setting_handling()
        test_instance.test_character_setting_prompt_construction()
        test_instance.test_backward_compatibility_with_old_prompt()
        print("🟢 GREEN PHASE: All backend tests passed!")
    except Exception as e:
        print(f"🔴 RED PHASE: Backend tests failed as expected: {e}")
        print("Now we need to implement the backend changes to make these tests pass")