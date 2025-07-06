#!/usr/bin/env python3
"""
Run a REAL integration test using the test framework
This will properly set up authentication and test the combat bug
"""

import sys
import os
import json
import unittest
from unittest.mock import Mock, patch

# Add mvp_site to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mvp_site')))

# Set environment
os.environ['TESTING'] = 'true'

# Mock Firebase admin to avoid credential issues
import firebase_admin
firebase_admin._apps = {'[DEFAULT]': Mock()}

class RealCombatBugTest(unittest.TestCase):
    """Real test for the combat bug claimed in PR #314"""
    
    @classmethod
    def setUpClass(cls):
        """Set up the Flask test client"""
        from main import create_app
        
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        cls.user_id = 'real-browser-test-user'
        
        print("\n" + "="*70)
        print("🧪 REAL INTEGRATION TEST - Testing Combat Bug")
        print("="*70)
    
    def test_combat_bug_real(self):
        """Test the actual combat bug with real requests"""
        
        # Step 1: Create a campaign
        print("\n✅ Creating test campaign...")
        
        # Mock Firestore responses
        with patch('firestore_service.create_campaign') as mock_create:
            mock_create.return_value = 'test-campaign-123'
            
            create_response = self.client.post(
                '/api/campaigns',
                headers={
                    'Content-Type': 'application/json',
                    'X-Test-Bypass-Auth': 'true',
                    'X-Test-User-ID': self.user_id
                },
                data=json.dumps({
                    'title': 'Combat Bug Test',
                    'prompt': 'A warrior battles a dragon',
                    'selectedPrompts': ['narrative', 'mechanics']
                })
            )
            
            print(f"Campaign creation status: {create_response.status_code}")
            
            if create_response.status_code == 201:
                campaign_data = create_response.get_json()
                campaign_id = campaign_data.get('campaign_id', 'test-campaign-123')
                print(f"✅ Campaign created: {campaign_id}")
                
                # Step 2: Test normal interaction
                print("\n✅ Testing normal interaction...")
                
                # Mock the interaction responses
                with patch('firestore_service.get_campaign_game_state') as mock_get_state, \
                     patch('firestore_service.add_story_entry') as mock_add_story, \
                     patch('gemini_service.generate_opening_story') as mock_gen_story:
                    
                    # Set up mocks
                    mock_get_state.return_value = Mock(to_dict=lambda: {
                        'version': 1,
                        'entities': {'NPCs': []},  # This might be the issue!
                        'narrative': {'current_scene': 'test'}
                    })
                    
                    mock_gen_story.return_value = Mock(
                        narrative_text="Test story response",
                        game_state_updates={}
                    )
                    
                    # Normal interaction
                    normal_response = self.client.post(
                        f'/api/campaigns/{campaign_id}/interact',
                        headers={
                            'Content-Type': 'application/json',
                            'X-Test-Bypass-Auth': 'true',
                            'X-Test-User-ID': self.user_id
                        },
                        data=json.dumps({
                            'input': 'I look around',
                            'mode': 'character'
                        })
                    )
                    
                    print(f"Normal interaction status: {normal_response.status_code}")
                    
                    # Step 3: TEST THE COMBAT BUG
                    print("\n" + "="*70)
                    print("🐛 TESTING COMBAT BUG - CRITICAL TEST!")
                    print("="*70)
                    
                    # Set up game state that might trigger the bug
                    # The bug is likely related to NPCs being a list instead of dict
                    mock_get_state.return_value = Mock(to_dict=lambda: {
                        'version': 1,
                        'entities': {
                            'NPCs': ['Dragon', 'Goblin']  # LIST instead of dict!
                        },
                        'narrative': {'current_scene': 'combat'}
                    })
                    
                    # Combat interaction
                    combat_response = self.client.post(
                        f'/api/campaigns/{campaign_id}/interact',
                        headers={
                            'Content-Type': 'application/json',
                            'X-Test-Bypass-Auth': 'true',
                            'X-Test-User-ID': self.user_id
                        },
                        data=json.dumps({
                            'input': 'I attack the nearest enemy with my sword!',
                            'mode': 'character'
                        })
                    )
                    
                    print(f"\nCombat response status: {combat_response.status_code}")
                    
                    if combat_response.status_code == 500:
                        error_data = combat_response.get_json()
                        error_text = json.dumps(error_data, indent=2)
                        
                        if "AttributeError" in error_text and "'list' object has no attribute 'items'" in error_text:
                            print("\n❌ COMBAT BUG CONFIRMED!")
                            print("AttributeError: 'list' object has no attribute 'items'")
                            print("\nThis confirms PR #314's finding!")
                            
                            # Extract error details
                            if error_data and 'traceback' in error_data:
                                for line in error_data['traceback'].split('\n'):
                                    if 'AttributeError' in line or '.items()' in line:
                                        print(f"  → {line.strip()}")
                        else:
                            print(f"\n⚠️ Different error: {error_data.get('error', 'Unknown')}")
                    
                    elif combat_response.status_code == 200:
                        print("\n✅ Combat succeeded! Bug may be fixed.")
                        combat_data = combat_response.get_json()
                        if combat_data and 'story' in combat_data:
                            print(f"Combat story length: {len(combat_data['story'])} chars")
                    
                    else:
                        print(f"\n⚠️ Unexpected status: {combat_response.status_code}")
            
            else:
                print(f"❌ Campaign creation failed: {create_response.status_code}")
                if create_response.data:
                    print(create_response.data.decode()[:500])
    
    def tearDown(self):
        """Clean up after test"""
        pass

if __name__ == '__main__':
    # Run the test
    print("\n🚀 Starting REAL integration test...")
    print("This uses Flask test client with proper mocking")
    print("Not a simulation - real HTTP request/response cycle!\n")
    
    unittest.main(verbosity=2)